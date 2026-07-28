"""
Trading Cycle Phases — Research → Strategy → Risk

Extracted from CoordinatorAgent to keep each file under 500 lines.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .communication import MessagePriority

logger = logging.getLogger(__name__)


class TradingCycleMixin:
    """Mixin providing trading cycle phase methods for CoordinatorAgent."""

    async def run_research_phase(
        self,
        market: str = "us_stock",
        context: dict | None = None
    ) -> dict:
        """
        Run the research phase: DataMiner first, then remaining analysts in parallel.

        DataMiner runs first to produce candidate symbols; those candidates are
        passed as context to the other research agents (Technical, Fundamental,
        News, Market) so they have concrete stocks to analyze.

        Returns combined research report.
        """
        logger.info("=== Research Phase Start ===")
        context = context or {}

        all_research_agents = [
            name for name in self.list_agents()
            if any(kw in name.lower() for kw in ["market", "data", "news", "fundamental", "technical"])
        ]

        if not all_research_agents:
            logger.warning("No research agents registered, skipping research phase")
            return {"status": "skipped", "reason": "No research agents registered"}

        # ── Step 1: Run DataMiner first to get candidate symbols ──
        data_miner_name = next(
            (n for n in all_research_agents if "data" in n.lower()),
            None
        )

        research_results: dict[str, dict] = {}
        candidates: list[dict] = []

        if data_miner_name:
            logger.info(f"Running DataMiner ({data_miner_name}) first to mine candidates")
            data_miner_task = {
                "type": "analyze",
                "input": {"market": market, "context": context},
                "context": context,
                "task_id": f"research_{data_miner_name}_{datetime.now().timestamp()}",
            }
            dm_result = await self.delegate(data_miner_name, data_miner_task, MessagePriority.HIGH)
            research_results[data_miner_name] = dm_result

            dm_output = dm_result.get("output", {})
            candidates = dm_output.get("candidates", dm_output.get("signals", []))
            if candidates:
                logger.info(f"DataMiner produced {len(candidates)} candidates")
            else:
                logger.info("DataMiner returned no candidates, continuing with empty list")
        else:
            logger.warning("No DataMiner agent found, research agents will run without candidate data")

        # ── Step 2: Build enriched context with DataMiner candidates ──
        research_context = {**context, "candidates": candidates}
        research_report_partial = {
            "phase": "research",
            "market": market,
            "timestamp": datetime.now().isoformat(),
            "agents": research_results,
        }

        # ── Step 3: Run remaining research agents in parallel ──
        remaining_agents = [n for n in all_research_agents if n != data_miner_name]

        if remaining_agents:
            task_base = {
                "type": "analyze",
                "input": {
                    "market": market,
                    "context": research_context,
                    "research": research_report_partial,
                },
                "context": research_context,
            }
            assignments = [
                (name, {**task_base, "task_id": f"research_{name}_{datetime.now().timestamp()}"})
                for name in remaining_agents
            ]
            remaining_results = await self.delegate_parallel(assignments, priority=MessagePriority.HIGH)
            research_results.update(remaining_results)

        report = {
            "phase": "research",
            "market": market,
            "timestamp": datetime.now().isoformat(),
            "agents": research_results,
            "summary": self._summarize_research(research_results),
            "candidates": candidates,
        }
        logger.info(f"Research phase complete: {len(research_results)} agents contributed, "
                     f"{len(candidates)} candidates")
        return report

    async def run_strategy_phase(
        self,
        research_report: dict,
        context: dict | None = None
    ) -> dict:
        """
        Run the strategy phase based on research results.

        Returns trading signals and backtest validation.
        """
        logger.info("=== Strategy Phase Start ===")
        context = context or {}

        strategy_agents = [
            name for name in self.list_agents()
            if any(kw in name.lower() for kw in ["signal", "backtest", "optimizer", "predictor", "ml"])
        ]

        if not strategy_agents:
            logger.warning("No strategy agents registered, skipping strategy phase")
            return {"status": "skipped", "reason": "No strategy agents registered"}

        task_base = {
            "type": "decide",
            "input": {"research": research_report, "context": context},
            "context": context
        }

        assignments = [
            (name, {**task_base, "task_id": f"strategy_{name}_{datetime.now().timestamp()}"})
            for name in strategy_agents
        ]

        results = await self.delegate_parallel(assignments, priority=MessagePriority.HIGH)

        report = {
            "phase": "strategy",
            "timestamp": datetime.now().isoformat(),
            "agents": results,
            "signals": self._extract_signals(results)
        }
        logger.info(f"Strategy phase complete: {len(report['signals'])} signals generated")
        return report

    async def run_risk_phase(
        self,
        strategy_report: dict,
        context: dict | None = None
    ) -> dict:
        """
        Run the risk assessment phase.

        Returns approved signals after risk vetting.
        """
        logger.info("=== Risk Phase Start ===")
        context = context or {}

        risk_agents = [
            name for name in self.list_agents()
            if any(kw in name.lower() for kw in ["risk", "position", "stop"])
        ]

        if not risk_agents:
            logger.warning("No risk agents registered, approving all signals by default")
            return {
                "phase": "risk",
                "timestamp": datetime.now().isoformat(),
                "approved_signals": strategy_report.get("signals", []),
                "rejected_signals": [],
                "agents": {}
            }

        task_base = {
            "type": "evaluate",
            "input": {"signals": strategy_report.get("signals", []), "context": context},
            "context": context
        }

        assignments = [
            (name, {**task_base, "task_id": f"risk_{name}_{datetime.now().timestamp()}"})
            for name in risk_agents
        ]

        results = await self.delegate_parallel(assignments, priority=MessagePriority.URGENT)

        approved, rejected = self._filter_signals(strategy_report.get("signals", []), results)

        report = {
            "phase": "risk",
            "timestamp": datetime.now().isoformat(),
            "agents": results,
            "approved_signals": approved,
            "rejected_signals": rejected
        }
        logger.info(f"Risk phase complete: {len(approved)} approved, {len(rejected)} rejected")
        return report

    async def run_trading_cycle(
        self,
        market: str = "us_stock",
        context: dict | None = None
    ) -> dict:
        """
        Run a complete trading cycle end-to-end.

        Flow: Research → Strategy → Risk → Final Decision

        Returns complete cycle results with final decisions.
        """
        cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"=== Trading Cycle {cycle_id} Start ===")

        context = context or {}
        context["cycle_id"] = cycle_id

        start_time = datetime.now()

        try:
            research = await self.run_research_phase(market, context)
            strategy = await self.run_strategy_phase(research, context)
            risk = await self.run_risk_phase(strategy, context)
            final_decision = await self._synthesize_decision(research, strategy, risk)

            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "cycle_id": cycle_id,
                "market": market,
                "status": "COMPLETE",
                "elapsed_seconds": elapsed,
                "research": research,
                "strategy": strategy,
                "risk": risk,
                "final_decision": final_decision,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Trading cycle {cycle_id} complete in {elapsed:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Trading cycle {cycle_id} failed: {e}")
            return {
                "cycle_id": cycle_id,
                "status": "FAILED",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
