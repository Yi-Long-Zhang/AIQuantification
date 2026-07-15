from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from .config import LLM_PROVIDERS, settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Supports: DeepSeek, OpenAI, Qwen, Gemini
    """

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

        logger.info(f"LLMClient initialized: provider={provider}, model={self.model}")

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
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._http_client

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of function calling tools
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            stream: If True, returns immediately (use chat_stream instead)

        Returns:
            Response dict from the API

        Raises:
            httpx.HTTPStatusError: On API errors
        """
        client = await self._client()

        # Build request body
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        # Only include max_tokens if specified (some models don't accept it)
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        elif self.max_tokens:
            body["max_tokens"] = self.max_tokens

        # Add tools if provided
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        # Stream flag (for completeness, but use chat_stream for streaming)
        if stream:
            body["stream"] = True

        try:
            resp = await client.post("/chat/completions", json=body)
            resp.raise_for_status()
            data = resp.json()

            # Log token usage
            if "usage" in data:
                usage = data["usage"]
                logger.debug(
                    f"LLM usage: prompt={usage.get('prompt_tokens')}, "
                    f"completion={usage.get('completion_tokens')}, "
                    f"total={usage.get('total_tokens')}"
                )

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            if self.fallback_client:
                logger.info("Trying fallback client...")
                return await self.fallback_client.chat(messages, tools, temperature, max_tokens, stream)
            raise

        except httpx.TimeoutException as e:
            logger.error(f"LLM request timeout: {e}")
            if self.fallback_client:
                logger.info("Trying fallback client...")
                return await self.fallback_client.chat(messages, tools, temperature, max_tokens, stream)
            raise

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            if self.fallback_client:
                logger.info("Trying fallback client...")
                return await self.fallback_client.chat(messages, tools, temperature, max_tokens, stream)
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Send a streaming chat completion request.

        Yields:
            Chunk dicts from the SSE stream

        Example:
            async for chunk in client.chat_stream(messages):
                if chunk['choices'][0].get('delta', {}).get('content'):
                    print(chunk['choices'][0]['delta']['content'], end='')
        """
        client = await self._client()

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": True,
        }

        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        elif self.max_tokens:
            body["max_tokens"] = self.max_tokens

        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"

        try:
            async with client.stream("POST", "/chat/completions", json=body) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    # SSE format: "data: {...}"
                    if not line.strip():
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        # End of stream marker
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            yield chunk
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse SSE chunk: {data_str[:100]}... - {e}")
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM stream error: {e.response.status_code} - {e.response.text}")
            raise

        except Exception as e:
            logger.error(f"LLM stream failed: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.debug("LLMClient HTTP connection closed")

    def __repr__(self) -> str:
        return f"<LLMClient provider={self.provider} model={self.model}>"
