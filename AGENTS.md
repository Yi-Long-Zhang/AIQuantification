# AIQuantification 开发者指南

> 用于 AI 编码助手的项目约定和上下文。

## 技术栈

- Python 3.13+, FastAPI, uvicorn
- 包管理: uv
- 数据: pandas, numpy, yfinance, akshare, pandas-ta
- LLM: OpenAI 兼容 API (DeepSeek / OpenAI / Qwen / Gemini)

## 项目结构

```
main.py                 # FastAPI 入口
config.yaml             # 配置文件（git ignored，含 API Key）
config.yaml.example     # 配置模板
agent/
  config.py             # 配置加载模块（读取 config.yaml）
  core.py               # ReAct Agent 循环
  llm_client.py         # LLM 客户端（多提供商）
  memory.py             # SQLite 记忆
  tools/                # 工具集（@tool 装饰器注册）
    registry.py         # 工具注册中心
  strategies/           # 策略定义
api/routes.py           # API 路由
models/                 # Pydantic 模型
```

## 关键约定

### 工具注册

所有工具使用 `@tool` 装饰器注册在 `agent/tools/registry.py`，自动生成 OpenAI 兼容的 tool definition。

### 配置文件

所有配置位于 `config.yaml`（不提交到 git），参考 `config.yaml.example`：

```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: "sk-xxx"
```

### 启动

```bash
uvicorn main:app --reload --port 8000
```

### 运行 Lint/Typecheck

```bash
python -m py_compile agent/config.py
python -m py_compile agent/core.py
```

### 测试

无测试框架配置，后续可添加 pytest。
