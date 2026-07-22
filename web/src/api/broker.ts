import api from './index'

export const brokerAPI = {
  /** 获取券商列表 */
  listBrokers: () => api.get<any, { brokers: any[]; count: number }>('/broker/list'),

  /** 获取券商状态 */
  getBrokerStatus: (name: string) => api.get<any, any>(`/broker/${name}/status`),

  /** 连接券商 */
  connectBroker: (name: string) => api.post<any, any>(`/broker/${name}/connect`),

  /** 获取订单 */
  getOrders: (name: string, status?: string) =>
    api.get<any, any>(`/broker/${name}/orders`, { params: { status } }),
}
