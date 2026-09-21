<template>
  <div class="db-tab-content">
    <div class="db-main">
      <div class="db-left" :style="{ width: leftWidth + 'px' }">
        <DBTreePanel
          ref="treeRef"
          :session-id="sessionId"
          :default-db-name="defaultDbName"
          :active-db="activeDb"
          :active-table="activeTable"
          @select-table="onSelectTable"
          @open-database="onOpenDatabase"
          @view-structure="onViewStructure"
          @new-query="onNewQuery"
          @object-removed="onObjectRemoved"
        />
      </div>
      <div class="db-resizer" @mousedown="onResizeStart" />
      <div class="db-right">
        <div v-if="docs.length === 0" class="db-placeholder">
          <span>{{ t('db.selectTableHint') }}</span>
        </div>
        <template v-else>
          <div class="doc-tabs">
            <div ref="docTabsScrollRef" class="doc-tabs-scroll" @wheel="onTabsWheel">
              <template v-for="(doc, index) in docs" :key="doc.id">
                <div
                  v-if="dragOverIndex === index && dragInsertAfter"
                  class="doc-tab-indicator"
                />
                <button
                  class="doc-tab"
                  :class="{ active: doc.id === activeDocId }"
                  :data-doc-id="doc.id"
                  draggable="true"
                  @click="activateDoc(doc.id)"
                  @auxclick.middle.prevent="closeDoc(doc.id)"
                  @contextmenu.prevent="onDocTabContextMenu($event, doc.id)"
                  @dragstart="onDocDragStart($event, doc.id)"
                  @dragover.prevent="onDocDragOver($event, index)"
                  @dragend="clearDragState"
                  @drop.prevent="onDocDrop($event, index)"
                >
                  <Table2 v-if="doc.kind === 'table' && !doc.isView" :size="'0.75rem'" class="doc-tab-icon" />
                  <Eye v-else-if="doc.kind === 'table'" :size="'0.75rem'" class="doc-tab-icon" />
                  <Database v-else-if="doc.kind === 'db-objects'" :size="'0.75rem'" class="doc-tab-icon" />
                  <Code2 v-else :size="'0.75rem'" class="doc-tab-icon" />
                  <span class="doc-tab-title" :title="docTitle(doc)">{{ docTitle(doc) }}</span>
                  <span class="doc-tab-close" @click.stop="closeDoc(doc.id)">×</span>
                </button>
              </template>
              <div v-if="dragOverIndex === docs.length - 1 && dragInsertAfter" class="doc-tab-indicator" />
            </div>
            <button
              v-if="docTabsShowMore"
              class="doc-tab-more"
              :title="t('tab.more')"
              @click.stop="docMoreMenuRef?.toggle($event.currentTarget)"
            >
              <MoreHorizontal :size="'0.875rem'" />
            </button>
            <Menu ref="docMoreMenuRef" v-model:visible="docMoreMenuVisible" align="end">
              <MenuItem
                v-for="d in docs"
                :key="d.id"
                :class="{ active: d.id === activeDocId }"
                @click="onDocMoreSelect(d.id)"
              >{{ docTitle(d) }}</MenuItem>
            </Menu>
            <button class="doc-tab-new" :title="t('db.newQuery')" @click="onNewQuery()">+</button>
          </div>

          <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
            <template v-if="current">
              <MenuItem @click="onCtxClose(current)">{{ t('tab.close') }}</MenuItem>
              <MenuItem :class="{ disabled: !canCloseOthersOf(current) }" @click="onCtxCloseOthers(current)">{{ t('tab.closeOther') }}</MenuItem>
              <MenuItem :class="{ disabled: !canCloseLeftOf(current) }" @click="onCtxCloseLeft(current)">{{ t('tab.closeLeft') }}</MenuItem>
              <MenuItem :class="{ disabled: !canCloseRightOf(current) }" @click="onCtxCloseRight(current)">{{ t('tab.closeRight') }}</MenuItem>
              <MenuDivider />
              <MenuItem @click="onCtxCloseAll">{{ t('tab.closeAll') }}</MenuItem>
            </template>
          </Menu>

          <div
            v-for="doc in docs"
            v-show="doc.id === activeDocId"
            :key="doc.id"
            class="doc-pane"
          >
            <!-- Table document: data | structure -->
            <template v-if="doc.kind === 'table'">
              <div class="db-subtabs">
                <button
                  class="db-tab"
                  :class="{ active: doc.subTab === 'data' }"
                  @click="doc.subTab = 'data'"
                >
                  {{ t('db.dataQuery') }}
                </button>
                <button
                  v-if="!doc.isView"
                  class="db-tab"
                  :class="{ active: doc.subTab === 'structure' }"
                  @click="openStructureSub(doc)"
                >
                  {{ t('db.tableStructure') }}
                </button>
              </div>
              <div class="db-right-top-content">
                <DBQueryEditor
                  v-show="doc.subTab === 'data'"
                  :session-id="sessionId"
                  :table-name="doc.tableName"
                  :db-name="doc.dbName"
                  :db-type="dbType"
                  :primary-keys="doc.primaryKeys"
                  :table-columns="doc.tableColumns"
                  :is-view="doc.isView"
                />
                <DBTableStructure
                  v-show="doc.subTab === 'structure' && !doc.isView"
                  :session-id="sessionId"
                  :db-name="doc.dbName"
                  :table-name="doc.tableName"
                  :load-trigger="doc.structureLoadTrigger"
                  @schema-loaded="(pks) => onSchemaLoaded(doc, pks)"
                />
              </div>
            </template>

            <!-- Database query -->
            <template v-else-if="doc.kind === 'db-query'">
              <div class="db-subtabs db-subtabs-actions">
                <span class="db-subtabs-label">{{ doc.dbName || t('db.newQuery') }}</span>
                <div class="db-subtabs-right">
                  <button
                    v-if="doc.dbName"
                    class="btn btn-ghost btn-sm"
                    @click="onOpenDatabase(doc.dbName, 'objects')"
                  >
                    {{ t('db.tableList') }}
                  </button>
                  <button
                    v-if="doc.dbName"
                    class="btn btn-ghost btn-sm"
                    @click="treeRef?.refreshDb(doc.dbName)"
                  >
                    {{ t('db.refreshTables') }}
                  </button>
                </div>
              </div>
              <div class="db-right-top-content">
                <DBQueryEditor
                  :session-id="sessionId"
                  :db-name="doc.dbName"
                  :db-type="dbType"
                  :auto-run="false"
                />
              </div>
            </template>

            <!-- Database objects -->
            <template v-else-if="doc.kind === 'db-objects'">
              <div class="db-subtabs db-subtabs-actions">
                <span class="db-subtabs-label">{{ doc.dbName }} · {{ t('db.tableList') }}</span>
                <div class="db-subtabs-right">
                  <button class="btn btn-ghost btn-sm" @click="onOpenDatabase(doc.dbName, 'query')">
                    {{ t('db.dataQuery') }}
                  </button>
                </div>
              </div>
              <div class="db-right-top-content">
                <DBObjectList
                  :session-id="sessionId"
                  :db-name="doc.dbName"
                  @open="onSelectTable"
                  @changed="onObjectsChanged"
                  @object-removed="onObjectRemoved"
                />
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { Table2, Eye, Code2, Database, MoreHorizontal } from '@lucide/vue'
import { useI18n } from '../i18n'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import DBTreePanel from './DBTreePanel.vue'
import DBTableStructure from './DBTableStructure.vue'
import DBQueryEditor from './DBQueryEditor.vue'
import DBObjectList from './DBObjectList.vue'
import { GetTableSchema } from '../../bindings/easyaiot/terminal/app'
import type { ColumnInfo } from '../types/database'

defineOptions({ name: 'DBTabContent' })

const { t } = useI18n()

const props = defineProps<{
  sessionId: string
  hostName?: string
  defaultDbName?: string
  dbType?: string
}>()

type DocKind = 'table' | 'db-query' | 'db-objects'

interface DocTab {
  id: string
  kind: DocKind
  dbName: string
  tableName: string
  isView: boolean
  subTab: 'data' | 'structure'
  primaryKeys: string[]
  tableColumns: ColumnInfo[]
  structureLoadTrigger: number
}

const docs = ref<DocTab[]>([])
const activeDocId = ref('')
const treeRef = ref<InstanceType<typeof DBTreePanel> | null>(null)
let docSeq = 0

const activeDoc = computed(() => docs.value.find(d => d.id === activeDocId.value) || null)
const activeDb = computed(() => activeDoc.value?.dbName || '')
const activeTable = computed(() => (activeDoc.value?.kind === 'table' ? activeDoc.value.tableName : '') || '')

const leftWidth = ref(220)
let resizeStartX = 0
let resizeStartWidth = 0

function nextId(prefix: string) {
  docSeq += 1
  return `${prefix}-${docSeq}`
}

function docTitle(doc: DocTab): string {
  if (doc.kind === 'table') return doc.tableName
  if (doc.kind === 'db-objects') return `${doc.dbName} · ${t('db.tableList')}`
  if (doc.dbName) return `${doc.dbName} · ${t('db.dataQuery')}`
  return t('db.newQuery')
}

function activateDoc(id: string) {
  activeDocId.value = id
}

function closeDoc(id: string) {
  const idx = docs.value.findIndex(d => d.id === id)
  if (idx < 0) return
  docs.value.splice(idx, 1)
  if (activeDocId.value === id) {
    const next = docs.value[Math.min(idx, docs.value.length - 1)]
    activeDocId.value = next?.id || ''
  }
}

const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const ctxMenuVisible = ref(false)

function ctxIndexFor(id: string) {
  return docs.value.findIndex(d => d.id === id)
}
function canCloseOthersOf() {
  return docs.value.length > 1
}
function canCloseLeftOf(id: string) {
  return ctxIndexFor(id) > 0
}
function canCloseRightOf(id: string) {
  const idx = ctxIndexFor(id)
  return idx >= 0 && idx < docs.value.length - 1
}

function onDocTabContextMenu(e: MouseEvent, id: string) {
  e.stopPropagation()
  const doc = docs.value.find(d => d.id === id)
  if (doc?.kind === 'table') {
    doc.subTab = 'data'
  }
  activateDoc(id)
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, id)
}

function onCtxClose(id: string) {
  closeDoc(id)
  ctxMenuVisible.value = false
}

function onCtxCloseOthers(id: string) {
  if (docs.value.length > 1) {
    docs.value = docs.value.filter(d => d.id === id)
    activeDocId.value = id
  }
  ctxMenuVisible.value = false
}

function onCtxCloseLeft(id: string) {
  const idx = ctxIndexFor(id)
  if (idx > 0) {
    const keepId = activeDocId.value
    docs.value = docs.value.filter((_, i) => i >= idx)
    if (!docs.value.find(d => d.id === keepId)) {
      activeDocId.value = docs.value[0]?.id || ''
    }
  }
  ctxMenuVisible.value = false
}

function onCtxCloseRight(id: string) {
  const idx = ctxIndexFor(id)
  if (idx >= 0 && idx < docs.value.length - 1) {
    const keepId = activeDocId.value
    docs.value = docs.value.filter((_, i) => i <= idx)
    if (!docs.value.find(d => d.id === keepId)) {
      activeDocId.value = docs.value[docs.value.length - 1]?.id || ''
    }
  }
  ctxMenuVisible.value = false
}

function onCtxCloseAll() {
  docs.value = []
  activeDocId.value = ''
  ctxMenuVisible.value = false
}

// ── Tab drag reorder (mirrors TabsList's insert-indicator pattern) ──

const dragId = ref('')
const dragOverIndex = ref(-1)
const dragInsertAfter = ref(false)

function onDocDragStart(e: DragEvent, id: string) {
  dragId.value = id
  e.dataTransfer?.setData('application/db-tab-id', id)
  e.dataTransfer!.effectAllowed = 'move'
}

function onDocDragOver(e: DragEvent, index: number) {
  if (!e.dataTransfer?.types.includes('application/db-tab-id')) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  dragOverIndex.value = index
  dragInsertAfter.value = e.clientX >= rect.left + rect.width / 2
  e.dataTransfer.dropEffect = 'move'
}

function onDocDrop(_e: DragEvent, index: number) {
  const from = docs.value.findIndex(d => d.id === dragId.value)
  const insertAfter = dragInsertAfter.value
  clearDragState()
  if (from < 0) return
  // Drop on the left half of a tab means "insert before it", i.e. target index.
  let to = insertAfter ? index + 1 : index
  // Moving right compacts the source slot out of the range first.
  if (from < to) to -= 1
  if (to === from) return
  const [moved] = docs.value.splice(from, 1)
  docs.value.splice(to, 0, moved)
}

function clearDragState() {
  dragId.value = ''
  dragOverIndex.value = -1
  dragInsertAfter.value = false
}

// ── Tab bar overflow: wheel scroll + "more" dropdown ──

const docTabsScrollRef = ref<HTMLElement | null>(null)
const docTabsShowMore = ref(false)
const docMoreMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const docMoreMenuVisible = ref(false)

function updateDocTabsOverflow() {
  const el = docTabsScrollRef.value
  if (!el) return
  docTabsShowMore.value = el.scrollWidth > el.clientWidth + 1
}

watch(() => docs.value.length, () => nextTick(updateDocTabsOverflow))
watch(activeDocId, () => nextTick(updateDocTabsOverflow))

let docTabsResize: ResizeObserver | null = null

onMounted(() => {
  docTabsResize = new ResizeObserver(updateDocTabsOverflow)
  if (docTabsScrollRef.value) docTabsResize.observe(docTabsScrollRef.value)
  nextTick(updateDocTabsOverflow)
})

onBeforeUnmount(() => {
  docTabsResize?.disconnect()
  docTabsResize = null
})

function onTabsWheel(e: WheelEvent) {
  if (docTabsScrollRef.value) docTabsScrollRef.value.scrollLeft += e.deltaY
}

function onDocMoreSelect(id: string) {
  docMoreMenuVisible.value = false
  activateDoc(id)
  scrollToDoc(id)
}

function scrollToDoc(id: string) {
  if (!docTabsScrollRef.value) return
  const el = docTabsScrollRef.value.querySelector(`[data-doc-id="${id}"]`) as HTMLElement | null
  el?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

function findTableDoc(dbName: string, tableName: string) {
  return docs.value.find(d => d.kind === 'table' && d.dbName === dbName && d.tableName === tableName)
}

function findDbDoc(kind: 'db-query' | 'db-objects', dbName: string) {
  return docs.value.find(d => d.kind === kind && d.dbName === dbName)
}

async function loadSchema(doc: DocTab) {
  try {
    const schema = await GetTableSchema(props.sessionId, doc.dbName, doc.tableName)
    doc.tableColumns = schema.columns
    doc.primaryKeys = schema.columns.filter(c => c.isPrimary).map(c => c.name)
  } catch { /* ignore */ }
}

async function onSelectTable(dbName: string, tableName: string, isView = false) {
  const existing = findTableDoc(dbName, tableName)
  if (existing) {
    existing.subTab = 'data'
    if (!existing.primaryKeys.length) await loadSchema(existing)
    activateDoc(existing.id)
    return
  }
  const doc: DocTab = {
    id: nextId('table'),
    kind: 'table',
    dbName,
    tableName,
    isView,
    subTab: 'data',
    primaryKeys: [],
    tableColumns: [],
    structureLoadTrigger: 0,
  }
  // Load schema first so the result grid opens with canEdit already true
  await loadSchema(doc)
  docs.value.push(doc)
  activateDoc(doc.id)
}

async function onViewStructure(dbName: string, tableName: string) {
  const existing = findTableDoc(dbName, tableName)
  if (existing) {
    existing.isView = false
    openStructureSub(existing)
    activateDoc(existing.id)
    return
  }
  const doc: DocTab = {
    id: nextId('table'),
    kind: 'table',
    dbName,
    tableName,
    isView: false,
    subTab: 'structure',
    primaryKeys: [],
    tableColumns: [],
    structureLoadTrigger: 1,
  }
  docs.value.push(doc)
  activateDoc(doc.id)
  await loadSchema(doc)
}

function openStructureSub(doc: DocTab) {
  doc.subTab = 'structure'
  doc.structureLoadTrigger += 1
}

function onOpenDatabase(dbName: string, tab: 'query' | 'objects' = 'objects') {
  // Prefer objects list when opening a database; only open query when explicitly requested.
  const kind: DocKind = tab === 'query' ? 'db-query' : 'db-objects'
  const existing = findDbDoc(kind, dbName)
  if (existing) {
    activateDoc(existing.id)
    return
  }
  // If opening objects while a query tab for same db is active, still create objects (do not reuse query).
  const doc: DocTab = {
    id: nextId(kind),
    kind,
    dbName,
    tableName: '',
    isView: false,
    subTab: 'data',
    primaryKeys: [],
    tableColumns: [],
    structureLoadTrigger: 0,
  }
  docs.value.push(doc)
  activateDoc(doc.id)
}

function onNewQuery(dbName?: string) {
  const db = dbName || activeDb.value || props.defaultDbName || ''
  const doc: DocTab = {
    id: nextId('query'),
    kind: 'db-query',
    dbName: db,
    tableName: '',
    isView: false,
    subTab: 'data',
    primaryKeys: [],
    tableColumns: [],
    structureLoadTrigger: 0,
  }
  docs.value.push(doc)
  activateDoc(doc.id)
}

function onSchemaLoaded(doc: DocTab, pks: string[]) {
  doc.primaryKeys = pks
}

function onObjectsChanged(dbName: string) {
  treeRef.value?.refreshDb(dbName)
}

function onObjectRemoved(payload: { dbName: string; tableName?: string; kind: 'table' | 'view' | 'database' }) {
  treeRef.value?.refreshDb(payload.dbName)
  if (payload.kind === 'database') {
    docs.value = docs.value.filter(d => d.dbName !== payload.dbName)
    if (!docs.value.find(d => d.id === activeDocId.value)) {
      activeDocId.value = docs.value[0]?.id || ''
    }
    return
  }
  if (payload.tableName) {
    const toClose = docs.value.filter(
      d => d.kind === 'table' && d.dbName === payload.dbName && d.tableName === payload.tableName
    )
    for (const d of toClose) closeDoc(d.id)
  }
}

function onResizeStart(e: MouseEvent) {
  resizeStartX = e.clientX
  resizeStartWidth = leftWidth.value
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function onResizeMove(e: MouseEvent) {
  const dx = e.clientX - resizeStartX
  leftWidth.value = Math.max(150, Math.min(500, resizeStartWidth + dx))
}

function onResizeEnd() {
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}
</script>

<style scoped>
.db-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.db-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.db-left {
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle);
  overflow: hidden;
}
.db-resizer {
  width: 0.25rem;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.db-resizer:hover {
  background: var(--border-subtle);
}
.db-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.doc-tabs {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  flex-shrink: 0;
  min-height: 2rem;
}
.doc-tabs-scroll {
  display: flex;
  flex: 1;
  overflow-x: auto;
  min-width: 0;
}
.doc-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  max-width: 11.25rem;
  padding: 0.375rem 0.5rem 0.375rem 0.75rem;
  border: none;
  border-right: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  flex-shrink: 0;
}
.doc-tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.doc-tab.active {
  background: var(--bg-base);
  color: var(--text-primary);
  box-shadow: inset 0 -0.125rem 0 var(--accent);
}
.doc-tab-icon {
  flex-shrink: 0;
  opacity: 0.8;
}
.doc-tab-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-tab-close {
  width: 1rem;
  height: 1rem;
  line-height: 0.875rem;
  border-radius: 0.1875rem;
  font-size: 0.875rem;
  color: var(--text-muted);
  flex-shrink: 0;
}
.doc-tab-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.doc-tab-indicator {
  width: 0.125rem;
  min-width: 0.125rem;
  align-self: stretch;
  background: var(--accent);
  opacity: 0.8;
  margin: 0.25rem 0;
  border-radius: 1px;
  flex-shrink: 0;
}
.doc-tab-more {
  width: 1.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-left: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
}
.doc-tab-more:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.doc-tab-new {
  width: 2rem;
  border: none;
  border-left: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1rem;
  flex-shrink: 0;
}
.doc-tab-new:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.doc-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}
.db-subtabs {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 0.5rem;
  flex-shrink: 0;
  min-height: 2rem;
}
.db-subtabs-actions {
  justify-content: space-between;
}
.db-subtabs-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 0 0.5rem;
}
.db-subtabs-right {
  display: flex;
  gap: 0.25rem;
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
.db-right-top-content {
  flex: 1;
  overflow: hidden;
  min-height: 0;
  min-width: 0;
  width: 100%;
}
.db-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: 0.875rem;
}
</style>
