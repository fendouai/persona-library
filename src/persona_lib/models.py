"""Pydantic data models for Persona Library."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SourceType = Literal["archetype", "user-created", "sample-derived", "brand", "inspired"]

TONE_KEYS = [
    "formality",
    "warmth",
    "confidence",
    "humor",
    "emotional_intensity",
    "directness",
]

TONE_LABELS = {
    "formality": "Formality",
    "warmth": "Warmth",
    "confidence": "Confidence",
    "humor": "Humor",
    "emotional_intensity": "Emotional intensity",
    "directness": "Directness",
}


class ToneDimensions(BaseModel):
    """Six measurable 0-1 tone dimensions."""

    formality: float = Field(ge=0, le=1)
    warmth: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    humor: float = Field(ge=0, le=1)
    emotional_intensity: float = Field(ge=0, le=1)
    directness: float = Field(ge=0, le=1)

    def as_dict(self) -> Dict[str, float]:
        return {k: float(getattr(self, k)) for k in TONE_KEYS}

    @classmethod
    def from_dict(cls, values: Dict[str, float]) -> "ToneDimensions":
        data = {k: float(values.get(k, 0.5)) for k in TONE_KEYS}
        return cls(**data)

    def weighted_average(self, other: "ToneDimensions", weight_self: float) -> "ToneDimensions":
        """Blend another tone vector. weight_self = share of this vector (0-1)."""
        w = max(0.0, min(1.0, weight_self))
        data = {}
        for k in TONE_KEYS:
            a = float(getattr(self, k))
            b = float(getattr(other, k))
            data[k] = a * w + b * (1 - w)
        return ToneDimensions(**data)


class Example(BaseModel):
    """A positive or negative example with input/output and optional reason."""

    label: Optional[str] = None
    input: str
    output: str = ""
    reason: Optional[str] = None


class StyleProfile(BaseModel):
    """The machine-parseable style description extracted from a Persona file."""

    voice_summary: str = ""
    tone: ToneDimensions = Field(default_factory=lambda: ToneDimensions.from_dict({}))
    sentence_patterns: List[str] = Field(default_factory=list)
    paragraph_patterns: List[str] = Field(default_factory=list)
    rhetorical_patterns: List[str] = Field(default_factory=list)
    preferred_vocabulary: List[str] = Field(default_factory=list)
    avoided_vocabulary: List[str] = Field(default_factory=list)
    signature_moves: List[str] = Field(default_factory=list)
    anti_patterns: List[str] = Field(default_factory=list)
    positive_examples: List[Example] = Field(default_factory=list)
    negative_examples: List[Example] = Field(default_factory=list)


class Persona(BaseModel):
    """A full persona: metadata + style profile + runtime rules."""

    id: str
    name: str
    description: str = ""
    category: str = "custom"
    languages: List[str] = Field(default_factory=lambda: ["en"])
    emoji: Optional[str] = None
    version: str = "0.1.0"
    author: str = "user"
    license: str = "MIT"
    tags: List[str] = Field(default_factory=list)
    source_type: SourceType = "user-created"
    style_strength_default: float = Field(default=0.7, ge=0, le=1)
    disclaimer: Optional[str] = None
    path: Optional[str] = None
    profile: StyleProfile = Field(default_factory=StyleProfile)
    content_preservation_rules: List[str] = Field(default_factory=list)
    transformation_rules: List[str] = Field(default_factory=list)
    body_markdown: str = ""

    def render_runtime_prompt(self, strength: Optional[float] = None) -> str:
        """Render the persona body as an executable runtime prompt."""
        s = self.style_strength_default if strength is None else strength
        head = f"# {self.name}\n\n"
        body = self.body_markdown or ""
        return f"{head}{body}\n\nStyle strength: {s:.2f}\n".strip()


class SemanticConstraints(BaseModel):
    """Phase-1 content lock: the semantic invariants that rewriting must not break."""

    claims: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    numbers: List[str] = Field(default_factory=list)
    position: Optional[str] = None
    uncertainties: List[str] = Field(default_factory=list)


class ConfidenceReport(BaseModel):
    """Confidence of a sample-derived persona extraction."""

    overall: float = Field(ge=0, le=1)
    dimensions: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Result of extracting a persona from author samples."""

    persona_id: str
    status: str = "draft"
    persona: Persona
    confidence: ConfidenceReport = Field(default_factory=ConfidenceReport)


class RewriteRequest(BaseModel):
    """POST /v1/rewrite request."""

    persona_id: Optional[str] = None
    persona: Optional[Persona] = None
    text: str = Field(min_length=1)
    style_strength: float = Field(default=0.7, ge=0, le=1)
    platform: Optional[str] = "generic"
    preserve_length: bool = True
    candidate_count: int = Field(default=3, ge=1, le=5)


class RewriteScore(BaseModel):
    meaning_preservation: float = Field(ge=0, le=1)
    style_match: float = Field(ge=0, le=1)
    readability: float = Field(ge=0, le=1)
    platform_fit: float = Field(ge=0, le=1)
    final_score: float = Field(ge=0, le=1)


class RewriteResult(BaseModel):
    output: str
    scores: RewriteScore
    alternatives: List[str] = Field(default_factory=list)
    constraints: SemanticConstraints = Field(default_factory=SemanticConstraints)


class MixRequest(BaseModel):
    personas: List[Dict[str, Any]] = Field(description='[{"id": "x", "weight": 0.7}, ...]')

    def validated(self, registry) -> List[tuple["Persona", float]]:
        entries = []
        for item in self.personas:
            pid = item["id"]
            w = float(item.get("weight", 0.5))
            persona = registry.get(pid)
            if persona is None:
                raise ValueError(f"Unknown persona: {pid}")
            entries.append((persona, w))
        return entries
