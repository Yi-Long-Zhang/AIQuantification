from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .base import Strategy


class SMACrossStrategy(Strategy):
    name = "sma_cross"
    description = "SMA 均线交叉策略（20日均线上穿50日均线买入）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sma20 = df["Close"].rolling(20).mean()
        sma50 = df["Close"].rolling(50).mean()
        signals = pd.Series(0, index=df.index)
        signals[sma20 > sma50] = 1
        signals[sma20 < sma50] = -1
        return signals


class MACDStrategy(Strategy):
    name = "macd"
    description = "MACD 趋势跟踪策略"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        exp12 = df["Close"].ewm(span=12).mean()
        exp26 = df["Close"].ewm(span=26).mean()
        macd_line = exp12 - exp26
        signal_line = macd_line.ewm(span=9).mean()
        signals = pd.Series(0, index=df.index)
        signals[macd_line > signal_line] = 1
        signals[macd_line < signal_line] = -1
        return signals


class RSIStrategy(Strategy):
    name = "rsi"
    description = "RSI 超买超卖反转策略"

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


class BollingerStrategy(Strategy):
    name = "bollinger"
    description = "布林带回归策略"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sma20 = df["Close"].rolling(20).mean()
        std20 = df["Close"].rolling(20).std()
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        signals = pd.Series(0, index=df.index)
        signals[df["Close"] < lower] = 1
        signals[df["Close"] > upper] = -1
        return signals


class IchimokuStrategy(Strategy):
    name = "ichimoku"
    description = "一目均衡表策略（转换线/基准线/云带综合判断）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high_9 = df["High"].rolling(9).max()
        low_9 = df["Low"].rolling(9).min()
        tenkan = (high_9 + low_9) / 2

        high_26 = df["High"].rolling(26).max()
        low_26 = df["Low"].rolling(26).min()
        kijun = (high_26 + low_26) / 2

        senkou_a = ((tenkan + kijun) / 2).shift(26)
        high_52 = df["High"].rolling(52).max()
        low_52 = df["Low"].rolling(52).min()
        senkou_b = ((high_52 + low_52) / 2).shift(26)

        cloud_top = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
        cloud_bottom = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)

        signals = pd.Series(0, index=df.index)
        signals[(tenkan > kijun) & (df["Close"] > cloud_top)] = 1
        signals[(tenkan < kijun) & (df["Close"] < cloud_bottom)] = -1
        return signals


class SMCStrategy(Strategy):
    name = "smc"
    description = "Smart Money Concepts 策略（订单块/流动性扫荡）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        h_20 = df["High"].rolling(20).max()
        l_20 = df["Low"].rolling(20).min()

        signals = pd.Series(0, index=df.index)
        signals[df["Close"] > h_20.shift(1)] = 1
        signals[df["Close"] < l_20.shift(1)] = -1
        return signals


class MultiFactorStrategy(Strategy):
    name = "multi_factor"
    description = "多因子评分策略（动量+波动率+成交量综合打分）"

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
    description = "加密货币资金费率套利策略（基于动量和波动率代理）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ret_8h = df["Close"].pct_change(3)
        ret_24h = df["Close"].pct_change(9)
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


_STRATEGIES: dict[str, type[Strategy]] = {
    "sma_cross": SMACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "ichimoku": IchimokuStrategy,
    "smc": SMCStrategy,
    "multi_factor": MultiFactorStrategy,
    "crypto_funding": CryptoFundingStrategy,
}


def get_strategy(name: str) -> Strategy | None:
    cls = _STRATEGIES.get(name)
    if cls:
        return cls()
    return None


def list_strategies() -> list[dict[str, Any]]:
    return [{"name": s.name, "description": s.description} for s in _STRATEGIES.values()]
