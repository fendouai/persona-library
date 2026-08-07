"""Persona Library API (FastAPI).

Endpoints:
  GET  /health
  GET  /v1/personas?category=&tag=&query=
  GET  /v1/personas/{persona_id}
  POST /v1/personas                        — manual persona creation (saved to disk)
  POST /v1/personas/extract                — create persona from samples
  POST /v1/rewrite                         — apply a persona to text
  POST /v1/mix                             — preview a blended profile
  POST /v1/evaluate                        — score an existing rewrite
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from persona_lib.blender import mix_personas
from persona_lib.config import default_config
from persona_lib.evaluator import combine_scores, evaluate_rewrite, heuristic_fidelity
from persona_lib.extractor import extract_persona
from persona_lib.llm import LLMClient
from persona_lib.loader import render_persona_markdown
from persona_lib.models import (
    ConfidenceReport,
    ExtractionResult,
    MixRequest,
    Persona,
    RewriteRequest,
    RewriteResult,
    RewriteScore,
)
from persona_lib.registry import PersonaRegistry
from persona_lib.rewriter import Rewriter

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = ROOT / "personas"

app = FastAPI(title="Persona Library", version="0.1.0", description="Create, manage, mix, and apply writing personas.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registry = PersonaRegistry(PERSONAS_DIR)
config = default_config()


class ExtractRequest(BaseModel):
    name: Optional[str] = None
    samples: List[str] = Field(min_length=1)
    language: str = "en"


class ManualCreateRequest(BaseModel):
    persona: Persona


class EvaluateRequest(BaseModel):
    persona_id: str
    original: str = Field(min_length=1)
    rewritten: str = Field(min_length=1)
    platform: str = "generic"


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "personas": len(registry), "llm_configured": config.available}


@app.get("/v1/personas")
def list_personas(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
) -> Dict[str, Any]:
    personas = registry.list(category=category, tag=tag, query=query)
    return {
        "count": len(personas),
        "personas": [p.model_dump(mode="json") for p in personas],
    }


@app.get("/v1/personas/meta")
def persona_meta() -> Dict[str, Any]:
    return {"categories": registry.categories(), "tags": registry.tags()}


@app.get("/v1/personas/{persona_id}")
def get_persona(persona_id: str) -> Dict[str, Any]:
    persona = registry.get(persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona not found: {persona_id}")
    return persona.model_dump(mode="json")


@app.post("/v1/personas")
def create_persona(req: ManualCreateRequest) -> Dict[str, Any]:
    """Manually create a persona; saves it to personas/custom/<id>.md."""
    persona = req.persona
    if registry.get(persona.id) is not None:
        raise HTTPException(status_code=409, detail=f"Persona already exists: {persona.id}")
    dest = PERSONAS_DIR / "custom" / f"{persona.id}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_persona_markdown(persona), encoding="utf-8")
    registry._by_id[persona.id] = persona
    return {"status": "created", "path": str(dest)}


@app.post("/v1/personas/extract")
def create_persona_from_samples(req: ExtractRequest) -> ExtractionResult:
    """Create a persona draft from author samples (with confidence report)."""
    try:
        return extract_persona(req.samples, name=req.name, language=req.language, config=config)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/v1/rewrite")
def rewrite(req: RewriteRequest) -> RewriteResult:
    try:
        return Rewriter(registry, config).rewrite(req)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/v1/mix")
def mix_preview(req: MixRequest) -> Dict[str, Any]:
    """Weighted blend preview: returns the blended persona (not saved)."""
    try:
        entries = req.validated(registry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    blended = mix_personas(entries)
    return blended.model_dump(mode="json")


@app.post("/v1/evaluate")
def evaluate(req: EvaluateRequest) -> RewriteScore:
    persona = registry.get(req.persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona not found: {req.persona_id}")
    try:
        return evaluate_rewrite(req.original, req.rewritten, persona, req.platform,
                                LLMClient(config), config)
    except Exception:
        return heuristic_fidelity(req.original, req.rewritten)
