<template>
  <div class="agent-monitor">
    <!-- Header -->
    <div class="page-header">
      <h1>🤖 Agent 监控中心</h1>
      <div class="header-actions">
        <el-tag :type="systemOnline ? 'success' : 'danger'">
          {{ systemOnline ? '系统在线' : '系统离线' }}
        </el-tag>
        <el-button @click="refreshStatus" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="runCycle" :loading="cycleRunning">
          <el-icon><VideoPlay /></el-icon>
          运行交易周期
        </el-button>
      </div>
    </div>

    <!-- Broker Stats -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ status.registered_agents?.length ?? 0 }}</div>
          <div class="stat-label">已注册 Agent</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value">{{ brokerStats.total_messages ?? 0 }}</div>
          <div class="stat-label">总消息数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value success">{{ executionSummary.successful ?? 0 }}</div>
          <div class="stat-label">成功任务</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-value danger">{{ executionSummary.failed ?? 0 }}</div>
          <div class="stat-label">失败任务</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- Agent Status Panel -->
      <el-col :span="10">
        <el-card class="panel-card">
          <template #header>
            <span>Agent 状态</span>
            <el-tag size="small" type="info" style="margin-left:8px">
              {{ status.registered_agents?.length ?? 0 }} 个
            </el-tag>
          </template>

          <div v-if="!status.registered_agents?.length" class="empty-state">
            <el-icon :size="40" color="#8b949e"><UserFilled /></el-icon>
            <p>暂无注册的 Agent</p>
            <p class="hint">运行一次交易周期后 Agent 将自动注册</p>
          </div>

          <div v-else class="agent-list">
            <div
              v-for="agent in status.registered_agents"
              :key="agent"
              class="agent-item"
              @click="selectedAgent = agent"
              :class="{ active: selectedAgent === agent }"
            >
              <div class="agent-icon">🤖</div>
              <div class="agent-info">
                <div class="agent-name">{{ agent }}</div>
                <div class="agent-queue">
                  队列: {{ brokerStats.queue_sizes?.[agent] ?? 0 }} 条消息
                </div>
              </div>
              <el-tag size="small" type="success">在线</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Message Log -->
      <el-col :span="14">
        <el-card class="panel-card">
          <template #header>
            <span>消息日志</span>
            <el-select
              v-model="selectedAgent"
              placeholder="筛选 Agent"
              clearable
              size="small"
              style="margin-left:8px;width:160px"
            >
              <el-option
                v-for="a in status.registered_agents ?? []"
                :key="a" :label="a" :value="a"
              />
            </el-select>
          </template>

          <div v-if="!messages.length" class="empty-state">
            <el-icon :size="40" color="#8b949e"><ChatLineRound /></el-icon>
            <p>暂无消息记录</p>
          </div>

          <div v-else class="message-log">
            <div
              v-for="msg in messages"
              :key="msg.message_id"
              class="message-item"
              :class="getMessageClass(msg.message_type)"
            >
              <div class="msg-header">
                <span class="msg-from">{{ msg.from_agent }}</span>
                <span class="msg-arrow">→</span>
                <span class="msg-to">{{ msg.to_agent }}</span>
                <el-tag size="small" :type="getTypeTagType(msg.message_type)">
                  {{ msg.message_type }}
                </el-tag>
                <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="msg-body">
                {{ truncate(JSON.stringify(msg.content), 120) }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Cycle Result -->
    <el-card v-if="lastCycleResult" class="cycle-card">
      <template #header>
        <span>最新交易周期结果</span>
        <el-tag
          :type="lastCycleResult.status === 'COMPLETE' ? 'success' : 'danger'"
          style="margin-left:8px"
        >
          {{ lastCycleResult.status }}
        </el-tag>
        <span class="cycle-time">{{ lastCycleResult.elapsed_seconds?.toFixed(1) }}s</span>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="周期ID">
          {{ lastCycleResult.cycle_id }}
        </el-descriptions-item>
        <el-descriptions-item label="市场">
          {{ lastCycleResult.market }}
        </el-descriptions-item>
        <el-descriptions-item label="时间">
          {{ formatTime(lastCycleResult.timestamp) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- Final Decisions -->
      <div v-if="lastCycleResult.final_decision?.decisions?.length" class="decisions">
        <h4>AI 决策</h4>
        <el-table :data="lastCycleResult.final_decision.decisions" size="small">
          <el-table-column prop="symbol" label="标的" width="90" />
          <el-table-column prop="action" label="动作" width="80">
            <template #default="{ row }">
              <el-tag :type="row.action === 'BUY' ? 'success' : row.action === 'SELL' ? 'danger' : 'info'">
                {{ row.action }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.round((row.confidence ?? 0) * 100)"
                :color="row.confidence >= 0.7 ? '#67C23A' : '#E6A23C'"
              />
            </template>
          </el-table-column>
          <el-table-column prop="reasoning" label="理由" show-overflow-tooltip />
        </el-table>
      </div>

      <el-empty v-else description="本轮无交易信号" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh, VideoPlay, UserFilled, ChatLineRound
} from '@element-plus/icons-vue'
import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8000' })

// ── State ──────────────────────────────────────────────
const loading      = ref(false)
const cycleRunning = ref(false)
const status       = ref<any>({})
const brokerStats  = ref<any>()
const messages     = ref<any[]>([])
const selectedAgent = ref<string | null>(null)
const lastCycleResult = ref<any>(null)
let pollTimer: number | null = null

// ── Computed ───────────────────────────────────────────
const systemOnline = computed(() => !!status.value.coordinator)
const executionSummary = computed(
  () => status.value.execution_summary ?? {}
)

// ── API calls ──────────────────────────────────────────
const refreshStatus = async () => {
  loading.value = true
  try {
    const [statusRes, statsRes, msgsRes] = await Promise.all([
      API.get('/multi-agent/status'),
      API.get('/multi-agent/broker/stats'),
      API.get('/multi-agent/messages', {
        params: { agent: selectedAgent.value || undefined, limit: 50 }
      })
    ])
    status.value      = statusRes.data
    brokerStats.value = statsRes.data
    messages.value    = msgsRes.data.messages.reverse()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const runCycle = async () => {
  cycleRunning.value = true
  try {
    const res = await API.post('/multi-agent/cycle', { market: 'us_stock' })
    lastCycleResult.value = res.data
    ElMessage.success('交易周期完成')
    await refreshStatus()
  } catch (e: any) {
    ElMessage.error('交易周期失败: ' + (e.message ?? ''))
  } finally {
    cycleRunning.value = false
  }
}

// ── Helpers ────────────────────────────────────────────
const formatTime = (ts: string) =>
  ts ? new Date(ts).toLocaleTimeString('zh-CN') : '-'

const truncate = (s: string, n: number) =>
  s.length > n ? s.slice(0, n) + '…' : s

const getMessageClass = (type: string) => ({
  'msg-request':      type === 'REQUEST',
  'msg-response':     type === 'RESPONSE',
  'msg-notification': type === 'NOTIFICATION',
  'msg-error':        type === 'ERROR',
})

const getTypeTagType = (type: string) =>
  ({ REQUEST: 'primary', RESPONSE: 'success', NOTIFICATION: 'info', ERROR: 'danger' }[type] ?? 'info')

// ── Lifecycle ──────────────────────────────────────────
onMounted(() => {
  refreshStatus()
  pollTimer = window.setInterval(refreshStatus, 10000)
})
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.agent-monitor { padding: 24px; min-height: 100vh; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h1 { margin: 0; font-size: 22px; color: #c9d1d9; }
.header-actions { display: flex; gap: 10px; align-items: center; }

.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; background: #161b22; border-color: #30363d; }
.stat-value { font-size: 28px; font-weight: 700; color: #58a6ff; margin-bottom: 4px; }
.stat-value.success { color: #67C23A; }
.stat-value.danger  { color: #f56c6c; }
.stat-label { font-size: 13px; color: #8b949e; }

.panel-card {
  background: #161b22;
  border-color: #30363d;
  margin-bottom: 16px;
  height: 380px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
:deep(.panel-card .el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.empty-state {
  text-align: center;
  color: #8b949e;
  padding: 40px 0;
}
.empty-state .hint { font-size: 12px; margin-top: 4px; }

/* Agent list */
.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #21262d;
}
.agent-item:hover, .agent-item.active { background: #21262d; }
.agent-icon { font-size: 22px; }
.agent-info { flex: 1; }
.agent-name { font-size: 14px; color: #c9d1d9; font-weight: 500; }
.agent-queue { font-size: 12px; color: #8b949e; margin-top: 2px; }

/* Message log */
.message-log { display: flex; flex-direction: column; gap: 8px; }
.message-item {
  padding: 8px 10px;
  border-radius: 6px;
  background: #0d1117;
  border-left: 3px solid #30363d;
  font-size: 13px;
}
.msg-request      { border-left-color: #58a6ff; }
.msg-response     { border-left-color: #67C23A; }
.msg-notification { border-left-color: #E6A23C; }
.msg-error        { border-left-color: #f56c6c; }

.msg-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.msg-from, .msg-to { color: #58a6ff; font-weight: 500; }
.msg-arrow { color: #8b949e; }
.msg-time { color: #8b949e; font-size: 11px; margin-left: auto; }
.msg-body { color: #8b949e; font-size: 12px; }

/* Cycle card */
.cycle-card { background: #161b22; border-color: #30363d; margin-top: 16px; }
.cycle-time { color: #8b949e; font-size: 13px; margin-left: 8px; }
.decisions { margin-top: 16px; }
.decisions h4 { color: #c9d1d9; margin: 0 0 10px; }
</style>
