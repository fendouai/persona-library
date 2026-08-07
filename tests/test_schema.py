"""Schema validation: all personas load and pass the lint script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from persona_lib.loader import load_persona_file  # noqa: E402
from persona_lib.models import Persona  # noqa: E402
from persona_lib.registry import PersonaRegistry  # noqa: E402
from lint_personas import lint_file  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = ROOT / "personas"

PERSONA_FILES = sorted(PERSONAS_DIR.glob("**/*.md"))


def test_first_batch_has_20_personas():
    assert len(PERSONA_FILES) >= 20


def test_all_personas_load_into_model():
    for path in PERSONA_FILES:
        persona = load_persona_file(path)
        assert isinstance(persona, Persona), path
        assert persona.id == path.stem, f"{path}: id != filename"


def test_all_personas_pass_lint():
    failures = []
    for path in PERSONA_FILES:
        errors = lint_file(path)
        if errors:
            failures.append((path, errors))
    assert not failures, "\n".join(f"{p}: {e}" for p, e in failures)


def test_all_personas_valid_against_json_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schemas" / "persona.schema.json").read_text())
    profile_schema = json.loads((ROOT / "schemas" / "style-profile.schema.json").read_text())
    from referencing import Registry, Resource
    registry = Registry().with_resource(
        "https://persona-library.dev/schemas/style-profile.schema.json",
        Resource.from_contents(profile_schema),
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)
    for path in PERSONA_FILES:
        persona = load_persona_file(path)
        validator.validate(persona.model_dump(mode="json"))


def test_registry_indexes_all():
    registry = PersonaRegistry(PERSONAS_DIR)
    assert len(registry) == len(PERSONA_FILES)
    assert registry.get("pragmatic-founder") is not None
    with pytest.raises(KeyError):
        registry.require("does-not-exist")


def test_categories_are_valid():
    categories = {c["id"] for c in json.loads((ROOT / "categories.json").read_text())["categories"]}
    registry = PersonaRegistry(PERSONAS_DIR)
    for persona in registry:
        assert persona.category in categories, persona.id
