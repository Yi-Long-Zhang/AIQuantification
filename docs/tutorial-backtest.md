# 策略回测教程

> 编写交易策略、运行回测、解读结果。

---

## 一、内置策略

系统内置 4 种策略：

| 策略名称 | 策略逻辑 | 适用场景 |
|---------|---------|---------|
| `sma_cross` | SMA20 上穿 SMA50 买入，下穿卖出 | 趋势跟踪 |
| `macd` | MACD 线上穿信号线买入，下穿卖出 | 趋势跟踪 |
| `rsi` | RSI < 30 买入，RSI > 70 卖出 | 反转交易 |
| `bollinger` | 价格触及下轨买入，触及上轨卖出 | 均值回归 |

---

## 二、运行回测

### 2.1 通过 API

```bash
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "sma_cross",
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "initial_capital": 100000.0
  }'
```

### 2.2 响应解读

```json
[
  {
    "strategy_name": "sma_cross",
    "symbol": "AAPL",
    "total_return": 15.23,
    "annualized_return": 15.23,
    "sharpe_ratio": 1.32,
    "max_drawdown": -8.5,
    "total_trades": 6,
    "win_rate": 0.67
  }
]
```

| 指标 | 含义 | 优秀 | 良好 | 一般 |
|------|------|------|------|------|
| `total_return` | 总收益率 (%) | >50% | >20% | >0% |
| `sharpe_ratio` | 夏普比率（风险调整收益） | >2.0 | >1.0 | >0.5 |
| `max_drawdown` | 最大回撤 (%) | <-10% | <-20% | <-30% |
| `win_rate` | 胜率 | >60% | >50% | >40% |

### 2.3 通过 Agent

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "对 AAPL 分别测试 SMA 金叉、MACD、RSI 三种策略，比较它们的表现"
  }'
```

Agent 会自动调用 `compare_strategies` 工具，运行多次回测并对比结果。

---

## 三、策略比较

使用 `compare_strategies` 工具比较多个策略在同一标的上的表现：

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "比较 AAPL 上所有内置策略的表现，给出最优策略建议"
  }'
```

Agent 会调用 `compare_strategies` 工具，输出类似：

```
## 策略对比结果 - AAPL

| 策略 | 收益率 | 夏普比率 | 最大回撤 | 胜率 | 交易次数 |
|------|--------|---------|---------|------|---------|
| sma_cross | +18.5% | 1.45 | -10.2% | 66.7% | 6 |
| macd | +22.3% | 1.62 | -8.5% | 75.0% | 8 |
| rsi | +8.2% | 0.85 | -12.1% | 55.6% | 18 |
| bollinger | +3.1% | 0.32 | -15.4% | 50.0% | 12 |

🏆 **建议**: MACD 策略在 AAPL 上表现最优（夏普 1.62，胜率 75%）
```

---

## 四、策略实现

内置策略定义在 `agent/strategies/registry.py`。

### 4.1 策略基类

所有策略继承 `Strategy` 基类：

```python
from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    name: str = "base"
    description: str = "Base strategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """生成交易信号
        返回: pd.Series, 值 1=买入, -1=卖出, 0=持有
        """
```

### 4.2 示例：SMA 金叉策略

```python
class SMACrossStrategy(Strategy):
    name = "sma_cross"
    description = "SMA 均线交叉策略"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        sma20 = df["Close"].rolling(20).mean()
        sma50 = df["Close"].rolling(50).mean()
        signals = pd.Series(0, index=df.index)
        signals[sma20 > sma50] = 1   # 金叉 → 买入
        signals[sma20 < sma50] = -1  # 死叉 → 卖出
        return signals
```

### 4.3 示例：RSI 策略

```python
class RSIStrategy(Strategy):
    name = "rsi"
    description = "RSI 超买超卖反转策略"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        signals = pd.Series(0, index=df.index)
        signals[rsi < 30] = 1   # 超卖 → 买入
        signals[rsi > 70] = -1  # 超买 → 卖出
        return signals
```

---

## 五、添加自定义策略

### 5.1 步骤

1. 在 `agent/strategies/` 下新建文件（或直接在 `registry.py` 中添加）
2. 继承 `Strategy` 基类
3. 实现 `generate_signals()` 方法
4. 注册到 `_STRATEGIES` 字典

### 5.2 示例：自定义均线组合策略

```python
# agent/strategies/registry.py

class EMAStrategy(Strategy):
    name = "ema_cross"
    description = "EMA 指数均线交叉策略"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema12 = df["Close"].ewm(span=12).mean()
        ema26 = df["Close"].ewm(span=26).mean()
        signals = pd.Series(0, index=df.index)
        signals[ema12 > ema26] = 1
        signals[ema12 < ema26] = -1
        return signals

# 注册到策略字典
_STRATEGIES = {
    "sma_cross": SMACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
    "ema_cross": EMAStrategy,  # ← 新增
}
```

### 5.3 验证

```bash
# 重启服务后检查
curl http://localhost:8000/strategies
# → {"strategies": [
#   {"name": "sma_cross", ...},
#   {"name": "macd", ...},
#   {"name": "rsi", ...},
#   {"name": "bollinger", ...},
#   {"name": "ema_cross", ...}  # 新的
# ]}

# 测试回测
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ema_cross",
    "symbols": ["AAPL"],
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  }'
```

---

## 六、注意事项

### 6.1 数据要求

- 至少需要 60 根 K 线数据（确保技术指标有足够的预热期）
- 周期建议 ≥ 1 年（覆盖不同市场环境）
- A 股使用前复权数据（`adjust="qfq"`）

### 6.2 策略设计要求

- 信号值范围：`-1`（卖出） / `0`（持有） / `1`（买入）
- 避免使用未来数据（look-ahead bias）
- 回测手续费和滑点未内置，后续版本会添加

### 6.3 局限

- 当前仅支持多头（做多），不支持做空
- 等权重仓位，不支持动态仓位调整
- 未考虑交易成本和滑点
