from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from agent.tools.crypto import (
    get_crypto_klines,
    get_crypto_realtime,
    get_crypto_orderbook,
    get_crypto_overview,
    _ccxt_klines,
    _yfinance_crypto_klines,
    _coingecko_klines,
)


@pytest.mark.asyncio
async def test_get_crypto_klines_empty():
    with patch("agent.tools.crypto._get_crypto_klines_with_fallback", new_callable=AsyncMock, return_value=[]):
        result = await get_crypto_klines(symbol="BTC")
        assert result == []


@pytest.mark.asyncio
async def test_get_crypto_klines_data():
    mock_data = [{"date": "2024-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}]
    with patch("agent.tools.crypto._get_crypto_klines_with_fallback", new_callable=AsyncMock, return_value=mock_data):
        result = await get_crypto_klines(symbol="BTC")
        assert result == mock_data


@pytest.mark.asyncio
async def test_ccxt_klines_no_exchange():
    result = await _ccxt_klines("BTC", "1d", "1y", "nonexistent_exchange")
    assert result is None


@pytest.mark.asyncio
async def test_yfinance_crypto_klines_error():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("Network error")
        result = await _yfinance_crypto_klines("BTC", "1d", "1y")
        assert result is None


@pytest.mark.asyncio
async def test_coingecko_klines_error():
    with patch("pycoingecko.CoinGeckoAPI") as mock_cg:
        mock_cg.side_effect = Exception("API error")
        result = await _coingecko_klines("BTC", "1d", "1y")
        assert result is None


@pytest.mark.asyncio
async def test_get_crypto_realtime_success():
    mock_ticker = {
        "last": 50000, "bid": 49999, "ask": 50001,
        "percentage": 2.5, "baseVolume": 1000000,
        "high": 51000, "low": 49000, "vwap": 50000,
    }
    mock_exchange = MagicMock()
    mock_exchange.fetch_ticker.return_value = mock_ticker

    import sys
    mock_ccxt = MagicMock()
    mock_ccxt.binance.return_value = mock_exchange
    with patch.dict(sys.modules, {"ccxt": mock_ccxt}):
        result = await get_crypto_realtime(symbol="BTC", exchange="binance")
        assert "price" in result
        assert result["price"] == 50000


@pytest.mark.asyncio
async def test_get_crypto_realtime_error():
    import sys
    mock_ccxt = MagicMock()
    mock_ccxt.binance.side_effect = Exception("Connection error")
    with patch.dict(sys.modules, {"ccxt": mock_ccxt}):
        result = await get_crypto_realtime(symbol="BTC")
        assert "error" in result


@pytest.mark.asyncio
async def test_get_crypto_orderbook_success():
    mock_ob = {
        "bids": [[49999, 1], [49998, 2]],
        "asks": [[50001, 1], [50002, 2]],
    }
    mock_exchange = MagicMock()
    mock_exchange.fetch_order_book.return_value = mock_ob

    import sys
    mock_ccxt = MagicMock()
    mock_ccxt.binance.return_value = mock_exchange
    with patch.dict(sys.modules, {"ccxt": mock_ccxt}):
        result = await get_crypto_orderbook(symbol="BTC")
        assert "bids" in result
        assert "asks" in result
        assert "spread" in result


@pytest.mark.asyncio
async def test_get_crypto_overview_success():
    mock_global = {
        "total_market_cap": {"usd": 2000000000000},
        "total_volume": {"usd": 100000000000},
        "market_cap_percentage": {"btc": 50.0, "eth": 20.0},
        "active_cryptocurrencies": 10000,
    }
    mock_coins = [
        {"symbol": "btc", "name": "Bitcoin", "current_price": 50000, "market_cap": 1000000000000, "price_change_percentage_24h": 2.5},
    ]

    import sys
    mock_pycoingecko = MagicMock()
    mock_instance = MagicMock()
    mock_instance.get_global.return_value = mock_global
    mock_instance.get_coins_markets.return_value = mock_coins
    mock_pycoingecko.CoinGeckoAPI.return_value = mock_instance
    with patch.dict(sys.modules, {"pycoingecko": mock_pycoingecko}):
        result = await get_crypto_overview()
        assert "total_market_cap_usd" in result
        assert "btc_dominance" in result
