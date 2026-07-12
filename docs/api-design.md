# API 设计

> RESTful 路由、请求/响应模型、流式 SSE、错误处理。

---

## 一、基础信息

- **Base URL**: `http://localhost:8000`
- **文档**: `http://localhost:8000/docs` (Swagger UI)
- **格式**: 所有请求/响应均为 JSON

---

## 二、端点总览

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 |
| GET | `/chat` | Web 聊天界面 |
| POST | `/agent/chat` | Agent 聊天（同步） |
| POST | `/agent/chat/stream` | Agent 聊天（流式 SSE） |
| GET | `/agent/tools` | 工具列表 |
| GET | `/strategies` | 策略列表 |
| POST | `/backtest` | 运行回测 |
| GET | `/market/{market}/overview` | 市场概况 |
| POST | `/market/quote` | 实时行情 |
| POST | `/market/klines` | K 线数据 |

---

## 三、详细说明

### 3.1 服务信息

```
GET /
```

**响应：**

```json
{
  "name": "AIQuantification",
  "version": "0.1.0",
  "description": "AI-powered quantitative trading agent",
  "config": {
    "llm_provider": "deepseek",
    "llm_model": "deepseek-chat",
    "config_file": "./config.yaml"
  },
  "endpoints": { ... }
}
```

### 3.2 Agent 聊天（同步）

```
POST /agent/chat
```

**请求体：**

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `query` | string | 是 | 用户输入 |
| `session_id` | string | 否 | 会话 ID（自动生成） |
| `market` | string | 否 | 市场 (默认 `us_stock`) |

**示例：**

```json
{
  "query": "分析 AAPL 的近期走势，给出交易建议",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "market": "us_stock"
}
```

**响应：**

```json
{
  "answer": "## AAPL 技术分析报告\n\n**当前价格**: $198.50\n\n### 技术指标\n- RSI(14): 45.2 — 中性\n- MACD: 柱状图转正，看多信号\n- SMA20/50: 20 日线在 50 日线上方，多头排列\n\n### 信号\n**信号**: BUY (置信度 0.65)\n**止损**: $188.50 (-5%)\n**仓位**: 轻仓试探",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.3 Agent 聊天（流式）

```
POST /agent/chat/stream
```

**请求体：** 与同步接口相同。

**响应格式：** Server-Sent Events (SSE)

```
data: {"session_id": "uuid-xxx"}

data: 正在获取 AAPL 的行情数据...

data: RSI(14) 为 45.2，处于中性区间...

data: MACD 柱状图转正，看多信号...

data: [DONE]
```

**前端使用：**

```javascript
const eventSource = new EventSource('/agent/chat/stream');
// 注意：实际使用 POST，需要用 fetch + ReadableStream
const response = await fetch('/agent/chat/stream', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query})
});
const reader = response.body.getReader();
```

### 3.4 工具列表

```
GET /agent/tools
```

**响应：**

```json
{
  "tools": [
    "get_stock_quote",
    "get_klines",
    "get_cn_klines",
    "get_market_overview",
    "calculate_indicators",
    "calculate_factor",
    "run_backtest",
    "compare_strategies",
    "calculate_position_size",
    "assess_portfolio_risk",
    "get_stock_news",
    "analyze_sentiment",
    "check_constitution"
  ],
  "count": 13
}
```

### 3.5 策略列表

```
GET /strategies
```

**响应：**

```json
{
  "strategies": [
    {"name": "sma_cross", "description": "SMA 均线交叉策略"},
    {"name": "macd", "description": "MACD 趋势跟踪策略"},
    {"name": "rsi", "description": "RSI 超买超卖反转策略"},
    {"name": "bollinger", "description": "布林带回归策略"}
  ]
}
```

### 3.6 运行回测

```
POST /backtest
```

**请求体：**

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `strategy_name` | string | 是 | 策略名称 |
| `symbols` | [string] | 是 | 标的列表 |
| `start_date` | string | 是 | 开始日期 (YYYY-MM-DD) |
| `end_date` | string | 是 | 结束日期 (YYYY-MM-DD) |
| `initial_capital` | float | 否 | 初始资金 (默认 100000) |

**请求示例：**

```json
{
  "strategy_name": "sma_cross",
  "symbols": ["AAPL", "MSFT"],
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "initial_capital": 100000.0
}
```

**响应：**

```json
[
  {
    "strategy_name": "sma_cross",
    "symbol": "AAPL",
    "total_return": 15.23,
    "annualized_return": 15.23,
    "sharpe_ratio": 1.32,
    "max_drawdown": -8.5,
    "total_trades": 6,
    "win_rate": 0.67
  },
  {
    "strategy_name": "sma_cross",
    "symbol": "MSFT",
    "total_return": 22.1,
    "annualized_return": 22.1,
    "sharpe_ratio": 1.65,
    "max_drawdown": -6.3,
    "total_trades": 5,
    "win_rate": 0.8
  }
]
```

### 3.7 市场概况

```
GET /market/{market}/overview

参数: market = us_stock | cn_stock | hk_stock
```

**响应：**

```json
[
  {"symbol": "^GSPC", "name": "S&P 500", "price": 5678.9, "change_percent": 0.45},
  {"symbol": "^DJI", "name": "Dow 30", "price": 42123.5, "change_percent": 0.32},
  {"symbol": "^IXIC", "name": "NASDAQ", "price": 18567.2, "change_percent": 0.78}
]
```

### 3.8 实时行情

```
POST /market/quote
```

**请求体：**

```json
{
  "symbol": "AAPL",
  "market": "us_stock"
}
```

**响应：**

```json
{
  "symbol": "AAPL",
  "price": 198.5,
  "change": 1.23,
  "change_percent": 0.62,
  "volume": 45230000,
  "market_cap": 3100000000000,
  "name": "Apple Inc."
}
```

### 3.9 K 线数据

```
POST /market/klines
```

**请求体：**

```json
{
  "symbol": "600519.SH",
  "market": "cn_stock",
  "interval": "daily",
  "period": "1y"
}
```

**响应：** K 线数组，每根包含 Date / Open / High / Low / Close / Volume。

---

## 四、错误处理

所有端点使用统一错误格式：

```json
{
  "detail": "错误描述信息"
}
```

HTTP 状态码：

| 状态码 | 含义 | 场景 |
|--------|------|------|
| 200 | 成功 | 正常响应 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 401 | 未授权 | API Key 未配置 |
| 404 | 未找到 | 策略/标的不存在 |
| 422 | 参数校验失败 | Pydantic 校验未通过 |
| 500 | 服务端错误 | LLM 调用失败、数据源错误 |

---

## 五、curl 示例

```bash
# Agent 聊天
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "分析 AAPL 走势", "market": "us_stock"}'

# 工具列表
curl http://localhost:8000/agent/tools

# 策略列表
curl http://localhost:8000/strategies

# 市场概况
curl http://localhost:8000/market/us_stock/overview

# 实时行情
curl -X POST http://localhost:8000/market/quote \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "market": "us_stock"}'

# 回测
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "sma_cross",
    "symbols": ["AAPL"],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  }'
```
