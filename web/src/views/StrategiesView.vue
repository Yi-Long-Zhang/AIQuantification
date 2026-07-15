<template>
  <div class="strategies-container">
    <div class="strategies-header">
      <h1>策略库</h1>
      <p class="subtitle">浏览和了解所有可用的交易策略</p>
    </div>

    <div v-loading="loading" class="strategies-grid">
      <el-empty
        v-if="!loading && strategies.length === 0"
        description="暂无策略"
      />

      <el-row :gutter="20" v-else>
        <el-col
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          v-for="strategy in strategies"
          :key="strategy.name"
        >
          <StrategyCard :strategy="strategy" @use="useStrategy" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { backtestAPI } from '@/api/backtest'
import type { Strategy } from '@/types'
import StrategyCard from '@/components/StrategyCard.vue'

const router = useRouter()
const strategies = ref<Strategy[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const response = await backtestAPI.getStrategies()
    strategies.value = response.data?.strategies || []
  } catch (error) {
    console.error('Load strategies error:', error)
  } finally {
    loading.value = false
  }
})

const useStrategy = (strategy: Strategy) => {
  // 跳转到回测页面并预填策略
  router.push({
    name: 'Backtest',
    query: { strategy: strategy.name }
  })
}
</script>

<style scoped>
.strategies-container {
  padding: 24px;
  min-height: 100vh;
}

.strategies-header {
  margin-bottom: 24px;
}

.strategies-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #c9d1d9;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #8b949e;
}

.strategies-grid {
  min-height: 400px;
}
</style>
