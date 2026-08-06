<template>
  <div class="paper-trading">
    <div class="page-header">
      <h1>模拟交易</h1>
      <p class="subtitle">PaperBroker 虚拟账户实时监控</p>
    </div>

    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">总权益</div>
          <div class="stat-value" :class="summary.equity >= summary.initial_capital ? 'profit' : 'loss'">
            ${{ summary.equity.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">总收益率</div>
          <div class="stat-value" :class="summary.total_return_pct >= 0 ? 'profit' : 'loss'">
            {{ summary.total_return_pct >= 0 ? '+' : '' }}{{ summary.total_return_pct.toFixed(2) }}%
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">现金余额</div>
          <div class="stat-value">${{ summary.cash.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">交易次数</div>
          <div class="stat-value">{{ summary.total_trades }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 权益曲线 -->
    <el-card shadow="hover" class="chart-card">
      <template #header><span>权益曲线</span></template>
      <div ref="equityChartRef" class="equity-chart" />
      <div v-if="!equityData.length" class="chart-empty">暂无权益数据</div>
    </el-card>

    <!-- 持仓 + 交易记录 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>当前持仓 ({{ summary.positions.length }})</span></template>
          <el-table :data="summary.positions" size="small" stripe v-if="summary.positions.length" empty-text="暂无持仓">
            <el-table-column prop="symbol" label="代码" width="80" />
            <el-table-column prop="qty" label="数量" width="70" />
            <el-table-column prop="avg_entry" label="均价" width="90">
              <template #default="{ row }">${{ row.avg_entry.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="current_price" label="现价" width="90">
              <template #default="{ row }">${{ row.current_price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值" width="100">
              <template #default="{ row }">${{ row.market_value.toLocaleString() }}</template>
            </el-table-column>
            <el-table-column prop="unrealized_pnl" label="浮动盈亏" width="110">
              <template #default="{ row }">
                <span :class="row.unrealized_pnl >= 0 ? 'profit' : 'loss'">
                  ${{ row.unrealized_pnl.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>最近交易</span></template>
          <el-table :data="recentTrades" size="small" stripe v-if="recentTrades.length" empty-text="暂无交易记录">
            <el-table-column prop="symbol" label="代码" width="70" />
            <el-table-column prop="side" label="方向" width="60">
              <template #default="{ row }">
                <el-tag :type="row.side === 'buy' ? 'success' : 'danger'" size="small">
                  {{ row.side === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="qty" label="数量" width="60" />
            <el-table-column prop="price" label="价格" width="80">
              <template #default="{ row }">${{ row.price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="realized_pl" label="盈亏" width="100">
              <template #default="{ row }">
                <span v-if="row.realized_pl !== null" :class="row.realized_pl >= 0 ? 'profit' : 'loss'">
                  ${{ row.realized_pl.toFixed(2) }}
                </span>
                <span v-else class="text-muted">进行中</span>
              </template>
            </el-table-column>
            <el-table-column prop="timestamp" label="时间" width="160">
              <template #default="{ row }">{{ formatTs(row.timestamp) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 执行记录 -->
    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="exec-header">
          <span>执行记录</span>
          <el-button size="small" @click="runDryRun" :loading="dryRunning">演练最近信号</el-button>
        </div>
      </template>
      <el-table :data="executionItems" size="small" stripe v-if="executionItems.length" empty-text="暂无执行记录（点击演练最近信号或等待调度器产出）">
        <el-table-column prop="symbol" label="代码" width="90" />
        <el-table-column prop="action" label="动作" width="80">
          <template #default="{ row }">
            <el-tag :type="row.action === 'BUY' ? 'success' : row.action === 'SELL' ? 'danger' : 'info'" size="small">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'filled' ? 'success' : row.status === 'planned' ? 'warning' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="90">
          <template #default="{ row }">{{ row.confidence?.toFixed(2) ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="90">
          <template #default="{ row }">{{ row.price != null ? '$' + row.price.toFixed(2) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="qty" label="数量" width="80">
          <template #default="{ row }">{{ row.qty ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="说明" min-width="200">
          <template #default="{ row }">{{ row.reason || row.order_id || row.order_status || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { brokerAPI, type PaperSummary, type PaperTrade, type DryRunItem } from '@/api/broker'
import { createChart, ColorType, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts'

// ── State ──
const summary = ref<PaperSummary>({
  initial_capital: 100000, cash: 100000, equity: 100000,
  unrealized_pnl: 0, total_realized_pnl: 0, total_return_pct: 0,
  positions: [], open_orders: 0, total_trades: 0,
})
const recentTrades = ref<PaperTrade[]>([])
const equityData = ref<{ time: string; equity: number }[]>([])
const equityChartRef = ref<HTMLElement | null>(null)
const executionItems = ref<DryRunItem[]>([])
const dryRunning = ref(false)
let chart: IChartApi | null = null
let equityLine: ISeriesApi<'Line'> | null = null
let pollTimer: number | null = null

// ── Data loading ──
const loadData = async () => {
  try {
    const [s, t, e] = await Promise.all([
      brokerAPI.getPaperSummary(),
      brokerAPI.getPaperTrades(20),
      brokerAPI.getPaperEquity(300),
    ])
    summary.value = s
    recentTrades.value = t.trades || []
    equityData.value = e.history || []
    updateChart()
  } catch (err) {
    console.error('Failed to load paper data:', err)
  }
}

// ── Execution dry-run ──
const runDryRun = async () => {
  dryRunning.value = true
  try {
    // Preview from current positions: evaluate exit signals on existing positions
    const decisions = summary.value.positions
      .filter(p => p.qty > 0)
      .slice(0, 10)
      .map(p => ({ symbol: p.symbol, action: p.unrealized_pnl >= 0 ? 'SELL' : 'HOLD', confidence: 0.5 }))
    const resp = await brokerAPI.dryRun('us_stock', decisions)
    executionItems.value = resp.items
    if (resp.orders_planned + resp.orders_filled === 0) {
      ElMessage.info('演练完成：无满足条件的信号')
    }
  } catch (err) {
    console.error('Dry-run failed:', err)
    ElMessage.error('演练失败，请查看控制台')
  } finally {
    dryRunning.value = false
  }
}

// ── Chart ──
const updateChart = () => {
  if (!equityChartRef.value) return
  if (!chart) {
    chart = createChart(equityChartRef.value, {
      layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#8b949e' },
      grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
      width: equityChartRef.value.clientWidth,
      height: 280,
      crosshair: { mode: 0 },
    })
    equityLine = chart.addLineSeries({ color: '#58a6ff', lineWidth: 2 })
  }
  const data: LineData[] = equityData.value.map((d, i) => ({
    time: i as LineData['time'],
    value: d.equity,
  }))
  equityLine?.setData(data)
  chart?.timeScale().fitContent()
}

const formatTs = (ts: string) => {
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}

// ── Lifecycle ──
onMounted(() => {
  loadData()
  pollTimer = window.setInterval(loadData, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  chart?.remove()
})
</script>

<style scoped>
.paper-trading { padding: 24px; min-height: 100vh; background: #0d1117; }
.page-header { margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 22px; color: #c9d1d9; }
.subtitle { margin: 4px 0 0; font-size: 13px; color: #8b949e; }
.stat-row { margin-bottom: 16px; }
.stat-card .stat-label { font-size: 12px; color: #8b949e; margin-bottom: 4px; }
.stat-value { font-size: 22px; font-weight: 600; color: #c9d1d9; }
.profit { color: #3fb950 !important; }
.loss { color: #f85149 !important; }
.text-muted { color: #8b949e; }
.chart-card { margin-bottom: 16px; }
.equity-chart { height: 280px; }
.chart-empty { text-align: center; color: #8b949e; padding: 60px 0; }
.chart-card :deep(.el-card__body) { padding: 0; }
.exec-header { display: flex; justify-content: space-between; align-items: center; }
</style>
