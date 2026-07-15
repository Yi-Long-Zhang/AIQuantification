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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { marketAPI } from '@/api/market'
import type { MarketQuote } from '@/types'
import MarketCard from '@/components/MarketCard.vue'
import { Refresh } from '@element-plus/icons-vue'

const activeMarket = ref('us_stock')
const marketData = ref<MarketQuote[]>([])
const loading = ref(false)
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

const showDetail = (item: MarketQuote) => {
  console.log('Show detail:', item)
  // TODO: 展示详情弹窗或跳转到详情页
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
</style>
