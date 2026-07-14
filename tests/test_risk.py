from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from agent.tools.risk import calculate_position_size, assess_portfolio_risk


@pytest.mark.asyncio
async def test_calculate_position_size_success():
    mock_quote = {"price": 150.0}
    with patch("agent.tools.risk.get_stock_quote", new_callable=AsyncMock, return_value=mock_quote):
        result = await calculate_position_size(
            symbol="AAPL",
            market="us_stock",
            confidence=0.7,
            account_balance=100000.0,
            win_rate=0.6,
            risk_per_trade=0.02,
        )
        assert "symbol" in result
        assert "shares" in result
        assert "kelly_fraction" in result
        assert result["shares"] >= 0
        assert 0 <= result["kelly_fraction"] <= 0.25


@pytest.mark.asyncio
async def test_calculate_position_size_no_price():
    mock_quote = {}
    with patch("agent.tools.risk.get_stock_quote", new_callable=AsyncMock, return_value=mock_quote):
        result = await calculate_position_size(symbol="AAPL")
        assert "error" in result


@pytest.mark.asyncio
async def test_assess_portfolio_risk_success():
    call_count = 0

    async def mock_get_klines_fn(symbol, market, interval, period):
        nonlocal call_count
        result = [{"Close": 100 + i + call_count * 5} for i in range(260)]
        call_count += 1
        return result

    with patch("agent.tools.risk.get_klines", new_callable=AsyncMock, side_effect=mock_get_klines_fn):
        result = await assess_portfolio_risk(symbols=["AAPL", "MSFT"], market="us_stock")
        assert "num_assets" in result
        assert "portfolio_volatility_pct" in result
        assert "correlation_matrix" in result
        assert "individual_vol" in result


@pytest.mark.asyncio
async def test_assess_portfolio_risk_no_data():
    with patch("agent.tools.risk.get_klines", new_callable=AsyncMock, return_value=[]):
        result = await assess_portfolio_risk(symbols=["INVALID"], market="us_stock")
        assert "error" in result
