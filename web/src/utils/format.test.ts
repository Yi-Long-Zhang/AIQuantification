/**
 * 格式化工具函数单元测试
 */
import { describe, it, expect } from 'vitest'
import { formatNumber, formatLargeNumber, formatPercent, formatTime, formatDate, formatDateTime } from './format'

describe('formatNumber', () => {
  it('format 数字默认精度', () => {
    expect(formatNumber(1234.5678)).toBe('1,234.57')
  })

  it('format 数字自定义精度', () => {
    expect(formatNumber(1234.5678, 4)).toBe('1,234.5678')
  })

  it('format 整数', () => {
    expect(formatNumber(1000, 0)).toBe('1,000')
  })

  it('format 负数', () => {
    expect(formatNumber(-123.45)).toBe('-123.45')
  })
})

describe('formatLargeNumber', () => {
  it('format T 级别', () => {
    expect(formatLargeNumber(2_500_000_000_000)).toBe('2.50T')
  })

  it('format B 级别', () => {
    expect(formatLargeNumber(1_500_000_000)).toBe('1.50B')
  })

  it('format M 级别', () => {
    expect(formatLargeNumber(5_000_000)).toBe('5.00M')
  })

  it('format K 级别', () => {
    expect(formatLargeNumber(1_200)).toBe('1.20K')
  })

  it('format 小于 1000', () => {
    expect(formatLargeNumber(999)).toBe('999')
  })

  it('format 零', () => {
    expect(formatLargeNumber(0)).toBe('0')
  })
})

describe('formatPercent', () => {
  it('正数显示加号', () => {
    expect(formatPercent(5.5)).toBe('+5.50%')
  })

  it('负数显示减号', () => {
    expect(formatPercent(-3.2)).toBe('-3.20%')
  })

  it('自定义精度', () => {
    expect(formatPercent(1.2349, 3)).toBe('+1.235%')
  })
})

describe('formatTime', () => {
  it('返回时分秒', () => {
    const result = formatTime(new Date('2026-07-22T14:30:00').getTime())
    expect(result).toMatch(/\d{2}:\d{2}:\d{2}/)
  })
})

describe('formatDate', () => {
  it('返回年-月-日', () => {
    const result = formatDate(new Date('2026-07-22').getTime())
    expect(result).toContain('2026')
    expect(result).toContain('07')
  })
})

describe('formatDateTime', () => {
  it('返回日期和时间', () => {
    const result = formatDateTime(new Date('2026-07-22T14:30:00').getTime())
    expect(result).toContain('2026')
    expect(result).toContain('14')
  })
})
