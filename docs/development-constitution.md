# AI 开发宪法

> 指导 AI 编码助手在 AIQuantification 项目中进行开发的根本准则。
> 本文档是开发过程的最高行为规范，所有 AI 生成的代码必须遵守。

---

## 第一条：总纲

**1.1** 本宪法定义 AI 编码助手在 AIQuantification 项目中编写、修改、审查代码时必须遵守的规则。

**1.2** AI 的首要目标：生成**正确、可维护、符合架构**的代码。

**1.3** AI 编码助手必须阅读并理解以下文件后再开始编码：

| 文件 | 获取信息 |
|------|---------|
| `docs/architecture.md` | 系统架构、分层模型、数据流 |
| `docs/agent-design.md` | Agent 核心机制、工具注册、LLM 抽象 |
| `docs/api-design.md` | API 路由设计、请求/响应格式 |
| `AGENT_CONSTITUTION.md` | 交易 Agent 的行为规则（非本文档） |

**1.4** 本文档存储在 `docs/development-constitution.md`，是唯一权威版本。

---

## 第二条：架构遵守

**2.1 分层原则**

代码必须严格遵守架构定义的分层，禁止跨层调用：

- ✅ `api/routes.py` → 调用 `agent/core.py`
- ✅ `agent/core.py` → 调用 `agent/llm_client.py`、`agent/tools/`
- ✅ `agent/tools/` → 可调用外部库（yfinance、pandas 等）
- ❌ `api/routes.py` → 直接调用外部库（绕过 Agent 层）
- ❌ `agent/tools/` → 直接调用 `api/` 层

**2.2 模块边界**

| 目录 | 允许依赖 | 禁止依赖 |
|------|---------|---------|
| `agent/` | `models/`, 外部库 | `api/` |
| `api/` | `agent/`, `models/` | 工具具体实现 |
| `models/` | 仅 Pydantic | 业务逻辑 |

**2.3 工具注册**

所有 Agent 工具必须使用 `@tool` 装饰器注册，禁止手动拼装 tool definition：

```python
# ✅ 正确
@tool(name="my_tool", description="...", parameters={...})
async def my_tool(param: str):
    ...

# ❌ 错误
custom_tool_def = {"type": "function", "function": {"name": "my_tool", ...}}
```

---

## 第三条：代码风格

**3.1 Python 规范**

- 遵循 PEP 8。
- 类型注解是必需的，禁止使用无类型标注的函数。
- 禁止使用 `Any` 作为函数参数或返回值类型（除非绝对必要）。
- 禁止使用 `from module import *`。

```python
# ✅ 正确
async def get_klines(symbol: str, market: str = "us_stock") -> list[dict]:
    ...

# ❌ 错误
async def get_klines(symbol, market = "us_stock"):
    ...
```

**3.2 import 顺序**

1. 标准库（`json`, `os`, `abc` 等）
2. 第三方库（`pandas`, `httpx`, `fastapi` 等）
3. 项目内部模块（`models`, `agent` 等）

每组之间空一行。

```python
# ✅ 正确
import json
from typing import Any

import pandas as pd
from fastapi import APIRouter

from models.schemas import TradeSignal
```

**3.3 命名约定**

| 类型 | 约定 | 示例 |
|------|------|------|
| 类名 | PascalCase | `QuantAgent`, `LLMClient` |
| 函数/方法 | snake_case | `get_klines`, `execute_tool` |
| 变量 | snake_case | `session_id`, `tool_result` |
| 常量 | UPPER_SNAKE | `MAX_ITERATIONS`, `SYSTEM_PROMPT` |
| 私有 | 前缀 `_` | `_run_loop`, `_TOOL_REGISTRY` |
| 文件 | snake_case | `market_data.py`, `llm_client.py` |

**3.4 错误处理**

- 所有可能失败的外部调用必须使用 try/except。
- 禁止捕获 `BaseException`（键盘中断、系统退出等）。
- 自定义异常使用有意义的错误消息。

```python
# ✅ 正确
try:
    result = await external_api_call()
except ValueError as e:
    return {"error": str(e)}
except Exception as e:
    return {"error": f"Unexpected error: {e}"}

# ❌ 错误
try:
    result = await external_api_call()
except:
    pass
```

**3.5 禁止的写法**

- ❌ 硬编码 API Key 或密码
- ❌ `print()` 调试输出（使用日志）
- ❌ 未捕获的 `await` 异常
- ❌ 超过 200 行的函数
- ❌ 超过 500 行的文件
- ❌ 魔法数字（使用命名常量）
- ❌ 遗留的 TODO/FIXME 不解释上下文

---

## 第四条：文档与注释

**4.1 函数文档**

每个工具函数必须有 docstring：

```python
@tool(name="calculate_indicators", description="计算技术指标", parameters={...})
async def calculate_indicators(
    symbol: str,
    market: str = "us_stock",
    indicators: list[str] | None = None,
) -> dict:
    """
    计算股票的技术指标。

    Args:
        symbol: 股票代码，如 AAPL
        market: 市场: us_stock, cn_stock, hk_stock, crypto
        indicators: 要计算的指标列表，默认计算 sma, ema, rsi, macd, bb

    Returns:
        dict: 包含各指标最新值的字典

    Raises:
        ValueError: 当 symbol 为空时
    """
    ...
```

**4.2 类文档**

核心类必须有 docstring，说明职责、使用方式、关键字段。

```python
class QuantAgent:
    """
    AI 量化交易 Agent。
    
    使用 ReAct 模式驱动 LLM 进行多轮推理和工具调用。
    支持多 LLM 提供商，配置通过 config.yaml 管理。
    
    Usage:
        agent = QuantAgent()
        response = await agent.chat("分析 AAPL", "session-id")
    """
```

**4.3 文档更新**

修改代码时必须同步更新相关文档：

| 修改范围 | 必须更新的文档 |
|---------|--------------|
| 新增工具 | `docs/api-design.md` 工具列表 |
| 新增/修改 API | `docs/api-design.md` 对应端点 |
| 架构变化 | `docs/architecture.md` |
| Agent 机制变化 | `docs/agent-design.md` |
| 新增策略 | `docs/tutorial-backtest.md` |
| 新增宪法条款 | `AGENT_CONSTITUTION.md` |

---

## 第五条：测试

**5.1 测试覆盖要求**

- 所有工具函数必须有单元测试。
- 所有 API 路由必须有集成测试。
- 核心 Agent 循环必须有端到端测试。

**5.2 测试位置**

```
tests/
├── test_tools/
│   ├── test_market_data.py
│   ├── test_technical.py
│   └── test_backtest.py
├── test_api/
│   └── test_routes.py
└── test_agent/
    └── test_core.py
```

**5.3 测试规范**

- 使用 `pytest` 框架。
- 异步测试使用 `pytest-asyncio`。
- 禁止依赖外部网络（mock 外部 API）。
- 测试函数命名：`test_<被测试函数>_<场景>`。

```python
# ✅ 正确
async def test_get_stock_quote_success():
    data = await get_stock_quote("AAPL")
    assert data["symbol"] == "AAPL"
    assert data["price"] is not None
```

---

## 第六条：安全

**6.1 API Key 与凭据**

- ❌ 禁止在任何代码中硬编码 API Key。
- ❌ 禁止将 `config.yaml` 提交到 Git。
- ✅ 所有凭据通过 `agent/config.py` 的 `Settings` 对象读取。
- ✅ 日志输出时必须脱敏 API Key（仅保留前 4 位）。

**6.2 用户数据**

- ❌ 禁止将用户查询内容写入日志明文（可写摘要）。
- ❌ 禁止将用户持仓数据返回给 LLM 以外的系统。
- ✅ SQLite 数据库文件默认存储在 `~/.aiquantification/`。

**6.3 代码安全**

- ✅ 所有用户输入在进入 LLM 前做长度限制（最大 4096 字符）。
- ✅ 所有工具结果返回前做大小限制（最大 50000 字符）。
- ❌ 禁止使用 `eval()`、`exec()`、`__import__()`。

---

## 第七条：Git 提交规范

**7.1 提交信息格式**

```
<type>: <简短描述>

<详细描述（可选）>

<关联 issue（可选）>
```

**7.2 type 类型**

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `docs` | 文档变更 |
| `refactor` | 重构（无功能变化） |
| `test` | 测试相关 |
| `style` | 代码格式（无逻辑变化） |
| `chore` | 杂项（依赖、构建等） |

**7.3 提交准则**

- 每个提交只做一件事（单一职责）。
- 描述使用中文或英文均可，保持一致性。
- 禁止提交包含调试代码、注释掉的代码段。
- 提交前必须验证代码语法正确（`python -m py_compile`）。
- **每次修改后自动提交**：AI 完成实现后必须立即执行 `git add` + `git commit`，不得等待用户要求。
- 禁止提交 `__pycache__/`、`config.yaml`、`.aiquantification/` 到版本控制。

---

## 第八条：AI 行为准则

**8.1 理解先行**

在修改任何代码之前，AI 必须：
1. 读取相关文件的全部内容（禁止仅基于文件名或摘要就修改）
2. 理解该文件在整个架构中的位置和职责
3. 理解该文件的代码风格和约定

**8.2 最小改动原则**

- 只修改实现目标所需的最少代码。
- 禁止"顺便"重构无关代码。
- 禁止添加未被请求的"额外功能"。

**8.3 一致性原则**

新代码必须与现有代码保持风格一致：
- 使用相同的库版本和 API 风格
- 使用相同的错误处理模式
- 使用相同的日志格式

**8.4 透明原则**

- AI 必须解释每个修改的理由。
- 当有多个设计方案时，AI 必须列出选项并推荐一个。
- 当 AI 不确定时，必须向用户提问，禁止猜测。

**8.5 拒绝不安全请求**

当用户要求 AI 执行以下操作时，AI 必须拒绝并解释原因：
1. 在代码中写入 API Key 或密码
2. 绕过安全检查或风控规则
3. 引入已知有漏洞的依赖版本
4. 删除测试或文档以"节省时间"

---

## 第九条：宪法修正

**9.1** 本文档可通过 Pull Request 修改，需至少一人审查。

**9.2** 每次修正须记录：

```
### YYYY-MM-DD

修改内容：[简述本次修改]
修改原因：[为什么修改]
修改人：[AI 或开发者]
```

**9.3** 本文档以 `docs/development-constitution.md` 为唯一权威版本。
