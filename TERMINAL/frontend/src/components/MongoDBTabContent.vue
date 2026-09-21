<template>
  <div class="mongodb-tab-content">
    <div class="mongo-main">
      <!-- Left tree panel -->
      <div class="mongo-left" :style="{ width: leftWidth + 'px' }">
        <div class="search-wrap">
          <input
            v-model="treeSearchQuery"
            class="search-input"
            :placeholder="t('db.searchTables')"
          />
          <button class="btn btn-ghost btn-icon btn-sm" :title="t('mongodb.refresh')" @click="refreshDatabases">
            <RefreshCw :size="'0.875rem'" />
          </button>
          <button class="btn btn-ghost btn-icon btn-sm" :title="t('common.more')" @click.stop="moreMenuRef?.toggle($event.currentTarget)">
            <MoreHorizontal :size="'0.875rem'" />
          </button>
          <Menu ref="moreMenuRef" v-model:visible="moreMenuVisible" align="end">
            <MenuItem @click="onMoreNewCollection">{{ t('mongodb.newCollection') }}</MenuItem>
            <MenuItem @click="onMoreNewDatabase">{{ t('db.newDatabase') }}</MenuItem>
            <MenuDivider />
            <MenuItem @click="onMoreRefresh">{{ t('mongodb.refresh') }}</MenuItem>
          </Menu>
        </div>
        <div class="tree-content" @contextmenu.prevent="onTreeContextMenu">
          <div v-if="treeLoading" class="tree-loading">{{ t('db.loading') }}</div>
          <template v-else>
            <div v-for="db in filteredDatabases" :key="db">
              <div
                class="db-header"
                :class="{ selected: activeTab?.kind === 'objects' && activeTab?.dbName === db }"
                @click="openObjectsTab(db)"
                @contextmenu.prevent="onDbContextMenu($event, db)"
              >
                <span class="db-arrow" @click.stop="toggleDb(db)">
                  <component :is="expandedDbs.has(db) ? ChevronDown : ChevronRight" :size="'0.75rem'" />
                </span>
                <Database :size="'0.875rem'" class="db-icon" />
                <span class="db-name">{{ db }}</span>
              </div>
              <div v-if="expandedDbs.has(db)" class="child-list">
                <div
                  v-for="col in (collections[db] || [])"
                  :key="col"
                  class="table-item"
                  :class="{ selected: activeTab?.kind === 'collection' && activeTab?.dbName === db && activeTab?.collectionName === col }"
                  @click="openCollectionTab(db, col)"
                  @contextmenu.prevent="onColContextMenu($event, db, col)"
                >
                  <span class="table-icon-spacer" />
                  <Layers :size="'0.875rem'" class="table-icon" />
                  <span class="table-name">{{ col }}</span>
                </div>
                <div v-if="!collections[db] || collections[db].length === 0" class="empty-hint">
                  {{ t('mongodb.noData') }}
                </div>
              </div>
            </div>
            <div v-if="filteredDatabases.length === 0 && !treeLoading" class="empty-hint">
              {{ t('mongodb.noData') }}
            </div>
          </template>
        </div>
      </div>

      <!-- Resizer -->
      <div class="mongo-resizer" @mousedown="onResizeStart" />

      <!-- Right content area -->
      <div class="mongo-right">
        <template v-if="tabs.length">
          <!-- Tab bar -->
          <div class="mongo-tab-bar">
            <div ref="tabScrollRef" class="mongo-tab-scroll" @wheel="onTabsWheel">
              <template v-for="(tab, index) in tabs" :key="tab.id">
                <div
                  v-if="tabDragOverIndex === index && tabDragInsertAfter"
                  class="mongo-tab-indicator"
                />
                <div
                  class="mongo-tab-item"
                  :class="{ active: tab.id === activeTabId }"
                  :data-tab-id="tab.id"
                  draggable="true"
                  @click="activateTab(tab.id)"
                  @middleclick.prevent="closeTab(tab.id)"
                  @contextmenu.prevent="onTabContextMenu($event, tab.id)"
                  @dragstart="onTabDragStart($event, tab.id)"
                  @dragover.prevent="onTabDragOver($event, index)"
                  @dragend="clearTabDragState"
                  @drop.prevent="onTabDrop($event, index)"
                >
                  <component :is="tab.kind === 'collection' ? Layers : Database" :size="'0.75rem'" class="tab-icon" />
                  <span class="tab-title">{{ tabTitle(tab) }}</span>
                  <button class="tab-close" :title="t('db.tabClose')" @click.stop="closeTab(tab.id)">×</button>
                </div>
              </template>
              <div v-if="tabDragOverIndex === tabs.length - 1 && tabDragInsertAfter" class="mongo-tab-indicator" />
            </div>
            <button
              v-if="tabShowMore"
              class="mongo-tab-more"
              :title="t('tab.more')"
              @click.stop="moreTabsMenuRef?.toggle($event.currentTarget)"
            >
              <MoreHorizontal :size="'0.875rem'" />
            </button>
            <Menu ref="moreTabsMenuRef" v-model:visible="moreTabsMenuVisible" align="end">
              <MenuItem
                v-for="tb in tabs"
                :key="tb.id"
                :class="{ active: tb.id === activeTabId }"
                @click="onTabMoreSelect(tb.id)"
              >{{ tabTitle(tb) }}</MenuItem>
            </Menu>
          </div>

          <!-- Panels (keep-alive via v-show) -->
          <div
            v-for="tab in tabs"
            :key="tab.id"
            v-show="tab.id === activeTabId"
            class="mongo-panel"
          >
            <MongoDBCollectionView
              v-if="tab.kind === 'collection'"
              :session-id="sessionId"
              :db-name="tab.dbName"
              :collection-name="tab.collectionName || ''"
            />

            <!-- Collection list (opened by clicking a database node) -->
            <div v-else-if="tab.kind === 'objects'" class="mongo-objects">
              <div class="mongo-objects-header">
                <span class="mongo-objects-title">{{ tab.dbName }} · {{ t('mongodb.collectionList') }}</span>
              </div>
              <div class="object-toolbar">
                <input
                  v-model="objectsSearch"
                  class="object-search"
                  :placeholder="t('db.searchTables')"
                />
                <button class="btn btn-default btn-sm" @click="onObjectsNewCollection(tab.dbName)">
                  <Plus :size="'0.875rem'" /> {{ t('mongodb.newCollection') }}
                </button>
              </div>
              <el-table
                :data="filteredObjects(tab.dbName)"
                border
                size="small"
                style="width:100%"
                class="db-result-table"
                :empty-text="t('db.noData')"
              >
                <el-table-column :label="t('mongodb.collection')" :min-width="uiPx(240)" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="object-name" @click="openCollectionTab(tab.dbName, row)">
                      <Layers :size="'0.875rem'" class="object-icon" />
                      {{ row }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column :label="t('common.actions')" :width="uiPx(80)" align="right">
                  <template #default="{ row }">
                    <button
                      class="btn btn-ghost btn-icon btn-sm danger"
                      :title="t('mongodb.dropCollection')"
                      @click.stop="onCtxDropCollection({ db: tab.dbName, col: row } as CtxMenuData)"
                    >
                      <Trash2 :size="'0.875rem'" />
                    </button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div v-else class="db-placeholder">
              <span>{{ t('mongodb.selectHint') }}</span>
            </div>
          </div>
        </template>
        <div v-else class="db-placeholder">
          <span>{{ t('mongodb.selectHint') }}</span>
        </div>
      </div>
    </div>

    <!-- Context menu -->
    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
      <template v-if="current?.type === 'blank'">
        <MenuItem @click="onCtxNewDatabase">{{ t('db.newDatabase') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxRefresh">{{ t('mongodb.refresh') }}</MenuItem>
      </template>
      <template v-else-if="current?.type === 'db'">
        <MenuItem @click="onCtxNewCollection(current as CtxMenuData)">{{ t('mongodb.newCollection') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxRefresh">{{ t('mongodb.refresh') }}</MenuItem>
        <MenuDivider />
        <MenuItem class="danger" @click="onCtxDropDatabase(current as CtxMenuData)">{{ t('mongodb.dropDatabase') }}</MenuItem>
      </template>
      <template v-else-if="current?.type === 'col'">
        <MenuItem @click="onCtxOpenColQuery(current as CtxMenuData)">{{ t('mongodb.openQuery') }}</MenuItem>
        <MenuItem @click="onCtxViewIndexes(current as CtxMenuData)">{{ t('mongodb.indexesTab') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxCopyName(current as CtxMenuData)">{{ t('mongodb.copyName') }}</MenuItem>
        <MenuDivider />
        <MenuItem class="danger" @click="onCtxDropCollection(current as CtxMenuData)">{{ t('mongodb.dropCollection') }}</MenuItem>
      </template>
    </Menu>

    <!-- Tab context menu -->
    <Menu ref="tabMenuRef" v-model:visible="tabMenuVisible" v-slot="{ current }">
      <template v-if="current">
        <MenuItem @click="onTabClose(current as number)">{{ t('tab.close') }}</MenuItem>
        <MenuItem :class="{ disabled: tabs.length <= 1 }" @click="onTabCloseOthers(current as number)">{{ t('tab.closeOther') }}</MenuItem>
        <MenuItem :class="{ disabled: tabIndexFor(current as number) <= 0 }" @click="onTabCloseLeft(current as number)">{{ t('tab.closeLeft') }}</MenuItem>
        <MenuItem :class="{ disabled: tabIndexFor(current as number) >= tabs.length - 1 }" @click="onTabCloseRight(current as number)">{{ t('tab.closeRight') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onTabCloseAll">{{ t('tab.closeAll') }}</MenuItem>
      </template>
    </Menu>

    <!-- New Collection dialog -->
    <el-dialog append-to-body
      v-model="newColDialogVisible"
      :title="t('mongodb.newCollection')"
      width="23.75rem"
    >
      <el-form label-width="5rem">
        <el-form-item :label="t('mongodb.collection')">
          <el-input v-model="newColName" :placeholder="t('mongodb.collection')" />
        </el-form-item>
        <el-form-item :label="t('db.databases')">
          <el-select v-model="ctxNewColDb" style="width:100%">
            <el-option v-for="db in databases" :key="db" :label="db" :value="db" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newColDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newColName.trim() || !ctxNewColDb" @click="createCollection">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- New Database dialog -->
    <el-dialog append-to-body v-model="newDbDialogVisible" :title="t('db.newDatabase')" width="23.75rem">
      <el-form label-width="5rem">
        <el-form-item :label="t('db.databases')">
          <el-input v-model="newDbName" :placeholder="t('db.databases')" />
        </el-form-item>
        <el-form-item :label="t('mongodb.collection')">
          <el-input v-model="newDbFirstCol" placeholder="optional" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newDbDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newDbName.trim()" @click="createDatabase">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { Database, Layers, ChevronRight, ChevronDown, RefreshCw, MoreHorizontal, Plus, Trash2 } from '@lucide/vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { uiPx } from '../utils/uiScale'
import {
  MongoListDatabases,
  MongoListCollections,
  MongoCreateCollection,
  MongoDropCollection,
  MongoDropDatabase,
} from '../../bindings/easyaiot/terminal/app'
import MongoDBCollectionView from './MongoDBCollectionView.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'

defineOptions({ name: 'MongoDBTabContent' })

const { t } = useI18n()

const props = defineProps<{
  sessionId: string
}>()

// ── Resize state ──
const leftWidth = ref(220)
let resizeStartX = 0
let resizeStartWidth = 0
let resizing = false

function onResizeStart(e: MouseEvent) {
  resizeStartX = e.clientX
  resizeStartWidth = leftWidth.value
  resizing = true
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}
function onResizeMove(e: MouseEvent) {
  const dx = e.clientX - resizeStartX
  leftWidth.value = Math.max(150, Math.min(500, resizeStartWidth + dx))
}
function onResizeEnd() {
  resizing = false
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

// ── Tree state ──
const databases = ref<string[]>([])
const collections = ref<Record<string, string[]>>({})
const expandedDbs = reactive(new Set<string>())
const treeLoading = ref(false)
const treeSearchQuery = ref('')

const filteredDatabases = computed(() => {
  const q = treeSearchQuery.value.trim().toLowerCase()
  if (!q) return databases.value
  return databases.value.filter(db => db.toLowerCase().includes(q))
})

// ── Tabs state ──
interface MongoTab {
  id: number
  kind: 'collection' | 'query' | 'objects'
  dbName: string
  collectionName?: string
}

const tabs = ref<MongoTab[]>([])
const activeTabId = ref<number | null>(null)
let nextTabId = 1

const activeTab = computed(() => tabs.value.find(t => t.id === activeTabId.value) || null)

function tabTitle(tab: MongoTab): string {
  if (tab.kind === 'collection') return tab.collectionName || ''
  if (tab.kind === 'objects') return `${tab.dbName} · ${t('mongodb.collectionList')}`
  return tab.dbName
}

function activateTab(id: number) {
  activeTabId.value = id
}

function openObjectsTab(dbName: string) {
  const existing = tabs.value.find(x => x.kind === 'objects' && x.dbName === dbName)
  if (existing) {
    activeTabId.value = existing.id
    return
  }
  const tab: MongoTab = { id: nextTabId++, kind: 'objects', dbName }
  tabs.value.push(tab)
  activeTabId.value = tab.id
  loadCollectionsFor(dbName)
}

function onObjectsNewCollection(dbName: string) {
  onCtxNewCollection({ db: dbName } as CtxMenuData)
}

function openCollectionTab(dbName: string, collectionName: string) {
  const existing = tabs.value.find(t => t.kind === 'collection' && t.dbName === dbName && t.collectionName === collectionName)
  if (existing) {
    activeTabId.value = existing.id
    return
  }
  const tab: MongoTab = { id: nextTabId++, kind: 'collection', dbName, collectionName }
  tabs.value.push(tab)
  activeTabId.value = tab.id
}

function closeTab(tabId: number) {
  const idx = tabs.value.findIndex(t => t.id === tabId)
  if (idx < 0) return
  tabs.value.splice(idx, 1)
  if (activeTabId.value === tabId) {
    if (!tabs.value.length) {
      activeTabId.value = null
    } else {
      const next = tabs.value[Math.min(idx, tabs.value.length - 1)]
      activeTabId.value = next.id
    }
  }
}

// ── Context menu state ──
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const ctxMenuVisible = ref(false)

// ── Toolbar (search box) refresh + more menu ──
const moreMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const moreMenuVisible = ref(false)

function onMoreNewDatabase() {
  moreMenuVisible.value = false
  onCtxNewDatabase()
}

function onMoreNewCollection() {
  moreMenuVisible.value = false
  onCtxNewCollection({ db: activeTab.value?.dbName || databases.value[0] || '' } as CtxMenuData)
}

function onMoreRefresh() {
  moreMenuVisible.value = false
  refreshDatabases()
}

// ── Tab context menu (mirrors DBTabContent) ──
const tabMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const tabMenuVisible = ref(false)

function tabIndexFor(id: number) {
  return tabs.value.findIndex(t => t.id === id)
}

function onTabContextMenu(e: MouseEvent, id: number) {
  e.stopPropagation()
  activateTab(id)
  tabMenuRef.value?.openAt(e.clientX, e.clientY, id)
}

function onTabClose(id: number) {
  closeTab(id)
  tabMenuVisible.value = false
}

function onTabCloseOthers(id: number) {
  if (tabs.value.length > 1) {
    tabs.value = tabs.value.filter(t => t.id === id)
    activeTabId.value = id
  }
  tabMenuVisible.value = false
}

function onTabCloseLeft(id: number) {
  const idx = tabIndexFor(id)
  if (idx > 0) {
    tabs.value = tabs.value.filter((_, i) => i >= idx)
  }
  tabMenuVisible.value = false
}

function onTabCloseRight(id: number) {
  const idx = tabIndexFor(id)
  if (idx >= 0 && idx < tabs.value.length - 1) {
    tabs.value = tabs.value.filter((_, i) => i <= idx)
  }
  tabMenuVisible.value = false
}

function onTabCloseAll() {
  tabs.value = []
  activeTabId.value = null
  tabMenuVisible.value = false
}

// ── Tab drag reorder (insert-indicator pattern, mirrors DBTabContent) ──

const tabDragId = ref(0)
const tabDragOverIndex = ref(-1)
const tabDragInsertAfter = ref(false)

function onTabDragStart(e: DragEvent, id: number) {
  tabDragId.value = id
  e.dataTransfer?.setData('application/mongo-tab-id', String(id))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onTabDragOver(e: DragEvent, index: number) {
  if (!e.dataTransfer?.types.includes('application/mongo-tab-id')) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  tabDragOverIndex.value = index
  tabDragInsertAfter.value = e.clientX >= rect.left + rect.width / 2
  e.dataTransfer.dropEffect = 'move'
}

function onTabDrop(_e: DragEvent, index: number) {
  const from = tabIndexFor(tabDragId.value)
  const insertAfter = tabDragInsertAfter.value
  clearTabDragState()
  if (from < 0) return
  let to = insertAfter ? index + 1 : index
  // Moving right compacts the source slot out of the range first.
  if (from < to) to -= 1
  if (to === from) return
  const [moved] = tabs.value.splice(from, 1)
  tabs.value.splice(to, 0, moved)
}

function clearTabDragState() {
  tabDragId.value = 0
  tabDragOverIndex.value = -1
  tabDragInsertAfter.value = false
}

// ── Tab bar overflow: wheel scroll + "more" dropdown ──

const tabScrollRef = ref<HTMLElement | null>(null)
const tabShowMore = ref(false)
const moreTabsMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const moreTabsMenuVisible = ref(false)

function updateTabOverflow() {
  const el = tabScrollRef.value
  if (!el) return
  tabShowMore.value = el.scrollWidth > el.clientWidth + 1
}

watch(() => tabs.value.length, () => nextTick(updateTabOverflow))
watch(activeTabId, () => nextTick(updateTabOverflow))

let tabBarResize: ResizeObserver | null = null

onMounted(() => {
  tabBarResize = new ResizeObserver(updateTabOverflow)
  if (tabScrollRef.value) tabBarResize.observe(tabScrollRef.value)
  nextTick(updateTabOverflow)
})

onUnmounted(() => {
  tabBarResize?.disconnect()
  tabBarResize = null
})

function onTabsWheel(e: WheelEvent) {
  if (tabScrollRef.value) tabScrollRef.value.scrollLeft += e.deltaY
}

function onTabMoreSelect(id: number) {
  moreTabsMenuVisible.value = false
  activateTab(id)
  scrollToTab(id)
}

function scrollToTab(id: number) {
  if (!tabScrollRef.value) return
  const el = tabScrollRef.value.querySelector(`[data-tab-id="${id}"]`) as HTMLElement | null
  el?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

interface CtxMenuData {
  type: 'db' | 'col' | 'blank'
  db: string
  col: string
}

// ── Dialog state ──
const newColDialogVisible = ref(false)
const newColName = ref('')
const ctxNewColDb = ref('')

const newDbDialogVisible = ref(false)
const newDbName = ref('')
const newDbFirstCol = ref('')

// ── Tree methods ──
async function loadCollectionsFor(db: string) {
  if (collections.value[db]) return
  try {
    const cols = await MongoListCollections(props.sessionId, db)
    collections.value[db] = cols.filter(c => !c.startsWith('system.'))
    collections.value = { ...collections.value }
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

// Expand every database by default (and lazily load its collections).
async function expandDefaultDbs(dbs: string[]) {
  for (const db of dbs) expandedDbs.add(db)
  await Promise.all(dbs.map(db => loadCollectionsFor(db)))
}

const objectsSearch = ref('')

function filteredObjects(dbName: string): string[] {
  const all = collections.value[dbName] || []
  const q = objectsSearch.value.trim().toLowerCase()
  if (!q) return all
  return all.filter(c => c.toLowerCase().includes(q))
}

async function refreshDatabases() {
  if (!props.sessionId) return
  treeLoading.value = true
  try {
    const allDbs = await MongoListDatabases(props.sessionId)
    databases.value = allDbs.filter(d => d !== 'config' && d !== 'local')
    await expandDefaultDbs(databases.value)
  } catch (e: any) {
    const err = e?.message || String(e)
    if (err.includes('not connected') || err.includes('session not found')) {
      await new Promise(r => setTimeout(r, 300))
      try {
        const allDbs = await MongoListDatabases(props.sessionId)
        databases.value = allDbs.filter(d => d !== 'config' && d !== 'local')
        await expandDefaultDbs(databases.value)
        treeLoading.value = false
        return
      } catch (_e2: any) {
        msg.error(_e2?.message || String(_e2))
      }
    } else {
      msg.error(err)
    }
  }
  treeLoading.value = false
}

async function toggleDb(db: string) {
  if (expandedDbs.has(db)) {
    expandedDbs.delete(db)
  } else {
    expandedDbs.add(db)
    await loadCollectionsFor(db)
  }
}

// ── Context menu handlers ──
function onTreeContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('.db-header') || target.closest('.table-item')) return
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, { type: 'blank', db: '', col: '' } as CtxMenuData)
}

function onDbContextMenu(e: MouseEvent, db: string) {
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, { type: 'db', db, col: '' } as CtxMenuData)
}

function onColContextMenu(e: MouseEvent, db: string, col: string) {
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, { type: 'col', db, col } as CtxMenuData)
}

function onCtxOpenColQuery(current: CtxMenuData) {
  openCollectionTab(current.db, current.col)
  ctxMenuVisible.value = false
}

function onCtxViewIndexes(current: CtxMenuData) {
  // Open the collection tab; switch to the indexes sub-tab inside it.
  openCollectionTab(current.db, current.col)
  ctxMenuVisible.value = false
}

function onCtxCopyName(current: CtxMenuData) {
  navigator.clipboard.writeText(current.col)
  ctxMenuVisible.value = false
}

function onCtxNewDatabase() {
  newDbName.value = ''
  newDbFirstCol.value = ''
  newDbDialogVisible.value = true
  ctxMenuVisible.value = false
}

async function createDatabase() {
  const dbName = newDbName.value.trim()
  if (!dbName) return
  const colName = newDbFirstCol.value.trim() || '_default'
  try {
    await MongoCreateCollection(props.sessionId, dbName, colName)
    msg.success(t('mongodb.collectionCreated'))
    newDbDialogVisible.value = false
    refreshDatabases()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function onCtxRefresh() {
  refreshDatabases()
  ctxMenuVisible.value = false
}

function onCtxNewCollection(current: CtxMenuData) {
  ctxNewColDb.value = current.db
  newColName.value = ''
  newColDialogVisible.value = true
}

async function createCollection() {
  const name = newColName.value.trim()
  if (!name || !ctxNewColDb.value) return
  try {
    await MongoCreateCollection(props.sessionId, ctxNewColDb.value, name)
    msg.success(t('mongodb.collectionCreated'))
    newColDialogVisible.value = false
    const cols = await MongoListCollections(props.sessionId, ctxNewColDb.value)
    collections.value[ctxNewColDb.value] = cols.filter(c => !c.startsWith('system.'))
    collections.value = { ...collections.value }
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function onCtxDropDatabase(current: CtxMenuData) {
  const db = current.db
  ElMessageBox.confirm(t('mongodb.dropDatabase') + ': ' + db, t('common.confirm'), { type: 'warning' })
    .then(async () => {
      try {
        await MongoDropDatabase(props.sessionId, db)
        msg.success(t('mongodb.databaseDropped'))
        databases.value = databases.value.filter(d => d !== db)
        // close any tabs belonging to this database
        const beforeLen = tabs.value.length
        tabs.value = tabs.value.filter(t => t.dbName !== db)
        if (tabs.value.length !== beforeLen && !tabs.value.find(t => t.id === activeTabId.value)) {
          activeTabId.value = tabs.value.length ? tabs.value[tabs.value.length - 1].id : null
        }
      } catch (e: any) {
        msg.error(e?.message || String(e))
      }
    })
    .catch(() => {})
  ctxMenuVisible.value = false
}

function onCtxDropCollection(current: CtxMenuData) {
  const db = current.db
  const col = current.col
  ElMessageBox.confirm(t('mongodb.dropCollection') + ': ' + col, t('common.confirm'), { type: 'warning' })
    .then(async () => {
      try {
        await MongoDropCollection(props.sessionId, db, col)
        msg.success(t('mongodb.collectionDropped'))
        if (collections.value[db]) {
          collections.value[db] = collections.value[db].filter(c => c !== col)
          collections.value = { ...collections.value }
        }
        // close the tab for this collection
        const closed = tabs.value.find(t => t.kind === 'collection' && t.dbName === db && t.collectionName === col)
        if (closed) closeTab(closed.id)
      } catch (e: any) {
        msg.error(e?.message || String(e))
      }
    })
    .catch(() => {})
  ctxMenuVisible.value = false
}

// ── Lifecycle ──
onMounted(() => {
  if (props.sessionId) {
    refreshDatabases()
  }
})

onUnmounted(() => {
  if (resizing) {
    document.removeEventListener('mousemove', onResizeMove)
    document.removeEventListener('mouseup', onResizeEnd)
  }
})

watch(() => props.sessionId, () => {
  if (props.sessionId) {
    tabs.value = []
    activeTabId.value = null
    databases.value = []
    collections.value = {}
    expandedDbs.clear()
    refreshDatabases()
  }
})
</script>

<style scoped>
/* ── Root ── */
.mongodb-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* ── Main layout ── */
.mongo-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.mongo-left {
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.mongo-resizer {
  width: 0.25rem;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.mongo-resizer:hover {
  background: var(--border-subtle);
}

.mongo-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── Search ── */
.search-wrap {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  flex-shrink: 0;
}
.search-input {
  flex: 1;
  min-width: 0;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  outline: none;
  transition: border-color 0.15s ease;
}
.search-input:focus {
  border-color: var(--accent);
}
.search-input::placeholder {
  color: var(--text-muted);
}

/* ── Tree ── */
.tree-content {
  flex: 1;
  overflow: auto;
}
.tree-loading {
  padding: 0.75rem;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  text-align: center;
}
.db-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.db-header:hover {
  background: var(--bg-hover);
}
.db-header.selected {
  background: var(--bg-hover);
}
.db-arrow {
  width: 0.75rem;
  flex-shrink: 0;
  color: var(--text-muted);
  display: flex;
  align-items: center;
}
.db-arrow:hover {
  color: var(--text-primary);
}
.db-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}
.db-name {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.table-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.table-item:hover {
  background: var(--bg-hover);
}
.table-item.selected {
  background: var(--bg-hover);
}
.table-icon-spacer {
  width: 1.875rem;
  flex-shrink: 0;
}
.table-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}
.table-name {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-hint {
  padding: 0.25rem 0.5rem 0.25rem 1.75rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ── Tab bar ── */
.mongo-tab-bar {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  flex-shrink: 0;
  min-height: 2rem;
}
.mongo-tab-scroll {
  display: flex;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  min-width: 0;
}
.mongo-tab-scroll::-webkit-scrollbar { height: 0.25rem; }
.mongo-tab-indicator {
  width: 0.125rem;
  min-width: 0.125rem;
  align-self: stretch;
  background: var(--accent);
  opacity: 0.8;
  margin: 0.25rem 0;
}
.mongo-tab-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  max-width: 11.25rem;
  padding: 0.375rem 0.5rem 0.375rem 0.75rem;
  border-right: 1px solid var(--border-subtle);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.12s ease;
}
.mongo-tab-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.mongo-tab-item.active {
  background: var(--bg-base);
  color: var(--text-primary);
  box-shadow: inset 0 -0.125rem 0 var(--accent);
}
.tab-icon { flex-shrink: 0; opacity: 0.8; }
.tab-title { overflow: hidden; text-overflow: ellipsis; }
.tab-close {
  width: 1rem;
  height: 1rem;
  line-height: 0.875rem;
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  border-radius: 0.1875rem;
  flex-shrink: 0;
}
.tab-close:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.mongo-tab-more {
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
.mongo-tab-more:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.mongo-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* ── Collection list panel ── */
.mongo-objects {
  flex: 1;
  overflow: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
}
.mongo-objects-header {
  margin-bottom: 0.5rem;
}
.mongo-objects-title {
  font-family: var(--font-ui);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}
.object-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.object-search {
  width: 15rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  outline: none;
}
.object-search:focus { border-color: var(--accent); }
.object-toolbar .btn:last-child { margin-left: auto; }
.object-name {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
  transition: color 0.15s ease;
}
.object-name:hover { color: var(--accent); }
.object-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}
/* 结果表格主题变量与 DBResultGrid 保持一致 */
.db-result-table {
  --el-table-header-bg-color: var(--bg-elevated, var(--bg-surface));
  --el-table-tr-bg-color: var(--bg-surface);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-subtle);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-text-color: var(--text-primary);
  --el-table-bg-color: var(--bg-surface);
  font-size: 0.75rem;
}

/* ── Placeholder ── */
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
