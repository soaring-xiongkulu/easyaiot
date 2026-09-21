import { defineStore } from 'pinia'
import { ref } from 'vue'
import { Events } from '@wailsio/runtime'
import {
  LoadTunnels, SaveTunnels, StartTunnel, StopTunnel, ListTunnelStates,
} from '../../bindings/easyaiot/terminal/app'
import { msg } from '../services/message'
import { t } from '../i18n'
// Module-level un-subscribers for tunnel:state / store:tunnels:changed listeners.
// Tracked at module scope so re-imports under HMR can detach the previous
// listener before re-subscribing (FE-03).
let unsubTunnelState: (() => void) | null = null
let unsubTunnelsChanged: (() => void) | null = null

export type TunnelMode = 'local' | 'remote' | 'dynamic'
export type TunnelStatus = 'stopped' | 'running' | 'error'

export interface SocksProxy {
  kind: string // 'socks5' | 'http'
  host: string
  port: number
  user?: string
  pass?: string
}

export interface Tunnel {
  id: string
  name: string
  mode: TunnelMode
  sshConnId: string
  listenHost?: string
  listenPort: number
  targetHost?: string
  targetPort?: number
  upstream?: SocksProxy
  autoStart?: boolean
  groupId?: string
  sortOrder?: number
}

export interface TunnelGroup {
  id: string
  name: string
  sortOrder?: number
}

export interface TunnelState {
  id: string
  status: TunnelStatus
  localPort?: number
  error?: string
}

let idCounter = 0
function genId(prefix: string): string {
  return `${prefix}-${Date.now()}-${++idCounter}`
}

export const useTunnelStore = defineStore('tunnels', () => {
  const groups = ref<TunnelGroup[]>([])
  const tunnels = ref<Tunnel[]>([])
  const states = ref<Record<string, TunnelState>>({})
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    try {
      const data = await LoadTunnels()
      groups.value = (data.groups as TunnelGroup[]) || []
      tunnels.value = (data.tunnels as Tunnel[]) || []
    } catch (e) {
      console.error('Failed to load tunnels:', e)
      groups.value = []
      tunnels.value = []
    }
    // Seed runtime states from the backend (auto-started tunnels).
    try {
      const list = await ListTunnelStates()
      for (const st of list) states.value[st.id] = st as TunnelState
    } catch (e) {
      console.error('Failed to list tunnel states:', e)
    }
    // Live state pushes. Errors are toasted here — one place covers manual
    // starts, auto-start failures at app boot and mid-run disconnects. The
    // bare backend error (e.g. "ssh handshake 10.x.x.x:22: ...") carries no
    // tunnel identity, so the toast prefixes the localized tunnel name; the
    // mid-run disconnect gets its own wording instead of "failed to start".
    let lastToastError = ''
    unsubTunnelState?.()
    unsubTunnelState =Events.On('tunnel:state', (ev) => { const st: TunnelState = ev.data;
      if (st.status === 'error' && st.error && st.error !== lastToastError) {
        lastToastError = st.error
        const name = tunnels.value.find(x => x.id === st.id)?.name || st.id
        if (st.error === 'ssh chain disconnected') {
          msg.error(t('tunnels.disconnected', { name }))
        } else {
          msg.error(`${t('tunnels.startFailed', { name })}: ${st.error}`)
        }
      }
      states.value = { ...states.value, [st.id]: st }
     })
    // Cross-window sync.
    unsubTunnelsChanged?.()
    unsubTunnelsChanged =Events.On('store:tunnels:changed', (ev) => { const data: { groups?: TunnelGroup[]; tunnels?: Tunnel[] } = ev.data; 
      groups.value = data.groups || []
      tunnels.value = data.tunnels || []
     })
    loaded.value = true
  }

  function dispose() {
    unsubTunnelState?.()
    unsubTunnelState = null
    unsubTunnelsChanged?.()
    unsubTunnelsChanged = null
  }

  async function save() {
    try {
      await SaveTunnels({
        version: 1,
        groups: JSON.parse(JSON.stringify(groups.value)),
        tunnels: JSON.parse(JSON.stringify(tunnels.value)),
      } as any)
    } catch (e) {
      console.error('Failed to save tunnels:', e)
    }
  }

  function statusOf(id: string): TunnelStatus {
    return states.value[id]?.status || 'stopped'
  }

  function addTunnel(t: Omit<Tunnel, 'id' | 'sortOrder'>): Tunnel {
    const tunnel: Tunnel = {
      ...t,
      id: genId('tun'),
      sortOrder: tunnels.value.filter(x => (x.groupId || undefined) === (t.groupId || undefined)).length,
    }
    tunnels.value.push(tunnel)
    save()
    return tunnel
  }

  function updateTunnel(id: string, patch: Partial<Tunnel>) {
    const idx = tunnels.value.findIndex(t => t.id === id)
    if (idx >= 0) {
      tunnels.value[idx] = { ...tunnels.value[idx], ...patch, id }
      save()
    }
  }

  function deleteTunnel(id: string) {
    stop(id)
    tunnels.value = tunnels.value.filter(t => t.id !== id)
    save()
  }

  function getTunnelsByGroup(groupId?: string): Tunnel[] {
    return tunnels.value
      .filter(t => (t.groupId || undefined) === (groupId || undefined))
      .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
  }

  function addGroup(name: string): TunnelGroup {
    const group: TunnelGroup = { id: genId('tung'), name, sortOrder: groups.value.length }
    groups.value.push(group)
    save()
    return group
  }

  function renameGroup(id: string, name: string) {
    const g = groups.value.find(x => x.id === id)
    if (g) { g.name = name; save() }
  }

  function deleteGroup(id: string, deleteTunnels: boolean) {
    if (deleteTunnels) {
      tunnels.value.filter(t => t.groupId === id).forEach(t => stop(t.id))
      tunnels.value = tunnels.value.filter(t => t.groupId !== id)
    } else {
      tunnels.value.forEach(t => { if (t.groupId === id) t.groupId = undefined })
    }
    groups.value = groups.value.filter(g => g.id !== id)
    save()
  }

  async function start(id: string, user?: string, password?: string): Promise<TunnelState> {
    const st = await StartTunnel(id, user || '', password || '')
    states.value = { ...states.value, [id]: st as TunnelState }
    return st as TunnelState
  }

  async function stop(id: string) {
    try {
      await StopTunnel(id)
      states.value = { ...states.value, [id]: { id, status: 'stopped' } }
    } catch (e) {
      console.error('Failed to stop tunnel:', e)
    }
  }

  return {
    groups, tunnels, states, loaded,
    load, save, statusOf,
    addTunnel, updateTunnel, deleteTunnel, getTunnelsByGroup,
    addGroup, renameGroup, deleteGroup,
    start, stop,
    dispose,
  }
})
