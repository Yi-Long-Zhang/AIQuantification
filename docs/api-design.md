# API 设计

## 基础信息

- 基础 URL：`http://localhost:8000`
- 数据格式：JSON
- 前端 UI：`GET /chat` → `web/index.html`

## 接口列表

### 健康检查

```
GET /health
→ {"status": "ok", "agent": "QuantAgent"}
```

### Agent 聊天（同步）

```
POST /agent/chat
请求：{"query": "分析 AAPL", "session_id": "可选", "market": "us_stock"}
响应：{"answer": "分析结果...", "session_id": "xxx"}
```

### Agent 聊天（流式 SSE）

```
POST /agent/chat/stream
请求：{"query": "分析 AAPL", "session_id": "可选"}
响应：SSE 事件流
  data: {"session_id": "xxx"}
  data: "部分回答文本..."
  data: [DONE]
```

### 工具列表

```
GET /agent/tools
→ {"tools": ["get_stock_quote", "get_klines", ...], "count": 35}
```

### 策略列表

```
GET /strategies
→ {"strategies": [{"name": "sma_cross", "description": "..."}, {"name": "macd", ...}, ...]}
```

### 回测

```
POST /backtest
请求：{
  "strategy_name": "sma_cross",
  "symbols": ["AAPL", "GOOGL"],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "initial_capital": 100000
}
响应：[{
  "strategy_name": "sma_cross",
  "symbol": "AAPL",
  "total_return": 15.2,
  "annualized_return": 15.2,
  "sharpe_ratio": 1.5,
  "max_drawdown": -8.3,
  "total_trades": 24,
  "win_rate": 58.3
}]
```

### 市场总览

```
GET /market/{market}/overview
→ {"market": "us_stock", "indices": [...], "timestamp": "..."}
```

### 实时报价

```
POST /market/quote
请求：{"symbol": "AAPL", "market": "us_stock"}
→ {"symbol": "AAPL", "price": 195.5, "change": 1.2, ...}
```

### K 线数据

```
POST /market/klines
请求：{"symbol": "AAPL", "market": "us_stock", "interval": "1d", "period": "1y"}
→ K 线 DataFrame 数据
```

### Alpha 因子列表

```
GET /alpha/factors?factor_set=all
→ {"alpha158": [...], "alpha101": [...]}
```

### Alpha 因子计算

```
POST /alpha/compute
请求：{"symbol": "AAPL", "market": "us_stock", "factor_set": "alpha158"}
→ {"symbol": "AAPL", "factor_set": "alpha158", "data": [...], "rows": 5}
```

### Alpha 因子评估

```
POST /alpha/evaluate
请求：{"symbol": "AAPL", "market": "us_stock", "factor_set": "alpha158", "top_n": 20}
→ {"symbol": "AAPL", "top_factors": [...], "total_evaluated": 160}
```

## 数据模型

所有请求/响应模型定义在 `models/schemas.py`：

- `AgentRequest` / `AgentResponse` — Agent 聊天
- `MarketDataRequest` — 行情查询
- `BacktestRequest` / `BacktestResult` — 回测
- `TradeSignal` — 交易信号
