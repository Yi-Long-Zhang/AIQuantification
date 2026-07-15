import api from './index'
import type { ApiResponse } from '@/types'

export interface ChatRequest {
  query: string
  session_id?: string
}

export interface ChatResponse {
  answer: string
  session_id: string
  thoughts?: any[]
}

export const agentAPI = {
  /**
   * 普通对话
   */
  chat: (data: ChatRequest) =>
    api.post<any, ChatResponse>('/agent/chat', data),

  /**
   * 流式对话 (SSE)
   */
  chatStream: (data: ChatRequest): EventSource => {
    const sessionId = data.session_id || crypto.randomUUID()
    const params = new URLSearchParams({
      query: data.query,
      session_id: sessionId
    })

    return new EventSource(`/agent/chat/stream?${params}`)
  },

  /**
   * 获取可用工具列表
   */
  getTools: () =>
    api.get<any, ApiResponse<{ tools: string[], count: number }>>('/agent/tools')
}
