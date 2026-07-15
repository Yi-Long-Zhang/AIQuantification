"""
Multi-Agent System - API Routes

Provides REST API endpoints for the multi-agent trading system.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from agent.config import settings
from agent.llm_client import LLMClient
from agent.multi_agent import CoordinatorAgent, MessageBroker

router = APIRouter(prefix="/multi-agent", tags=["multi-agent"])
limiter = Limiter(key_func=get_remote_address)

# Singleton instances
_broker: MessageBroker | None = None
_coordinator: CoordinatorAgent | None = None


def get_coordinator() -> CoordinatorAgent:
    global _broker, _coordinator
    if _coordinator is None:
        _broker = MessageBroker()
        llm = LLMClient(provider=settings.llm_provider)
        _coordinator = CoordinatorAgent(llm_client=llm, broker=_broker)
    return _coordinator


# ─── Request / Response models ─────────────────────────────────────────────

class RunCycleRequest(BaseModel):
    market: str = "us_stock"
    context: dict = {}


class RegisterAgentRequest(BaseModel):
    agent_type: str      # future: "market_analyst", "backtester", …
    agent_name: str


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/status")
@limiter.limit("60/minute")
async def get_status(request: Request):
    """Return coordinator and all registered agents' status."""
    coordinator = get_coordinator()
    return coordinator.get_status()


@router.post("/cycle")
@limiter.limit("5/minute")
async def run_cycle(request: Request, req: RunCycleRequest):
    """
    Trigger a full trading cycle.

    Runs: Research → Strategy → Risk → Final Decision
    """
    coordinator = get_coordinator()
    result = await coordinator.run_trading_cycle(
        market=req.market,
        context=req.context
    )
    return result


@router.get("/agents")
@limiter.limit("60/minute")
async def list_agents(request: Request):
    """List all registered agents."""
    coordinator = get_coordinator()
    return {
        "agents": coordinator.list_agents(),
        "count": len(coordinator.list_agents())
    }


@router.get("/messages")
@limiter.limit("30/minute")
async def get_messages(request: Request, agent: str | None = None, limit: int = 50):
    """Get message history, optionally filtered by agent."""
    coordinator = get_coordinator()
    messages = coordinator.broker.get_message_history(agent_name=agent, limit=limit)
    return {
        "messages": [m.to_dict() for m in messages],
        "count": len(messages)
    }


@router.get("/broker/stats")
@limiter.limit("60/minute")
async def broker_stats(request: Request):
    """Return message broker statistics."""
    coordinator = get_coordinator()
    return coordinator.broker.get_stats()
