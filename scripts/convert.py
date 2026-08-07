#!/usr/bin/env python3
"""Convert personas between formats (markdown <-> json / yaml / toml).

Usage:
    python scripts/convert.py personas/archetypes/pragmatic-founder.md --format json
    python scripts/convert.py personas/archetypes/pragmatic-founder.md --format yaml
    python scripts/convert.py personas/archetypes/pragmatic-founder.md --format toml
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.loader import load_persona_file  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3 or "--format" not in args:
        print(__doc__)
        return 1
    path = Path(args[0])
    fmt = args[args.index("--format") + 1]
    persona = load_persona_file(path)
    data = persona.model_dump(mode="json")
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif fmt == "yaml":
        import yaml
        print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    elif fmt == "toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        print(_to_toml(data))
    else:
        print(f"Unknown format: {fmt} (json | yaml | toml)")
        return 1
    return 0


def _to_toml(data: dict) -> str:
    out = [f"id = {_q(data['id'])}", f"name = {_q(data['name'])}",
           f"category = {_q(data['category'])}", f"version = {_q(data['version'])}"]
    out.append("profile = " + _inline(data.get("profile", {})))
    return "\n".join(out)


def _q(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _inline(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    sys.exit(main())
