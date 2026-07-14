import logging

import numpy as np
import pandas as pd

from .registry import tool

logger = logging.getLogger(__name__)


def _run_backtest_logic(
    df: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float = 100000.0,
    slippage_pct: float = 0.0,
    fee_rate: float = 0.0,
) -> dict:
    """核心回测逻辑，支持滑点和手续费"""
    position = 0
    capital = initial_capital
    shares = 0.0
    trades = []
    portfolio_value = []
    last_signal = 0

    for i in range(len(df)):
        sig = signals.iloc[i]
        price = df["Close"].iloc[i]

        if pd.isna(price) or price <= 0:
            equity = capital + shares * price if shares > 0 else capital
            portfolio_value.append(equity)
            continue

        if sig == 1 and last_signal != 1 and position <= 0:
            buy_price = price * (1 + slippage_pct / 100)
            cost = shares * buy_price if shares > 0 else 0
            fee = cost * fee_rate / 100 if shares > 0 else 0
            capital -= fee
            shares = capital / buy_price
            capital = 0.0
            position = 1
            trades.append({
                "date": str(df["Date"].iloc[i])[:10],
                "type": "BUY", "price": round(buy_price, 2),
                "shares": round(shares, 4), "fee": round(fee, 2),
            })
            last_signal = 1

        elif sig == -1 and last_signal != -1 and position >= 0 and shares > 0:
            sell_price = price * (1 - slippage_pct / 100)
            revenue = shares * sell_price
            fee = revenue * fee_rate / 100
            capital = revenue - fee
            pnl = round((sell_price / trades[-1]["price"] - 1) * 100, 2) if trades else 0
            trades.append({
                "date": str(df["Date"].iloc[i])[:10],
                "type": "SELL", "price": round(sell_price, 2),
                "shares": round(shares, 4), "fee": round(fee, 2),
                "pnl_pct": pnl,
            })
            shares = 0.0
            position = -1
            last_signal = -1

        equity = capital + shares * price
        portfolio_value.append(equity)

    if shares > 0:
        final_price = df["Close"].iloc[-1]
        fee = shares * final_price * fee_rate / 100
        capital = shares * final_price - fee
        shares = 0.0

    pv = pd.Series(portfolio_value)
    total_return = (capital - initial_capital) / initial_capital * 100

    daily_returns = pv.pct_change().dropna()
    sharpe = np.nan
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = round(np.sqrt(252) * daily_returns.mean() / daily_returns.std(), 2)

    peak = pv.cummax()
    drawdown = (pv - peak) / peak.replace(0, np.nan) * 100
    max_dd = round(drawdown.min(), 2) if not drawdown.empty else 0

    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = sum(1 for t in sell_trades if t.get("pnl_pct", 0) > 0)
    win_rate = round(wins / max(len(sell_trades), 1), 2)

    # 计算年化收益率
    trading_days = len(df)
    years = trading_days / 252 if trading_days > 0 else 1
    annualized_return = ((capital / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    return {
        "total_return_pct": round(total_return, 2),
        "annualized_return_pct": round(annualized_return, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_dd,
        "total_trades": len(trades),
        "win_rate": win_rate,
        "trade_log": trades[-20:],
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
    }


def _generate_signals(df: pd.DataFrame, strategy: str) -> pd.Series:
    """根据策略名称生成交易信号"""
    signals = pd.Series(0, index=df.index)

    if strategy == "sma_cross":
        sma20 = df["Close"].rolling(20).mean()
        sma50 = df["Close"].rolling(50).mean()
        signals[sma20 > sma50] = 1
        signals[sma20 < sma50] = -1

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

    elif strategy == "ichimoku":
        high_9 = df["High"].rolling(9).max()
        low_9 = df["Low"].rolling(9).min()
        tenkan = (high_9 + low_9) / 2
        high_26 = df["High"].rolling(26).max()
        low_26 = df["Low"].rolling(26).min()
        kijun = (high_26 + low_26) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((df["High"].rolling(52).max() + df["Low"].rolling(52).min()) / 2).shift(26)
        cloud_top = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
        cloud_bottom = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
        signals[(tenkan > kijun) & (df["Close"] > cloud_top)] = 1
        signals[(tenkan < kijun) & (df["Close"] < cloud_bottom)] = -1

    elif strategy == "smc":
        df = df.copy()
        df["h_20"] = df["High"].rolling(20).max()
        df["l_20"] = df["Low"].rolling(20).min()
        signals[(df["Close"] > df["h_20"].shift(1))] = 1
        signals[(df["Close"] < df["l_20"].shift(1))] = -1

    elif strategy == "multi_factor":
        ret_20 = df["Close"].pct_change(20)
        vol_20 = df["Close"].pct_change().rolling(20).std()
        vol_score = -vol_20.rank(pct=True)
        ret_score = ret_20.rank(pct=True)
        avg_vol = df["Volume"].rolling(20).mean()
        vol_ratio = df["Volume"] / avg_vol.replace(0, np.nan)
        vol_ratio_score = vol_ratio.rank(pct=True)
        composite = 0.4 * ret_score + 0.3 * vol_score + 0.3 * vol_ratio_score
        signals[composite > 0.6] = 1
        signals[composite < 0.4] = -1

    elif strategy == "crypto_funding":
        ret_8h = df["Close"].pct_change(3)
        vol_24h = df["Close"].pct_change().rolling(9).std()
        momentum_signal = pd.Series(0, index=df.index)
        momentum_signal[ret_8h > 0.02] = 1
        momentum_signal[ret_8h < -0.02] = -1
        vol_signal = pd.Series(0, index=df.index)
        vol_signal[vol_24h > vol_24h.rolling(20).mean() * 1.5] = -1
        vol_signal[vol_24h < vol_24h.rolling(20).mean() * 0.5] = 1
        signals[(momentum_signal == 1) & (vol_signal >= 0)] = 1
        signals[(momentum_signal == -1) & (vol_signal <= 0)] = -1

    return signals


async def _fetch_and_prepare_df(symbol: str, market: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """获取数据并预处理"""
    from .market_data import get_klines

    klines = await get_klines(symbol, market, interval="1d", period="2y")

    if not klines:
        return None

    df = pd.DataFrame(klines)
    date_col = "Date" if "Date" in df.columns else "date"
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "open" in df.columns:
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                           "close": "Close", "volume": "Volume"}, inplace=True)

    df["Date"] = pd.to_datetime(df[date_col])
    df = df.sort_values("Date").reset_index(drop=True)

    if start_date:
        df = df[df["Date"] >= start_date]
    if end_date:
        df = df[df["Date"] <= end_date]

    return df if len(df) >= 60 else None


@tool(
    name="run_backtest",
    description="运行策略回测（支持滑点和手续费）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
        "strategy": {"type": "string", "description": "策略: sma_cross, macd, rsi, bollinger, ichimoku, smc, multi_factor", "default": "sma_cross"},
        "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD", "default": ""},
        "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD", "default": ""},
        "initial_capital": {"type": "number", "description": "初始资金", "default": 100000},
        "slippage_pct": {"type": "number", "description": "滑点百分比，默认0.1", "default": 0.1},
        "fee_rate": {"type": "number", "description": "手续费率百分比，默认0.1", "default": 0.1},
    },
)
async def run_backtest(
    symbol: str,
    market: str = "us_stock",
    strategy: str = "sma_cross",
    start_date: str = "",
    end_date: str = "",
    initial_capital: float = 100000.0,
    slippage_pct: float = 0.1,
    fee_rate: float = 0.1,
) -> dict:
    df = await _fetch_and_prepare_df(symbol, market, start_date, end_date)
    if df is None:
        return {"error": "Insufficient data (need >= 60 rows)"}

    signals = _generate_signals(df, strategy)
    result = _run_backtest_logic(df, signals, initial_capital, slippage_pct, fee_rate)
    result["symbol"] = symbol
    result["strategy"] = strategy
    result["slippage_pct"] = slippage_pct
    result["fee_rate"] = fee_rate
    return result


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


@tool(
    name="monte_carlo_test",
    description="Monte Carlo 置换检验：随机打乱交易信号 N 次，评估策略是否显著",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "strategy": {"type": "string", "description": "策略", "default": "sma_cross"},
        "n_simulations": {"type": "integer", "description": "模拟次数，默认1000", "default": 1000},
    },
)
async def monte_carlo_test(
    symbol: str,
    market: str = "us_stock",
    strategy: str = "sma_cross",
    n_simulations: int = 1000,
) -> dict:
    df = await _fetch_and_prepare_df(symbol, market, "", "")
    if df is None:
        return {"error": "Insufficient data"}

    real_signals = _generate_signals(df, strategy)
    real_result = _run_backtest_logic(df, real_signals)
    real_return = real_result["total_return_pct"]

    simulated_returns = []
    for _ in range(n_simulations):
        shuffled = real_signals.sample(frac=1, random_state=None).reset_index(drop=True)
        res = _run_backtest_logic(df, shuffled)
        simulated_returns.append(res["total_return_pct"])

    simulated_returns = np.array(simulated_returns)
    p_value = float(np.mean(simulated_returns >= real_return))
    ci_lower = float(np.percentile(simulated_returns, 5))
    ci_upper = float(np.percentile(simulated_returns, 95))

    return {
        "symbol": symbol, "strategy": strategy,
        "real_return_pct": round(real_return, 2),
        "simulated_mean_pct": round(float(simulated_returns.mean()), 2),
        "simulated_std_pct": round(float(simulated_returns.std()), 2),
        "p_value": round(p_value, 4),
        "significant_95": p_value < 0.05,
        "confidence_interval_90": [round(ci_lower, 2), round(ci_upper, 2)],
        "n_simulations": n_simulations,
    }


@tool(
    name="walk_forward_test",
    description="Walk-Forward 滚动窗口回测：避免过拟合，评估策略在样本外的表现",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "strategy": {"type": "string", "description": "策略", "default": "sma_cross"},
        "train_days": {"type": "integer", "description": "训练窗口天数，默认252（1年）", "default": 252},
        "test_days": {"type": "integer", "description": "测试窗口天数，默认63（1季度）", "default": 63},
    },
)
async def walk_forward_test(
    symbol: str,
    market: str = "us_stock",
    strategy: str = "sma_cross",
    train_days: int = 252,
    test_days: int = 63,
) -> dict:
    df = await _fetch_and_prepare_df(symbol, market, "", "")
    if df is None:
        return {"error": "Insufficient data"}

    window_results = []
    n = len(df)
    start = 0

    while start + train_days + test_days <= n:
        train_df = df.iloc[start:start + train_days].reset_index(drop=True)
        test_df = df.iloc[start + train_days:start + train_days + test_days].reset_index(drop=True)

        train_signals = _generate_signals(train_df, strategy)
        test_signals = _generate_signals(test_df, strategy)

        train_res = _run_backtest_logic(train_df, train_signals)
        test_res = _run_backtest_logic(test_df, test_signals)

        window_results.append({
            "train_start": str(train_df["Date"].iloc[0])[:10],
            "train_end": str(train_df["Date"].iloc[-1])[:10],
            "test_start": str(test_df["Date"].iloc[0])[:10],
            "test_end": str(test_df["Date"].iloc[-1])[:10],
            "train_return_pct": train_res["total_return_pct"],
            "test_return_pct": test_res["total_return_pct"],
            "train_sharpe": train_res["sharpe_ratio"],
            "test_sharpe": test_res["sharpe_ratio"],
        })

        start += test_days

    if not window_results:
        return {"error": "Not enough data for walk-forward analysis"}

    avg_train = np.mean([w["train_return_pct"] for w in window_results])
    avg_test = np.mean([w["test_return_pct"] for w in window_results])
    avg_train_sharpe = np.mean([w["train_sharpe"] for w in window_results if not np.isnan(w["train_sharpe"])])
    avg_test_sharpe = np.mean([w["test_sharpe"] for w in window_results if not np.isnan(w["test_sharpe"])])

    return {
        "symbol": symbol, "strategy": strategy,
        "n_windows": len(window_results),
        "avg_train_return_pct": round(float(avg_train), 2),
        "avg_test_return_pct": round(float(avg_test), 2),
        "avg_train_sharpe": round(float(avg_train_sharpe), 2),
        "avg_test_sharpe": round(float(avg_test_sharpe), 2),
        "overfitting_ratio": round(float(avg_test / avg_train), 2) if avg_train != 0 else None,
        "windows": window_results,
    }
