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

### 3.4 DRY 原则（禁止复制粘贴）

- 相同逻辑出现 ≥2 次必须提取为共享函数/基类方法
- 子类之间重复的方法必须提升到父类
- 策略逻辑不允许多处独立实现，必须引用单一来源

### 3.5 类型注解

- 强制使用 PEP 604 现代语法：`str | None`，禁止 `Optional[str]`
- 所有公开函数必须有参数和返回值类型注解
- dict/list 等泛型容器标注具体类型参数（如 `dict[str, float]`）

### 3.6 错误处理

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

### 5.1 分支策略

- `main`：稳定分支，只通过 PR/Merge 进入，禁止直接提交
- 功能开发使用 `feature/<描述>` 分支（如 `feature/phase3-frontend`）
- 修复使用 `fix/<描述>` 分支
- 开发完成后合并到 `main`，**保留分支，不删除**

### 5.2 提交格式

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
- 数据: pandas, numpy, yfinance, akshare
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

## 十一、前端规范

### 11.1 技术栈

- Vue 3 + TypeScript + Vite（`web/` 目录独立管理）
- 状态管理：Pinia
- UI 组件库：Element Plus / Naive UI
- 图表：TradingView lightweight-charts
- HTTP 客户端：Axios（统一拦截器处理错误）

### 11.2 代码规范

- 所有 `.vue` 组件使用 `<script setup lang="ts">`
- `.ts` 文件必须有类型标注，禁止 `any`（除非有充分理由）
- API 层（`web/src/api/`）只封装请求，不包含业务逻辑
- 前端必须有测试：推荐 vitest，覆盖核心组件和 API 层

### 11.3 禁止

- ❌ 在 Python 路由中内嵌 HTML/CSS/JS（由 Vue 前端处理）
- ❌ 前后端 API 契约不一致（前端拦截器字段后端不验证）

## 十二、测试要求

- 新增功能必须包含测试（`tests/` 目录）
- 每个 API 路由端点至少有一个集成测试
- 核心模块（agent/, tools/）覆盖率 ≥ 80%
- 工具函数覆盖率 ≥ 90%
- Bug 修复必须包含回归测试

> 完整开发宪法见 `docs/development-constitution.md`（9 章 356 行，含测试规范、文档规范、宪法修正流程）。
