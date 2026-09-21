<template>
  <div
    class="companion-sidebar monitor-sidebar"
  >
    <div v-if="!sessionId" class="companion-empty">
      <span v-if="connecting">{{ t('companion.connecting') }}</span>
      <span v-else-if="connectError">{{ connectError }}</span>
      <span v-else>{{ t('companion.needSsh') }}</span>
    </div>

    <div v-else class="monitor-body">
      <!-- System info -->
      <div class="card">
        <div class="sys-row">
          <span class="sys-label">{{ t('companion.host') }}</span>
          <span class="sys-value" :title="hostText">{{ hostText }}</span>
        </div>
        <div class="sys-row">
          <span class="sys-label">{{ t('monitor.os') }}</span>
          <span class="sys-value" :title="systemInfo?.os || '-'">{{ systemInfo?.os || '-' }}</span>
        </div>
        <div class="sys-row">
          <span class="sys-label">{{ t('monitor.arch') }}</span>
          <span class="sys-value" :title="systemInfo?.arch || '-'">{{ systemInfo?.arch || '-' }}</span>
        </div>
        <div class="sys-row">
          <span class="sys-label">{{ t('companion.uptime') }}</span>
          <span class="sys-value">{{ uptimeText }}</span>
        </div>
      </div>

      <!-- CPU -->
      <div class="card">
        <div class="mem-row">
          <div class="mem-head">
            <span>{{ t('monitor.cpu') }}</span>
            <span class="mem-val cpu">{{ fmtPct(cpu.usage) }}</span>
          </div>
          <div class="mem-bar"><div class="mem-fill cpu" :style="{ width: Math.min(cpu.usage, 100) + '%' }" /></div>
        </div>

        <!-- CPU load average -->
        <div class="load-row">
          <span class="load-label">1m</span>
          <span class="load-val">{{ cpu.load1 }}</span>
          <span class="load-label">5m</span>
          <span class="load-val">{{ cpu.load5 }}</span>
          <span class="load-label">15m</span>
          <span class="load-val">{{ cpu.load15 }}</span>
        </div>

        <div class="expand-toggle" @click="showCores = !showCores">
          <ChevronRight :size="'0.75rem'" class="chev" :class="{ open: showCores }" />
          <span>{{ t('monitor.allCores') }} ({{ cpus.length }})</span>
        </div>
        <div v-if="showCores" class="detail-list">
          <div v-for="c in cpus" :key="c.core" class="detail-row">
            <span class="detail-name">CPU {{ c.core }}</span>
            <div class="detail-bar"><div class="detail-fill" :style="{ width: fmtWidth(c.usage) }" /></div>
            <span class="detail-val">{{ fmtPct(c.usage) }}</span>
          </div>
        </div>
      </div>

      <!-- Memory -->
      <div class="card">
        <div class="mem-row">
          <div class="mem-head">
            <span>{{ t('companion.physMem') }}</span>
            <span class="mem-val">{{ formatMem(mem.used) }} / {{ formatMem(mem.total) }}</span>
          </div>
          <div class="mem-bar"><div class="mem-fill phys" :style="{ width: Math.min(mem.usage, 100) + '%' }" /></div>
        </div>
        <div class="mem-row">
          <div class="mem-head">
            <span>{{ t('companion.swapMem') }}</span>
            <span class="mem-val">{{ formatMem(swap.used) }} / {{ formatMem(swap.total) }}</span>
          </div>
          <div class="mem-bar"><div class="mem-fill swap" :style="{ width: Math.min(swap.usage, 100) + '%' }" /></div>
        </div>
      </div>

      <!-- Network -->
      <div class="card">
        <div class="net-stats">
          <div class="net-stat">
            <span class="net-label">{{ t('companion.netTxRate') }}</span>
            <span class="net-num tx">{{ formatBytes(net.tx) }}/s</span>
          </div>
          <div class="net-stat">
            <span class="net-label">{{ t('companion.netRxRate') }}</span>
            <span class="net-num rx">{{ formatBytes(net.rx) }}/s</span>
          </div>
        </div>

        <div class="expand-toggle" @click="showNets = !showNets">
          <ChevronRight :size="'0.75rem'" class="chev" :class="{ open: showNets }" />
          <span>{{ t('monitor.allNetworks') }} ({{ nets.length }})</span>
        </div>
        <div v-if="showNets" class="detail-list">
          <div v-for="n in nets" :key="n.name" class="detail-row net">
            <span class="detail-name" :title="n.name">{{ n.name }}</span>
            <span class="detail-sub">↓{{ formatBytes(n.rx) }}/s</span>
            <span class="detail-sub tx">↑{{ formatBytes(n.tx) }}/s</span>
          </div>
        </div>
      </div>

      <!-- Disk -->
      <div class="card">
        <div class="mem-row">
          <div class="mem-head">
            <span>{{ t('monitor.disk') }}</span>
            <span class="mem-val">{{ disk.used }} / {{ disk.total }}</span>
          </div>
          <div class="mem-bar"><div class="mem-fill disk" :style="{ width: fmtWidth(disk.usage) }" /></div>
        </div>

        <div class="expand-toggle" @click="toggleDisks">
          <ChevronRight :size="'0.75rem'" class="chev" :class="{ open: showDisks }" />
          <span>{{ t('monitor.allDisks') }} ({{ mountedDisks.length }})</span>
        </div>
        <div v-if="showDisks" class="detail-list">
          <div v-if="diskLoading" class="detail-empty">{{ t('monitor.loading') }}</div>
          <div v-for="d in mountedDisks" v-else :key="d.name + d.mountPoint" class="detail-row disk">
            <span class="detail-name" :title="d.name">{{ d.mountPoint || d.name }}</span>
            <div class="detail-bar"><div class="detail-fill" :style="{ width: fmtWidth(d.usage) }" /></div>
            <span class="detail-val">{{ d.used }} / {{ d.total }}</span>
          </div>
        </div>
      </div>

      <!-- Host clock -->
      <div class="card">
        <div class="sys-row">
          <span class="sys-label">{{ t('monitor.timezone') }}</span>
          <span class="sys-value" :title="systemInfo?.timezone || '-'">{{ systemInfo?.timezone || '-' }}</span>
        </div>
        <div class="sys-row">
          <span class="sys-label">{{ t('monitor.clock') }}</span>
          <span class="sys-value">{{ hostClockText }}</span>
        </div>
        <div class="sys-row">
          <span class="sys-label">{{ t('monitor.skew') }}</span>
          <span class="sys-value">{{ clockSkewText }}</span>
        </div>
      </div>

      <!-- Open full monitor (pinned at the bottom) -->
      <button class="full-monitor-btn" @click="openFullMonitor">
        <ExternalLink :size="'0.875rem'" />
        <span>{{ t('companion.openFullMonitor') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ExternalLink, ChevronRight } from '@lucide/vue'
import { useI18n } from '../i18n'
import { useCompanionStore } from '../stores/companionStore'
import { usePanelStore } from '../stores/panelStore'
import { Events } from '@wailsio/runtime'
import { SetMonitorActiveTab, SetMonitorPaused, GetDisks } from '../../bindings/easyaiot/terminal/app'
const { t } = useI18n()
const companionStore = useCompanionStore()
const panelStore = usePanelStore()

const connecting = ref(false)
const connectError = ref('')
const systemInfo = ref<Record<string, any> | null>(null)

const cpu = ref({ usage: 0, total: 0, user: 0, system: 0, iowait: 0, cores: 0, processes: 0, load1: '-', load5: '-', load15: '-' })
const mem = ref({ total: 0, used: 0, free: 0, usage: 0 })
const swap = ref({ total: 0, used: 0, usage: 0 })
const net = ref({ rx: 0, tx: 0, rxTotal: 0, txTotal: 0 })
const disk = ref({ total: '', used: '', usage: 0 })

// Expandable detail lists: per-core / per-NIC (live from perf payload) and
// per-disk (fetched on-demand via GetDisks when expanded).
const cpus = ref<any[]>([])
const nets = ref<any[]>([])
const disks = ref<any[]>([])
const diskLoading = ref(false)
const showCores = ref(false)
const showNets = ref(false)
const showDisks = ref(false)

// Only directories with a mount point are shown in the disk detail list.
const mountedDisks = computed(() => disks.value.filter((d: any) => d.mountPoint))

const sessionId = computed(() => companionStore.currentMonitorSessionId)

const hostText = computed(() => {
  const ip = systemInfo.value?.localIP
  const pid = companionStore.activeSshPanelId
  const panel = pid ? panelStore.getPanel(pid) : null
  const host = panel?.config?.host || ''
  if (ip) return ip
  if (host) return host
  return '-'
})

const uptimeText = computed(() => {
  const sec = Number(systemInfo.value?.uptimeSec || 0)
  if (!sec) return '-'
  const d = Math.floor(sec / 86400)
  const h = Math.floor((sec % 86400) / 3600)
  const m = Math.floor((sec % 3600) / 60)
  if (d > 0) return `${d}d ${h}h ${m}m`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
})

// Host clock: systemInfo.epochSec is the host's POSIX time at the moment the
// system payload arrived (hostClockAt). Extrapolating with the live tick lets
// the host clock keep ticking, and the skew to the local clock is constant.
const hostClockAt = ref(0)
const clockNow = ref(0)

const hostClockText = computed(() => {
  const base = Number(systemInfo.value?.epochSec)
  if (!base || !hostClockAt.value) return '-'
  const liveMs = base * 1000 + (clockNow.value - hostClockAt.value)
  const tz = systemInfo.value?.timezone
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeZone: tz,
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    }).format(new Date(liveMs))
  } catch {
    return new Date(liveMs).toLocaleTimeString(undefined, { hour12: false })
  }
})

const clockSkewText = computed(() => {
  const base = Number(systemInfo.value?.epochSec)
  if (!base || !hostClockAt.value) return '-'
  // Positive = host clock is ahead of the local machine.
  const s = (base * 1000 - hostClockAt.value) / 1000
  return formatSkew(s)
})

function formatSkew(seconds: number): string {
  const sign = seconds < 0 ? '-' : '+'
  const abs = Math.abs(seconds)
  if (abs < 1) return `${sign}${abs.toFixed(1)}s`
  const d = Math.floor(abs / 86400)
  const h = Math.floor((abs % 86400) / 3600)
  const m = Math.floor((abs % 3600) / 60)
  const s = Math.round(abs % 60)
  if (d > 0) return `${sign}${d}d ${h}h ${m}m`
  if (h > 0) return `${sign}${h}h ${m}m`
  if (m > 0) return `${sign}${m}m ${s}s`
  return `${sign}${s}s`
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes < 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1)
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatMem(gb: number): string {
  if (!gb) return '0 B'
  if (gb < 1) return (gb * 1024).toFixed(0) + ' MB'
  return gb.toFixed(1) + ' GB'
}

function fmtPct(v: number, clamp100 = true): string {
  let n = Number(v)
  if (!Number.isFinite(n)) n = 0
  if (clamp100) n = Math.min(100, Math.max(0, n))
  else n = Math.max(0, n)
  return n.toFixed(1) + '%'
}

function fmtWidth(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n)) return '0%'
  return Math.min(100, Math.max(0, n)) + '%'
}

async function ensureConnected() {
  const pid = companionStore.activeSshPanelId
  if (!pid || !companionStore.monitorVisible) return
  connecting.value = true
  connectError.value = ''
  try {
    const sid = await companionStore.ensureMonitor(pid)
    if (sid) {
      SetMonitorActiveTab(sid, 'overview').catch(() => {})
      // Resume polling now that this sidebar is visible again.
      SetMonitorPaused(sid, false).catch(() => {})
      // Load the disk snapshot so the "all disks" count shows without expanding.
      loadDisks()
    }
  } catch (e: any) {
    connectError.value = e?.toString?.() || t('companion.needSsh')
  } finally {
    connecting.value = false
  }
}

function openFullMonitor() {
  const pid = companionStore.activeSshPanelId
  const panel = pid ? panelStore.getPanel(pid) : null
  if (!panel?.config) return
  window.dispatchEvent(new CustomEvent('app:connect-monitor', { detail: panel }))
}

async function loadDisks() {
  if (disks.value.length > 0) return
  const sid = sessionId.value
  if (!sid) return
  diskLoading.value = true
  try {
    disks.value = await GetDisks(sid)
  } catch {
    disks.value = []
  } finally {
    diskLoading.value = false
  }
}

async function toggleDisks() {
  showDisks.value = !showDisks.value
  if (showDisks.value) await loadDisks()
}

let unsub: (() => void) | null = null
let clockTimer: ReturnType<typeof setInterval> | null = null

function bindListeners() {
  unsub?.()
  unsub = Events.On('session:data', (ev) => { const data: any = ev.data;
    if (data?.id !== sessionId.value) return
    if (typeof data.data === 'string') {
      const connMatch = data.data.match(/\[Connection failed: ([^\]]+)\]/)
      if (connMatch) {
        connectError.value = connMatch[1]
        return
      }
    }
    try {
      const payload = JSON.parse(data.data)
      if (payload.type === 'system') {
        systemInfo.value = payload.system
        hostClockAt.value = Date.now()
        return
      }
      if (payload.type === 'performance') {
        if (payload.cpu) {
          cpu.value = {
            usage: payload.cpu.usage || 0,
            total: payload.cpu.total ?? ((payload.cpu.usage || 0) * (payload.cpu.cores || 1)),
            user: payload.cpu.user || 0,
            system: payload.cpu.system || 0,
            iowait: payload.cpu.iowait || 0,
            cores: payload.cpu.cores || 0,
            processes: payload.cpu.processes || 0,
            load1: payload.cpu.load1 ?? '-',
            load5: payload.cpu.load5 ?? '-',
            load15: payload.cpu.load15 ?? '-',
          }
        }
        if (payload.memory) {
          mem.value = {
            total: payload.memory.total || 0,
            used: payload.memory.used || 0,
            free: payload.memory.free || 0,
            usage: payload.memory.usage || 0,
          }
        }
        if (payload.swap) {
          swap.value = {
            total: payload.swap.total || 0,
            used: payload.swap.used || 0,
            usage: payload.swap.usage || 0,
          }
        }
        if (payload.network) {
          net.value = {
            rx: payload.network.rx || 0,
            tx: payload.network.tx || 0,
            rxTotal: payload.network.rxTotal || 0,
            txTotal: payload.network.txTotal || 0,
          }
          if (Array.isArray(payload.nets)) nets.value = payload.nets
        }
        if (payload.disk) {
          disk.value = {
            total: payload.disk.total || '',
            used: payload.disk.used || '',
            usage: payload.disk.usage || 0,
          }
        }
        if (Array.isArray(payload.cpus)) cpus.value = payload.cpus
      }
    } catch { /* ignore */ }
   })
}

/** Restore this panel's cached monitor data; returns true if a cache existed. */
function restoreCache(): boolean {
  const pid = companionStore.activeSshPanelId
  const cached = pid ? companionStore.getMonitorViewCache(pid) : null
  if (!cached) return false
  systemInfo.value = cached.systemInfo ?? null
  hostClockAt.value = cached.systemInfoAt ?? 0
  cpu.value = { ...cached.cpu }
  mem.value = { ...cached.mem }
  swap.value = { ...cached.swap }
  net.value = { ...cached.net }
  cpus.value = Array.isArray(cached.cpus) ? [...cached.cpus] : []
  nets.value = Array.isArray(cached.nets) ? [...cached.nets] : []
  disks.value = Array.isArray(cached.disks) ? [...cached.disks] : []
  showCores.value = !!cached.expanded?.cores
  showNets.value = !!cached.expanded?.nets
  showDisks.value = !!cached.expanded?.disks
  return true
}

watch(sessionId, (sid) => {
  // Re-entering an already-visited tab: restore its cached values instead of
  // resetting, so switching back shows the previous content instantly.
  if (restoreCache()) {
    if (sid) {
      bindListeners()
      SetMonitorActiveTab(sid, 'overview').catch(() => {})
    }
    return
  }
  // No cache for this panel yet → clear any stale info from the previously
  // viewed panel until the new one reports in.
  systemInfo.value = null
  cpus.value = []
  nets.value = []
  disks.value = []
  showCores.value = false
  showNets.value = false
  showDisks.value = false
  if (!sid) return
  bindListeners()
  SetMonitorActiveTab(sid, 'overview').catch(() => {})
})

// Persist the current values per SSH panel so a later switch-back can restore them.
watch(
  [systemInfo, cpu, mem, swap, net, cpus, nets, disks, showCores, showNets, showDisks],
  () => {
    const pid = companionStore.activeSshPanelId
    if (!pid) return
    companionStore.setMonitorViewCache(pid, {
      systemInfo: systemInfo.value ? { ...systemInfo.value } : null,
      systemInfoAt: hostClockAt.value || Date.now(),
      cpu: { ...cpu.value },
      mem: { ...mem.value },
      swap: { ...swap.value },
      net: { ...net.value },
      cpus: [...cpus.value],
      nets: [...nets.value],
      disks: [...disks.value],
      expanded: { cores: showCores.value, nets: showNets.value, disks: showDisks.value },
    })
  },
  { deep: true },
)

watch(() => companionStore.monitorVisible, (v) => {
  if (v) {
    ensureConnected()
  }
})

watch(() => companionStore.activeSshPanelId, () => {
  if (companionStore.monitorVisible) ensureConnected()
})

onMounted(() => {
  bindListeners()
  // Re-mounting after the view was hidden (e.g. switching files<->monitor):
  // restore this panel's cached data since the session didn't change.
  if (!restoreCache()) {
    // Fresh (never-visited) panel: start collapsed with no stale detail data.
    cpus.value = []
    nets.value = []
    disks.value = []
    showCores.value = false
    showNets.value = false
    showDisks.value = false
  }
  if (companionStore.monitorVisible) ensureConnected()
  // Drive the live host clock.
  const tick = () => { clockNow.value = Date.now() }
  tick()
  clockTimer = window.setInterval(tick, 1000)
})

onUnmounted(() => {
  unsub?.()
  if (clockTimer) window.clearInterval(clockTimer)
  clockTimer = null
  // The sidebar is hidden — pause the companion monitor session so it stops
  // polling the remote host until it is shown again.
  const sid = sessionId.value
  if (sid) SetMonitorPaused(sid, true).catch(() => {})
})
</script>

<style scoped>
.companion-sidebar {
  background: transparent;
  display: flex;
  flex-direction: column;
  position: relative;
  flex: 1 1 0;
  width: 100%;
  height: auto;
  min-height: 0;
  overflow: hidden;
}
.companion-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 1rem;
  text-align: center;
}
.monitor-body {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 0.625rem;
  min-height: 0;
}

.full-monitor-btn {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  flex-shrink: 0;
  padding: 0.625rem;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 0.625rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.full-monitor-btn:hover {
  color: var(--accent);
  background: var(--accent-subtle);
  border-color: var(--accent-subtle);
  box-shadow: 0 0 0 1px var(--accent-subtle) inset;
}

.card {
  background: var(--bg-surface);
  border-radius: 0.625rem;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.sys-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  min-width: 0;
}
.sys-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  flex-shrink: 0;
}
.sys-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: right;
}

.mem-row { display: flex; flex-direction: column; gap: 0.25rem; }
.mem-head {
  display: flex;
  justify-content: space-between;
  font-size: 0.6875rem;
  color: var(--text-secondary);
}
.mem-val {
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}
.mem-val.cpu { color: var(--chart-1, #60a5fa); font-weight: 600; }
.mem-bar {
  height: 0.5rem;
  border-radius: 62.4375rem;
  background: var(--bg-hover);
  overflow: hidden;
}
.mem-fill {
  height: 100%;
  border-radius: 62.4375rem;
  transition: width 0.35s ease;
}
.mem-fill.cpu { background: linear-gradient(90deg, #6366f1, #818cf8); }
.mem-fill.phys { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.mem-fill.swap { background: linear-gradient(90deg, #14b8a6, #2dd4bf); }

.load-row {
  display: flex;
  align-items: baseline;
  gap: 0.375rem;
  flex-wrap: wrap;
}
.load-label {
  font-size: 0.625rem;
  color: var(--text-muted);
}
.load-val {
  font-size: 0.75rem;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: var(--text-secondary);
  margin-right: 0.25rem;
}

.net-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}
.net-stat {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.net-label { font-size: 0.625rem; color: var(--text-muted); }
.net-num {
  font-size: 0.8125rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.net-num.tx { color: #f59e0b; }
.net-num.rx { color: #4ade80; }

.mem-fill.disk { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }

.expand-toggle {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  padding: 0.125rem 0;
  user-select: none;
}
.expand-toggle:hover { color: var(--text-secondary); }
.expand-toggle .chev { transition: transform 0.15s ease; flex-shrink: 0; }
.expand-toggle .chev.open { transform: rotate(90deg); }

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 0.1875rem;
  max-height: 10.625rem;
  overflow: auto;
  padding-top: 0.375rem;
  border-top: 1px solid var(--border-subtle);
}
.detail-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.6875rem;
  min-width: 0;
}
.detail-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  min-width: 0;
}
.detail-bar {
  flex: 1;
  height: 0.3125rem;
  max-width: 5rem;
  border-radius: 62.4375rem;
  background: var(--bg-hover);
  overflow: hidden;
}
.detail-fill {
  height: 100%;
  border-radius: 62.4375rem;
  background: linear-gradient(90deg, var(--accent), var(--accent-glow));
}
.detail-val {
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  min-width: 2.5rem;
  text-align: right;
}
.detail-sub {
  font-variant-numeric: tabular-nums;
  color: var(--text-muted);
  flex-shrink: 0;
}
.detail-sub.tx { color: #f59e0b; }
.detail-row.net .detail-sub {
  width: 4.5rem;
  text-align: right;
}
.detail-empty {
  padding: 0.375rem 0;
  font-size: 0.6875rem;
  color: var(--text-muted);
}
</style>