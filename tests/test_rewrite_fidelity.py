"""Rewrite pipeline internals: scoring weights, heuristic fidelity, blending."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from persona_lib.blender import mix_personas, mix_profiles, normalize_weights  # noqa: E402
from persona_lib.evaluator import combine_scores, heuristic_fidelity  # noqa: E402
from persona_lib.loader import load_persona_file  # noqa: E402
from persona_lib.models import RewriteRequest, ToneDimensions  # noqa: E402
from persona_lib.registry import PersonaRegistry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
registry = PersonaRegistry(ROOT / "personas")


def test_combine_scores_weights():
    score = combine_scores(1.0, 1.0, 1.0, 1.0)
    assert score.final_score == 1.0
    score = combine_scores(0.0, 1.0, 1.0, 1.0)
    assert score.final_score == pytest_approx(0.55)
    score = combine_scores(1.0, 0.0, 1.0, 1.0)
    assert score.final_score == pytest_approx(0.70)


def pytest_approx(value: float) -> float:
    return round(value, 3)


def test_combine_scores_clamps():
    score = combine_scores(2.0, -1.0, 0.5, 0.5)
    assert 0.0 <= score.final_score <= 1.0


def test_meaning_has_highest_weight():
    base = combine_scores(1.0, 1.0, 1.0, 1.0).final_score
    meaning_drop = base - combine_scores(0.0, 1.0, 1.0, 1.0).final_score
    style_drop = base - combine_scores(1.0, 0.0, 1.0, 1.0).final_score
    assert meaning_drop > style_drop


def test_heuristic_fidelity_detects_number_changes():
    original = "We shipped 12 features to 340 customers in Q3."
    kept = heuristic_fidelity(original, "We delivered 12 features to 340 customers this quarter.")
    changed = heuristic_fidelity(original, "We delivered 100 features to 2 customers.")
    assert kept.meaning_preservation > changed.meaning_preservation
    assert changed.meaning_preservation < 0.5


def test_heuristic_fidelity_length():
    words = "the quick brown fox jumps over the lazy dog and keeps moving " * 2
    short = heuristic_fidelity(words, words + " adding a few more words here.")
    long = heuristic_fidelity(words, " ".join(["extra"] * 300))
    assert short.readability > long.readability


def test_normalize_weights():
    entries = [(p, 1.0) for p in [registry.get("pragmatic-founder")]]
    normalized = normalize_weights(entries + [(registry.get("warm-educator"), 3.0)])
    assert sum(w for _, w in normalized) == pytest_approx(1.0)
    assert normalized[1][1] == pytest_approx(0.75)


def test_mix_profiles_weighted_tone():
    a = registry.require("pragmatic-founder")
    b = registry.require("warm-educator")
    blended = mix_profiles([(a, 0.7), (b, 0.3)])
    expected_warmth = a.profile.tone.warmth * 0.7 + b.profile.tone.warmth * 0.3
    assert abs(blended.tone.warmth - expected_warmth) < 0.01
    assert blended.tone.directness == pytest_approx(
        a.profile.tone.directness * 0.7 + b.profile.tone.directness * 0.3
    )


def test_mix_personas_builds_runtime_prompt():
    a = registry.require("pragmatic-founder")
    b = registry.require("warm-educator")
    blended = mix_personas([(a, 0.7), (b, 0.3)])
    prompt = blended.render_runtime_prompt(0.8)
    assert "# Blended Persona" in prompt or blended.name in prompt
    assert "Style strength: 0.80" in prompt


def test_loader_parses_examples():
    persona = load_persona_file(ROOT / "personas" / "archetypes" / "pragmatic-founder.md")
    assert len(persona.profile.positive_examples) >= 3
    first = persona.profile.positive_examples[0]
    assert first.input and first.output
    neg = persona.profile.negative_examples[0]
    assert neg.input and neg.reason


def test_rewrite_request_validation():
    req = RewriteRequest(persona_id="x", text="hi")
    assert req.style_strength == 0.7
    assert req.candidate_count == 3


def test_tone_weighted_average():
    a = ToneDimensions(formality=1.0, warmth=0.0, confidence=0.5, humor=0.5,
                       emotional_intensity=0.5, directness=0.5)
    b = ToneDimensions(formality=0.0, warmth=1.0, confidence=0.5, humor=0.5,
                       emotional_intensity=0.5, directness=0.5)
    blended = a.weighted_average(b, 0.5)
    assert blended.formality == 0.5
    assert blended.warmth == 0.5
