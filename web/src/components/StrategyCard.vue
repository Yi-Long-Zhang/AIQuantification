<template>
  <el-card class="strategy-card" :body-style="{ padding: '20px' }" shadow="hover">
    <div class="card-content">
      <div class="strategy-header">
        <div class="strategy-icon">
          <el-icon :size="28" color="#58a6ff">
            <TrendCharts />
          </el-icon>
        </div>
        <el-tag :type="tagType" size="small" class="type-tag">{{ strategy.type }}</el-tag>
      </div>

      <h3 class="strategy-name">{{ strategy.name }}</h3>
      <p class="strategy-desc">{{ strategy.description }}</p>

      <div v-if="strategy.tags?.length" class="tags-row">
        <el-tag
          v-for="tag in strategy.tags" :key="tag"
          size="small" type="info" class="skill-tag"
        >{{ tag }}</el-tag>
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
import { computed } from 'vue'

const props = defineProps<{
  strategy: Strategy
}>()

const emit = defineEmits<{
  use: [strategy: Strategy]
}>()

const tagType = computed(() => {
  const map: Record<string, string> = {
    '趋势': 'success',
    '反转': 'warning',
    '均值回归': 'danger',
    '事件驱动': 'info',
    '组合': 'primary',
  }
  return map[props.strategy.type] || ''
})

const handleUse = () => {
  emit('use', props.strategy)
}
</script>

<style scoped>
.strategy-card {
  background: #161b22;
  border: 1px solid #30363d;
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

.strategy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.strategy-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-tag {
  margin-left: auto;
}

.strategy-name {
  margin: 0 0 8px;
  font-size: 18px;
  color: #c9d1d9;
  font-weight: 600;
  text-transform: lowercase;
}

.strategy-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #8b949e;
  line-height: 1.5;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.skill-tag {
  margin: 2px;
}
</style>
