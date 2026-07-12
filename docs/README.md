# 文档索引

| 文档 | 说明 |
|------|------|
| [architecture.md](architecture.md) | 系统架构 — 分层、数据流、技术栈 |
| [agent-design.md](agent-design.md) | Agent 设计 — ReAct 循环、LLM 调用、工具注册 |
| [api-design.md](api-design.md) | API 路由 — 接口列表、请求/响应格式 |

## 快速理解项目

```
用户输入 → Agent (ReAct 循环) → 调用工具 → LLM 推理 → 返回结果
```

**核心代码路径**：

```
main.py → api/routes.py → agent/core.py → agent/llm_client.py
                                           → agent/tools/*.py
                                           → agent/strategies/*.py
```

**配置**：`config.yaml` → `agent/config.py` → `Settings` 对象（API Key、数据库路径等）

**启动**：`uv run uvicorn main:app --reload --port 8000`
