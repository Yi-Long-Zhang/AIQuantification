"""
Multi-Agent System - Coordinator Agent

The Coordinator is the master orchestrator that manages all other agents,
decomposes tasks, and synthesizes results into final decisions.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from .base import BaseAgent
from .communication import AgentMessage, MessageBroker, MessageType, MessagePriority

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Master orchestrator that coordinates all other agents.

    Responsibilities:
    - Register and manage all agents
    - Decompose high-level goals into tasks
    - Delegate tasks to specialist agents in parallel
    - Synthesize results into final decisions
    - Manage the daily trading cycle
    """

    def __init__(self, llm_client, broker: MessageBroker):
        super().__init__(
            name="Coordinator",
            llm_client=llm_client,
            tools=[],
            system_prompt="""You are the Coordinator, the master orchestrator of an AI quantitative trading system.

Your role is to:
1. Break down trading goals into concrete tasks
2. Assign tasks to the right specialist agents
3. Synthesize multi-source analysis into clear decisions
4. Enforce risk rules before any trade is approved
5. Produce a structured final decision with reasoning

Decision framework:
- Research phase → Strategy phase → Risk check → Execute or reject
- Confidence threshold for execution: >= 0.65
- Any risk veto blocks the trade regardless of confidence

Output decisions as JSON with: symbol, action, confidence, reasoning, risk_approved.
"""
        )
        self.broker = broker
        self.registered_agents: dict[str, BaseAgent] = {}

        # Register self with broker
        self.broker.register_agent(self.name)

    # ─────────────────────────────────────────────
    # Agent registry
    # ─────────────────────────────────────────────

    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent."""
        self.registered_agents[agent.name] = agent
        self.broker.register_agent(agent.name)
        logger.info(f"Coordinator registered agent: {agent.name}")

    def get_agent(self, name: str) -> BaseAgent | None:
        """Retrieve a registered agent by name."""
        return self.registered_agents.get(name)

    def list_agents(self) -> list[str]:
        """Return list of registered agent names."""
        return list(self.registered_agents.keys())

    # ─────────────────────────────────────────────
    # Task delegation
    # ─────────────────────────────────────────────

    async def delegate(
        self,
        agent_name: str,
        task: dict,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> dict:
        """
        Delegate a task to a specialist agent and await its result.

        Args:
            agent_name: Target agent name
            task: Task definition dict
            priority: Message priority

        Returns:
            Agent result dict
        """
        agent = self.get_agent(agent_name)
        if agent is None:
            raise ValueError(f"Agent '{agent_name}' is not registered")

        # Send task message
        msg = AgentMessage(
            from_agent=self.name,
            to_agent=agent_name,
            message_type=MessageType.REQUEST,
            content={"task": task},
            priority=priority
        )
        await self.broker.send(msg)

        # Execute directly (same-process agents)
        result = await agent.execute(task)

        # Send result back via broker for audit trail
        reply = msg.create_response({"result": result})
        await self.broker.send(reply)

        return result

    async def delegate_parallel(
        self,
        assignments: list[tuple[str, dict]],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> dict[str, dict]:
        """
        Delegate tasks to multiple agents in parallel.

        Args:
            assignments: List of (agent_name, task) tuples
            priority: Message priority

        Returns:
            Dict mapping agent_name → result
        """
        tasks = [
            self.delegate(agent_name, task, priority)
            for agent_name, task in assignments
        ]
        names = [agent_name for agent_name, _ in assignments]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {name} raised: {result}")
                output[name] = {"status": "FAILED", "error": str(result)}
            else:
                output[name] = result

        return output

    # ─────────────────────────────────────────────
    # Trading cycle phases
    # ─────────────────────────────────────────────

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

            # Extract candidates from DataMiner output
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
            # Phase 1: Research (parallel)
            research = await self.run_research_phase(market, context)

            # Phase 2: Strategy
            strategy = await self.run_strategy_phase(research, context)

            # Phase 3: Risk check
            risk = await self.run_risk_phase(strategy, context)

            # Final decision via LLM synthesis
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

    # ─────────────────────────────────────────────
    # BaseAgent abstract method implementations
    # ─────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market = input_data.get("market", "us_stock")
        return await self.run_trading_cycle(market, context)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        research = input_data.get("research", {})
        strategy = input_data.get("strategy", {})
        risk = input_data.get("risk", {})
        return await self._synthesize_decision(research, strategy, risk)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return self.get_status()

    # ─────────────────────────────────────────────
    # Synthesis helpers
    # ─────────────────────────────────────────────

    async def _synthesize_decision(
        self,
        research: dict,
        strategy: dict,
        risk: dict
    ) -> dict:
        """Ask LLM to synthesize a final trading decision."""
        approved_signals = risk.get("approved_signals", [])
        if not approved_signals:
            return {
                "action": "HOLD",
                "signals": [],
                "confidence": 0.0,
                "reasoning": "No approved signals after risk assessment",
                "risk_approved": False
            }

        prompt = f"""Based on the following multi-agent analysis, synthesize a final trading decision.

Research Summary: {research.get('summary', {})}
Strategy Signals: {strategy.get('signals', [])}
Risk-Approved Signals: {approved_signals}

Provide a final decision for the top 3 signals at most."""

        schema = {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"},
                            "action": {"type": "string"},
                            "confidence": {"type": "number"},
                            "entry_price": {"type": "number"},
                            "stop_loss": {"type": "number"},
                            "take_profit": {"type": "number"},
                            "reasoning": {"type": "string"}
                        }
                    }
                },
                "market_view": {"type": "string"},
                "overall_confidence": {"type": "number"}
            }
        }

        try:
            result = await self.ask_llm_structured(prompt, schema)
            result["risk_approved"] = True
            return result
        except Exception as e:
            logger.error(f"Decision synthesis failed: {e}")
            return {
                "decisions": approved_signals,
                "market_view": "Unknown",
                "overall_confidence": 0.5,
                "risk_approved": True,
                "error": str(e)
            }

    def _summarize_research(self, results: dict) -> dict:
        """Summarize research results across agents."""
        successful = {k: v for k, v in results.items() if v.get("status") == "SUCCESS"}
        return {
            "total_agents": len(results),
            "successful": len(successful),
            "data_points": sum(
                len(v.get("output", {})) for v in successful.values()
            )
        }

    def _extract_signals(self, results: dict) -> list[dict]:
        """Extract trading signals from strategy agent results."""
        signals = []
        for agent_name, result in results.items():
            if result.get("status") == "SUCCESS":
                output = result.get("output", {})
                if "signal" in output:
                    signals.append(output["signal"])
                elif "signals" in output:
                    signals.extend(output["signals"])
        return signals

    def _filter_signals(
        self,
        signals: list[dict],
        risk_results: dict
    ) -> tuple[list[dict], list[dict]]:
        """Split signals into approved and rejected based on risk assessment."""
        # Default: approve all if no risk agent vetoed
        vetoes = set()
        for result in risk_results.values():
            if result.get("status") == "SUCCESS":
                rejected = result.get("output", {}).get("rejected_symbols", [])
                vetoes.update(rejected)

        approved = [s for s in signals if s.get("symbol") not in vetoes]
        rejected = [s for s in signals if s.get("symbol") in vetoes]
        return approved, rejected

    # ─────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return coordinator and all agent statuses."""
        return {
            "coordinator": self.name,
            "registered_agents": self.list_agents(),
            "broker_stats": self.broker.get_stats(),
            "execution_summary": self.get_execution_summary()
        }
