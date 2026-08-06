/**
 * broker.ts API 层单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { brokerAPI } from './broker'
import api from './index'

vi.mock('./index', () => ({ default: { get: vi.fn(), post: vi.fn() } }))

const mockApi = vi.mocked(api)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('brokerAPI.listBrokers', () => {
  it('调用 GET /broker/list', async () => {
    mockApi.get.mockResolvedValue({ brokers: [{ name: 'alpaca', connected: false }], count: 1 })

    const result = await brokerAPI.listBrokers()

    expect(mockApi.get).toHaveBeenCalledWith('/broker/list')
    expect(result.brokers).toHaveLength(1)
    expect(result.brokers[0].name).toBe('alpaca')
    expect(result.count).toBe(1)
  })
})

describe('brokerAPI.getBrokerStatus', () => {
  it('调用 GET /broker/{name}/status', async () => {
    mockApi.get.mockResolvedValue({ name: 'alpaca', connected: true, account: { account_id: 'acc1', cash: 50000, equity: 60000, buying_power: 100000, broker: 'alpaca', currency: 'USD', status: 'ACTIVE', timestamp: '2024-01-01' }, positions: [] })

    const result = await brokerAPI.getBrokerStatus('alpaca')

    expect(mockApi.get).toHaveBeenCalledWith('/broker/alpaca/status')
    expect(result.connected).toBe(true)
    expect(result.account?.account_id).toBe('acc1')
  })

  it('未连接的券商', async () => {
    mockApi.get.mockResolvedValue({ name: 'alpaca', connected: false })

    const result = await brokerAPI.getBrokerStatus('alpaca')

    expect(result.connected).toBe(false)
  })
})

describe('brokerAPI.connectBroker', () => {
  it('调用 POST /broker/{name}/connect', async () => {
    mockApi.post.mockResolvedValue({ name: 'alpaca', connected: true })

    const result = await brokerAPI.connectBroker('alpaca')

    expect(mockApi.post).toHaveBeenCalledWith('/broker/alpaca/connect')
    expect(result.connected).toBe(true)
  })
})

describe('brokerAPI.getOrders', () => {
  it('调用 GET /broker/{name}/orders（不带状态过滤）', async () => {
    mockApi.get.mockResolvedValue({ orders: [], count: 0 })

    const result = await brokerAPI.getOrders('alpaca')

    expect(mockApi.get).toHaveBeenCalledWith('/broker/alpaca/orders', { params: { status: undefined } })
    expect(result.orders).toEqual([])
  })

  it('支持按状态过滤', async () => {
    mockApi.get.mockResolvedValue({ orders: [{ order_id: 'ord1', symbol: 'AAPL', side: 'buy', qty: 10, filled_qty: 10, price: 150, avg_fill_price: 150, status: 'filled', type: 'market', created_at: '2024-01-01' }], count: 1 })

    const result = await brokerAPI.getOrders('alpaca', 'filled')

    expect(mockApi.get).toHaveBeenCalledWith('/broker/alpaca/orders', { params: { status: 'filled' } })
    expect(result.orders).toHaveLength(1)
    expect(result.orders[0].status).toBe('filled')
  })
})
