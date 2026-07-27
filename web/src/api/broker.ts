import api from './index'
import type {
  BrokerStatusResponse,
  BrokerConnectResult,
  BrokerOrdersResponse,
  BrokerListResponse,
} from '@/types'

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
}
