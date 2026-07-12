from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


DEFAULT_PATHS = [
    "./config.yaml",
    "./config.yml",
    "~/.aiquantification/config.yaml",
    "/etc/aiquantification/config.yaml",
]

LLM_PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {"base_url": "https://api.deepseek.com", "models": ["deepseek-chat", "deepseek-reasoner"]},
    "openai": {"base_url": "https://api.openai.com/v1", "models": ["gpt-4o", "gpt-4o-mini", "o3-mini"]},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "models": ["qwen-plus", "qwen-max", "qwen-turbo"]},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "models": ["gemini-2.0-flash", "gemini-2.5-pro"]},
}


class Settings:
    def __init__(self, config_path: str | None = None):
        self._raw: dict[str, Any] = {}
        self._loaded_path: str | None = None
        self._load(config_path)

    def _load(self, config_path: str | None = None):
        paths = [config_path] if config_path else DEFAULT_PATHS
        for p in paths:
            expanded = os.path.expanduser(p)
            if os.path.isfile(expanded):
                self._load_file(expanded)
                self._loaded_path = expanded
                return
        self._raw = {}

    def _load_file(self, path: str):
        if yaml is None:
            raise ImportError("PyYAML is required. Install with: uv pip install pyyaml")
        with open(path) as f:
            self._raw = yaml.safe_load(f) or {}

    @property
    def loaded_path(self) -> str | None:
        return self._loaded_path

    @property
    def llm_provider(self) -> str:
        return self._raw.get("llm", {}).get("provider", "deepseek")

    @property
    def llm_model(self) -> str | None:
        return self._raw.get("llm", {}).get("model")

    @property
    def llm_api_key(self) -> str | None:
        return self._raw.get("llm", {}).get("api_key")

    @property
    def llm_api_base(self) -> str | None:
        return self._raw.get("llm", {}).get("api_base")

    @property
    def llm_temperature(self) -> float:
        return self._raw.get("llm", {}).get("temperature", 0.3)

    @property
    def llm_max_tokens(self) -> int:
        return self._raw.get("llm", {}).get("max_tokens", 4096)

    @property
    def llm_fallback(self) -> dict[str, Any] | None:
        return self._raw.get("llm", {}).get("fallback")

    @property
    def provider_info(self) -> dict[str, Any]:
        provider = self.llm_provider
        info = LLM_PROVIDERS.get(provider, {})
        return {
            "provider": provider,
            "base_url": self.llm_api_base or info.get("base_url", ""),
            "api_key": self.llm_api_key or "",
            "model": self.llm_model or (info.get("models", [""])[0] if info.get("models") else ""),
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
        }

    @property
    def memory_db_path(self) -> str:
        return os.path.expanduser(self._raw.get("memory", {}).get("db_path", "~/.aiquantification/memory.db"))

    @property
    def constitution_path(self) -> str:
        return os.path.expanduser(self._raw.get("constitution", {}).get("path", "AGENT_CONSTITUTION.md"))

    @property
    def server_host(self) -> str:
        return self._raw.get("server", {}).get("host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self._raw.get("server", {}).get("port", 8000)

    @property
    def server_reload(self) -> bool:
        return self._raw.get("server", {}).get("reload", True)


settings = Settings()
