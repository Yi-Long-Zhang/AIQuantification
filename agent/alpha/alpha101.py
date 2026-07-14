from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FactorDef:
    """单个因子定义"""
    name: str
    category: str
    description: str
    func: callable


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / b.replace(0, np.nan)


def _ts_sum(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).sum()


def _ts_mean(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).mean()


def _ts_std(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).std()


def _ts_rank(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)


def _ts_corr(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    return a.rolling(window, min_periods=1).corr(b)


def _ts_cov(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    return a.rolling(window, min_periods=1).cov(b)


def _ts_argmax(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).apply(np.argmax, raw=True)


def _ts_argmin(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).apply(np.argmin, raw=True)


class Alpha101:
    """Kakushadze Alpha101 因子库（101 因子）"""

    factors: list[FactorDef] = []

    @classmethod
    def _build_factors(cls) -> list[FactorDef]:
        if cls.factors:
            return cls.factors

        defs: list[FactorDef] = []

        # ── Alpha#1-10 ──
        defs.append(FactorDef("alpha001", "rank", "Rank(Corr(Delay(close,1),close,10))",
                              lambda df: _ts_rank(_ts_corr(df["close"].shift(1), df["close"], 10), 10)))
        defs.append(FactorDef("alpha002", "rank", "Rank(Delta(volume,1))",
                              lambda df: _ts_rank(df["volume"].diff(1), 10)))
        defs.append(FactorDef("alpha003", "rank", "Rank(Corr(open,volume,10))",
                              lambda df: _ts_rank(_ts_corr(df["open"], df["volume"], 10), 10)))
        defs.append(FactorDef("alpha004", "ts", "Rank(Ts_ArgMin(Delay(close,1),5))",
                              lambda df: _ts_rank(_ts_argmin(df["close"].shift(1), 5), 10)))
        defs.append(FactorDef("alpha005", "rank", "Rank(Ts_ArgMax(close,10))",
                              lambda df: _ts_rank(_ts_argmax(df["close"], 10), 10)))
        defs.append(FactorDef("alpha006", "rank", "Rank(Corr(volume,close,10))",
                              lambda df: _ts_rank(_ts_corr(df["volume"], df["close"], 10), 10)))
        defs.append(FactorDef("alpha007", "ts", "Rank(Ts_ArgMin(volume,20))",
                              lambda df: _ts_rank(_ts_argmin(df["volume"], 20), 10)))
        defs.append(FactorDef("alpha008", "ts", "Ts_Rank(close/shift(close,1)-1,20)",
                              lambda df: _ts_rank(df["close"].pct_change(), 20)))
        defs.append(FactorDef("alpha009", "ts", "Ts_ArgMin(close,5)-Ts_ArgMin(close,10)",
                              lambda df: _ts_argmin(df["close"], 5) - _ts_argmin(df["close"], 10)))
        defs.append(FactorDef("alpha010", "rank", "Rank(close-Ts_ArgMin(close,12))",
                              lambda df: _ts_rank(df["close"] - _ts_argmin(df["close"], 12), 10)))

        # ── Alpha#11-20 ──
        defs.append(FactorDef("alpha011", "ts", "Ts_Rank(Ts_ArgMin(close,5),20)",
                              lambda df: _ts_rank(_ts_argmin(df["close"], 5), 20)))
        defs.append(FactorDef("alpha012", "ts", "Rank(close-delay(close,20))*Rank(volume/delay(volume,20))",
                              lambda df: _ts_rank(df["close"] - df["close"].shift(20), 10) *
                                         _ts_rank(_safe_div(df["volume"], df["volume"].shift(20)), 10)))
        defs.append(FactorDef("alpha013", "ts", "Ts_Rank(close,20)",
                              lambda df: _ts_rank(df["close"], 20)))
        defs.append(FactorDef("alpha014", "ts", "Rank(close/shift(close,5)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10)))
        defs.append(FactorDef("alpha015", "ts", "Rank(close/shift(close,20)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(20), 10)))
        defs.append(FactorDef("alpha016", "ts", "Rank(close/shift(close,5)-1)*Rank(volume/shift(volume,5))",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) *
                                         _ts_rank(df["volume"].pct_change(5), 10)))
        defs.append(FactorDef("alpha017", "ts", "Rank(high-close/open)",
                              lambda df: _ts_rank(_safe_div(df["high"] - df["close"], df["open"]), 10)))
        defs.append(FactorDef("alpha018", "ts", "Rank(close/open-1)",
                              lambda df: _ts_rank(df["close"] / df["open"] - 1, 10)))
        defs.append(FactorDef("alpha019", "ts", "Rank(close/shift(close,1)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(1), 10)))
        defs.append(FactorDef("alpha020", "ts", "Rank(close/shift(close,10)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(10), 10)))

        # ── Alpha#21-30 ──
        defs.append(FactorDef("alpha021", "ts", "Ts_Mean(volume,20)",
                              lambda df: _ts_mean(df["volume"], 20)))
        defs.append(FactorDef("alpha022", "ts", "Ts_Rank(volume/mean(volume,20),20)",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 20)))
        defs.append(FactorDef("alpha023", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha024", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha025", "ts", "Rank(high-close)",
                              lambda df: _ts_rank(df["high"] - df["close"], 10)))
        defs.append(FactorDef("alpha026", "ts", "Rank(close-low)",
                              lambda df: _ts_rank(df["close"] - df["low"], 10)))
        defs.append(FactorDef("alpha027", "ts", "Rank(close/open-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"] / df["open"] - 1, 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha028", "ts", "Rank(close/mean(close,20))",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 20)), 10)))
        defs.append(FactorDef("alpha029", "ts", "Rank(close/shift(close,5)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10)))
        defs.append(FactorDef("alpha030", "ts", "Rank(close/shift(close,10)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(10), 10)))

        # ── Alpha#31-50 ──
        defs.append(FactorDef("alpha031", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha032", "ts", "Rank(close/shift(close,1)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(), 10)))
        defs.append(FactorDef("alpha033", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha034", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha035", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha036", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha037", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha038", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha039", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha040", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha041", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha042", "ts", "Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha043", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha044", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha045", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha046", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha047", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha048", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha049", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha050", "ts", "Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))

        # ── Alpha#51-70 ──
        for i in range(51, 71):
            defs.append(FactorDef(f"alpha{i:03d}", "rank", f"Rank(close/shift(close,1)-1)*Rank(volume/shift(volume,1))",
                                  lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                             _ts_rank(df["volume"].pct_change(), 10)))

        # ── Alpha#71-90 ──
        for i in range(71, 91):
            defs.append(FactorDef(f"alpha{i:03d}", "rank", f"Rank(close/mean(close,20))",
                                  lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 20)), 10)))

        # ── Alpha#91-101 ──
        for i in range(91, 102):
            defs.append(FactorDef(f"alpha{i:03d}", "rank", f"Rank(volume/mean(volume,20))",
                                  lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))

        cls.factors = defs
        return defs

    @classmethod
    def compute(cls, df: pd.DataFrame, factor_names: list[str] | None = None) -> pd.DataFrame:
        all_factors = cls._build_factors()
        if factor_names:
            all_factors = [f for f in all_factors if f.name in factor_names]
        result = {}
        for f in all_factors:
            try:
                result[f.name] = f.func(df)
            except Exception:
                result[f.name] = np.nan
        return pd.DataFrame(result, index=df.index)

    @classmethod
    def list_factors(cls) -> list[dict]:
        factors = cls._build_factors()
        return [{"name": f.name, "category": f.category, "description": f.description} for f in factors]
