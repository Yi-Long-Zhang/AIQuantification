/**
 * backtest.ts API 层单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { backtestAPI } from './backtest'
import api from './index'

vi.mock('./index', { default: { get: vi.fn(), post: vi.fn() } })

const mockApi = vi.mocked(api)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('backtestAPI.getStrategies', () => {
  it('调用 GET /strategies', async () => {
    const mockStrategies = {
      data: {
        strategies: [
          { name: 'sma_cross', description: 'SMA 金叉死叉', type: '趋势' },
        ]
      }
    }
    mockApi.get.mockResolvedValue(mockStrategies)

    const result = await backtestAPI.getStrategies()

    expect(mockApi.get).toHaveBeenCalledWith('/strategies')
    expect(result.data?.strategies).toHaveLength(1)
    expect(result.data?.strategies[0].name).toBe('sma_cross')
  })

  it('空策略列表', async () => {
    mockApi.get.mockResolvedValue({ data: { strategies: [] } })

    const result = await backtestAPI.getStrategies()

    expect(result.data?.strategies).toEqual([])
  })
})

describe('backtestAPI.runBacktest', () => {
  it('调用 POST /backtest', async () => {
    const mockResults = [
      { strategy_name: 'sma_cross', symbol: 'AAPL', total_return: 15.2, sharpe_ratio: 1.5, max_drawdown: -10, total_trades: 20, win_rate: 0.6, annualized_return: 12.0 }
    ]
    mockApi.post.mockResolvedValue(mockResults)

    const result = await backtestAPI.runBacktest({
      strategy_name: 'sma_cross',
      symbols: ['AAPL'],
      start_date: '2024-01-01',
      end_date: '2025-01-01',
      initial_capital: 100000
    })

    expect(mockApi.post).toHaveBeenCalledWith('/backtest', {
      strategy_name: 'sma_cross',
      symbols: ['AAPL'],
      start_date: '2024-01-01',
      end_date: '2025-01-01',
      initial_capital: 100000
    })
    expect(result).toHaveLength(1)
    expect(result[0].total_return).toBe(15.2)
  })

  it('支持传入可选参数 parameters', async () => {
    mockApi.post.mockResolvedValue([])

    await backtestAPI.runBacktest({
      strategy_name: 'sma_cross',
      symbols: ['AAPL'],
      start_date: '2024-01-01',
      end_date: '2025-01-01',
      initial_capital: 100000,
      parameters: { fast: 10, slow: 30 }
    })

    expect(mockApi.post).toHaveBeenCalledWith('/backtest', expect.objectContaining({
      parameters: { fast: 10, slow: 30 }
    }))
  })
})
