"""Export and install personas to other tools (Claude, Codex, OpenCode, JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import Persona


def export_json(persona: Persona) -> Dict:
    return persona.model_dump(mode="json")


def export_claude(persona: Persona) -> str:
    """Claude (Claude Code / Claude.ai custom instructions): prompt-only markdown."""
    return f"# {persona.name}\n\n{persona.body_markdown}\n"


def export_codex(persona: Persona) -> str:
    """Codex: frontmatter name/description -> agent header, body -> developer instructions."""
    header = (
        f"# {persona.name}\n\n"
        f"**Description**: {persona.description}\n"
        f"**Category**: {persona.category}\n"
        f"**Tags**: {', '.join(persona.tags)}\n"
        f"**Version**: {persona.version}\n\n"
    )
    return header + persona.body_markdown + "\n"


def export_opencode(persona: Persona) -> str:
    """OpenCode: YAML-ish frontmatter + instructions, ready for agent config."""
    front = {
        "name": persona.name,
        "description": persona.description,
        "emoji": persona.emoji,
        "tags": persona.tags,
        "model": "inherit",
    }
    return (
        f"```yaml\n{json.dumps(front, ensure_ascii=False, indent=2)}\n```\n\n"
        f"# {persona.name}\n\n{persona.body_markdown}\n"
    )


EXPORTERS = {
    "json": export_json,
    "claude": export_claude,
    "codex": export_codex,
    "opencode": export_opencode,
}

INSTALL_DIRS = {
    "claude": ".claude/personas",
    "codex": ".codex/personas",
    "opencode": ".opencode/personas",
}


def export_persona(persona: Persona, fmt: str = "json") -> str:
    if fmt not in EXPORTERS:
        raise ValueError(f"Unknown export format: {fmt}. Available: {', '.join(EXPORTERS)}")
    if fmt == "json":
        return json.dumps(export_json(persona), indent=2, ensure_ascii=False)
    return str(EXPORTERS[fmt](persona))


def install_persona(persona: Persona, tool: str, target_dir: Path) -> Path:
    """Install a persona into a tool-specific directory under target_dir."""
    if tool not in INSTALL_DIRS:
        raise ValueError(f"Unknown tool: {tool}. Available: {', '.join(INSTALL_DIRS)}")
    fmt = "claude" if tool == "claude" else ("codex" if tool == "codex" else "opencode")
    dest = target_dir / INSTALL_DIRS[tool]
    dest.mkdir(parents=True, exist_ok=True)
    filename = f"{persona.id}.md"
    if fmt == "json":
        filename = f"{persona.id}.json"
    out = dest / filename
    out.write_text(export_persona(persona, fmt), encoding="utf-8")
    return out
