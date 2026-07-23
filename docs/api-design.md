# API 设计

基础 URL：`http://localhost:8000` · 格式：JSON · 前端：`http://localhost:5173`

## Agent 聊天

```
POST /agent/chat
    {"query": "分析 AAPL", "session_id": "可选", "market": "us_stock"}
    → {"answer": "分析结果...", "session_id": "xxx"}

POST /agent/chat/stream
    {"query": "分析 AAPL", "session_id": "可选"}
    → SSE stream: data: {"session_id": "..."} ... data: [DONE]
```

## Agent 能力

```
GET /agent/tools    → {"tools": [...], "count": 40+}
GET /strategies     → {"strategies": [{name, description, type, tags, markets, params, risk_level}, ...]}
GET /skills         → {"skills": [...], "count": 13}
GET /alpha/factors  → {"alpha158": [...], "alpha101": [...]}
```

## 市场数据

```
GET  /market/{market}/overview         → 市场总览 (us_stock/cn_stock/hk_stock/crypto)
POST /market/quote     {"symbol":"AAPL", "market":"us_stock"}          → 实时报价
POST /market/klines    {"symbol":"AAPL", "market":"us_stock", "interval":"1d", "period":"1y"} → K线
```

## 回测

```
POST /backtest
    {"strategy_name": "sma_cross", "symbols": ["AAPL"],
     "start_date": "2024-01-01", "end_date": "2025-01-01", "initial_capital": 100000}
    → [{"symbol":"AAPL","total_return":15.2,"sharpe_ratio":1.5,...}]
```

## Alpha 因子

```
POST /alpha/compute   {"symbol":"AAPL", "market":"us_stock", "factor_set":"alpha158"}
POST /alpha/evaluate  {"symbol":"AAPL", "market":"us_stock", "factor_set":"alpha158", "top_n":20}
```

## 多 Agent

```
GET  /multi-agent/status         → 协调器状态
POST /multi-agent/cycle          → 触发完整交易周期 {"market":"us_stock"}
GET  /multi-agent/agents         → Agent 列表
GET  /multi-agent/messages       → 消息历史
GET  /multi-agent/broker/stats   → Broker 统计
```

## 券商连接

```
GET  /broker/list                → 已注册券商列表
GET  /broker/{name}/status       → 账户 + 持仓
POST /broker/{name}/connect      → 连接券商
GET  /broker/{name}/orders       → 订单列表
POST /broker/import-trades       → CSV 交易导入
```

## 基础

```
GET /       → 服务信息 + 端点索引
GET /health → {"status":"ok","agent":"QuantAgent"}
GET /chat   → HTML 聊天界面
```
