# 市场分析教程

> 使用 AIQuantification 获取市场行情、执行技术分析、生成交易信号。

---

## 一、概述

AIQuantification 的 Agent 会自动使用多个工具综合分析市场，给出结构化的交易建议。

标准分析流程：
1. 获取行情数据（价格、成交量）
2. 计算技术指标（RSI、MACD、均线等）
3. 计算量化因子（动量、波动率）
4. 分析市场情绪
5. 综合多维度信息 → 生成信号
6. 按风控规则计算仓位

---

## 二、基础查询

### 2.1 单只股票分析

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "分析 AAPL 的近期走势和技术指标，给出交易建议"}'
```

Agent 会自动：
1. 获取 AAPL 的 K 线数据
2. 计算 RSI、MACD、SMA/EMA
3. 判断趋势方向
4. 结合多个指标 → 给出 BUY/SELL/HOLD 信号

### 2.2 A 股分析

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析贵州茅台的近期走势",
    "market": "cn_stock"
  }'
```

Agent 会使用 AKShare 获取 A 股数据（复权 K 线）。

### 2.3 加密货币分析

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析比特币的技术面",
    "market": "crypto"
  }'
```

---

## 三、获取原始数据（不经过 Agent）

### 3.1 实时行情

```bash
curl -X POST http://localhost:8000/market/quote \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "market": "us_stock"}'
```

响应示例：

```json
{
  "symbol": "AAPL",
  "price": 198.50,
  "change": 1.23,
  "change_percent": 0.62,
  "volume": 45230000,
  "market_cap": 3100000000000,
  "name": "Apple Inc."
}
```

### 3.2 K 线数据

```bash
# 美股
curl -X POST http://localhost:8000/market/klines \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "market": "us_stock", "interval": "1d", "period": "6mo"}'

# A 股
curl -X POST http://localhost:8000/market/klines \
  -H "Content-Type: application/json" \
  -d '{"symbol": "sh600519", "market": "cn_stock", "interval": "daily", "period": "1y"}'
```

参数说明：

| 参数 | 选项 | 说明 |
|------|------|------|
| `market` | us_stock / cn_stock / hk_stock / crypto | 市场 |
| `interval` | 1d / 1wk / 1mo | K 线周期 |
| `period` | 1mo / 3mo / 6mo / 1y / 2y / 5y / max | 回溯时间 |

### 3.3 市场概况

```bash
# 美股三大指数
curl http://localhost:8000/market/us_stock/overview

# A 股主要指数
curl http://localhost:8000/market/cn_stock/overview
```

---

## 四、技术指标分析

通过 Agent 可以获取完整的技术分析报告。Agent 会计算以下指标：

| 指标 | 用途 | 信号含义 |
|------|------|---------|
| SMA20/50 | 趋势判断 | 20 日线 > 50 日线 = 多头 |
| RSI(14) | 超买超卖 | >70 超买、<30 超卖 |
| MACD | 趋势动能 | 柱状图转正 = 看多 |
| 布林带 | 波动率 | 触及下轨 = 超卖 |
| ATR(14) | 波动率度量 | 值越大波动越大 |
| Stochastic | 动量 | K 线 > D 线 = 多头 |

示例查询：

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "详细分析 AAPL 的 RSI、MACD 和布林带指标"
  }'
```

---

## 五、信号分类

Agent 输出的信号分为五个等级：

| 信号 | 置信度要求 | 行动 |
|------|-----------|------|
| STRONG_BUY | ≥0.7 | 正常开仓，3+ 维度一致看多 |
| BUY | ≥0.5 | 轻仓试探，2 维度看多 |
| HOLD | 任意 | 持仓不动，信号不明确 |
| SELL | ≥0.5 | 减仓，2 维度看空 |
| STRONG_SELL | ≥0.7 | 清仓，3+ 维度一致看空或触发止损 |

### 信号输出格式

Agent 的回答会包含结构化的信号摘要：

```
## 信号汇总

| 指标 | 数值 | 信号 |
|------|------|------|
| RSI(14) | 45.2 | 中性 |
| MACD | 柱状图 +0.15 | 看多 |
| SMA20/50 | 200.5 > 195.3 | 多头排列 |
| 布林带 | 价格在中轨上方 | 中性偏多 |

**综合信号**: BUY (置信度: 0.65)
**止损**: $188.50 (-5.0%)
**仓位建议**: 轻仓 (账户的 15%)
```

---

## 六、情绪分析

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "当前市场情绪如何？"}'
```

Agent 会获取：
- 加密货币恐惧与贪婪指数（Alternative.me）
- 美股 VIX 恐慌指数

---

## 七、完整分析示例

推荐提示词模板：

```
分析 {标的} 的 {市场} 走势，需要包含：
1. 当前价格和近期涨跌幅
2. 主要技术指标（RSI、MACD、均线）
3. 趋势判断
4. 风险提示
5. 明确的交易信号（BUY/SELL/HOLD）和置信度
6. 建议的止损位和仓位比例
```

示例：

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析 MSFT 的走势，需要包含技术指标、趋势判断和明确的交易信号"
  }'
```
