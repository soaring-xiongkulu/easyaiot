/** EasyAIoT IDEA 社区贡献在线 IDE（默认当前主机 :9300，可通过环境变量覆盖） */

const trimEnv = (value: string | undefined) => (value ?? '').trim()

export const IDEA_DEFAULT_PORT = 9300
const SESSION_KEY = 'easyaiot.idea.session'

export function getIdeaPortalUrl(): string {
  const configured = trimEnv(import.meta.env.VITE_IDEA_URL)
  if (configured) {
    return configured.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location
    return `${protocol}//${hostname}:${IDEA_DEFAULT_PORT}`
  }
  return `http://localhost:${IDEA_DEFAULT_PORT}`
}

export function getIdeaToken(): string {
  return trimEnv(import.meta.env.VITE_IDEA_TOKEN)
}

export function getIdeaSession(): string {
  if (typeof localStorage === 'undefined') {
    return ''
  }
  return localStorage.getItem(SESSION_KEY) || ''
}

export function setIdeaSession(token: string) {
  if (typeof localStorage === 'undefined') {
    return
  }
  if (token) {
    localStorage.setItem(SESSION_KEY, token)
  } else {
    localStorage.removeItem(SESSION_KEY)
  }
}

export function clearIdeaSession() {
  setIdeaSession('')
}

type IdeaFetchOptions = {
  method?: string
  body?: unknown
  query?: Record<string, string | undefined>
}

export type IdeaWorkspace = {
  id: string
  name: string
  user: string
  status: string
  port: number
  password: string
  url: string
  created_at: string
  container_id: string
  image: string
  last_active_at?: string
  idle_seconds?: number
}

export type IdeaStats = {
  total: number
  running: number
  max_total: number
  image: string
  git_url: string
  port_range: number[]
  data_dir: string
  idle_timeout_hours: number
}

export type IdeaAuthUser = {
  provider: string
  id: string
  login: string
  name: string
  avatar_url: string
  email: string
  workspace_user: string
}

export type IdeaAuthProviders = {
  providers: Array<{ id: string; name: string; enabled: boolean }>
  required: boolean
  redirect_base: string
}

async function ideaFetch<T>(path: string, options: IdeaFetchOptions = {}): Promise<T> {
  const base = getIdeaPortalUrl()
  const url = new URL(path.replace(/^\//, ''), base.endsWith('/') ? base : `${base}/`)
  if (options.query) {
    Object.entries(options.query).forEach(([k, v]) => {
      if (v !== undefined && v !== '') {
        url.searchParams.set(k, v)
      }
    })
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const token = getIdeaToken()
  if (token) {
    headers['X-IDEA-Token'] = token
  }
  const session = getIdeaSession()
  if (session) {
    headers['X-IDEA-Session'] = session
  }
  const resp = await fetch(url.toString(), {
    method: options.method || 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })
  const json = await resp.json().catch(() => ({}))
  if (!resp.ok || json?.ok === false) {
    throw new Error(json?.error || `IDEA request failed (${resp.status})`)
  }
  return json.data as T
}

export function getIdeaAuthProviders() {
  return ideaFetch<IdeaAuthProviders>('api/auth/providers')
}

export function getIdeaAuthMe() {
  return ideaFetch<IdeaAuthUser | null>('api/auth/me')
}

export function logoutIdeaAuth() {
  return ideaFetch<{ logged_out: boolean }>('api/auth/logout', { method: 'POST' })
}

export function getIdeaLoginUrl(provider: string): string {
  return `${getIdeaPortalUrl()}/api/auth/login/${encodeURIComponent(provider)}`
}

export function getIdeaStats() {
  return ideaFetch<IdeaStats>('api/stats')
}

export function listIdeaWorkspaces(user?: string) {
  return ideaFetch<IdeaWorkspace[]>('api/workspaces', { query: { user } })
}

export function createIdeaWorkspace(user?: string) {
  return ideaFetch<IdeaWorkspace>('api/workspaces', {
    method: 'POST',
    body: user ? { user } : {},
  })
}

export function stopIdeaWorkspace(id: string) {
  return ideaFetch<IdeaWorkspace>(`api/workspaces/${encodeURIComponent(id)}/stop`, {
    method: 'POST',
  })
}

export function startIdeaWorkspace(id: string) {
  return ideaFetch<IdeaWorkspace>(`api/workspaces/${encodeURIComponent(id)}/start`, {
    method: 'POST',
  })
}

export function heartbeatIdeaWorkspace(id: string) {
  return ideaFetch<IdeaWorkspace>(`api/workspaces/${encodeURIComponent(id)}/heartbeat`, {
    method: 'POST',
  })
}

export function deleteIdeaWorkspace(id: string) {
  return ideaFetch<{ deleted: boolean; id: string }>(
    `api/workspaces/${encodeURIComponent(id)}`,
    { method: 'DELETE' },
  )
}

export function openIdeaWorkspace(ws: Pick<IdeaWorkspace, 'url'>) {
  if (!ws?.url) {
    return
  }
  window.open(ws.url, '_blank', 'noopener,noreferrer')
}

export function formatIdle(seconds?: number): string {
  if (seconds === undefined || seconds === null || Number.isNaN(seconds)) {
    return '-'
  }
  if (seconds < 60) {
    return `${seconds}s`
  }
  if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m`
  }
  return `${(seconds / 3600).toFixed(1)}h`
}

/** 处理 OAuth 回调带回的 ?idea_token= / ?idea_error= */
export function consumeIdeaOauthCallback(): { token?: string; error?: string } {
  if (typeof window === 'undefined') {
    return {}
  }
  const url = new URL(window.location.href)
  const token = url.searchParams.get('idea_token') || ''
  const error = url.searchParams.get('idea_error') || ''
  if (token || error) {
    url.searchParams.delete('idea_token')
    url.searchParams.delete('idea_error')
    window.history.replaceState({}, '', url.pathname + url.search + url.hash)
  }
  if (token) {
    setIdeaSession(token)
  }
  return { token: token || undefined, error: error || undefined }
}
