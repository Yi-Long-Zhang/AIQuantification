import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from agent.config import settings
from agent.core import QuantAgent
from agent.strategies.registry import list_strategies
from agent.tools.registry import get_tool_names
from models.schemas import AgentRequest, AgentResponse, BacktestRequest, BacktestResult, MarketDataRequest

router = APIRouter()
_agent: QuantAgent | None = None
limiter = Limiter(key_func=get_remote_address)


def get_agent() -> QuantAgent:
    global _agent
    if _agent is None:
        _agent = QuantAgent(llm_provider=settings.llm_provider)
    return _agent


@router.post("/agent/chat", response_model=AgentResponse)
@limiter.limit("10/minute")
async def agent_chat(request: Request, req: AgentRequest):
    session_id = req.session_id or str(uuid.uuid4())
    agent = get_agent()
    answer = await agent.chat(req.query, session_id)
    return AgentResponse(answer=answer, session_id=session_id)


@router.post("/agent/chat/stream")
@limiter.limit("10/minute")
async def agent_chat_stream(request: Request, req: AgentRequest):
    session_id = req.session_id or str(uuid.uuid4())
    agent = get_agent()

    async def generate():
        yield f"data: {{\"session_id\": \"{session_id}\"}}\n\n"
        async for chunk in agent.stream_chat(req.query, session_id):
            if chunk:
                yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agent/tools")
async def list_tools():
    return {"tools": get_tool_names(), "count": len(get_tool_names())}


@router.get("/strategies")
async def get_strategies():
    return {"strategies": list_strategies()}


@router.post("/backtest", response_model=list[BacktestResult])
async def run_backtest(req: BacktestRequest):
    from agent.tools.backtest import run_backtest as run_bt
    results = []
    for symbol in req.symbols:
        result = await run_bt(
            symbol=symbol,
            strategy=req.strategy_name,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
        )
        if "error" not in result:
            results.append(BacktestResult(
                strategy_name=req.strategy_name,
                symbol=symbol,
                total_return=result.get("total_return_pct", 0),
                annualized_return=result.get("annualized_return_pct", 0),
                sharpe_ratio=result.get("sharpe_ratio", 0),
                max_drawdown=result.get("max_drawdown_pct", 0),
                total_trades=result.get("total_trades", 0),
                win_rate=result.get("win_rate", 0),
            ))
    return results


@router.get("/market/{market}/overview")
async def market_overview(market: str = "us_stock"):
    from agent.tools.market_data import get_market_overview
    return await get_market_overview(market)


@router.post("/market/quote")
async def market_quote(req: MarketDataRequest):
    from agent.tools.market_data import get_stock_quote
    return await get_stock_quote(req.symbol, req.market)


@router.post("/market/klines")
async def market_klines(req: MarketDataRequest):
    if req.market == "cn_stock":
        from agent.tools.market_data import get_cn_klines
        return await get_cn_klines(req.symbol, req.interval, req.period)
    from agent.tools.market_data import get_klines
    return await get_klines(req.symbol, req.market, req.interval, req.period)


@router.get("/alpha/factors")
async def list_alpha_factors(factor_set: str = "all"):
    from agent.tools.alpha import list_alpha_factors as list_factors
    return await list_factors(factor_set)


@router.post("/alpha/compute")
async def compute_alpha(symbol: str, market: str = "us_stock", factor_set: str = "alpha158"):
    from agent.tools.alpha import compute_alpha_factors
    return await compute_alpha_factors(symbol, market, factor_set)


@router.post("/alpha/evaluate")
async def evaluate_alpha(symbol: str, market: str = "us_stock", factor_set: str = "alpha158", top_n: int = 20):
    from agent.tools.alpha import evaluate_alpha_factors
    return await evaluate_alpha_factors(symbol, market, factor_set, top_n)


@router.get("/health")
async def health():
    return {"status": "ok", "agent": "QuantAgent"}
