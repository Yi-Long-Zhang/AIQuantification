/** Vitest test setup — minimal configuration for Vue component tests */
import { config } from '@vue/test-utils'

// Stub global components used across the app
config.global.stubs = {
  'router-link': true,
  'router-view': true,
  'el-icon': true,
  'el-collapse': true,
  'el-collapse-item': true,
  'el-button': true,
  'el-input': true,
  'el-card': true,
  'el-row': true,
  'el-col': true,
  'el-tag': true,
  'el-table': true,
  'el-table-column': true,
}
