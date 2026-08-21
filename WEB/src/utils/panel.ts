/** EasyAIoT PANEL 运维控制台地址（默认当前主机 :9200，可通过环境变量覆盖） */

const trimEnv = (value: string | undefined) => (value ?? '').trim()

export const PANEL_DEFAULT_PORT = 9200

/** PANEL 控制台基址：优先 VITE_PANEL_URL，否则当前访问主机 + 9200 */
export function getPanelConsoleUrl(): string {
  const configured = trimEnv(import.meta.env.VITE_PANEL_URL)
  if (configured) {
    return configured.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { hostname } = window.location
    // PANEL 仅提供 HTTP（:9200），勿继承平台 HTTPS
    return `http://${hostname}:${PANEL_DEFAULT_PORT}`
  }
  return `http://localhost:${PANEL_DEFAULT_PORT}`
}

/** 新窗口打开 PANEL 运维控制台 */
export function openPanelConsole(): void {
  const url = getPanelConsoleUrl()
  window.open(url, '_blank', 'noopener,noreferrer')
}
