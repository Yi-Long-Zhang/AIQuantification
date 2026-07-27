/**
 * BacktestResult 组件测试
 *
 * 该组件使用 el-table 的 scoped slot + lightweight-charts。
 * scoped slot 内容依赖 el-table 内部数据提供，无法通过 stub 模拟。
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BacktestResult from './BacktestResult.vue'

vi.mock('lightweight-charts', () => ({
  createChart: vi.fn(() => ({
    remove: vi.fn(),
    addLineSeries: vi.fn(() => ({ setData: vi.fn() })),
    timeScale: vi.fn(() => ({ fitContent: vi.fn() })),
  })),
  ColorType: { Solid: 'solid' },
  CrosshairMode: { Normal: 0 },
}))

function slotStub(tag: string) {
  return { template: `<div class="${tag}-mock"><slot /></div>` }
}

describe('BacktestResult', () => {
  const sampleResult = {
    strategy_name: 'sma_cross',
    symbol: 'AAPL',
    total_return: 15.2,
    annualized_return: 12.0,
    sharpe_ratio: 1.5,
    max_drawdown: -10.5,
    total_trades: 25,
    win_rate: 0.6,
  }

  it('有结果时组件正常挂载', () => {
    const wrapper = mount(BacktestResult, {
      props: { results: [sampleResult] },
      global: {
        stubs: {
          'el-table': slotStub('el-table'),
          'el-table-column': { template: '<div class="el-table-column-mock" />' },
          'el-progress': { template: '<div class="el-progress-mock" />' },
          'el-divider': { template: '<hr />' },
          'el-descriptions': slotStub('el-descriptions'),
          'el-descriptions-item': slotStub('el-descriptions-item'),
          'el-statistic': slotStub('el-statistic'),
          'el-icon': slotStub('el-icon'),
          'el-row': slotStub('el-row'),
          'el-col': slotStub('el-col'),
          'el-tag': slotStub('el-tag'),
        },
      },
    })
    expect(wrapper.find('.backtest-result').exists()).toBe(true)
  })

  it('有结果时渲染统计汇总区域', () => {
    const wrapper = mount(BacktestResult, {
      props: { results: [sampleResult] },
      global: {
        stubs: {
          'el-table': slotStub('el-table'),
          'el-table-column': { template: '<div class="el-table-column-mock" />' },
          'el-progress': { template: '<div class="el-progress-mock" />' },
          'el-divider': { template: '<hr />' },
          'el-descriptions': slotStub('el-descriptions'),
          'el-descriptions-item': slotStub('el-descriptions-item'),
          'el-statistic': slotStub('el-statistic'),
          'el-icon': slotStub('el-icon'),
          'el-row': slotStub('el-row'),
          'el-col': slotStub('el-col'),
          'el-tag': slotStub('el-tag'),
        },
      },
    })
    expect(wrapper.text()).toContain('净值曲线')
  })

  it('空结果时组件正常挂载', () => {
    const wrapper = mount(BacktestResult, {
      props: { results: [] },
      global: {
        stubs: {
          'el-table': slotStub('el-table'),
          'el-table-column': { template: '<div class="el-table-column-mock" />' },
          'el-empty': slotStub('el-empty'),
          'el-progress': { template: '<div class="el-progress-mock" />' },
          'el-divider': { template: '<hr />' },
          'el-descriptions': slotStub('el-descriptions'),
          'el-descriptions-item': slotStub('el-descriptions-item'),
          'el-statistic': slotStub('el-statistic'),
          'el-icon': slotStub('el-icon'),
          'el-row': slotStub('el-row'),
          'el-col': slotStub('el-col'),
          'el-tag': slotStub('el-tag'),
        },
      },
    })
    expect(wrapper.find('.backtest-result').exists()).toBe(true)
  })
})
