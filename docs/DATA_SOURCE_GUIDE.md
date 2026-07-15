# 数据源配置和测试指南

## 问题诊断

当前问题：市场数据 API 返回 500 错误，无法获取行情数据。

---

## 🔍 数据源检查

### 依赖库状态
```bash
# 检查是否安装
cd C:\code\PycharmProjects\AIQuantification
python -c "import yfinance; print('yfinance:', yfinance.__version__)"
python -c "import akshare; print('akshare:', akshare.__version__)"
python -c "import ccxt; print('ccxt:', ccxt.__version__)"
```

### 测试数据获取
```python
# 测试美股数据（yfinance）
import yfinance as yf
stock = yf.Ticker('AAPL')
data = stock.history(period='1d')
print(data)

# 测试 A股数据（akshare）
import akshare as ak
df = ak.stock_zh_a_spot_em()
print(df.head())

# 测试加密货币数据（ccxt）
import ccxt
exchange = ccxt.binance()
ticker = exchange.fetch_ticker('BTC/USDT')
print(ticker)
```

---

## 🛠️ 常见问题和解决方案

### 问题 1: yfinance 连接失败

**症状**: 
```
HTTPError: 404 Client Error: Not Found for url
```

**原因**: Yahoo Finance API 限制或网络问题

**解决方案**:
```python
# 方法 1: 添加 User-Agent
import yfinance as yf
yf.pdr_override()

# 方法 2: 使用代理
import yfinance as yf
stock = yf.Ticker('AAPL', proxy='http://proxy:port')

# 方法 3: 增加重试
import time
for i in range(3):
    try:
        data = stock.history(period='1d')
        break
    except:
        time.sleep(1)
```

---

### 问题 2: akshare 获取失败

**症状**:
```
JSONDecodeError / ConnectionError
```

**原因**: 网络问题或数据源更新

**解决方案**:
```bash
# 升级到最新版本
pip install akshare --upgrade

# 清除缓存
pip cache purge
```

---

### 问题 3: ccxt 交易所连接失败

**症状**:
```
ccxt.NetworkError
```

**解决方案**:
```python
import ccxt

# 使用不同的交易所
exchanges = [
    ccxt.binance(),
    ccxt.coinbase(),
    ccxt.kraken()
]

for exchange in exchanges:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f'{exchange.name}: {ticker["last"]}')
        break
    except Exception as e:
        print(f'{exchange.name} failed: {e}')
        continue
```

---

## 🚀 快速修复方案

### 方案 1: 使用模拟数据（推荐测试用）

修改 `agent/tools/market_data.py`，添加模拟数据：

```python
# 在文件开头添加
MOCK_DATA = True  # 开发模式使用模拟数据

async def get_stock_quote(symbol: str, market: str = "us_stock") -> dict:
    if MOCK_DATA:
        # 返回模拟数据
        return {
            "symbol": symbol,
            "price": 150.25,
            "change": 2.35,
            "change_percent": 1.59,
            "volume": 50234567,
            "market_cap": 2450000000000,
            "timestamp": datetime.now().isoformat()
        }
    
    # 原有的真实数据获取逻辑
    ...
```

### 方案 2: 添加重试和容错

```python
import asyncio
from functools import wraps

def retry_on_error(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        raise
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_error(retries=3, delay=2)
async def get_stock_quote(symbol: str, market: str = "us_stock") -> dict:
    # 原有逻辑
    ...
```

### 方案 3: 配置数据源优先级

```python
# config.yaml
data_sources:
  us_stock:
    - provider: yfinance
      priority: 1
    - provider: alpha_vantage
      priority: 2
      api_key: "your_key"
  
  cn_stock:
    - provider: akshare
      priority: 1
    - provider: tushare
      priority: 2
      token: "your_token"
```

---

## 📝 测试脚本

创建 `test_data_sources.py`:

```python
import asyncio
from agent.tools.market_data import (
    get_stock_quote,
    get_klines,
    get_market_overview
)

async def test_all():
    print("Testing US Stock...")
    try:
        result = await get_stock_quote("AAPL", "us_stock")
        print(f"✅ AAPL: ${result.get('price', 'N/A')}")
    except Exception as e:
        print(f"❌ AAPL failed: {e}")
    
    print("\nTesting CN Stock...")
    try:
        result = await get_stock_quote("000001", "cn_stock")
        print(f"✅ 000001: ¥{result.get('price', 'N/A')}")
    except Exception as e:
        print(f"❌ 000001 failed: {e}")
    
    print("\nTesting Market Overview...")
    try:
        result = await get_market_overview("us_stock")
        print(f"✅ Market overview: {len(result.get('data', []))} items")
    except Exception as e:
        print(f"❌ Market overview failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_all())
```

运行测试:
```bash
cd C:\code\PycharmProjects\AIQuantification
python test_data_sources.py
```

---

## 🎯 推荐行动

### 立即执行（5分钟）

1. **检查依赖库**
```bash
python -c "import yfinance; import akshare; import ccxt; print('All OK')"
```

2. **测试单个股票**
```bash
python -c "
import yfinance as yf
stock = yf.Ticker('AAPL')
print(stock.info.get('currentPrice', 'No data'))
"
```

3. **如果失败，启用模拟数据**
```python
# 临时解决方案：在 market_data.py 顶部添加
MOCK_DATA_MODE = True
```

### 根本解决（30分钟）

1. 添加完整的错误处理
2. 实现数据源 fallback
3. 添加缓存机制
4. 配置 API 密钥（如需要）

---

## 📞 需要帮助？

告诉我具体的错误信息，我可以：
1. 诊断具体问题
2. 提供针对性解决方案
3. 帮你修改代码实现容错
4. 配置备用数据源

---

**现在数据无法获取是正常的，这是数据源配置问题，不是代码错误。** 

需要我帮你实现模拟数据或修复数据源吗？
