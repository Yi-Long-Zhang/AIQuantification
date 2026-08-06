"""
Trading Cycle Scheduler — automated trading cycle execution.

Runs trading cycles at configurable intervals per market using asyncio.
No external dependency (APScheduler); uses asyncio.create_task + sleep loops.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta

from agent.llm_client import LLMClient
from agent.multi_agent import CoordinatorAgent, MessageBroker

logger = logging.getLogger(__name__)


# ── Market schedule config ────────────────────────────────────────────────────

MARKET_SCHEDULES: dict[str, dict] = {
    "us_stock": {
        "enabled": True,
        "interval_minutes": 60,           # Run every 60 minutes during market hours
        "market_open": time(9, 30),       # 9:30 AM ET
        "market_close": time(16, 0),      # 4:00 PM ET
        "timezone": "US/Eastern",
        "run_on_startup": True,
    },
    "cn_stock": {
        "enabled": True,
        "interval_minutes": 120,          # Run every 2 hours
        "market_open": time(9, 30),
        "market_close": time(15, 0),
        "timezone": "Asia/Shanghai",
        "run_on_startup": True,
    },
    "hk_stock": {
        "enabled": True,
        "interval_minutes": 120,          # Run every 2 hours
        "market_open": time(9, 30),
        "market_close": time(16, 0),
        "timezone": "Asia/Hong_Kong",
        "run_on_startup": True,
    },
    "crypto": {
        "enabled": True,
        "interval_minutes": 240,          # Run every 4 hours (24/7)
        "market_open": time(0, 0),        # Always open
        "market_close": time(23, 59),
        "timezone": "UTC",
        "run_on_startup": True,
    },
}


# ── Scheduler ─────────────────────────────────────────────────────────────────

class TradingScheduler:
    """
    Automated trading cycle scheduler.

    Manages per-market asyncio tasks that run trading cycles on schedule.
    """

    def __init__(self, llm_provider: str | None = None):
        self._llm_provider = llm_provider
        self._coordinator: CoordinatorAgent | None = None
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def get_coordinator(self) -> CoordinatorAgent:
        """Lazy-init coordinator singleton with registered agents."""
        if self._coordinator is None:
            from agent.config import settings
            from agent.multi_agent.agent_factory import register_default_agents
            broker = MessageBroker()
            llm = LLMClient(provider=self._llm_provider or settings.llm_provider)
            coordinator = CoordinatorAgent(llm_client=llm, broker=broker)
            register_default_agents(coordinator, llm)
            self._coordinator = coordinator
        return self._coordinator

    async def start(self) -> None:
        """Start all scheduled market tasks."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        self._running = True

        for market, config in MARKET_SCHEDULES.items():
            if not config["enabled"]:
                continue
            task = asyncio.create_task(self._run_market_loop(market, config))
            self._tasks[market] = task
            logger.info(f"Scheduler started for {market} (every {config['interval_minutes']}min)")

    async def stop(self) -> None:
        """Stop all scheduled tasks."""
        self._running = False
        for market, task in self._tasks.items():
            task.cancel()
        self._tasks.clear()
        logger.info("Scheduler stopped")

    # ── Per-market loop ───────────────────────────────────────────────────

    async def _run_market_loop(self, market: str, config: dict) -> None:
        """Run trading cycles for a single market on schedule."""
        interval = config["interval_minutes"] * 60  # Convert to seconds
        is_24_7 = config["market_open"] == time(0, 0) and config["market_close"] == time(23, 59)

        # Run once on startup if configured
        if config.get("run_on_startup"):
            await self._run_cycle_safe(market)

        while self._running:
            await asyncio.sleep(interval)

            # Skip if not in market hours (except 24/7 markets like crypto)
            if not is_24_7 and not self._in_market_hours(config):
                logger.debug(f"{market}: outside market hours, skipping cycle")
                continue

            await self._run_cycle_safe(market)

    async def _run_cycle_safe(self, market: str) -> None:
        """Run a single trading cycle with error handling."""
        try:
            logger.info(f"=== Scheduled trading cycle for {market} ===")
            coordinator = self.get_coordinator()
            result = await coordinator.run_trading_cycle(market=market)
            status = result.get("status", "UNKNOWN")
            logger.info(f"Scheduled cycle for {market}: {status}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Scheduled cycle failed for {market}: {e}")

    # ── Market hours check ────────────────────────────────────────────────

    @staticmethod
    def _in_market_hours(config: dict) -> bool:
        """Check if current time falls within market hours."""
        now = datetime.now().time()
        return config["market_open"] <= now <= config["market_close"]

    # ── Status ────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return scheduler status."""
        return {
            "running": self._running,
            "markets": {
                market: {
                    "enabled": cfg["enabled"],
                    "interval_minutes": cfg["interval_minutes"],
                    "task_active": market in self._tasks and not self._tasks[market].done(),
                }
                for market, cfg in MARKET_SCHEDULES.items()
            },
        }


# ── Global singleton ─────────────────────────────────────────────────────────

_scheduler: TradingScheduler | None = None


def get_scheduler() -> TradingScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = TradingScheduler()
    return _scheduler


async def start_scheduler() -> None:
    """Convenience: get or create and start the scheduler."""
    sched = get_scheduler()
    await sched.start()
