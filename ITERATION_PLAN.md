# AIQuantification 迭代计划

> 基于与 Vibe-Trading（⭐19k）的差距分析，制定的 12 周迭代计划。
> 最后更新：2026-07-13

---

## 决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 前端技术栈 | Vue 3 + TypeScript + Vite | 上手快、中文生态好、TradingView 图表支持好 |
| 港股数据源 | akshare（基础） + 富途 API（盘口/实时） | akshare 免费无限制做基础，富途做 L2 高级数据 |
| 加密货币数据源 | ccxt（主） + CoinGecko（备） | ccxt 支持 100+ 交易所，免费无限制 |
| 市场优先级 | A 股 + 美股 + 港股 + 加密货币 同时扩展 | 覆盖面广 |

---

## 差距一览

| 维度 | 当前 | 目标 | 差距 |
|------|------|------|------|
| 策略 | 4 个 | 87 个技能 + 460 个因子 | -83 技能 |
| 数据源 | 2 个（yfinance + akshare） | 19 个 + 自动 fallback | -17 源 |
| 回测 | 1 个基础引擎 | 7 个引擎 + Monte Carlo | -6 引擎 |
| 工具 | 13 个 | 68 个 + 54 个 MCP | -55 工具 |
| Agent | 单 Agent | 多 Agent 协作（30 预设） | 整个协作系统 |
| 前端 | 原生 HTML/JS | Vue 3 + TypeScript SPA | 需要重写 |
| CLI | 无 | 命令行 + 15 个斜杠命令 | 整个没有 |
| 实盘 | 无 | 10 个券商连接器 | 整个没有 |
| IM 通知 | 无 | 16 个渠道 | 整个没有 |
| MCP | 无 | 54 个 MCP 工具 | 整个没有 |
| Docker | 无 | 完整 Docker 化 | 整个没有 |

---

## 第一阶段：数据和回测基础（第 1-2 周）

**目标**：4 个市场的数据源稳定可用，回测引擎达到专业级

### 1.1 港股数据工具

| 文件 | 新增函数 | 数据源 | 功能 |
|------|---------|--------|------|
| `agent/tools/market_data.py` | `get_hk_klines` | akshare `stock_hk_hist()` | 港股 K 线（日/周/月，前复权/后复权） |
| `agent/tools/market_data.py` | `get_hk_realtime` | akshare `stock_hk_spot_em()` | 港股实时行情（批量） |
| `agent/tools/market_data.py` | `get_hk_index` | akshare / yfinance | 恒生指数、恒生科技指数 |
| `agent/tools/market_data.py` | `get_hk_flow` | akshare `stock_hsgt_hist_em()` | 南向/北向资金流 |

### 1.2 加密货币数据工具

| 文件 | 新增函数 | 数据源 | 功能 |
|------|---------|--------|------|
| `agent/tools/market_data.py` | `get_crypto_klines` | ccxt `fetch_ohlcv()` | 加密货币 K 线（Binance/OKX 等） |
| `agent/tools/market_data.py` | `get_crypto_realtime` | ccxt `fetch_ticker()` | 实时价格、24h 涨跌 |
| `agent/tools/market_data.py` | `get_crypto_orderbook` | ccxt `fetch_order_book()` | 买五卖五盘口 |
| `agent/tools/market_data.py` | `get_crypto_overview` | CoinGecko | 全市场概览（总市值、恐惧贪婪指数） |

### 1.3 数据源 Fallback 机制

```python
async def get_klines_with_fallback(symbol, market, interval, period):
    """带自动切换的数据获取"""
    sources = {
        "us_stock": [_yfinance_klines, _akshare_klines],
        "cn_stock": [_akshare_klines, _yfinance_klines],
        "hk_stock": [_akshare_hk_klines, _yfinance_hk_klines],
        "crypto": [_ccxt_klines, _coingecko_klines],
    }
    for source_fn in sources.get(market, []):
        try:
            result = await source_fn(symbol, interval, period)
            if result and "error" not in result:
                return result
        except Exception:
            continue
    return {"error": f"All data sources failed for {symbol}"}
```

### 1.4 OHLC 数据质量检查

```python
def _validate_ohlcv(df):
    """过滤异常 K 线：最高<最低、价格为负、成交量异常"""
    mask = (
        (df['high'] >= df['low']) &
        (df['open'] > 0) &
        (df['close'] > 0) &
        (df['volume'] >= 0)
    )
    return df[mask]
```

### 1.5 回测引擎升级

| 升级项 | 具体内容 |
|--------|---------|
| Monte Carlo 置换检验 | 随机打乱交易信号 1000 次，计算 p-value |
| Walk-Forward 分析 | 滚动窗口训练+测试，避免过拟合 |
| 滑点建模 | 按成交量百分比计算滑点冲击 |
| 手续费建模 | 区分 Maker/Taker 费率，支持不同市场费率 |
| 逐笔归因 | 每笔交易的盈亏分析、胜率统计 |

### 1.6 策略扩充到 8+

| 新策略 | 逻辑 | 适用市场 |
|--------|------|---------|
| ichimoku | 一目均衡表（转换线/基准线/云带） | 全市场 |
| smc | Smart Money Concepts（订单块/流动性扫荡） | 全市场 |
| multi_factor | 多因子评分（动量+价值+波动率） | 全市场 |
| crypto_funding | 加密货币资金费率套利 | 加密货币 |

**交付**：4 个市场数据可用、自动 fallback、专业回测、8+ 策略

---

## 第二阶段：Agent 智能化（第 3-4 周）

**目标**：工具数从 13 扩到 30+，因子库从 0 到 255+

### 2.1 新增工具（按市场）

| 工具 | 功能 | 数据源 |
|------|------|--------|
| `get_hk_fund_flow` | 港股资金流向（南向/北向） | akshare |
| `get_hk_valuation` | 港股估值数据（PE/PB/市值） | akshare |
| `get_crypto_funding_rate` | 加密货币永续合约资金费率 | ccxt |
| `get_crypto_open_interest` | 加密货币持仓量 | ccxt |
| `get_crypto_fear_greed` | 加密货币恐惧贪婪指数 | alternative.me |
| `get_crypto_top_coins` | 加密货币市值 Top 100 | CoinGecko |
| `get_global_macro` | 全球宏观数据（利率/CPI/GDP） | akshare |
| `get_sector_rotation` | 板块轮动分析 | akshare |
| `calculate_crypto_indicators` | 加密货币专用指标（MVRV/NVT） | CoinMetrics |

### 2.2 技能系统

```
agent/skills/
├── registry.py          # 技能注册中心
├── loader.py            # 自动发现并加载 skills/ 下的技能
└── skills/
    ├── hk_fund_flow.yaml      # 港股资金流分析技能
    ├── crypto_sentiment.yaml   # 加密货币情绪分析技能
    ├── multi_market_compare.yaml # 多市场对比技能
    └── ...
```

### 2.3 因子库（Alpha Zoo）

| 因子库 | 数量 | 来源 |
|--------|------|------|
| Alpha158 | 150 | Microsoft Qlib |
| Alpha101 | 101 | Kakushadze 论文 |
| **合计** | **255** | |

评估指标：IC（信息系数）、IR（信息比率）、换手率、存活率

### 2.4 记忆升级

- SQLite 升级 FTS5 全文搜索
- 跨会话记忆持久化到 `~/.aiquantification/memory/`
- 支持按关键词搜索历史分析

**交付**：35 工具、251 因子、3 技能、FTS5 记忆

---

## 第三阶段：Vue 3 前端（第 5-6 周）

**目标**：现代交易仪表盘，支持实时数据、K 线图表、Agent 对话

### 3.1 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | 上手快 |
| 构建 | Vite | 快速开发体验 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| 图表 | TradingView lightweight-charts | 专业金融图表，轻量 |
| UI 组件库 | Element Plus 或 Naive UI | 中文生态好 |
| SSE 通信 | EventSource API | 实时流式对话 |
| HTTP 客户端 | Axios | 稳定可靠 |
| CSS | Tailwind CSS 或 UnoCSS | 快速样式开发 |

### 3.2 页面规划

| 页面 | 功能 |
|------|------|
| `/chat` | Agent 对话主界面（SSE 流式、工具调用可视化） |
| `/dashboard` | 市场概览仪表盘（多市场实时行情、指数、资金流） |
| `/backtest` | 回测页面（策略选择、参数配置、结果展示、图表） |
| `/strategies` | 策略库浏览（策略详情、历史表现、因子分析） |
| `/alpha` | 因子库（Alpha Zoo 浏览、IC/IR 排名、因子对比） |
| `/settings` | 设置页（LLM 配置、数据源配置、API Key 管理） |

### 3.3 目录结构

```
web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── views/
│   │   ├── ChatView.vue           # Agent 对话
│   │   ├── DashboardView.vue      # 市场仪表盘
│   │   ├── BacktestView.vue       # 回测
│   │   ├── StrategiesView.vue     # 策略库
│   │   ├── AlphaView.vue          # 因子库
│   │   └── SettingsView.vue       # 设置
│   ├── components/
│   │   ├── ChatMessage.vue        # 对话消息气泡
│   │   ├── KlineChart.vue         # K 线图表（TradingView）
│   │   ├── MarketCard.vue         # 行情卡片
│   │   ├── BacktestResult.vue     # 回测结果表格
│   │   └── ToolCallDisplay.vue    # 工具调用过程展示
│   ├── stores/
│   │   ├── chat.ts                # 对话状态
│   │   ├── market.ts              # 行情数据
│   │   └── settings.ts            # 配置管理
│   ├── api/
│   │   └── index.ts               # 后端 API 封装
│   └── router/
│       └── index.ts               # 路由配置
└── public/
    └── favicon.ico
```

### 3.4 后端 API 配合调整

- `api/routes.py` 添加 CORS 支持（前端开发服务器跨域）
- `api/routes.py` 添加静态文件服务（生产环境）
- SSE 端点格式统一（JSON 格式化）

**交付**：Vue 3 交易仪表盘，支持 K 线图表、实时行情、Agent 对话、回测展示

---

## 第四阶段：多 Agent 协作（第 7-8 周）

**目标**：多个 Agent 组成团队分工合作

### 4.1 协作引擎

```python
# agent/swarm/engine.py
class SwarmEngine:
    """DAG 执行引擎"""
    async def execute(self, workflow: Workflow, query: str):
        # 1. 解析 DAG 依赖
        # 2. 并行执行无依赖的 Agent
        # 3. 收集结果，传递给下游 Agent
        # 4. 汇总最终结果
```

### 4.2 预设团队（30 个）

| 团队 | 成员 | 职责 |
|------|------|------|
| 投研委员会 | 宏观分析师 + 行业分析师 + 量化分析师 | 综合投资建议 |
| 技术分析组 | 趋势分析师 + 形态分析师 + 动量分析师 | 技术面多维度分析 |
| 风控委员会 | 风险分析师 + 合规检查员 | 风险评估和合规审查 |
| 加密货币组 | 链上分析师 + 衍生品分析师 + 情绪分析师 | 加密市场专项分析 |

### 4.3 研究工作流

```
假设注册 → 数据收集 → 信号生成 → 回测验证 → 报告生成
```

**交付**：多 Agent DAG 引擎、30 个团队预设、自动化研究闭环

---

## 第五阶段：部署和生态（第 9-10 周）

### 5.1 Docker 化

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --no-dev
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`：后端 + 前端 + SQLite 持久化卷

### 5.2 命令行工具

```
aiq chat          # 启动 Agent 对话
aiq backtest      # 命令行回测
aiq skills        # 查看已加载技能
aiq sessions      # 查看历史会话
aiq serve         # 启动 Web 服务
```

### 5.3 MCP 集成

- MCP Server：暴露工具给 Claude/Cursor 调用
- MCP Client：调用外部 MCP 服务器

### 5.4 Telegram 机器人

```
/quote AAPL       # 查询报价
/backtest SMA 0700.HK  # 港股回测
/alert BTC > 100000    # 价格提醒
/portfolio             # 持仓概览
```

**交付**：Docker 一键部署、CLI 工具、MCP 互通、Telegram 推送

---

## 第六阶段：高级功能和打磨（第 11-12 周）

| 功能 | 内容 |
|------|------|
| 富途 API 集成 | Level 2 盘口数据、实时逐笔成交 |
| 券商连接 v1 | IBKR（盈透）只读 + Alpaca 模拟交易 |
| Shadow Account | 导入券商交易记录，分析交易行为 |
| 安全加固 | CSRF 防护、代码沙箱、密钥脱敏 |
| CI/CD | GitHub Actions 自动测试 |
| 文档完善 | API 文档、部署指南、用户手册 |

**交付**：富途盘口、券商连接、交易分析、企业级安全

---

## 文件改动预览

```
AIQuantification/
├── main.py                          # 修改：添加 CORS、静态文件服务
├── agent/
│   ├── core.py                      # 修改：支持多 Agent
│   ├── tools/
│   │   ├── market_data.py           # 大改：港股+加密+fallback
│   │   ├── backtest.py              # 大改：Monte Carlo/Walk-Forward
│   │   ├── crypto.py                # 新增：加密货币专用工具
│   │   ├── hk_stock.py              # 新增：港股专用工具
│   │   └── constitution.py          # 修改：适配多市场
│   ├── skills/                      # 新增：技能系统
│   │   ├── registry.py
│   │   ├── loader.py
│   │   └── skills/
│   ├── swarm/                       # 新增：多 Agent 协作
│   │   ├── engine.py
│   │   ├── presets.py
│   │   └── workers.py
│   └── alpha/                       # 新增：因子库
│       ├── alpha158.py
│       ├── alpha101.py
│       └── evaluator.py
├── web/                             # 新增：Vue 3 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/
│   │   ├── api/
│   │   └── router/
│   └── ...
├── cli/                             # 新增：命令行工具
│   └── main.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── docs/                            # 更新文档
```

---

## 依赖变化

```toml
# pyproject.toml 新增
[project]
dependencies = [
    # 现有
    "fastapi", "uvicorn", "openai", "pandas", "numpy",
    "yfinance", "akshare", "pyyaml", "aiosqlite",
    # 第一阶段新增
    "ccxt>=4.0",                    # 加密货币数据
    "pycoingecko>=3.0",             # CoinGecko 备用
    # 第三阶段新增
    # (前端在 web/ 目录单独管理)
    # 第五阶段新增
    # (CLI 和 Docker 独立管理)
]
```

---

## 进度追踪

| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|---------|---------|------|
| 第一阶段：数据和回测基础 | ✅ 完成 | 2026-07-13 | 2026-07-13 | 23 工具/7 策略/4 市场数据 |
| 第二阶段：Agent 智能化 | ✅ 完成 | 2026-07-13 | 2026-07-15 | 35 工具/8 策略/251 因子/3 技能/FTS5/105 测试 |
| 第三阶段：Vue 3 前端 | ⬜ 待开始 | | | |
| 第四阶段：多 Agent 协作 | ⬜ 待开始 | | | |
| 第五阶段：部署和生态 | ⬜ 待开始 | | | |
| 第六阶段：高级功能和打磨 | ⬜ 待开始 | | | |
