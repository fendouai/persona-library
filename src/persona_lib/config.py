"""Configuration for the LLM backend (OpenAI-compatible interface)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class LLMConfig:
    api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    )
    base_url: str = field(
        default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    model: str = field(default_factory=lambda: os.environ.get("PERSONA_LLM_MODEL", "gpt-4o-mini"))
    temperature: float = field(default_factory=lambda: float(os.environ.get("PERSONA_LLM_TEMPERATURE", "0.7")))
    timeout: float = field(default_factory=lambda: float(os.environ.get("PERSONA_LLM_TIMEOUT", "120")))
    max_tokens: int = field(default_factory=lambda: int(os.environ.get("PERSONA_LLM_MAX_TOKENS", "4096")))

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def as_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "max_tokens": self.max_tokens,
        }


def default_config() -> LLMConfig:
    return LLMConfig()
