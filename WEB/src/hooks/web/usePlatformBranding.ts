import { reactive, toRefs } from 'vue'
import type { PlatformBrandingVO } from '@/api/infra/platformBranding'
import {
  getPlatformBranding,
  resetPlatformBranding,
  updatePlatformBranding,
} from '@/api/infra/platformBranding'
import {
  clearPlatformBrandingConfig,
  getDefaultPlatformBranding,
  loadFabHiddenState,
  type PlatformBrandingConfig,
  saveFabHiddenState,
} from '@/utils/platformBrandingStorage'

const state = reactive({
  config: getDefaultPlatformBranding(),
  fabHidden: loadFabHiddenState(),
  defaults: getDefaultPlatformBranding(),
  loaded: false,
})

function escapeCssUrl(url: string): string {
  return url.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
}

// 浏览器标签页图标与平台 Logo 保持一致，保留 index.html 中的默认图标作为加载前兜底
function applyFavicon(logo: string): void {
  let favicon = document.querySelector<HTMLLinkElement>('link[rel~="icon"]')
  if (!favicon) {
    favicon = document.createElement('link')
    favicon.rel = 'icon'
    document.head.appendChild(favicon)
  }
  favicon.href = logo
}

function applyBrandingToDom(config: PlatformBrandingConfig): void {
  applyFavicon(config.platformLogo)

  const lightBg = escapeCssUrl(config.loginBgLight)
  const darkBg = escapeCssUrl(config.loginBgDark)
  // 登录组件直接消费变量，避免动态全局选择器被组件样式覆盖
  const rootStyle = document.documentElement.style
  rootStyle.setProperty('--platform-login-bg-light', `url("${lightBg}")`)
  rootStyle.setProperty('--platform-login-bg-dark', `url("${darkBg}")`)
}

applyBrandingToDom(state.config)

function pickText(value: string | undefined, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value : fallback
}

function mergeServerConfig(data: PlatformBrandingVO): PlatformBrandingConfig {
  const defaults = getDefaultPlatformBranding()
  return {
    platformName: pickText(data.platformName, defaults.platformName),
    platformLogo: pickText(data.platformLogo, defaults.platformLogo),
    platformLogoFileId: data.platformLogoFileId ?? null,
    dashboardTitle: pickText(data.dashboardTitle, defaults.dashboardTitle),
    loginName: pickText(data.loginName, defaults.loginName),
    loginLogo: pickText(data.loginLogo, defaults.loginLogo),
    loginLogoFileId: data.loginLogoFileId ?? null,
    loginFormTitle: typeof data.loginFormTitle === 'string' ? data.loginFormTitle : defaults.loginFormTitle,
    loginBgLight: pickText(data.loginBgLight, defaults.loginBgLight),
    loginBgLightFileId: data.loginBgLightFileId ?? null,
    loginBgDark: pickText(data.loginBgDark, defaults.loginBgDark),
    loginBgDarkFileId: data.loginBgDarkFileId ?? null,
  }
}

function applyServerConfig(data: PlatformBrandingVO): void {
  Object.assign(state.config, mergeServerConfig(data))
  applyBrandingToDom(state.config)
}

let loadPromise: Promise<boolean> | null = null

/** 数据库无表、无记录或接口不可用时保持内置默认配置 */
function loadConfig(): Promise<boolean> {
  if (loadPromise) {
    return loadPromise
  }
  loadPromise = getPlatformBranding()
    .then((data) => {
      applyServerConfig(data || {})
      clearPlatformBrandingConfig()
      state.loaded = true
      return true
    })
    .catch((error) => {
      console.warn('平台品牌配置读取失败，使用内置默认配置', error)
      state.loaded = true
      return false
    })
  return loadPromise
}

void loadConfig()

export function usePlatformBranding() {
  async function updateConfig(partial: Partial<PlatformBrandingConfig>): Promise<void> {
    const next = { ...state.config, ...partial }
    const saved = await updatePlatformBranding({
      platformName: next.platformName,
      platformLogoFileId: next.platformLogoFileId,
      dashboardTitle: next.dashboardTitle,
      loginName: next.loginName,
      loginLogoFileId: next.loginLogoFileId,
      loginFormTitle: next.loginFormTitle,
      loginBgLightFileId: next.loginBgLightFileId,
      loginBgDarkFileId: next.loginBgDarkFileId,
    })
    applyServerConfig(saved)
  }

  async function resetConfig(): Promise<void> {
    const saved = await resetPlatformBranding()
    applyServerConfig(saved)
    clearPlatformBrandingConfig()
  }

  function setFabHidden(hidden: boolean): void {
    state.fabHidden = hidden
    saveFabHiddenState(hidden)
  }

  return {
    ...toRefs(state),
    updateConfig,
    resetConfig,
    loadConfig,
    setFabHidden,
  }
}
