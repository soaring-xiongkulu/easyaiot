import defaultLogo from '@/assets/images/logo.png'
import defaultLightBg from '@/assets/images/light-bg.png'
import defaultDarkBg from '@/assets/images/dark-bg.png'

const PLATFORM_BRANDING_STORAGE_KEY = 'PLATFORM_BRANDING_CONFIG'
export const PLATFORM_BRANDING_FAB_HIDDEN_KEY = 'PLATFORM_BRANDING_FAB_HIDDEN'

export interface PlatformBrandingConfig {
  /** 管理后台平台名称（侧边栏、浏览器标题等） */
  platformName: string
  /** 管理后台平台 Logo */
  platformLogo: string
  /** 管理后台平台 Logo 文件编号，空值表示使用内置默认图片 */
  platformLogoFileId: number | null
  /** 大屏顶部标题 */
  dashboardTitle: string
  /** 登录页左侧名称 */
  loginName: string
  /** 登录页 Logo */
  loginLogo: string
  /** 登录页 Logo 文件编号，空值表示使用内置默认图片 */
  loginLogoFileId: number | null
  /** 登录表单标题，留空则使用 i18n 默认文案 */
  loginFormTitle: string
  /** 登录页浅色背景 */
  loginBgLight: string
  /** 登录页浅色背景文件编号，空值表示使用内置默认图片 */
  loginBgLightFileId: number | null
  /** 登录页深色背景 */
  loginBgDark: string
  /** 登录页深色背景文件编号，空值表示使用内置默认图片 */
  loginBgDarkFileId: number | null
}

export function getDefaultPlatformBranding(): PlatformBrandingConfig {
  const envTitle = import.meta.env.VITE_GLOB_APP_TITLE || '云边端一体化智能算法应用平台'
  return {
    platformName: envTitle,
    platformLogo: defaultLogo,
    platformLogoFileId: null,
    dashboardTitle: '云边端一体算法预警监控平台',
    loginName: envTitle,
    loginLogo: defaultLogo,
    loginLogoFileId: null,
    loginFormTitle: '',
    loginBgLight: defaultLightBg,
    loginBgLightFileId: null,
    loginBgDark: defaultDarkBg,
    loginBgDarkFileId: null,
  }
}

/** 服务端配置加载成功后清除历史浏览器品牌数据，避免旧值再次成为配置来源 */
export function clearPlatformBrandingConfig(): void {
  try {
    window.localStorage.removeItem(PLATFORM_BRANDING_STORAGE_KEY)
  }
  catch (error) {
    console.error(error)
  }
}

export function loadFabHiddenState(): boolean {
  return readJson(PLATFORM_BRANDING_FAB_HIDDEN_KEY) === true
}

export function saveFabHiddenState(hidden: boolean): void {
  writeJson(PLATFORM_BRANDING_FAB_HIDDEN_KEY, hidden)
}

/** 使用原生 JSON，避免通用 storage 工具在退出登录时被一并清空后的二次解析问题 */
function readJson(key: string): unknown {
  try {
    const item = window.localStorage.getItem(key)
    if (!item)
      return null
    return JSON.parse(item)
  }
  catch (error) {
    console.error(error)
    return null
  }
}

function writeJson(key: string, value: unknown): boolean {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
    return true
  }
  catch (error) {
    console.error(error)
    return false
  }
}
