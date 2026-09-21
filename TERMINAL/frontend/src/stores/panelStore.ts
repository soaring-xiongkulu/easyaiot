import { defineStore } from 'pinia'
import { reactive } from 'vue'
import type { Panel, PanelStatus, ConnectionConfig } from '../types/workspace'
import { DisableSessionOutputLog, RegisterSessionForPanel, UnregisterSession } from '../../bindings/easyaiot/terminal/app'

export interface TransferFileState {
  path: string
  status: 'running' | 'done' | 'failed'
}

export interface TransferTaskUI {
  id: string
  type: 'upload' | 'download'
  name: string
  // Full source/target paths from the backend's start payload — the retry
  // spec round-trips these back to SftpRetryTransfer.
  localPath: string
  remotePath: string
  percentage: number
  speed: string
  eta: string
  status: 'running' | 'paused' | 'done' | 'error' | 'cancelled'
  lastBytes: number
  lastTime: number
  total: number
  // Directory-transfer detail (empty for single-file tasks).
  fileCount: number
  completedFiles: number
  currentFile: string
  files: TransferFileState[]
  failedFiles: { path: string; error: string }[]
}

export interface VNCCache {
  rfb: any
  container: HTMLDivElement
}

export interface SPICECache {
  sc: any
  container: HTMLDivElement
}

const panelState = reactive<{
  panels: Map<string, Panel>
  transferTasks: Map<string, TransferTaskUI[]>
  proxyAddrs: Map<string, string>
  vncCaches: Map<string, VNCCache>
}>({
  panels: new Map(),
  transferTasks: new Map(),
  proxyAddrs: new Map(),
  vncCaches: new Map(),
  spiceCaches: new Map()
})

export const usePanelStore = defineStore('panel', () => {
  function makeTitleUnique(title: string, excludePanelId?: string): string {
    const others = [...panelState.panels.values()]
      .filter(p => p.id !== excludePanelId)
      .map(p => p.title)
    if (!others.includes(title)) return title
    let n = 2
    while (others.includes(`${title} (${n})`)) n++
    return `${title} (${n})`
  }

  function createPanel(config: ConnectionConfig | null, type: Panel['type'] = 'ssh'): Panel {
    const id = `panel-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    let title: string
    if (type === 'local') {
      title = 'Local'
    } else if (config) {
      title = `${config.host} ${config.user}`
    } else {
      title = 'New Panel'
    }
    const uniqueTitle = makeTitleUnique(title)
    const panel: Panel = {
      id,
      tabId: '',
      type,
      sessionId: null,
      title: uniqueTitle,
      status: 'disconnected',
      config
    }
    panelState.panels.set(id, panel)
    return panel
  }

  function removePanel(id: string) {
    const p = panelState.panels.get(id)
    // Close any active output log so the footer banner is written and
    // the file handle is released. Fire-and-forget; the backend logs
    // any error via its own facilities.
    DisableSessionOutputLog(id).catch(() => {})
    if (p?.sessionId) {
      UnregisterSession(p.sessionId).catch(() => {})
    }
    panelState.panels.delete(id)
  }

  function getPanel(id: string): Panel | undefined {
    return panelState.panels.get(id)
  }

  function bindSession(panelId: string, sessionId: string) {
    const p = panelState.panels.get(panelId)
    if (!p) return
    const prev = p.sessionId
    p.sessionId = sessionId
    // Tell the backend which panel this session belongs to so per-panel
    // output logging survives reconnects. The previous session's binding
    // is dropped best-effort — if it's already gone the backend no-ops.
    if (prev && prev !== sessionId) {
      UnregisterSession(prev).catch(() => {})
    }
    if (sessionId) {
      RegisterSessionForPanel(sessionId, panelId).catch(() => {})
    }
  }

  function updateStatus(panelId: string, status: PanelStatus) {
    const p = panelState.panels.get(panelId)
    if (p) p.status = status
  }

  function updateTitle(panelId: string, title: string) {
    const p = panelState.panels.get(panelId)
    if (!p) return
    p.title = makeTitleUnique(title, panelId)
  }

  function setOutputLog(panelId: string, state: { enabled: boolean; path: string }) {
    const p = panelState.panels.get(panelId)
    if (p) p.outputLog = state
  }

  function movePanelToTab(panelId: string, tabId: string) {
    const p = panelState.panels.get(panelId)
    if (p) p.tabId = tabId
  }

  function getTransferTasks(panelId: string): TransferTaskUI[] {
    if (!panelState.transferTasks.has(panelId)) {
      panelState.transferTasks.set(panelId, [])
    }
    return panelState.transferTasks.get(panelId)!
  }

  function removeTransferTasks(key: string) {
    panelState.transferTasks.delete(key)
  }

  function setProxyAddr(panelId: string, addr: string) {
    panelState.proxyAddrs.set(panelId, addr)
  }

  function getProxyAddr(panelId: string): string | undefined {
    return panelState.proxyAddrs.get(panelId)
  }

  function removeProxyAddr(panelId: string) {
    panelState.proxyAddrs.delete(panelId)
  }

  function setVNCCache(panelId: string, cache: VNCCache) {
    panelState.vncCaches.set(panelId, cache)
  }

  function getVNCCache(panelId: string): VNCCache | undefined {
    return panelState.vncCaches.get(panelId)
  }

  function removeVNCCache(panelId: string) {
    const cached = panelState.vncCaches.get(panelId)
    if (cached) {
      if (cached.container.parentNode) {
        cached.container.parentNode.removeChild(cached.container)
      }
      panelState.vncCaches.delete(panelId)
    }
  }

  function disconnectVNCCache(panelId: string) {
    const cached = panelState.vncCaches.get(panelId)
    if (cached) {
      try { cached.rfb?.disconnect() } catch (_) {}
    }
  }

  function setSPICECache(panelId: string, cache: SPICECache) {
    panelState.spiceCaches.set(panelId, cache)
  }

  function getSPICECache(panelId: string): SPICECache | undefined {
    return panelState.spiceCaches.get(panelId)
  }

  function removeSPICECache(panelId: string) {
    const cached = panelState.spiceCaches.get(panelId)
    if (cached) {
      if (cached.container.parentNode) {
        cached.container.parentNode.removeChild(cached.container)
      }
      panelState.spiceCaches.delete(panelId)
    }
  }

  function disconnectSPICECache(panelId: string) {
    const cached = panelState.spiceCaches.get(panelId)
    if (cached) {
      try { cached.sc?.stop() } catch (_) {}
    }
  }

  return {
    panels: panelState.panels,
    transferTasks: panelState.transferTasks,
    proxyAddrs: panelState.proxyAddrs,
    vncCaches: panelState.vncCaches,
    getTransferTasks,
    removeTransferTasks,
    createPanel,
    removePanel,
    getPanel,
    bindSession,
    updateStatus,
    updateTitle,
    setOutputLog,
    movePanelToTab,
    setProxyAddr,
    getProxyAddr,
    removeProxyAddr,
    setVNCCache,
    getVNCCache,
    removeVNCCache,
    disconnectVNCCache,
    setSPICECache,
    getSPICECache,
    removeSPICECache,
    disconnectSPICECache
  }
})
