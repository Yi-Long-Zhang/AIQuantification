# 系统架构

## 分层结构

```
┌─────────────────────────────────────────────────┐
│                   FastAPI                        │
│               main.py + api/routes.py            │
│              (HTTP 接口、静态文件)                │
├─────────────────────────────────────────────────┤
│                  Agent 层                        │
│            agent/core.py (ReAct 循环)            │
│         agent/llm_client.py (多 LLM 客户端)      │
│            agent/memory.py (SQLite 记忆)          │
├─────────────────────────────────────────────────┤
│              工具层 (agent/tools/)                │
│  market_data.py │ backtest.py │ technical.py     │
│  risk.py │ news.py │ constitution.py │ registry.py│
├─────────────────────────────────────────────────┤
│            策略层 (agent/strategies/)             │
│        sma_cross │ macd │ rsi │ bollinger        │
├─────────────────────────────────────────────────┤
│           数据层 (外部 API)                       │
│       yfinance │ akshare │ newsapi.org           │
└─────────────────────────────────────────────────┘
```

## 依赖关系

```
api/routes.py
  ↓
agent/core.py (QuantAgent)
  ├── agent/llm_client.py (LLM 调用)
  ├── agent/memory.py (会话记忆)
  ├── agent/tools/registry.py (工具调度)
  │   ├── market_data.py → yfinance, akshare
  │   ├── technical.py → pandas-ta
  │   ├── backtest.py → numpy, pandas
  │   ├── risk.py → numpy
  │   └── news.py → newsapi.org
  └── agent/strategies/registry.py → 策略定义
```

**规则**：只能上层调用下层，不能跨层或反向调用。

## 技术栈

| 用途 | 库 |
|------|-----|
| Web 框架 | FastAPI + uvicorn |
| LLM 调用 | openai (兼容 DeepSeek/OpenAI/Qwen/Gemini) |
| 美股数据 | yfinance |
| A股数据 | akshare |
| 技术指标 | pandas-ta |
| 数值计算 | numpy, pandas |
| 记忆存储 | SQLite (agent/memory.py) |
| 配置管理 | PyYAML → Settings 对象 |

## 数据流示例：用户问 "分析 AAPL"

```
1. POST /agent/chat  {"query": "分析 AAPL"}
2. routes.py → QuantAgent.chat("分析 AAPL", session_id)
3. core.py 构建 messages（system prompt + 历史 + 用户问题）
4. LLM 返回 → 需要调用工具 → tool_calls: [get_stock_quote, calculate_indicators]
5. core.py 执行工具 → 返回工具结果给 LLM
6. LLM 综合分析 → 返回最终回答
7. 响应: {"answer": "AAPL 当前价格... 技术面...", "session_id": "xxx"}
```

## 目录结构

```
AIQuantification/
├── main.py              # FastAPI 入口
├── config.yaml          # 用户配置（git ignored）
├── config.yaml.example  # 配置模板
├── pyproject.toml       # uv 项目配置
├── AGENTS.md            # AI 开发宪法
├── agent/
│   ├── config.py        # Settings（读 config.yaml）
│   ├── core.py          # QuantAgent（ReAct 核心）
│   ├── llm_client.py    # 多 LLM 客户端
│   ├── memory.py        # SQLite 记忆
│   ├── tools/           # 工具集（@tool 装饰器）
│   └── strategies/      # 策略定义 + 注册
├── api/
│   └── routes.py        # 所有 API 路由
├── models/
│   └── schemas.py       # Pydantic 数据模型
├── web/
│   ├── index.html       # 聊天 Web UI
│   └── static/          # CSS/JS
└── docs/                # 文档
```
