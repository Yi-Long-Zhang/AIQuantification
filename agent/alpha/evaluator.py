from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class FactorMetrics:
    """因子评估指标"""
    ic_mean: float
    ic_std: float
    ir: float
    ic_positive_ratio: float
    turnover: float
    survival_rate: float
    sharpe: float
    max_drawdown: float


class FactorEvaluator:
    """因子评估器"""

    @staticmethod
    def compute_ic(factor_values: pd.Series, returns: pd.Series, method: str = "spearman") -> pd.Series:
        if method == "spearman":
            def _spearman_corr(window_size: int = 20) -> pd.Series:
                result = pd.Series(np.nan, index=factor_values.index)
                f_arr = factor_values.values
                r_arr = returns.values
                for i in range(window_size - 1, len(f_arr)):
                    f_win = f_arr[i - window_size + 1: i + 1]
                    r_win = r_arr[i - window_size + 1: i + 1]
                    valid = np.isfinite(f_win) & np.isfinite(r_win)
                    if valid.sum() >= 5:
                        result.iloc[i] = float(pd.Series(f_win[valid]).corr(pd.Series(r_win[valid]), method="spearman"))
                return result
            return _spearman_corr()
        return factor_values.rolling(20, min_periods=5).corr(returns)

    @staticmethod
    def compute_rank_ic(factor_values: pd.Series, returns: pd.Series) -> pd.Series:
        return FactorEvaluator.compute_ic(factor_values, returns, method="spearman")

    @staticmethod
    def compute_turnover(factor_values: pd.Series, top_pct: float = 0.1) -> float:
        n_top = max(1, int(len(factor_values) * top_pct))
        rank = factor_values.rank(pct=True)
        is_top = rank >= (1 - top_pct)
        turnover = is_top.astype(int).diff().abs().sum()
        total_periods = len(factor_values) - 1
        if total_periods == 0:
            return 0.0
        return turnover / total_periods

    @staticmethod
    def compute_survival_rate(factor_values: pd.DataFrame) -> float:
        if factor_values.empty:
            return 0.0
        non_nan_ratio = factor_values.notna().mean().mean()
        return float(non_nan_ratio)

    @staticmethod
    def compute_sharpe(returns: pd.Series, risk_free: float = 0.0) -> float:
        if len(returns) < 2:
            return 0.0
        excess = returns - risk_free
        return float(excess.mean() / excess.std() * np.sqrt(252)) if excess.std() > 0 else 0.0

    @staticmethod
    def compute_max_drawdown(returns: pd.Series) -> float:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())

    @classmethod
    def evaluate(cls, factor_values: pd.Series, forward_returns: pd.Series) -> FactorMetrics:
        ic_series = cls.compute_ic(factor_values, forward_returns)
        ic_mean = float(ic_series.mean()) if not ic_series.empty else 0.0
        ic_std = float(ic_series.std()) if not ic_series.empty else 1.0
        ir = ic_mean / ic_std if ic_std > 0 else 0.0
        ic_positive = (ic_series > 0).mean() if not ic_series.empty else 0.0

        turnover = cls.compute_turnover(factor_values)
        sharpe = cls.compute_sharpe(forward_returns)
        max_dd = cls.compute_max_drawdown(forward_returns)

        survival = cls.compute_survival_rate(pd.DataFrame({"f": factor_values}))

        return FactorMetrics(
            ic_mean=ic_mean,
            ic_std=ic_std,
            ir=ir,
            ic_positive_ratio=float(ic_positive),
            turnover=turnover,
            survival_rate=survival,
            sharpe=sharpe,
            max_drawdown=max_dd,
        )

    @classmethod
    def evaluate_batch(cls, factor_df: pd.DataFrame, forward_returns: pd.Series) -> dict[str, FactorMetrics]:
        results = {}
        for col in factor_df.columns:
            try:
                results[col] = cls.evaluate(factor_df[col], forward_returns)
            except Exception as e:
                logger.warning("Failed to evaluate factor %s: %s", col, e)
        return results

    @classmethod
    def rank_factors(cls, metrics: dict[str, FactorMetrics], top_n: int = 20) -> list[dict]:
        sorted_factors = sorted(metrics.items(), key=lambda x: abs(x[1].ir), reverse=True)
        return [
            {
                "name": name,
                "ic_mean": round(m.ic_mean, 4),
                "ir": round(m.ir, 4),
                "turnover": round(m.turnover, 4),
                "sharpe": round(m.sharpe, 4),
                "max_drawdown": round(m.max_drawdown, 4),
            }
            for name, m in sorted_factors[:top_n]
        ]
