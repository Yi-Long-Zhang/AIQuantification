import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const sessionId = ref<string>(crypto.randomUUID())
  const messages = ref<Message[]>([])
  const isLoading = ref(false)

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    messages.value.push({
      ...message,
      id: crypto.randomUUID(),
      timestamp: Date.now()
    })
  }

  const updateLastMessage = (content: string) => {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = content
    }
  }

  const clearMessages = () => {
    messages.value = []
    sessionId.value = crypto.randomUUID()
  }

  return {
    sessionId,
    messages,
    isLoading,
    addMessage,
    updateLastMessage,
    clearMessages
  }
})
