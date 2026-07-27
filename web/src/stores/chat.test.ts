/**
 * chat store 单元测试
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from './chat'

describe('chat store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态 — 空消息、未加载', () => {
    const store = useChatStore()
    expect(store.messages).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.sessionId).toBeTruthy()
  })

  it('addMessage 添加用户消息', () => {
    const store = useChatStore()
    store.addMessage({ role: 'user', content: '分析 AAPL' })

    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('user')
    expect(store.messages[0].content).toBe('分析 AAPL')
    expect(store.messages[0].id).toBeTruthy()
    expect(store.messages[0].timestamp).toBeGreaterThan(0)
  })

  it('addMessage 添加助手消息', () => {
    const store = useChatStore()
    store.addMessage({ role: 'assistant', content: '分析完成' })

    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].role).toBe('assistant')
  })

  it('addMessage 支持 tool_calls', () => {
    const store = useChatStore()
    store.addMessage({
      role: 'assistant',
      content: '正在分析...',
      tool_calls: [{ tool: 'get_stock_quote', args: { symbol: 'AAPL' } }]
    })

    expect(store.messages[0].tool_calls).toHaveLength(1)
    expect(store.messages[0].tool_calls![0].tool).toBe('get_stock_quote')
  })

  it('updateLastMessage 更新最后一条消息', () => {
    const store = useChatStore()
    store.addMessage({ role: 'user', content: '测试' })
    store.addMessage({ role: 'assistant', content: '完' })

    store.updateLastMessage('完成')

    expect(store.messages[1].content).toBe('完成')
  })

  it('updateLastMessage 跳过用户消息', () => {
    const store = useChatStore()
    store.addMessage({ role: 'user', content: '测试' })

    store.updateLastMessage('新内容')

    expect(store.messages[0].content).toBe('测试')
  })

  it('updateLastMessage 空消息列表不报错', () => {
    const store = useChatStore()
    expect(() => store.updateLastMessage('内容')).not.toThrow()
  })

  it('clearMessages 清空并重置 session', () => {
    const store = useChatStore()
    const oldSessionId = store.sessionId

    store.addMessage({ role: 'user', content: '测试' })
    store.clearMessages()

    expect(store.messages).toEqual([])
    expect(store.sessionId).not.toBe(oldSessionId)
  })
})
