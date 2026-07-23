<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>市场仪表盘</h1>
      <el-button @click="loadMarketData" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-tabs v-model="activeMarket" @tab-change="loadMarketData" class="market-tabs">
      <el-tab-pane label="🇺🇸 美股" name="us_stock"></el-tab-pane>
      <el-tab-pane label="🇨🇳 A股" name="cn_stock"></el-tab-pane>
      <el-tab-pane label="🇭🇰 港股" name="hk_stock"></el-tab-pane>
      <el-tab-pane label="₿ 加密货币" name="crypto"></el-tab-pane>
    </el-tabs>

    <div v-loading="loading" class="market-grid">
      <el-empty
        v-if="!loading && marketData.length === 0"
        description="暂无数据"
      />

      <el-row :gutter="20" v-else>
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in marketData" :key="item.symbol">
          <MarketCard :data="item" @click="showDetail(item)" />
        </el-col>
      </el-row>
    </div>

    <el-divider />
    <div class="chart-section">
      <h3>K 线图</h3>
      <el-select v-model="chartSymbol" @change="chartKey++" placeholder="选择股票" size="small" style="width:200px;margin-bottom:12px">
        <el-option v-for="s in chartSymbols" :key="s" :label="s" :value="s" />
      </el-select>
      <KlineChart v-if="chartSymbol" :key="chartKey" :symbol="chartSymbol" :market="activeMarket" />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailItem?.symbol || '详情'" width="400px">
      <template v-if="detailItem">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="代码">{{ detailItem.symbol }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ detailItem.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="价格">
            <span :class="detailItem.change_percent >= 0 ? 'price-up' : 'price-down'">
              ${{ detailItem.price?.toLocaleString() }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="涨跌幅">
            <el-tag :type="detailItem.change_percent >= 0 ? 'success' : 'danger'" size="small">
              {{ detailItem.change_percent >= 0 ? '+' : '' }}{{ detailItem.change_percent }}%
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="成交量">{{ detailItem.volume?.toLocaleString() || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { marketAPI } from '@/api/market'
import type { MarketQuote } from '@/types'
import MarketCard from '@/components/MarketCard.vue'
import KlineChart from '@/components/KlineChart.vue'
import { Refresh } from '@element-plus/icons-vue'

const activeMarket = ref('us_stock')
const marketData = ref<MarketQuote[]>([])
const loading = ref(false)
const error = ref('')
const chartSymbol = ref('AAPL')
const chartKey = ref(0)
const chartSymbols: Record<string, string[]> = {
  us_stock: ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
  cn_stock: ['600519', '000001', '300750'],
  hk_stock: ['00700', '09988', '01810'],
  crypto: ['BTC', 'ETH', 'BNB', 'SOL'],
}
let refreshTimer: number | null = null

const loadMarketData = async () => {
  loading.value = true
  try {
    const response = await marketAPI.getOverview(activeMarket.value)
    marketData.value = response.data || []
  } catch (error) {
    console.error('Load market data error:', error)
    marketData.value = []
  } finally {
    loading.value = false
  }
}

const detailVisible = ref(false)
const detailItem = ref<MarketQuote | null>(null)

const showDetail = (item: MarketQuote) => {
  detailItem.value = item
  detailVisible.value = true
}

onMounted(() => {
  loadMarketData()
  // 每30秒自动刷新
  refreshTimer = window.setInterval(loadMarketData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
  color: #c9d1d9;
}

.market-tabs {
  margin-bottom: 24px;
}

.market-grid {
  min-height: 400px;
}

.price-up {
  color: #3fb950;
  font-weight: 600;
}

.price-down {
  color: #da3633;
  font-weight: 600;
}
</style>
