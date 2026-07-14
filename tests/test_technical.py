from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agent.tools.technical import (
    _sma,
    _ema,
    _rsi,
    _macd,
    _bbands,
    _atr,
    _stoch,
    _adx,
)


def _create_series(n: int = 100) -> pd.Series:
    np.random.seed(42)
    return pd.Series(100 + np.cumsum(np.random.randn(n) * 2))


def _create_hlcv(n: int = 100) -> pd.DataFrame:
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    return pd.DataFrame({
        "Open": close - np.random.rand(n),
        "High": close + np.random.rand(n) * 2,
        "Low": close - np.random.rand(n) * 2,
        "Close": close,
        "Volume": np.random.randint(1000, 10000, n),
    })


def test_sma():
    s = _create_series(100)
    result = _sma(s, 20)
    assert len(result) == 100
    assert pd.notna(result.iloc[-1])
    assert result.iloc[:19].isna().all()


def test_ema():
    s = _create_series(100)
    result = _ema(s, 12)
    assert len(result) == 100
    assert pd.notna(result.iloc[-1])


def test_rsi():
    s = _create_series(100)
    result = _rsi(s, 14)
    assert len(result) == 100
    assert pd.notna(result.iloc[-1])
    assert 0 <= result.iloc[-1] <= 100


def test_macd():
    s = _create_series(100)
    result = _macd(s)
    assert len(result) == 100
    assert result.shape[1] == 3
    assert all(col in result.columns for col in ["MACD_12_26_9", "MACDs_12_26_9", "MACDh_12_26_9"])


def test_bbands():
    s = _create_series(100)
    result = _bbands(s)
    assert len(result) == 100
    assert result.shape[1] == 3
    assert all(col in result.columns for col in ["BBL_20_2.0", "BBM_20_2.0", "BBU_20_2.0"])
    assert result["BBU_20_2.0"].iloc[-1] > result["BBL_20_2.0"].iloc[-1]


def test_atr():
    df = _create_hlcv(100)
    result = _atr(df["High"], df["Low"], df["Close"], 14)
    assert len(result) == 100
    assert pd.notna(result.iloc[-1])
    assert result.iloc[-1] > 0


def test_stoch():
    df = _create_hlcv(100)
    result = _stoch(df["High"], df["Low"], df["Close"])
    assert len(result) == 100
    assert result.shape[1] == 2
    assert 0 <= result.iloc[-1, 0] <= 100


def test_adx():
    df = _create_hlcv(100)
    result = _adx(df["High"], df["Low"], df["Close"])
    assert len(result) == 100
    assert result.shape[1] == 3
