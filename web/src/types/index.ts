// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  tool_calls?: ToolCall[]
}

// 工具调用
export interface ToolCall {
  tool: string
  args: Record<string, any>
  result?: any
}

// 市场行情
export interface MarketQuote {
  symbol: string
  name?: string
  price: number
  change: number
  change_percent: number
  volume: number
  market_cap?: number
}

// 回测结果
export interface BacktestResult {
  strategy_name: string
  symbol: string
  total_return: number
  annualized_return: number
  sharpe_ratio: number
  max_drawdown: number
  total_trades: number
  win_rate: number
}

// K线数据
export interface Kline {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// 策略信息
export interface Strategy {
  name: string
  description: string
  parameters?: Record<string, any>
}

// 技能信息
export interface Skill {
  name: string
  description: string
  tools: string[]
  tool_params: Record<string, any>
  prompt_template: string
  tags: string[]
}

// API响应
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}
