import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.message

    if (status === 401) {
      ElMessage.error('未授权，请配置 API Key')
    } else if (status === 403) {
      ElMessage.error('API Key 无效或已撤销')
    } else if (status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试')
    } else if (status === 500) {
      ElMessage.error(`服务器错误: ${detail}`)
    } else {
      ElMessage.error(`请求失败: ${detail}`)
    }

    return Promise.reject(error)
  }
)

export default api
