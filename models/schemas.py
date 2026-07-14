from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class AgentMessage(BaseModel):
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_results: list[dict[str, Any]] | None = None
    timestamp: datetime = datetime.now()


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000, description="用户查询内容")
    session_id: str | None = Field(None, max_length=100, description="会话ID")
    market: str = Field("us_stock", max_length=20, description="市场类型")
    symbols: list[str] | None = Field(None, max_length=50, description="股票代码列表")


class AgentResponse(BaseModel):
    answer: str
    session_id: str
    thoughts: list[dict[str, Any]] | None = None


class MarketDataRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    market: str = Field("us_stock", max_length=20, description="市场类型")
    interval: str = Field("1d", max_length=10, description="K线周期")
    period: str = Field("1y", max_length=10, description="时间范围")


class BacktestRequest(BaseModel):
    strategy_name: str = Field(..., min_length=1, max_length=50, description="策略名称")
    symbols: list[str] = Field(..., min_length=1, max_length=50, description="股票代码列表")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="结束日期 YYYY-MM-DD")
    initial_capital: float = Field(100000.0, gt=0, le=100000000, description="初始资金")
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
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    direction: str = Field(..., pattern=r"^(long|short)$", description="方向: long/short")
    confidence: float = Field(..., ge=0, le=1, description="信心度 0-1")
    entry_price: float | None = Field(None, gt=0, description="入场价格")
    stop_loss: float | None = Field(None, gt=0, description="止损价格")
    take_profit: float | None = Field(None, gt=0, description="止盈价格")
    reason: str = Field(..., min_length=1, max_length=1000, description="交易理由")
    timestamp: datetime = datetime.now()
