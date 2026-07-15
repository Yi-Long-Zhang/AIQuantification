<template>
  <el-card class="market-card" :body-style="{ padding: '20px' }" shadow="hover">
    <div class="card-header">
      <span class="symbol">{{ data.symbol }}</span>
      <span v-if="data.name" class="name">{{ data.name }}</span>
    </div>

    <div class="price-section">
      <div class="price">{{ formatPrice(data.price) }}</div>
      <div :class="['change', data.change >= 0 ? 'positive' : 'negative']">
        {{ data.change >= 0 ? '+' : '' }}{{ formatPrice(data.change) }}
        ({{ data.change >= 0 ? '+' : '' }}{{ data.change_percent.toFixed(2) }}%)
      </div>
    </div>

    <div class="info-section">
      <div class="info-item">
        <span class="label">成交量</span>
        <span class="value">{{ formatVolume(data.volume) }}</span>
      </div>
      <div v-if="data.market_cap" class="info-item">
        <span class="label">市值</span>
        <span class="value">{{ formatVolume(data.market_cap) }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { MarketQuote } from '@/types'

defineProps<{
  data: MarketQuote
}>()

const formatPrice = (price: number) => {
  if (price >= 1000) {
    return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  return price.toFixed(2)
}

const formatVolume = (volume: number) => {
  if (volume >= 1e12) return (volume / 1e12).toFixed(2) + 'T'
  if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B'
  if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M'
  if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K'
  return volume.toString()
}
</script>

<style scoped>
.market-card {
  margin-bottom: 20px;
  background: #161b22;
  border: 1px solid #30363d;
  cursor: pointer;
  transition: all 0.3s;
}

.market-card:hover {
  border-color: #58a6ff;
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.symbol {
  font-size: 18px;
  font-weight: bold;
  color: #58a6ff;
}

.name {
  font-size: 12px;
  color: #8b949e;
}

.price-section {
  margin-bottom: 16px;
}

.price {
  font-size: 28px;
  font-weight: 600;
  color: #c9d1d9;
  margin-bottom: 4px;
}

.change {
  font-size: 16px;
  font-weight: 600;
}

.change.positive {
  color: #3fb950;
}

.change.negative {
  color: #f85149;
}

.info-section {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #30363d;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: #8b949e;
}

.value {
  font-size: 14px;
  color: #c9d1d9;
  font-weight: 500;
}
</style>
