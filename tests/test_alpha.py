from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv():
    np.random.seed(42)
    n = 252
    dates = pd.date_range("2025-01-01", periods=n)
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    return pd.DataFrame({
        "date": dates,
        "open": close - np.random.rand(n),
        "high": close + np.random.rand(n) * 2,
        "low": close - np.random.rand(n) * 2,
        "close": close,
        "volume": np.random.randint(1000000, 10000000, n).astype(float),
    })


def test_alpha158_factor_count(sample_ohlcv):
    from agent.alpha import Alpha158
    factors = Alpha158.list_factors()
    assert len(factors) >= 150


def test_alpha158_compute(sample_ohlcv):
    from agent.alpha import Alpha158
    result = Alpha158.compute(sample_ohlcv)
    assert not result.empty
    assert len(result.columns) >= 150


def test_alpha158_compute_specific(sample_ohlcv):
    from agent.alpha import Alpha158
    result = Alpha158.compute(sample_ohlcv, factor_names=["KBAR_open", "RSI_12"])
    assert "KBAR_open" in result.columns
    assert "RSI_12" in result.columns


def test_alpha101_factor_count(sample_ohlcv):
    from agent.alpha import Alpha101
    factors = Alpha101.list_factors()
    assert len(factors) >= 101


def test_alpha101_compute(sample_ohlcv):
    from agent.alpha import Alpha101
    result = Alpha101.compute(sample_ohlcv)
    assert not result.empty
    assert len(result.columns) >= 101


def test_alpha101_uniqueness():
    from agent.alpha import Alpha101
    factors = Alpha101.list_factors()
    names = [f["name"] for f in factors]
    assert len(names) == len(set(names)), "Alpha101 factors should have unique names"
