import type { ConfigProviderThemeVars } from '@wot-ui/ui/components/wd-config-provider/types'

import { defineStore } from 'pinia'

/**
 * EasyAIoT 品牌色板（wot 2.x 主色阶 primary1-10，primary6 为主色）
 * 深邃科技蓝，专业、冷静、聚焦，适合 IoT 管控场景
 */
const BRAND_PRIMARY = {
  primary1: '#eaefff', // 浅底/选中底
  primary2: '#d3e0ff',
  primary3: '#aec6ff',
  primary4: '#84a9ff',
  primary5: '#5987ff',
  primary6: '#2f6bff', // 主色
  primary7: '#2658d9', // 点击态
  primary8: '#1d46b3',
  primary9: '#15348c',
  primary10: '#0d2265',
}

export const useThemeStore = defineStore(
  'theme-store',
  () => {
    /** 主题 */
    const theme = ref<'light' | 'dark'>('light')

    /** 主题变量（persist 持久化的是旧数据时也会被下方默认值兜底重建） */
    const themeVars = ref<ConfigProviderThemeVars>({
      ...BRAND_PRIMARY,
      // 主按钮
      buttonPrimaryBg: BRAND_PRIMARY.primary6,
      buttonPrimaryBgActive: BRAND_PRIMARY.primary7,
      // 导航栏
      navbarBg: '#ffffff',
    })

    /** 设置主题变量 */
    const setThemeVars = (partialVars: Partial<ConfigProviderThemeVars>) => {
      themeVars.value = { ...themeVars.value, ...partialVars }
    }

    /** 切换主题 */
    const toggleTheme = () => {
      theme.value = theme.value === 'light' ? 'dark' : 'light'
    }

    return {
      /** 设置主题变量 */
      setThemeVars,
      /** 切换主题 */
      toggleTheme,
      /** 主题变量 */
      themeVars,
      /** 主题 */
      theme,
    }
  },
  {
    persist: true,
  },
)
