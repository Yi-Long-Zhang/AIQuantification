/**
 * SSE 工具单元测试
 */
import { describe, it, expect, vi } from 'vitest'
import { StreamAggregator } from './sse'

describe('StreamAggregator', () => {
  it('初始内容为空', () => {
    const agg = new StreamAggregator()
    expect(agg.getContent()).toBe('')
  })

  it('添加数据块累积内容', () => {
    const agg = new StreamAggregator()
    agg.add('Hello')
    agg.add(' World')
    expect(agg.getContent()).toBe('Hello World')
  })

  it('onChange 回调正确触发', () => {
    const agg = new StreamAggregator()
    const callback = vi.fn()
    agg.onChange(callback)
    agg.add('test')
    expect(callback).toHaveBeenCalledWith('test')
  })

  it('onChange 多次触发累积', () => {
    const agg = new StreamAggregator()
    const callback = vi.fn()
    agg.onChange(callback)
    agg.add('a')
    agg.add('b')
    expect(callback).toHaveBeenCalledTimes(2)
    expect(callback).toHaveBeenLastCalledWith('ab')
  })

  it('clear 清空缓冲区', () => {
    const agg = new StreamAggregator()
    agg.add('data')
    agg.clear()
    expect(agg.getContent()).toBe('')
  })

  it('多个回调都收到通知', () => {
    const agg = new StreamAggregator()
    const cb1 = vi.fn()
    const cb2 = vi.fn()
    agg.onChange(cb1)
    agg.onChange(cb2)
    agg.add('hello')
    expect(cb1).toHaveBeenCalledWith('hello')
    expect(cb2).toHaveBeenCalledWith('hello')
  })
})
