#!/usr/bin/env python3
"""Deterministic consistency test for a persona (no LLM required).

Verifies structure and checks the persona's own positive examples:
facts (numbers, entities) present in Input must survive in Output.

Usage:
    python scripts/test_persona.py <persona-id-or-file>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.loader import load_persona_file  # noqa: E402
from persona_lib.registry import PersonaRegistry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NUMBERS = re.compile(r"\d[\d,.]*")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python scripts/test_persona.py <persona-id-or-file>")
        return 1
    arg = args[0]
    path = Path(arg)
    persona = load_persona_file(path) if path.exists() else PersonaRegistry(ROOT / "personas").require(arg)

    failures = []
    checks = {
        "id": bool(persona.id),
        "name": bool(persona.name),
        "description": bool(persona.description),
        "tone dimensions": all(
            0.0 <= v <= 1.0 for v in persona.profile.tone.as_dict().values()
        ),
        "preferred vocab": len(persona.profile.preferred_vocabulary) >= 3,
        "avoided vocab": len(persona.profile.avoided_vocabulary) >= 3,
        "positive examples": len(persona.profile.positive_examples) >= 2,
        "negative examples": len(persona.profile.negative_examples) >= 1,
        "preservation rules": len(persona.content_preservation_rules) >= 4,
        "transformation rules": len(persona.transformation_rules) >= 3,
        "anti-patterns": len(persona.profile.anti_patterns) >= 3,
        "signature moves": len(persona.profile.signature_moves) >= 3,
    }
    for name, ok in checks.items():
        status = "ok  " if ok else "FAIL"
        print(f"  {status} {name}")
        if not ok:
            failures.append(name)

    print("\n  fidelity checks on positive examples:")
    example_failures = 0
    for i, ex in enumerate(persona.profile.positive_examples, start=1):
        inp_numbers = set(NUMBERS.findall(ex.input))
        out_numbers = set(NUMBERS.findall(ex.output))
        lost = inp_numbers - out_numbers
        if lost:
            example_failures += 1
            print(f"  FAIL example {i}: numbers lost in output: {sorted(lost)}")
        else:
            print(f"  ok   example {i}: numbers preserved ({sorted(inp_numbers) if inp_numbers else 'n/a'})")
    if example_failures:
        failures.append("example fidelity")

    print(f"\nResult: {'FAIL' if failures else 'PASS'} ({persona.id})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
