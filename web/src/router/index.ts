import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat'
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: 'AI 对话' }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: '市场仪表盘' }
    },
    {
      path: '/backtest',
      name: 'Backtest',
      component: () => import('@/views/BacktestView.vue'),
      meta: { title: '策略回测' }
    },
    {
      path: '/strategies',
      name: 'Strategies',
      component: () => import('@/views/StrategiesView.vue'),
      meta: { title: '策略库' }
    },
    {
      path: '/agents',
      name: 'AgentMonitor',
      component: () => import('@/views/AgentMonitorView.vue'),
      meta: { title: 'Agent 监控' }
    }
  ]
})

// 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = `${to.meta.title} - AIQuantification`
  }
  next()
})

export default router
