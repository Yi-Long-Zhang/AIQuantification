<template>
  <el-card class="strategy-card" :body-style="{ padding: '20px' }" shadow="hover">
    <div class="card-content">
      <div class="strategy-icon">
        <el-icon :size="32" color="#58a6ff">
          <TrendCharts />
        </el-icon>
      </div>

      <h3 class="strategy-name">{{ strategy.name }}</h3>
      <p class="strategy-desc">{{ strategy.description }}</p>

      <div v-if="strategy.parameters" class="parameters">
        <el-divider />
        <div class="param-title">参数配置</div>
        <div class="param-list">
          <div
            v-for="(value, key) in strategy.parameters"
            :key="key"
            class="param-item"
          >
            <span class="param-key">{{ key }}:</span>
            <span class="param-value">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button type="primary" @click="handleUse" style="width: 100%">
        <el-icon><DataAnalysis /></el-icon>
        使用此策略
      </el-button>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import type { Strategy } from '@/types'
import { TrendCharts, DataAnalysis } from '@element-plus/icons-vue'

const props = defineProps<{
  strategy: Strategy
}>()

const emit = defineEmits<{
  use: [strategy: Strategy]
}>()

const handleUse = () => {
  emit('use', props.strategy)
}
</script>

<style scoped>
.strategy-card {
  background: #161b22;
  border: 1px solid #30363d;
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.strategy-card:hover {
  border-color: #58a6ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(88, 166, 255, 0.15);
}

.card-content {
  flex: 1;
}

.strategy-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.strategy-name {
  margin: 0 0 8px;
  font-size: 18px;
  color: #c9d1d9;
  font-weight: 600;
}

.strategy-desc {
  margin: 0;
  font-size: 14px;
  color: #8b949e;
  line-height: 1.6;
  min-height: 42px;
}

.parameters {
  margin-top: 16px;
}

.param-title {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 8px;
  font-weight: 500;
}

.param-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-item {
  font-size: 12px;
  display: flex;
  justify-content: space-between;
}

.param-key {
  color: #8b949e;
}

.param-value {
  color: #58a6ff;
  font-weight: 500;
}
</style>
