"""Persona registry: scan, index, search."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .loader import load_persona_file
from .models import Persona

PERSONA_GLOB = "*.md"

_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class PersonaRegistry:
    """Indexes all personas under a root directory."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._by_id: Dict[str, Persona] = {}
        self._load_all()

    def _load_all(self) -> None:
        for path in sorted(self.root.glob(f"**/{PERSONA_GLOB}")):
            try:
                persona = load_persona_file(path)
            except Exception:
                continue
            if not persona.id:
                continue
            self._by_id[persona.id] = persona

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterable[Persona]:
        return iter(self._by_id.values())

    def get(self, persona_id: str) -> Optional[Persona]:
        return self._by_id.get(persona_id)

    def require(self, persona_id: str) -> Persona:
        persona = self.get(persona_id)
        if persona is None:
            raise KeyError(f"Persona not found: {persona_id}")
        return persona

    def list(self, category: Optional[str] = None, tag: Optional[str] = None,
             query: Optional[str] = None) -> List[Persona]:
        results = list(self._by_id.values())
        if category:
            results = [p for p in results if p.category == category]
        if tag:
            results = [p for p in results if tag in p.tags]
        if query:
            q = query.lower()
            results = [
                p for p in results
                if q in p.id.lower()
                or q in p.name.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.tags)
            ]
        results.sort(key=lambda p: (p.category, p.id))
        return results

    def categories(self) -> List[str]:
        seen: List[str] = []
        for p in self._by_id.values():
            if p.category not in seen:
                seen.append(p.category)
        return sorted(seen)

    def tags(self) -> List[str]:
        seen: List[str] = []
        for p in self._by_id.values():
            for t in p.tags:
                if t not in seen:
                    seen.append(t)
        return sorted(seen)

    def build_index(self, out_personas: Path, out_registry: Path) -> Dict[str, object]:
        """Write dist/personas.json (full) and dist/registry.json (metadata index)."""
        personas = [p.model_dump() for p in self._by_id.values()]
        registry = {
            "generated_at": None,
            "count": len(personas),
            "categories": self.categories(),
            "tags": self.tags(),
            "personas": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "category": p.category,
                    "emoji": p.emoji,
                    "languages": p.languages,
                    "tags": p.tags,
                    "source_type": p.source_type,
                    "version": p.version,
                    "style_strength_default": p.style_strength_default,
                }
                for p in self._by_id.values()
            ],
        }
        out_personas.parent.mkdir(parents=True, exist_ok=True)
        out_registry.parent.mkdir(parents=True, exist_ok=True)
        out_personas.write_text(json.dumps(personas, indent=2, ensure_ascii=False), encoding="utf-8")
        out_registry.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
        return registry


def validate_persona_id(persona_id: str) -> bool:
    return bool(_ID_RE.match(persona_id))


def normalize_id(name: str) -> str:
    """Turn 'Pragmatic Founder' -> 'pragmatic-founder'."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)
