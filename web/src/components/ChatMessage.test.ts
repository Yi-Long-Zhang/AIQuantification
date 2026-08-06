/**
 * ChatMessage 组件单元测试
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from './ChatMessage.vue'
import type { Message } from '@/types'

describe('ChatMessage.vue', () => {
  const userMsg = (content: string): Message => ({
    id: 'm1', role: 'user', content, timestamp: Date.now(),
  })
  const aiMsg = (content: string): Message => ({
    id: 'm2', role: 'assistant', content, timestamp: Date.now(),
  })

  it('渲染用户消息', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: userMsg('分析 AAPL') },
    })
    expect(wrapper.text()).toContain('分析 AAPL')
  })

  it('渲染 AI 消息', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: aiMsg('AAPL 当前趋势看涨') },
    })
    expect(wrapper.text()).toContain('AAPL')
  })

  it('用户消息添加 user 类', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: userMsg('test') },
    })
    expect(wrapper.classes()).toContain('user')
  })

  it('AI 消息添加 assistant 类', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: aiMsg('test') },
    })
    expect(wrapper.classes()).toContain('assistant')
  })
})
