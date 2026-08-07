"""Persona consistency: tone ranges, uniqueness, sections, example fidelity."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.registry import PersonaRegistry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
registry = PersonaRegistry(ROOT / "personas")


def test_unique_ids():
    ids = [p.id for p in registry]
    assert len(ids) == len(set(ids))


def test_tone_dimensions_in_range():
    for persona in registry:
        for key, value in persona.profile.tone.as_dict().items():
            assert 0.0 <= value <= 1.0, f"{persona.id}.{key} = {value}"


def test_tone_dimensions_are_diverse():
    vectors = [p.profile.tone.as_dict() for p in registry]
    keys = list(vectors[0].keys())
    for k in keys:
        vals = [v[k] for v in vectors]
        assert max(vals) - min(vals) > 0.3, f"dimension {k} lacks spread: {vals}"


def test_personas_are_pairwise_distinct():
    vectors = [(p.id, p.profile.tone.as_dict()) for p in registry]
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            a, b = vectors[i], vectors[j]
            diff = [abs(a[1][k] - b[1][k]) for k in a[1]]
            assert max(diff) >= 0.1, f"{a[0]} and {b[0]} have near-identical tone"


def test_required_content():
    for persona in registry:
        assert persona.profile.voice_summary, persona.id
        assert len(persona.profile.preferred_vocabulary) >= 3, persona.id
        assert len(persona.profile.avoided_vocabulary) >= 3, persona.id
        assert len(persona.profile.positive_examples) >= 2, persona.id
        assert len(persona.profile.negative_examples) >= 1, persona.id
        assert len(persona.content_preservation_rules) >= 4, persona.id
        assert len(persona.transformation_rules) >= 3, persona.id
        assert any("factual claim" in r.lower() for r in persona.content_preservation_rules), persona.id
        assert any("unsupported" in r.lower() for r in persona.content_preservation_rules), persona.id
        assert any(k in a.lower() for a in persona.profile.anti_patterns for k in ("personal", "storie", "fake", "fabricat")), persona.id


def test_source_types_valid():
    valid = {"archetype", "user-created", "sample-derived", "brand", "inspired"}
    for persona in registry:
        assert persona.source_type in valid, persona.id


def test_no_real_person_names_in_ids():
    banned = ["steve", "jobs", "musk", "paul", "graham", "gates", "bezos"]
    for persona in registry:
        lower = persona.id.lower()
        assert not any(b in lower for b in banned), persona.id
