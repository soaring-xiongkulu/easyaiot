// Unified connection launcher. One registry of per-type connect specs and one
// runner implementing the shared connect skeleton (persist → credentials →
// panel → tab → session), replacing the former family of copy-pasted
// onConnectXxx handlers in App.vue. Persistence bookkeeping for the save /
// connect / connect-only entry points lives here too, so "connect only"
// behaves uniformly for every type. Adding a connection type means adding a
// spec entry instead of a new handler.
//
// The generic terminal path (ssh/telnet/mosh/local/wsl/tcp/serial) is genuinely
// different — it must wait for the real xterm size before SessionStart — so it
// stays in App.vue and is handed in per call via `connectTerminal`.
import { CreateSession, RecordRecentConnection } from '../../bindings/easyaiot/terminal/app'
import { useConnectionStore } from '../stores/connectionStore'
import { usePanelStore } from '../stores/panelStore'
import { useTabStore } from '../stores/tabStore'
import { useSessionStore } from '../stores/sessionStore'
import { fileTransferProto } from '../utils/fileTransferUtils'
import { parseWslFromShell } from '../utils/shellLabel'
import { t } from '../i18n'
import { msg } from '../services/message'
import type { ConnectionConfig, MemberConnectResult } from '../types/session'

// App.vue-provided dependencies: the credential dialog and the start-tab
// repositioning helper both live in App.vue. Wired once via configureLauncher.
export interface LauncherDeps {
  ensureCredentials(config: ConnectionConfig): Promise<ConnectionConfig | null>
  closeStartAndReposition(prevStart: any): (newTabId: string) => void
}

let deps: LauncherDeps | null = null

export function configureLauncher(d: LauncherDeps) {
  deps = d
}

export interface LaunchOptions {
  // Save to the connection list + recent history (default true). "Connect
  // only" passes false: no store write, no recent entry; the transient
  // session still gets a stable id for panel/tab wiring.
  persist?: boolean
  // An existing connection was edited → update instead of add.
  wasEdit?: boolean
  // Start tab to close and reposition the new tab after.
  prevStart?: any
  // Fallback for types without a spec: the generic terminal path in App.vue.
  // Returns the created panel id + status when the caller is workspace
  // orchestration (create-from-selection / open-saved); plain connects ignore it.
  connectTerminal?: (config: ConnectionConfig, persist: boolean) => Promise<MemberConnectResult | void> | MemberConnectResult | void
}

// Shared persistence bookkeeping for the save / connect / connect-only entry
// points (mirrors the former onConnect prelude).
export function persistConnection(config: ConnectionConfig, wasEdit = false) {
  const connectionStore = useConnectionStore()
  if (wasEdit) {
    connectionStore.update(config.id, config)
  } else {
    connectionStore.add(config)
  }
}

export async function launchConnection(config: ConnectionConfig, opts: LaunchOptions = {}) {
  const persist = opts.persist ?? true
  if (persist) {
    persistConnection(config, opts.wasEdit ?? false)
  } else if (!config.id) {
    // Give the transient session a stable id for panel/tab wiring even
    // though it will not be persisted to the connection list.
    config.id = `conn-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
  }

  const spec = SPECS[config.type]
  if (spec) {
    await runSpec(config.type, config, spec, opts)
    return
  }
  await opts.connectTerminal?.(config, persist)
}

// Open the protocol-agnostic file browser for a config — the SSH companion
// (SFTP/SCP per the connection's fileTransferProto preference) and the
// app:connect-sftp window event all land here. Unlike launchConnection this
// forces the SFTP spec regardless of config.type.
export async function launchFileBrowser(config: ConnectionConfig, opts: LaunchOptions = {}) {
  const persist = opts.persist ?? true
  if (persist) persistConnection(config)
  await runSpec('sftp', config, SPECS.sftp, opts)
}

// Open the monitor view for a config (SSH host monitor companion, and the
// app:connect-monitor window event). Forces the monitor spec regardless of
// config.type.
export async function launchMonitor(config: ConnectionConfig, opts: LaunchOptions = {}) {
  const persist = opts.persist ?? true
  if (persist) persistConnection(config)
  await runSpec('monitor', config, SPECS.monitor, opts)
}

// Open the WSL distro's file browser (wsl-file session over //wsl.localhost).
// Never persists — it is a transient view of the wsl connection.
export async function launchWslFileBrowser(config: ConnectionConfig, opts: LaunchOptions = {}) {
  const fileConfig: ConnectionConfig = { ...config, type: 'wsl-file' }
  await runSpec('wsl-file', fileConfig, SPECS['wsl-file'], { ...opts, persist: false })
}

// Per-type connect behavior. Every field defaults from the SPEC KEY (which is
// the config type, or the forced kind for the companion entries), so a plain
// entry only lists its deviations:
// - title: defaults to `user@host`-style (preferring the saved name).
// - uiType: when the panel AND tab kind differ from the key (the file-transfer
//   family renders as the protocol-agnostic 'sftp' panel/tab).
// - panelType: panel-kind-only override (the database family shares the
//   'database' panel for reconnect routing while tabs keep their own kind).
// - sessionType: CreateSession kind, defaults to the key; a function form is
//   supported for per-connection resolution. componentSession instead marks
//   kinds whose tab content owns the session (x11-desktop, k8s, container).
// - sessionFirst: create the session BEFORE the tab. VNC/SPICE mount their
//   content immediately and need sessionId + proxyAddr already bound (v3
//   race: the session:status 'connected' event fires during CreateSession,
//   before the component has its session id).
// - initSession: also register the session in sessionStore.
// - needsCredentials: run ensureCredentials first (default true).
// - prepare: normalize config fields before anything else.
// - onError: session-creation failure handling; the default closes the tab
//   and removes the panel (sessionFirst failure just removes the panel).
interface ConnectSpec {
  uiType?: string
  panelType?: string
  title?(config: ConnectionConfig): string
  tabExtra?(config: ConnectionConfig): Record<string, unknown>
  sessionType?: string | ((config: ConnectionConfig) => string)
  componentSession?: boolean
  sessionFirst?: boolean
  initSession?: boolean
  needsCredentials?: boolean
  prepare?(config: ConnectionConfig): void
  onError?(panelId: string, e: unknown): void
}

const userHost = (c: ConnectionConfig) => c.name || `${c.user}@${c.host}`
const dbTitle = (c: ConnectionConfig) => c.name || `${c.type}:${c.user}@${c.host}`

function resolveSessionType(key: string, spec: ConnectSpec, config: ConnectionConfig): string {
  const st = spec.sessionType ?? key
  return typeof st === 'function' ? st(config) : st
}

const SPECS: Record<string, ConnectSpec> = {
  // File-transfer family: the panel/tab are the protocol-agnostic 'sftp'
  // browser; only the SESSION differs (and the ssh companion honors the
  // per-connection SFTP/SCP preference).
  sftp: { sessionType: c => fileTransferProto(c) },
  scp: { uiType: 'sftp' },
  ftp: { uiType: 'sftp' },
  smb: { uiType: 'sftp' },
  webdav: { uiType: 'sftp' },
  s3: {
    uiType: 'sftp',
    needsCredentials: false,
    title: c => c.name || (c.s3Bucket ? `s3://${c.s3Bucket}` : c.host),
  },
  rdp: { initSession: true },
  vnc: { sessionFirst: true, initSession: true, title: c => c.name || c.host },
  spice: { sessionFirst: true, initSession: true, title: c => c.name || c.host },
  // The X11DesktopTabContent owns CreateSession + X11DesktopConnect; it runs
  // when the tab mounts and reads the panel's config.
  'x11-desktop': { componentSession: true, title: c => c.name || c.host || 'X11 Desktop' },
  database: {
    panelType: 'database',
    prepare: c => { c.dbType = c.dbType || 'mysql' },
    title: c => c.name || `${c.dbType}:${c.user}@${c.host}`,
    initSession: true,
    onError: (panelId, e) => {
      // Database tabs stay open on failure (the SQL editor is usable to
      // retry); surface the error on the panel instead of tearing the tab
      // down.
      usePanelStore().updateStatus(panelId, 'error')
      msg.error(`${t('db.connectFailed')}: ${(e as any)?.message || String(e)}`)
    },
  },
  // Standalone NoSQL types share the database panel (reconnect routing) while
  // tabs and sessions carry their own kind.
  redis: { panelType: 'database', initSession: true, title: dbTitle },
  mongodb: { panelType: 'database', initSession: true, title: dbTitle },
  elasticsearch: { panelType: 'database', initSession: true, title: dbTitle },
  k8s: {
    componentSession: true,
    needsCredentials: false,
    title: c => c.name || 'K8s',
    tabExtra: c => ({ connectionId: c.id, connId: null, namespace: c.k8sNamespace || 'default' }),
  },
  container: {
    componentSession: true,
    needsCredentials: false,
    title: c => c.name || 'Container',
    tabExtra: c => ({ connectionId: c.id, runtime: c.containerRuntime ?? 'docker' }),
  },
  monitor: { initSession: true },
  // WSL distro file browser: a runtime variant of the wsl connection — the
  // config is remapped to the wsl-file session kind and never persisted.
  'wsl-file': {
    uiType: 'sftp',
    needsCredentials: false,
    title: c => c.name || `WSL ${parseWslFromShell(c.shellPath) || ''}`,
    prepare: c => { c.type = 'wsl-file' },
  },
}

async function runSpec(key: string, config: ConnectionConfig, spec: ConnectSpec, opts: LaunchOptions) {
  const panelStore = usePanelStore()
  const tabStore = useTabStore()
  const sessionStore = useSessionStore()
  const persist = opts.persist ?? true
  spec.prepare?.(config)

  if (spec.needsCredentials !== false && deps) {
    const resolved = await deps.ensureCredentials(config)
    if (!resolved) return
    config = resolved
  }

  const displayTitle = (spec.title ?? userHost)(config)
  const panelKind = (spec.uiType ?? spec.panelType ?? key) as Parameters<typeof panelStore.createPanel>[1]
  const panel = panelStore.createPanel(config, panelKind)
  panelStore.updateTitle(panel.id, displayTitle)
  const reposition = opts.prevStart && deps ? deps.closeStartAndReposition(opts.prevStart) : null

  const tabKind = (spec.uiType ?? key) as Parameters<typeof tabStore.createTab>[0]
  let tab: { id: string } | null = null
  const openTab = () => {
    const t = useTabStore().createTab(tabKind, displayTitle, panel.id, spec.tabExtra?.(config))
    reposition?.(t.id)
    panelStore.movePanelToTab(panel.id, t.id)
    return t
  }

  const sessionType = spec.componentSession ? undefined : resolveSessionType(key, spec, config)
  if (!sessionType) {
    // Session lifecycle belongs to the tab's content component: panel + tab
    // only.
    openTab()
    if (persist) RecordRecentConnection(config.id)
    return
  }

  if (!spec.sessionFirst) {
    tab = openTab()
    if (persist) RecordRecentConnection(config.id)
  }

  try {
    const info = await CreateSession(sessionType, config)
    if (spec.sessionFirst && info?.proxyAddr) panelStore.setProxyAddr(panel.id, info.proxyAddr)
    panelStore.bindSession(panel.id, info.id)
    if (spec.initSession) sessionStore.initSession(info.id)
    if (spec.sessionFirst) {
      tab = openTab()
      if (persist) RecordRecentConnection(config.id)
    }
  } catch (e) {
    console.error(`Failed to create ${sessionType} session:`, e)
    if (spec.onError) {
      spec.onError(panel.id, e)
    } else {
      if (tab) tabStore.closeTab(tab.id)
      panelStore.removePanel(panel.id)
    }
  }
}
