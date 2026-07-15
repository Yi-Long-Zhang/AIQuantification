<template>
  <div :class="['message', message.role]">
    <div class="message-avatar">
      <el-icon :size="24">
        <User v-if="message.role === 'user'" />
        <Avatar v-else />
      </el-icon>
    </div>

    <div class="message-body">
      <div class="message-header">
        <span class="role-badge">
          {{ message.role === 'user' ? '你' : 'AI Agent' }}
        </span>
        <span class="timestamp">
          {{ formatTime(message.timestamp) }}
        </span>
      </div>

      <div class="message-content" v-html="formattedContent"></div>

      <!-- 工具调用展示 -->
      <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
        <el-collapse>
          <el-collapse-item
            v-for="(call, idx) in message.tool_calls"
            :key="idx"
            :title="`🔧 ${call.tool}`"
          >
            <div class="tool-detail">
              <div class="tool-args">
                <strong>参数:</strong>
                <pre>{{ JSON.stringify(call.args, null, 2) }}</pre>
              </div>
              <div v-if="call.result" class="tool-result">
                <strong>结果:</strong>
                <pre>{{ JSON.stringify(call.result, null, 2) }}</pre>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { Message } from '@/types'
import { User, Avatar } from '@element-plus/icons-vue'

const props = defineProps<{
  message: Message
}>()

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

const formattedContent = computed(() => {
  return marked(props.message.content)
})

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #21262d;
  border: 1px solid #30363d;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #1f6feb;
  border-color: #1f6feb;
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.role-badge {
  font-weight: 600;
  color: #c9d1d9;
}

.timestamp {
  color: #8b949e;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  background: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
}

.message.user .message-content {
  background: #1f6feb;
  border-color: #1f6feb;
  color: white;
}

.message-content :deep(p) {
  margin: 0 0 8px 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: #0d1117;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.message-content :deep(pre) {
  background: #0d1117;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
}

.tool-calls {
  margin-top: 12px;
}

.tool-detail {
  font-size: 13px;
}

.tool-args,
.tool-result {
  margin-bottom: 12px;
}

.tool-detail pre {
  background: #0d1117;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin-top: 4px;
  font-size: 12px;
}
</style>
