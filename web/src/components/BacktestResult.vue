<template>
  <div class="backtest-result">
    <el-table
      :data="results"
      style="width: 100%"
      :row-class-name="tableRowClassName"
      stripe
    >
      <el-table-column prop="symbol" label="股票" width="100" fixed />

      <el-table-column label="总收益率" width="120" sortable>
        <template #default="{ row }">
          <span :class="['value', row.total_return >= 0 ? 'positive' : 'negative']">
            {{ row.total_return >= 0 ? '+' : '' }}{{ row.total_return.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>

      <el-table-column label="年化收益" width="120" sortable prop="annualized_return">
        <template #default="{ row }">
          <span :class="['value', row.annualized_return >= 0 ? 'positive' : 'negative']">
            {{ row.annualized_return >= 0 ? '+' : '' }}{{ row.annualized_return.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>

      <el-table-column label="夏普比率" width="120" sortable prop="sharpe_ratio">
        <template #default="{ row }">
          <el-tag :type="getSharpeType(row.sharpe_ratio)" size="small">
            {{ row.sharpe_ratio.toFixed(2) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="最大回撤" width="120" sortable prop="max_drawdown">
        <template #default="{ row }">
          <span class="value negative">
            {{ row.max_drawdown.toFixed(2) }}%
          </span>
        </template>
      </el-table-column>

      <el-table-column label="交易次数" width="100" sortable prop="total_trades" />

      <el-table-column label="胜率" width="100" sortable prop="win_rate">
        <template #default="{ row }">
          <el-progress
            :percentage="row.win_rate * 100"
            :color="getWinRateColor(row.win_rate)"
            :stroke-width="12"
          />
        </template>
      </el-table-column>

      <el-table-column label="策略" min-width="150" prop="strategy_name" />
    </el-table>

    <!-- 统计汇总 -->
    <div class="summary" v-if="results.length > 0">
      <el-divider />
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="平均收益率" :value="avgReturn" suffix="%" :precision="2">
            <template #prefix>
              <el-icon :color="avgReturn >= 0 ? '#3fb950' : '#f85149'">
                <TrendCharts />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="平均夏普比率" :value="avgSharpe" :precision="2">
            <template #prefix>
              <el-icon color="#58a6ff">
                <DataAnalysis />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="平均最大回撤" :value="avgDrawdown" suffix="%" :precision="2">
            <template #prefix>
              <el-icon color="#f85149">
                <Bottom />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="平均胜率" :value="avgWinRate" suffix="%" :precision="1">
            <template #prefix>
              <el-icon color="#3fb950">
                <Trophy />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </div>

    <!-- 净值曲线 -->
    <div v-if="results.length > 0" class="equity-section">
      <el-divider />
      <h3 class="section-title">净值曲线</h3>
      <div ref="equityChartRef" class="equity-chart" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import type { BacktestResult } from '@/types'
import { TrendCharts, DataAnalysis, Bottom, Trophy } from '@element-plus/icons-vue'
import { createChart, ColorType, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts'

const props = defineProps<{
  results: BacktestResult[]
  equityData?: number[][]  // per-result equity curves
}>()

const equityChartRef = ref<HTMLElement | null>(null)
let equityChart: IChartApi | null = null
let equityLine: ISeriesApi<'Line'> | null = null

watch(() => props.equityData, drawEquity, { deep: true })

function drawEquity() {
  if (!equityChartRef.value || !props.equityData?.length) return
  equityChart?.remove()
  equityChart = createChart(equityChartRef.value, {
    layout: { background: { type: ColorType.Solid, color: '#0d1117' }, textColor: '#c9d1d9' },
    grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
    width: equityChartRef.value.clientWidth,
    height: 300,
  })
  equityLine = equityChart.addLineSeries({ color: '#58a6ff', lineWidth: 2 })
  const data: LineData[] = props.equityData[0].map((v, i) => ({ time: i, value: v }))
  equityLine.setData(data)
  equityChart.timeScale().fitContent()
}

const props = defineProps<{
  results: BacktestResult[]
}>()

// 表格行类名
const tableRowClassName = ({ row }: { row: BacktestResult }) => {
  return row.total_return >= 0 ? 'success-row' : 'danger-row'
}

// 夏普比率类型
const getSharpeType = (sharpe: number) => {
  if (sharpe >= 2) return 'success'
  if (sharpe >= 1) return ''
  if (sharpe >= 0) return 'warning'
  return 'danger'
}

// 胜率颜色
const getWinRateColor = (rate: number) => {
  if (rate >= 0.6) return '#3fb950'
  if (rate >= 0.5) return '#58a6ff'
  return '#f85149'
}

// 统计汇总
const avgReturn = computed(() => {
  if (props.results.length === 0) return 0
  return props.results.reduce((sum, r) => sum + r.total_return, 0) / props.results.length
})

const avgSharpe = computed(() => {
  if (props.results.length === 0) return 0
  return props.results.reduce((sum, r) => sum + r.sharpe_ratio, 0) / props.results.length
})

const avgDrawdown = computed(() => {
  if (props.results.length === 0) return 0
  return props.results.reduce((sum, r) => sum + r.max_drawdown, 0) / props.results.length
})

const avgWinRate = computed(() => {
  if (props.results.length === 0) return 0
  return (props.results.reduce((sum, r) => sum + r.win_rate, 0) / props.results.length) * 100
})
</script>

<style scoped>
.backtest-result {
  width: 100%;
}

.value {
  font-weight: 600;
  font-size: 14px;
}

.value.positive {
  color: #3fb950;
}

.value.negative {
  color: #f85149;
}

:deep(.el-table) {
  background: #0d1117;
  color: #c9d1d9;
}

:deep(.el-table th) {
  background: #161b22;
  color: #c9d1d9;
  border-bottom: 1px solid #30363d;
}

:deep(.el-table td) {
  border-bottom: 1px solid #30363d;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #161b22;
}

:deep(.el-table__body tr:hover > td) {
  background: #21262d !important;
}

.summary {
  margin-top: 24px;
}

:deep(.el-statistic__head) {
  color: #8b949e;
  font-size: 14px;
}

:deep(.el-statistic__content) {
  color: #c9d1d9;
}

.equity-section {
  margin-top: 24px;
}

.section-title {
  font-size: 15px;
  color: #c9d1d9;
  margin: 0 0 12px;
}

.equity-chart {
  width: 100%;
  height: 300px;
}
</style>
