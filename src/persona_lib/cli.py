"""Persona Library CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer

from .blender import mix_personas
from .config import default_config
from .exporter import export_persona, install_persona
from .extractor import extract_persona
from .llm import LLMError
from .models import MixRequest, RewriteRequest
from .registry import PersonaRegistry, normalize_id
from .rewriter import Rewriter

app = typer.Typer(name="persona", help="Create, manage, mix, and apply writing personas.")

ROOT = Path(__file__).resolve().parent.parent.parent
PERSONAS_DIR = ROOT / "personas"


def _registry() -> PersonaRegistry:
    return PersonaRegistry(PERSONAS_DIR)


@app.command(name="list")
def list_personas(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search id/name/description/tags"),
):
    """List available personas."""
    registry = _registry()
    rows = registry.list(category=category, tag=tag, query=query)
    if not rows:
        typer.echo("No personas found.")
        return
    for p in rows:
        emoji = p.emoji or "•"
        typer.echo(f"{emoji} {p.id:<32} [{p.category:<12}] {p.name} — {p.description}")


@app.command()
def show(persona_id: str):
    """Show a persona's metadata and style profile."""
    persona = _registry().require(persona_id)
    typer.echo(f"# {persona.emoji or ''} {persona.name}  ({persona.id})")
    typer.echo(f"Category: {persona.category} | Version: {persona.version} | "
               f"Source: {persona.source_type} | Langs: {', '.join(persona.languages)}")
    typer.echo(f"Description: {persona.description}")
    typer.echo(f"Tags: {', '.join(persona.tags)}")
    typer.echo("\nTone Dimensions:")
    for k, v in persona.profile.tone.as_dict().items():
        typer.echo(f"  {k}: {v:.2f}")
    typer.echo(f"\nVoice: {persona.profile.voice_summary}")
    typer.echo(f"Preferred vocab ({len(persona.profile.preferred_vocabulary)}): "
               f"{', '.join(persona.profile.preferred_vocabulary[:10])}")
    typer.echo(f"Avoided vocab ({len(persona.profile.avoided_vocabulary)}): "
               f"{', '.join(persona.profile.avoided_vocabulary[:10])}")
    if persona.path:
        typer.echo(f"\nFile: {persona.path}")


@app.command()
def extract(
    samples_file: Path = typer.Option(..., "--from", "-f", help="File with sample texts"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Persona name"),
    save: bool = typer.Option(False, "--save", help="Save draft to personas/custom/"),
):
    """Create a persona draft from author sample texts."""
    text = samples_file.read_text(encoding="utf-8")
    samples = [s.strip() for s in text.split("\n---\n") if s.strip()]
    if not samples:
        samples = [text]
    result = extract_persona(samples, name=name)
    typer.echo(f"Draft persona: {result.persona_id} (confidence {result.confidence.overall:.2f})")
    for w in result.confidence.warnings:
        typer.echo(f"  warning: {w}")
    typer.echo("\n" + result.persona.render_runtime_prompt()[:4000])
    if save:
        dest = PERSONAS_DIR / "custom" / f"{result.persona_id}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_persona_to_markdown(result.persona), encoding="utf-8")
        typer.echo(f"\nSaved: {dest}")


@app.command(name="create")
def create_interactive():
    """Manually create a persona with interactive prompts."""
    name = typer.prompt("Persona name")
    category = typer.prompt("Category", default="custom")
    description = typer.prompt("One-line description", default="")
    voice = typer.prompt("Voice summary (comma-separated adjectives)", default="")
    strength = float(typer.prompt("Default style strength (0-1)", default="0.7"))
    persona_id = normalize_id(name)
    md = _manual_markdown(persona_id, name, category, description, voice, strength)
    dest = PERSONAS_DIR / "custom" / f"{persona_id}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(md, encoding="utf-8")
    typer.echo(f"Created: {dest}")


@app.command()
def rewrite(
    input_file: Path,
    persona_id: str = typer.Option(..., "--persona", "-p", help="Persona id"),
    strength: float = typer.Option(0.7, "--strength", "-s", min=0.0, max=1.0),
    platform: str = typer.Option("generic", "--platform", help="x | linkedin | email | blog | newsletter"),
    candidates: int = typer.Option(3, "--candidates", min=1, max=5),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write result to file"),
    no_evaluate: bool = typer.Option(False, "--no-evaluate", help="Skip scoring"),
):
    """Rewrite a text file using a persona."""
    registry = _registry()
    text = input_file.read_text(encoding="utf-8")
    request = RewriteRequest(
        persona_id=persona_id,
        text=text,
        style_strength=strength,
        platform=platform,
        candidate_count=candidates,
    )
    rewriter = Rewriter(registry, default_config())
    result = rewriter.rewrite(request, evaluate=not no_evaluate)
    typer.echo(result.output)
    typer.echo("\n--- scores ---")
    typer.echo(result.scores.model_dump_json(indent=2))
    if output:
        output.write_text(result.output + "\n", encoding="utf-8")
        typer.echo(f"\nWrote: {output}")


@app.command()
def mix(
    input_file: Path,
    strength: float = typer.Option(0.7, "--strength", min=0.0, max=1.0),
    platform: str = typer.Option("generic", "--platform"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Rewrite using a mix of personas. JSON file: [{"id": "...", "weight": 0.7}, ...]"""
    registry = _registry()
    data = json.loads(input_file.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "personas" in data:
        data = data["personas"]
    if not isinstance(data, list):
        raise typer.BadParameter("mix file must be [{\"id\": ..., \"weight\": ...}, ...] or {\"personas\": [...]}")
    entries = MixRequest(personas=data).validated(registry)
    blended = mix_personas(entries)
    typer.echo(f"Blended profile of {len(entries)} personas. Tone:")
    for k, v in blended.profile.tone.as_dict().items():
        typer.echo(f"  {k}: {v:.2f}")
    original = typer.prompt("Original text to rewrite")
    request = RewriteRequest(persona=blended, text=original, style_strength=strength, platform=platform)
    result = Rewriter(registry, default_config()).rewrite(request)
    typer.echo("\n" + result.output)
    if output:
        output.write_text(result.output + "\n", encoding="utf-8")


@app.command(name="export")
def export_persona_cmd(
    persona_id: str,
    tool: str = typer.Option("json", "--tool", help="claude | codex | opencode | json"),
    format: str = typer.Option(None, "--format", help="Alias for --tool"),
):
    """Export a persona to another tool's format."""
    fmt = format or tool
    persona = _registry().require(persona_id)
    typer.echo(export_persona(persona, fmt))


@app.command()
def install(
    persona_id: str,
    tool: str = typer.Option(..., "--tool", help="claude | codex | opencode"),
    target_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Target project directory"),
):
    """Install a persona into a tool-specific directory."""
    persona = _registry().require(persona_id)
    path = install_persona(persona, tool, target_dir)
    typer.echo(f"Installed to {path}")


def _persona_to_markdown(persona) -> str:
    from .loader import parse_persona_markdown
    md = persona.body_markdown
    front = (
        f"---\nid: {persona.id}\nname: {persona.name}\ndescription: {persona.description}\n"
        f"category: {persona.category}\nlanguage:\n  - {persona.languages[0] if persona.languages else 'en'}\n"
        f"emoji: ✍️\nversion: 0.1.0\nauthor: user\nlicense: MIT\n"
        f"tags:\n  - sample-derived\nsource_type: sample-derived\nstyle_strength_default: 0.7\n---\n\n"
    )
    return front + md


def _manual_markdown(persona_id: str, name: str, category: str, description: str,
                     voice: str, strength: float) -> str:
    tone_defaults = "".join(
        f"- {k.replace('_', ' ').title()}: 0.5\n" for k in
        ["formality", "warmth", "confidence", "humor", "emotional_intensity", "directness"]
    )
    return f"""---
id: {persona_id}
name: {name}
description: {description}
category: {category}
language:
  - en
emoji: ✍️
version: 0.1.0
author: user
license: MIT
tags: []
source_type: user-created
style_strength_default: {strength}
---

# {name}

## Identity

Describe how this persona expresses itself.

## Perspective

- Describe what lenses it views content through

## Voice Summary

{voice}

## Tone Dimensions

{tone_defaults}
## Sentence Style

- Edit this list

## Paragraph Style

- Edit this list

## Vocabulary

### Prefer

- edit

### Avoid

- edit

## Rhetorical Patterns

- Edit this list

## Signature Moves

- Edit this list

## Anti-Patterns

Never:

- Add fake personal stories
- Change factual claims merely to improve style

## Content Preservation Rules

1. Preserve all factual claims
2. Preserve names, numbers, dates, links, and citations
3. Preserve the author's original position
4. Do not add unsupported facts
5. Do not remove qualifications or uncertainty

## Transformation Rules

1. Lead with the most important conclusion
2. Remove generic introductions
3. Keep the output length within ±20%

## Positive Examples

### Example 1

Input:

> ...

Output:

> ...

## Negative Examples

### Example 1

Input:

> ...

Reason:

...

## Context Adaptation

### Social Post

- ...

### Long-form Article

- ...

## Evaluation Rubric

Score each output from 1 to 5:

- Meaning preservation
- Voice consistency
- Sentence rhythm
- Vocabulary match
- Structural match
- Absence of forbidden patterns
"""


def main() -> None:
    try:
        app()
    except LLMError as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
