<template>
  <div class="detail-drawer-backdrop" :class="{ open: !!mode }" @click.self="$emit('close')"></div>
  <div class="detail-drawer" :class="{ open: !!mode }" :style="mode ? { width: drawerWidth + 'px' } : undefined" @click.stop>
    <div class="drawer-resizer" @mousedown="onResizeStart"></div>
    <div class="detail-drawer-header">
      <span class="detail-drawer-title">{{ target?.name || '' }}</span>
      <el-button link @click="$emit('close')"><el-icon><Close :size="'1rem'" /></el-icon></el-button>
    </div>

    <template v-if="mode === 'detail'">
      <div class="db-tabs">
        <button class="db-tab" :class="{ active: tab === 'struct' }" @click="tab = 'struct'">{{ t('container.detail') }}</button>
        <button class="db-tab" :class="{ active: tab === 'json' }" @click="tab = 'json'">JSON</button>
      </div>

      <div v-show="tab === 'struct'" class="detail-body" @contextmenu="onCopyContextMenu">
        <div v-if="detailError" class="detail-section">
          <div class="detail-row"><span class="detail-value">{{ detailError }}</span></div>
        </div>
        <div v-else-if="detailLoading" class="detail-section">
          <div class="detail-row"><span class="detail-value">{{ t('container.detailLoading') }}</span></div>
        </div>
        <div v-for="sec in detailSections" :key="sec.label" class="detail-section">
          <div class="detail-section-title">{{ sec.label }}</div>
          <div v-for="f in sec.fields" :key="f[0]" class="detail-row">
            <span class="detail-label">{{ f[0] }}</span>
            <span class="detail-value">{{ f[1] || '—' }}</span>
          </div>
        </div>
      </div>

      <div v-show="tab === 'json'" class="json-pane">
        <div class="json-actions">
          <el-button size="small" @click="copyRaw">{{ t('container.copy') }}</el-button>
        </div>
        <pre class="json-body" @contextmenu="onCopyContextMenu">{{ prettyRaw }}</pre>
      </div>
    </template>

    <div v-else-if="mode === 'logs'" class="logs-pane">
      <div class="logs-toolbar">
        <el-select v-model="logTail" size="small" style="width: 5.625rem" @change="restartLogs">
          <el-option :value="100" label="100" />
          <el-option :value="500" label="500" />
          <el-option :value="2000" label="2000" />
        </el-select>
        <el-checkbox v-model="logTimestamps" border size="small" @change="restartLogs">{{ t('k8s.logTimestamps') }}</el-checkbox>
        <el-checkbox v-model="logWrap" border size="small">{{ t('k8s.logWrap') }}</el-checkbox>
        <el-button size="small" @click="logLines = []">{{ t('k8s.logClear') }}</el-button>
        <el-button size="small" @click="logPaused = !logPaused">{{ logPaused ? t('k8s.logResume') : t('k8s.logPause') }}</el-button>
      </div>
      <div ref="logBody" class="logs-body" :class="{ 'logs-nowrap': !logWrap }" @contextmenu="onCopyContextMenu">
        <div v-for="(l, i) in logLines" :key="i" class="log-line"><span class="log-ts">{{ l.ts }}</span>{{ l.msg }}</div>
      </div>
    </div>

    <Menu ref="copyMenuRef" v-model:visible="copyMenuVisible">
      <MenuItem @click="onCopyMenu">{{ t('container.copy') }}</MenuItem>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElButton, ElIcon, ElMessage, ElSelect, ElOption, ElCheckbox } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import { useContainerStore } from '../stores/containerStore'
import * as client from '../services/containerClient'
import type { StreamHandle } from '../services/containerClient'
import { useI18n } from '../i18n'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import { Clipboard } from '@wailsio/runtime'
import type { ContainerDetail, ContainerInfo, InspectResult } from '../types/container'

const props = defineProps<{ mode: 'detail' | 'logs' | null; tabId: string; target: ContainerInfo | null }>()
defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()
const store = useContainerStore()

// Right-click "复制" on selectable log text — shows only when something is
// selected; positioned at the pointer (Menu.openAt, viewport-adaptive).
const copyMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const copyMenuVisible = ref(false)

function onCopyContextMenu(e: MouseEvent) {
  const sel = window.getSelection()?.toString() || ''
  if (!sel) return
  e.preventDefault()
  e.stopPropagation()
  copyMenuRef.value?.openAt(e.clientX, e.clientY)
}

async function onCopyMenu() {
  const sel = window.getSelection()?.toString() || ''
  if (sel) {
    try { await Clipboard.SetText(sel) } catch { try { await navigator.clipboard.writeText(sel) } catch { /* ignore */ } }
  }
  copyMenuVisible.value = false
}

// Drawer width (draggable). Logs mode widens; not persisted.
const drawerWidth = ref(420)
watch(() => props.mode, (m) => {
  if (m === 'logs' && drawerWidth.value < 640) drawerWidth.value = 640
})
let resizeStartX = 0
let resizeStartW = 0
function onResizeMove(e: MouseEvent) {
  const dx = resizeStartX - e.clientX
  drawerWidth.value = Math.max(320, Math.min(window.innerWidth - 120, resizeStartW + dx))
}
function onResizeEnd() {
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}
function onResizeStart(e: MouseEvent) {
  resizeStartX = e.clientX
  resizeStartW = drawerWidth.value
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
  e.preventDefault()
}

// ── detail mode ────────────────────────────────────────────────
interface DetailSection { label: string; fields: [string, string][] }

const tab = ref<'struct' | 'json'>('struct')
const inspectResult = ref<InspectResult | null>(null)
const detailError = ref('')
const detailLoading = ref(false)
let detailGen = 0

async function loadDetail() {
  const myGen = ++detailGen
  inspectResult.value = null
  detailError.value = ''
  detailLoading.value = true
  try {
    const r = await store.loadDetail(props.tabId, props.target!.id)
    if (myGen !== detailGen) return
    inspectResult.value = r
  } catch (e: any) {
    if (myGen === detailGen) detailError.value = String(e?.message || e)
  } finally {
    if (myGen === detailGen) detailLoading.value = false
  }
}

function sections(d: ContainerDetail): DetailSection[] {
  const ports = (d.ports || []).map(p =>
    `${p.hostIp ? p.hostIp + ':' : ''}${p.hostPort}:${p.containerPort}${p.protocol !== 'tcp' ? '/' + p.protocol : ''}`
  ).join(', ')
  const mounts = (d.mounts || []).map(m => `${m.destination}:${m.source}${m.rw ? '' : ' (ro)'}`).join('\n')
  const env = (d.env || []).join('\n')
  return [
    { label: t('container.secOverview'), fields: [
      [t('container.fName'), d.name], [t('container.fId'), d.id.slice(0, 12)],
      [t('container.fImage'), d.image], [t('container.fState'), d.state],
      [t('container.fRestart'), d.restartPolicy],
    ]},
    { label: t('container.secCommand'), fields: [
      [t('container.fEntrypoint'), d.entrypoint], [t('container.fCommand'), d.command],
      [t('container.fWorkDir'), d.workDir], [t('container.fUser'), d.user],
    ]},
    { label: t('container.secNetwork'), fields: [
      [t('container.fNetMode'), d.networkMode], [t('container.fIP'), d.ip],
      [t('container.fGateway'), d.gateway],
      [t('container.fPorts'), ports],
    ]},
    { label: t('container.secMounts'), fields: mounts ? [[t('container.secMounts'), mounts]] : [] },
    { label: t('container.secEnv'), fields: env ? [[t('container.secEnv'), env]] : [] },
    { label: t('container.secState'), fields: [
      [t('container.fStartedAt'), d.startedAt], [t('container.fFinishedAt'), d.finishedAt],
      [t('container.fExitCode'), d.exitCode == null ? '—' : String(d.exitCode)],
      [t('container.fPid'), d.pid ? String(d.pid) : '—'],
      [t('container.fOOM'), d.oomKilled ? 'yes' : 'no'],
    ]},
  ]
}

const detailSections = computed(() => {
  const d = inspectResult.value?.detail
  if (!d) return []
  return sections(d).filter(s => s.fields.length > 0)
})

const prettyRaw = computed(() => {
  const raw = inspectResult.value?.raw || ''
  if (!raw) return ''
  try { return JSON.stringify(JSON.parse(raw), null, 2) } catch { return raw }
})

async function copyRaw() {
  try { await navigator.clipboard.writeText(prettyRaw.value); ElMessage.success(t('k8s.copied')) }
  catch (e: any) { ElMessage.error(`${t('k8s.copyFailed')}: ${e?.message || e}`) }
}

// ── logs mode ──────────────────────────────────────────────────
const logTail = ref(500)
const logTimestamps = ref(false)
const logWrap = ref(true)
const logPaused = ref(false)
const logLines = ref<{ ts: string; msg: string }[]>([])
const logBody = ref<HTMLElement | null>(null)
let logHandle: StreamHandle | null = null
let logGen = 0

// Split the runtime's "<RFC3339 timestamp> <message>" line into its two parts.
function splitLogLine(line: string): { ts: string; msg: string } {
  const sp = line.indexOf(' ')
  if (sp > 0 && /^\d{4}-\d\d-\d\dT/.test(line)) {
    return { ts: line.slice(0, sp), msg: line.slice(sp + 1) }
  }
  return { ts: '', msg: line }
}

function stopLogs() { logGen++; logHandle?.stop(); logHandle = null }
async function restartLogs() {
  stopLogs()
  const myGen = ++logGen
  logLines.value = []
  if (props.mode !== 'logs' || !props.target) return
  const connId = store.sessions[props.tabId]?.connId
  if (!connId) return
  const handle = await client.startLogs(connId, props.target.id, logTail.value, logTimestamps.value,
    (line) => {
      if (logPaused.value) return
      logLines.value.push(splitLogLine(line))
      if (logLines.value.length > 5000) logLines.value.splice(0, logLines.value.length - 5000)
      nextTick(() => { if (logBody.value) logBody.value.scrollTop = logBody.value.scrollHeight })
    },
    () => {},
  )
  if (myGen !== logGen || props.mode !== 'logs' || !props.target) { handle.stop(); return }
  logHandle = handle
}

watch(() => [props.mode, props.target], () => {
  if (props.mode === 'detail' && props.target) {
    tab.value = 'struct'
    loadDetail()
  }
  if (props.mode === 'logs' && props.target) restartLogs()
  else stopLogs()
})

onBeforeUnmount(stopLogs)
</script>

<style scoped>
/* Shell classes mirror K8sDetailDrawer.vue (scoped styles don't cross components) */
.detail-drawer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
  z-index: 99;
}

.detail-drawer-backdrop.open {
  opacity: 1;
  pointer-events: auto;
}

.detail-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 26.25rem;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border-subtle);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.detail-drawer.open {
  transform: translateX(0);
}

.drawer-resizer {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 0.3125rem;
  cursor: col-resize;
  z-index: 101;
  background: transparent;
  transition: background 0.15s ease;
}
.drawer-resizer:hover {
  background: var(--accent, #4096ff);
}

.detail-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.detail-drawer-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-ui);
}

.detail-section {
  padding: 0 0.25rem;
  margin-bottom: 0.75rem;
}

.detail-row {
  display: flex;
  padding: 0.625rem 0;
  border-bottom: 1px solid var(--border-subtle);
  gap: 0.75rem;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
  flex-shrink: 0;
  width: 6.25rem;
  min-width: 6.25rem;
}

.detail-value {
  font-size: 0.8125rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  word-break: break-all;
  white-space: pre-wrap;
  flex: 1;
  user-select: text;
}

.db-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 0.5rem;
  flex-shrink: 0;
}
.db-tab {
  padding: 0.375rem 1rem;
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  border-bottom: 0.125rem solid transparent;
  transition: all 0.15s ease;
}
.db-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.db-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}

.detail-body { flex: 1; overflow: auto; padding: 0.75rem 1rem; }
.detail-section-title { font-weight: 600; color: var(--text-secondary); margin: 0.5rem 0 0.25rem; }

.json-pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.json-actions { display: flex; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-subtle); }
.json-body {
  margin: 0;
  padding: 0.75rem;
  overflow: auto;
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  white-space: pre-wrap;
  flex: 1;
  user-select: text;
  cursor: text;
}

.logs-pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
/* 统一控件间距，避免 el-checkbox 自带 margin 造成控件左右间隔过大 */
.logs-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-subtle); flex-wrap: wrap; }
.logs-toolbar :deep(.el-checkbox) { margin-right: 0; }
.logs-body {
  flex: 1;
  overflow: auto;
  padding: 0.75rem;
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  user-select: text;
  cursor: text;
}
.log-line { white-space: pre-wrap; word-break: break-all; }
/* 不换行模式：整行不折行，横向滚动 */
.logs-nowrap .log-line { white-space: pre; word-break: normal; }
/* 时间戳灰色，与正文区分；正文用默认色 */
.log-ts { color: var(--text-muted); margin-right: 0.5rem; }
.log-ts:empty { margin-right: 0; }
</style>
