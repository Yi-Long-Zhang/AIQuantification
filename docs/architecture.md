# 架构总览

> 整体架构设计、模块职责、数据流与分层模型。

---

## 一、设计目标

- **模块化**：每个子系统职责单一，可独立替换或扩展。
- **LLM 无关**：通过抽象层支持任意 OpenAI 兼容 API（DeepSeek / OpenAI / Qwen / Gemini）。
- **工具驱动**：Agent 通过工具与外部世界交互，工具自动注册为 LLM function calling schema。
- **安全优先**：智能体宪法约束行为边界，三级风控熔断。
- **可审计**：所有决策保留完整证据链，SQLite 持久化。

---

## 二、系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户接口层 (API Layer)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ REST API     │  │ SSE Stream   │  │ Web Chat UI            │ │
│  │ /agent/chat  │  │ /chat/stream │  │ /chat                  │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────────────────┘ │
└─────────┼──────────────────┼────────────────────────────────────┘
          │                  │
┌─────────▼──────────────────▼────────────────────────────────────┐
│                     编排层 (Orchestration)                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Agent Core (ReAct Loop)                                   │ │
│  │  ① 解析用户输入 → ② LLM 推理 → ③ 工具调用 → ④ 结果注入     │ │
│  │  ⑤ 循环直到 LLM 给出最终答案                                │ │
│  └──────────┬─────────────────────────────────────────────────┘ │
└─────────────┼───────────────────────────────────────────────────┘
              │
    ┌─────────┼──────────┬────────────────┬─────────────┐
    ▼         ▼          ▼                ▼             ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐ ┌──────────┐
│ LLM    │ │ 工具   │ │ 策略   │ │ 记忆         │ │ 宪法     │
│ 客户端 │ │ 注册表 │ │ 注册表 │ │ Memory       │ │ 约束     │
└───┬────┘ └───┬────┘ └───┬────┘ └──────┬───────┘ └──────────┘
    │          │          │             │
    ▼          ▼          ▼             ▼
┌────────┐ ┌──────────────────────┐ ┌──────────┐
│Config  │ │  工具实现层           │ │ SQLite   │
│Loader  │ │ market_data          │ │ DB       │
│        │ │ technical            │ │          │
│yaml →  │ │ backtest             │ │ sessions │
│dict    │ │ risk                 │ │ messages │
│        │ │ news                 │ │ trades   │
│        │ │ constitution         │ │ knowledge│
└────────┘ └──────────────────────┘ └──────────┘
```

---

## 三、分层详解

### 3.1 用户接口层

**职责**：接收外部请求，返回响应。

- **REST API**：`/agent/chat` — 同步聊天、`/agent/tools` — 工具列表、`/backtest` — 回测。
- **SSE Stream**：`/agent/chat/stream` — 流式输出，适合长时间分析任务。
- **Web Chat UI**：`/chat` — 暗色主题的浏览器聊天界面，无需额外客户端。

### 3.2 编排层

**职责**：驱动 Agent 的思考-行动-观察循环。

- **ReAct Loop**：LLM 推理 → 选择工具 → 执行工具 → 观察结果 → 继续推理。
- **最大迭代次数**：默认 10 轮，防止无限循环。
- **System Prompt 注入**：智能体宪法 + 能力描述 + 决策流程，每次请求自动注入。

### 3.3 LLM 抽象层

**职责**：屏蔽不同 LLM 提供商的 API 差异。

- 支持：DeepSeek / OpenAI / Qwen / Gemini。
- 统一接口：`chat()` 同步、`chat_stream()` 流式。
- 失败回退：主 LLM 不可用时自动切换 fallback 配置。
- 所有凭据通过 `config.yaml` 读取，不依赖环境变量。

### 3.4 工具层

**职责**：Agent 与外部世界交互的唯一途径。

所有工具通过 `@tool` 装饰器注册，自动：
1. 生成 OpenAI 兼容的 `tools` 定义（name / description / parameters）
2. 注册到 `_TOOL_REGISTRY`
3. 在 `/agent/tools` 端点可见

### 3.5 策略层

**职责**：定义交易策略信号生成逻辑。

- 基类 `Strategy` 定义 `generate_signals(df) -> pd.Series` 接口。
- 内置策略：SMA 金叉、MACD、RSI 超买超卖、布林带回归。
- 可通过继承 `Strategy` 添加自定义策略，自动注册。

### 3.6 记忆层

**职责**：跨会话持久化数据。

| 表 | 用途 |
|----|------|
| `sessions` | 会话元数据 |
| `messages` | 聊天记录（含工具调用元数据） |
| `trades` | 交易记录 |
| `knowledge` | 知识点存储（市场/标的 → 键值对） |

### 3.7 配置层

**职责**：统一管理所有配置。

- 文件：`config.yaml`（本地）、`config.yaml.example`（模板）。
- 查找路径：`./config.yaml` → `~/.aiquantification/config.yaml` → `/etc/aiquantification/config.yaml`。
- 模块：`agent/config.py` → 全局 `settings` 对象。

---

## 四、数据流

### 4.1 聊天请求流

```
用户输入 "分析 AAPL"
    │
    ▼
POST /agent/chat { query: "分析 AAPL", session_id: "xxx" }
    │
    ▼
Agent Core 创建/恢复会话
    │
    ▼
构造 System Prompt（宪法 + 能力描述）
    │
    ▼
构造 Messages（system + 历史 + 用户）
    │
    ▼
LLM 推理返回 tool_calls
    │
    ▼
┌─ 循环 ──────────────────────────────────────┐
│  解析 tool_call → 执行对应工具              │
│  e.g. get_klines("AAPL") → get_indicators() │
│  → 返回结果注入 messages                     │
│  → LLM 再次推理                              │
└─────────────────────────────────────────────┘
    │
    ▼
LLM 返回最终文本答案
    │
    ▼
保存到 Memory → 返回响应
```

### 4.2 工具注册流

```
@tool(name="get_klines", description="...", parameters={...})
async def get_klines(symbol, market, interval, period):
    ...

    │
    ▼
registry.py:
  - 反射解析函数签名 → 生成 JSON Schema
  - 注册到 _TOOL_REGISTRY[name] = {func, definition}
  - definition = OpenAI tools[0] 格式
    │
    ▼
/agent/tools → 返回所有工具定义
LLM 调用 → execute_tool(name, **kwargs)
```

---

## 五、设计决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| LLM 协议 | OpenAI 兼容 API | 统一接口，供应商无感切换 |
| 工具装饰器 | `@tool` 自注册 | 零配置，即写即用 |
| 配置格式 | YAML | 可读性好，支持注释 |
| API 风格 | REST + SSE | 同步/流式双模式 |
| 记忆存储 | SQLite | 零依赖，轻量可靠 |
| 回测引擎 | 向量化计算 | 速度快，适合批量回测 |
| 技术指标 | pandas-ta | 覆盖 100+ 指标，社区活跃 |
| 宪法注入 | System Prompt | 每次请求自动约束 |
