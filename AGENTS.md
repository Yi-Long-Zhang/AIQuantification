# AI 开发宪法

> AI 编码助手在 AIQuantification 项目中的行为准则与开发规范。
> 本文档在会话启动时自动加载，AI 必须遵守以下所有规则。

---

## 一、必读文件

开始编码前必须阅读：

| 文件 | 获取信息 |
|------|---------|
| `docs/architecture.md` | 系统架构、分层模型、数据流 |
| `docs/agent-design.md` | Agent 核心机制、工具注册、LLM 抽象 |
| `docs/api-design.md` | API 路由设计、请求/响应格式 |
| `docs/development-constitution.md` | 完整开发宪法（本文档是精要版） |
| `AGENTS.md` | **本文档** — 自动加载，包含核心约束 |

---

## 二、架构遵守

### 2.1 分层原则

禁止跨层调用：

- ✅ `api/routes.py` → `agent/core.py`
- ✅ `agent/core.py` → `agent/llm_client.py`, `agent/tools/`
- ✅ `agent/tools/` → 外部库
- ❌ `api/routes.py` → 直接调用外部库
- ❌ `agent/tools/` → `api/`

模块依赖方向：`api/` → `agent/` → `models/`, 外部库

### 2.2 工具注册

所有 Agent 工具必须使用 `@tool` 装饰器：

```python
@tool(name="my_tool", description="...", parameters={...})
async def my_tool(param: str) -> dict:
    ...
```

---

## 三、代码规范

### 3.1 Python

- 类型注解是**强制**的，禁止无类型标注的函数
- 遵循 PEP 8
- import 顺序：标准库 → 第三方 → 项目内部

### 3.2 命名

| 类型 | 约定 | 示例 |
|------|------|------|
| 类 | PascalCase | `QuantAgent` |
| 函数/变量 | snake_case | `get_klines` |
| 常量 | UPPER_SNAKE | `MAX_ITERATIONS` |
| 文件 | snake_case | `market_data.py` |

### 3.3 禁止

- ❌ 硬编码 API Key 或密码
- ❌ `print()`（用日志）
- ❌ `eval()`, `exec()`, `__import__()`
- ❌ 超过 200 行的函数
- ❌ 超过 500 行的文件
- ❌ 魔法数字（用命名常量）
- ❌ `from module import *`
- ❌ 捕获 `BaseException`

### 3.4 错误处理

```python
try:
    result = await external_api_call()
except ValueError as e:
    return {"error": str(e)}
except Exception as e:
    return {"error": f"Unexpected error: {e}"}
```

---

## 四、安全

- API Key 通过 `config.yaml` + `agent/config.py` 读取，禁止写死在代码里
- `config.yaml` 不提交 Git（已在 `.gitignore`）
- 日志输出时脱敏 API Key（仅保留前 4 位）
- 用户数据不得明文写日志
- 工具结果限制 50000 字符

---

## 五、Git 提交

```
<type>: <简短描述>

type: feat / fix / docs / refactor / test / style / chore
```

- 每个提交只做一件事
- 提交前验证：`python -m py_compile`
- **每次修改后自动提交**：AI 完成实现后必须立即执行 `git add` + `git commit`，不得等待用户要求
- 禁止提交 `__pycache__/`、`config.yaml`、`.aiquantification/`

---

## 六、AI 行为准则

### 6.1 理解先行

修改文件前必须读取该文件的**全部内容**，不得仅凭文件名修改。

### 6.2 最小改动

只修改实现目标所需的最少代码。禁止"顺便"重构或添加未请求的功能。

### 6.3 一致性

新代码必须与现有代码风格一致（库版本、错误处理模式、日志格式）。

### 6.4 透明

- 解释每个修改的理由
- 多方案时列出选项并推荐一个
- 不确定时必须提问，禁止猜测

### 6.5 拒绝不安全请求

当被要求执行以下操作时必须拒绝：
1. 在代码中写入 API Key
2. 绕过风控或安全检查
3. 引入有漏洞的依赖
4. 删除测试或文档

---

## 七、项目结构

```
main.py                 # FastAPI 入口
config.yaml             # 配置（git ignored）
config.yaml.example     # 配置模板
AGENTS.md               # ← 本文档（opencode 自动加载）
agent/
  config.py             # 配置加载
  core.py               # ReAct Agent 循环
  llm_client.py         # LLM 客户端（DeepSeek/OpenAI/Qwen/Gemini）
  memory.py             # SQLite 记忆
  tools/                # 工具集（@tool 装饰器注册）
    registry.py         # 工具注册中心
  strategies/           # 策略定义
api/routes.py           # FastAPI 路由
models/schemas.py       # Pydantic 模型
docs/                   # 设计文档与教程
```

## 八、技术栈

- Python 3.13+, FastAPI, uvicorn
- 包管理: uv
- 数据: pandas, numpy, yfinance, akshare, pandas-ta
- LLM: OpenAI 兼容 API（DeepSeek/OpenAI/Qwen/Gemini）
- 配置: YAML（`agent/config.py` → `Settings` 对象）

## 九、关键 API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/agent/chat` | Agent 聊天（同步） |
| POST | `/agent/chat/stream` | Agent 聊天（流式 SSE） |
| GET | `/agent/tools` | 工具列表 |
| POST | `/backtest` | 运行回测 |
| POST | `/market/quote` | 实时行情 |
| POST | `/market/klines` | K 线数据 |

## 十、启动

```bash
uvicorn main:app --reload --port 8000
```

> 完整开发宪法见 `docs/development-constitution.md`（9 章 356 行，含测试规范、文档规范、宪法修正流程）。
