#!/usr/bin/env python3
"""Check a persona against existing personas for meaningful difference.

Usage:
    python scripts/check-originality.py personas/founders/my-new-persona.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.loader import load_persona_file  # noqa: E402
from persona_lib.registry import PersonaRegistry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIMILARITY_THRESHOLD = 0.6  # above this, flag as too similar


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def tone_distance(a: dict, b: dict) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 1.0
    dist = sum(abs(float(a[k]) - float(b[k])) for k in keys) / len(keys)
    return dist  # 0 = identical, 1 = maximally different


def similarity(target, other) -> dict:
    vocab = jaccard(
        set(target.profile.preferred_vocabulary) | set(target.profile.avoided_vocabulary),
        set(other.profile.preferred_vocabulary) | set(other.profile.avoided_vocabulary),
    )
    tone = 1.0 - tone_distance(target.profile.tone.as_dict(), other.profile.tone.as_dict())
    return {"id": other.id, "vocab_similarity": vocab, "tone_similarity": tone}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python scripts/check-originality.py <persona-file>")
        return 1
    target = load_persona_file(Path(args[0]))
    registry = PersonaRegistry(ROOT / "personas")
    if target.id in registry._by_id:
        registry._by_id.pop(target.id)

    results = sorted(
        (similarity(target, other) for other in registry if other.id != target.id),
        key=lambda r: r["vocab_similarity"] + r["tone_similarity"],
        reverse=True,
    )[:5]

    print(f"Most similar to '{target.id}':")
    flagged = False
    for r in results:
        combined = r["vocab_similarity"] * 0.5 + r["tone_similarity"] * 0.5
        flag = "  <-- TOO SIMILAR" if combined >= SIMILARITY_THRESHOLD else ""
        if flag:
            flagged = True
        print(f"  {r['id']:<32} vocab={r['vocab_similarity']:.2f} "
              f"tone={r['tone_similarity']:.2f} combined={combined:.2f}{flag}")
    if not flagged:
        print("\nOK: sufficiently distinct from existing personas.")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
