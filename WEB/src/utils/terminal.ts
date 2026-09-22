/** EasyAIoT TERMINAL 多协议终端地址（默认当前主机 :9245，可通过环境变量覆盖） */

const trimEnv = (value: string | undefined) => (value ?? '').trim()

export const TERMINAL_DEFAULT_PORT = 9245

/** TERMINAL Web 基址：优先 VITE_TERMINAL_URL，否则当前访问主机 + 9245 */
export function getTerminalUrl(): string {
  const configured = trimEnv(import.meta.env.VITE_TERMINAL_URL)
  if (configured) {
    return configured.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { hostname } = window.location
    // TERMINAL 仅提供 HTTP（:9245），勿继承平台 HTTPS
    return `http://${hostname}:${TERMINAL_DEFAULT_PORT}`
  }
  return `http://localhost:${TERMINAL_DEFAULT_PORT}`
}

/** 新窗口独立打开 TERMINAL 终端 */
export function openTerminalStandalone(): void {
  const url = getTerminalUrl()
  window.open(url, '_blank', 'noopener,noreferrer')
}

export type TerminalHealth = {
  online: boolean
  latencyMs?: number
}

/** 探测 TERMINAL Web 是否可达（跨端口可能因 CORS 误报，仅作参考） */
export async function checkTerminalHealth(timeoutMs = 2500): Promise<TerminalHealth> {
  const url = getTerminalUrl()
  const started = Date.now()
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const resp = await fetch(url, { method: 'GET', mode: 'no-cors', cache: 'no-store', signal: controller.signal })
    return { online: !!resp, latencyMs: Date.now() - started }
  } catch {
    return { online: false, latencyMs: Date.now() - started }
  } finally {
    clearTimeout(timer)
  }
}
