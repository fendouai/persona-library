"""OpenAI-compatible LLM client (sync + async) used by extractor/rewriter/evaluator."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from .config import LLMConfig, default_config


class LLMError(RuntimeError):
    pass


def _extract_json(text: str) -> Any:
    """Best-effort JSON extraction from a model response."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fences = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    for fence in fences:
        try:
            return json.loads(fence.strip())
        except json.JSONDecodeError:
            continue
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise LLMError("Model response did not contain valid JSON")


class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or default_config()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, system: str, user: str, json_mode: bool = False, temperature: Optional[float] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.config.temperature if temperature is None else temperature,
            "max_tokens": self.config.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def chat(self, system: str, user: str, json_mode: bool = False,
             temperature: Optional[float] = None) -> str:
        if not self.config.available:
            raise LLMError(
                "No LLM API key configured. Set OPENAI_API_KEY (or OPENAI_BASE_URL / "
                "PERSONA_LLM_MODEL for compatible providers)."
            )
        payload = self._payload(system, user, json_mode=json_mode, temperature=temperature)
        try:
            resp = httpx.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return str(data["choices"][0]["message"]["content"])
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LLM response: {exc}") from exc

    def chat_json(self, system: str, user: str, temperature: Optional[float] = None) -> Any:
        return _extract_json(self.chat(system, user, json_mode=True, temperature=temperature))

    async def achat(self, system: str, user: str, json_mode: bool = False,
                    temperature: Optional[float] = None) -> str:
        if not self.config.available:
            raise LLMError(
                "No LLM API key configured. Set OPENAI_API_KEY (or OPENAI_BASE_URL / "
                "PERSONA_LLM_MODEL for compatible providers)."
            )
        payload = self._payload(system, user, json_mode=json_mode, temperature=temperature)
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                resp = await client.post(
                    f"{self.config.base_url.rstrip('/')}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return str(data["choices"][0]["message"]["content"])
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected LLM response: {exc}") from exc

    async def achat_json(self, system: str, user: str, temperature: Optional[float] = None) -> Any:
        return _extract_json(await self.achat(system, user, json_mode=True, temperature=temperature))
