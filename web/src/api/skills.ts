import api from './index'
import type { Skill, ApiResponse } from '@/types'

export const skillsAPI = {
  /**
   * 获取技能列表
   */
  getSkills: () =>
    api.get<any, ApiResponse<{ skills: Skill[] }>>('/skills'),
}
