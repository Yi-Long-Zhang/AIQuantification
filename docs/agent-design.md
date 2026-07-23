# Agent 设计

## 单 Agent：ReAct 循环

`agent/core.py` → `QuantAgent.chat()`

```
用户输入 → LLM 推理 → 需要工具？→ 执行工具 → 结果返回 LLM → 重复
                   ↓
                   否 → 返回最终答案
```

最大迭代 10 次。每轮 LLM 可调用多个工具，结果注入上下文后继续推理。

## 多 Agent：Coordinator 调度

`agent/multi_agent/coordinator.py` → `CoordinatorAgent.run_trading_cycle()`

```
Research Phase (串行)        Strategy Phase (并行)     Risk Phase (并行)
DataMiner → candidates ──→  Backtester            →  RiskManager
    ↓                        PortfolioOptimizer        ↓
MarketAnalyst                                        (approved /
TechnicalAnalyst                                      rejected)
FundamentalAnalyst                                          ↓
NewsAnalyst                                          Final Decision
     ↕                                                    ↕
  研究结果                                            LLM 合成最终决策
```

### 8 个 Agent

| Agent | 类型 | 职责 |
|-------|------|------|
| DataMiner | Research | 扫描候选股票，多因子评分排序 |
| MarketAnalyst | Research | 市场趋势、板块轮动、宏观风险 |
| TechnicalAnalyst | Research | K线技术指标、支撑阻力、买卖信号 |
| FundamentalAnalyst | Research | 估值、成长性、财务健康度 |
| NewsAnalyst | Research | 新闻情绪评分、事件影响分析 |
| Backtester | Strategy | 回测验证信号显著性 |
| PortfolioOptimizer | Strategy | 资金分配、仓位计算 |
| RiskManager | Risk | 宪法合规、止损检查、组合风险 |

## LLM 客户端

4 家 LLM 全部走 OpenAI 兼容 API：

| Provider | 默认模型 |
|----------|---------|
| deepseek | deepseek-chat |
| openai | gpt-4o |
| qwen | qwen-plus |
| gemini | gemini-2.0-flash |

自动 fallback：按 provider_info 列表逐一尝试，失败后切换。

## 工具系统

### 注册

所有工具在 `agent/tools/` 和 `agent/broker/tools.py` 下定义，用 `@tool` 装饰器：

```python
@tool(name="my_tool", description="...", parameters={...})
async def my_tool(param: str) -> dict: ...
```

### 工具列表（40+ 个）

| 分类 | 工具 | 用途 |
|------|------|------|
| 市场数据 | `get_stock_quote`, `get_klines`, `get_cn_klines`, `get_market_overview`, `get_global_macro`, `get_sector_rotation` | 多市场行情 |
| 港股 | `get_hk_klines`, `get_hk_realtime`, `get_hk_index`, `get_hk_flow`, `get_hk_fund_flow`, `get_hk_valuation` | 港股数据 |
| 加密货币 | `get_crypto_klines`, `get_crypto_realtime`, `get_crypto_orderbook`, `get_crypto_overview`, `get_crypto_fear_greed`, `get_crypto_top_coins`, `get_crypto_funding_rate`, `get_crypto_open_interest`, `calculate_crypto_indicators` | 区块链数据 |
| 技术分析 | `calculate_indicators`, `calculate_factor` | 指标计算 |
| Alpha | `compute_alpha_factors`, `evaluate_alpha_factors`, `list_alpha_factors` | 251 因子 |
| 回测 | `run_backtest`, `compare_strategies`, `monte_carlo_test`, `walk_forward_test`, `trade_attribution` | 策略评估 |
| 风险 | `calculate_position_size`, `assess_portfolio_risk` | 风控 |
| 新闻 | `get_stock_news`, `analyze_sentiment` | 市场情绪 |
| 宪法 | `check_constitution` | 合规检查 |
| 券商 | `import_trades_csv`, `analyze_trade_performance` | 交易分析 |

## 技能系统（13 个技能）

`agent/skills/skills/` 使用 Markdown + YAML frontmatter 定义可复用分析工作流。每个技能指定：名称、描述、工具列表、工具参数、标签、执行逻辑 prompt。

## 因子库（251 个）

`agent/alpha/` — Alpha158(150) + Alpha101(101)。评估指标：IC、IR、换手率、存活率。

## 记忆系统

SQLite + FTS5 全文搜索，支持跨会话记忆、交易记录、知识库。

## 策略系统（18 个）

所有策略继承 `Strategy` ABC，分类：趋势(7)、反转(3)、均值回归(4)、事件驱动(2)、组合(1)。每个策略定义：名称、类型、标签、适用市场、参数、风险等级。
