/**
 * MarketCard 组件测试
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MarketCard from './MarketCard.vue'
import type { MarketQuote } from '@/types'

describe('MarketCard', () => {
  const baseProps = {
    data: {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 150.50,
      change: 2.5,
      change_percent: 1.68,
      volume: 100000000,
      market_cap: 2500000000000
    }
  }

  function createWrapper(props: { data: MarketQuote }) {
    return mount(MarketCard, {
      props,
      global: {
        stubs: {
          'el-card': { template: '<div class="el-card-stub"><slot /></div>' },
          'el-icon': { template: '<i class="el-icon-stub"><slot /></i>' },
        }
      }
    })
  }

  it('渲染股票代码', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('AAPL')
  })

  it('渲染名称', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('Apple Inc.')
  })

  it('渲染价格', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('150.50')
  })

  it('渲染涨跌幅', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('+1.68%')
  })

  it('渲染成交量', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('100.00M')
  })

  it('渲染市值', () => {
    const wrapper = createWrapper(baseProps)
    expect(wrapper.text()).toContain('2.50T')
  })

  it('负值显示减号', () => {
    const wrapper = createWrapper({
      data: { ...baseProps.data, change: -3.2, change_percent: -2.1 }
    })
    expect(wrapper.text()).toContain('-2.10%')
  })
})
