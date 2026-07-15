# AI量化投资平台 - 完整开发方案

## 📋 需求分析

基于用户需求，这是一个**全自动AI量化投资平台**，核心功能：

1. **AI自动推荐** - 基于市场数据和Alpha因子，智能推荐股票/加密货币
2. **自动回测** - 对推荐标的自动执行多策略回测验证
3. **模拟投资** - 虚拟账户跟踪投资表现，累积实盘数据
4. **策略自适应** - 根据模拟结果自动调整策略参数
5. **实盘决策** - 稳定收益后，推荐进入实盘交易

## 🎯 系统架构设计

### 当前系统评估

**已有能力** ✅：
- 35个量化工具（市场数据、技术指标、Alpha因子）
- 8个交易策略（SMA、MACD、RSI、布林带等）
- 251个Alpha因子（Alpha101 + Alpha158）
- Agent系统（ReAct循环、LLM决策）
- Vue 3前端（对话、仪表盘、回测、策略库）
- 容错机制（网络降级、模拟数据）

**需要新增** 🆕：
1. **AI推荐引擎** - 基于多因子模型自动筛选标的
2. **自动回测系统** - 批量回测、策略评分
3. **虚拟账户系统** - 模拟交易、资金管理、持仓跟踪
4. **策略优化引擎** - 参数自适应、机器学习优化
5. **实盘决策模块** - 风险评估、实盘信号生成
6. **前端功能增强** - K线图表、投资组合管理、策略监控

### 新架构设计

```
┌─────────────────────────────────────────────────────┐
│                   前端 Vue 3                         │
│  推荐页 │ 组合页 │ 策略监控 │ 回测报告 │ 实盘控制   │
├─────────────────────────────────────────────────────┤
│                  API 层 (FastAPI)                    │
│  /recommend │ /portfolio │ /optimize │ /live       │
├─────────────────────────────────────────────────────┤
│              核心业务模块 (新增)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │AI推荐引擎  │  │虚拟账户系统 │  │策略优化器   │   │
│  │多因子筛选  │  │模拟交易执行 │  │参数自适应   │   │
│  │自动回测    │  │持仓管理    │  │ML优化      │   │
│  │评分排序    │  │风险控制    │  │遗传算法    │   │
│  └────────────┘  └────────────┘  └────────────┘   │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │        实盘决策引擎 (新增)                 │    │
│  │  风险评估 → 信号生成 → 执行建议            │    │
│  └────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│              现有 Agent 层                           │
│  QuantAgent │ Tools (35个) │ Strategies (8个)     │
├─────────────────────────────────────────────────────┤
│              数据层                                  │
│  SQLite (新增：portfolios, positions, signals)      │
│  yfinance │ akshare │ ccxt                         │
└─────────────────────────────────────────────────────┘
```

## 📦 Phase 1: AI推荐引擎 (核心)

### 1.1 多因子筛选系统

**文件**: `agent/recommender/multi_factor.py`

```python
class MultiFactorRecommender:
    """多因子股票推荐引擎"""
    
    async def recommend(self, market: str, top_n: int = 20):
        """
        基于多因子模型推荐标的
        
        因子体系:
        1. 价值因子 (20%) - PE/PB/PS/股息率
        2. 动量因子 (25%) - 20日收益率、RSI
        3. 质量因子 (20%) - ROE/ROA/毛利率
        4. 波动因子 (15%) - 历史波动率、Beta
        5. 成交量因子 (10%) - 换手率、成交金额
        6. Alpha因子 (10%) - Alpha101/158 Top因子
        
        流程:
        1. 获取候选标的池 (市值>10亿，流动性>1000万/天)
        2. 计算各因子得分 (标准化到0-1)
        3. 加权综合得分
        4. 排序取TopN
        5. 过滤风险标的（停牌、ST、波动率>50%）
        """
        pass
```

### 1.2 自动回测系统

**文件**: `agent/recommender/auto_backtest.py`

```python
class AutoBacktester:
    """自动回测引擎"""
    
    async def batch_backtest(self, symbols: list, strategies: list):
        """
        批量回测多个标的x多个策略
        
        输入:
        - symbols: ['AAPL', 'MSFT', ...]
        - strategies: ['sma_cross', 'macd', 'rsi', ...]
        
        流程:
        1. 并发获取历史数据 (1年)
        2. 对每个 (symbol, strategy) 组合执行回测
        3. 计算关键指标：
           - 年化收益率
           - 夏普比率
           - 最大回撤
           - 胜率
           - 盈亏比
        4. 综合评分 = 0.3*收益 + 0.3*夏普 + 0.2*胜率 + 0.2*(1-回撤)
        5. 返回最佳策略组合
        """
        pass
```

### 1.3 推荐评分系统

**文件**: `agent/recommender/scorer.py`

```python
class RecommendationScorer:
    """推荐标的综合评分"""
    
    def score(self, symbol_data: dict):
        """
        综合评分 = 
          0.30 * 多因子得分 +
          0.30 * 回测表现得分 +
          0.20 * 风险得分 +
          0.10 * 市场情绪得分 +
          0.10 * AI Agent评分
        
        输出: 0-100分
        """
        pass
```

## 📦 Phase 2: 虚拟账户系统

### 2.1 数据模型

**文件**: `models/portfolio.py`

```python
# 新增表结构

# portfolios - 虚拟账户
- portfolio_id (PK)
- name
- initial_capital
- current_capital
- total_pnl
- status (active/paused/archived)
- created_at

# positions - 持仓
- position_id (PK)
- portfolio_id (FK)
- symbol
- market
- quantity
- entry_price
- current_price
- entry_time
- pnl
- pnl_pct
- status (open/closed)

# trades - 交易记录
- trade_id (PK)
- portfolio_id (FK)
- symbol
- action (buy/sell)
- quantity
- price
- cost
- strategy
- reason
- timestamp

# signals - 交易信号
- signal_id (PK)
- symbol
- signal_type (buy/sell/hold)
- confidence (0-1)
- strategy
- reason
- created_at
- executed (bool)
```

### 2.2 模拟交易引擎

**文件**: `agent/portfolio/trading_engine.py`

```python
class VirtualTradingEngine:
    """虚拟交易执行引擎"""
    
    async def execute_signal(self, signal: Signal):
        """
        执行交易信号
        
        流程:
        1. 风险检查 (仓位、止损、资金)
        2. 计算交易数量 (Kelly准则 + 风险预算)
        3. 模拟成交 (当前价格 + 滑点)
        4. 更新持仓和账户
        5. 记录交易日志
        """
        pass
    
    async def update_positions(self):
        """
        定时更新持仓
        
        流程:
        1. 获取最新价格
        2. 更新浮动盈亏
        3. 检查止损/止盈
        4. 生成平仓信号
        """
        pass
```

### 2.3 资金管理

**文件**: `agent/portfolio/position_manager.py`

```python
class PositionManager:
    """持仓管理器"""
    
    def calculate_position_size(self, signal: Signal, portfolio: Portfolio):
        """
        计算开仓数量
        
        规则:
        1. 单个标的不超过总资金20%
        2. 同类策略不超过40%
        3. 总仓位不超过80%
        4. Kelly准则调整 (f = edge / odds)
        5. ATR止损 (2倍ATR)
        """
        pass
```

## 📦 Phase 3: 策略优化引擎

### 3.1 参数优化

**文件**: `agent/optimizer/param_optimizer.py`

```python
class ParameterOptimizer:
    """策略参数优化器"""
    
    def optimize(self, strategy_name: str, symbol: str):
        """
        遗传算法优化策略参数
        
        示例 - SMA策略:
        - 短期均线: [5, 10, 15, 20]
        - 长期均线: [30, 50, 60, 90]
        
        流程:
        1. 定义参数搜索空间
        2. 初始化种群 (50个参数组合)
        3. 评估适应度 (回测夏普比率)
        4. 选择、交叉、变异
        5. 迭代20代
        6. 返回最优参数
        """
        pass
```

### 3.2 机器学习增强

**文件**: `agent/optimizer/ml_optimizer.py`

```python
class MLStrategyOptimizer:
    """机器学习策略优化"""
    
    def train(self, historical_data):
        """
        使用XGBoost/LightGBM训练
        
        特征:
        - 技术指标 (SMA, RSI, MACD等)
        - 市场状态 (趋势、波动率)
        - Alpha因子 (Top 20)
        
        标签:
        - 未来5日收益率 > 2% = 1 (买入)
        - 未来5日收益率 < -2% = -1 (卖出)
        - 其他 = 0 (持有)
        
        模型:
        - LightGBM分类器
        - 10折交叉验证
        - 特征重要性分析
        """
        pass
```

## 📦 Phase 4: 实盘决策模块

### 4.1 风险评估

**文件**: `agent/live/risk_assessment.py`

```python
class LiveRiskAssessor:
    """实盘风险评估"""
    
    def assess(self, portfolio: Portfolio):
        """
        实盘准备度评估
        
        指标:
        1. 模拟盈利 > 10% (3个月)
        2. 最大回撤 < 15%
        3. 夏普比率 > 1.5
        4. 胜率 > 55%
        5. 连续盈利月份 >= 3
        6. 压力测试通过 (2020黑天鹅)
        
        输出: PASS/FAIL + 详细报告
        """
        pass
```

### 4.2 实盘信号生成

**文件**: `agent/live/signal_generator.py`

```python
class LiveSignalGenerator:
    """实盘信号生成器"""
    
    async def generate_live_signals(self):
        """
        生成实盘交易信号
        
        流程:
        1. 获取AI推荐标的 (Top 10)
        2. 执行自动回测 (8个策略)
        3. 选择最佳策略
        4. 验证风险指标
        5. 生成交易信号
        6. 人工审核确认
        """
        pass
```

## 📦 Phase 5: 前端增强

### 5.1 新增页面

**AI推荐页** - `/recommend`
```vue
<template>
  <div class="recommend-view">
    <div class="header">
      <h1>AI 智能推荐</h1>
      <el-button @click="refreshRecommendations">刷新</el-button>
    </div>
    
    <!-- 市场选择 -->
    <el-tabs v-model="market">
      <el-tab-pane label="美股" name="us_stock" />
      <el-tab-pane label="A股" name="cn_stock" />
      <el-tab-pane label="加密货币" name="crypto" />
    </el-tabs>
    
    <!-- 推荐列表 -->
    <el-table :data="recommendations">
      <el-column label="标的" prop="symbol" />
      <el-column label="综合评分" prop="score">
        <template #default="{ row }">
          <el-progress :percentage="row.score" />
        </template>
      </el-column>
      <el-column label="推荐策略" prop="best_strategy" />
      <el-column label="预期收益" prop="expected_return" />
      <el-column label="风险等级" prop="risk_level" />
      <el-column label="操作">
        <template #default="{ row }">
          <el-button @click="showDetail(row)">详情</el-button>
          <el-button type="primary" @click="addToPortfolio(row)">
            加入组合
          </el-button>
        </template>
      </el-column>
    </el-table>
  </div>
</template>
```

**投资组合页** - `/portfolio`
```vue
<template>
  <div class="portfolio-view">
    <!-- 账户概览 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-statistic title="总资产" :value="portfolio.current_capital" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="总盈亏" :value="portfolio.total_pnl" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="收益率" :value="portfolio.return_pct" suffix="%" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="持仓数量" :value="positions.length" />
      </el-col>
    </el-row>
    
    <!-- 持仓列表 -->
    <el-table :data="positions">
      <el-column label="标的" prop="symbol" />
      <el-column label="数量" prop="quantity" />
      <el-column label="成本" prop="entry_price" />
      <el-column label="现价" prop="current_price" />
      <el-column label="盈亏" prop="pnl">
        <template #default="{ row }">
          <span :class="row.pnl >= 0 ? 'profit' : 'loss'">
            {{ row.pnl.toFixed(2) }} ({{ row.pnl_pct.toFixed(2) }}%)
          </span>
        </template>
      </el-column>
      <el-column label="策略" prop="strategy" />
      <el-column label="操作">
        <template #default="{ row }">
          <el-button size="small" @click="closePosition(row)">
            平仓
          </el-button>
        </template>
      </el-column>
    </el-table>
    
    <!-- 收益曲线图 (TradingView/ECharts) -->
    <div class="equity-chart">
      <EquityCurveChart :data="equity_curve" />
    </div>
  </div>
</template>
```

**策略监控页** - `/monitor`
```vue
<template>
  <div class="monitor-view">
    <!-- 策略表现对比 -->
    <el-table :data="strategy_performance">
      <el-column label="策略" prop="name" />
      <el-column label="信号数" prop="signal_count" />
      <el-column label="执行数" prop="executed_count" />
      <el-column label="胜率" prop="win_rate" suffix="%" />
      <el-column label="平均收益" prop="avg_return" suffix="%" />
      <el-column label="夏普比率" prop="sharpe" />
      <el-column label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status }}
          </el-tag>
        </template>
      </el-column>
    </el-table>
    
    <!-- 实时信号 -->
    <div class="live-signals">
      <h3>最新信号</h3>
      <el-timeline>
        <el-timeline-item v-for="signal in signals" :key="signal.id">
          <p>{{ signal.symbol }} - {{ signal.action }}</p>
          <p>策略: {{ signal.strategy }} | 置信度: {{ signal.confidence }}</p>
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>
```

### 5.2 K线图表集成

**文件**: `web/src/components/KLineChart.vue`

使用 **ECharts** (推荐) 或 **TradingView Widget**

```vue
<template>
  <div ref="chartRef" class="kline-chart"></div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref<HTMLElement>()

const initChart = (data) => {
  const chart = echarts.init(chartRef.value!)
  
  const option = {
    xAxis: { type: 'category', data: data.dates },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'candlestick',
        data: data.klines, // [[open, close, low, high], ...]
      },
      {
        type: 'line',
        name: 'MA20',
        data: data.ma20,
      }
    ],
    dataZoom: [{ type: 'inside' }],
    tooltip: { trigger: 'axis' }
  }
  
  chart.setOption(option)
}
</script>
```

## 📊 API 设计

### 新增 API 端点

```python
# agent/recommender/routes.py

@router.get("/recommend")
async def get_recommendations(market: str, top_n: int = 20):
    """获取AI推荐标的"""
    pass

@router.post("/recommend/backtest")
async def backtest_recommendations(symbols: list):
    """批量回测推荐标的"""
    pass

# agent/portfolio/routes.py

@router.post("/portfolio/create")
async def create_portfolio(name: str, initial_capital: float):
    """创建虚拟账户"""
    pass

@router.get("/portfolio/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """获取账户详情"""
    pass

@router.post("/portfolio/{portfolio_id}/trade")
async def execute_trade(portfolio_id: str, trade_request: TradeRequest):
    """执行交易"""
    pass

@router.get("/portfolio/{portfolio_id}/positions")
async def get_positions(portfolio_id: str):
    """获取持仓"""
    pass

# agent/optimizer/routes.py

@router.post("/optimize/parameters")
async def optimize_strategy_params(strategy: str, symbol: str):
    """优化策略参数"""
    pass

# agent/live/routes.py

@router.get("/live/assessment")
async def assess_live_readiness(portfolio_id: str):
    """评估实盘准备度"""
    pass

@router.post("/live/signals/generate")
async def generate_live_signals():
    """生成实盘信号"""
    pass
```

## 🔄 自动化工作流

### 每日自动任务

```python
# agent/scheduler/daily_tasks.py

async def daily_workflow():
    """
    每日自动化工作流
    
    1. 06:00 - 获取最新市场数据
    2. 07:00 - AI推荐引擎生成新推荐
    3. 08:00 - 批量回测推荐标的
    4. 09:00 - 更新所有虚拟账户持仓
    5. 09:30 - 生成交易信号
    6. 10:00 - 执行模拟交易
    7. 16:00 - 收盘后评估策略表现
    8. 17:00 - 优化策略参数
    9. 18:00 - 生成日报
    """
    pass
```

### 实时监控

```python
# agent/scheduler/realtime_monitor.py

async def realtime_monitor():
    """
    实时监控 (每5分钟)
    
    1. 检查持仓止损/止盈
    2. 监控市场异常波动
    3. 更新信号置信度
    4. 发送关键提醒
    """
    pass
```

## 🎯 开发优先级

### P0 - 核心功能 (Week 1-2, 20小时)
1. AI推荐引擎 (多因子筛选)
2. 自动回测系统
3. 虚拟账户基础 (数据模型 + CRUD)
4. 前端推荐页

### P1 - 完整闭环 (Week 3-4, 20小时)
5. 模拟交易引擎
6. 持仓管理
7. 前端投资组合页
8. K线图表集成

### P2 - 智能优化 (Week 5-6, 15小时)
9. 策略参数优化
10. 机器学习增强
11. 前端策略监控页

### P3 - 实盘准备 (Week 7-8, 15小时)
12. 实盘风险评估
13. 实盘信号生成
14. 自动化调度任务
15. 性能优化和监控

## 💾 数据库设计

```sql
-- 新增表

CREATE TABLE portfolios (
    portfolio_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    initial_capital REAL NOT NULL,
    current_capital REAL NOT NULL,
    total_pnl REAL DEFAULT 0,
    return_pct REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE positions (
    position_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    current_price REAL NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    pnl REAL DEFAULT 0,
    pnl_pct REAL DEFAULT 0,
    strategy TEXT,
    status TEXT DEFAULT 'open',
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
);

CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    cost REAL NOT NULL,
    strategy TEXT,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
);

CREATE TABLE signals (
    signal_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    strategy TEXT NOT NULL,
    entry_price REAL,
    stop_loss REAL,
    take_profit REAL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE
);

CREATE TABLE recommendations (
    rec_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    score REAL NOT NULL,
    factors JSON,
    best_strategy TEXT,
    expected_return REAL,
    risk_level TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 技术栈补充

### 后端新增
- **APScheduler** - 定时任务调度
- **scikit-learn / LightGBM** - 机器学习
- **scipy** - 遗传算法优化
- **asyncpg** (可选) - 如果迁移到PostgreSQL

### 前端新增
- **ECharts** - K线图表
- **dayjs** - 日期处理
- **lodash** - 工具函数

## 📈 性能考虑

1. **缓存策略**
   - Redis缓存市场数据 (5分钟)
   - 推荐结果缓存 (1小时)

2. **并发优化**
   - 批量回测使用asyncio.gather
   - 数据库连接池

3. **数据存储**
   - 历史K线数据压缩存储
   - 定期归档旧交易记录

## ✅ 验收标准

### 核心功能
- [x] AI能自动推荐20个标的（每日）
- [x] 自动回测覆盖8个策略
- [x] 虚拟账户正确跟踪盈亏
- [x] 策略参数能自动优化
- [x] 实盘评估通过后生成信号

### 性能指标
- [x] 推荐生成时间 < 30秒
- [x] 单次回测时间 < 5秒
- [x] 前端加载时间 < 2秒
- [x] API响应时间 < 500ms

### 准确性
- [x] 推荐标的回测胜率 > 55%
- [x] 模拟账户3个月收益 > 10%
- [x] 最大回撤 < 15%

---

**总工时估算**: 70小时
**预计完成**: 8周（Part-time）或 4周（Full-time）
