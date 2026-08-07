"""Persona extraction from author samples (six-step pipeline).

1. sample cleaning (local, deterministic)
2. content vs style separation (LLM-guided)
3. style dimension extraction
4. persona draft generation
5. positive/negative example generation
6. consistency test (reported as confidence)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .config import LLMConfig, default_config
from .llm import LLMClient
from .loader import parse_persona_markdown
from .models import ConfidenceReport, ExtractionResult, Persona
from .registry import normalize_id

EXTRACT_SYSTEM = "You are a writing-style analyst."

SAMPLE_CLEAN_REPLACEMENTS = [
    (re.compile(r"<[^>]+>"), " "),            # HTML tags
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), ""),  # images
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),  # inline links -> text
    (re.compile(r"^#{1,6}\s*", re.MULTILINE), ""),  # headings
    (re.compile(r"^\s*[-*+]\s+", re.MULTILINE), ""),  # bullets
    (re.compile(r"^\s*\d+[.)]\s+", re.MULTILINE), ""),  # numbered lists
    (re.compile(r"^\s*>+\s?", re.MULTILINE), ""),  # blockquotes
    (re.compile(r"\*\*|__|\*|`|~~"), ""),       # emphasis markers
    (re.compile(r"^\s*(regards|best|thanks|thanks,\s*\S*|sincerely|sent from).*$", re.MULTILINE | re.IGNORECASE), ""),
    (re.compile(r"^\s*[-=_~*]{3,}\s*$", re.MULTILINE), ""),  # hr rules
]


def clean_sample(text: str) -> str:
    """Step 1: strip HTML/markdown noise, forwards, signatures, duplicates."""
    out = text
    for pattern, repl in SAMPLE_CLEAN_REPLACEMENTS:
        out = pattern.sub(repl, out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    lines = [ln.strip() for ln in out.splitlines()]
    seen: set[str] = set()
    cleaned: List[str] = []
    for ln in lines:
        if not ln:
            continue
        if "转发" in ln or "Forwarded" in ln or ln.startswith("-----") :
            continue
        key = ln.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


def extract_persona(
    samples: List[str],
    name: Optional[str] = None,
    language: str = "en",
    config: Optional[LLMConfig] = None,
    prompt_path: Optional[Path] = None,
) -> ExtractionResult:
    """Run the full extraction pipeline against the LLM.

    Returns a draft persona plus a confidence report. The draft is not written
    to disk; callers decide (CLI `--save` / API `status: draft`).
    """
    cleaned = [clean_sample(s) for s in samples if clean_sample(s)]
    if not cleaned:
        raise ValueError("No usable sample text after cleaning.")

    client = LLMClient(config or default_config())
    if prompt_path is None:
        prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "extract-persona.md"
    system = prompt_path.read_text(encoding="utf-8")

    user = (
        f"Author samples (cleaned):\n\n"
        + "\n\n---SAMPLE BREAK---\n\n".join(cleaned)
        + "\n\nDesired persona name: "
        + (name or "Sample-derived Persona")
        + f"\nLanguage: {language}\n"
        + "\nReturn JSON with keys: persona {id, name, description, category, "
        "language, tags, source_type, style_strength_default, profile {voice_summary, "
        "tone {formality, warmth, confidence, humor, emotional_intensity, directness}, "
        "sentence_patterns, paragraph_patterns, rhetorical_patterns, preferred_vocabulary, "
        "avoided_vocabulary, signature_moves, anti_patterns, positive_examples [{input, output}], "
        "negative_examples [{input, output, reason}]}, content_preservation_rules, "
        "transformation_rules, positive_examples_evidence, confidence {overall, "
        "sentence_style, vocabulary, long_form_structure, humor}, warnings}"
    )
    data = client.chat_json(system, user)

    profile_data = data.get("profile") or {}
    tone_data = profile_data.get("tone") or {}
    positive_raw = profile_data.get("positive_examples") or []
    negative_raw = profile_data.get("negative_examples") or []

    markdown = _render_draft_markdown(
        name=(name or data.get("name") or "Sample-derived Persona"),
        description=data.get("description", ""),
        category=data.get("category", "custom"),
        language=language,
        source_type="sample-derived",
        voice_summary=profile_data.get("voice_summary", ""),
        tone=tone_data,
        sentence_patterns=profile_data.get("sentence_patterns", []),
        paragraph_patterns=profile_data.get("paragraph_patterns", []),
        rhetorical_patterns=profile_data.get("rhetorical_patterns", []),
        preferred=profile_data.get("preferred_vocabulary", []),
        avoided=profile_data.get("avoided_vocabulary", []),
        signature_moves=profile_data.get("signature_moves", []),
        anti_patterns=profile_data.get("anti_patterns", []),
        positive_examples=positive_raw,
        negative_examples=negative_raw,
        preservation_rules=data.get("content_preservation_rules", []),
        transformation_rules=data.get("transformation_rules", []),
    )
    persona = parse_persona_markdown(markdown)
    conf_data = data.get("confidence") or {}
    overall = float(conf_data.get("overall", 0.5))
    warnings = [str(w) for w in data.get("warnings", [])]
    dimensions = {k: float(v) for k, v in conf_data.items() if k != "overall"}
    confidence = ConfidenceReport(
        overall=max(0.0, min(1.0, overall)),
        dimensions=dimensions,
        warnings=warnings,
    )
    persona_id = normalize_id(name or data.get("name") or "sample-persona")
    persona.id = persona_id
    if not persona.description:
        persona.description = data.get("description") or "Sample-derived writing persona."
    return ExtractionResult(persona_id=persona_id, status="draft", persona=persona, confidence=confidence)


def _bullet_list(items: List[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def _examples_block(examples: List[dict], with_reason: bool = False) -> str:
    blocks = []
    for i, ex in enumerate(examples, start=1):
        inp = ex.get("input") or ex.get("input") or ""
        out = ex.get("output") or ""
        reason = ex.get("reason") or ""
        if not inp:
            continue
        block = f"### Example {i}\n\nInput:\n\n> {inp.strip()}\n"
        if with_reason:
            if reason:
                block += f"\nReason:\n\n{reason.strip()}\n"
        else:
            if out:
                block += f"\nOutput:\n\n> {out.strip()}\n"
        blocks.append(block)
    return "\n\n".join(blocks)


def _render_draft_markdown(
    name: str,
    description: str,
    category: str,
    language: str,
    source_type: str,
    voice_summary: str,
    tone: dict,
    sentence_patterns: List[str],
    paragraph_patterns: List[str],
    rhetorical_patterns: List[str],
    preferred: List[str],
    avoided: List[str],
    signature_moves: List[str],
    anti_patterns: List[str],
    positive_examples: List[dict],
    negative_examples: List[dict],
    preservation_rules: List[str],
    transformation_rules: List[str],
) -> str:
    tone_lines = "\n".join(
        f"- {key.replace('_', ' ').title()}: {float(value):.2f}"
        for key, value in tone.items()
    )
    default_rules = [
        "Preserve all factual claims",
        "Preserve names, numbers, dates, links, and citations",
        "Preserve the author's original position",
        "Do not add unsupported facts",
        "Do not remove qualifications or uncertainty",
    ]
    rules = preservation_rules or default_rules
    transforms = transformation_rules or [
        "Lead with the most important conclusion",
        "Remove generic introductions",
        "Keep the output within ±20% length unless requested otherwise",
    ]
    numbered = "\n".join(f"{i}. {r}" for i, r in enumerate(rules, start=1))
    numbered_t = "\n".join(f"{i}. {r}" for i, r in enumerate(transforms, start=1))
    return f"""---
id: {normalize_id(name)}
name: {name}
description: {description}
category: {category}
language:
  - {language}
emoji: ✍️
version: 0.1.0
author: user
license: MIT
tags:
  - sample-derived
source_type: {source_type}
style_strength_default: 0.7
---

# {name}

## Identity

You express yourself in a style distilled from the author's sample writing.
You are not a copy of the author; you apply an extracted communication
framework.

## Perspective

- Based on patterns observed in the author's sample writing
- Style features come from the samples; subject matter is not style

## Voice Summary

{voice_summary or "Extracted from samples."}

## Tone Dimensions

{tone_lines}

## Sentence Style

{_bullet_list(sentence_patterns)}

## Paragraph Style

{_bullet_list(paragraph_patterns)}

## Vocabulary

### Prefer

{_bullet_list(preferred)}

### Avoid

{_bullet_list(avoided)}

## Rhetorical Patterns

{_bullet_list(rhetorical_patterns)}

## Signature Moves

{_bullet_list(signature_moves)}

## Anti-Patterns

Never:

- Add fake personal stories
- Exaggerate certainty without evidence
- Change factual claims merely to improve style
{_bullet_list(["- " + a for a in anti_patterns if a])}

## Content Preservation Rules

{numbered}

## Transformation Rules

{numbered_t}

## Positive Examples

{_examples_block(positive_examples)}

## Negative Examples

{_examples_block(negative_examples, with_reason=True)}

## Context Adaptation

### Social Post

- Open strong, keep it short, one central insight

### Long-form Article

- Preserve argument order, keep examples, maintain citations

### Email

- State the purpose early, keep requests explicit

## Evaluation Rubric

Score each output from 1 to 5:

- Meaning preservation
- Voice consistency
- Sentence rhythm
- Vocabulary match
- Structural match
- Absence of forbidden patterns
"""
