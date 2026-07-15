<template>
  <div class="chat-container">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <h2>AI 量化分析助手</h2>
      <div class="header-actions">
        <el-button text @click="clearChat">
          <el-icon><Delete /></el-icon>
          清空对话
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages-area" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-state">
        <el-icon :size="64" color="#8b949e"><ChatDotRound /></el-icon>
        <h3>开始对话</h3>
        <p>尝试问我：分析 AAPL 的技术面，或者比较 BTC 和 ETH</p>
      </div>

      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />

      <div v-if="isLoading" class="loading-indicator">
        <el-icon class="is-loading" :size="20"><Loading /></el-icon>
        <span>AI 分析中...</span>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入你的问题，例如：分析 AAPL 的近期走势，或 Ctrl+Enter 快速发送"
        @keydown.enter.ctrl="sendMessage"
        @keydown.enter.meta="sendMessage"
      />
      <el-button
        type="primary"
        :loading="isLoading"
        :disabled="!inputText.trim()"
        @click="sendMessage"
      >
        <el-icon><Promotion /></el-icon>
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { agentAPI } from '@/api/agent'
import ChatMessage from '@/components/ChatMessage.vue'
import { Delete, ChatDotRound, Loading, Promotion } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const chatStore = useChatStore()
const { messages, isLoading, addMessage, updateLastMessage } = chatStore

const inputText = ref('')
const messagesRef = ref<HTMLElement>()

const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value) return

  const query = inputText.value.trim()
  inputText.value = ''

  // 添加用户消息
  addMessage({ role: 'user', content: query })

  isLoading.value = true

  try {
    // 使用流式对话
    const eventSource = agentAPI.chatStream({
      query,
      session_id: chatStore.sessionId
    })

    let assistantMessage = ''
    let hasAddedAssistantMsg = false

    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close()
        isLoading.value = false
        return
      }

      try {
        const data = JSON.parse(event.data)

        if (data.session_id) {
          chatStore.sessionId = data.session_id
        }

        if (data.chunk) {
          assistantMessage += data.chunk

          if (!hasAddedAssistantMsg) {
            addMessage({ role: 'assistant', content: assistantMessage })
            hasAddedAssistantMsg = true
          } else {
            updateLastMessage(assistantMessage)
          }

          // 滚动到底部
          scrollToBottom()
        }

        if (data.error) {
          console.error('Stream error:', data.error)
          eventSource.close()
          isLoading.value = false
        }
      } catch (e) {
        console.error('Parse error:', e)
      }
    }

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      eventSource.close()
      isLoading.value = false

      if (!assistantMessage) {
        addMessage({
          role: 'assistant',
          content: '抱歉，连接出现问题，请重试。'
        })
      }
    }

  } catch (error) {
    console.error('Chat error:', error)
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const clearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空对话历史吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    chatStore.clearMessages()
  } catch {
    // 取消操作
  }
}
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0d1117;
}

.chat-header {
  padding: 16px 24px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
  color: #c9d1d9;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8b949e;
  text-align: center;
}

.empty-state h3 {
  margin: 16px 0 8px;
  color: #c9d1d9;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8b949e;
  font-size: 14px;
}

.input-area {
  padding: 16px 24px;
  background: #161b22;
  border-top: 1px solid #30363d;
  display: flex;
  gap: 12px;
}

.input-area :deep(.el-textarea__inner) {
  background: #0d1117;
  border-color: #30363d;
  color: #c9d1d9;
}

.input-area :deep(.el-textarea__inner):focus {
  border-color: #58a6ff;
}
</style>
