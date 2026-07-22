<template>
  <div class="broker-container">
    <div class="broker-header">
      <h1>券商连接</h1>
      <p class="subtitle">管理券商连接，查看账户和持仓</p>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!loading && brokers.length === 0" description="暂无已注册的券商" />

      <el-row :gutter="20" v-else>
        <el-col :span="12" v-for="broker in brokers" :key="broker.name">
          <el-card class="broker-card" :class="{ connected: broker.connected }">
            <template #header>
              <div class="broker-header-row">
                <span class="broker-name">{{ broker.name.toUpperCase() }}</span>
                <el-tag :type="broker.connected ? 'success' : 'info'" size="small">
                  {{ broker.connected ? '已连接' : '未连接' }}
                </el-tag>
              </div>
            </template>

            <div v-if="statuses[broker.name]">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="账户ID">{{ statuses[broker.name].account?.account_id || '-' }}</el-descriptions-item>
                <el-descriptions-item label="现金">${{ statuses[broker.name].account?.cash?.toLocaleString() || '-' }}</el-descriptions-item>
                <el-descriptions-item label="净资产">${{ statuses[broker.name].account?.equity?.toLocaleString() || '-' }}</el-descriptions-item>
                <el-descriptions-item label="购买力">${{ statuses[broker.name].account?.buying_power?.toLocaleString() || '-' }}</el-descriptions-item>
              </el-descriptions>

              <div v-if="statuses[broker.name].positions?.length" class="positions-section">
                <h3 class="section-title">持仓 ({{ statuses[broker.name].positions.length }})</h3>
                <el-table :data="statuses[broker.name].positions" size="small" stripe>
                  <el-table-column prop="symbol" label="代码" width="80" />
                  <el-table-column prop="qty" label="数量" width="80" />
                  <el-table-column prop="avg_entry_price" label="均价" width="100">
                    <template #default="{ row }">${{ row.avg_entry_price?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column prop="current_price" label="现价" width="100">
                    <template #default="{ row }">${{ row.current_price?.toFixed(2) }}</template>
                  </el-table-column>
                  <el-table-column prop="unrealized_pl" label="浮动盈亏" width="120">
                    <template #default="{ row }">
                      <span :class="row.unrealized_pl >= 0 ? 'profit' : 'loss'">
                        ${{ row.unrealized_pl?.toFixed(2) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="market_value" label="市值" width="100">
                    <template #default="{ row }">${{ row.market_value?.toLocaleString() }}</template>
                  </el-table-column>
                </el-table>
              </div>
            </div>

            <div class="broker-actions">
              <el-button
                :type="broker.connected ? 'default' : 'primary'"
                size="small"
                :loading="connecting === broker.name"
                @click="handleConnect(broker.name)"
              >
                {{ broker.connected ? '重新连接' : '连接' }}
              </el-button>
              <el-button size="small" @click="handleRefresh(broker.name)">
                刷新
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { brokerAPI } from '@/api/broker'

const brokers = ref<any[]>([])
const statuses = reactive<Record<string, any>>({})
const loading = ref(false)
const connecting = ref<string | null>(null)

const loadBrokers = async () => {
  loading.value = true
  try {
    const res = await brokerAPI.listBrokers()
    brokers.value = res.brokers || []
  } catch {
    brokers.value = []
  } finally {
    loading.value = false
  }
}

const loadStatus = async (name: string) => {
  try {
    const res = await brokerAPI.getBrokerStatus(name)
    statuses[name] = res
  } catch {
    statuses[name] = { connected: false }
  }
}

const handleRefresh = async (name: string) => {
  await loadStatus(name)
  ElMessage.success(`${name.toUpperCase()} 已刷新`)
}

const handleConnect = async (name: string) => {
  connecting.value = name
  try {
    await brokerAPI.connectBroker(name)
    await loadStatus(name)
    ElMessage.success(`${name.toUpperCase()} 连接成功`)
  } catch {
    ElMessage.error(`${name.toUpperCase()} 连接失败`)
  } finally {
    connecting.value = null
  }
}

onMounted(async () => {
  await loadBrokers()
  for (const b of brokers.value) {
    await loadStatus(b.name)
  }
})
</script>

<style scoped>
.broker-container {
  padding: 24px;
  min-height: 100vh;
}

.broker-header {
  margin-bottom: 24px;
}

.broker-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #c9d1d9;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #8b949e;
}

.broker-card {
  margin-bottom: 20px;
}

.broker-card.connected {
  border-left: 3px solid #3fb950;
}

.broker-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.broker-name {
  font-weight: 600;
  font-size: 16px;
}

.broker-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.positions-section {
  margin-top: 16px;
}

.section-title {
  font-size: 14px;
  color: #c9d1d9;
  margin: 0 0 8px;
}

.profit {
  color: #3fb950;
}

.loss {
  color: #da3633;
}
</style>
