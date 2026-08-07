#!/usr/bin/env python3
"""Build dist/personas.json and dist/registry.json from the personas directory."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.registry import PersonaRegistry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    registry = PersonaRegistry(ROOT / "personas")
    out_personas = ROOT / "dist" / "personas.json"
    out_registry = ROOT / "dist" / "registry.json"
    index = registry.build_index(out_personas, out_registry)
    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    out_registry.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Indexed {index['count']} personas across {len(index['categories'])} categories")
    print(f"  -> {out_personas.relative_to(ROOT)}")
    print(f"  -> {out_registry.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
