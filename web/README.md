# AIQuantification Web Frontend

Vue 3 + TypeScript + Vite 前端项目

## 安装和启动

```bash
npm install
npm run dev       # 开发 http://localhost:5173
npm run build     # 构建生产版本
npm test          # vitest 运行测试
npm run test:watch  # vitest 监听模式
```

## 页面 (7 个)

| 路由 | 页面 | 功能 |
|------|------|------|
| `/chat` | ChatView | AI 对话（SSE 流式响应） |
| `/dashboard` | DashboardView | 4市场实时行情仪表盘 |
| `/backtest` | BacktestView | 策略回测配置+结果 |
| `/strategies` | StrategiesView | 18策略 + 13技能浏览 |
| `/agents` | AgentMonitorView | 8 Agent 监控+消息日志 |
| `/broker` | BrokerView | 券商连接+账户+持仓 |
| `/` | → `/chat` | 默认跳转 |

## 技术栈

- Vue 3 + TypeScript + Vite
- Element Plus（UI 组件库）
- Pinia（状态管理）
- Vue Router（路由）
- Axios（HTTP 客户端，统一拦截器）
- UnoCSS（原子化 CSS）
- Marked（Markdown 渲染）
- Vitest（测试框架）

## 项目结构

```
web/src/
├── api/              # Axios API 封装 (index/agent/market/backtest/broker/skills)
├── views/            # 7 个页面组件
├── components/       # 5 个通用组件 (ChatMessage/StrategyCard/MarketCard/BacktestResult)
├── stores/           # Pinia (chat)
├── router/           # Vue Router
├── types/            # TypeScript 类型
├── utils/            # format / sse 工具
├── App.vue           # 根组件（侧边栏导航 + 设置对话框）
└── main.ts           # 入口
```

## 测试

```bash
npm test   # 31 个 vitest 测试
```
覆盖：API 层、工具函数（format/sse）、ChatMessage 组件。
