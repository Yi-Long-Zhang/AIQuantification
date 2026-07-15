# AIQuantification Web Frontend

Vue 3 + TypeScript + Vite 前端项目

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run dev
```

访问 http://localhost:5173

## 构建生产版本

```bash
npm run build
```

## 项目结构

```
web/
├── src/
│   ├── api/          # API 接口封装
│   ├── views/        # 页面组件
│   ├── components/   # 通用组件
│   ├── stores/       # Pinia 状态管理
│   ├── router/       # 路由配置
│   ├── types/        # TypeScript 类型定义
│   ├── utils/        # 工具函数
│   ├── App.vue       # 根组件
│   └── main.ts       # 入口文件
├── public/           # 静态资源
├── index.html        # HTML 模板
├── package.json      # 项目配置
├── vite.config.ts    # Vite 配置
└── tsconfig.json     # TypeScript 配置
```

## 功能特性

- ✅ AI 对话（支持 SSE 流式响应）
- ✅ 市场仪表盘（4个市场实时行情）
- ✅ 策略回测（可视化回测结果）
- ✅ 策略库浏览
- ✅ Dark 主题
- ✅ 响应式设计
- ✅ API Key 配置

## 技术栈

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- UnoCSS
- Marked (Markdown 渲染)
