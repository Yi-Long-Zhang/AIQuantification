<template>
  <div class="strategies-container">
    <div class="strategies-header">
      <h1>策略库与技能</h1>
      <p class="subtitle">浏览交易策略和 AI 量化技能</p>
    </div>

    <el-tabs v-model="activeTab" class="content-tabs">
      <el-tab-pane label="交易策略" name="strategies">
        <div v-loading="loadingStrategies" class="content-grid">
          <el-empty
            v-if="!loadingStrategies && strategies.length === 0"
            description="暂无策略"
          />
          <el-row :gutter="20" v-else>
            <el-col
              :xs="24" :sm="12" :md="8" :lg="6"
              v-for="strategy in strategies" :key="strategy.name"
            >
              <StrategyCard :strategy="strategy" @use="useStrategy" />
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="AI 技能" name="skills">
        <div v-loading="loadingSkills" class="content-grid">
          <el-empty
            v-if="!loadingSkills && skills.length === 0"
            description="暂无技能"
          />
          <el-row :gutter="20" v-else>
            <el-col
              :xs="24" :sm="12" :md="8" :lg="6"
              v-for="skill in skills" :key="skill.name"
            >
              <el-card shadow="hover" class="skill-card">
                <template #header>
                  <div class="skill-header">
                    <span class="skill-name">{{ skill.name }}</span>
                    <el-tag
                      v-for="tag in skill.tags" :key="tag"
                      size="small" class="skill-tag"
                    >{{ tag }}</el-tag>
                  </div>
                </template>
                <p class="skill-desc">{{ skill.description }}</p>
                <div v-if="skill.tools.length" class="skill-tools">
                  <span class="tools-label">工具：</span>
                  <el-tag
                    v-for="tool in skill.tools" :key="tool"
                    size="small" type="info" class="tool-tag"
                  >{{ tool }}</el-tag>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { backtestAPI } from '@/api/backtest'
import { skillsAPI } from '@/api/skills'
import type { Strategy, Skill } from '@/types'
import StrategyCard from '@/components/StrategyCard.vue'

const router = useRouter()
const activeTab = ref('strategies')

const strategies = ref<Strategy[]>([])
const loadingStrategies = ref(false)

const skills = ref<Skill[]>([])
const loadingSkills = ref(false)

onMounted(async () => {
  loadingStrategies.value = true
  try {
    const response = await backtestAPI.getStrategies()
    strategies.value = response.data?.strategies || []
  } catch (error) {
    console.error('Load strategies error:', error)
  } finally {
    loadingStrategies.value = false
  }

  loadingSkills.value = true
  try {
    const response = await skillsAPI.getSkills()
    skills.value = response.data?.skills || []
  } catch (error) {
    console.error('Load skills error:', error)
  } finally {
    loadingSkills.value = false
  }
})

const useStrategy = (strategy: Strategy) => {
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

.content-grid {
  min-height: 400px;
}

.content-tabs {
  margin-top: 8px;
}

.skill-card {
  margin-bottom: 16px;
}

.skill-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.skill-name {
  font-weight: 600;
  font-size: 15px;
  color: #58a6ff;
}

.skill-tag {
  margin-left: 4px;
}

.skill-desc {
  font-size: 13px;
  color: #8b949e;
  line-height: 1.5;
  margin: 0 0 12px;
}

.skill-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.tools-label {
  font-size: 12px;
  color: #6e7681;
}

.tool-tag {
  margin: 2px;
}
</style>
