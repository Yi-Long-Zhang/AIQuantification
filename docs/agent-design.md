# Agent 设计

## ReAct 循环

Agent 使用 ReAct（Reasoning + Acting）模式，循环执行：

```
用户输入 → LLM 推理 → 需要工具？→ 是 → 执行工具 → 结果返回 LLM → 重复
                   ↓
                   否 → 返回最终答案
```

**最大迭代**：10 次（防止无限循环）

核心代码：`agent/core.py` → `QuantAgent.chat()`

## System Prompt

Agent 的 system prompt 由三部分拼接：

1. **基础角色**：你是一个专业的量化交易分析师...
2. **可用工具说明**：列出所有工具名称和用途
3. **记忆注入**：最近 10 条历史对话

## LLM 客户端

`agent/llm_client.py` 支持 4 家 LLM，全部走 OpenAI 兼容 API：

| Provider | 默认模型 | 配置字段 |
|----------|---------|---------|
| deepseek | deepseek-chat | `LLM_API_KEY` |
| openai | gpt-4o | `LLM_API_KEY` + `LLM_BASE_URL` |
| qwen | qwen-plus | `LLM_API_KEY` |
| gemini | gemini-2.0-flash | `LLM_API_KEY` |

**Fallback 机制**：DeepSeek → OpenAI → Qwen → Gemini

```python
# 调用方式
from agent.llm_client import LLMClient
client = LLMClient(provider="deepseek", api_key="sk-xxx")
response = await client.chat(messages=[{"role": "user", "content": "分析 AAPL"}])
```

## 工具系统

### 注册

所有工具在 `agent/tools/` 下定义，用 `@tool` 装饰器注册：

```python
from agent.tools.registry import tool

@tool(
    name="get_stock_quote",
    description="获取股票实时报价",
    parameters={"symbol": {"description": "股票代码"}, "market": {"description": "市场: us_stock/cn_stock"}}
)
async def get_stock_quote(symbol: str, market: str = "us_stock") -> dict:
    ...
```

### 注册中心

`agent/tools/registry.py` 维护全局字典 `_TOOL_REGISTRY`：

```python
_TOOL_REGISTRY = {
    "get_stock_quote": {"func": <function>, "definition": <tool_def>},
    ...
}
```

### 导入触发

`agent/tools/__init__.py` 导入所有工具模块 → 触发 `@tool` 装饰器执行 → 注册到字典。

**关键**：必须在 `__init__.py` 中 import，否则工具不会被注册。

### 执行

Agent 调用工具时：

```python
# core.py 中
result = await execute_tool("get_stock_quote", symbol="AAPL", market="us_stock")
```

### 工具列表（共 30 个）

| 文件 | 工具 | 用途 |
|------|------|------|
| market_data.py | `get_stock_quote` | 实时报价（yfinance） |
| market_data.py | `get_klines` | K 线数据（自动切换 US/CN/HK/Crypto） |
| market_data.py | `get_cn_klines` | A 股 K 线（akshare） |
| market_data.py | `get_market_overview` | 市场总览 |
| market_data.py | `get_global_macro` | 全球宏观数据（GDP/CPI/PMI/利率等） |
| market_data.py | `get_sector_rotation` | 板块轮动分析 |
| hk_stock.py | `get_hk_klines` | 港股 K 线（AKShare） |
| hk_stock.py | `get_hk_realtime` | 港股实时行情 |
| hk_stock.py | `get_hk_index` | 港股指数（恒指/恒生科技） |
| hk_stock.py | `get_hk_flow` | 南向/北向资金流 |
| hk_stock.py | `get_hk_fund_flow` | 港股资金流向（机构/散户） |
| hk_stock.py | `get_hk_valuation` | 港股估值（PE/PB/PS） |
| crypto.py | `get_crypto_klines` | 加密货币 K 线（CCXT → yfinance → CoinGecko） |
| crypto.py | `get_crypto_realtime` | 加密货币实时行情 |
| crypto.py | `get_crypto_orderbook` | 买五卖五盘口 |
| crypto.py | `get_crypto_overview` | 加密货币全市场概览 |
| crypto.py | `get_crypto_fear_greed` | 恐惧贪婪指数 |
| crypto.py | `get_crypto_top_coins` | 市值 Top N 排名 |
| crypto.py | `get_crypto_funding_rate` | 永续合约资金费率 |
| crypto.py | `get_crypto_open_interest` | 合约持仓量 |
| crypto.py | `calculate_crypto_indicators` | 链上指标（MVRV/NVT/NUPL） |
| technical.py | `calculate_indicators` | 技术指标（SMA/EMA/RSI/MACD/BB/ATR/Stoch/ADX） |
| technical.py | `calculate_factor` | 量化因子（动量/波动率/量比/价格/SMA比） |
| backtest.py | `run_backtest` | 回测策略（支持滑点/手续费） |
| backtest.py | `compare_strategies` | 策略对比 |
| backtest.py | `monte_carlo_test` | Monte Carlo 置换检验 |
| backtest.py | `walk_forward_test` | Walk-Forward 滚动窗口回测 |
| risk.py | `calculate_position_size` | 仓位计算（Kelly + 风险预算） |
| risk.py | `assess_portfolio_risk` | 组合风险（相关性/波动率） |
| news.py | `get_stock_news` | 股票新闻 |
| news.py | `analyze_sentiment` | 情绪分析（Fear & Greed/VIX） |
| constitution.py | `check_constitution` | 合规检查 |

## 技能系统

`agent/skills/` 使用 YAML 定义可复用分析工作流：

```
agent/skills/
├── registry.py          # 技能注册中心
├── loader.py            # YAML 自动发现加载
└── skills/
    ├── hk_fund_flow.yaml      # 港股资金流分析技能
    ├── crypto_sentiment.yaml  # 加密货币情绪分析技能
    └── multi_market_compare.yaml # 多市场对比技能
```

## 因子库（Alpha Zoo）

`agent/alpha/` 提供 251+ 量化因子：

| 因子库 | 数量 | 来源 |
|--------|------|------|
| Alpha158 | 150 | Microsoft Qlib |
| Alpha101 | 101 | Kakushadze 论文 |
| **合计** | **251** | |

评估指标：IC（信息系数）、IR（信息比率）、换手率、存活率、Sharpe、最大回撤

## 记忆系统

`agent/memory.py` 使用 SQLite + FTS5 全文搜索：

- **sessions** 表：会话元数据
- **messages** 表：对话历史
- **messages_fts**：消息全文搜索索引
- **trades** 表：交易记录
- **knowledge** 表：知识库
- **knowledge_fts**：知识全文搜索索引

每次对话自动存储，下次打开同一 session 可恢复上下文。支持全文搜索历史分析。

## 策略系统

`agent/strategies/registry.py` 注册 8 个内置策略：

| 策略 | 逻辑 |
|------|------|
| sma_cross | SMA 5/20 金叉死叉 |
| macd | MACD 信号线交叉 |
| rsi | RSI 超买超卖 |
| bollinger | 布林带突破 |
| ichimoku | 一目均衡表（转换线/基准线/云带） |
| smc | Smart Money Concepts（订单块/流动性扫荡） |
| multi_factor | 多因子评分（动量+波动率+成交量） |
| crypto_funding | 加密货币资金费率套利 |

所有策略继承自 `Strategy` ABC（`agent/strategies/base.py`），必须实现 `generate_signals(df)` 方法。
