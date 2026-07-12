from .registry import tool


@tool(
    name="calculate_position_size",
    description="计算仓位大小（基于凯利公式和风险预算）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "confidence": {"type": "number", "description": "策略信心 0-1", "default": 0.5},
        "account_balance": {"type": "number", "description": "账户余额", "default": 100000},
        "win_rate": {"type": "number", "description": "历史胜率", "default": 0.5},
        "risk_per_trade": {"type": "number", "description": "单笔风险比例 0-1", "default": 0.02},
    },
)
async def calculate_position_size(
    symbol: str,
    market: str = "us_stock",
    confidence: float = 0.5,
    account_balance: float = 100000.0,
    win_rate: float = 0.5,
    risk_per_trade: float = 0.02,
) -> dict:
    from .market_data import get_stock_quote
    quote = await get_stock_quote(symbol, market)
    price = quote.get("price")

    if not price:
        return {"error": "Cannot get current price"}

    kelly_fraction = win_rate - (1 - win_rate) * (1 - confidence) / max(confidence, 0.01)
    kelly_fraction = max(0, min(kelly_fraction, 0.25))

    risk_capital = account_balance * risk_per_trade
    position_value = account_balance * kelly_fraction
    position_value = min(position_value, risk_capital / max(risk_per_trade, 0.01))

    shares = int(position_value / price)
    actual_value = shares * price

    return {
        "symbol": symbol,
        "price": price,
        "kelly_fraction": round(kelly_fraction, 4),
        "risk_capital": round(risk_capital, 2),
        "recent_price": round(actual_value, 2),
        "shares": shares,
        "position_pct": round(actual_value / account_balance * 100, 2),
        "stop_loss_pct": round(risk_per_trade / max(kelly_fraction, 0.01) * 100, 2) if kelly_fraction > 0 else 0,
    }


@tool(
    name="assess_portfolio_risk",
    description="评估投资组合风险",
    parameters={
        "symbols": {
            "type": "array",
            "items": {"type": "string"},
            "description": "持仓股票代码列表",
        },
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
    },
)
async def assess_portfolio_risk(symbols: list[str], market: str = "us_stock") -> dict:
    from .market_data import get_klines
    import pandas as pd
    import numpy as np

    returns_dict = {}
    errors = []

    for sym in symbols:
        try:
            klines = await get_klines(sym, market, interval="1d", period="1y")
            if klines:
                df = pd.DataFrame(klines)
                close = pd.to_numeric(df["Close"], errors="coerce")
                returns_dict[sym] = close.pct_change().dropna().tail(252)
        except Exception as e:
            errors.append(f"{sym}: {e}")

    if not returns_dict:
        return {"error": "No data available", "errors": errors}

    returns_df = pd.DataFrame(returns_dict)
    correlation = returns_df.corr().round(4)

    portfolio_vol = np.nan
    if len(returns_df.columns) > 0:
        weights = np.array([1.0 / len(returns_df.columns)] * len(returns_df.columns))
        cov = returns_df.cov() * 252
        portfolio_vol = np.sqrt(weights.T @ cov @ weights) * 100

    risk_report = {
        "num_assets": len(symbols),
        "portfolio_volatility_pct": round(portfolio_vol, 2),
        "correlation_matrix": correlation.to_dict(),
        "individual_vol": {},
        "errors": errors,
    }

    for sym in symbols:
        if sym in returns_dict and len(returns_dict[sym]) > 0:
            risk_report["individual_vol"][sym] = round(returns_dict[sym].std() * np.sqrt(252) * 100, 2)

    return risk_report
