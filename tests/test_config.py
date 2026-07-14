import os
import tempfile
import pytest
from agent.config import Settings


def test_settings_default_provider():
    settings = Settings()
    assert settings.llm_provider in ("deepseek", "openai", "qwen", "gemini")


def test_settings_default_temperature():
    settings = Settings()
    assert settings.llm_temperature == 0.3


def test_settings_default_max_tokens():
    settings = Settings()
    assert settings.llm_max_tokens == 4096


def test_settings_loaded_path():
    settings = Settings()
    if settings.loaded_path:
        assert os.path.isfile(settings.loaded_path)


def test_settings_nonexistent_config():
    settings = Settings(config_path="/nonexistent/path/config.yaml")
    assert settings.llm_provider == "deepseek"


def test_settings_from_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("llm:\n  provider: openai\n  model: gpt-4o\n  temperature: 0.5\n")
        f.flush()
        settings = Settings(config_path=f.name)
        assert settings.llm_provider == "openai"
        assert settings.llm_model == "gpt-4o"
        assert settings.llm_temperature == 0.5
    os.unlink(f.name)


def test_settings_server_defaults():
    settings = Settings()
    assert settings.server_host == "0.0.0.0"
    assert settings.server_port == 8000
    assert settings.server_reload is True
