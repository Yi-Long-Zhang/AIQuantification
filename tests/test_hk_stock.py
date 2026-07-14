from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import pandas as pd

from agent.tools.hk_stock import (
    get_hk_klines,
    get_hk_realtime,
    get_hk_index,
    get_hk_flow,
    _yfinance_hk_klines,
    _akshare_hk_klines,
)


@pytest.mark.asyncio
async def test_get_hk_klines_empty():
    with patch("agent.tools.hk_stock._get_hk_klines_with_fallback", new_callable=AsyncMock, return_value=[]):
        result = await get_hk_klines(symbol="00700")
        assert result == []


@pytest.mark.asyncio
async def test_get_hk_klines_data():
    mock_data = [{"date": "2024-01-01", "open": 300, "high": 310, "low": 290, "close": 305, "volume": 1000000}]
    with patch("agent.tools.hk_stock._get_hk_klines_with_fallback", new_callable=AsyncMock, return_value=mock_data):
        result = await get_hk_klines(symbol="00700")
        assert result == mock_data


@pytest.mark.asyncio
async def test_yfinance_hk_klines_error():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.side_effect = Exception("Network error")
        result = await _yfinance_hk_klines("00700", "daily", "1y")
        assert result is None


@pytest.mark.asyncio
async def test_akshare_hk_klines_error():
    import sys
    mock_akshare = MagicMock()
    mock_akshare.stock_hk_hist.side_effect = Exception("API error")
    with patch.dict(sys.modules, {"akshare": mock_akshare}):
        result = await _akshare_hk_klines("00700", "daily", "1y")
        assert result is None


@pytest.mark.asyncio
async def test_get_hk_realtime_success():
    mock_df = pd.DataFrame({
        "代码": ["00700", "09988"],
        "名称": ["腾讯", "阿里巴巴"],
        "最新价": [300.0, 80.0],
        "涨跌额": [5.0, -2.0],
        "涨跌幅": [1.67, -2.44],
        "成交量": [1000000, 500000],
        "成交额": [300000000, 40000000],
        "市盈率": [15.0, 20.0],
        "总市值": [3000000000000, 2000000000000],
    })

    import sys
    mock_akshare = MagicMock()
    mock_akshare.stock_hk_spot_em.return_value = mock_df
    with patch.dict(sys.modules, {"akshare": mock_akshare}):
        result = await get_hk_realtime(symbols=["00700"])
        assert isinstance(result, list)
        assert len(result) <= 50


@pytest.mark.asyncio
async def test_get_hk_index_success():
    mock_info = {"regularMarketPrice": 20000, "regularMarketChangePercent": 0.5}

    with patch("yfinance.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = mock_info
        mock_ticker_class.return_value = mock_ticker
        result = await get_hk_index()
        assert isinstance(result, list)
        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_hk_flow_success():
    mock_df = pd.DataFrame({"date": ["2024-01-01"], "net_flow": [1000000]})

    import sys
    mock_akshare = MagicMock()
    mock_akshare.stock_hsgt_hist_em.return_value = mock_df
    with patch.dict(sys.modules, {"akshare": mock_akshare}):
        result = await get_hk_flow(direction="both")
        assert "northbound" in result or "southbound" in result


@pytest.mark.asyncio
async def test_get_hk_flow_error():
    import sys
    mock_akshare = MagicMock()
    mock_akshare.stock_hsgt_hist_em.side_effect = Exception("API error")
    with patch.dict(sys.modules, {"akshare": mock_akshare}):
        result = await get_hk_flow(direction="both")
        assert "error" in result
