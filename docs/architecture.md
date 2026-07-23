# 系统架构

## 分层结构

```
┌─────────────────────────────────────────────────────────┐
│               API 层 (FastAPI)                           │
│  api/routes.py + api/multi_agent_routes.py               │
│  (40+ HTTP 端点)                                         │
├─────────────────────────────────────────────────────────┤
│              Agent 层                                    │
│  agent/core.py (QuantAgent ReAct)                        │
│  agent/multi_agent/coordinator.py (8 Agent 调度)          │
│  agent/llm_client.py (4 LLM 提供商)                       │
│  agent/memory.py (SQLite + FTS5)                         │
│  agent/skills/ (13 个技能)                                │
├─────────────────────────────────────────────────────────┤
│            工具层 (agent/tools/ — 40+ 工具)                │
│  market_data · crypto · hk_stock · technical · alpha     │
│  backtest · risk · news · constitution                  │
├─────────────────────────────────────────────────────────┤
│          策略层 (agent/strategies/ — 18 策略)             │
│  趋势/反转/均值回归/事件驱动/组合                          │
├─────────────────────────────────────────────────────────┤
│          券商层 (agent/broker/)                           │
│  Alpaca (REST) · IBKR (ib_insync) · Shadow Account       │
├─────────────────────────────────────────────────────────┤
│        基础设施 (agent/data/ + agent/notify/)              │
│  数据源框架 · Telegram · Webhook                          │
└─────────────────────────────────────────────────────────┘
```

## 规则

只能上层调用下层，禁止跨层或反向调用：
- ✅ `api/` → `agent/`
- ✅ `agent/` → `agent/tools/` / `agent/strategies/` / `agent/broker/`
- ✅ `agent/tools/` → 外部库
- ❌ `api/` → 直接调用外部库
- ❌ `agent/tools/` → `api/`

## 技术栈

| 用途 | 库 |
|------|-----|
| Web 框架 | FastAPI + uvicorn |
| LLM | openai SDK (DeepSeek/OpenAI/Qwen/Gemini) |
| 美股数据 | yfinance |
| A股/港股数据 | akshare |
| 加密货币 | ccxt + pycoingecko |
| 券商 API | httpx (Alpaca REST) + ib_insync (IBKR) |
| 数值计算 | numpy, pandas, scipy |
| 记忆存储 | SQLite + FTS5 (aiosqlite) |
| 配置 | PyYAML → Settings |
| 限流 | slowapi |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |

## 目录结构

```
AIQuantification/
├── main.py                    # FastAPI 入口
├── config.yaml.example        # 配置模板
├── agent/
│   ├── config.py              # Settings
│   ├── core.py                # QuantAgent
│   ├── llm_client.py          # LLM 客户端
│   ├── memory.py              # SQLite + FTS5
│   ├── tools/                 # 40+ @tool
│   ├── strategies/            # 18 策略
│   ├── alpha/                 # 251 因子 (Alpha158 + Alpha101)
│   ├── skills/                # 13 技能
│   ├── multi_agent/           # 8 Agent
│   │   ├── research/          # 5 Research Agent
│   │   ├── strategy/          # Backtester + Portfolio
│   │   └── risk/              # RiskManager
│   ├── broker/                # Alpaca + IBKR + Shadow
│   ├── data/                  # 数据源框架
│   └── notify/                # Telegram + Webhook
├── api/
│   ├── routes.py              # 单 Agent + Market + Backtest + Broker
│   └── multi_agent_routes.py  # 多 Agent API
├── models/schemas.py          # Pydantic 模型
├── tests/                     # 280+ 测试
├── web/                       # Vue 3 前端
│   └── src/
│       ├── views/             # 7 个页面
│       ├── components/        # 5 个组件
│       └── api/               # Axios 封装
└── docs/                      # 文档
```
