<template>
  <div class="container-tab">
    <div class="container-toolbar">
      <el-select
        v-if="session?.runtime === 'nerdctl'"
        :model-value="session.namespace"
        size="small"
        style="width: 8.75rem"
        filterable
        allow-create
        @change="onNamespaceChange"
      >
        <el-option v-for="ns in namespaceOptions" :key="ns" :label="ns" :value="ns" />
      </el-select>
      <el-input
        v-model="filter"
        size="small"
        :placeholder="t('k8s.filter')"
        clearable
        style="width: 12.5rem"
      />
      <div class="toolbar-spacer" />
      <el-button size="small" @click="createOpen = true">{{ t('container.create') }}</el-button>
      <el-button size="small" :icon="RefreshCw" @click="store.refresh(tab.id)" />
      <el-radio-group :model-value="view" size="small" @change="onViewChange">
        <el-radio-button value="containers">{{ t('container.containers') }}</el-radio-button>
        <el-radio-button value="images">{{ t('container.images') }}</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="session?.error" class="container-error">{{ session.error }}</div>
    <div v-else-if="!session || session.loading" class="container-loading">{{ t('container.loading') }}</div>

    <template v-else>
      <div v-show="view === 'containers'" class="container-table-wrap">
        <el-table
          :data="filteredContainers"
          size="small"
          height="calc(100% - 2.5rem)"
          class="k8s-list-table"
          border
          @row-click="openDetail"
        >
          <el-table-column :label="t('container.colName')" :min-width="uiPx(180)" sortable :sort-method="(a, b) => a.name.localeCompare(b.name)" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('container.colImage')" :min-width="uiPx(220)" sortable :sort-method="(a, b) => a.image.localeCompare(b.image)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.image }}</template>
          </el-table-column>
          <el-table-column
            :label="t('container.colState')"
            :width="uiPx(110)"
            sortable
            :sort-method="(a, b) => a.state.localeCompare(b.state)"
            :filters="stateFilters"
            :filter-method="(val, row) => row.state === val"
          >
            <template #default="{ row }">
              <span :data-state="row.state" class="container-state">{{ row.state }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('container.colPorts')" :min-width="uiPx(160)" sortable :sort-method="(a, b) => a.ports.localeCompare(b.ports)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.ports }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colCreated')" :min-width="uiPx(130)" sortable :sort-method="(a, b) => a.createdAt.localeCompare(b.createdAt)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.createdAt }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colActions')" :width="uiPx(172)" fixed="right" class-name="k8s-action-cell">
            <template #default="{ row }">
              <button class="btn btn-ghost btn-icon btn-sm" :title="t('container.exec')" @click.stop="openExec(row)">
                <SquareTerminal :size="'0.875rem'" />
              </button>
              <button class="btn btn-ghost btn-icon btn-sm" :title="t('container.logs')" @click.stop="openLogs(row)">
                <ScrollText :size="'0.875rem'" />
              </button>
              <button v-if="row.state !== 'running'" class="btn btn-ghost btn-icon btn-sm" :title="t('container.start')" @click.stop="runAction(row, 'start')">
                <Play :size="'0.875rem'" />
              </button>
              <button v-if="row.state === 'running'" class="btn btn-ghost btn-icon btn-sm" :title="t('container.stop')" @click.stop="runAction(row, 'stop')">
                <Square :size="'0.875rem'" />
              </button>
              <button v-if="session?.runtime !== 'wslc'" class="btn btn-ghost btn-icon btn-sm" :title="t('container.restart')" @click.stop="runAction(row, 'restart')">
                <Power :size="'0.875rem'" />
              </button>
              <button v-if="session?.runtime !== 'wslc'" class="btn btn-ghost btn-icon btn-sm" :title="t('container.rename')" @click.stop="onRename(row)">
                <Pencil :size="'0.875rem'" />
              </button>
              <button class="btn btn-ghost btn-icon btn-sm danger" :title="t('container.remove')" @click.stop="onRemove(row)">
                <Trash2 :size="'0.875rem'" />
              </button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-show="view === 'images'" class="container-table-wrap">
        <el-table
          :data="filteredImages"
          size="small"
          height="calc(100% - 5.0rem)"
          class="k8s-list-table"
          border
        >
          <el-table-column :label="t('container.colRepository')" :min-width="uiPx(220)" sortable :sort-method="(a, b) => a.repository.localeCompare(b.repository)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.repository }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colTag')" :min-width="uiPx(140)" sortable :sort-method="(a, b) => a.tag.localeCompare(b.tag)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.tag }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colId')" :width="uiPx(130)">
            <template #default="{ row }">{{ shortId(row.id) }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colSize')" :width="uiPx(110)" sortable :sort-method="(a, b) => a.size.localeCompare(b.size)">
            <template #default="{ row }">{{ row.size }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colCreated')" :min-width="uiPx(130)" sortable :sort-method="(a, b) => a.createdAt.localeCompare(b.createdAt)" show-overflow-tooltip>
            <template #default="{ row }">{{ row.createdAt }}</template>
          </el-table-column>
          <el-table-column :label="t('container.colActions')" :width="uiPx(38)" fixed="right" class-name="k8s-action-cell">
            <template #default="{ row }">
              <button class="btn btn-ghost btn-icon btn-sm danger" :title="t('container.removeImage')" @click.stop="onRemoveImage(row)">
                <Trash2 :size="'0.875rem'" />
              </button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pull-actions">
          <el-input v-model="pullImage" size="small" :placeholder="t('container.pullPlaceholder')" style="width: 20.0rem" @keyup.enter="onPull" />
          <el-button size="small" :loading="pulling" @click="onPull">{{ t('container.pull') }}</el-button>
        </div>
        <div v-if="pullLines.length" class="pull-log">
          <div v-for="(l, i) in pullLines" :key="i" class="log-line">{{ l }}</div>
        </div>
      </div>
    </template>

    <ContainerDetailDrawer
      :mode="drawerMode"
      :tab-id="tab.id"
      :target="drawerTarget"
      @close="drawerMode = null"
    />
    <ContainerCreateDialog v-model="createOpen" :tab-id="tab.id" @created="store.refresh(tab.id)" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox, ElTable, ElTableColumn } from 'element-plus'
import { RefreshCw, SquareTerminal, ScrollText, Play, Square, Power, Pencil, Trash2 } from '@lucide/vue'
import { useContainerStore } from '../stores/containerStore'
import * as client from '../services/containerClient'
import type { StreamHandle } from '../services/containerClient'
import { useI18n } from '../i18n'
import ContainerDetailDrawer from './ContainerDetailDrawer.vue'
import ContainerCreateDialog from './ContainerCreateDialog.vue'
import type { ContainerImage, ContainerInfo, ContainerTab } from '../types/container'
import { uiPx } from '../utils/uiScale'

const props = defineProps<{ tab: ContainerTab }>()

const { t } = useI18n()
const store = useContainerStore()
const session = computed(() => store.sessions[props.tab.id])

const namespaceOptions = computed(() => {
  const s = session.value
  if (!s) return []
  const set = new Set(s.namespaces.length ? s.namespaces : [s.namespace])
  set.add('default')
  return [...set]
})

const view = ref<'containers' | 'images'>('containers')

// ── search / filter ────────────────────────────────────────────
const filter = ref('')
const filteredContainers = computed(() => {
  const f = filter.value.trim().toLowerCase()
  const list = session.value?.containers || []
  return f ? list.filter(c => c.name.toLowerCase().includes(f)) : list
})
const filteredImages = computed(() => {
  const f = filter.value.trim().toLowerCase()
  const list = session.value?.images || []
  return f ? list.filter(i => i.repository.toLowerCase().includes(f)) : list
})
const stateFilters = computed(() => {
  const set = new Set<string>()
  for (const c of session.value?.containers || []) set.add(c.state)
  return [...set].filter(Boolean).sort().map(v => ({ text: v, value: v }))
})

function onViewChange(v: string | number | boolean) {
  view.value = v as 'containers' | 'images'
  if (view.value === 'images') store.loadImages(props.tab.id)
}

async function onNamespaceChange(ns: string) {
  try {
    await store.setNamespace(props.tab.id, ns)
  } catch (e: any) {
    ElMessage.error(String(e?.message || e))
  }
}

// ── drawer / create ────────────────────────────────────────────
const drawerMode = ref<'detail' | 'logs' | null>(null)
const drawerTarget = ref<ContainerInfo | null>(null)
const createOpen = ref(false)

function openDetail(c: ContainerInfo) {
  drawerMode.value = 'detail'
  drawerTarget.value = c
}
function openLogs(c: ContainerInfo) {
  drawerTarget.value = c
  drawerMode.value = 'logs'
}
async function openExec(c: ContainerInfo) {
  try {
    await store.openContainerExec(props.tab, c)
  } catch (e: any) {
    ElMessage.error(String(e?.message || e))
  }
}

// ── actions ────────────────────────────────────────────────────
async function runAction(c: ContainerInfo, act: string) {
  try {
    if (act === 'start' || act === 'stop' || act === 'restart') {
      await ElMessageBox.confirm(
        t('container.actionConfirm', { action: t('container.' + act), name: c.name }),
        t('common.confirm'),
        { type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') },
      )
    }
    await store.action(props.tab.id, c.id, act)
  } catch (e: any) {
    if (e === 'cancel' || e === 'close') return
    ElMessage.error(String(e?.message || e))
  }
}

async function onRename(c: ContainerInfo) {
  try {
    const { value } = await ElMessageBox.prompt(
      t('container.renameMessage', { name: c.name }),
      t('container.rename'),
      { inputValue: c.name, confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') },
    )
    if (value && value !== c.name) await store.rename(props.tab.id, c.id, value)
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(String(e?.message || e))
  }
}

async function onRemove(c: ContainerInfo) {
  try {
    await ElMessageBox.confirm(
      t('container.removeConfirm', { name: c.name }),
      t('common.confirm'),
      { type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') },
    )
    await store.action(props.tab.id, c.id, 'rm')
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(String(e?.message || e))
  }
}

async function onRemoveImage(img: ContainerImage) {
  try {
    await ElMessageBox.confirm(
      t('container.removeImageConfirm', { name: `${img.repository}:${img.tag}` }),
      t('common.confirm'),
      { type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') },
    )
    const s = session.value
    if (!s) return
    await client.removeImage(s.connId, img.id)
    await store.loadImages(props.tab.id)
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(String(e?.message || e))
  }
}

// ── image pull ─────────────────────────────────────────────────
const pullImage = ref('')
const pulling = ref(false)
const pullLines = ref<string[]>([])
let pullHandle: StreamHandle | null = null

async function onPull() {
  const s = session.value
  const image = pullImage.value.trim()
  if (!s || !image || pulling.value) return
  pullLines.value = []
  pulling.value = true
  try {
    pullHandle = await client.startPull(s.connId, image,
      (line) => pullLines.value.push(line),
      (err) => {
        pulling.value = false
        pullHandle = null
        if (err) ElMessage.error(err)
        else store.loadImages(props.tab.id)
      },
    )
  } catch (e: any) {
    pulling.value = false
    ElMessage.error(String(e?.message || e))
  }
}

function shortId(id: string) {
  const raw = id.replace(/^sha256:/, '')
  return raw.length > 12 ? raw.slice(0, 12) : raw
}

function onReconnectEvent(e: Event) {
  const panelId = (e as CustomEvent)?.detail?.panelId
  if (panelId && panelId === props.tab.panelId) reconnect()
}

// Force-reconnect: close the current container connection, then re-open it
// (open() re-initializes loading/error state and reconnects the client).
async function reconnect() {
  try { store.close(props.tab.id) } catch (_) {}
  await store.open(props.tab)
}

onMounted(() => {
  store.open(props.tab)
  // Tab right-click 「重连」(Reconnect) menu → forced reconnect of this tab.
  window.addEventListener('panel:reconnect', onReconnectEvent)
})
onBeforeUnmount(() => {
  window.removeEventListener('panel:reconnect', onReconnectEvent)
  pullHandle?.stop()
  store.close(props.tab.id)
})
</script>

<style scoped>
.container-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.container-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  border-bottom: 1px solid var(--el-border-color-lighter, #333);
  flex-shrink: 0;
}

.toolbar-spacer {
  flex: 1;
}

.container-error {
  color: var(--el-color-danger, #f56);
  padding: 0.75rem;
  white-space: pre-wrap;
}

.container-loading {
  padding: 0.75rem;
  opacity: 0.7;
}

.container-table-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.k8s-list-table {
  flex: 1;
}

/* Action-column cell: tighter padding + 0.25rem gap between .btn-icon buttons
   (mirrors K8sResourceList's action-cell styling). */
.k8s-list-table :deep(.k8s-action-cell .cell) {
  padding: 0 0.25rem;
  white-space: nowrap;
  display: flex;
  align-items: center;
}
.k8s-list-table :deep(.k8s-action-cell .btn-icon + .btn-icon) {
  margin-left: 0.25rem;
}

.k8s-list-table :deep(.el-table__row) {
  cursor: pointer;
}

.container-state[data-state='running'] {
  color: var(--el-color-success, #67c23a);
}

.container-state[data-state='paused'] {
  color: var(--el-color-warning, #e6a23c);
}

.pull-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  flex-shrink: 0;
}

.pull-log {
  margin: 0 0.625rem 0.625rem;
  padding: 0.5rem 0.75rem;
  max-height: 15rem;
  overflow: auto;
  background: var(--bg-surface);
  border: 1px solid var(--el-border-color-lighter, #333);
  border-radius: var(--radius-sm, 0.25rem);
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  user-select: text;
}

.pull-log .log-line {
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
