import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { CreateSession, CloseSession, ListSessions } from '../../bindings/easyaiot/terminal/app'
import { usePanelStore } from './panelStore'
import { useSessionStore } from './sessionStore'
import { useTabStore } from './tabStore'
import { useConnectionStore } from './connectionStore'
import { fileTransferProto } from '../utils/fileTransferUtils'
import { unregisterTransferRoute } from '../services/transferTaskCenter'
import type { ConnectionConfig } from '../types/session'

export interface CompanionEntry {
  sftpSessionId?: string
  monitorSessionId?: string
  creatingSftp?: boolean
  creatingMonitor?: boolean
}

const DEFAULT_FILES_WIDTH = 300
const DEFAULT_MONITOR_WIDTH = 320

// Per-SSH-panel caches of the companion views, so switching between terminal
// tabs restores the previously loaded file listing / monitor graphs instead of
// re-fetching them. Keyed by the SSH panel id.
export interface FileViewCache {
  cwd: string
  files: unknown[]
}
export interface MonitorViewCache {
  systemInfo: Record<string, any> | null
  systemInfoAt: number
  cpu: Record<string, any>
  mem: Record<string, any>
  swap: Record<string, any>
  net: Record<string, any>
  // Expandable detail lists / their expansion state, kept per panel so the
  // sidebar restores them on return.
  cpus: any[]
  nets: any[]
  disks: any[]
  expanded: { cores: boolean; nets: boolean; disks: boolean }
}

export const useCompanionStore = defineStore('companion', () => {
  const filesVisible = ref(false)
  const monitorVisible = ref(false)
  const filesWidth = ref(DEFAULT_FILES_WIDTH)
  const monitorWidth = ref(DEFAULT_MONITOR_WIDTH)
  const entries = ref<Record<string, CompanionEntry>>({})
  const fileViewCache = ref<Record<string, FileViewCache>>({})
  const monitorViewCache = ref<Record<string, MonitorViewCache>>({})
  // Per-files-panel "follow terminal path" flag (sidebar navigates when the
  // terminal's shell reports a cwd change). Ephemeral by design: never
  // persisted, resets with the session.
  const followPathByPanel = ref<Record<string, boolean>>({})

  const panelStore = usePanelStore()
  const sessionStore = useSessionStore()
  const tabStore = useTabStore()

  function getActiveSshPanelId(): string | null {
    const pid = tabStore.getActivePanelId()
    if (!pid) return null
    const panel = panelStore.getPanel(pid)
    if (!panel || panel.type !== 'ssh') return null
    return pid
  }

  function getActiveWslPanelId(): string | null {
    const pid = tabStore.getActivePanelId()
    if (!pid) return null
    const panel = panelStore.getPanel(pid)
    if (!panel || panel.type !== 'wsl') return null
    return pid
  }

  /** Active panel that owns a file sidebar: an SSH panel or a WSL terminal. */
  function getActiveFilesPanelId(): string | null {
    return getActiveSshPanelId() ?? getActiveWslPanelId()
  }

  function isWslPanel(pid: string | null): boolean {
    if (!pid) return false
    return panelStore.getPanel(pid)?.type === 'wsl'
  }

  const activeSshPanelId = computed(() => getActiveSshPanelId())

  const activeFilesPanelId = computed(() => getActiveFilesPanelId())

  const sshConnected = computed(() => {
    const pid = activeSshPanelId.value
    if (!pid) return false
    const panel = panelStore.getPanel(pid)
    if (!panel?.sessionId) return false
    return sessionStore.getStatus(panel.sessionId) === 'connected'
  })

  // File sidebar is available for a connected SSH panel or a running WSL terminal.
  const filesConnected = computed(() => {
    const pid = activeFilesPanelId.value
    if (!pid) return false
    const panel = panelStore.getPanel(pid)
    if (!panel?.sessionId) return false
    return sessionStore.getStatus(panel.sessionId) === 'connected'
  })

  const canToggle = computed(() => filesConnected.value)

  const currentSftpSessionId = computed(() => {
    const pid = activeFilesPanelId.value
    if (!pid) return null
    return entries.value[pid]?.sftpSessionId ?? null
  })

  const currentMonitorSessionId = computed(() => {
    const pid = activeSshPanelId.value
    if (!pid) return null
    return entries.value[pid]?.monitorSessionId ?? null
  })

  // Companion file-panel transfer lists are stored in panelStore under a key
  // derived from the owning (SSH/WSL) panel id. Terminal tabs use the same
  // helper to surface active companion transfers on their tab.
  function sftpTransferKeyOf(panelId: string): string {
    return panelId ? `${panelId}__sftp` : ''
  }

  const transferKey = computed(() => sftpTransferKeyOf(getActiveFilesPanelId() ?? ''))

  function ensureEntry(sshPanelId: string): CompanionEntry {
    if (!entries.value[sshPanelId]) {
      entries.value[sshPanelId] = {}
    }
    return entries.value[sshPanelId]
  }

  function cloneConfig(config: ConnectionConfig): ConnectionConfig {
    // SSH panels keep deferConnect=true so the PTY starts after xterm measures
    // size. Companion SFTP/monitor sessions must connect immediately — otherwise
    // CreateSession returns and never launches Connect().
    return {
      ...config,
      deferConnect: false,
      initialCols: 0,
      initialRows: 0,
    }
  }

  function resolveConfig(sshPanelId: string): ConnectionConfig | null {
    const panel = panelStore.getPanel(sshPanelId)
    if (!panel?.config) return null
    const config = cloneConfig(panel.config)
    // Prefer password still held on the live SSH panel; fall back to the
    // connection store (which may have been refreshed from keychain).
    if (!config.password && config.authType === 'password' && config.id) {
      const stored = useConnectionStore().connections.find(c => c.id === config.id)
      if (stored?.password) config.password = stored.password
    }
    return config
  }

  async function sessionAlive(sessionId: string | undefined): Promise<boolean> {
    if (!sessionId) return false
    try {
      const sessions = await ListSessions()
      const sess = sessions.find(s => s.id === sessionId)
      return sess?.status === 'connected' || sess?.status === 'connecting'
    } catch {
      const st = sessionStore.getStatus(sessionId)
      return st === 'connected' || st === 'connecting'
    }
  }

  async function ensureSftp(sshPanelId: string): Promise<string | null> {
    const config = resolveConfig(sshPanelId)
    if (!config) return null
    const entry = ensureEntry(sshPanelId)
    if (entry.sftpSessionId && await sessionAlive(entry.sftpSessionId)) {
      return entry.sftpSessionId
    }
    if (entry.sftpSessionId) {
      unregisterTransferRoute(entry.sftpSessionId)
      try { await CloseSession(entry.sftpSessionId) } catch { /* ignore */ }
      entry.sftpSessionId = undefined
    }
    if (entry.creatingSftp) {
      for (let i = 0; i < 50; i++) {
        await new Promise(r => setTimeout(r, 100))
        if (entry.sftpSessionId) return entry.sftpSessionId
        if (!entry.creatingSftp) break
      }
      return entry.sftpSessionId ?? null
    }
    entry.creatingSftp = true
    try {
      // WSL terminals have no SFTP subsystem — their file sidebar is served by
      // the WSL file session over \\wsl.localhost\<distro>.
      if (isWslPanel(sshPanelId)) {
        config.type = 'wsl-file'
        const info = await CreateSession('wsl-file', config)
        entries.value = {
          ...entries.value,
          [sshPanelId]: { ...entries.value[sshPanelId], sftpSessionId: info.id, creatingSftp: false },
        }
        sessionStore.initSession(info.id)
        return info.id
      }
      // Honor the connection's file-transfer protocol preference: 'scp' for
      // hosts without an SFTP subsystem, 'sftp' (default) otherwise.
      const proto = fileTransferProto(config)
      config.type = proto
      const info = await CreateSession(proto, config)
      entries.value = {
        ...entries.value,
        [sshPanelId]: { ...entries.value[sshPanelId], sftpSessionId: info.id, creatingSftp: false },
      }
      sessionStore.initSession(info.id)
      return info.id
    } catch (e) {
      console.error('companion sftp create failed:', e)
      entries.value = {
        ...entries.value,
        [sshPanelId]: { ...entries.value[sshPanelId], creatingSftp: false },
      }
      return null
    }
  }

  async function ensureMonitor(sshPanelId: string): Promise<string | null> {
    const config = resolveConfig(sshPanelId)
    if (!config) return null
    const entry = ensureEntry(sshPanelId)
    if (entry.monitorSessionId && await sessionAlive(entry.monitorSessionId)) {
      return entry.monitorSessionId
    }
    if (entry.monitorSessionId) {
      try { await CloseSession(entry.monitorSessionId) } catch { /* ignore */ }
      entry.monitorSessionId = undefined
    }
    if (entry.creatingMonitor) {
      for (let i = 0; i < 50; i++) {
        await new Promise(r => setTimeout(r, 100))
        if (entry.monitorSessionId) return entry.monitorSessionId
        if (!entry.creatingMonitor) break
      }
      return entry.monitorSessionId ?? null
    }
    entry.creatingMonitor = true
    try {
      config.type = 'monitor'
      const info = await CreateSession('monitor', config)
      entries.value = {
        ...entries.value,
        [sshPanelId]: { ...entries.value[sshPanelId], monitorSessionId: info.id, creatingMonitor: false },
      }
      sessionStore.initSession(info.id)
      return info.id
    } catch (e) {
      console.error('companion monitor create failed:', e)
      entries.value = {
        ...entries.value,
        [sshPanelId]: { ...entries.value[sshPanelId], creatingMonitor: false },
      }
      return null
    }
  }

  async function toggleFiles() {
    if (!canToggle.value && !filesVisible.value) return
    if (filesVisible.value) {
      filesVisible.value = false
      return
    }
    const pid = getActiveFilesPanelId()
    if (!pid) return
    filesVisible.value = true
    await ensureSftp(pid)
  }

  async function toggleMonitor() {
    if (!canToggle.value && !monitorVisible.value) return
    if (monitorVisible.value) {
      monitorVisible.value = false
      return
    }
    const pid = getActiveSshPanelId()
    if (!pid) return
    monitorVisible.value = true
    await ensureMonitor(pid)
  }

  // Follow-terminal-path is DEFAULT-OFF: the record only ever stores an
  // explicit `true` (user turned it on); absence means disabled.
  function toggleFollowPath(panelId: string) {
    const next = followPathByPanel.value[panelId] !== true
    followPathByPanel.value = { ...followPathByPanel.value, [panelId]: next }
  }

  async function disposeForPanel(sshPanelId: string) {
    const entry = entries.value[sshPanelId]
    // Drop companion view caches together with the panel's sessions.
    if (fileViewCache.value[sshPanelId]) {
      delete fileViewCache.value[sshPanelId]
    }
    if (monitorViewCache.value[sshPanelId]) {
      delete monitorViewCache.value[sshPanelId]
    }
    delete followPathByPanel.value[sshPanelId]
    if (!entry) return
    const sftpId = entry.sftpSessionId
    const monitorId = entry.monitorSessionId
    delete entries.value[sshPanelId]
    if (sftpId) {
      try { await CloseSession(sftpId) } catch { /* ignore */ }
      unregisterTransferRoute(sftpId)
      panelStore.removeTransferTasks(sftpTransferKeyOf(sshPanelId))
    }
    if (monitorId) {
      try { await CloseSession(monitorId) } catch { /* ignore */ }
    }
  }

  async function disposeForPanels(panelIds: string[]) {
    await Promise.all(panelIds.map(id => disposeForPanel(id)))
  }

  function setFilesWidth(w: number) {
    filesWidth.value = Math.min(Math.max(w, 240), 560)
  }

  function setMonitorWidth(w: number) {
    monitorWidth.value = Math.min(Math.max(w, 260), 560)
  }

  function getFileViewCache(sshPanelId: string): FileViewCache | undefined {
    return fileViewCache.value[sshPanelId]
  }

  function setFileViewCache(sshPanelId: string, cache: FileViewCache) {
    fileViewCache.value = { ...fileViewCache.value, [sshPanelId]: cache }
  }

  function getMonitorViewCache(sshPanelId: string): MonitorViewCache | undefined {
    return monitorViewCache.value[sshPanelId]
  }

  function setMonitorViewCache(sshPanelId: string, cache: MonitorViewCache) {
    monitorViewCache.value = { ...monitorViewCache.value, [sshPanelId]: cache }
  }

  return {
    filesVisible,
    monitorVisible,
    filesWidth,
    monitorWidth,
    entries,
    followPathByPanel,
    activeSshPanelId,
    activeFilesPanelId,
    sshConnected,
    filesConnected,
    canToggle,
    currentSftpSessionId,
    currentMonitorSessionId,
    transferKey,
    sftpTransferKeyOf,
    ensureSftp,
    ensureMonitor,
    toggleFiles,
    toggleMonitor,
    disposeForPanel,
    disposeForPanels,
    setFilesWidth,
    setMonitorWidth,
    getActiveSshPanelId,
    getActiveFilesPanelId,
    isWslPanel,
    getFileViewCache,
    setFileViewCache,
    getMonitorViewCache,
    setMonitorViewCache,
    toggleFollowPath,
  }
})
