"""
Reversal and specialized strategies — RSI, RSI Divergence, MultiFactor,
CryptoFunding, EarningsMomentum.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Strategy


class RSIStrategy(Strategy):
    name = "rsi"
    description = "RSI 超买超卖反转策略（RSI<30买入，>70卖出）"
    type = "反转"
    tags = ["reversal", "rsi", "overbought-oversold"]
    markets = ["us_stock", "cn_stock", "hk_stock", "crypto"]
    params = {"period": "14", "oversold": "30", "overbought": "70"}
    risk_level = "中"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        signals = pd.Series(0, index=df.index)
        signals[rsi < 30] = 1
        signals[rsi > 70] = -1
        return signals


class RSIDivergenceStrategy(Strategy):
    name = "rsi_divergence"
    description = "RSI 背离（价格与 RSI 方向不一致时捕捉转折）"
    type = "反转"
    tags = ["rsi", "divergence", "reversal"]
    markets = ["us_stock", "crypto"]
    params = {"rsi_period": "14", "window": "10"}
    risk_level = "高"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        signals = pd.Series(0, index=df.index)
        window = 10
        for i in range(window * 2, len(df)):
            prev_low = df["Close"].iloc[i - window * 2:i - window].min()
            prev_high = df["Close"].iloc[i - window * 2:i - window].max()
            rsi_prev = rsi.iloc[i - window * 2:i - window]
            if df["Close"].iloc[i] < prev_low and rsi.iloc[i] > rsi_prev.min():
                signals.iloc[i] = 1
            elif df["Close"].iloc[i] > prev_high and rsi.iloc[i] < rsi_prev.max():
                signals.iloc[i] = -1
        return signals


class MultiFactorStrategy(Strategy):
    name = "multi_factor"
    description = "多因子评分（动量+低波+成交量综合打分）"
    type = "组合"
    tags = ["multi-factor", "scoring", "composite"]
    markets = ["us_stock", "cn_stock"]
    params = {"ret_lookback": "20", "vol_lookback": "20", "buy_threshold": "0.6", "sell_threshold": "0.4"}
    risk_level = "中"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ret_20 = df["Close"].pct_change(20)
        vol_20 = df["Close"].pct_change().rolling(20).std()
        ret_score = ret_20.rank(pct=True)
        vol_score = (-vol_20).rank(pct=True)
        avg_vol = df["Volume"].rolling(20).mean()
        vol_ratio = df["Volume"] / avg_vol.replace(0, np.nan)
        vol_ratio_score = vol_ratio.rank(pct=True)
        composite = 0.4 * ret_score + 0.3 * vol_score + 0.3 * vol_ratio_score
        signals = pd.Series(0, index=df.index)
        signals[composite > 0.6] = 1
        signals[composite < 0.4] = -1
        return signals


class CryptoFundingStrategy(Strategy):
    name = "crypto_funding"
    description = "加密货币资金费率套利（动量+波动率代理）"
    type = "事件驱动"
    tags = ["crypto", "funding-rate", "arbitrage"]
    markets = ["crypto"]
    params = {"momentum_period": "3", "vol_period": "9"}
    risk_level = "高"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ret_8h = df["Close"].pct_change(3)
        vol_24h = df["Close"].pct_change().rolling(9).std()
        momentum_signal = pd.Series(0, index=df.index)
        momentum_signal[ret_8h > 0.02] = 1
        momentum_signal[ret_8h < -0.02] = -1
        vol_signal = pd.Series(0, index=df.index)
        vol_signal[vol_24h > vol_24h.rolling(20).mean() * 1.5] = -1
        vol_signal[vol_24h < vol_24h.rolling(20).mean() * 0.5] = 1
        signals = pd.Series(0, index=df.index)
        signals[(momentum_signal == 1) & (vol_signal >= 0)] = 1
        signals[(momentum_signal == -1) & (vol_signal <= 0)] = -1
        return signals


class EarningsMomentumStrategy(Strategy):
    name = "earnings_momentum"
    description = "财报动量（财报跳空 >3% 后追踪趋势 5 天）"
    type = "事件驱动"
    tags = ["earnings", "event-driven", "post-earnings-drift"]
    markets = ["us_stock"]
    params = {"gap_threshold": "3.0", "hold_days": "5"}
    risk_level = "高"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        gap = df["Open"] / df["Close"].shift(1).replace(0, np.nan) - 1
        signals = pd.Series(0, index=df.index)
        for i in range(5, len(df)):
            if abs(gap.iloc[i]) > 0.03:
                post_gap_ret = df["Close"].iloc[i:min(i + 5, len(df))].pct_change().sum()
                if gap.iloc[i] > 0.03 and post_gap_ret > 0: signals.iloc[i] = 1
                elif gap.iloc[i] < -0.03 and post_gap_ret < 0: signals.iloc[i] = -1
        return signals
