import axios, { type AxiosInstance } from 'axios'
import { message } from 'ant-design-vue'

const PANEL_BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.trim() || ''

function getToken(): string {
  return localStorage.getItem('panel_token') || (import.meta.env.VITE_PANEL_TOKEN as string) || ''
}

function createClient(): AxiosInstance {
  const client = axios.create({
    baseURL: PANEL_BASE,
    timeout: 60000,
  })
  client.interceptors.request.use((config) => {
    const token = getToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers['X-Panel-Token'] = token
    }
    return config
  })
  client.interceptors.response.use(
    (resp) => {
      const body = resp.data
      if (body && typeof body === 'object' && 'code' in body) {
        if (body.code === 0) return body.data
        const msg = body.msg || '请求失败'
        message.error(msg)
        return Promise.reject(new Error(msg))
      }
      return body
    },
    (err) => {
      const msg = err?.response?.data?.msg || err?.message || 'PANEL API 不可用'
      message.error(msg)
      return Promise.reject(err)
    },
  )
  return client
}

const http = createClient()

export interface PanelOverview {
  host: Record<string, any>
  docker: Record<string, any>
  profile: Record<string, any>
  containers: { total: number; running: number; stopped: number }
  projects: string[]
  panel: Record<string, any> & {
    deploySupported?: boolean
    platform?: {
      os?: string
      label?: string
      deploySupported?: boolean
      desktopImageOnly?: boolean
      message?: string
      hint?: string
      scriptName?: string
    }
    web?: {
      url?: string
      port?: string
      configured?: boolean
      running?: boolean
      status?: 'running' | 'stopped' | 'missing' | string
      message?: string
      container?: string
      containerState?: string
      containerStatus?: string
    }
  }
}

export interface PanelContainer {
  id: string
  name: string
  image: string
  status: string
  state: string
  createdAt?: string
  ports?: string
  stats?: {
    cpuPercent?: number
    memPercent?: number
    memUsage?: string
    netIO?: string
  } | null
}

export interface TopologyNode {
  id: string
  label: string
  group: string
  state: string
  containerName?: string
  containerId?: string
  cpuPercent?: number
  memPercent?: number
  memUsage?: string
  netIO?: { rx?: string; tx?: string; raw?: string }
}

export interface TopologyEdge {
  source: string
  target: string
  label: string
  active: boolean
}

export interface StackAction {
  action: string
  label: string
  dangerous: boolean
  desc: string
  category?: string
  supportsImageMode?: boolean
  supportsParallelBuild?: boolean
  supportsBuildArch?: boolean
  argKey?: string
  argLabel?: string
  argOptional?: boolean
  argOptions?: { value: string; label: string }[]
}

export interface StackJob {
  id: string
  action: string
  args: string[]
  scope?: 'all' | 'middleware' | 'business' | string
  script?: string
  scriptName?: string
  status: string
  error?: string
  log?: string
  logTail?: string
}

export interface StackMeta {
  categories: { key: string; label: string; desc: string }[]
  modules: { value: string; label: string }[]
  runtimeModules: { value: string; label: string }[]
  buildArchs: { value: string; label: string }[]
  imageModes: { value: string; label: string }[]
  allowDangerous: boolean
  actions: StackAction[]
  deploySupported?: boolean
  deployMessage?: string
  deployHint?: string
  desktopImageOnly?: boolean
  installScript?: string
  installScriptExists?: boolean
  scriptName?: string
  scope?: 'all' | 'middleware' | 'business' | string
  scopes?: { value: string; label: string; desc: string }[]
  platform?: {
    os?: string
    system?: string
    label?: string
    machine?: string
    deploySupported?: boolean
    desktopImageOnly?: boolean
    message?: string
    hint?: string
    scriptName?: string
  }
}

export const getOverview = () => http.get('/api/overview') as Promise<PanelOverview>
export const getLinks = () =>
  http.get('/api/links') as Promise<{
    web: {
      url: string
      port: string
      configured: boolean
      running: boolean
      status?: 'running' | 'stopped' | 'missing' | string
      message?: string
      container?: string
      containerState?: string
      containerStatus?: string
    }
  }>
export const getContainers = (params?: { all?: boolean; stats?: boolean }) =>
  http.get('/api/containers', {
    params: {
      all: params?.all === false ? '0' : '1',
      stats: params?.stats === false ? '0' : '1',
    },
  }) as Promise<{ list: PanelContainer[]; total: number }>
export const getContainerLogs = (id: string, tail = 200) =>
  http.get(`/api/containers/${encodeURIComponent(id)}/logs`, { params: { tail } }) as Promise<{
    logs: string
  }>
export const controlContainer = (id: string, action: 'start' | 'stop' | 'restart') =>
  http.post(`/api/containers/${encodeURIComponent(id)}/${action}`)

export interface PanelImage {
  id: string
  shortId: string
  repository: string
  tag: string
  ref: string
  digest?: string
  createdAt?: string
  createdSince?: string
  size?: string
  sizeBytes?: number
  dangling?: boolean
}

export const getImages = () =>
  http.get('/api/images') as Promise<{
    list: PanelImage[]
    total: number
    dangling: number
    totalBytes: number
  }>

export interface ImageCatalogItem {
  module: string
  remote: string
  local: string
  compose: string
  expectedRef: string
  required: boolean
  fullOnly?: boolean
  profileDependent?: boolean
  present: boolean
  status: 'ready' | 'missing' | 'optional_ready' | 'optional_missing' | string
  image?: PanelImage | null
  containers: { name: string; id: string; state: string; status: string; image: string }[]
  runningContainers: number
}

export interface ImageCatalog {
  profile: string
  summary: {
    required: number
    ready: number
    missing: number
    optionalMissing: number
    otherImages: number
    totalLocalImages: number
    dangling: number
  }
  modules: string[]
  items: ImageCatalogItem[]
  others: PanelImage[]
  deployProfile?: Record<string, any>
}

export const getImageCatalog = (profile?: string) =>
  http.get('/api/images/catalog', {
    params: profile ? { profile } : undefined,
  }) as Promise<ImageCatalog>

export const inspectImage = (ref: string) =>
  http.get(`/api/images/${encodeURIComponent(ref)}/inspect`) as Promise<{
    id: string
    inspect: Record<string, any>
  }>
export const removeImage = (ref: string, force = false) =>
  http.post(`/api/images/${encodeURIComponent(ref)}/remove`, { force }) as Promise<{
    ok: boolean
    id: string
    output?: string
  }>
export const pruneImages = (danglingOnly = true) =>
  http.post('/api/images/prune', { danglingOnly }) as Promise<{
    ok: boolean
    danglingOnly: boolean
    output?: string
  }>

export const getTopology = () =>
  http.get('/api/topology') as Promise<{
    nodes: TopologyNode[]
    edges: TopologyEdge[]
    summary: Record<string, number>
  }>
export const getProfile = () => http.get('/api/profile') as Promise<Record<string, any>>

export type DeployScope = 'all' | 'middleware' | 'business'

export const getStackActions = (scope: DeployScope = 'all') =>
  http.get('/api/stack/actions', { params: { scope } }) as Promise<{
    actions: StackAction[]
    allowDangerous: boolean
    scope?: string
  }>
export const getStackMeta = (scope: DeployScope = 'all') =>
  http.get('/api/stack/meta', { params: { scope } }) as Promise<StackMeta>
export const runStackAction = (payload: {
  action: string
  args?: string[]
  profile?: string
  scope?: DeployScope
  options?: Record<string, unknown>
  env?: Record<string, string>
}) => http.post('/api/stack/run', payload) as Promise<StackJob>
export const getStackJob = (id: string) =>
  http.get(`/api/stack/jobs/${encodeURIComponent(id)}`) as Promise<StackJob>
export const listStackJobs = (limit = 15, scope?: DeployScope) =>
  http.get('/api/stack/jobs', {
    params: { limit, ...(scope ? { scope } : {}) },
  }) as Promise<{ list: StackJob[] }>
export const cancelStackJob = (id: string) =>
  http.post(`/api/stack/jobs/${encodeURIComponent(id)}/cancel`) as Promise<StackJob>

export interface DeployProcess {
  pid: number
  ppid: number
  name: string
  cmd: string
  marker: string
  cwd?: string
  user?: string
  status?: string
  startedAt?: number
  ownedByPanel?: boolean
}

export const listDeployProcesses = (scope?: DeployScope) =>
  http.get('/api/stack/processes', {
    params: scope ? { scope } : undefined,
  }) as Promise<{ list: DeployProcess[]; total: number }>
export const killDeployProcesses = (payload?: {
  pids?: number[]
  all?: boolean
  scope?: DeployScope
}) =>
  http.post('/api/stack/processes/kill', payload || { all: true }) as Promise<{
    killed: { pid: number; ok: boolean; error?: string }[]
    errors: string[]
    remaining: DeployProcess[]
    totalKilled: number
  }>
