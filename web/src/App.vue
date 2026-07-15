<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <h2>🤖 AIQuant</h2>
        <p class="subtitle">量化交易助手</p>
      </div>

      <el-menu
        :default-active="$route.path"
        router
        background-color="#161b22"
        text-color="#c9d1d9"
        active-text-color="#58a6ff"
        class="sidebar-menu"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 对话</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>市场仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/backtest">
          <el-icon><DataAnalysis /></el-icon>
          <span>策略回测</span>
        </el-menu-item>
        <el-menu-item index="/strategies">
          <el-icon><Management /></el-icon>
          <span>策略库</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button text @click="showSettings = true">
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="main-content">
      <router-view />
    </el-main>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="设置" width="500px">
      <el-form label-width="100px">
        <el-form-item label="API Key">
          <el-input
            v-model="apiKey"
            type="password"
            placeholder="输入 API Key（可选）"
            show-password
          />
          <div class="form-tip">
            如果后端启用了认证，需要配置 API Key
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ChatDotRound, Monitor, DataAnalysis, Management, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const showSettings = ref(false)
const apiKey = ref('')

onMounted(() => {
  // 加载已保存的 API Key
  apiKey.value = localStorage.getItem('api_key') || ''
})

const saveSettings = () => {
  if (apiKey.value) {
    localStorage.setItem('api_key', apiKey.value)
    ElMessage.success('设置已保存')
  } else {
    localStorage.removeItem('api_key')
    ElMessage.info('已清除 API Key')
  }
  showSettings.value = false
}
</script>

<style scoped>
.layout {
  height: 100vh;
  background: #0d1117;
  color: #c9d1d9;
}

.sidebar {
  background: #161b22;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 24px 20px;
  text-align: center;
  border-bottom: 1px solid #30363d;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  color: #58a6ff;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 12px;
  color: #8b949e;
}

.sidebar-menu {
  flex: 1;
  border: none;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #30363d;
  text-align: center;
}

.main-content {
  padding: 0;
  overflow: auto;
  background: #0d1117;
}

.form-tip {
  font-size: 12px;
  color: #8b949e;
  margin-top: 4px;
}
</style>
