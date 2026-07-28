"""
Technical K-line pattern factors.

Recognizes classic candlestick formations and produces
signal-oriented factor values (+1 = bullish, -1 = bearish, 0 = neutral).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def factor_doji(df: pd.DataFrame) -> pd.Series:
    """Doji: Open ≈ Close, body < 5% of range."""
    body = (df["Open"] - df["Close"]).abs()
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    return (body / h_l < 0.05).astype(float)


def factor_hammer(df: pd.DataFrame) -> pd.Series:
    """Hammer: small body, long lower shadow, minimal upper shadow."""
    body = (df["Close"] - df["Open"]).abs()
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    lower_shadow = df[["Open", "Close"]].min(axis=1) - df["Low"]
    upper_shadow = df["High"] - df[["Open", "Close"]].max(axis=1)
    is_hammer = (lower_shadow > 2 * body) & (upper_shadow < body * 0.5) & (body > 0)
    return is_hammer.astype(float)


def factor_engulfing(df: pd.DataFrame) -> pd.Series:
    """Bullish/Bearish engulfing."""
    prev_open = df["Open"].shift(1)
    prev_close = df["Close"].shift(1)
    bullish = (df["Close"] > prev_open) & (df["Open"] < prev_close) & (prev_close < prev_open)
    bearish = (df["Close"] < prev_open) & (df["Open"] > prev_close) & (prev_close > prev_open)
    return bullish.astype(float) - bearish.astype(float)


def factor_morning_star(df: pd.DataFrame) -> pd.Series:
    """Morning/Evening star (3-candle pattern)."""
    c1 = df["Close"].shift(2) - df["Open"].shift(2)
    c3 = df["Close"] - df["Open"]
    morning = (c1 < 0) & (df["Close"] > df["Open"].shift(2)) & (c3 > 0)
    evening = (c1 > 0) & (df["Close"] < df["Open"].shift(2)) & (c3 < 0)
    return morning.astype(float) - evening.astype(float)


def factor_marubozu(df: pd.DataFrame) -> pd.Series:
    """Marubozu: long body, no shadows."""
    body = (df["Close"] - df["Open"]).abs()
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    is_marubozu = body > h_l * 0.9
    bullish = is_marubozu & (df["Close"] > df["Open"])
    bearish = is_marubozu & (df["Close"] < df["Open"])
    return bullish.astype(float) - bearish.astype(float)


def factor_three_white_soldiers(df: pd.DataFrame) -> pd.Series:
    """Three white soldiers / three black crows."""
    c0 = df["Close"] > df["Open"]
    c1 = df["Close"].shift(1) > df["Open"].shift(1)
    c2 = df["Close"].shift(2) > df["Open"].shift(2)
    soldiers = c0 & c1 & c2
    crows = (~c0) & (~c1) & (~c2)
    return soldiers.astype(float) - crows.astype(float)


def factor_spinning_top(df: pd.DataFrame) -> pd.Series:
    """Spinning top: small body with long shadows on both sides."""
    body = (df["Close"] - df["Open"]).abs()
    h_l = (df["High"] - df["Low"]).replace(0, np.nan)
    lower = df[["Open", "Close"]].min(axis=1) - df["Low"]
    upper = df["High"] - df[["Open", "Close"]].max(axis=1)
    is_spinning = (body / h_l < 0.3) & (lower > body) & (upper > body)
    return is_spinning.astype(float) * np.where(df["Close"] > df["Open"], 1, -1)


def factor_tweezer_bottom(df: pd.DataFrame) -> pd.Series:
    """Tweezer bottom: two consecutive candles with equal lows."""
    low_eq = (df["Low"] - df["Low"].shift(1)).abs() < df["Close"].pct_change().abs().rolling(20).mean() * 0.1
    is_tweezer = low_eq & (df["Close"] > df["Open"])
    return is_tweezer.astype(float)


# ── Registry ──────────────────────────────────────────────────────────────────

TECHNICAL_FACTORS: dict[str, callable] = {
    "doji": factor_doji,
    "hammer": factor_hammer,
    "engulfing": factor_engulfing,
    "morning_star": factor_morning_star,
    "marubozu": factor_marubozu,
    "three_white_soldiers": factor_three_white_soldiers,
    "spinning_top": factor_spinning_top,
    "tweezer_bottom": factor_tweezer_bottom,
}
