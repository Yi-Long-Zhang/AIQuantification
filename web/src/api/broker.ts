import api from './index'
import type {
  BrokerStatusResponse,
  BrokerConnectResult,
  BrokerOrdersResponse,
  BrokerListResponse,
} from '@/types'

export interface PaperSummary {
  initial_capital: number
  cash: number
  equity: number
  unrealized_pnl: number
  total_realized_pnl: number
  total_return_pct: number
  positions: {
    symbol: string
    qty: number
    avg_entry: number
    current_price: number
    market_value: number
    unrealized_pnl: number
  }[]
  open_orders: number
  total_trades: number
}

export interface PaperTrade {
  trade_id: string
  symbol: string
  side: string
  qty: number
  price: number
  realized_pl: number | null
  commission: number | null
  timestamp: string
}

export interface PaperTradesResponse {
  trades: PaperTrade[]
  count: number
}

export interface PaperEquityResponse {
  history: { time: string; equity: number }[]
  count: number
}

export const brokerAPI = {
  /** 获取券商列表 */
  listBrokers: () =>
    api.get<never, BrokerListResponse>('/broker/list'),

  /** 获取券商状态 */
  getBrokerStatus: (name: string) =>
    api.get<never, BrokerStatusResponse>(`/broker/${name}/status`),

  /** 连接券商 */
  connectBroker: (name: string) =>
    api.post<never, BrokerConnectResult>(`/broker/${name}/connect`),

  /** 获取订单 */
  getOrders: (name: string, status?: string) =>
    api.get<never, BrokerOrdersResponse>(`/broker/${name}/orders`, { params: { status } }),

  /** PaperBroker 摘要 */
  getPaperSummary: () =>
    api.get<never, PaperSummary>('/broker/paper/summary'),

  /** PaperBroker 交易记录 */
  getPaperTrades: (limit: number = 50) =>
    api.get<never, PaperTradesResponse>('/broker/paper/trades', { params: { limit } }),

  /** PaperBroker 权益历史 */
  getPaperEquity: (limit: number = 500) =>
    api.get<never, PaperEquityResponse>('/broker/paper/equity', { params: { limit } }),
}
