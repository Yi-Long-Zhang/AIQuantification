from __future__ import annotations

from dataclasses import dataclass, field

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


def _ts_mean(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).mean()


def _ts_std(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).std()


def _ts_max(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).max()


def _ts_min(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).min()


def _ts_rank(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=1).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)


def _ts_delta(s: pd.Series, period: int) -> pd.Series:
    return s.diff(period)


def _ts_corr(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    return a.rolling(window, min_periods=1).corr(b)


def _ts_cov(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    return a.rolling(window, min_periods=1).cov(b)


class Alpha158:
    """Qlib Alpha158 因子库（150 因子）"""

    factors: list[FactorDef] = []

    @classmethod
    def _build_factors(cls) -> list[FactorDef]:
        if cls.factors:
            return cls.factors

        defs: list[FactorDef] = []

        # ── KBAR: K线形态因子 (6) ──
        defs.append(FactorDef("KBAR_open", "kbar", "开盘价/收盘价",
                              lambda df: _safe_div(df["open"], df["close"])))
        defs.append(FactorDef("KBAR_high", "kbar", "最高价/收盘价",
                              lambda df: _safe_div(df["high"], df["close"])))
        defs.append(FactorDef("KBAR_low", "kbar", "最低价/收盘价",
                              lambda df: _safe_div(df["low"], df["close"])))
        defs.append(FactorDef("KBAR_upper_shadow", "kbar", "上影线",
                              lambda df: _safe_div(df["high"] - np.maximum(df["open"], df["close"]), df["close"])))
        defs.append(FactorDef("KBAR_lower_shadow", "kbar", "下影线",
                              lambda df: _safe_div(np.minimum(df["open"], df["close"]) - df["low"], df["close"])))
        defs.append(FactorDef("KBAR_body", "kbar", "实体",
                              lambda df: _safe_div(np.abs(df["close"] - df["open"]), df["close"])))

        # ── PRICE: 价格因子 (20) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"PRICE_mean_{d}", "price", f"MA{d}",
                                  lambda df, w=d: _ts_mean(df["close"], w)))
            defs.append(FactorDef(f"PRICE_std_{d}", "price", f"STD{d}",
                                  lambda df, w=d: _ts_std(df["close"], w)))
            defs.append(FactorDef(f"PRICE_max_{d}", "price", f"MAX{d}",
                                  lambda df, w=d: _ts_max(df["close"], w)))
            defs.append(FactorDef(f"PRICE_min_{d}", "price", f"MIN{d}",
                                  lambda df, w=d: _ts_min(df["close"], w)))
            defs.append(FactorDef(f"PRICE_rank_{d}", "price", f"RANK{d}",
                                  lambda df, w=d: _ts_rank(df["close"], w)))
        defs.append(FactorDef("PRICE_52w_high_ratio", "price", "当前价/52周最高",
                              lambda df: _safe_div(df["close"], _ts_max(df["high"], 252))))
        defs.append(FactorDef("PRICE_52w_low_ratio", "price", "当前价/52周最低",
                              lambda df: _safe_div(df["close"], _ts_min(df["low"], 252))))

        # ── VOLUME: 成交量因子 (16) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"VOL_mean_{d}", "volume", f"VOL_MA{d}",
                                  lambda df, w=d: _ts_mean(df["volume"], w)))
            defs.append(FactorDef(f"VOL_std_{d}", "volume", f"VOL_STD{d}",
                                  lambda df, w=d: _ts_std(df["volume"], w)))
            defs.append(FactorDef(f"VOL_ratio_{d}", "volume", f"VOL_RATIO{d}",
                                  lambda df, w=d: _safe_div(df["volume"], _ts_mean(df["volume"], w))))
            defs.append(FactorDef(f"VOL_rank_{d}", "volume", f"VOL_RANK{d}",
                                  lambda df, w=d: _ts_rank(df["volume"], w)))

        # ── MOMENTUM: 动量因子 (20) ──
        for d in [5, 10, 20, 60, 120]:
            defs.append(FactorDef(f"MOM_ret_{d}", "momentum", f"{d}日收益率",
                                  lambda df, w=d: _safe_div(df["close"], df["close"].shift(w)) - 1))
            defs.append(FactorDef(f"MOM_ma_diff_{d}", "momentum", f"价格/MA{d}偏离",
                                  lambda df, w=d: _safe_div(df["close"], _ts_mean(df["close"], w)) - 1))

        # ── VOLATILITY: 波动率因子 (12) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"VOL_ret_std_{d}", "volatility", f"{d}日收益率标准差",
                                  lambda df, w=d: _ts_std(df["close"].pct_change(), w)))
            defs.append(FactorDef(f"VOL_high_low_{d}", "volatility", f"{d}日振幅",
                                  lambda df, w=d: _safe_div(_ts_max(df["high"], w) - _ts_min(df["low"], w), df["close"])))
            defs.append(FactorDef(f"VOL_close_open_{d}", "volatility", f"{d}日收盘/开盘波动",
                                  lambda df, w=d: _ts_std(_safe_div(df["close"], df["open"]), w)))

        # ── CORRELATION: 相关性因子 (12) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"CORR_vol_price_{d}", "correlation", f"量价相关性{d}日",
                                  lambda df, w=d: _ts_corr(df["volume"], df["close"], w)))
            defs.append(FactorDef(f"COV_vol_price_{d}", "correlation", f"量价协方差{d}日",
                                  lambda df, w=d: _ts_cov(df["volume"], df["close"], w)))

        # ── RSI: RSI 因子 (4) ──
        for d in [6, 12, 24, 48]:
            defs.append(FactorDef(f"RSI_{d}", "rsi", f"RSI{d}",
                                  lambda df, w=d: _compute_rsi(df["close"], w)))

        # ── MACD: MACD 因子 (3) ──
        defs.append(FactorDef("MACD_line", "macd", "MACD线",
                              lambda df: _compute_macd(df["close"])[0]))
        defs.append(FactorDef("MACD_signal", "macd", "信号线",
                              lambda df: _compute_macd(df["close"])[1]))
        defs.append(FactorDef("MACD_hist", "macd", "柱状图",
                              lambda df: _compute_macd(df["close"])[2]))

        # ── BOLLINGER: 布林带因子 (4) ──
        defs.append(FactorDef("BOLL_upper", "bollinger", "布林上轨",
                              lambda df: _ts_mean(df["close"], 20) + 2 * _ts_std(df["close"], 20)))
        defs.append(FactorDef("BOLL_lower", "bollinger", "布林下轨",
                              lambda df: _ts_mean(df["close"], 20) - 2 * _ts_std(df["close"], 20)))
        defs.append(FactorDef("BOLL_width", "bollinger", "布林带宽",
                              lambda df: _safe_div(4 * _ts_std(df["close"], 20), _ts_mean(df["close"], 20))))
        defs.append(FactorDef("BOLL_pct", "bollinger", "布林位置",
                              lambda df: _safe_div(df["close"] - (_ts_mean(df["close"], 20) - 2 * _ts_std(df["close"], 20)),
                                                   4 * _ts_std(df["close"], 20))))

        # ── ATR: ATR 因子 (4) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"ATR_{d}", "atr", f"ATR{d}",
                                  lambda df, w=d: _ts_mean(
                                      np.maximum(
                                          df["high"] - df["low"],
                                          np.maximum(np.abs(df["high"] - df["close"].shift(1)),
                                                     np.abs(df["low"] - df["close"].shift(1)))
                                      ), w)))

        # ── STOCH: 随机指标因子 (4) ──
        for d in [9, 14, 21, 30]:
            defs.append(FactorDef(f"STOCH_k_{d}", "stoch", f"KD-K{d}",
                                  lambda df, w=d: _safe_div(
                                      df["close"] - _ts_min(df["low"], w),
                                      _ts_max(df["high"], w) - _ts_min(df["low"], w)) * 100))

        # ── ADX: ADX 因子 (4) ──
        for d in [14, 20, 30, 60]:
            defs.append(FactorDef(f"ADX_{d}", "adx", f"ADX{d}",
                                  lambda df, w=d: _compute_adx(df, w)))

        # ── OBV: OBV 因子 (4) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"OBV_ma_{d}", "obv", f"OBV_MA{d}",
                                  lambda df, w=d: _ts_mean(_compute_obv(df), w)))

        # ── VWAP: VWAP 因子 (4) ──
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"VWAP_ratio_{d}", "vwap", f"价格/VWAP{d}",
                                  lambda df, w=d: _safe_div(
                                      df["close"],
                                      (df["close"] * df["volume"]).rolling(w, min_periods=1).sum() /
                                      df["volume"].rolling(w, min_periods=1).sum())))

        # ── PRICE_PATTERN: 价格形态因子 (20) ──
        defs.append(FactorDef("PATTERN_hammer", "pattern", "锤子线",
                              lambda df: ((df["close"] > df["open"]) &
                                          ((df["open"] - df["low"]) > 2 * (df["close"] - df["open"])) &
                                          ((df["high"] - df["close"]) < 0.1 * (df["close"] - df["open"]))).astype(float)))
        defs.append(FactorDef("PATTERN_doji", "pattern", "十字星",
                              lambda df: (np.abs(df["close"] - df["open"]) < 0.1 * (df["high"] - df["low"])).astype(float)))
        defs.append(FactorDef("PATTERN_engulfing", "pattern", "吞没形态",
                              lambda df: ((df["close"].shift(1) < df["open"].shift(1)) &
                                          (df["close"] > df["open"]) &
                                          (df["open"] < df["close"].shift(1)) &
                                          (df["close"] > df["open"].shift(1))).astype(float)))
        defs.append(FactorDef("PATTERN_morning_star", "pattern", "晨星",
                              lambda df: _detect_morning_star(df)))
        defs.append(FactorDef("PATTERN_evening_star", "pattern", "暮星",
                              lambda df: _detect_evening_star(df)))
        for i in range(1, 6):
            defs.append(FactorDef(f"PATTERN_ret_{i}d", "pattern", f"{i}日连续涨跌",
                                  lambda df, n=i: (df["close"] > df["close"].shift(n)).astype(float) * 2 - 1))
        for i in range(1, 6):
            defs.append(FactorDef(f"PATTERN_gap_{i}d", "pattern", f"{i}日缺口",
                                  lambda df, n=i: _safe_div(df["open"] - df["close"].shift(n), df["close"].shift(n))))

        # ── INTRADAY: 日内因子 (10) ──
        defs.append(FactorDef("INTRADAY_range", "intraday", "日内振幅",
                              lambda df: _safe_div(df["high"] - df["low"], df["close"])))
        defs.append(FactorDef("INTRADAY_upper_shadow_ratio", "intraday", "上影线比例",
                              lambda df: _safe_div(df["high"] - np.maximum(df["open"], df["close"]), df["high"] - df["low"])))
        defs.append(FactorDef("INTRADAY_lower_shadow_ratio", "intraday", "下影线比例",
                              lambda df: _safe_div(np.minimum(df["open"], df["close"]) - df["low"], df["high"] - df["low"])))
        defs.append(FactorDef("INTRADAY_body_ratio", "intraday", "实体比例",
                              lambda df: _safe_div(np.abs(df["close"] - df["open"]), df["high"] - df["low"])))
        defs.append(FactorDef("INTRADAY_close_position", "intraday", "收盘位置",
                              lambda df: _safe_div(df["close"] - df["low"], df["high"] - df["low"])))
        for d in [5, 10, 20, 60, 120]:
            defs.append(FactorDef(f"INTRADAY_avg_range_{d}", "intraday", f"{d}日平均振幅",
                                  lambda df, w=d: _ts_mean(_safe_div(df["high"] - df["low"], df["close"]), w)))

        # ── COMPLEX: 复合因子 (32) ──
        defs.append(FactorDef("COMPLEX_momentum_quality", "complex", "动量质量",
                              lambda df: _safe_div(_ts_mean(df["close"].pct_change(), 20), _ts_std(df["close"].pct_change(), 20))))
        defs.append(FactorDef("COMPLEX_vol_price_trend", "complex", "量价趋势",
                              lambda df: _safe_div(_ts_mean(df["volume"].pct_change(), 10), _ts_mean(df["close"].pct_change(), 10))))
        defs.append(FactorDef("COMPLEX_reversal_strength", "complex", "反转强度",
                              lambda df: _safe_div(df["close"].pct_change(5), _ts_std(df["close"].pct_change(), 20))))
        defs.append(FactorDef("COMPLEX_trend_consistency", "complex", "趋势一致性",
                              lambda df: _safe_div((df["close"] > df["close"].shift(1)).rolling(20).sum(), 20)))
        for d in [5, 10, 20, 60]:
            defs.append(FactorDef(f"COMPLEX_price_volume_div_{d}", "complex", f"量价背离{d}日",
                                  lambda df, w=d: _ts_corr(df["close"].pct_change(), df["volume"].pct_change(), w)))
            defs.append(FactorDef(f"COMPLEX_volatility_adjusted_ret_{d}", "complex", f"波动率调整收益{d}日",
                                  lambda df, w=d: _safe_div(df["close"].pct_change(d), _ts_std(df["close"].pct_change(), w))))
            defs.append(FactorDef(f"COMPLEX_max_drawdown_{d}", "complex", f"最大回撤{d}日",
                                  lambda df, w=d: _compute_max_drawdown(df["close"], w)))
            defs.append(FactorDef(f"COMPLEX_skewness_{d}", "complex", f"偏度{d}日",
                                  lambda df, w=d: df["close"].pct_change().rolling(w, min_periods=1).skew()))

        cls.factors = defs
        return defs

    @classmethod
    def compute(cls, df: pd.DataFrame, factor_names: list[str] | None = None) -> pd.DataFrame:
        """计算因子值"""
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


# ── Helper functions ──

def _compute_rsi(prices: pd.Series, period: int) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period, min_periods=1).mean()
    rs = _safe_div(gain, loss)
    return 100 - (100 / (1 + rs))


def _compute_macd(prices: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal
    return macd_line, signal, hist


def _compute_adx(df: pd.DataFrame, period: int) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    tr = np.maximum(high - low, np.maximum(np.abs(high - close.shift(1)), np.abs(low - close.shift(1))))
    atr = _ts_mean(tr, period)
    plus_di = 100 * _safe_div(_ts_mean(plus_dm, period), atr)
    minus_di = 100 * _safe_div(_ts_mean(minus_dm, period), atr)
    dx = 100 * _safe_div(np.abs(plus_di - minus_di), plus_di + minus_di)
    return _ts_mean(dx, period)


def _compute_obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff())
    return (direction * df["volume"]).cumsum()


def _compute_max_drawdown(prices: pd.Series, window: int) -> pd.Series:
    def _mdd(x):
        cummax = np.maximum.accumulate(x)
        drawdown = (x - cummax) / np.where(cummax != 0, cummax, np.nan)
        return drawdown.min()
    return prices.rolling(window, min_periods=1).apply(_mdd, raw=True)


def _detect_morning_star(df: pd.DataFrame) -> pd.Series:
    body1 = np.abs(df["close"].shift(2) - df["open"].shift(2))
    body2 = np.abs(df["close"].shift(1) - df["open"].shift(1))
    body3 = np.abs(df["close"] - df["open"])
    return ((body1 > body2) & (body2 < body3 * 0.3) &
            (df["close"].shift(2) < df["open"].shift(2)) &
            (df["close"] > df["open"])).astype(float)


def _detect_evening_star(df: pd.DataFrame) -> pd.Series:
    body1 = np.abs(df["close"].shift(2) - df["open"].shift(2))
    body2 = np.abs(df["close"].shift(1) - df["open"].shift(1))
    body3 = np.abs(df["close"] - df["open"])
    return ((body1 > body2) & (body2 < body3 * 0.3) &
            (df["close"].shift(2) > df["open"].shift(2)) &
            (df["close"] < df["open"])).astype(float)
