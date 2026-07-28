"""
Mean reversion strategies — Bollinger, ZScore, PairTrading, GapFill.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Strategy


class BollingerStrategy(Strategy):
    name = "bollinger"
    description = "布林带回归策略（触及下轨买入，上轨卖出）"
    type = "均值回归"
    tags = ["mean-reversion", "volatility", "bollinger"]
    markets = ["us_stock", "cn_stock", "hk_stock"]
    params = {"period": "20", "std": "2.0"}
    risk_level = "低"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        signals = pd.Series(0, index=df.index)
        signals[df["Close"] < lower] = 1
        signals[df["Close"] > upper] = -1
        return signals


class ZScoreMeanReversionStrategy(Strategy):
    name = "zscore_mean_reversion"
    description = "Z-score 均值回归（价格偏离均线超 2σ 反向操作）"
    type = "均值回归"
    tags = ["mean-reversion", "z-score", "statistical"]
    markets = ["us_stock", "cn_stock", "hk_stock"]
    params = {"ma_period": "20", "threshold": "2.0"}
    risk_level = "中"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        zscore = (df["Close"] - ma20) / std20.replace(0, np.nan)
        signals = pd.Series(0, index=df.index)
        signals[zscore < -2] = 1
        signals[zscore > 2] = -1
        return signals


class PairTradingStrategy(Strategy):
    name = "pair_trading"
    description = "配对交易（用基准对冲，价差偏离时反向操作）"
    type = "均值回归"
    tags = ["pair-trading", "market-neutral", "spread"]
    markets = ["us_stock", "hk_stock"]
    params = {"spread_period": "20", "threshold": "2.0"}
    risk_level = "中"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        benchmark = df.get("benchmark", df["Close"].rolling(20).mean())
        spread = df["Close"] / benchmark.replace(0, np.nan) - 1
        spread_ma = spread.rolling(20).mean()
        spread_std = spread.rolling(20).std()
        zscore = (spread - spread_ma) / spread_std.replace(0, np.nan)
        signals = pd.Series(0, index=df.index)
        signals[zscore < -2] = 1
        signals[zscore > 2] = -1
        signals[zscore.abs() < 0.5] = 0
        return signals


class GapFillStrategy(Strategy):
    name = "gap_fill"
    description = "缺口回补（跳空 >1% 后预期回补，高开做空低开做多）"
    type = "均值回归"
    tags = ["gap", "fill", "reversal"]
    markets = ["us_stock", "cn_stock"]
    params = {"gap_threshold": "1.0"}
    risk_level = "高"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        prev_close = df["Close"].shift(1)
        gap = (df["Open"] - prev_close) / prev_close.replace(0, np.nan) * 100
        signals = pd.Series(0, index=df.index)
        signals[gap > 1] = -1
        signals[gap < -1] = 1
        return signals
