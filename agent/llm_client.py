from __future__ import annotations

import json
from typing import Any

import httpx

from .config import LLM_PROVIDERS, settings


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None):
        provider = provider or settings.llm_provider
        provider_def = LLM_PROVIDERS.get(provider)
        if not provider_def:
            msg = f"Unsupported provider: {provider}. Choose from {list(LLM_PROVIDERS.keys())}"
            raise ValueError(msg)

        api_key = settings.llm_api_key
        if not api_key:
            msg = (
                f"Missing api_key for provider '{provider}' in config.yaml. "
                f"Edit config.yaml and set llm.api_key"
            )
            raise ValueError(msg)

        self.provider = provider
        self.base_url = settings.llm_api_base or provider_def["base_url"]
        self.model = model or settings.llm_model or provider_def["models"][0]
        self.api_key = api_key
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self._http_client: httpx.AsyncClient | None = None

        self.fallback_client: LLMClient | None = None
        fallback = settings.llm_fallback
        if fallback and fallback.get("api_key"):
            self.fallback_client = LLMClient._from_dict(fallback)

    @classmethod
    def _from_dict(cls, cfg: dict[str, Any]) -> LLMClient:
        client = cls.__new__(cls)
        provider = cfg["provider"]
        provider_def = LLM_PROVIDERS.get(provider, {})
        client.provider = provider
        client.base_url = cfg.get("api_base") or provider_def.get("base_url", "")
        client.model = cfg.get("model") or (provider_def.get("models", [""])[0] if provider_def.get("models") else "")
        client.api_key = cfg["api_key"]
        client.temperature = cfg.get("temperature", 0.3)
        client.max_tokens = cfg.get("max_tokens", 4096)
        client._http_client = None
        client.fallback_client = None
        return client

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._http_client

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        client = await self._client()
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        try:
            resp = await client.post("/chat/completions", json=body)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if self.fallback_client:
                return await self.fallback_client.chat(messages, tools, temperature, max_tokens)
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        client = await self._client()
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        async with client.stream("POST", "/chat/completions", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
