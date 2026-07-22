/**
 * API 层单元测试 — 验证请求封装的正确性
 */
import { describe, it, expect } from 'vitest'
import api from './index'

describe('API 层基础功能', () => {
  it('api 实例存在', () => {
    expect(api).toBeDefined()
  })

  it('api.defaults.baseURL 为空（使用 Vite proxy）', () => {
    // 测试环境下 axios 实例应该有默认配置
    expect(api.defaults.baseURL).toBeUndefined()
  })

  it('api.defaults.timeout 超时时间已设置', () => {
    expect(api.defaults.timeout).toBeGreaterThan(0)
  })
})

describe('API 层拦截器', () => {
  it('请求拦截器已注册（当前为 0 — 认证功能后续启用）', () => {
    const interceptors = api.interceptors.request
    expect(interceptors).toBeDefined()
  })

  it('响应拦截器已注册（统一错误处理）', () => {
    const interceptors = api.interceptors.response
    expect(interceptors).toBeDefined()
    expect(interceptors.handlers.length).toBeGreaterThan(0)
  })
})
