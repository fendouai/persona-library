"""Persona mixing: blend weighted personas into one temporary profile."""

from __future__ import annotations

from typing import Dict, List, Tuple

from .models import Persona, StyleProfile, ToneDimensions

TONE_KEYS = ["formality", "warmth", "confidence", "humor", "emotional_intensity", "directness"]


def normalize_weights(entries: List[Tuple[Persona, float]]) -> List[Tuple[Persona, float]]:
    total = sum(max(0.0, w) for _, w in entries)
    if total <= 0:
        raise ValueError("Weights must sum to a positive value")
    return [(p, max(0.0, w) / total) for p, w in entries]


def mix_profiles(entries: List[Tuple[Persona, float]]) -> StyleProfile:
    """Weighted-average tone + union of patterns/vocabulary ranked by weight."""
    entries = normalize_weights(entries)

    tone_values: Dict[str, float] = {k: 0.0 for k in TONE_KEYS}
    for persona, weight in entries:
        t = persona.profile.tone.as_dict()
        for k in TONE_KEYS:
            tone_values[k] += t[k] * weight

    def union_by_weight(key: str) -> List[str]:
        counts: Dict[str, float] = {}
        for persona, weight in entries:
            for item in getattr(persona.profile, key):
                counts[item] = counts.get(item, 0.0) + weight
        return [item for item, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)]

    examples = [ex for p, _ in entries for ex in p.profile.positive_examples]
    neg_examples = [ex for p, _ in entries for ex in p.profile.negative_examples]

    return StyleProfile(
        voice_summary=" + ".join(p.profile.voice_summary for p, _ in entries if p.profile.voice_summary)[:500],
        tone=ToneDimensions(**tone_values),
        sentence_patterns=union_by_weight("sentence_patterns"),
        paragraph_patterns=union_by_weight("paragraph_patterns"),
        rhetorical_patterns=union_by_weight("rhetorical_patterns"),
        preferred_vocabulary=union_by_weight("preferred_vocabulary"),
        avoided_vocabulary=union_by_weight("avoided_vocabulary"),
        signature_moves=union_by_weight("signature_moves"),
        anti_patterns=union_by_weight("anti_patterns"),
        positive_examples=examples[:4],
        negative_examples=neg_examples[:2],
    )


def mix_personas(entries: List[Tuple[Persona, float]], blend_name: str = "Blended Persona") -> Persona:
    """Create a temporary Persona from blended profiles (not written to disk)."""
    profile = mix_profiles(entries)
    return Persona(
        id="blend",
        name=blend_name,
        description="Weighted blend of " + ", ".join(p.name for p, _ in entries),
        category="custom",
        languages=list(dict.fromkeys(lang for p, _ in entries for lang in p.languages)),
        emoji="🎨",
        version="0.1.0",
        author="user",
        tags=["blended"],
        source_type="user-created",
        style_strength_default=sum(p.style_strength_default * w for p, w in normalize_weights(entries)),
        profile=profile,
        content_preservation_rules=list(
            dict.fromkeys(rule for p, _ in entries for rule in p.content_preservation_rules)
        ),
        transformation_rules=list(
            dict.fromkeys(rule for p, _ in entries for rule in p.transformation_rules)
        ),
        body_markdown=_render_blend_body(profile),
    )


def _render_blend_body(profile: StyleProfile) -> str:
    tone = "\n".join(f"- {k.replace('_', ' ').title()}: {getattr(profile.tone, k):.2f}" for k in TONE_KEYS)
    lines = [
        f"# Blended Persona\n",
        "## Identity\n\nYou communicate in a style that blends the weighted mix of the selected personas.\n",
        "## Voice Summary\n\n" + (profile.voice_summary or "Blended voice.") + "\n",
        "## Tone Dimensions\n\n" + tone + "\n",
        "## Sentence Style\n\n" + _bullets(profile.sentence_patterns) + "\n",
        "## Paragraph Style\n\n" + _bullets(profile.paragraph_patterns) + "\n",
        "## Vocabulary\n\n### Prefer\n\n" + _bullets(profile.preferred_vocabulary) + "\n\n### Avoid\n\n" + _bullets(profile.avoided_vocabulary) + "\n",
        "## Rhetorical Patterns\n\n" + _bullets(profile.rhetorical_patterns) + "\n",
        "## Signature Moves\n\n" + _bullets(profile.signature_moves) + "\n",
        "## Anti-Patterns\n\nNever:\n\n" + _bullets(profile.anti_patterns) + "\n",
    ]
    return "\n".join(lines).strip()


def _bullets(items: List[str]) -> str:
    return "\n".join(f"- {i}" for i in items)
