import os
import tempfile
import pytest
from agent.config import Settings
from agent.llm_client import LLMClient, LLM_PROVIDERS


def test_llm_providers_defined():
    assert "deepseek" in LLM_PROVIDERS
    assert "openai" in LLM_PROVIDERS
    assert "qwen" in LLM_PROVIDERS
    assert "gemini" in LLM_PROVIDERS


def test_llm_provider_structure():
    for provider, info in LLM_PROVIDERS.items():
        assert "base_url" in info
        assert "models" in info
        assert len(info["models"]) > 0


def test_llm_client_missing_api_key():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("llm:\n  provider: deepseek\n  api_key: null\n")
        f.flush()
        test_settings = Settings(config_path=f.name)
    os.unlink(f.name)

    import agent.llm_client as llm_mod
    original_settings = llm_mod.settings
    llm_mod.settings = test_settings

    try:
        with pytest.raises(ValueError, match="Missing api_key"):
            LLMClient(provider="deepseek")
    finally:
        llm_mod.settings = original_settings


def test_llm_client_unsupported_provider():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("llm:\n  provider: unsupported\n  api_key: test-key\n")
        f.flush()
        test_settings = Settings(config_path=f.name)
    os.unlink(f.name)

    import agent.llm_client as llm_mod
    original_settings = llm_mod.settings
    llm_mod.settings = test_settings

    try:
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient()
    finally:
        llm_mod.settings = original_settings


def test_llm_client_from_dict():
    cfg = {
        "provider": "openai",
        "api_key": "test-key",
        "model": "gpt-4o",
        "temperature": 0.5,
        "max_tokens": 2048,
    }
    client = LLMClient._from_dict(cfg)
    assert client.provider == "openai"
    assert client.api_key == "test-key"
    assert client.model == "gpt-4o"
    assert client.temperature == 0.5
    assert client.max_tokens == 2048
    assert client.fallback_client is None


def test_llm_client_from_dict_with_fallback():
    cfg = {
        "provider": "deepseek",
        "api_key": "test-key",
        "fallback": {
            "provider": "openai",
            "api_key": "fallback-key",
            "model": "gpt-4o-mini",
        },
    }
    client = LLMClient._from_dict(cfg)
    assert client.fallback_client is None
    assert client.api_key == "test-key"

    fallback_cfg = cfg["fallback"]
    fallback_client = LLMClient._from_dict(fallback_cfg)
    assert fallback_client.provider == "openai"
    assert fallback_client.api_key == "fallback-key"
    assert fallback_client.model == "gpt-4o-mini"
