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
  args: Record<string, unknown>
  result?: unknown
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
  type?: string
  tags?: string[]
  markets?: string[]
  params?: Record<string, string>
  risk_level?: string
  parameters?: Record<string, string | number | boolean>
}

// 技能信息
export interface Skill {
  name: string
  description: string
  tools: string[]
  tool_params: Record<string, unknown>
  prompt_template: string
  tags: string[]
}

// API响应
export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}

// ── Broker 类型 ──────────────────────────────────────────────────────────────

/** 券商列表条目 */
export interface BrokerInfo {
  name: string
  connected: boolean
}

/** 账户信息 */
export interface BrokerAccount {
  broker: string
  account_id: string
  cash: number
  equity: number
  buying_power: number
  currency: string
  status: string
  timestamp: string
}

/** 持仓信息 */
export interface BrokerPosition {
  symbol: string
  qty: number
  avg_entry_price: number
  current_price: number
  market_value: number
  unrealized_pl: number
  unrealized_pl_pct: number
  asset_class: string
}

/** 订单信息 */
export interface BrokerOrder {
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

/** 券商状态响应 */
export interface BrokerStatusResponse {
  name: string
  connected: boolean
  error?: string
  account?: BrokerAccount
  positions?: BrokerPosition[]
}

/** 券商连接结果 */
export interface BrokerConnectResult {
  name: string
  connected: boolean
}

/** 券商列表响应 */
export interface BrokerListResponse {
  brokers: BrokerInfo[]
  count: number
}

/** 券商订单列表响应 */
export interface BrokerOrdersResponse {
  orders: BrokerOrder[]
  count: number
}

// ── Agent 类型 ───────────────────────────────────────────────────────────────

/** 工具调用思维 */
export interface Thought {
  tool: string
  args: Record<string, unknown>
  result?: unknown
  timestamp?: number
}

// ── Multi-Agent 类型 ─────────────────────────────────────────────────────────

/** 多 Agent 状态 */
export interface MultiAgentStatus {
  coordinator: string
  registered_agents?: string[]
  broker_stats?: BrokerStats
  execution_summary?: ExecutionSummary
}

/** Broker 消息统计 */
export interface BrokerStats {
  registered_agents: number
  agents: string[]
  total_messages: number
  messages_by_type: Record<string, number>
  messages_by_agent: Record<string, number>
  queue_sizes: Record<string, number>
}

/** Agent 执行统计 */
export interface ExecutionSummary {
  agent: string
  total_tasks: number
  successful: number
  failed: number
  success_rate: number
}

/** 多 Agent 消息（后端 to_dict 字段） */
export interface AgentMessage {
  message_id: string
  from_agent: string
  to_agent: string
  message_type: string
  content: unknown
  priority: string
  correlation_id?: string | null
  timestamp: string
}

/** 交易周期结果 */
export interface CycleResult {
  cycle_id: string
  market: string
  status: string
  elapsed_seconds: number
  research: unknown
  strategy: unknown
  risk: unknown
  final_decision: {
    decisions?: Decision[]
    market_view?: string
    overall_confidence?: number
    risk_approved?: boolean
    action?: string
    reasoning?: string
  }
  execution?: Record<string, unknown>
  timestamp: string
  error?: string
}

/** AI 交易决策 */
export interface Decision {
  symbol: string
  action: string
  confidence: number
  entry_price?: number
  stop_loss?: number
  take_profit?: number
  reasoning?: string
}
