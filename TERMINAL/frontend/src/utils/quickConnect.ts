import type { ConnectionConfig } from '../types/session'
import { useIdentityStore } from '../stores/identityStore'
import {
  CATEGORY_META, CATEGORY_ORDER, CONNECTION_TYPES, connectionTypeFormLabel, typeFilterKey,
  defaultPortFor, isSqlDbType,
} from './connectionTypes'

export { isSqlDbType }

// Platform detection for Windows-only features (e.g., WSLC)
export const isWindows = /windows/i.test(navigator.userAgent)

// Quick-connect protocol prefixes derived from the connectionTypes registry:
// every non-hostless type is addressable by its own name (ssh, rdp, redis,
// …), SQL engines by their dbType (mysql, oracle, …) under the shared
// 'database' type. Only genuine aliases are listed here; default ports come
// from the registry. Host-less kinds (local/wsl/serial), UI-only kinds and
// the container family are not addressable this way.
const QUICK_PROTOCOL_ALIASES: Record<string, string> = {
  http: 'webdav',
  https: 'webdav',
  postgresql: 'postgres',
  mongo: 'mongodb',
  es: 'elasticsearch',
  opensearch: 'elasticsearch',
}
const HOSTLESS_QUICK_TYPES = new Set(['local', 'wsl', 'serial'])

function buildQuickProtocols(): Record<string, { type: string; dbType?: string }> {
  const map: Record<string, { type: string; dbType?: string }> = {}
  for (const info of CONNECTION_TYPES) {
    if (info.formHidden || info.category === 'container' || HOSTLESS_QUICK_TYPES.has(info.type)) continue
    if (info.dbType) map[info.dbType] = { type: info.type, dbType: info.dbType }
    else map[info.type] = { type: info.type }
  }
  for (const [alias, target] of Object.entries(QUICK_PROTOCOL_ALIASES)) {
    map[alias] = map[target]
  }
  return map
}

const QUICK_PROTOCOLS = buildQuickProtocols()

// Helper: parse [user[:password]@]host[:port]
function parseHost(s: string) {
  const m = s.match(/^(?:([^@]+)@)?([^:]+)(?::(\d+))?$/)
  if (!m) return { host: s }
  let user = ''
  let pass = ''
  if (m[1]) {
    const colonIdx = m[1].indexOf(':')
    if (colonIdx >= 0) {
      user = m[1].slice(0, colonIdx)
      pass = m[1].slice(colonIdx + 1)
    } else {
      user = m[1]
    }
  }
  return {
    user,
    password: pass || undefined,
    host: m[2],
    port: m[3] ? parseInt(m[3]) : undefined,
  }
}

export function parseQuickConnect(raw: string): Partial<ConnectionConfig> | null {
  const input = raw.trim()
  if (!input) return null

  const parts = input.split(/\s+/)
  const first = parts[0].toLowerCase()

  // Pattern: [type] [user[:password]@]host[:port]
  if (parts.length >= 2 && QUICK_PROTOCOLS[first]) {
    const cfg = QUICK_PROTOCOLS[first]
    const rest = parts.slice(1).join(' ')
    const h = parseHost(rest)
    const result: any = { type: cfg.type, host: h.host }
    if (cfg.dbType) result.dbType = cfg.dbType
    if (h.user) result.user = h.user
    if (h.password) result.password = h.password
    result.port = h.port || defaultPortFor(cfg.type, cfg.dbType)
    return result
  }

  // Patterns: [user[:password]@]host[:port]  or  host[:port]  (default ssh)
  const h = parseHost(input)
  const result: any = { type: 'ssh', host: h.host }
  if (h.user) result.user = h.user
  if (h.password) result.password = h.password
  result.port = h.port || 22
  return result
}

// Default port lookup delegated to the connectionTypes registry
function getDefaultPort(type: string, dbType?: string): number | undefined {
  return defaultPortFor(type, dbType)
}

export function formatConnSubtitle(config: ConnectionConfig, getShellLabel?: (path: string) => string): string {
  let typeLabel = config.type
  if (config.type === 'database') typeLabel = config.dbType || config.type
  else if (config.type === 'container') typeLabel = config.containerRuntime || config.type
  let detail: string
  if (config.type === 's3') {
    detail = config.host
  } else if (config.type === 'local') {
    detail = getShellLabel ? getShellLabel(config.shellPath || '') : 'Local'
  } else {
    const defaultPort = getDefaultPort(config.type, config.dbType)
    const showPort = defaultPort !== config.port && defaultPort !== undefined
    const portStr = showPort ? `:${config.port}` : ''
    // Identity connections keep config.user empty by design (the username lives
    // in the referenced identity and is materialized at connect time), so the
    // display name is resolved from the identity store here.
    let user = config.user
    if (!user && config.authType === 'identity' && config.identityId) {
      user = useIdentityStore().identities.find((i) => i.id === config.identityId)?.username || ''
    }
    detail = user ? `${user}@${config.host}${portStr}` : `${config.host}${portStr}`
  }
  return `${typeLabel} ${detail}`
}

// Does a connection match a type-filter key (`all` / `database:<dbType>` /
// `container:<runtime>` / plain type)? Shared by the sidebar and the start
// page, which apply the same filter semantics to their lists.
export function matchTypeFilter(conn: ConnectionConfig, filter: string): boolean {
  if (filter === 'all') return true
  if (filter.startsWith('database:')) {
    return conn.type === 'database' && conn.dbType === filter.slice('database:'.length)
  }
  if (filter.startsWith('container:')) {
    return conn.type === 'container' && (conn.containerRuntime || 'docker') === filter.slice('container:'.length)
  }
  return conn.type === filter
}

// Origin (base) connection type for a filter key, ignoring any `:` suffix
// (e.g. `database:mysql` → `database`, `container:docker` → `container`).
export function getTypeBaseType(key: string): string {
  return key.split(':')[0]
}

// Grouping key used by the type filter for a connection, the same shape as a
// filter value: `database:<dbType>` / `container:<runtime>` / plain type.
export function getConnectionTypeKey(config: ConnectionConfig): string {
  if (config.type === 'database' && config.dbType) return `database:${config.dbType}`
  if (config.type === 'container') return `container:${config.containerRuntime || 'docker'}`
  return config.type
}

// Pretty-print a type filter key that isn't covered by a static label — today
// only container runtimes (`container:docker` → `Docker`). `containerRuntime`
// values are lowercase; capitalize the first letter for the menu/trigger.
export function formatTypeFilterLabel(key: string): string {
  const prefix = 'container:'
  if (key.startsWith(prefix)) {
    const rt = key.slice(prefix.length)
    return rt.charAt(0).toUpperCase() + rt.slice(1)
  }
  return key
}

// Top-level category (key) a filter value belongs to, with a fallback category
// for any unexpected type so it still shows up in the menu. Database types are
// further routed to the sql/nosql sub-categories by dbType.
export function getTypeCategory(key: string): string {
  const base = getTypeBaseType(key)
  if (base === 'database') {
    return isSqlDbType(key.slice('database:'.length)) ? 'sql' : 'nosql'
  }
  return CONNECTION_TYPES.find(t => t.type === base)?.category || 'other'
}

// Two-level type catalog for the type filter, derived from the connectionTypes
// registry (same category order and subtype order as the new-connection form —
// both come from the registry). `t` is required for the localized category
// titles and type names; `isWin` controls whether Windows-only options (WSL,
// WSLC) are included.
export function getTypeFilterCatalog(t: (key: string) => string, isWin = false) {
  return CATEGORY_ORDER.map(key => ({
    key,
    label: t(CATEGORY_META[key].labelKey),
    items: CONNECTION_TYPES
      .filter(info => info.category === key && !info.formHidden && (info.windowsOnly ? isWin : true))
      .map(info => ({ key: typeFilterKey(info), label: connectionTypeFormLabel(info, t) })),
  }))
}

// Ordered, labelled category keys for the two-level filter menu.
export const TYPE_CATEGORIES: string[] = [...CATEGORY_ORDER, 'other']
