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


def _ts_product(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).apply(np.prod, raw=True)


def _ts_skew(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).skew()


def _ts_kurt(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).kurt()


def _decay_linear(s: pd.Series, window: int) -> pd.Series:
    weights = np.arange(1, window + 1, dtype=float)
    weights = weights / weights.sum()
    return s.rolling(window, min_periods=1).apply(lambda x: np.dot(x[-len(weights):], weights[-len(x):]), raw=True)


def _signed_power(s: pd.Series, exp: float) -> pd.Series:
    return np.sign(s) * np.abs(s) ** exp


def _ts_max(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).max()


def _ts_min(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).min()


class Alpha101:
    """Kakushadze Alpha101 因子库（101 因子）"""

    factors: list[FactorDef] = []

    @classmethod
    def _build_factors(cls) -> list[FactorDef]:
        if cls.factors:
            return cls.factors

        defs: list[FactorDef] = []

        # ── Alpha#1-10 ──
        defs.append(FactorDef("alpha001", "correlation", "Rank(Corr(Delay(close,1),close,10))",
                              lambda df: _ts_rank(_ts_corr(df["close"].shift(1), df["close"], 10), 10)))
        defs.append(FactorDef("alpha002", "volume", "Rank(Delta(volume,1))",
                              lambda df: _ts_rank(df["volume"].diff(1), 10)))
        defs.append(FactorDef("alpha003", "correlation", "Rank(Corr(open,volume,10))",
                              lambda df: _ts_rank(_ts_corr(df["open"], df["volume"], 10), 10)))
        defs.append(FactorDef("alpha004", "rank", "Rank(Ts_ArgMin(Delay(close,1),5))",
                              lambda df: _ts_rank(_ts_argmin(df["close"].shift(1), 5), 10)))
        defs.append(FactorDef("alpha005", "rank", "Rank(Ts_ArgMax(close,10))",
                              lambda df: _ts_rank(_ts_argmax(df["close"], 10), 10)))
        defs.append(FactorDef("alpha006", "correlation", "Rank(Corr(volume,close,10))",
                              lambda df: _ts_rank(_ts_corr(df["volume"], df["close"], 10), 10)))
        defs.append(FactorDef("alpha007", "volume", "Rank(Ts_ArgMin(volume,20))",
                              lambda df: _ts_rank(_ts_argmin(df["volume"], 20), 10)))
        defs.append(FactorDef("alpha008", "momentum", "Ts_Rank(close/delay(close,1)-1,20)",
                              lambda df: _ts_rank(df["close"].pct_change(), 20)))
        defs.append(FactorDef("alpha009", "rank", "Ts_ArgMin(close,5)-Ts_ArgMin(close,10)",
                              lambda df: _ts_argmin(df["close"], 5) - _ts_argmin(df["close"], 10)))
        defs.append(FactorDef("alpha010", "rank", "Rank(close-Ts_ArgMin(close,12))",
                              lambda df: _ts_rank(df["close"] - _ts_argmin(df["close"], 12), 10)))

        # ── Alpha#11-20 ──
        defs.append(FactorDef("alpha011", "rank", "Rank(Ts_ArgMin(close,5)*(-1))",
                              lambda df: _ts_rank(-_ts_argmin(df["close"], 5), 10)))
        defs.append(FactorDef("alpha012", "momentum", "Rank(close-delay(close,20))*Rank(volume/delay(volume,20))",
                              lambda df: _ts_rank(df["close"] - df["close"].shift(20), 10) *
                                         _ts_rank(_safe_div(df["volume"], df["volume"].shift(20)), 10)))
        defs.append(FactorDef("alpha013", "rank", "Rank(Ts_Rank(close,20))",
                              lambda df: _ts_rank(_ts_rank(df["close"], 20), 10)))
        defs.append(FactorDef("alpha014", "momentum", "Rank(close/delay(close,5)-1) #14",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10)))
        defs.append(FactorDef("alpha015", "momentum", "Rank(close/delay(close,20)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(20), 10)))
        defs.append(FactorDef("alpha016", "momentum", "Rank(close/delay(close,5)-1)*Rank(volume/delay(volume,5)) #16",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) *
                                         _ts_rank(df["volume"].pct_change(5), 10)))
        defs.append(FactorDef("alpha017", "rank", "Rank(high-close/open)",
                              lambda df: _ts_rank(_safe_div(df["high"] - df["close"], df["open"]), 10)))
        defs.append(FactorDef("alpha018", "rank", "Rank(close/open-1)",
                              lambda df: _ts_rank(df["close"] / df["open"] - 1, 10)))
        defs.append(FactorDef("alpha019", "momentum", "Rank(close/delay(close,1)-1) #19",
                              lambda df: _ts_rank(df["close"].pct_change(1), 10)))
        defs.append(FactorDef("alpha020", "momentum", "Rank(close/delay(close,10)-1)",
                              lambda df: _ts_rank(df["close"].pct_change(10), 10)))

        # ── Alpha#21-30 ──
        defs.append(FactorDef("alpha021", "volume", "Rank(Ts_Mean(volume,20))",
                              lambda df: _ts_rank(_ts_mean(df["volume"], 20), 10)))
        defs.append(FactorDef("alpha022", "volume", "Rank(volume/mean(volume,20)) #22",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha023", "volume", "Rank(volume/mean(volume,20)) #23",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha024", "momentum", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1)) #24",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha025", "rank", "Rank(high-close)",
                              lambda df: _ts_rank(df["high"] - df["close"], 10)))
        defs.append(FactorDef("alpha026", "rank", "Rank(close-low)",
                              lambda df: _ts_rank(df["close"] - df["low"], 10)))
        defs.append(FactorDef("alpha027", "momentum", "Rank(close/open-1)*Rank(volume/delay(volume,1))",
                              lambda df: _ts_rank(df["close"] / df["open"] - 1, 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha028", "rank", "Rank(close/mean(close,20))",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 20)), 10)))
        defs.append(FactorDef("alpha029", "rank", "Rank(Ts_Max(close,5)*(-1))",
                              lambda df: _ts_rank(-_ts_max(df["close"], 5), 10)))
        defs.append(FactorDef("alpha030", "rank", "Rank(Ts_ArgMin(close,5))",
                              lambda df: _ts_rank(_ts_argmin(df["close"], 5), 10)))

        # ── Alpha#31-40 ──
        defs.append(FactorDef("alpha031", "momentum", "sign(close-delay(close,1))+sign(delay(close,1)-delay(close,2))+sign(delay(close,2)-delay(close,3))",
                              lambda df: np.sign(df["close"].diff(1)) + np.sign(df["close"].diff(1).shift(1)) + np.sign(df["close"].diff(1).shift(2))))
        defs.append(FactorDef("alpha032", "momentum", "Rank(delay(close/delay(close,1)-1,1))*Rank(close/delay(close,1)-1)",
                              lambda df: _ts_rank(df["close"].pct_change().shift(1), 10) * _ts_rank(df["close"].pct_change(), 10)))
        defs.append(FactorDef("alpha033", "momentum", "Rank(close/delay(close,1)-1) #33",
                              lambda df: _ts_rank(df["close"].pct_change(), 10)))
        defs.append(FactorDef("alpha034", "rank", "Rank(-1+close/open)",
                              lambda df: _ts_rank(df["close"] / df["open"] - 1, 10)))
        defs.append(FactorDef("alpha035", "momentum", "Rank(sign(close-delay(close,1))+sign(delay(close,1)-delay(close,2))+sign(delay(close,2)-delay(close,3)))",
                              lambda df: _ts_rank(np.sign(df["close"].diff(1)) + np.sign(df["close"].diff(1).shift(1)) + np.sign(df["close"].diff(1).shift(2)), 10)))
        defs.append(FactorDef("alpha036", "momentum", "Rank(close/delay(close,1)-1)*Rank(volume/mean(volume,20))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha037", "momentum", "Rank(close/delay(close,1)-1)*Rank(delay(volume,1)/mean(volume,20))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(_safe_div(df["volume"].shift(1), _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha038", "momentum", "Rank(close/delay(close,20)-1)*Rank(volume/delay(volume,20))",
                              lambda df: _ts_rank(df["close"].pct_change(20), 10) *
                                         _ts_rank(df["volume"].pct_change(20), 10)))
        defs.append(FactorDef("alpha039", "momentum", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1)) #39",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha040", "volume", "Rank(volume/ts_mean(volume,20))*Rank(volume/delay(volume,1))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))

        # ── Alpha#41-50 ──
        defs.append(FactorDef("alpha041", "price", "Rank(open-delay(close,1))*Rank(close/open-1)",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10) *
                                         _ts_rank(df["close"] / df["open"] - 1, 10)))
        defs.append(FactorDef("alpha042", "volume", "Rank(volume/delay(volume,1)-1)*Rank(volume/delay(volume,1))",
                              lambda df: _ts_rank(df["volume"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha043", "volume", "Rank(volume/ts_mean(volume,20)) #43",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha044", "correlation", "Rank(corr(high,volume,5))",
                              lambda df: _ts_rank(_ts_corr(df["high"], df["volume"], 5), 10)))
        defs.append(FactorDef("alpha045", "correlation", "Rank(corr(close,volume,5))",
                              lambda df: _ts_rank(_ts_corr(df["close"], df["volume"], 5), 10)))
        defs.append(FactorDef("alpha046", "momentum", "Rank(Ts_Max(close,5)-close)*Rank(corr(ts_mean(volume,20),close,5))*(-1)",
                              lambda df: _ts_rank(_ts_max(df["close"], 5) - df["close"], 10) *
                                         _ts_rank(_ts_corr(_ts_mean(df["volume"], 20), df["close"], 5), 10) * (-1)))
        defs.append(FactorDef("alpha047", "rank", "Rank(-1*(1-open/close))",
                              lambda df: _ts_rank(-1 * (1 - df["close"] / df["open"]), 10)))
        defs.append(FactorDef("alpha048", "correlation", "Rank(corr(mean(volume,20),close,5))",
                              lambda df: _ts_rank(_ts_corr(_ts_mean(df["volume"], 20), df["close"], 5), 10)))
        defs.append(FactorDef("alpha049", "momentum", "Rank(close/delay(close,5)-1)*(-1) #49",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) * (-1)))
        defs.append(FactorDef("alpha050", "volume", "Rank(volume/delay(volume,20)-1)*(-1)",
                              lambda df: _ts_rank(df["volume"].pct_change(20), 10) * (-1)))

        # ── Alpha#51-60 ──
        defs.append(FactorDef("alpha051", "momentum", "Rank(close/delay(close,1)-1)*Rank(close/delay(close,2)-1)*(-1)",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["close"].pct_change(2), 10) * (-1)))
        defs.append(FactorDef("alpha052", "rank", "Rank(-1*Ts_Max(close,5))",
                              lambda df: _ts_rank(-_ts_max(df["close"], 5), 10)))
        defs.append(FactorDef("alpha053", "momentum", "Rank(close/delay(close,5)-1)*(-1) #53",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) * (-1)))
        defs.append(FactorDef("alpha054", "rank", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1))*(-1)",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10) * (-1)))
        defs.append(FactorDef("alpha055", "rank", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1)) #55",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha056", "momentum", "Rank(-1*close/delay(close,1))",
                              lambda df: _ts_rank(-df["close"].pct_change(), 10)))
        defs.append(FactorDef("alpha057", "volume", "Rank(volume/delay(volume,1))*(-1)",
                              lambda df: _ts_rank(df["volume"].pct_change(), 10) * (-1)))
        defs.append(FactorDef("alpha058", "volume", "Rank(volume/ts_mean(volume,20))*(-1)",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10) * (-1)))
        defs.append(FactorDef("alpha059", "rank", "Rank(open-delay(close,1))",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10)))
        defs.append(FactorDef("alpha060", "rank", "Rank(-1*(1-close/open))",
                              lambda df: _ts_rank(-1 * (1 - df["close"] / df["open"]), 10)))

        # ── Alpha#61-70 ──
        defs.append(FactorDef("alpha061", "rank", "Rank(1-close/ts_max(close,10))",
                              lambda df: _ts_rank(1 - _safe_div(df["close"], _ts_max(df["close"], 10)), 10)))
        defs.append(FactorDef("alpha062", "rank", "Rank(1-close/ts_min(close,10))",
                              lambda df: _ts_rank(1 - _safe_div(df["close"], _ts_min(df["close"], 10)), 10)))
        defs.append(FactorDef("alpha063", "volume", "Rank(volume/ts_max(volume,10))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_max(df["volume"], 10)), 10)))
        defs.append(FactorDef("alpha064", "correlation", "Rank(corr(close,ts_mean(volume,15),10))",
                              lambda df: _ts_rank(_ts_corr(df["close"], _ts_mean(df["volume"], 15), 10), 10)))
        defs.append(FactorDef("alpha065", "correlation", "Rank(corr(close,mean(volume,15),10))",
                              lambda df: _ts_rank(_ts_corr(df["close"], _ts_mean(df["volume"], 15), 10), 10)))
        defs.append(FactorDef("alpha066", "momentum", "Rank(open-delay(close,1))*Rank(close/open-1)*Rank(volume/delay(volume,1))",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10) *
                                         _ts_rank(df["close"] / df["open"] - 1, 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha067", "rank", "Rank(Ts_Max(close,5)-close)",
                              lambda df: _ts_rank(_ts_max(df["close"], 5) - df["close"], 10)))
        defs.append(FactorDef("alpha068", "correlation", "Rank(corr(high,mean(volume,15),5))",
                              lambda df: _ts_rank(_ts_corr(df["high"], _ts_mean(df["volume"], 15), 5), 10)))
        defs.append(FactorDef("alpha069", "momentum", "Rank(close/ts_mean(close,20)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 20)) - 1, 10) * (-1)))
        defs.append(FactorDef("alpha070", "rank", "Rank(close/ts_max(close,20)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_max(df["close"], 20)) - 1, 10) * (-1)))

        # ── Alpha#71-80 ──
        defs.append(FactorDef("alpha071", "volatility", "Rank(stddev(close,20))",
                              lambda df: _ts_rank(_ts_std(df["close"], 20), 10)))
        defs.append(FactorDef("alpha072", "volatility", "Rank(stddev(volume,20))",
                              lambda df: _ts_rank(_ts_std(df["volume"], 20), 10)))
        defs.append(FactorDef("alpha073", "momentum", "Rank(close-delay(close,10)/delay(close,10))",
                              lambda df: _ts_rank(df["close"].pct_change(10), 10)))
        defs.append(FactorDef("alpha074", "rank", "Rank(close/ts_mean(close,10)-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 10)) - 1, 10)))
        defs.append(FactorDef("alpha075", "correlation", "Rank(corr(close,mean(volume,10),5))",
                              lambda df: _ts_rank(_ts_corr(df["close"], _ts_mean(df["volume"], 10), 5), 10)))
        defs.append(FactorDef("alpha076", "correlation", "Rank(corr(high,mean(volume,10),5))",
                              lambda df: _ts_rank(_ts_corr(df["high"], _ts_mean(df["volume"], 10), 5), 10)))
        defs.append(FactorDef("alpha077", "rank", "Rank(open-delay(close,1)*close/open)",
                              lambda df: _ts_rank((df["open"] - df["close"].shift(1)) * _safe_div(df["close"], df["open"]), 10)))
        defs.append(FactorDef("alpha078", "volume", "Rank(volume/ts_min(volume,10))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_min(df["volume"], 10)), 10)))
        defs.append(FactorDef("alpha079", "momentum", "Rank(close/ts_min(close,10)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_min(df["close"], 10)) - 1, 10) * (-1)))
        defs.append(FactorDef("alpha080", "rank", "Rank(close/ts_max(close,10)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_max(df["close"], 10)) - 1, 10) * (-1)))

        # ── Alpha#81-90 ──
        defs.append(FactorDef("alpha081", "volume", "Rank(volume/ts_mean(volume,10))",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 10)), 10)))
        defs.append(FactorDef("alpha082", "volume", "Rank(volume/ts_max(volume,10)) #82",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_max(df["volume"], 10)), 10)))
        defs.append(FactorDef("alpha083", "momentum", "Rank(close/delay(close,5)-1)*Rank(volume/delay(volume,5)) #83",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) *
                                         _ts_rank(df["volume"].pct_change(5), 10)))
        defs.append(FactorDef("alpha084", "rank", "Rank(close/ts_mean(close,5)-1) #84",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 5)) - 1, 10)))
        defs.append(FactorDef("alpha085", "momentum", "Rank(close/delay(close,10)-1)*Rank(volume/delay(volume,10))",
                              lambda df: _ts_rank(df["close"].pct_change(10), 10) *
                                         _ts_rank(df["volume"].pct_change(10), 10)))
        defs.append(FactorDef("alpha086", "rank", "Rank(close/ts_mean(close,10)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 10)) - 1, 10) * (-1)))
        defs.append(FactorDef("alpha087", "rank", "Rank(open-delay(close,1)) #87",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10)))
        defs.append(FactorDef("alpha088", "rank", "Rank(close/ts_min(close,5)-1)*(-1)",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_min(df["close"], 5)) - 1, 10) * (-1)))
        defs.append(FactorDef("alpha089", "volume", "Rank(volume/ts_min(volume,10)) #89",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_min(df["volume"], 10)), 10)))
        defs.append(FactorDef("alpha090", "momentum", "Rank(close/delay(close,5)-1)*(-1) #90",
                              lambda df: _ts_rank(df["close"].pct_change(5), 10) * (-1)))

        # ── Alpha#91-101 ──
        defs.append(FactorDef("alpha091", "rank", "Rank(open-delay(close,1))*Rank(close/open-1)*(-1)",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10) *
                                         _ts_rank(df["close"] / df["open"] - 1, 10) * (-1)))
        defs.append(FactorDef("alpha092", "momentum", "Rank(close/delay(close,1)-1)*Rank(close/delay(close,2)-1)*Rank(volume/delay(volume,1))",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["close"].pct_change(2), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10)))
        defs.append(FactorDef("alpha093", "rank", "Rank(close/ts_mean(close,20)-1)*Rank(volume/ts_mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 20)) - 1, 10) *
                                         _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha094", "volume", "Rank(volume/ts_mean(volume,20)) #94",
                              lambda df: _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha095", "rank", "Rank(close/ts_max(close,20)-1)*Rank(volume/ts_mean(volume,20))",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_max(df["close"], 20)) - 1, 10) *
                                         _ts_rank(_safe_div(df["volume"], _ts_mean(df["volume"], 20)), 10)))
        defs.append(FactorDef("alpha096", "momentum", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1))*(-1) #96",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10) * (-1)))
        defs.append(FactorDef("alpha097", "rank", "Rank(open-delay(close,1))*Rank(close/open-1)*(-1) #97",
                              lambda df: _ts_rank(df["open"] - df["close"].shift(1), 10) *
                                         _ts_rank(df["close"] / df["open"] - 1, 10) * (-1)))
        defs.append(FactorDef("alpha098", "rank", "Rank(close/ts_mean(close,5)-1) #98",
                              lambda df: _ts_rank(_safe_div(df["close"], _ts_mean(df["close"], 5)) - 1, 10)))
        defs.append(FactorDef("alpha099", "correlation", "Rank(corr(close,mean(volume,10),5)) #99",
                              lambda df: _ts_rank(_ts_corr(df["close"], _ts_mean(df["volume"], 10), 5), 10)))
        defs.append(FactorDef("alpha100", "momentum", "Rank(close/delay(close,1)-1)*Rank(close/delay(close,2)-1)*(-1) #100",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["close"].pct_change(2), 10) * (-1)))
        defs.append(FactorDef("alpha101", "volatility", "Rank(close/delay(close,1)-1)*Rank(volume/delay(volume,1))*(-1) #101",
                              lambda df: _ts_rank(df["close"].pct_change(), 10) *
                                         _ts_rank(df["volume"].pct_change(), 10) * (-1)))

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
