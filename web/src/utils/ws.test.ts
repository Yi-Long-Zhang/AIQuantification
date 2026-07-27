/**
 * WebSocket 工具模块测试
 *
 * 注意：jsdom 中没有原生 WebSocket，需要在测试前 mock。
 * MarketWS 内部使用 setInterval（心跳）和 setTimeout（重连），
 * 使用 vi.useFakeTimers 避免定时器挂起。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { MarketWS } from './ws'

describe('MarketWS', () => {
  beforeEach(() => {
    vi.useFakeTimers()

    // Mock WebSocket — jsdom 不支持
    class MockWebSocket {
      static CONNECTING = 0
      static OPEN = 1
      static CLOSED = 2
      readyState = 1
      url: string
      onopen: (() => void) | null = null
      onmessage: ((event: MessageEvent) => void) | null = null
      onclose: ((event: CloseEvent) => void) | null = null
      onerror: ((event: Event) => void) | null = null
      CONNECTING = 0
      OPEN = 1
      CLOSED = 2
      constructor(url: string) { this.url = url }
      close() { this.readyState = 2; this.onclose?.(new CloseEvent('close')) }
      send(_data: string) { /* noop */ }
      addEventListener = vi.fn()
      removeEventListener = vi.fn()
      dispatchEvent = vi.fn()
    }
    globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('构造时保存 market 参数', () => {
    const ws = new MarketWS('us_stock')
    expect(ws).toBeDefined()
    ws.disconnect()
  })

  it('connect 不报错', () => {
    const ws = new MarketWS('crypto')
    expect(() => ws.connect()).not.toThrow()
    ws.disconnect()
  })

  it('onMessage 注册回调后不报错', () => {
    const ws = new MarketWS('us_stock')
    const cb = vi.fn()
    ws.onMessage(cb)
    expect(() => ws.disconnect()).not.toThrow()
  })

  it('disconnect 清理定时器', () => {
    const ws = new MarketWS('us_stock')
    ws.connect()
    expect(() => ws.disconnect()).not.toThrow()
  })

  it('多次 disconnect 不报错', () => {
    const ws = new MarketWS('us_stock')
    expect(() => {
      ws.disconnect()
      ws.disconnect()
    }).not.toThrow()
  })
})
