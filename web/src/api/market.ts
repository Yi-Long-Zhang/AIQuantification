import api from './index'
import type { MarketQuote, Kline, ApiResponse } from '@/types'

export interface MarketDataRequest {
  symbol: string
  market: string
  interval?: string
  period?: string
}

export const marketAPI = {
  /**
   * 获取市场概览
   */
  getOverview: (market: string) =>
    api.get<any, ApiResponse<MarketQuote[]>>(`/market/${market}/overview`),

  /**
   * 获取实时报价
   */
  getQuote: (symbol: string, market: string = 'us_stock') =>
    api.post<any, ApiResponse<MarketQuote>>('/market/quote', { symbol, market }),

  /**
   * 获取K线数据
   */
  getKlines: (params: MarketDataRequest) =>
    api.post<any, ApiResponse<Kline[]>>('/market/klines', params)
}
