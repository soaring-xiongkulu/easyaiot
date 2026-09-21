import { getAccessToken, getRefreshToken, getTenantId } from '@/utils/auth'
import { getFuxaOpenUrl } from '@/api/device/visualize'

/** 项目类型：大屏 / 组态（FUXA）/ 数字孪生 */
export type VisualizeProjectType = 'dashboard' | 'scada' | 'twin'

export const VISUALIZE_PROJECT_TYPE_OPTIONS = [
  { label: '大屏', value: 'dashboard' as VisualizeProjectType },
  { label: '组态（FUXA）', value: 'scada' as VisualizeProjectType },
  { label: '数字孪生', value: 'twin' as VisualizeProjectType },
]

export function isScadaProject(projectType?: string | null): boolean {
  return projectType === 'scada'
}

export function isTwinProject(projectType?: string | null): boolean {
  return projectType === 'twin'
}

export function getProjectTypeLabel(projectType?: string | null): string {
  if (isScadaProject(projectType)) return '组态'
  if (isTwinProject(projectType)) return '数字孪生'
  return '大屏'
}

export function getTwinBaseUrl(): string {
  const raw = ((import.meta.env.VITE_GLOB_TWIN_URL as string) || 'http://localhost:5173').trim()
  if (raw.startsWith('/') && typeof window !== 'undefined') return `${window.location.origin}${raw}`.replace(/\/$/, '')
  return raw.replace(/\/$/, '')
}

/** 内置 FUXA 演示项目 ID（与 visualize_demo_seed.sql 一致） */
export const FUXA_DEMO_PROJECT_IDS = new Set<number>([9311, 9312, 9313, 9314])

/** 内置 FUXA 演示画面名（与 easyaiot_scada_demo.fuxap 一致） */
export const FUXA_DEMO_VIEW_NAMES = new Set<string>([
  '水厂工艺总貌',
  '产线运行看板',
  '厂区管网组态',
  '配电室电力监视',
])

export interface FuxaDemoProjectLike {
  id?: number | string | null
  projectType?: string | null
  projectName?: string | null
  editorRef?: string | null
}

/** 是否为内置演示组态（只读，禁止打开 FUXA 编辑器改删工艺图） */
export function isFuxaDemoProject(project?: FuxaDemoProjectLike | null): boolean {
  if (!project) return false
  if (project.projectType != null && project.projectType !== '' && !isScadaProject(project.projectType)) {
    return false
  }
  const id = Number(project.id)
  if (Number.isFinite(id) && FUXA_DEMO_PROJECT_IDS.has(id)) {
    return true
  }
  const name = (project.projectName || '').trim()
  const ref = (project.editorRef || '').trim()
  return FUXA_DEMO_VIEW_NAMES.has(name) || FUXA_DEMO_VIEW_NAMES.has(ref)
}

/** VISUALIZE 大屏编辑器基址（开发默认 :8002）
 * - 绝对地址原样使用
 * - 相对路径（如生产 env 的 /visualize）解析为当前主机 :8002
 *   （与 FUXA 同理：独立容器站点根部署，不做 WEB 子路径反代）
 */
export function getVisualizeBaseUrl(): string {
  const raw = ((import.meta.env.VITE_GLOB_VISUALIZE_URL as string) || 'http://localhost:8002').trim()
  if (!raw || raw === '/visualize' || raw.startsWith('/visualize/')) {
    if (typeof window !== 'undefined' && window.location?.hostname) {
      return `${window.location.protocol}//${window.location.hostname}:8002`
    }
    return 'http://localhost:8002'
  }
  if (raw.startsWith('/')) {
    if (typeof window !== 'undefined' && window.location?.origin) {
      return `${window.location.origin}${raw}`.replace(/\/$/, '')
    }
  }
  return raw.replace(/\/$/, '')
}

/**
 * FUXA 组态编辑器基址（开发默认 :1881）
 * - 绝对地址原样使用
 * - 相对路径（如生产 env 的 /fuxa）解析为当前主机 :1881
 *   （FUXA Angular 资源为站点根绝对路径，不可做子路径反代）
 */
export function getFuxaBaseUrl(): string {
  const raw = ((import.meta.env.VITE_GLOB_FUXA_URL as string) || 'http://localhost:1881').trim()
  if (!raw || raw === '/fuxa' || raw.startsWith('/fuxa/')) {
    if (typeof window !== 'undefined' && window.location?.hostname) {
      return `${window.location.protocol}//${window.location.hostname}:1881`
    }
    return 'http://localhost:1881'
  }
  if (raw.startsWith('/')) {
    if (typeof window !== 'undefined' && window.location?.origin) {
      return `${window.location.origin}${raw}`.replace(/\/$/, '')
    }
  }
  return raw.replace(/\/$/, '')
}

export interface OpenVisualizeEditorOptions {
  /** 项目类型，默认 dashboard */
  projectType?: string | null
  /** 组态可选：FUXA 相对路径（如 /editor）或画面名 */
  editorRef?: string | null
  /** 组态可选：项目名称；当 editorRef 为空或仅为 /editor 时回退为画面名 */
  projectName?: string | null
}

/**
 * 解析组态打开用的画面引用
 * - `/editor`、`/home` 等路径原样保留（预览时走运行态）
 * - 编辑模式下空引用或仅 `/editor` 时回退为项目名（与 FUXA Views 画面名对齐）
 */
export function resolveScadaEditorRef(
  mode: 'edit' | 'preview',
  editorRef?: string | null,
  projectName?: string | null,
): string | null {
  const ref = (editorRef || '').trim()
  const name = (projectName || '').trim()
  if (mode === 'edit' && (!ref || ref === '/editor')) {
    return name || null
  }
  return ref || name || null
}

/**
 * 打开可视化编辑器（新标签页）
 * - dashboard：VISUALIZE 大屏编辑器
 * - scada：FUXA 组态（优先 SSO 免登）
 */
export function openVisualizeEditor(
  projectId: number | string,
  mode: 'edit' | 'preview' = 'edit',
  options?: OpenVisualizeEditorOptions,
) {
  if (isTwinProject(options?.projectType)) {
    const project = (options?.editorRef || 'industrial').replace(/^\?project=/, '')
    window.open(`${getTwinBaseUrl()}/?project=${encodeURIComponent(project)}&mode=${mode}`, '_blank')
    return
  }
  if (isScadaProject(options?.projectType)) {
    let openMode = mode
    // 演示组态只读：即便点「打开编辑器」也只进运行态，避免改删工艺图
    if (
      openMode === 'edit' &&
      isFuxaDemoProject({
        id: projectId,
        projectType: options?.projectType,
        projectName: options?.projectName,
        editorRef: options?.editorRef,
      })
    ) {
      openMode = 'preview'
    }
    const editorRef = resolveScadaEditorRef(openMode, options?.editorRef, options?.projectName)
    void openFuxaEditor(openMode, editorRef, projectId)
    return
  }
  openDashboardEditor(projectId, mode)
}

/**
 * 将后端返回的 FUXA SSO URL 主机改写为当前页面访问主机:1881。
 * 避免 public-url 配成内网 IP 后，外网用户浏览器无法打开。
 */
export function alignFuxaOpenUrlWithBrowser(url: string): string {
  if (!url || typeof window === 'undefined' || !window.location?.hostname) {
    return url
  }
  try {
    const parsed = new URL(url, window.location.href)
    const browserBase = getFuxaBaseUrl()
    const target = new URL(browserBase)
    parsed.protocol = target.protocol
    parsed.hostname = target.hostname
    parsed.port = target.port
    return parsed.toString()
  } catch {
    return url
  }
}

/**
 * 打开 FUXA：优先走后端 SSO 代登录桥接页；失败则直跳
 * - 编辑器 /editor
 * - 运行态 /home?view=画面名
 */
export async function openFuxaEditor(
  mode: 'edit' | 'preview' = 'edit',
  editorRef?: string | null,
  projectId?: number | string | null,
) {
  try {
    const res = await getFuxaOpenUrl({
      id: projectId,
      mode,
      editorRef: editorRef || undefined,
    })
    const url = res?.url
    if (url) {
      window.open(alignFuxaOpenUrlWithBrowser(url), '_blank')
      return
    }
  } catch (e) {
    console.warn('[FUXA SSO] fallback to direct open', e)
  }
  openFuxaDirect(mode, editorRef)
}

/**
 * 直跳 FUXA（无 SSO，适合鉴权关闭或后端不可达）
 * 编辑模式带画面名时，走同源桥接页写入 @frango.webeditor.currentview 再进编辑器
 * （FUXA 编辑器靠该 localStorage 恢复当前画面，直接开 /editor 无法按项目切换）
 */
export function openFuxaDirect(mode: 'edit' | 'preview' = 'edit', editorRef?: string | null) {
  const base = getFuxaBaseUrl()
  const ref = (editorRef || '').trim()
  // 演示画面禁止直跳 /editor（含无 token 桥接）
  const effectiveMode =
    mode === 'edit' && FUXA_DEMO_VIEW_NAMES.has(ref) ? 'preview' : mode

  let path: string
  if (ref.startsWith('/')) {
    // 演示保护下避免把 /editor 当目标
    path = effectiveMode === 'preview' && (ref === '/editor' || ref.startsWith('/editor?'))
      ? '/home'
      : ref
  } else if (effectiveMode === 'preview') {
    path = ref ? `/home?view=${encodeURIComponent(ref)}` : '/home'
  } else if (ref) {
    // 同源桥接：写入 currentview 后跳 /editor（无需 token）
    const qs = new URLSearchParams({
      mode: 'edit',
      view: ref,
      allowOpenWithoutToken: '1',
      _ts: String(Date.now()),
    })
    path = `/easyaiot-sso.html?${qs.toString()}`
  } else {
    path = '/editor'
  }

  window.open(`${base}${path}`, '_blank')
}

/**
 * 打开 VISUALIZE 大屏编辑器
 * - 同域：写入 GO_ACCESS_TOKEN 供编辑器读取
 * - 跨域：通过 hash query 传递 accessToken（编辑器入口会落库并清理 URL）
 */
function openDashboardEditor(projectId: number | string, mode: 'edit' | 'preview' = 'edit') {
  const token = getAccessToken()
  if (!token) {
    throw new Error('未登录，无法打开可视化编辑器')
  }

  const path = mode === 'preview' ? 'chart/preview' : 'chart/home'
  const base = getVisualizeBaseUrl()
  const refreshToken = getRefreshToken() || ''
  const tenantId = getTenantId() || '1'

  try {
    const editorOrigin = new URL(base, window.location.href).origin
    if (editorOrigin === window.location.origin) {
      localStorage.setItem(
        'GO_ACCESS_TOKEN',
        JSON.stringify({
          accessToken: token,
          refreshToken,
          tenantId,
        }),
      )
    }
  } catch {
    // ignore
  }

  const qs = new URLSearchParams({
    accessToken: String(token),
    tenantId: String(tenantId),
  })
  if (refreshToken) {
    qs.set('refreshToken', String(refreshToken))
  }

  const url = `${base}/#/${path}/${projectId}?${qs.toString()}`
  window.open(url, '_blank')
}
