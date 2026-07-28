"""
Alpha 191 Factors — High IC/IR academic alpha factors.

Reference: "101 Formulaic Alphas" (Kakushadze, 2015) — extended set.
Each function takes a DataFrame with OHLCV columns and returns a Series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Helper functions ──────────────────────────────────────────────────────────

def _ts_corr(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    return a.rolling(window).corr(b)


def _ts_rank(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])


def _ts_delta(s: pd.Series, period: int) -> pd.Series:
    return s - s.shift(period)


def _ts_sum(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).sum()


def _ts_mean(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).mean()


def _ts_std(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).std()


def _ts_min(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).min()


def _ts_max(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window).max()


def _ts_scale(s: pd.Series, k: int = 1) -> pd.Series:
    return s / s.abs().rolling(10).mean() * k


# ── Factor functions ──────────────────────────────────────────────────────────

def alpha_vwap_momentum(df: pd.DataFrame) -> pd.Series:
    """VWAP 20-day momentum relative to volume-weighted price."""
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    vwap = (typical * df["Volume"]).rolling(20).sum() / df["Volume"].rolling(20).sum()
    return df["Close"] / vwap.replace(0, np.nan) - 1


def alpha_intraday_reversal(df: pd.DataFrame) -> pd.Series:
    """Intraday reversal: (Close - Open) / (High - Low)."""
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    return -(df["Close"] - df["Open"]) / h_l


def alpha_price_volume_divergence(df: pd.DataFrame) -> pd.Series:
    """Price-volume divergence: price up + volume down = bearish."""
    ret_5d = df["Close"].pct_change(5)
    vol_chg_5d = df["Volume"].pct_change(5)
    return -ret_5d * vol_chg_5d


def alpha_turnover_price(df: pd.DataFrame) -> pd.Series:
    """Turnover-price correlation over 20 days."""
    turnover = df["Volume"] / df["Volume"].rolling(50).mean()
    return _ts_corr(turnover, df["Close"], 20)


def alpha_volatility_skew(df: pd.DataFrame) -> pd.Series:
    """Volatility skew: upside vol vs downside vol ratio."""
    ret_1d = df["Close"].pct_change()
    up_vol = ret_1d.clip(lower=0).rolling(20).std()
    dn_vol = (-ret_1d.clip(upper=0)).rolling(20).std()
    return (up_vol - dn_vol) / dn_vol.replace(0, np.nan)


def alpha_gap_reversal(df: pd.DataFrame) -> pd.Series:
    """Gap fill probability based on historical reversion rate."""
    gap = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1).replace(0, np.nan)
    return -gap.rolling(50).mean()


def alpha_relative_high_low(df: pd.DataFrame) -> pd.Series:
    """Position of Close within [Low, High] range relative to 20-day window."""
    high_20 = df["High"].rolling(20).max()
    low_20 = df["Low"].rolling(20).min()
    h_l = (high_20 - low_20).replace(0, np.nan)
    return (df["Close"] - low_20) / h_l


def alpha_overnight_gap(df: pd.DataFrame) -> pd.Series:
    """Overnight gap: (Open - PrevClose) / PrevClose."""
    return (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1).replace(0, np.nan)


def alpha_volume_price_trend(df: pd.DataFrame) -> pd.Series:
    """VPT: cumulative volume × price change indicator."""
    vpt = (df["Volume"] * df["Close"].pct_change()).cumsum()
    return vpt.diff(5)


def alpha_aroon(df: pd.DataFrame) -> pd.Series:
    """Aroon indicator: (aroon_up - aroon_down)."""
    high_25 = df["High"].rolling(25)
    low_25 = df["Low"].rolling(25)
    aroon_up = high_25.apply(lambda x: (25 - (len(x) - x.argmax())) / 25 * 100)
    aroon_down = low_25.apply(lambda x: (25 - (len(x) - x.argmin())) / 25 * 100)
    return aroon_up - aroon_down


def alpha_chaikin_mf(df: pd.DataFrame) -> pd.Series:
    """Chaikin Money Flow over 20 days."""
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    mf_multiplier = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / h_l
    mf_volume = mf_multiplier * df["Volume"]
    return mf_volume.rolling(20).sum() / df["Volume"].rolling(20).sum()


def alpha_elder_ray(df: pd.DataFrame) -> pd.Series:
    """Elder Ray: Bull Power - Bear Power."""
    ema13 = df["Close"].ewm(span=13).mean()
    return df["High"].rolling(2).max() - ema13


def alpha_price_momentum_osc(df: pd.DataFrame) -> pd.Series:
    """PMO: 35-period EMA of 20-day momentum."""
    mom = df["Close"].pct_change(20)
    return mom.ewm(span=35).mean()


# ── Registry ──────────────────────────────────────────────────────────────────

FACTORS_191: dict[str, callable] = {
    "vwap_momentum": alpha_vwap_momentum,
    "intraday_reversal": alpha_intraday_reversal,
    "price_volume_divergence": alpha_price_volume_divergence,
    "turnover_price": alpha_turnover_price,
    "volatility_skew": alpha_volatility_skew,
    "gap_reversal": alpha_gap_reversal,
    "relative_high_low": alpha_relative_high_low,
    "overnight_gap": alpha_overnight_gap,
    "volume_price_trend": alpha_volume_price_trend,
    "aroon": alpha_aroon,
    "chaikin_mf": alpha_chaikin_mf,
    "elder_ray": alpha_elder_ray,
    "price_momentum_osc": alpha_price_momentum_osc,
}
