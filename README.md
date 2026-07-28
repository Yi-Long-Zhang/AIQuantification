# AI量化交易系统

**项目状态**: 🟢 生产就绪  
**版本**: v3.0.0  
**最后更新**: 2026-07-28

---

## 🎯 项目概述

基于 AI Agent 的量化交易系统，支持策略开发、回测、模拟交易、实时行情监控。

### 核心能力

- **40+ 量化工具** — 多市场数据、技术指标、Alpha 因子、回测、风控、券商连接
- **28 个交易策略** — 趋势/反转/均值回归/事件驱动/组合/ML 六大类别
- **264 + 8 Alpha 因子** — Alpha101 + Alpha158 + Alpha191 + K线形态因子
- **8 个 AI Agent** — 5 Research + Backtester + PortfolioOptimizer + RiskManager
- **13 个 AI 技能** — 行业轮动、跨市场套利、财报解读、形态识别等
- **纸交易引擎** — 虚拟资金簿、市价/限价单、滑点佣金、P&L 追踪
- **实时行情管道** — yfinance/ccxt/akshare 真实数据 WebSocket 推送
- **策略自动调度** — per-market asyncio 定时器，按交易时段自动运行
- **风控系统** — 日亏熔断、仓位限制、杠杆上限、日交易数限制
- **Vue 3 前端** — 8 个页面（TypeScript 全类型化，零 `any`）
- **券商连接** — Alpaca + IBKR + PaperBroker
- **通知系统** — Telegram + Webhook
- **TTL 数据缓存** — 6 种粒度内存缓存层
- **LLM 指数退避重试** — 3 次重试（2s/4s/8s + jitter）后切换 fallback

---

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+

### 安装和启动

```bash
# 1. 克隆项目
git clone https://github.com/Yi-Long-Zhang/AIQuantification.git
cd AIQuantification

# 2. 安装后端依赖
uv sync

# 3. 配置
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 LLM API Key

# 4. 启动后端（自动启动行情轮询 + 策略调度器）
uv run uvicorn main:app --reload

# 5. 启动前端（新终端）
cd web
npm install
npm run dev
```

### 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端 |
| http://localhost:8000 | 后端 API |
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:5173/paper | 模拟交易看板 |

---

## 🏗️ 项目结构

```
AIQuantification/
├── main.py                 FastAPI 入口
├── conftest.py             pytest fixtures
├── config.yaml(.example)   配置
├── pyproject.toml          构建配置
├── agent/                  主包
│   ├── core.py             ReAct Agent 循环
│   ├── llm_client.py       LLM 客户端（4 家提供商 + 退避重试）
│   ├── memory.py           SQLite + FTS5 记忆（公共 API）
│   ├── models.py           Pydantic 数据模型
│   ├── scheduler.py        交易周期自动调度
│   ├── tools/              40+ 量化工具
│   │   ├── cache.py        TTL 内存缓存层
│   │   └── ...
│   ├── strategies/         28 个交易策略（6 类别）
│   │   ├── evaluator.py    策略评估/对比/因子归因
│   │   └── ...
│   ├── alpha/              264+8 Alpha 因子库
│   ├── skills/             13 个 AI 技能（Markdown）
│   ├── multi_agent/        8 Agent 协作框架
│   ├── broker/             券商连接（Alpaca/IBKR/Paper）
│   ├── data/               数据源框架
│   ├── notify/             Telegram/Webhook 通知
│   └── ws/                 WebSocket 实时行情
├── api/                    FastAPI 路由
├── tests/                  300+ 测试
├── docs/                   技术文档
├── scripts/                工具脚本
└── web/                    Vue 3 + TypeScript 前端
```

---

## 📚 文档

| 文档 | 内容 |
|------|------|
| [架构设计](docs/architecture.md) | 系统分层架构和技术栈 |
| [Agent设计](docs/agent-design.md) | ReAct 循环、多 Agent 协作 |
| [API设计](docs/api-design.md) | REST API 规范 |
| [开发准则](docs/development-constitution.md) | 代码规范、Git 提交规范 |
| [Agent准则](docs/agent-constitution.md) | 交易行为准则 |
| [测试指南](docs/TESTING_GUIDE.md) | 测试策略 |
| [数据源配置](docs/DATA_SOURCE_GUIDE.md) | 数据源和容错 |
| [迭代计划](ITERATION_PLAN.md) | 项目路线图 |

---

## 📊 技术栈

### 后端

- **Python 3.13+** / FastAPI + uvicorn
- **SQLite + FTS5**（WAL 模式）
- **yfinance / akshare / ccxt** — 多市场数据
- **pandas / numpy / scipy / lightgbm**
- **OpenAI SDK** — DeepSeek / OpenAI / Qwen / Gemini
- **包管理** uv

### 前端

- **Vue 3** + TypeScript + Vite
- **Element Plus** / **lightweight-charts**
- **Pinia** 状态管理 / **Axios** HTTP

---

## 📈 项目统计

| 指标 | 数值 |
|------|------|
| Python 文件 | 74 |
| 量化工具 | 40+ |
| 交易策略 | 28（6 类别） |
| Alpha 因子 | 264 + 8 |
| AI Agent | 8 |
| AI 技能 | 13 |
| 券商连接 | 3（Alpaca + IBKR + Paper） |
| 前端页面 | 8 |
| 测试用例 | 300+ |
