#!/usr/bin/env python3
"""Lint personas against PERSONA_SPEC.md.

Usage:
    python scripts/lint-personas.py                      # all personas
    python scripts/lint-personas.py personas/<cat>/<id>.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.models import TONE_KEYS  # noqa: E402
from persona_lib.registry import validate_persona_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = ROOT / "personas"
CATEGORIES = {c["id"] for c in json.loads((ROOT / "categories.json").read_text())["categories"]}

REQUIRED_FRONTMATTER = ["id", "name", "description", "category", "language", "emoji",
                        "version", "author", "license", "source_type"]
REQUIRED_SECTIONS = [
    "identity", "perspective", "voice summary", "tone dimensions", "sentence style",
    "paragraph style", "vocabulary", "rhetorical patterns", "signature moves",
    "anti-patterns", "content preservation rules", "transformation rules",
    "positive examples", "negative examples", "context adaptation", "evaluation rubric",
]
SOURCE_TYPES = {"archetype", "user-created", "sample-derived", "brand", "inspired"}


def lint_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        return ["missing frontmatter delimiter"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return ["unterminated frontmatter"]

    import yaml
    try:
        front = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        return [f"frontmatter YAML error: {exc}"]
    if not isinstance(front, dict):
        return ["frontmatter is not a mapping"]

    pid = str(front.get("id", ""))
    if pid != path.stem:
        errors.append(f"frontmatter id '{pid}' != filename '{path.stem}'")
    if not validate_persona_id(pid):
        errors.append(f"invalid id format: '{pid}'")
    for key in REQUIRED_FRONTMATTER:
        if key not in front:
            errors.append(f"missing frontmatter key: {key}")
    if len(str(front.get("description", ""))) > 120:
        errors.append(f"description too long ({len(str(front.get('description', '')))} > 120 chars)")
    category = str(front.get("category", ""))
    if category not in CATEGORIES:
        errors.append(f"unknown category: '{category}' (valid: {sorted(CATEGORIES)})")
    stype = str(front.get("source_type", ""))
    if stype not in SOURCE_TYPES:
        errors.append(f"invalid source_type: '{stype}'")
    if stype == "inspired" and not front.get("disclaimer"):
        errors.append("source_type=inspired requires disclaimer")
    version = str(front.get("version", ""))
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        errors.append(f"invalid version: '{version}'")
    langs = front.get("language") or front.get("languages") or []
    if not isinstance(langs, list) or not langs:
        errors.append("language must be a non-empty list")

    body = "\n".join(lines[end + 1:])
    lower = body.lower()
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in lower:
            errors.append(f"missing section: ## {section}")

    tone_block = _section(body, "tone dimensions")
    tone_keys_found = set()
    for m in re.finditer(r"^\s*[-*]\s*(.+?):\s*([0-1](?:\.\d+)?|1\.0?|0\.0?)\s*$", tone_block, re.MULTILINE):
        label = m.group(1).strip().lower()
        tone_keys_found.add(label)
        val = float(m.group(2))
        if not (0.0 <= val <= 1.0):
            errors.append(f"tone '{label}' out of range: {val}")
    expected = {k.replace("_", " ") for k in TONE_KEYS}
    missing = expected - tone_keys_found
    if missing:
        errors.append(f"tone dimensions missing: {sorted(missing)} (found: {sorted(tone_keys_found)})")

    pos_block = _section(body, "positive examples")
    if "Input:" not in pos_block:
        errors.append("positive examples: no 'Input:' field")
    if "Output:" not in pos_block:
        errors.append("positive examples: no 'Output:' field")

    neg_block = _section(body, "negative examples")
    if "Input:" not in neg_block:
        errors.append("negative examples: no 'Input:' field")

    if "### Prefer" not in _section(body, "vocabulary"):
        errors.append("vocabulary missing '### Prefer'")
    if "### Avoid" not in _section(body, "vocabulary"):
        errors.append("vocabulary missing '### Avoid'")

    if "Never:" not in _section(body, "anti-patterns"):
        errors.append("anti-patterns must contain a 'Never:' list")

    return errors


def _section(body: str, name: str) -> str:
    pattern = re.compile(rf"^## {re.escape(name)}\s*$", re.MULTILINE | re.IGNORECASE)
    m = pattern.search(body)
    if not m:
        return ""
    start = m.end()
    nxt = re.compile(r"^## ", re.MULTILINE).search(body, start)
    return body[start: nxt.start() if nxt else len(body)]


def main() -> int:
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args]
    else:
        files = sorted(PERSONAS_DIR.glob("**/*.md"))
    failed = 0
    total = 0
    for path in files:
        total += 1
        errors = lint_file(path)
        if errors:
            failed += 1
            print(f"FAIL {path.relative_to(ROOT)}")
            for e in errors:
                print(f"     - {e}")
        else:
            print(f"ok   {path.relative_to(ROOT)}")
    print(f"\n{total - failed}/{total} personas passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
