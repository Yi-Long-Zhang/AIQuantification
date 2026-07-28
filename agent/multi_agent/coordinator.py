"""
Multi-Agent System - Coordinator Agent

The Coordinator is the master orchestrator that manages all other agents,
decomposes tasks, and synthesizes results into final decisions.

Phase methods (research/strategy/risk/cycle) are in trading_cycle.py.
Decision synthesis helpers are in decision_synthesizer.py.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BaseAgent
from .communication import AgentMessage, MessageBroker, MessageType, MessagePriority
from .trading_cycle import TradingCycleMixin
from .decision_synthesizer import DecisionSynthesizerMixin

logger = logging.getLogger(__name__)


class CoordinatorAgent(TradingCycleMixin, DecisionSynthesizerMixin, BaseAgent):
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
        results = await self._gather_safe(tasks, names)
        return results

    async def _gather_safe(
        self,
        coros: list,
        names: list[str],
    ) -> dict[str, dict]:
        """Gather coroutines with exception handling per agent."""
        import asyncio
        gathered = await asyncio.gather(*coros, return_exceptions=True)
        output = {}
        for name, result in zip(names, gathered):
            if isinstance(result, Exception):
                logger.error(f"Agent {name} raised: {result}")
                output[name] = {"status": "FAILED", "error": str(result)}
            else:
                output[name] = result
        return output

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
