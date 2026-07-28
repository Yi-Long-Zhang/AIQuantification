"""
Strategy Evaluator — Cross-strategy comparison and factor attribution.

Provides batch evaluation of multiple strategies on the same data,
computing performance metrics and ranking strategies by Sharpe ratio.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from .registry import get_strategy

logger = logging.getLogger(__name__)


def evaluate_strategy(
    strategy_name: str,
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    fee_rate: float = 0.001,
) -> dict[str, Any]:
    """Evaluate a single strategy and return metrics."""
    strategy = get_strategy(strategy_name)
    if strategy is None:
        return {"error": f"Strategy '{strategy_name}' not found", "strategy_name": strategy_name}

    signals = strategy.generate_signals(df)

    # Run backtest logic
    position = 0
    capital = initial_capital
    shares = 0.0
    trades: list[dict] = []
    equity_curve: list[float] = []

    for i in range(len(df)):
        price = float(df["Close"].iloc[i])
        signal = int(signals.iloc[i])

        if signal != 0 and signal != position:
            # Close existing
            if position != 0 and shares > 0:
                sell_value = shares * price * (1 - fee_rate)
                capital = sell_value
                trades.append({
                    "entry": f"bar_{len(equity_curve)}",
                    "side": "sell" if position == 1 else "cover",
                    "price": price,
                    "pnl": capital - (shares * prev_entry),
                })
                shares = 0.0
            # Open new
            if signal != 0:
                shares = (capital * (1 - fee_rate)) / price
                prev_entry = price
            position = signal

        equity = capital if shares == 0 else shares * price
        equity_curve.append(equity)

    # Close final position
    if shares > 0:
        capital = shares * df["Close"].iloc[-1] * (1 - fee_rate)

    # Compute metrics
    equity_series = pd.Series(equity_curve)
    returns = equity_series.pct_change().dropna()
    total_return = (capital - initial_capital) / initial_capital * 100
    sharpe = _sharpe_ratio(returns)
    max_dd = _max_drawdown(equity_series)
    win_rate = sum(1 for t in trades if t.get("pnl", 0) > 0) / max(len(trades), 1) if trades else 0

    return {
        "strategy_name": strategy_name,
        "strategy_type": strategy.type,
        "total_return_pct": round(total_return, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "total_trades": len(trades),
        "win_rate": round(win_rate, 3),
        "final_capital": round(capital, 2),
    }


def compare_strategies(
    strategy_names: list[str],
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    Batch evaluate multiple strategies and rank by Sharpe ratio.

    Returns top_n strategies sorted by Sharpe ratio descending.
    """
    results = []
    for name in strategy_names:
        try:
            result = evaluate_strategy(name, df, initial_capital)
            if "error" not in result:
                results.append(result)
        except Exception as e:
            logger.debug(f"Strategy {name} evaluation failed: {e}")

    results.sort(key=lambda r: r.get("sharpe_ratio", -999), reverse=True)
    return results[:top_n]


def factor_attribution(
    strategy_name: str,
    df: pd.DataFrame,
    factor_names: list[str],
) -> dict[str, Any]:
    """
    Attribute strategy returns to alpha factors.
    Returns factor exposures and contribution.
    """
    strategy = get_strategy(strategy_name)
    if strategy is None:
        return {"error": f"Strategy '{strategy_name}' not found"}

    signals = strategy.generate_signals(df)
    returns = df["Close"].pct_change().dropna()

    factors = {}
    for fname in factor_names:
        try:
            from agent.alpha.evaluator import compute_factor
            factor_series = compute_factor(fname, df)
            if factor_series is not None:
                factors[fname] = factor_series
        except Exception as e:
            logger.debug("Factor %s attribution skipped: %s", fname, e)
            continue

    if not factors:
        return {"error": "No valid factors computed", "strategy_name": strategy_name}

    factor_df = pd.DataFrame(factors)
    strategy_signals = signals.shift(1).loc[returns.index].dropna()
    common_idx = strategy_signals.index.intersection(factor_df.index)

    if len(common_idx) < 20:
        return {"error": "Insufficient overlapping data", "strategy_name": strategy_name}

    # Simple: IC per factor (correlation with strategy returns)
    strategy_returns = returns.loc[common_idx] * strategy_signals.loc[common_idx]
    ic_results = {}
    for fname in factor_df.columns:
        ic = factor_df[fname].loc[common_idx].corr(strategy_returns)
        ic_results[fname] = round(float(ic) if not np.isnan(ic) else 0, 4)

    return {
        "strategy_name": strategy_name,
        "factor_ic": ic_results,
        "top_factor": max(ic_results, key=ic_results.get) if ic_results else None,
    }


def _sharpe_ratio(returns: pd.Series, risk_free: float = 0.02) -> float:
    if len(returns) < 2 or returns.std() == 0:
        return 0
    annual_factor = np.sqrt(252)
    return float((returns.mean() - risk_free / 252) / returns.std() * annual_factor)


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak.replace(0, np.nan) * 100
    return float(dd.min())
