"""Persona file loader: parses frontmatter + structured Markdown body."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import (
    TONE_KEYS,
    TONE_LABELS,
    Example,
    Persona,
    SourceType,
    StyleProfile,
    ToneDimensions,
)

FRONTMATTER_DELIMITER = "---"
BULLET = re.compile(r"^\s*[-*]\s+(.+)$")
NUMBERED = re.compile(r"^\s*\d+[.、)]\s*(.+)$")


def _split_frontmatter(text: str) -> Optional[Dict[str, Any]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_DELIMITER:
            end = i
            break
    if end is None:
        return None
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _bullets(section: str) -> List[str]:
    out = []
    for line in section.splitlines():
        m = BULLET.match(line)
        if m:
            out.append(m.group(1).strip())
    return out


def _numbered(section: str) -> List[str]:
    out = []
    for line in section.splitlines():
        m = NUMBERED.match(line)
        if m:
            out.append(m.group(1).strip())
    return out


def _tone_from_section(section: str) -> ToneDimensions:
    values: Dict[str, float] = {}
    for line in section.splitlines():
        m = BULLET.match(line)
        if not m:
            continue
        item = m.group(1).strip()
        if ":" not in item:
            continue
        key, _, raw = item.partition(":")
        label = key.strip().lower().replace("_", " ").replace("-", " ")
        target = None
        for k, lbl in TONE_LABELS.items():
            if label == lbl.lower():
                target = k
                break
        if target is None and label in TONE_KEYS:
            target = label
        if target is None:
            continue
        try:
            values[target] = float(raw.strip())
        except ValueError:
            continue
    return ToneDimensions.from_dict(values)


def _parse_examples(section: str, negative: bool) -> List[Example]:
    """Parse '### Example N' blocks with Input:/Output:/Reason: fields."""
    examples: List[Example] = []
    current: Optional[Dict[str, Any]] = None
    field: Optional[str] = None
    buffer: List[str] = []

    def commit_current() -> None:
        nonlocal current, field, buffer
        if current is None:
            return
        text = "\n".join(buffer).strip()
        if field is not None and text:
            current[field] = text
        if negative:
            examples.append(
                Example(
                    label=current.get("label"),
                    input=current.get("input", ""),
                    output="",
                    reason=current.get("reason"),
                )
            )
        else:
            examples.append(
                Example(
                    label=current.get("label"),
                    input=current.get("input", ""),
                    output=current.get("output", ""),
                )
            )
        current = None
        field = None
        buffer = []

    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            commit_current()
            current = {"label": stripped[4:].strip()}
            continue
        if current is None:
            continue
        if stripped in ("Input:", "Output:", "Reason:"):
            text = "\n".join(buffer).strip()
            if field is not None and text:
                current[field] = text
            field = stripped[:-1].lower()
            buffer = []
            continue
        if field is not None:
            buffer.append(line)
        elif stripped:
            current.setdefault("input", line)
    commit_current()
    return examples


def _split_sections(body: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current = "__lead__"
    parts: List[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            sections[current] = "\n".join(parts).strip()
            current = line[3:].strip().lower()
            parts = []
        elif line.startswith("# "):
            sections[current] = "\n".join(parts).strip()
            current = "__lead__"
            parts = [line]
        else:
            parts.append(line)
    sections[current] = "\n".join(parts).strip()
    return sections


def parse_persona_markdown(md_text: str, path: Optional[str] = None) -> Persona:
    """Parse a persona Markdown file (frontmatter + body) into a Persona model."""
    front = _split_frontmatter(md_text) or {}
    body_start = 0
    lines = md_text.splitlines()
    if lines and lines[0].strip() == FRONTMATTER_DELIMITER:
        for i in range(1, len(lines)):
            if lines[i].strip() == FRONTMATTER_DELIMITER:
                body_start = i + 1
                break
    body = "\n".join(lines[body_start:]).strip()
    sections = _split_sections(body)

    def section(key: str) -> str:
        for k, v in sections.items():
            if k == key:
                return v
        return ""

    vocab_section = section("vocabulary")
    preferred, avoided = _vocab_subsections(vocab_section)

    profile = StyleProfile(
        voice_summary=section("voice summary"),
        tone=_tone_from_section(section("tone dimensions")),
        sentence_patterns=_bullets(section("sentence style")),
        paragraph_patterns=_bullets(section("paragraph style")),
        rhetorical_patterns=_bullets(section("rhetorical patterns")),
        preferred_vocabulary=preferred,
        avoided_vocabulary=avoided,
        signature_moves=_bullets(section("signature moves")),
        anti_patterns=_bullets(section("anti-patterns")),
        positive_examples=_parse_examples(section("positive examples"), negative=False),
        negative_examples=_parse_examples(section("negative examples"), negative=True),
    )

    source_type = str(front.get("source_type", "user-created"))
    if source_type not in ("archetype", "user-created", "sample-derived", "brand", "inspired"):
        source_type = "user-created"

    persona = Persona(
        id=str(front.get("id", "")).strip(),
        name=str(front.get("name", "")).strip(),
        description=str(front.get("description", "")).strip(),
        category=str(front.get("category", "custom")).strip(),
        languages=[str(x) for x in front.get("language", front.get("languages", ["en"]))],
        emoji=front.get("emoji"),
        version=str(front.get("version", "0.1.0")),
        author=str(front.get("author", "user")),
        license=str(front.get("license", "MIT")),
        tags=[str(x) for x in front.get("tags", [])],
        source_type=source_type,
        style_strength_default=float(front.get("style_strength_default", 0.7)),
        disclaimer=front.get("disclaimer"),
        path=path,
        profile=profile,
        content_preservation_rules=_numbered(section("content preservation rules")),
        transformation_rules=_numbered(section("transformation rules")),
        body_markdown=body,
    )
    return persona


def _subsection(block: str, name: str) -> str:
    """Extract a '### <name>' subsection from a block; falls back to empty."""
    target = "### " + name
    found = False
    parts: List[str] = []
    for line in block.splitlines():
        if line.strip().lower() == target.lower():
            found = True
            continue
        if found and line.startswith("### "):
            break
        if found:
            parts.append(line)
    return "\n".join(parts).strip()


def _subsection_bullets(block: str, name: str) -> List[str]:
    return _bullets(_subsection(block, name))


def _vocab_subsections(block: str) -> tuple[List[str], List[str]]:
    return (
        _subsection_bullets(block, "prefer"),
        _subsection_bullets(block, "avoid"),
    )


def load_persona_file(path: Path) -> Persona:
    return parse_persona_markdown(path.read_text(encoding="utf-8"), path=str(path))


def render_persona_markdown(persona: Persona) -> str:
    """Render a Persona model back to spec-compliant Markdown (frontmatter + body)."""
    langs = "\n".join(f"  - {lang}" for lang in (persona.languages or ["en"]))
    tags = "\n".join(f"  - {tag}" for tag in persona.tags) if persona.tags else "  - sample-derived"
    disclaimer = ""
    if persona.disclaimer:
        disclaimer = f"disclaimer: >\n  {persona.disclaimer}\n"
    front = (
        f"---\n"
        f"id: {persona.id}\n"
        f"name: {persona.name}\n"
        f"description: {persona.description}\n"
        f"category: {persona.category}\n"
        f"language:\n{langs}\n"
        f"emoji: {persona.emoji or '✍️'}\n"
        f"version: {persona.version}\n"
        f"author: {persona.author}\n"
        f"license: {persona.license}\n"
        f"tags:\n{tags}\n"
        f"source_type: {persona.source_type}\n"
        f"style_strength_default: {persona.style_strength_default}\n"
        f"{disclaimer}"
        f"---\n\n"
    )
    body = persona.body_markdown.strip()
    if not body:
        body = f"# {persona.name}\n\n"
    return front + body + "\n"
