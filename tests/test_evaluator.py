from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    factor = pd.Series(np.random.randn(n))
    returns = pd.Series(np.random.randn(n) * 0.02)
    return factor, returns


def test_compute_ic(sample_data):
    from agent.alpha.evaluator import FactorEvaluator
    factor, returns = sample_data
    ic = FactorEvaluator.compute_ic(factor, returns)
    assert len(ic) == len(factor)


def test_compute_sharpe(sample_data):
    from agent.alpha.evaluator import FactorEvaluator
    _, returns = sample_data
    sharpe = FactorEvaluator.compute_sharpe(returns)
    assert isinstance(sharpe, float)


def test_compute_max_drawdown(sample_data):
    from agent.alpha.evaluator import FactorEvaluator
    _, returns = sample_data
    mdd = FactorEvaluator.compute_max_drawdown(returns)
    assert isinstance(mdd, float)
    assert mdd <= 0


def test_evaluate(sample_data):
    from agent.alpha.evaluator import FactorEvaluator
    factor, returns = sample_data
    metrics = FactorEvaluator.evaluate(factor, returns)
    assert hasattr(metrics, "ic_mean")
    assert hasattr(metrics, "ir")
    assert hasattr(metrics, "sharpe")
    assert hasattr(metrics, "max_drawdown")


def test_rank_factors(sample_data):
    from agent.alpha.evaluator import FactorEvaluator, FactorMetrics
    metrics = {
        "factor_a": FactorMetrics(ic_mean=0.05, ic_std=0.1, ir=0.5, ic_positive_ratio=0.6, turnover=0.1, survival_rate=1.0, sharpe=1.2, max_drawdown=-0.1),
        "factor_b": FactorMetrics(ic_mean=0.02, ic_std=0.1, ir=0.2, ic_positive_ratio=0.55, turnover=0.15, survival_rate=1.0, sharpe=0.8, max_drawdown=-0.15),
    }
    ranked = FactorEvaluator.rank_factors(metrics, top_n=1)
    assert len(ranked) == 1
    assert ranked[0]["name"] == "factor_a"
