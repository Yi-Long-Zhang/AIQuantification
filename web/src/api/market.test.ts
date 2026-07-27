/**
 * market.ts API 层单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { marketAPI } from './market'
import api from './index'

vi.mock('./index', { default: { get: vi.fn(), post: vi.fn() } })

const mockApi = vi.mocked(api)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('marketAPI.getOverview', () => {
  it('调用 GET /market/{market}/overview', async () => {
    const mockData = {
      data: [
        { symbol: 'AAPL', price: 150, change: 2.5, change_percent: 1.5, volume: 1000000 }
      ]
    }
    mockApi.get.mockResolvedValue(mockData)

    const result = await marketAPI.getOverview('us_stock')

    expect(mockApi.get).toHaveBeenCalledWith('/market/us_stock/overview')
    expect(result.data).toHaveLength(1)
    expect(result.data?.[0].symbol).toBe('AAPL')
  })
})

describe('marketAPI.getQuote', () => {
  it('调用 POST /market/quote', async () => {
    mockApi.post.mockResolvedValue({
      data: { symbol: 'AAPL', price: 150, change: 2.5, change_percent: 1.5, volume: 1000000 }
    })

    const result = await marketAPI.getQuote('AAPL')

    expect(mockApi.post).toHaveBeenCalledWith('/market/quote', { symbol: 'AAPL', market: 'us_stock' })
    expect(result.data?.symbol).toBe('AAPL')
  })

  it('支持指定市场', async () => {
    mockApi.post.mockResolvedValue({ data: { symbol: '0700', price: 400, change: 5, change_percent: 1.2, volume: 500000 } })

    const result = await marketAPI.getQuote('0700', 'hk_stock')

    expect(mockApi.post).toHaveBeenCalledWith('/market/quote', { symbol: '0700', market: 'hk_stock' })
    expect(result.data?.price).toBe(400)
  })
})

describe('marketAPI.getKlines', () => {
  it('调用 POST /market/klines', async () => {
    const mockKlines = [
      { Date: '2024-01-01', Open: 150, High: 155, Low: 148, Close: 153, Volume: 1000000 }
    ]
    mockApi.post.mockResolvedValue(mockKlines)

    const result = await marketAPI.getKlines('AAPL')

    expect(mockApi.post).toHaveBeenCalledWith('/market/klines', {
      symbol: 'AAPL', market: 'us_stock', interval: '1d', period: '1y'
    })
    expect(result).toHaveLength(1)
    expect(result[0].Date).toBe('2024-01-01')
  })

  it('支持自定义周期', async () => {
    mockApi.post.mockResolvedValue([])

    await marketAPI.getKlines('BTC', 'crypto', '1h', '3mo')

    expect(mockApi.post).toHaveBeenCalledWith('/market/klines', {
      symbol: 'BTC', market: 'crypto', interval: '1h', period: '3mo'
    })
  })
})
