/** EasyAIoT HARNESS — 仅经 IDEA 门户组合访问（默认当前主机 :9300?harness=1） */

import { getIdeaPortalUrl } from '@/utils/idea'

const trimEnv = (value: string | undefined) => (value ?? '').trim()

export const HARNESS_DEFAULT_PORT = 3080
export const IDEA_HARNESS_QUERY = 'harness=1'

export function getHarnessAppName(): string {
  const configured = trimEnv(import.meta.env.VITE_HARNESS_APP_NAME)
  if (configured)
    return configured
  return 'AI 助手'
}

export function getHarnessLogoUrl(): string {
  return trimEnv(import.meta.env.VITE_HARNESS_LOGO)
}

const HIDE_KEY = 'easyaiot.harness.float.hidden'
const PANEL_OPEN_KEY = 'easyaiot.harness.panel.open'

export function isHarnessPanelOpen(): boolean {
  if (typeof localStorage === 'undefined') {
    return false
  }
  return localStorage.getItem(PANEL_OPEN_KEY) === '1'
}

export function setHarnessPanelOpen(open: boolean) {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (open) {
    localStorage.setItem(PANEL_OPEN_KEY, '1')
  }
  else {
    localStorage.removeItem(PANEL_OPEN_KEY)
  }
}

/** 全局事件：任意页面请求打开右下角悬浮聊天抽屉 */
export const HARNESS_PANEL_OPEN_EVENT = 'easyaiot:harness-panel-open'

export function requestHarnessPanelOpen() {
  if (typeof window === 'undefined') {
    return
  }
  window.dispatchEvent(new CustomEvent(HARNESS_PANEL_OPEN_EVENT))
}

/** 组合入口：IDEA 门户（含 HARNESS），不再直连 :3080 */
export function getHarnessPortalUrl(): string {
  const idea = getIdeaPortalUrl()
  const sep = idea.includes('?') ? '&' : '?'
  return `${idea}${sep}${IDEA_HARNESS_QUERY}`
}

/** @deprecated 保留探测用；健康检查仍可打 HARNESS 端口 */
export function getHarnessServiceUrl(): string {
  const configured = trimEnv(import.meta.env.VITE_HARNESS_URL)
  if (configured) {
    return configured.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { hostname } = window.location
    // HARNESS 仅提供 HTTP（:3080），勿继承平台 HTTPS
    return `http://${hostname}:${HARNESS_DEFAULT_PORT}`
  }
  return `http://localhost:${HARNESS_DEFAULT_PORT}`
}

export function openHarnessPortal() {
  window.open(getHarnessPortalUrl(), '_blank', 'noopener,noreferrer')
}

export type HarnessHealth = {
  online: boolean
  status?: number
  latencyMs?: number
}

/** 探测 Harness Web UI 是否可达（跨端口可能因 CORS 误报，仅作参考） */
export async function checkHarnessHealth(): Promise<HarnessHealth> {
  const url = `${getHarnessServiceUrl()}/?embed=idea`
  const started = Date.now()
  try {
    const resp = await fetch(url, { method: 'GET', cache: 'no-store' })
    return {
      online: resp.ok || resp.status < 500,
      status: resp.status,
      latencyMs: Date.now() - started,
    }
  } catch {
    try {
      await fetch(url, { method: 'GET', mode: 'no-cors', cache: 'no-store' })
      return { online: true, latencyMs: Date.now() - started }
    } catch {
      return { online: false, latencyMs: Date.now() - started }
    }
  }
}

export const HARNESS_QUICK_PROMPTS = [
  '用 easyaiot_list_modules 介绍 EasyAIoT 各模块职责与端口',
  '调用 easyaiot_gateway_health 检查 Gateway 是否正常',
  '调用 easyaiot_dev_portals 告诉我 WEB / IDEA / HARNESS 怎么打开',
  '阅读 README_zh.md，用三句话概括 EasyAIoT 平台定位',
  '打开 HARNESS/README.md，说明如何新建会话才能看到全仓源码',
  '我想新增一个摄像头接入流程，应该改 WEB 还是 VIDEO 模块？',
  '帮我在 WEB 里找告警中心相关的路由与页面文件，并在侧边栏打开',
] as const

export function isHarnessFloatHidden(): boolean {
  if (typeof localStorage === 'undefined') {
    return false
  }
  return localStorage.getItem(HIDE_KEY) === '1'
}

export function setHarnessFloatHidden(hidden: boolean) {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (hidden) {
    localStorage.setItem(HIDE_KEY, '1')
  } else {
    localStorage.removeItem(HIDE_KEY)
  }
}

export function copyHarnessPrompt(text: string): Promise<void> {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text)
  }
  return Promise.reject(new Error('clipboard unavailable'))
}
