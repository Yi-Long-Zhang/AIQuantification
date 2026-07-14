from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from agent.tools.news import get_stock_news, analyze_sentiment


@pytest.mark.asyncio
async def test_get_stock_news_success():
    mock_news = [
        {"title": "Test News 1", "publisher": "Publisher 1", "link": "http://example.com/1", "type": "Article"},
        {"title": "Test News 2", "publisher": "Publisher 2", "link": "http://example.com/2", "type": "Article"},
    ]
    mock_ticker = MagicMock()
    mock_ticker.news = mock_news

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await get_stock_news(symbol="AAPL", market="us_stock", max_news=5)
        assert isinstance(result, list)
        assert len(result) <= 5
        assert "title" in result[0]


@pytest.mark.asyncio
async def test_get_stock_news_no_news():
    mock_ticker = MagicMock()
    mock_ticker.news = []

    with patch("yfinance.Ticker", return_value=mock_ticker):
        result = await get_stock_news(symbol="AAPL", market="us_stock")
        assert result == []


@pytest.mark.asyncio
async def test_get_stock_news_error():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("Network error")
        result = await get_stock_news(symbol="INVALID", market="us_stock")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]


@pytest.mark.asyncio
async def test_analyze_sentiment_crypto():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"value": "25", "value_classification": "Fear"}]}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await analyze_sentiment(market="crypto")
        assert "market" in result
        assert result["market"] == "crypto"


@pytest.mark.asyncio
async def test_analyze_sentiment_us_stock():
    mock_info = {"regularMarketPrice": 20.0}

    with patch("yfinance.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = mock_info
        mock_ticker_class.return_value = mock_ticker
        result = await analyze_sentiment(market="us_stock")
        assert "market" in result
        assert result["market"] == "us_stock"
        assert "vix" in result


@pytest.mark.asyncio
async def test_analyze_sentiment_unknown_market():
    result = await analyze_sentiment(market="forex")
    assert result["market"] == "forex"
