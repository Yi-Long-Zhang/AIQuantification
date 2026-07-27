/**
 * skills.ts API 层单元测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { skillsAPI } from './skills'
import api from './index'

vi.mock('./index', { default: { get: vi.fn(), post: vi.fn() } })

const mockApi = vi.mocked(api)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('skillsAPI.getSkills', () => {
  it('调用 GET /skills', async () => {
    const mockSkills = {
      data: {
        skills: [
          { name: 'industry_rotation', description: '行业轮动分析', tools: ['get_sector_rotation'], tool_params: {}, prompt_template: '', tags: ['宏观'] }
        ]
      }
    }
    mockApi.get.mockResolvedValue(mockSkills)

    const result = await skillsAPI.getSkills()

    expect(mockApi.get).toHaveBeenCalledWith('/skills')
    expect(result.data?.skills).toHaveLength(1)
    expect(result.data?.skills[0].name).toBe('industry_rotation')
  })

  it('空技能列表', async () => {
    mockApi.get.mockResolvedValue({ data: { skills: [] } })

    const result = await skillsAPI.getSkills()

    expect(result.data?.skills).toEqual([])
  })
})
