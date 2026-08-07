"""Three-phase rewriting pipeline:

1. content lock      — extract semantic constraints from the source text
2. persona rewrite   — generate N candidates
3. evaluate & select — score candidates, return the best
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .config import LLMConfig, default_config
from .evaluator import combine_scores, evaluate_rewrite, heuristic_fidelity
from .llm import LLMClient
from .models import (
    Persona,
    RewriteRequest,
    RewriteResult,
    RewriteScore,
    SemanticConstraints,
)
from .registry import PersonaRegistry

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

NUMBERS_RE = re.compile(r"\b\d[\d,.]*\b")


class Rewriter:
    def __init__(self, registry: PersonaRegistry, config: Optional[LLMConfig] = None):
        self.registry = registry
        self.config = config or default_config()
        self.client = LLMClient(self.config)

    # ----- phase 1: content lock -----

    def lock_content(self, text: str) -> SemanticConstraints:
        system = (
            "You are a content lock extractor. Your job is to extract every "
            "semantic invariant from a text so it can be rewritten without "
            "changing meaning."
        )
        user = (
            "Extract from the source text:\n"
            "- claims: list of factual/assertive claims (complete statements)\n"
            "- entities: proper nouns, product names, people, organizations\n"
            "- numbers: all numbers, amounts, dates, percentages, statistics\n"
            "- position: the author's stance in one sentence (or null)\n"
            "- uncertainties: qualifications, hedging, 'might/may/possibly' statements\n\n"
            f"Source text:\n{text}\n\n"
            'Return JSON: {"claims": [], "entities": [], "numbers": [], "position": null, "uncertainties": []}'
        )
        data = self.client.chat_json(system, user)
        return SemanticConstraints(
            claims=[str(c) for c in data.get("claims", [])],
            entities=[str(e) for e in data.get("entities", [])],
            numbers=[str(n) for n in data.get("numbers", [])],
            position=data.get("position"),
            uncertainties=[str(u) for u in data.get("uncertainties", [])],
        )

    def lock_content_local(self, text: str) -> SemanticConstraints:
        """Deterministic fallback: capture numbers and obvious entities."""
        return SemanticConstraints(
            claims=[], entities=[], numbers=list(dict.fromkeys(NUMBERS_RE.findall(text))),
            position=None, uncertainties=[],
        )

    # ----- phase 2: rewrite -----

    def _render_prompt(self, req: RewriteRequest, persona: Persona, constraints: SemanticConstraints) -> tuple[str, str]:
        template = (PROMPTS_DIR / "rewrite-with-persona.md").read_text(encoding="utf-8")
        persona_prompt = persona.render_runtime_prompt(req.style_strength)
        target_len = "keep original length" if req.preserve_length else "no length requirement"
        system = template.split("Persona:\n{{persona}}")[0].strip()
        user = (
            f"Persona:\n{persona_prompt}\n\n"
            f"Semantic constraints (must remain intact):\n{constraints.model_dump_json(indent=1)}\n\n"
            f"Source text:\n{req.text}\n\n"
            "Return ONLY the rewritten text, no commentary."
        )
        system = (
            system.replace("{{style_strength}}", f"{req.style_strength:.2f}")
            .replace("{{platform}}", req.platform or "generic")
            .replace("{{target_length}}", target_len)
        )
        return system, user

    def rewrite_candidates(self, req: RewriteRequest, persona: Persona,
                           constraints: SemanticConstraints) -> List[str]:
        system, user_template = self._render_prompt(req, persona, constraints)
        candidates: List[str] = []
        for _ in range(req.candidate_count):
            raw = self.client.chat(system, user_template, temperature=0.8)
            text = raw.strip().strip("`").strip()
            if text:
                candidates.append(text)
        if not candidates:
            raise RuntimeError("Rewriting produced no output.")
        return candidates

    # ----- orchestration -----

    def rewrite(self, req: RewriteRequest, evaluate: bool = True,
                platform: Optional[str] = None) -> RewriteResult:
        if req.persona is not None:
            persona = req.persona
        else:
            persona = self.registry.require(req.persona_id or "")

        try:
            constraints = self.lock_content(req.text)
        except Exception:
            constraints = self.lock_content_local(req.text)

        candidates = self.rewrite_candidates(req, persona, constraints)
        best = candidates[0]
        scores = RewriteScore(
            meaning_preservation=1.0, style_match=1.0, readability=1.0,
            platform_fit=1.0, final_score=1.0,
        )

        if evaluate:
            ranked = []
            for candidate in candidates:
                try:
                    scores = evaluate_rewrite(
                        req.text, candidate, persona, req.platform or platform or "generic",
                        self.client, self.config,
                    )
                except Exception:
                    scores = heuristic_fidelity(req.text, candidate)
                ranked.append((scores.final_score, candidate, scores))
            ranked.sort(key=lambda item: item[0], reverse=True)
            best = ranked[0][1]
            scores = ranked[0][2]

        return RewriteResult(
            output=best,
            scores=scores,
            alternatives=[c for c in candidates if c != best],
            constraints=constraints,
        )


async def rewrite_async(req: RewriteRequest, registry: PersonaRegistry,
                        config: Optional[LLMConfig] = None) -> RewriteResult:
    """Async variant for FastAPI (shared code path via sync calls for simplicity)."""
    rewriter = Rewriter(registry, config)
    return rewriter.rewrite(req)
