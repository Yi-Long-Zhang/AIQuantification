import api from './index'
import type { BacktestResult, Strategy, ApiResponse } from '@/types'

export interface BacktestRequest {
  strategy_name: string
  symbols: string[]
  start_date: string
  end_date: string
  initial_capital: number
  parameters?: Record<string, any>
}

export const backtestAPI = {
  /**
   * 获取策略列表
   */
  getStrategies: () =>
    api.get<any, ApiResponse<{ strategies: Strategy[] }>>('/strategies'),

  /**
   * 运行回测
   */
  runBacktest: (data: BacktestRequest) =>
    api.post<any, BacktestResult[]>('/backtest', data)
}
