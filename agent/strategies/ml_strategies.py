"""
Machine Learning Strategies — LightGBM + Ensemble.

Uses LightGBM for multi-factor signal prediction and an ensemble
meta-strategy that combines multiple sub-strategies via weighted voting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Strategy


class LightGBMStrategy(Strategy):
    name = "lightgbm"
    description = "LightGBM 多因子预测（20日收益方向分类+置信度）"
    type = "机器学习"
    tags = ["ml", "lightgbm", "multi-factor", "classification"]
    markets = ["us_stock", "cn_stock", "hk_stock", "crypto"]
    params = {"lookback": "60", "prediction_period": "5", "min_samples": "200"}
    risk_level = "中"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        if len(df) < 200:
            return pd.Series(0, index=df.index)

        try:
            import lightgbm as lgb
        except ImportError:
            return pd.Series(0, index=df.index)

        # ── Build multi-factor feature set ──
        close = df["Close"]
        features = pd.DataFrame(index=df.index)
        for p in [5, 10, 20, 60]:
            features[f"ret_{p}d"] = close.pct_change(p)
            features[f"ma_{p}d"] = close / close.rolling(p).mean() - 1
            features[f"vol_{p}d"] = close.pct_change().rolling(p).std()
        features["rsi"] = self._calc_rsi(close)
        features["volume_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()
        features["high_low_ratio"] = (df["High"].rolling(20).max() - df["Low"].rolling(20).min()) / close
        features["gap"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)

        target = close.pct_change(5).shift(-5)
        target_binary = (target > 0.005).astype(int) | ((target < -0.005).astype(int) * -1)

        # ── Train-test split ──
        train_end = int(len(features) * 0.7)
        X_train = features.iloc[:train_end].dropna().astype(float)
        y_train = target_binary.iloc[:train_end].loc[X_train.index]
        X_test = features.iloc[train_end:].dropna().astype(float)

        if len(X_train) < 100 or X_test.empty:
            return pd.Series(0, index=df.index)

        try:
            model = lgb.LGBMClassifier(
                n_estimators=100, max_depth=5, num_leaves=31,
                random_state=42, verbose=-1, force_col_wise=True,
            )
            model.fit(X_train, y_train)
            proba = model.predict_proba(X_test)
            pred = np.argmax(proba, axis=1) - 1  # -1, 0, +1
        except Exception:
            return pd.Series(0, index=df.index)

        signals = pd.Series(0, index=df.index)
        signals.loc[X_test.index] = pred
        return signals

    @staticmethod
    def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))


class EnsembleStrategy(Strategy):
    name = "ensemble"
    description = "策略集成（多子策略加权投票，动态权重）"
    type = "组合"
    tags = ["ensemble", "voting", "meta", "composite"]
    markets = ["us_stock", "cn_stock", "hk_stock", "crypto"]
    params = {
        "sma_weight": "1", "macd_weight": "1.2", "rsi_weight": "0.8",
        "bollinger_weight": "0.9", "ichimoku_weight": "0.7",
    }
    risk_level = "低"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        from .trend_strategies import SMACrossStrategy, MACDStrategy, IchimokuStrategy
        from .specialized_strategies import RSIStrategy
        from .mean_reversion_strategies import BollingerStrategy

        # Compute each sub-strategy's signals
        sub_signals = {}
        try:
            sub_signals["sma"] = SMACrossStrategy().generate_signals(df)
            sub_signals["macd"] = MACDStrategy().generate_signals(df)
            sub_signals["rsi"] = RSIStrategy().generate_signals(df)
            sub_signals["bollinger"] = BollingerStrategy().generate_signals(df)
            sub_signals["ichimoku"] = IchimokuStrategy().generate_signals(df)
        except Exception:
            return pd.Series(0, index=df.index)

        # Dynamic weights: more weight to strategies with recent success
        weights = {}
        for name, signals in sub_signals.items():
            recent_accuracy = self._recent_signal_accuracy(signals, df["Close"], 20)
            weights[name] = max(0.5, recent_accuracy)  # Minimum 0.5 weight

        # Weighted ensemble
        composite = pd.Series(0.0, index=df.index, dtype=float)
        for name, signals in sub_signals.items():
            composite += signals.astype(float) * weights[name]
        composite /= sum(weights.values())

        # Threshold-based signal
        result = pd.Series(0, index=df.index)
        result[composite > 0.3] = 1
        result[composite < -0.3] = -1
        return result

    @staticmethod
    def _recent_signal_accuracy(
        signals: pd.Series, price: pd.Series, window: int
    ) -> float:
        """Estimate recent signal accuracy by comparing to actual returns."""
        actual = price.pct_change(1).shift(-1)
        correct = ((signals > 0) & (actual > 0)) | ((signals < 0) & (actual < 0))
        recent_hits = correct.iloc[-window:].sum()
        recent_total = (~correct.iloc[-window:].isna()).sum()
        return recent_hits / max(recent_total, 1)
