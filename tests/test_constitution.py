from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from agent.tools.constitution import check_constitution


@pytest.mark.asyncio
async def test_check_constitution_no_file():
    with patch("pathlib.Path.exists", return_value=False):
        result = await check_constitution(article="")
        assert "error" in result


@pytest.mark.asyncio
async def test_check_constitution_all():
    constitution_text = "# Constitution\n## 总则\nContent 1\n## 风控原则\nContent 2\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=constitution_text):
            result = await check_constitution(article="")
            assert "constitution" in result
            assert "articles" in result


@pytest.mark.asyncio
async def test_check_constitution_search_match():
    constitution_text = "# Constitution\n## 总则\nContent 1\n## 风控原则\nRisk control\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=constitution_text):
            result = await check_constitution(article="风控")
            assert "matches" in result
            assert result["count"] >= 1


@pytest.mark.asyncio
async def test_check_constitution_search_no_match():
    constitution_text = "# Constitution\n## 总则\nContent 1\n"
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=constitution_text):
            result = await check_constitution(article="nonexistent")
            assert "matches" in result
            assert len(result["matches"]) == 0
