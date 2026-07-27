import api from './index'
import type { MarketQuote, ApiResponse } from '@/types'

/** 原始K线数据行（字段名因数据源而异） */
export type KlineRow = Record<string, string | number>

export interface MarketDataRequest {
  symbol: string
  market: string
  interval?: string
  period?: string
}

export const marketAPI = {
  /** 获取市场概览 */
  getOverview: (market: string) =>
    api.get<never, ApiResponse<MarketQuote[]>>(`/market/${market}/overview`),

  /** 获取实时报价 */
  getQuote: (symbol: string, market: string = 'us_stock') =>
    api.post<MarketDataRequest, ApiResponse<MarketQuote>>('/market/quote', { symbol, market }),

  /** 获取K线数据 */
  getKlines: (symbol: string, market: string = 'us_stock', interval: string = '1d', period: string = '1y') =>
    api.post<MarketDataRequest, KlineRow[]>('/market/klines', { symbol, market, interval, period })
}
