# 文档索引

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | 系统架构 — 分层、数据流、技术栈、目录结构 |
| [agent-design.md](agent-design.md) | Agent 设计 — ReAct 循环、多 Agent、工具注册、技能、因子库 |
| [api-design.md](api-design.md) | API 设计 — 全部端点列表、请求/响应格式 |
| [DATA_SOURCE_GUIDE.md](DATA_SOURCE_GUIDE.md) | 数据源 — 已集成源、fallback、插件框架 |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | 测试指南 — 运行方式、覆盖统计、添加新测试 |
| [development-constitution.md](development-constitution.md) | 开发宪法（完整版） — 代码规范、分支策略、安全要求 |
| [AGENTS.md](../AGENTS.md) | 开发宪法（精要版） — AI 编码助手自动加载 |
| [AGENT_CONSTITUTION.md](../AGENT_CONSTITUTION.md) | 交易宪法 — 风控原则、仓位限制、决策框架 |
| [ITERATION_PLAN.md](../ITERATION_PLAN.md) | 迭代计划 — 完成进度、待修复问题 |
| [README.md](../README.md) | 项目首页 — 快速开始、功能特性、项目统计 |

## 快速理解项目

```
用户输入 → API 路由 → QuantAgent (ReAct) → 调用工具 → LLM 推理 → 返回结果
                    → Coordinator (多Agent) → Research/S/R → 决策合成
```

## 核心代码路径

```
main.py
├── api/routes.py              # 单 Agent + 市场 + 回测 + Broker API
├── api/multi_agent_routes.py  # 多 Agent API
├── agent/
│   ├── core.py                # QuantAgent（ReAct 核心）
│   ├── llm_client.py          # 多 LLM 客户端
│   ├── memory.py              # SQLite + FTS5 记忆
│   ├── config.py              # 配置加载
│   ├── tools/                 # 40+ 量化工具
│   ├── strategies/            # 18 个交易策略
│   ├── alpha/                 # 251 个因子
│   ├── skills/                # 13 个技能
│   ├── multi_agent/           # 8 个 Agent（Research + Strategy + Risk）
│   ├── broker/                # Alpaca + IBKR 券商连接
│   ├── data/                  # 数据源插件框架
│   └── notify/                # Telegram + Webhook 通知
└── web/                       # Vue 3 前端
```

**启动**：`uv run uvicorn main:app --reload --port 8000`
