"""Quality evaluation: content fidelity + style match + readability + platform fit.

Final Score = 0.45 * meaning + 0.30 * style + 0.15 * readability + 0.10 * platform
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .config import LLMConfig, default_config
from .llm import LLMClient
from .models import Persona, RewriteScore

WEIGHTS = {
    "meaning_preservation": 0.45,
    "style_match": 0.30,
    "readability": 0.15,
    "platform_fit": 0.10,
}

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

_NUMBERS_RE = re.compile(r"\b\d[\d,.]*\b")


def combine_scores(meaning: float, style: float, readability: float, platform_fit: float) -> RewriteScore:
    """Deterministic weighted combination (0.45 / 0.30 / 0.15 / 0.10)."""
    clamp = lambda v: max(0.0, min(1.0, float(v)))
    meaning, style, readability, platform_fit = (
        clamp(meaning), clamp(style), clamp(readability), clamp(platform_fit)
    )
    final = (
        0.45 * meaning + 0.30 * style + 0.15 * readability + 0.10 * platform_fit
    )
    return RewriteScore(
        meaning_preservation=round(meaning, 3),
        style_match=round(style, 3),
        readability=round(readability, 3),
        platform_fit=round(platform_fit, 3),
        final_score=round(clamp(final), 3),
    )


def heuristic_fidelity(original: str, rewritten: str, target_ratio: float = 0.2) -> RewriteScore:
    """Deterministic fallback score when no LLM is available.

    Checks number preservation, length ratio, and vocabulary signal.
    """
    orig_numbers = set(_NUMBERS_RE.findall(original))
    new_numbers = set(_NUMBERS_RE.findall(rewritten))
    if orig_numbers:
        number_hits = len(orig_numbers & new_numbers) / len(orig_numbers)
    else:
        number_hits = 1.0

    def words(s: str) -> int:
        return len(s.split())

    ow, nw = max(1, words(original)), max(1, words(rewritten))
    ratio = nw / ow
    length_score = 1.0 if abs(ratio - 1.0) <= target_ratio else max(0.0, 1.0 - abs(ratio - 1.0) * 3)

    meaning = round(0.7 * number_hits + 0.3 * length_score, 3)
    style = round(min(1.0, 0.4 + 0.3 * number_hits), 3)
    readability = round(max(0.3, 1.0 - abs(ratio - 1.0)), 3)
    platform_fit = 0.8
    return combine_scores(meaning, style, readability, platform_fit)


def evaluate_rewrite(
    original: str,
    rewritten: str,
    persona: Persona,
    platform: str,
    client: Optional[LLMClient] = None,
    config: Optional[LLMConfig] = None,
) -> RewriteScore:
    """Two LLM judges (style + fidelity) merged deterministically."""
    llm = client or LLMClient(config or default_config())
    style_prompt = (PROMPTS_DIR / "evaluate-style.md").read_text(encoding="utf-8")
    fidelity_prompt = (PROMPTS_DIR / "evaluate-fidelity.md").read_text(encoding="utf-8")

    style_sys, style_usr = style_prompt, (
        f"Persona:\n{persona.render_runtime_prompt()}\n\n"
        f"Original text:\n{original}\n\n"
        f"Rewritten text:\n{rewritten}\n\n"
        f"Target platform: {platform}\n"
    )
    fid_sys, fid_usr = fidelity_prompt, (
        f"Original text:\n{original}\n\n"
        f"Rewritten text:\n{rewritten}\n"
    )

    try:
        style_data = llm.chat_json(style_sys, style_usr, temperature=0.2)
        fid_data = llm.chat_json(fid_sys, fid_usr, temperature=0.2)
    except Exception:
        return heuristic_fidelity(original, rewritten)

    def grab(data: dict, key: str, default: float) -> float:
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return default

    overfitting = grab(style_data, "overfitting", 0.0)
    style_match = grab(style_data, "style_match", 0.5) * (1.0 - 0.5 * overfitting)
    readability = grab(style_data, "readability", 0.5)
    platform_fit = grab(style_data, "platform_fit", 0.5)
    meaning = grab(fid_data, "meaning_preservation", 0.5)
    fact = grab(fid_data, "fact_integrity", 0.5)
    meaning = min(meaning, fact)
    return combine_scores(meaning, style_match, readability, platform_fit)
