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

export interface DryRunDecision {
  symbol: string
  action: string
  confidence: number
  entry_price?: number
}

export interface DryRunItem {
  status: string
  reason?: string | null
  symbol: string
  action?: string
  confidence?: number
  price?: number
  qty?: number
  notional?: number
  order_id?: string
  order_status?: string
}

export interface DryRunResponse {
  dry_run: boolean
  timestamp: string
  decisions_seen: number
  orders_planned: number
  orders_filled: number
  orders_rejected: number
  items: DryRunItem[]
}

export interface PaperOrderResult {
  order_id: string
  symbol: string
  side: string
  qty: number
  filled_qty: number
  price: number | null
  avg_fill_price: number | null
  status: string
  type: string
  created_at: string
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

  /** 执行演练：预览决策会产生的订单 */
  dryRun: (market: string, decisions: DryRunDecision[]) =>
    api.post<never, DryRunResponse>('/execution/dry-run', { market, decisions }),

  /** PaperBroker 手动下单 */
  submitOrder: (data: { symbol: string; side: string; qty: number; order_type?: string; price?: number | null }) =>
    api.post<never, PaperOrderResult>('/broker/paper/order', data),
}
