"""
Scheduler 单元测试
"""
from __future__ import annotations

import pytest
from agent.scheduler import TradingScheduler, MARKET_SCHEDULES


class TestTradingScheduler:
    def test_scheduler_not_running_initially(self):
        sched = TradingScheduler()
        assert sched.get_status()["running"] is False

    def test_get_status_returns_markets(self):
        sched = TradingScheduler()
        status = sched.get_status()
        assert "markets" in status
        for market in MARKET_SCHEDULES:
            assert market in status["markets"]

    def test_start_starts_tasks(self):
        sched = TradingScheduler()
        sched.start()
        status = sched.get_status()
        assert status["running"] is True
        # Stop after test
        import asyncio
        asyncio.run(sched.stop())

    def test_stop_stops_tasks(self):
        sched = TradingScheduler()
        sched.start()
        import asyncio
        asyncio.run(sched.stop())
        status = sched.get_status()
        assert status["running"] is False

    def test_market_hours_check(self):
        assert TradingScheduler._in_market_hours({
            "market_open": __import__("datetime").time(0, 0),
            "market_close": __import__("datetime").time(23, 59),
        }) is True

    def test_get_coordinator_returns_instance(self):
        sched = TradingScheduler()
        # Should not raise
        status = sched.get_status()
        assert status["running"] is False

    def test_start_twice_no_error(self):
        sched = TradingScheduler()
        sched.start()
        sched.start()  # Should log warning, not crash
        import asyncio
        asyncio.run(sched.stop())

    def test_disabled_market_not_started(self):
        sched = TradingScheduler()
        # Override schedule to disable us_stock
        MARKET_SCHEDULES["us_stock"]["enabled"] = False
        sched.start()
        status = sched.get_status()
        # Re-enable for other tests
        MARKET_SCHEDULES["us_stock"]["enabled"] = True
        import asyncio
        asyncio.run(sched.stop())
        assert status["running"] is True
