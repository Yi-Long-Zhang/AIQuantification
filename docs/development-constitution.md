# AI 开发宪法

> AI 编码助手在 AIQuantification 项目中的行为准则与开发规范。
> 本文档是完整版，包含测试规范、文档规范、宪法修正流程。

---

## 一、必读文件

开始编码前必须阅读：

| 文件 | 获取信息 |
|------|---------|
| `docs/architecture.md` | 系统架构、分层模型、数据流 |
| `docs/agent-design.md` | Agent 核心机制、工具注册、LLM 抽象 |
| `docs/api-design.md` | API 路由设计、请求/响应格式 |
| `AGENTS.md` | 精要版宪法（自动加载） |

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

## 七、测试规范

### 7.1 测试要求

- 新增功能必须包含测试
- Bug 修复必须包含回归测试
- 测试文件命名：`test_<module>.py`
- 测试目录：`tests/`

### 7.2 测试覆盖率

- 核心模块（agent/, tools/）：≥ 80%
- 工具函数：≥ 90%
- API 路由：≥ 70%

### 7.3 测试类型

| 类型 | 用途 | 工具 |
|------|------|------|
| 单元测试 | 函数级别 | pytest |
| 集成测试 | 模块间交互 | pytest-asyncio |
| 回归测试 | Bug 修复验证 | pytest |

### 7.4 测试示例

```python
# tests/test_registry.py
import pytest
from agent.tools.registry import tool, get_tool_definitions, execute_tool

@tool(name="test_tool", description="Test tool")
async def test_tool(x: int) -> dict:
    return {"result": x * 2}

def test_tool_registration():
    defs = get_tool_definitions()
    assert any(d["function"]["name"] == "test_tool" for d in defs)

@pytest.mark.asyncio
async def test_tool_execution():
    result = await execute_tool("test_tool", x=5)
    assert result == {"result": 10}
```

---

## 八、文档规范

### 8.1 必需文档

| 文件 | 内容 | 更新时机 |
|------|------|---------|
| `README.md` | 项目简介、快速开始 | 新功能发布 |
| `docs/architecture.md` | 系统架构 | 架构变更 |
| `docs/agent-design.md` | Agent 设计 | Agent 变更 |
| `docs/api-design.md` | API 设计 | 路由变更 |
| `AGENTS.md` | AI 行为准则 | 规则变更 |

### 8.2 代码文档

- 公开函数必须有 docstring
- 复杂逻辑必须有注释
- TODO 标记必须包含负责人和日期

### 8.3 变更日志

重大变更必须更新 `CHANGELOG.md`：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增功能描述

### Changed
- 变更功能描述

### Fixed
- 修复问题描述
```

---

## 九、宪法修正流程

### 9.1 修正提案

1. 在 GitHub Issues 中创建"宪法修正"议题
2. 说明修正理由和影响范围
3. 标记为 `constitution` 标签

### 9.2 审核流程

1. 项目维护者审核提案
2. 重大修正需 7 天公示期
3. 收集社区反馈并调整

### 9.3 生效

1. 合并 PR 后立即生效
2. 更新版本号
3. 通知所有协作者

### 9.4 回滚

1. 发现严重问题可紧急回滚
2. 回滚 PR 需至少 2 个维护者批准
3. 回滚后需重新评估修正案

---

## 十、项目结构

```
main.py                 # FastAPI 入口
config.yaml             # 配置（git ignored）
config.yaml.example     # 配置模板
AGENTS.md               # ← 精要版宪法（opencode 自动加载）
AGENT_CONSTITUTION.md   # 智能体宪法（交易行为准则）
agent/
  config.py             # 配置加载
  core.py               # ReAct Agent 循环
  llm_client.py         # LLM 客户端（DeepSeek/OpenAI/Qwen/Gemini）
  memory.py             # SQLite 记忆
  tools/                # 工具集（@tool 装饰器注册）
    registry.py         # 工具注册中心
    market_data.py      # 美股/A股数据工具
    hk_stock.py         # 港股专用工具
    crypto.py           # 加密货币专用工具
    technical.py        # 技术指标计算
    backtest.py         # 策略回测
    risk.py             # 风险管理
    news.py             # 新闻和情绪分析
    constitution.py     # 智能体宪法检查
  strategies/           # 策略定义
    base.py             # 策略基类（ABC）
    registry.py         # 策略注册中心
api/routes.py           # FastAPI 路由
models/schemas.py       # Pydantic 模型
tests/                  # 测试目录
docs/                   # 设计文档与教程
```

---

> 本宪法自发布之日起生效，最终解释权归 AIQuantification 项目所有。
