# Agent 核心设计

> ReAct 循环、工具注册机制、LLM 多提供商抽象、记忆系统。

---

## 一、ReAct 循环

Agent 的核心是 **ReAct (Reasoning + Acting)** 模式。每次请求经历以下循环：

```
Input: user query
          │
          ▼
     ┌──────────┐
     │  LLM     │◄──────── messages[system, history, user]
     │ 推理     │
     └────┬─────┘
          │
     ┌────┴─────┐
     │ 有 tool  │  YES ──→ 解析 tool_call → 执行工具
     │_calls?   │                    │
     └────┬─────┘                    ▼
          │ NO              结果注入 messages
          │                    │
          ▼                    ▼
     ┌──────────┐          ┌──────────┐
     │ 返回答案  │          │ LLM 再   │
     │ 给用户    │          │ 次推理    │
     └──────────┘          └──────────┘
                               │
                          max_iter 超限?
                               │
                          ┌────┴─────┐
                          │  YES     │
                          │ 超限返回 │
                          └──────────┘
```

### 关键实现 (agent/core.py)

```python
async def _run_loop(self, messages, session_id, max_iterations=10):
    for iteration in range(max_iterations):
        result = await self.llm.chat(messages, tools=self.tools)

        # 检查是否有工具调用
        if not message.get("tool_calls"):
            return message.get("content")

        # 遍历所有工具调用
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            tool_result = await execute_tool(func_name, **args)
            messages.append({"role": "tool", ...})

    return "已达最大迭代次数..."
```

### 设计要点

- **最大迭代 10 次**：防止无限循环耗尽 token 和 API 费用。
- **Tool result 截断 50000 字符**：避免上下文窗口溢出。
- **异常隔离**：单个工具失败不影响整个循环。
- **每次迭代保存到 Memory**：失败时可恢复会话上下文。

---

## 二、工具注册机制

### 2.1 @tool 装饰器

```python
@tool(
    name="calculate_indicators",
    description="计算技术指标",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "indicators": {"type": "array", "items": {"type": "string"}},
    },
)
async def calculate_indicators(symbol, market="us_stock", indicators=None):
    ...
```

### 2.2 自动生成 Tool Definition

装饰器内部通过 `inspect.signature` 反射函数参数：

| 函数参数 | → | Tool Definition |
|---------|---|-----------------|
| `symbol: str` | → | `{type: "string", required: true}` |
| `market: str = "us_stock"` | → | `{type: "string", default: "us_stock"}` |
| `indicators: list` | → | `{type: "array", items: {type: "string"}}` |

生成格式与 OpenAI function calling 完全兼容：

```json
{
  "type": "function",
  "function": {
    "name": "calculate_indicators",
    "description": "计算技术指标",
    "parameters": {
      "type": "object",
      "properties": {
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场"},
        "indicators": {"type": "array", "items": {"type": "string"}}
      },
      "required": ["symbol"]
    }
  }
}
```

### 2.3 注册中心 (agent/tools/registry.py)

```python
_TOOL_REGISTRY = {
    "get_klines": {"func": <async function>, "definition": {...}},
    "calculate_indicators": {"func": <async function>, "definition": {...}},
    "run_backtest": {"func": <async function>, "definition": {...}},
    ...
}
```

提供三个全局函数：

| 函数 | 用途 |
|------|------|
| `get_tool_definitions()` | 返回所有 tool definition（给 LLM） |
| `execute_tool(name, **kwargs)` | 按名称执行工具 |
| `get_tool_names()` | 返回工具名称列表 |

### 2.4 添加新工具的步骤

1. 在 `agent/tools/` 下新建 `.py` 文件
2. 定义 `async def` 函数，使用 `@tool` 装饰器
3. 重启服务即可（自动注册）

```python
from .registry import tool

@tool(
    name="my_new_tool",
    description="我的新工具",
    parameters={
        "param1": {"type": "string", "description": "参数1"},
    },
)
async def my_new_tool(param1: str, param2: int = 0):
    # 工具逻辑
    return {"result": "ok"}
```

---

## 三、LLM 多提供商抽象

### 3.1 提供商配置

```yaml
# config.yaml
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: "sk-xxx"
  temperature: 0.3
  max_tokens: 4096
  # 备用（可选）
  fallback:
    provider: openai
    model: gpt-4o-mini
    api_key: "sk-xxx"
```

### 3.2 提供商定义

| 提供商 | 默认 API 地址 | 可用模型 |
|--------|-------------|---------|
| deepseek | https://api.deepseek.com | deepseek-chat, deepseek-reasoner |
| openai | https://api.openai.com/v1 | gpt-4o, gpt-4o-mini, o3-mini |
| qwen | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus, qwen-max, qwen-turbo |
| gemini | https://generativelanguage.googleapis.com/v1beta/openai | gemini-2.0-flash, gemini-2.5-pro |

### 3.3 LLMClient 接口

```python
class LLMClient:
    async def chat(self, messages, tools=None, temperature=None, max_tokens=None) -> dict
        # → {"choices": [{"message": {"content": "...", "tool_calls": [...]}}]}

    async def chat_stream(self, messages, tools=None, temperature=None, max_tokens=None)
        # → 逐 chunk yield {"choices": [{"delta": {"content": "..."}}]}
```

### 3.4 Fallback 机制

当主 LLM 调用失败（网络错误、限流、API 错误）：

```python
try:
    resp = await client.post("/chat/completions", json=body)
    resp.raise_for_status()
except Exception:
    if self.fallback_client:
        return await self.fallback_client.chat(messages, tools)
    raise
```

---

## 四、系统提示词与宪法注入

系统提示词在每次请求时动态构建：

```python
SYSTEM_PROMPT = f"""
您是一个量化交易分析 AI 助手。您必须遵守以下宪法：

{_load_constitution()}  ← 从 AGENT_CONSTITUTION.md 读取

您的可用工具：
- ...

决策流程：
1. 至少覆盖 3 个分析维度搜集数据
2. 多维度综合加权
3. 分配信号等级 (STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL)
4. 分配置信度 (0.0~1.0)
5. 按风控规则计算仓位
6. 始终包含止损和止盈
"""
```

宪法文件 (`AGENT_CONSTITUTION.md`) 共 7 章：

| 章 | 核心约束 |
|----|---------|
| 风控原则 | 单笔亏损 ≤2%、仓位 ≤30%、三级回撤熔断 |
| 数据原则 | 禁止前瞻偏差、数据源优先级、缓存时效 |
| 决策框架 | 三维度分析、五级信号、置信度评分 |
| 伦理准则 | 透明度、合规性、隐私保护 |

---

## 五、记忆系统

### 5.1 表结构

```sql
sessions (session_id, created_at, updated_at)
messages (id, session_id, role, content, metadata, created_at)
trades   (id, session_id, symbol, direction, confidence, pnl, ...)
knowledge(id, market, symbol, key, value, created_at)
```

### 5.2 API

```python
memory = AgentMemory(db_path="~/.aiquantification/memory.db")

# 会话管理
memory.create_session("uuid-xxx")
memory.get_history("uuid-xxx", limit=50)

# 消息存储
memory.save_message("uuid-xxx", "user", "分析 AAPL")
memory.save_message("uuid-xxx", "assistant", "结果...", metadata={"tool": "get_klines"})

# 交易记录
memory.save_trade("uuid-xxx", "AAPL", "BUY", 0.8, 150.0, "MACD 金叉")

# 知识存储
memory.save_knowledge("us_stock", "AAPL", "pe_ratio", "28.5")
memory.get_knowledge(market="us_stock", symbol="AAPL")
```

### 5.3 会话恢复

每次请求通过 `session_id` 恢复上下文，最多加载最近 20 条消息：

```python
def _convert_history(self, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-20:]:  # 只保留最近 20 条
        messages.append({"role": msg["role"], "content": msg["content"]})
    return messages
```

---

## 六、错误处理策略

| 异常类型 | 处理方式 |
|---------|---------|
| LLM API 错误 (4xx) | 仅报告错误，不自动重试 |
| LLM 网络超时 | 自动切换到 fallback provider |
| 工具执行异常 | 返回 `{"error": "..."}`，注入循环继续 |
| JSON 解析失败 | 返回 `{"error": "parse error"}` |
| 数据源不可用 | 报告具体缺失，建议备用数据源 |
