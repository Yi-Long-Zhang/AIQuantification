import pandas as pd
import numpy as np

from .registry import tool


@tool(
    name="run_backtest",
    description="运行策略回测",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "strategy": {"type": "string", "description": "策略类型: sma_cross, macd, rsi, bollinger", "default": "sma_cross"},
        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD", "default": ""},
        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD", "default": ""},
        "initial_capital": {"type": "number", "description": "初始资金", "default": 100000},
    },
)
async def run_backtest(
    symbol: str,
    market: str = "us_stock",
    strategy: str = "sma_cross",
    start_date: str = "",
    end_date: str = "",
    initial_capital: float = 100000.0,
) -> dict:
    from .market_data import get_klines
    klines = await get_klines(symbol, market, interval="1d", period="2y")
    if not klines:
        return {"error": "No data"}

    df = pd.DataFrame(klines)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    if start_date:
        df = df[df["Date"] >= start_date]
    if end_date:
        df = df[df["Date"] <= end_date]

    if len(df) < 60:
        return {"error": "Insufficient data"}

    signals = pd.Series(0, index=df.index)

    if strategy == "sma_cross":
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()
        signals[df["SMA20"] > df["SMA50"]] = 1
        signals[df["SMA20"] < df["SMA50"]] = -1

    elif strategy == "macd":
        exp12 = df["Close"].ewm(span=12).mean()
        exp26 = df["Close"].ewm(span=26).mean()
        macd_line = exp12 - exp26
        signal_line = macd_line.ewm(span=9).mean()
        signals[macd_line > signal_line] = 1
        signals[macd_line < signal_line] = -1

    elif strategy == "rsi":
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        signals[rsi < 30] = 1
        signals[rsi > 70] = -1

    elif strategy == "bollinger":
        sma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        signals[df["Close"] < lower] = 1
        signals[df["Close"] > upper] = -1

    position = 0
    capital = initial_capital
    shares = 0
    trades = []
    portfolio_value = []
    last_signal = 0

    for i in range(len(df)):
        sig = signals.iloc[i]
        price = df["Close"].iloc[i]

        if pd.notna(price) and price > 0:
            if sig == 1 and last_signal != 1 and position <= 0:
                shares = capital / price
                capital -= shares * price
                position = 1
                trades.append({"date": str(df["Date"].iloc[i])[:10], "type": "BUY", "price": round(price, 2), "shares": round(shares, 4)})
                last_signal = 1
            elif sig == -1 and last_signal != -1 and position >= 0 and shares > 0:
                capital += shares * price
                trades.append({"date": str(df["Date"].iloc[i])[:10], "type": "SELL", "price": round(price, 2), "shares": round(shares, 4)})
                shares = 0
                position = -1
                last_signal = -1

        equity = capital + shares * price
        portfolio_value.append(equity)

    if shares > 0:
        capital += shares * df["Close"].iloc[-1]
        shares = 0

    pv = pd.Series(portfolio_value)
    total_return = (capital - initial_capital) / initial_capital * 100

    daily_returns = pv.pct_change().dropna()
    sharpe = np.nan
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = round(np.sqrt(252) * daily_returns.mean() / daily_returns.std(), 2)

    peak = pv.cummax()
    drawdown = (pv - peak) / peak * 100
    max_dd = round(drawdown.min(), 2)

    wins = sum(1 for t in trades if t["type"] == "SELL" and t["price"] > 0)
    loss = sum(1 for t in trades if t["type"] == "SELL" and t["price"] <= 0)
    win_rate = round(wins / max(len(trades) // 2, 1), 2) if trades else 0

    return {
        "symbol": symbol,
        "strategy": strategy,
        "total_return_pct": round(total_return, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_dd,
        "total_trades": len(trades),
        "win_rate": win_rate,
        "trade_log": trades[-20:],
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
    }


@tool(
    name="compare_strategies",
    description="比较多个策略的回测表现",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "strategies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "策略列表",
        },
    },
)
async def compare_strategies(symbol: str, market: str = "us_stock", strategies: list[str] | None = None) -> list[dict]:
    if strategies is None:
        strategies = ["sma_cross", "macd", "rsi", "bollinger"]
    results = []
    for s in strategies:
        result = await run_backtest(symbol=symbol, market=market, strategy=s)
        if "error" not in result:
            results.append({
                "strategy": s,
                "total_return_pct": result.get("total_return_pct"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "max_drawdown_pct": result.get("max_drawdown_pct"),
                "total_trades": result.get("total_trades"),
                "win_rate": result.get("win_rate"),
            })
    return sorted(results, key=lambda x: x.get("sharpe_ratio", 0) or 0, reverse=True)
