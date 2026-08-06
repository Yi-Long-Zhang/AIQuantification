/**
 * StrategyCard 组件测试
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StrategyCard from './StrategyCard.vue'
import type { Strategy } from '@/types'

describe('StrategyCard', () => {
  const baseProps = {
    strategy: {
      name: 'sma_cross',
      description: 'SMA 金叉死叉策略',
      type: '趋势',
      tags: ['均线', '趋势跟踪'],
      markets: ['us_stock', 'hk_stock'],
      risk_level: '低',
      params: { fast: '10', slow: '30' }
    }
  }

  function createWrapper(props: { strategy: Strategy }) {
    return mount(StrategyCard, {
      props,
      global: {
        stubs: {
          'el-card': { template: '<div class="el-card-stub"><slot /><slot name="footer" /></div>' },
          'el-tag': { template: '<span class="el-tag-stub"><slot /></span>' },
          'el-icon': { template: '<i class="el-icon-stub"><slot /></i>' },
          'el-button': { template: '<button class="el-button-stub" @click="$emit(\'click\', $event)"><slot /></button>' },
        }
      }
    })
  }

  it('渲染策略名称和描述', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('sma_cross')
    expect(wrapper.text()).toContain('SMA 金叉死叉策略')
  })

  it('渲染类型标签', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('趋势')
  })

  it('渲染标签列表', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('均线')
    expect(wrapper.text()).toContain('趋势跟踪')
  })

  it('渲染市场标签', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('美股')
    expect(wrapper.text()).toContain('港股')
  })

  it('渲染参数', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('fast=10')
    expect(wrapper.text()).toContain('slow=30')
  })

  it('渲染风险等级', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('低')
  })

  it('无 tags/markets/params/risk_level 时跳过对应区域', () => {
    const wrapper = createWrapper({
      strategy: { name: 'test', description: 'desc' }
    })
    expect(wrapper.text()).toContain('test')
    expect(wrapper.text()).toContain('desc')
  })

  it('点击按钮触发 use 事件', async () => {
    const wrapper = createWrapper(baseProps)
    const button = wrapper.find('.el-button-stub')
    await button.trigger('click')
    expect(wrapper.emitted('use')).toBeTruthy()
    expect(wrapper.emitted('use')![0][0]).toEqual(baseProps.strategy)
  })
})
