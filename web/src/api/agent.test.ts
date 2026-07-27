/**
 * agent.ts API 层单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { agentAPI } from './agent'
import api from './index'

vi.mock('./index', { default: { get: vi.fn(), post: vi.fn() } })

const mockApi = vi.mocked(api)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('agentAPI.chat', () => {
  it('调用 POST /agent/chat 并返回 ChatResponse', async () => {
    const mockResponse = { answer: '分析结果', session_id: 'sess-1' }
    mockApi.post.mockResolvedValue(mockResponse)

    const result = await agentAPI.chat({ query: '分析 AAPL' })

    expect(mockApi.post).toHaveBeenCalledWith('/agent/chat', { query: '分析 AAPL' })
    expect(result).toEqual(mockResponse)
  })

  it('支持传入 session_id', async () => {
    mockApi.post.mockResolvedValue({ answer: '', session_id: 'sess-1' })

    await agentAPI.chat({ query: '测试', session_id: 'sess-abc' })

    expect(mockApi.post).toHaveBeenCalledWith('/agent/chat', { query: '测试', session_id: 'sess-abc' })
  })
})

describe('agentAPI.chatStream', () => {
  beforeEach(() => {
    // jsdom 无 EventSource，用 mock 构造函数替代
    class MockEventSource {
      url: string
      readyState = 0
      onopen: unknown = null
      onmessage: unknown = null
      onerror: unknown = null
      CONNECTING = 0
      OPEN = 1
      CLOSED = 2
      constructor(url: string) { this.url = url }
      close() { /* noop */ }
      addEventListener = vi.fn()
      removeEventListener = vi.fn()
      dispatchEvent = vi.fn()
    }
    globalThis.EventSource = MockEventSource as unknown as typeof EventSource
  })

  it('返回 EventSource 实例', () => {
    const es = agentAPI.chatStream({ query: '分析 AAPL' })
    expect(es).toBeDefined()
    es.close()
  })

  it('不传 session_id 时自动生成', () => {
    const es = agentAPI.chatStream({ query: '测试' })
    expect(es.url).toContain('query=')
    expect(es.url).toContain('session_id=')
    es.close()
  })

  it('使用传入的 session_id', () => {
    const es = agentAPI.chatStream({ query: '测试', session_id: 'sess-fixed' })
    expect(es.url).toContain('session_id=sess-fixed')
    es.close()
  })
})

describe('agentAPI.getTools', () => {
  it('调用 GET /agent/tools', async () => {
    mockApi.get.mockResolvedValue({ data: { tools: ['tool1'], count: 1 } })

    const result = await agentAPI.getTools()

    expect(mockApi.get).toHaveBeenCalledWith('/agent/tools')
    expect(result.data?.tools).toEqual(['tool1'])
  })
})
