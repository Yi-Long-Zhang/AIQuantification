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
    description = "RSI 超买超卖反转策略（RSI<30买入，>70卖出）"

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
    description = "布林带回归策略（价格触及下轨买入，上轨卖出）"

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
    description = "多因子评分策略（动量+低波+成交量综合打分）"

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


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5 — 新增 10 个策略
# ═══════════════════════════════════════════════════════════════════════════════

class ATRChannelStrategy(Strategy):
    name = "atr_channel"
    description = "ATR 通道突破策略（基于平均真实波幅的动态通道，价格突破上轨做多）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        mid = df["Close"].rolling(20).mean()
        upper = mid + 2 * atr
        lower = mid - 2 * atr
        signals = pd.Series(0, index=df.index)
        signals[df["Close"] > upper] = 1
        signals[df["Close"] < lower] = -1
        return signals


class ParabolicSARStrategy(Strategy):
    name = "parabolic_sar"
    description = "Parabolic SAR 趋势跟踪策略（SAR 指标转向点判断趋势反转）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high = df["High"]
        low = df["Low"]
        length = len(df)
        sar = np.zeros(length)
        ep = np.zeros(length)
        af = np.zeros(length)
        trend = np.zeros(length)  # 1 = uptrend, -1 = downtrend

        if length < 2:
            return pd.Series(0, index=df.index)

        sar[0] = low[0]
        ep[0] = high[0]
        af[0] = 0.02
        trend[0] = 1

        for i in range(1, length):
            if trend[i - 1] == 1:
                sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
                sar[i] = min(sar[i], low[i - 1], low[i - 2]) if i >= 2 else min(sar[i], low[i - 1])
                if high[i] > ep[i - 1]:
                    ep[i] = high[i]
                    af[i] = min(af[i - 1] + 0.02, 0.2)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
                if sar[i] > low[i]:
                    trend[i] = -1
                    sar[i] = ep[i - 1]
                    ep[i] = low[i]
                    af[i] = 0.02
                else:
                    trend[i] = 1
            else:
                sar[i] = sar[i - 1] - af[i - 1] * (sar[i - 1] - ep[i - 1])
                sar[i] = max(sar[i], high[i - 1], high[i - 2]) if i >= 2 else max(sar[i], high[i - 1])
                if low[i] < ep[i - 1]:
                    ep[i] = low[i]
                    af[i] = min(af[i - 1] + 0.02, 0.2)
                else:
                    ep[i] = ep[i - 1]
                    af[i] = af[i - 1]
                if sar[i] < high[i]:
                    trend[i] = 1
                    sar[i] = ep[i - 1]
                    ep[i] = high[i]
                    af[i] = 0.02
                else:
                    trend[i] = -1

        signals = pd.Series(0, index=df.index)
        for i in range(1, length):
            if trend[i] == 1 and trend[i - 1] == -1:
                signals.iloc[i] = 1
            elif trend[i] == -1 and trend[i - 1] == 1:
                signals.iloc[i] = -1
        return signals


class ZScoreMeanReversionStrategy(Strategy):
    name = "zscore_mean_reversion"
    description = "Z-score 均值回归策略（价格偏离均线超过 2 个标准差时反向操作）"

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
    description = "配对交易策略（用大盘 ETF 做基准，个股相对强弱偏离时反向操作）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 使用 Close 作为基准，计算相对强弱
        returns = df["Close"].pct_change()
        # 如果没有基准列（benchmark），用滚动均值代替
        benchmark = df.get("benchmark", df["Close"].rolling(20).mean())
        spread = df["Close"] / benchmark.replace(0, np.nan) - 1
        spread_ma = spread.rolling(20).mean()
        spread_std = spread.rolling(20).std()
        zscore = (spread - spread_ma) / spread_std.replace(0, np.nan)
        signals = pd.Series(0, index=df.index)
        signals[zscore < -2] = 1
        signals[zscore > 2] = -1
        signals[zscore.abs() < 0.5] = 0  # 回归均值后平仓
        return signals


class VolumeWeightedMomentumStrategy(Strategy):
    name = "volume_weighted_momentum"
    description = "成交量加权动量策略（价格动量用成交量加权，放量突破确认趋势）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        returns = df["Close"].pct_change(10)
        avg_vol = df["Volume"].rolling(20).mean()
        vol_ratio = df["Volume"] / avg_vol.replace(0, np.nan)
        # 动量 × 成交量确认
        vw_momentum = returns * vol_ratio.clip(0, 3)
        vw_ma = vw_momentum.rolling(10).mean()
        signals = pd.Series(0, index=df.index)
        signals[vw_ma > 0.03] = 1
        signals[vw_ma < -0.03] = -1
        return signals


class GapFillStrategy(Strategy):
    name = "gap_fill"
    description = "缺口回补策略（价格跳空后预期回补缺口，高开低走做空，低开高走做多）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        prev_close = df["Close"].shift(1)
        gap = (df["Open"] - prev_close) / prev_close.replace(0, np.nan) * 100
        signals = pd.Series(0, index=df.index)
        # 跳空高开 >1% 做空（预期回补）
        signals[gap > 1] = -1
        # 跳空低开 >1% 做多（预期回补）
        signals[gap < -1] = 1
        return signals


class RSIDivergenceStrategy(Strategy):
    name = "rsi_divergence"
    description = "RSI 背离策略（价格创新低但 RSI 未创新低 → 底背离买入，反之卖出）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        # 检测背离：比较最近两个波峰/波谷
        signals = pd.Series(0, index=df.index)
        window = 10
        for i in range(window * 2, len(df)):
            recent_high = df["Close"].iloc[i - window:i].max()
            recent_low = df["Close"].iloc[i - window:i].min()
            prev_high = df["Close"].iloc[i - window * 2:i - window].max()
            prev_low = df["Close"].iloc[i - window * 2:i - window].min()
            rsi_recent = rsi.iloc[i - window:i]
            rsi_prev = rsi.iloc[i - window * 2:i - window]
            # 底背离：价格新低，RSI 未新低
            if df["Close"].iloc[i] < prev_low and rsi.iloc[i] > rsi_prev.min():
                signals.iloc[i] = 1
            # 顶背离：价格新高，RSI 未新高
            elif df["Close"].iloc[i] > prev_high and rsi.iloc[i] < rsi_prev.max():
                signals.iloc[i] = -1
        return signals


class EarningsMomentumStrategy(Strategy):
    name = "earnings_momentum"
    description = "财报动量策略（财报跳空后追踪趋势，利用公告后漂移效应）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # 模拟财报跳空：检测单日异常跳空（>3%）
        gap = df["Open"] / df["Close"].shift(1).replace(0, np.nan) - 1
        signals = pd.Series(0, index=df.index)
        for i in range(5, len(df)):
            if abs(gap.iloc[i]) > 0.03:
                # 跳空后追踪 5 天趋势
                post_gap_ret = df["Close"].iloc[i:min(i + 5, len(df))].pct_change().sum()
                if gap.iloc[i] > 0.03 and post_gap_ret > 0:
                    signals.iloc[i] = 1
                elif gap.iloc[i] < -0.03 and post_gap_ret < 0:
                    signals.iloc[i] = -1
        return signals


class DonchianChannelStrategy(Strategy):
    name = "donchian_channel"
    description = "Donchian 通道突破策略（20日最高/最低价通道，突破上轨做多，下轨做空）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        upper = df["High"].rolling(20).max()
        lower = df["Low"].rolling(20).min()
        mid = (upper + lower) / 2
        signals = pd.Series(0, index=df.index)
        signals[df["Close"] > upper.shift(1)] = 1
        signals[df["Close"] < lower.shift(1)] = -1
        # 回归中轨后平仓
        signals[(df["Close"] < mid) & (signals == 1)] = 0
        signals[(df["Close"] > mid) & (signals == -1)] = 0
        return signals


class KeltnerChannelStrategy(Strategy):
    name = "keltner_channel"
    description = "Keltner 通道策略（EMA + ATR 通道，价格突破上轨做多，结合趋势过滤）"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema20 = df["Close"].ewm(span=20).mean()
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        upper = ema20 + 2 * atr
        lower = ema20 - 2 * atr
        # 加趋势过滤：EMA 斜率
        ema_slope = ema20.diff(5)
        signals = pd.Series(0, index=df.index)
        signals[(df["Close"] > upper) & (ema_slope > 0)] = 1
        signals[(df["Close"] < lower) & (ema_slope < 0)] = -1
        return signals


# ── Registry ─────────────────────────────────────────────────────────────────

_STRATEGIES: dict[str, type[Strategy]] = {
    # 原有 8 个
    "sma_cross": SMACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "ichimoku": IchimokuStrategy,
    "smc": SMCStrategy,
    "multi_factor": MultiFactorStrategy,
    "crypto_funding": CryptoFundingStrategy,
    # 新增 10 个
    "atr_channel": ATRChannelStrategy,
    "parabolic_sar": ParabolicSARStrategy,
    "zscore_mean_reversion": ZScoreMeanReversionStrategy,
    "pair_trading": PairTradingStrategy,
    "volume_weighted_momentum": VolumeWeightedMomentumStrategy,
    "gap_fill": GapFillStrategy,
    "rsi_divergence": RSIDivergenceStrategy,
    "earnings_momentum": EarningsMomentumStrategy,
    "donchian_channel": DonchianChannelStrategy,
    "keltner_channel": KeltnerChannelStrategy,
}


def get_strategy(name: str) -> Strategy | None:
    cls = _STRATEGIES.get(name)
    if cls:
        return cls()
    return None


def list_strategies() -> list[dict[str, Any]]:
    return [{"name": s.name, "description": s.description} for s in _STRATEGIES.values()]
