# 数据源指南

## 已集成数据源

| 数据源 | 市场 | 库 | 用途 |
|--------|------|-----|------|
| Yahoo Finance | 美股 | yfinance | K线、报价、基本面 |
| AKShare | A股/港股 | akshare | 行情、资金流、宏观 |
| CCXT | 加密货币 | ccxt | 100+交易所K线、ticker |
| CoinGecko | 加密货币 | pycoingecko | 市场概览、排名 |
| Alpaca Markets | 美股 | httpx (REST) | 券商账户、持仓、订单 |
| IBKR | 全市场 | ib_insync | TWS/IB Gateway 只读连接 |

## Fallback 机制

每个市场都有自动降级：

```
美股: yfinance → akshare → mock 数据
A股: akshare → yfinance → mock 数据
港股: akshare → yfinance → mock 数据
加密货币: ccxt → CoinGecko → yfinance → mock 数据
```

网络不可用时工具返回 mock 数据而非报错，Agent 可继续分析。

## 数据源框架

`agent/data/` 提供插件化数据源抽象层：

```python
from agent.data import BaseDataSource, register_source

class MySource(BaseDataSource):
    name = "polygon"
    priority = 1

    async def connect(self) -> bool: ...
    async def get_klines(self, symbol, interval, period): ...
    async def get_quote(self, symbol): ...

register_source(MySource())
```

## 添加新数据源

1. 继承 `agent.data.BaseDataSource`
2. 实现 `connect` / `get_klines` / `get_quote`
3. 调用 `register_source()` 注册
4. 在 `config.yaml` 的 `brokers` 段配置 API Key
