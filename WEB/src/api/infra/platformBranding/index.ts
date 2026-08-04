import { defHttp } from '@/utils/http/axios'

export interface PlatformBrandingVO {
  platformName?: string
  platformLogoFileId?: number | null
  platformLogo?: string
  dashboardTitle?: string
  loginName?: string
  loginLogoFileId?: number | null
  loginLogo?: string
  loginFormTitle?: string
  loginBgLightFileId?: number | null
  loginBgLight?: string
  loginBgDarkFileId?: number | null
  loginBgDark?: string
}

export interface PlatformBrandingSaveVO {
  platformName: string
  platformLogoFileId: number | null
  dashboardTitle: string
  loginName: string
  loginLogoFileId: number | null
  loginFormTitle: string
  loginBgLightFileId: number | null
  loginBgDarkFileId: number | null
}

export interface PlatformBrandingImageVO {
  fileId: number
  url: string
}

/** 未登录页面也需要读取；失败时由品牌配置 Hook 使用内置默认值兜底 */
export function getPlatformBranding() {
  return defHttp.get<PlatformBrandingVO>(
    { url: '/infra/platform-branding/get' },
    { errorMessageMode: 'none' },
  )
}

export function updatePlatformBranding(data: PlatformBrandingSaveVO) {
  return defHttp.put<PlatformBrandingVO>(
    { url: '/infra/platform-branding/update', data },
    { errorMessageMode: 'none' },
  )
}

export function resetPlatformBranding() {
  return defHttp.post<PlatformBrandingVO>(
    { url: '/infra/platform-branding/reset' },
    { errorMessageMode: 'none' },
  )
}

export function uploadPlatformBrandingImage(file: Blob, filename: string) {
  const data = new FormData()
  data.append('file', file, filename)
  return defHttp.post<PlatformBrandingImageVO>(
    { url: '/infra/platform-branding/image', data },
    { errorMessageMode: 'none' },
  )
}
