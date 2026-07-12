from pydantic import BaseModel
from typing import Any
from datetime import datetime


class AgentMessage(BaseModel):
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[dict[str, Any]] | None = None
    timestamp: datetime = datetime.now()


class AgentRequest(BaseModel):
    query: str
    session_id: str | None = None
    market: str = "us_stock"
    symbols: list[str] | None = None


class AgentResponse(BaseModel):
    answer: str
    session_id: str
    thoughts: list[dict[str, Any]] | None = None


class MarketDataRequest(BaseModel):
    symbol: str
    market: str = "us_stock"
    interval: str = "1d"
    period: str = "1y"


class BacktestRequest(BaseModel):
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    parameters: dict[str, Any] | None = None


class BacktestResult(BaseModel):
    strategy_name: str
    symbol: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float


class TradeSignal(BaseModel):
    symbol: str
    direction: str
    confidence: float
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    reason: str
    timestamp: datetime = datetime.now()
