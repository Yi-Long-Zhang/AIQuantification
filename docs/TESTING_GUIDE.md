# 测试指南

## 运行测试

```bash
# 全部后端测试
cd AIQuantification
.venv/Scripts/python.exe -m pytest tests/ -v

# 单模块测试
.venv/Scripts/python.exe -m pytest tests/test_api.py -v
.venv/Scripts/python.exe -m pytest tests/test_broker.py -v
.venv/Scripts/python.exe -m pytest tests/test_memory.py -v

# 前端测试
cd web
npm test          # vitest run（一次性）
npm run test:watch  # vitest（监听模式）
```

## 测试覆盖

| 模块 | 测试文件 | 测试数 |
|------|---------|--------|
| API 路由 | test_api.py | 35 |
| Agent 核心 | test_core.py, test_base_agent.py | 15+ |
| 多 Agent | test_research_agents.py, test_communication.py, test_strategy_risk_agents.py | 56 |
| 工具 | test_technical.py, test_risk.py, test_backtest.py | 20+ |
| 券商 | test_broker.py, test_broker_registry.py, test_broker_alpaca.py, test_broker_ibkr.py | 46 |
| Shadow Account | test_broker_shadow.py | 14 |
| 记忆 | test_memory.py, test_fts5.py | 13 |
| 技能 | test_skills.py, test_skill_loader.py | 9 |
| 数据+通知 | test_data_notify.py | 8 |
| 策略 | test_deep_coverage.py | 18 |
| 前端 | api/index.test.ts, format.test.ts, sse.test.ts, ChatMessage.test.ts | 31 |
| **合计** | | **280+** |

## 测试类型

| 类型 | 工具 | 用途 |
|------|------|------|
| 单元测试 | pytest | 函数/类级别 |
| 集成测试 | pytest + TestClient | API 端点 |
| 异步测试 | pytest-asyncio | async 函数 |
| HTTP Mock | respx | 券商 API mock |
| 前端测试 | vitest + jsdom | Vue 组件 + TS 工具 |

## 添加新测试

```python
# tests/test_my_module.py
import pytest

def test_my_function():
    result = my_function(1, 2)
    assert result == 3

@pytest.mark.asyncio
async def test_my_async():
    result = await my_async_function()
    assert result is not None
```
