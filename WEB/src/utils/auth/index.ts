import type { BasicKeys } from '@/utils/cache/persistent'
import { Persistent } from '@/utils/cache/persistent'
import { ACCESS_TOKEN_KEY, CacheTypeEnum, REFRESH_TOKEN_KEY, TENANT_ID_KEY } from '@/enums/cacheEnum'
import projectSetting from '@/settings/projectSetting'

const REMEMBER_ME_KEY = 'REMEMBER_ME__'
const JWT_TOKEN_KEY = 'jwt_token'

const { permissionCacheType } = projectSetting

function useLocalStorage(): boolean {
  const stored = localStorage.getItem(REMEMBER_ME_KEY)
  if (stored !== null)
    return stored === 'true'
  return permissionCacheType === CacheTypeEnum.LOCAL
}

function getStorageFns() {
  return useLocalStorage()
    ? { get: Persistent.getLocal, set: Persistent.setLocal, clear: Persistent.clearLocal }
    : { get: Persistent.getSession, set: Persistent.setSession, clear: Persistent.clearSession }
}

export function getRememberMe(): boolean {
  const stored = localStorage.getItem(REMEMBER_ME_KEY)
  if (stored !== null)
    return stored === 'true'
  return permissionCacheType === CacheTypeEnum.LOCAL
}

export function setRememberMe(remember: boolean) {
  localStorage.setItem(REMEMBER_ME_KEY, String(remember))
}

export function syncJwtToken(token?: string | null) {
  if (token)
    localStorage.setItem(JWT_TOKEN_KEY, token)
  else
    localStorage.removeItem(JWT_TOKEN_KEY)
}

export function getJwtToken(): string {
  return getAccessToken() || localStorage.getItem(JWT_TOKEN_KEY) || ''
}

let isLoggingOut = false

/** 会话失效时统一跳转登录页（防重复触发） */
export function handleSessionTimeout() {
  if (isLoggingOut)
    return
  isLoggingOut = true
  import('@/store/modules/user')
    .then(({ useUserStoreWithOut }) => useUserStoreWithOut().logout(true))
    .finally(() => {
      // 登录页不会再通过整页刷新重置模块状态，需显式释放防重入标记。
      isLoggingOut = false
    })
}

export function getAccessToken(): string {
  return getAuthCache(ACCESS_TOKEN_KEY)
}

export function setAccessToken(value: string) {
  syncJwtToken(value)
  return setAuthCache(ACCESS_TOKEN_KEY, value)
}

export function getRefreshToken(): string {
  return getAuthCache(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(value: string) {
  return setAuthCache(REFRESH_TOKEN_KEY, value)
}

export function getTenantId() {
  return getAuthCache(TENANT_ID_KEY)
}

export function setTenantId(value) {
  return setAuthCache(TENANT_ID_KEY, value)
}

export function getAuthCache<T>(key: BasicKeys) {
  const { get } = getStorageFns()
  return get(key) as T
}

export function setAuthCache(key: BasicKeys, value) {
  const { set } = getStorageFns()
  return set(key, value, true)
}

export function clearAuthCache(immediate = true) {
  syncJwtToken(null)
  Persistent.clearLocal(immediate)
  Persistent.clearSession(immediate)
}

/** 登录时根据 rememberMe 切换存储介质并清理旧 Token */
export function switchAuthStorage(remember: boolean) {
  setRememberMe(remember)
  if (remember) {
    Persistent.clearSession(true)
  }
  else {
    Persistent.clearLocal(true)
  }
}
