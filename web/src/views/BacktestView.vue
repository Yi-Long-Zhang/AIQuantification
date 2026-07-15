<template>
  <div class="backtest-container">
    <div class="backtest-header">
      <h1>策略回测</h1>
      <p class="subtitle">通过历史数据验证交易策略的表现</p>
    </div>

    <!-- 配置表单 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>回测配置</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="选择策略" prop="strategy_name">
          <el-select
            v-model="form.strategy_name"
            placeholder="请选择策略"
            style="width: 100%"
            @change="onStrategyChange"
          >
            <el-option
              v-for="s in strategies"
              :key="s.name"
              :label="s.name"
              :value="s.name"
            >
              <div class="strategy-option">
                <span>{{ s.name }}</span>
                <span class="strategy-desc">{{ s.description }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="股票代码" prop="symbols">
          <el-select
            v-model="form.symbols"
            multiple
            filterable
            allow-create
            placeholder="输入股票代码，如 AAPL, MSFT"
            style="width: 100%"
          >
            <el-option
              v-for="symbol in popularSymbols"
              :key="symbol"
              :label="symbol"
              :value="symbol"
            />
          </el-select>
          <div class="form-tip">
            支持多个股票代码，可以直接输入创建
          </div>
        </el-form-item>

        <el-form-item label="回测周期" prop="dateRange">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            :disabled-date="disabledDate"
          />
        </el-form-item>

        <el-form-item label="初始资金">
          <el-input-number
            v-model="form.initial_capital"
            :min="10000"
            :max="10000000"
            :step="10000"
            :precision="0"
            style="width: 200px"
          />
          <span class="currency-unit">USD</span>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="runBacktest"
            :loading="loading"
            :disabled="!canSubmit"
          >
            <el-icon><DataAnalysis /></el-icon>
            开始回测
          </el-button>
          <el-button @click="resetForm">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 结果展示 -->
    <el-card v-if="results.length > 0" class="results-card">
      <template #header>
        <div class="card-header">
          <span>回测结果</span>
          <el-button text @click="exportResults">
            <el-icon><Download /></el-icon>
            导出结果
          </el-button>
        </div>
      </template>

      <BacktestResult :results="results" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { backtestAPI } from '@/api/backtest'
import type { Strategy, BacktestResult as IBacktestResult } from '@/types'
import BacktestResult from '@/components/BacktestResult.vue'
import { DataAnalysis, RefreshLeft, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const strategies = ref<Strategy[]>([])
const form = ref({
  strategy_name: '',
  symbols: [] as string[],
  initial_capital: 100000
})
const dateRange = ref<[string, string]>(['', ''])
const results = ref<IBacktestResult[]>([])
const loading = ref(false)
const formRef = ref<FormInstance>()

// 常用股票代码
const popularSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD']

// 表单验证规则
const rules: FormRules = {
  strategy_name: [
    { required: true, message: '请选择策略', trigger: 'change' }
  ],
  symbols: [
    { required: true, message: '请输入至少一个股票代码', trigger: 'change' }
  ]
}

// 是否可以提交
const canSubmit = computed(() => {
  return form.value.strategy_name &&
         form.value.symbols.length > 0 &&
         dateRange.value[0] &&
         dateRange.value[1]
})

// 禁用未来日期
const disabledDate = (date: Date) => {
  return date.getTime() > Date.now()
}

// 加载策略列表
onMounted(async () => {
  try {
    const response = await backtestAPI.getStrategies()
    strategies.value = response.data?.strategies || []

    // 设置默认日期（最近1年）
    const end = new Date()
    const start = new Date()
    start.setFullYear(start.getFullYear() - 1)

    dateRange.value = [
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    ]
  } catch (error) {
    console.error('Load strategies error:', error)
  }
})

// 策略变化
const onStrategyChange = (strategyName: string) => {
  const strategy = strategies.value.find(s => s.name === strategyName)
  console.log('Selected strategy:', strategy)
}

// 运行回测
const runBacktest = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (!dateRange.value[0] || !dateRange.value[1]) {
      ElMessage.warning('请选择回测周期')
      return
    }

    loading.value = true
    try {
      results.value = await backtestAPI.runBacktest({
        ...form.value,
        start_date: dateRange.value[0],
        end_date: dateRange.value[1]
      })

      if (results.value.length === 0) {
        ElMessage.warning('回测未返回结果')
      } else {
        ElMessage.success('回测完成')
      }
    } catch (error) {
      console.error('Backtest error:', error)
    } finally {
      loading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  results.value = []
}

// 导出结果
const exportResults = () => {
  const csv = [
    ['股票', '策略', '总收益率', '年化收益', '夏普比率', '最大回撤', '交易次数', '胜率'].join(','),
    ...results.value.map(r => [
      r.symbol,
      r.strategy_name,
      r.total_return.toFixed(2) + '%',
      r.annualized_return.toFixed(2) + '%',
      r.sharpe_ratio.toFixed(2),
      r.max_drawdown.toFixed(2) + '%',
      r.total_trades,
      (r.win_rate * 100).toFixed(1) + '%'
    ].join(','))
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `backtest_${Date.now()}.csv`
  link.click()
}
</script>

<style scoped>
.backtest-container {
  padding: 24px;
  min-height: 100vh;
}

.backtest-header {
  margin-bottom: 24px;
}

.backtest-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #c9d1d9;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #8b949e;
}

.config-card,
.results-card {
  margin-bottom: 24px;
  background: #161b22;
  border: 1px solid #30363d;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strategy-desc {
  font-size: 12px;
  color: #8b949e;
}

.form-tip {
  font-size: 12px;
  color: #8b949e;
  margin-top: 4px;
}

.currency-unit {
  margin-left: 8px;
  color: #8b949e;
}
</style>
