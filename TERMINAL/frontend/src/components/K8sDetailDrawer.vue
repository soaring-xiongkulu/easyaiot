<template>
  <div class="detail-drawer-backdrop" :class="{ open: !!mode }" @click="$emit('close')"></div>
  <div class="detail-drawer" :class="{ open: !!mode }" :style="mode ? { width: drawerWidth + 'px' } : undefined">
    <div class="drawer-resizer" @mousedown="onResizeStart"></div>
    <div class="detail-drawer-header">
      <span class="detail-drawer-title">{{ headerTitle }}</span>
      <el-button link @click="$emit('close')"><el-icon><Close :size="'1rem'" /></el-icon></el-button>
    </div>

    <template v-if="mode === 'detail'">
      <div class="db-tabs">
        <button class="db-tab" :class="{ active: tab === 'struct' }" @click="tab = 'struct'">{{ t('k8s.detail') }}</button>
        <button class="db-tab" :class="{ active: tab === 'yaml' }" @click="tab = 'yaml'">YAML</button>
      </div>

      <div v-show="tab === 'struct'" class="detail-body" @contextmenu="onCopyContextMenu">
        <div v-for="sec in sections" :key="sec.label" class="detail-section">
          <div class="detail-section-title">{{ sec.label }}</div>
          <div v-for="f in sec.fields" :key="f.label" class="detail-row">
            <span class="detail-label">{{ f.label }}</span>
            <span class="detail-value">{{ fieldText(f) }}</span>
          </div>
        </div>
        <!-- Pod events (async) -->
        <div v-if="isPod" class="detail-section">
          <div class="detail-section-title">Events</div>
          <div v-if="eventsError" class="detail-row"><span class="detail-value">{{ eventsError }}</span></div>
          <div v-else-if="!events.length" class="detail-row"><span class="detail-value">—</span></div>
          <div v-else v-for="(ev, i) in events" :key="i" class="detail-row">
            <span class="detail-label">{{ ev.lastTimestamp || ev.eventTime || '' }}</span>
            <span class="detail-value">{{ ev.type }} {{ ev.reason }}: {{ ev.message }}</span>
          </div>
        </div>
      </div>

      <div v-show="tab === 'yaml'" class="yaml-pane">
        <div class="yaml-actions">
          <template v-if="!editing">
            <el-button size="small" @click="startEdit">{{ t('k8s.edit') }}</el-button>
            <el-button size="small" @click="copyYaml">{{ t('k8s.copy') }}</el-button>
          </template>
          <template v-else>
            <el-button size="small" type="primary" :loading="saving" @click="save">{{ t('common.save') }}</el-button>
            <el-button size="small" @click="cancelEdit">{{ t('common.cancel') }}</el-button>
          </template>
        </div>
        <pre v-if="!editing" class="k8s-yaml-drawer-body" @contextmenu="onCopyContextMenu">{{ yamlText }}</pre>
        <SyntaxEditor v-else v-model="draft" lang="yaml" compact />
        <div v-if="saveError" class="yaml-error">{{ saveError }}</div>
      </div>
    </template>

    <div v-else-if="mode === 'logs'" class="logs-pane">
      <div class="logs-toolbar">
        <el-select v-model="logContainer" size="small" style="width: 10.0rem" @change="restartLogs">
          <el-option v-for="c in containerNames" :key="c" :label="c" :value="c" />
        </el-select>
        <el-select v-model="logTail" size="small" style="width: 5.625rem" @change="restartLogs">
          <el-option :value="100" label="100" />
          <el-option :value="500" label="500" />
          <el-option :value="2000" label="2000" />
        </el-select>
        <el-checkbox v-model="logPrevious" border size="small" @change="restartLogs">{{ t('k8s.logPrevious') }}</el-checkbox>
        <el-checkbox v-model="logTimestamps" border size="small">{{ t('k8s.logTimestamps') }}</el-checkbox>
        <el-checkbox v-model="logWrap" border size="small">{{ t('k8s.logWrap') }}</el-checkbox>
        <el-button size="small" @click="logLines = []">{{ t('k8s.logClear') }}</el-button>
        <el-button size="small" @click="logPaused = !logPaused">{{ logPaused ? t('k8s.logResume') : t('k8s.logPause') }}</el-button>
      </div>
      <div
        ref="logBody"
        class="k8s-yaml-drawer-body logs-body"
        :class="{ 'logs-hide-ts': !logTimestamps, 'logs-nowrap': !logWrap }"
        @contextmenu="onCopyContextMenu"
      >
        <div v-for="(l, i) in logLines" :key="i" class="log-line"><span class="log-ts">{{ l.ts }}</span>{{ l.msg }}</div>
      </div>
    </div>

    <Menu ref="copyMenuRef" v-model:visible="copyMenuVisible">
      <MenuItem @click="onCopyMenu">{{ t('k8s.copy') }}</MenuItem>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElButton, ElIcon, ElMessage, ElSelect, ElOption, ElCheckbox } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import { dump, load } from 'js-yaml'
import { getResource, genericDetailSections, type DetailSection } from '../services/k8sResources'
import { requestJSON, startLogStream, type LogHandle } from '../services/k8sClient'
import { useI18n } from '../i18n'
import Menu from './Menu.vue'
import SyntaxEditor from './SyntaxEditor.vue'
import { Clipboard } from '@wailsio/runtime'
import MenuItem from './MenuItem.vue'

const props = defineProps<{ connId: string; mode: 'detail' | 'logs' | null; target: any | null; resourceKey: string; selfPathOverride?: (obj: any) => string; initialTab?: 'detail' | 'yaml' }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'saved'): void }>()

const { t } = useI18n()

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

// Drawer width (draggable). Defaults widen for logs mode; not persisted.
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

const tab = ref<'struct' | 'yaml'>('struct')
const editing = ref(false)
const draft = ref('')
const saving = ref(false)
const saveError = ref('')

watch(() => props.target, () => {
  tab.value = props.initialTab === 'yaml' ? 'yaml' : 'struct'
  editing.value = false; saveError.value = ''
  events.value = []; eventsError.value = ''
  if (isPod.value) loadEvents()
})

const headerTitle = computed(() => {
  const o = props.target
  if (!o) return ''
  return `${o.kind || getResource(props.resourceKey)?.kind || '?'} / ${o.metadata?.namespace || 'cluster'} / ${o.metadata?.name || ''}`
})

const sections = computed<DetailSection[]>(() => {
  const desc = getResource(props.resourceKey)
  if (desc?.detailSections?.length) return desc.detailSections
  return genericDetailSections()
})

function fieldText(f: any): string {
  if (!props.target) return ''
  const v = f.value(props.target)
  return typeof v === 'object' && v ? v.text : String(v ?? '')
}

// ── Pod events (async fetch; can't ride the synchronous detailSections model) ──
const events = ref<any[]>([])
const eventsError = ref('')
const isPod = computed(() => {
  if (props.mode !== 'detail' || !props.target) return false
  const kind = props.target.kind || getResource(props.resourceKey)?.kind
  return props.resourceKey === 'pods' || kind === 'Pod'
})
let eventsGen = 0
async function loadEvents() {
  const myGen = ++eventsGen
  const o = props.target
  if (!o?.metadata) return
  const ns = o.metadata.namespace || ''
  const name = o.metadata.name || ''
  const path = `/api/v1/namespaces/${encodeURIComponent(ns)}/events?fieldSelector=involvedObject.name%3D${encodeURIComponent(name)}&limit=200`
  try {
    const { status, data, raw } = await requestJSON<any>(props.connId, 'GET', path)
    if (myGen !== eventsGen) return
    if (status === 200 && data) {
      events.value = (data.items || []).slice().sort((a: any, b: any) =>
        String(a.lastTimestamp || a.eventTime || '').localeCompare(String(b.lastTimestamp || b.eventTime || '')))
    } else {
      eventsError.value = `HTTP ${status}: ${raw?.slice(0, 200) || ''}`
    }
  } catch (e: any) {
    if (myGen === eventsGen) eventsError.value = String(e?.message || e)
  }
}

const yamlText = computed(() => {
  if (!props.target) return ''
  try { return dump(props.target, { sortKeys: false, lineWidth: 120 }) }
  catch (e: any) { return `# dump failed: ${e?.message || e}` }
})

function startEdit() { draft.value = yamlText.value; editing.value = true; saveError.value = '' }
function cancelEdit() { editing.value = false; saveError.value = '' }
async function copyYaml() {
  try { await navigator.clipboard.writeText(yamlText.value); ElMessage.success(t('k8s.copied')) }
  catch (e: any) { ElMessage.error(`${t('k8s.copyFailed')}: ${e?.message || e}`) }
}

function selfPath(o: any): string {
  if (props.selfPathOverride) return props.selfPathOverride(o)
  const desc = getResource(props.resourceKey)!
  const ns = o.metadata?.namespace
  const base = desc.listPath(ns || '').split('?')[0]
  return `${base}/${encodeURIComponent(o.metadata?.name)}`
}

async function save() {
  saving.value = true; saveError.value = ''
  try {
    const parsed = load(draft.value) as any
    if (!parsed || typeof parsed !== 'object') throw new Error('YAML is not an object')
    const { status, raw } = await requestJSON(props.connId, 'PUT', selfPath(props.target), JSON.stringify(parsed), 'application/json')
    if (status < 200 || status >= 300) throw new Error(`HTTP ${status}: ${raw?.slice(0, 200) || ''}`)
    editing.value = false
    emit('saved')
    emit('close')
    ElMessage.success(t('k8s.saved'))
  } catch (e: any) {
    saveError.value = String(e?.message || e)
  } finally {
    saving.value = false
  }
}

const logContainer = ref('')
const logTail = ref(500)
const logPrevious = ref(false)
const logTimestamps = ref(false)
const logWrap = ref(false)
const logPaused = ref(false)
// 日志始终自动滚动到底部（不再提供开关）。
// Timestamps are always streamed from the API; visibility is a CSS-only toggle
// (see .logs-hide-ts), so switching the checkbox never re-fetches the log.
const logLines = ref<{ ts: string; msg: string }[]>([])
const logBody = ref<HTMLElement | null>(null)
let logHandle: LogHandle | null = null
let logGen = 0

const containerNames = computed(() => (props.target?.spec?.containers || []).map((c: any) => c.name))

// Split the API's "<RFC3339 timestamp> <message>" line into its two parts.
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
  const ns = props.target.metadata?.namespace
  const pod = props.target.metadata?.name
  const handle = await startLogStream(
    props.connId, ns, pod, logContainer.value, logTail.value, true, logPrevious.value,
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
  if (props.mode === 'logs' && props.target) {
    logContainer.value = containerNames.value[0] || ''
    restartLogs()
  } else {
    stopLogs()
  }
})

onBeforeUnmount(stopLogs)
</script>

<style scoped>
/* Copied verbatim from MonitorTabContent.vue */
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

/* Detail rows copied from MonitorTabContent.vue (.process-detail rows); the
   per-section scroll is dropped so the whole detail-body scrolls once. */
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

/* Copied verbatim from DBTabContent.vue */
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

/* Preformatted YAML body */
.k8s-yaml-drawer-body {
  margin: 0;
  padding: 0.75rem;
  overflow: auto;
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  white-space: pre-wrap;
  height: 100%;
  box-sizing: border-box;
  user-select: text;
  cursor: text;
}

.detail-body { flex: 1; overflow: auto; padding: 0.75rem 1rem; }
.detail-section-title { font-weight: 600; color: var(--text-secondary); margin: 0.5rem 0 0.25rem; }
.yaml-pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.yaml-actions { display: flex; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-subtle); }
.yaml-error { color: var(--el-color-danger, #f56); padding: 0.5rem 0.75rem; font-size: 0.75rem; }

.detail-drawer.wide { width: 40rem; }
.logs-pane { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
/* 统一控件间距，避免 el-checkbox 自带 margin 造成时间戳等控件左右间隔过大 */
.logs-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-subtle); flex-wrap: wrap; }
.logs-toolbar :deep(.el-checkbox) { margin-right: 0; }
.logs-body { flex: 1; overflow: auto; }
.log-line { white-space: pre-wrap; word-break: break-all; }
/* 不换行模式：整行不折行，横向滚动 */
.logs-nowrap .log-line { white-space: pre; word-break: normal; }
/* 时间戳与正文之间留一个空格 */
.log-ts { color: var(--text-muted); margin-right: 0.5rem; }
.log-ts:empty { margin-right: 0; }
.logs-hide-ts .log-ts { display: none; }
</style>
