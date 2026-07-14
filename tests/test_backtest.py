import numpy as np
import pandas as pd
import pytest
from agent.tools.backtest import (
    _generate_signals,
    _run_backtest_logic,
)
from agent.tools.market_data import _validate_ohlcv


def _create_test_df(n: int = 100) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    return pd.DataFrame({
        "Date": dates,
        "Open": close - np.random.rand(n),
        "High": close + np.random.rand(n) * 2,
        "Low": close - np.random.rand(n) * 2,
        "Close": close,
        "Volume": np.random.randint(1000, 10000, n),
    })


def test_generate_signals_sma_cross():
    df = _create_test_df(100)
    signals = _generate_signals(df, "sma_cross")
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_generate_signals_macd():
    df = _create_test_df(100)
    signals = _generate_signals(df, "macd")
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_generate_signals_rsi():
    df = _create_test_df(100)
    signals = _generate_signals(df, "rsi")
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_generate_signals_bollinger():
    df = _create_test_df(100)
    signals = _generate_signals(df, "bollinger")
    assert len(signals) == len(df)
    assert set(signals.unique()).issubset({-1, 0, 1})


def test_run_backtest_logic_basic():
    df = _create_test_df(100)
    signals = pd.Series(0, index=df.index)
    signals.iloc[20:50] = 1
    signals.iloc[50:80] = -1

    result = _run_backtest_logic(df, signals, initial_capital=100000)
    assert "total_return_pct" in result
    assert "sharpe_ratio" in result
    assert "max_drawdown_pct" in result
    assert "total_trades" in result
    assert "win_rate" in result
    assert "annualized_return_pct" in result


def test_run_backtest_logic_with_fees():
    df = _create_test_df(100)
    signals = pd.Series(0, index=df.index)
    signals.iloc[20:50] = 1
    signals.iloc[50:80] = -1

    result_no_fee = _run_backtest_logic(df, signals, initial_capital=100000, fee_rate=0.0)
    result_with_fee = _run_backtest_logic(df, signals, initial_capital=100000, fee_rate=0.1)
    assert result_with_fee["final_capital"] <= result_no_fee["final_capital"]


def test_run_backtest_logic_with_slippage():
    df = _create_test_df(100)
    signals = pd.Series(0, index=df.index)
    signals.iloc[20:50] = 1
    signals.iloc[50:80] = -1

    result_no_slip = _run_backtest_logic(df, signals, initial_capital=100000, slippage_pct=0.0)
    result_with_slip = _run_backtest_logic(df, signals, initial_capital=100000, slippage_pct=0.5)
    assert result_with_slip["final_capital"] <= result_no_slip["final_capital"]


def test_validate_ohlcv():
    df = _create_test_df(100)
    df.loc[5, "high"] = df.loc[5, "low"] - 1
    validated = _validate_ohlcv(df)
    assert len(validated) == len(df) - 1
