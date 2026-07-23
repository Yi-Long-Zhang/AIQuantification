"""Additional backend tests — notify, broker tools, strategy signals"""

from __future__ import annotations

import pytest
from agent.notify import Notification, broadcast, register_notifier, list_notifiers
from agent.notify.webhook import WebhookNotifier
from agent.strategies.registry import get_strategy, list_strategies
from agent.broker.shadow import parse_trades_csv, analyze_trades


class TestNotifyBroadcast:
    def test_broadcast_empty(self):
        import asyncio
        from agent.notify import _notifiers
        _notifiers.clear()
        n = Notification(title="T", message="M")
        results = asyncio.run(broadcast(n))
        assert isinstance(results, dict)

    def test_list_notifiers_after_register(self):
        from agent.notify import _notifiers
        _notifiers.clear()
        register_notifier(WebhookNotifier("https://example.com"))
        assert len(list_notifiers()) == 1


class TestStrategySignals:
    """Verify all 18 strategies generate valid signal series."""

    def _sample_df(self):
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2024-01-01", periods=200, freq="B")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(200) * 1.5)
        return pd.DataFrame({
            "Date": dates, "Open": close * 0.99, "High": close * 1.02,
            "Low": close * 0.98, "Close": close, "Volume": np.random.randint(1000000, 5000000, 200),
        })

    def test_all_strategies_generate_signals(self):
        df = self._sample_df()
        strategies = list_strategies()
        assert len(strategies) == 18
        for s_info in strategies:
            strat = get_strategy(s_info["name"])
            assert strat is not None, f"Failed to get strategy: {s_info['name']}"
            signals = strat.generate_signals(df)
            assert len(signals) == len(df), f"{s_info['name']}: signal length mismatch"
            assert set(signals.unique()).issubset({-1, 0, 1}), f"{s_info['name']}: unexpected signal values"

    def test_all_strategies_have_markets(self):
        for s in list_strategies():
            assert s["markets"], f"{s['name']}: missing markets"
            assert len(s["markets"]) >= 1
            assert s["risk_level"] in ("低", "中", "高"), f"{s['name']}: invalid risk_level"
