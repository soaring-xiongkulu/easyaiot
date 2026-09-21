<template>
  <div class="db-tree-panel">

    <div class="search-wrap">
      <input
        v-model="searchQuery"
        class="search-input"
        :placeholder="t('db.searchTables')"
      />
      <button class="btn btn-ghost btn-icon btn-sm" :title="t('db.refreshDatabases')" @click="refreshAll">
        <RefreshCw :size="'0.875rem'" />
      </button>
      <button class="btn btn-ghost btn-icon btn-sm" :title="t('common.more')" @click.stop="moreMenuRef?.toggle($event.currentTarget)">
        <MoreHorizontal :size="'0.875rem'" />
      </button>
      <Menu ref="moreMenuRef" v-model:visible="moreMenuVisible" align="end">
        <MenuItem :class="{ disabled: !canCreateDatabase }" @click="onMoreNewDatabase">{{ t('db.newDatabase') }}</MenuItem>
        <MenuItem @click="onMoreNewTable">{{ t('db.newTable') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onMoreRefresh">{{ t('db.refreshDatabases') }}</MenuItem>
      </Menu>
    </div>
    <div ref="treeContentRef" class="tree-content" @contextmenu.prevent="onTreeContextMenu">
      <div v-if="loading || runningSqlFile" class="tree-loading">{{ t('db.loading') }}</div>
      <template v-for="db in filteredDbs" :key="db.name">
        <div
          class="db-header"
          :data-db-row="db.name"
          :class="{ selected: selectedDb === db.name && !selectedTable }"
          @click="onDbClick(db.name)"
          @dblclick="onDbActivate(db.name)"
          @contextmenu.prevent="onDbContextMenu($event, db.name)"
        >
          <span class="db-arrow" @click.stop="onToggleDb(db.name)">
            <component :is="expandedDbs.has(db.name) ? ChevronDown : ChevronRight" :size="'0.75rem'" />
          </span>
          <Database class="db-icon" :size="'0.875rem'" />
          <span class="db-name">{{ db.name }}</span>
        </div>
        <template v-if="expandedDbs.has(db.name)">
          <div
            v-for="t in db.tables"
            :key="t.name"
            class="table-item"
            :data-table-row="db.name + '/' + t.name"
            :class="{ selected: selectedTable === t.name && selectedDb === db.name }"
            @click="onTableClick(db.name, t.name)"
            @dblclick="onTableDblClick(db.name, t)"
            @contextmenu.prevent="onTableContextMenu($event, db.name, t)"
          >
            <span class="table-icon-spacer" />
            <component :is="t.type === 'view' ? Eye : Table2" class="table-icon" :size="'0.875rem'" />
            <span class="table-name">{{ t.name }}</span>
          </div>
          <div v-if="db.tables.length === 0" class="empty-hint">
            {{ t('db.noTables') }}
          </div>
        </template>
      </template>
    </div>

    <Menu
      ref="ctxMenuRef"
      v-model:visible="ctxMenuVisible"
      v-slot="{ current }"
    >
      <template v-if="current && current.type === 'db'">
        <MenuItem @click="onCtxListDatabase">{{ t('db.tableList') }}</MenuItem>
        <MenuItem @click="onCtxNewQuery">{{ t('db.newQuery') }}</MenuItem>
        <MenuItem @click="onCtxRunSqlFile">{{ t('db.runSqlFile') }}</MenuItem>
        <MenuDivider />
        <MenuItem v-if="canCreateDatabase" @click="onCtxNewDatabase">{{ t('db.newDatabase') }}</MenuItem>
        <MenuItem @click="onCtxNewTable">{{ t('db.newTable') }}</MenuItem>
        <MenuItem class="danger" @click="onCtxDropDatabase">{{ t('db.dropDatabase') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxRefresh">{{ t('db.refreshTables') }}</MenuItem>
      </template>
      <template v-else-if="current && current.type === 'table'">
        <MenuItem @click="onCtxViewData">{{ t('db.openData') }}</MenuItem>
        <MenuItem v-if="current.tableType !== 'view'" @click="onCtxViewStructure">{{ t('db.tableStructure') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxCopyName">{{ t('db.copyName') }}</MenuItem>
        <MenuItem v-if="(current as DbMenuCtx).tableType !== 'view'" @click="onCtxCopyTable">{{ t('db.copyTable') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onCtxExportStructure">{{ t('db.exportStructure') }}</MenuItem>
        <MenuItem v-if="current.tableType !== 'view'" @click="onCtxExportData">{{ t('db.exportData') }}</MenuItem>
        <MenuItem v-if="current.tableType !== 'view'" @click="onCtxExportStructureData">{{ t('db.exportStructureData') }}</MenuItem>
        <MenuDivider />
        <template v-if="current.tableType === 'view'">
          <MenuItem class="danger" @click="onCtxDropView">{{ t('db.dropView') }}</MenuItem>
        </template>
        <template v-else>
          <MenuItem class="danger" @click="onCtxTruncateTable">{{ t('db.truncateTable') }}</MenuItem>
          <MenuItem class="danger" @click="onCtxDropTable">{{ t('db.dropTable') }}</MenuItem>
        </template>
      </template>
      <template v-else-if="current && current.type === 'blank'">
        <MenuItem @click="onCtxNewQueryBlank">{{ t('db.newQuery') }}</MenuItem>
        <MenuItem v-if="canCreateDatabase" @click="onCtxNewDatabase">{{ t('db.newDatabase') }}</MenuItem>
        <MenuItem @click="onCtxRefreshDatabases">{{ t('db.refreshDatabases') }}</MenuItem>
      </template>
    </Menu>

    <!-- Confirm dialog -->
    <el-dialog append-to-body
      v-model="confirmVisible"
      :title="confirmTitle"
      width="26.25rem"
    >
      <div class="confirm-body">
        <p class="confirm-text">{{ confirmText }}</p>
        <p class="confirm-hint">{{ t('db.typeToConfirm', { name: confirmName }) }}</p>
        <el-input v-model="confirmInput" :placeholder="confirmName" />
      </div>
      <template #footer>
        <el-button @click="confirmVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" :disabled="confirmInput !== confirmName" @click="onConfirm">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- New Database dialog -->
    <el-dialog append-to-body v-model="newDbVisible" :title="t('db.newDatabase')" width="23.75rem">
      <el-form label-width="5rem">
        <el-form-item :label="t('db.dbName')">
          <el-input v-model="newDbName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newDbVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newDbName.trim()" @click="onCreateDatabase">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- New Table dialog -->
    <el-dialog append-to-body v-model="newTableVisible" :title="t('db.newTable')" width="23.75rem">
      <el-form label-width="5rem">
        <el-form-item :label="t('db.tableName')">
          <el-input v-model="newTableName" />
        </el-form-item>
        <el-form-item :label="t('db.databases')">
          <el-select v-model="newTableDb" style="width:100%">
            <el-option v-for="d in databases" :key="d.name" :label="d.name" :value="d.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newTableVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newTableName.trim() || !newTableDb" @click="onCreateTable">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Copy Table dialog -->
    <el-dialog append-to-body v-model="copyTableVisible" :title="t('db.copyTable')" width="23.75rem">
      <el-form label-width="5rem">
        <el-form-item :label="t('db.sourceTable')">
          <el-input :model-value="copySourceTable" disabled />
        </el-form-item>
        <el-form-item :label="t('db.tableName')">
          <el-input v-model="copyTableName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="copyTableVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!copyTableName.trim()" @click="onCopyTable">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick, h } from 'vue'
import { Database, Table2, Eye, ChevronRight, ChevronDown, RefreshCw, MoreHorizontal } from '@lucide/vue'
import { useI18n } from '../i18n'
import { ElMessageBox } from 'element-plus'
import { GetDatabases, GetTables, CreateDatabase, DropDatabase, CreateTable, DropTable, DropView, TruncateTable, CopyTable, GetDBCapabilities, DumpTable, SaveFileDialogFiltered, WriteFileBase64, OpenFileDialogFiltered, ReadFileBase64, ExecuteSQLScript } from '../../bindings/easyaiot/terminal/app'
import { msg } from '../services/message'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import type { TableInfo } from '../types/database'

const { t } = useI18n()

interface DbEntry {
  name: string
  tables: TableInfo[]
  loaded: boolean
}

const props = defineProps<{
  sessionId: string
  defaultDbName?: string
  activeDb?: string
  activeTable?: string
}>()

const caps = ref<Record<string, any> | null>(null)
const canCreateDatabase = computed(() => caps.value?.['supportsCreateDatabase'] ?? true)

async function loadCapabilities() {
  try {
    caps.value = await GetDBCapabilities(props.sessionId)
  } catch (e) {
    console.error('Failed to load capabilities:', e)
  }
}

watch(() => props.sessionId, () => {
  if (props.sessionId) loadCapabilities()
}, { immediate: true })

const emit = defineEmits<{
  selectTable: [dbName: string, tableName: string, isView?: boolean]
  openDatabase: [dbName: string, tab?: 'query' | 'objects']
  viewStructure: [dbName: string, tableName: string]
  newQuery: [dbName?: string]
  objectRemoved: [payload: { dbName: string; tableName?: string; kind: 'table' | 'view' | 'database' }]
}>()

const databases = ref<DbEntry[]>([])
const expandedDbs = ref(new Set<string>())
const selectedDb = ref('')
const selectedTable = ref('')
const searchQuery = ref('')
const loading = ref(false)
const treeContentRef = ref<HTMLElement | null>(null)

async function loadTree() {
  if (!props.sessionId) return
  loading.value = true
  try {
    const dbs = await GetDatabases(props.sessionId)
    // Auto-expand the connection's default db only when it's actually a real
    // entry in the list. For databases where the configured "dbName" is not a
    // browsable namespace (e.g. Oracle's service name), it won't match and we
    // just list the available schemas collapsed.
    let autoOpen = ''
    if (props.defaultDbName && dbs.includes(props.defaultDbName)) {
      const tables = await GetTables(props.sessionId, props.defaultDbName)
      databases.value = [{ name: props.defaultDbName, tables, loaded: true }]
      expandedDbs.value = new Set([props.defaultDbName])
      autoOpen = props.defaultDbName
    } else if (dbs.length === 1) {
      // Single schema/db (e.g. Oracle showing only the current schema) — expand it.
      const only = dbs[0]
      const tables = await GetTables(props.sessionId, only)
      databases.value = [{ name: only, tables, loaded: true }]
      expandedDbs.value = new Set([only])
      autoOpen = only
    } else {
      databases.value = dbs.map((db: string) => ({ name: db, tables: [], loaded: false }))
      expandedDbs.value = new Set()
    }
    if (autoOpen) {
      selectedDb.value = autoOpen
      selectedTable.value = ''
      emit('openDatabase', autoOpen, 'objects')
    }
  } catch (e) {
    console.error('Failed to load tree:', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.sessionId, (newId) => {
  if (newId) loadTree()
}, { immediate: true })

// Sync tree highlight/position when the active db/table changes from outside
// (breadcrumb navigation, object list, etc.)
watch(() => [props.activeDb, props.activeTable], async ([db, table]) => {
  if (!db) return
  selectedDb.value = db
  selectedTable.value = table || ''
  if (table && !expandedDbs.value.has(db)) {
    expandedDbs.value.add(db)
    const entry = databases.value.find(d => d.name === db)
    if (entry && !entry.loaded) {
      try {
        entry.tables = await GetTables(props.sessionId, db)
        entry.loaded = true
      } catch { /* ignore */ }
    }
    expandedDbs.value = new Set(expandedDbs.value)
  }
  await nextTick()
  scrollActiveIntoView()
})

function scrollActiveIntoView() {
  const root = treeContentRef.value
  if (!root || !selectedDb.value) return
  const key = selectedTable.value ? `${selectedDb.value}/${selectedTable.value}` : selectedDb.value
  const attr = selectedTable.value ? 'data-table-row' : 'data-db-row'
  const esc = key.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
  const el = root.querySelector(`[${attr}="${esc}"]`) as HTMLElement | null
  el?.scrollIntoView({ block: 'nearest' })
}

async function ensureDbExpanded(dbName: string) {
  if (expandedDbs.value.has(dbName)) return
  expandedDbs.value.add(dbName)
  const db = databases.value.find(d => d.name === dbName)
  if (db && !db.loaded) {
    try {
      db.tables = await GetTables(props.sessionId, dbName)
      db.loaded = true
    } catch (e) {
      console.error('Failed to load tables:', e)
    }
  }
  expandedDbs.value = new Set(expandedDbs.value)
}

async function onDbActivate(dbName: string) {
  selectedDb.value = dbName
  selectedTable.value = ''
  await ensureDbExpanded(dbName)
  emit('openDatabase', dbName, 'objects')
}

async function onDbClick(dbName: string) {
  await onDbActivate(dbName)
}

async function onToggleDb(dbName: string) {
  if (expandedDbs.value.has(dbName)) {
    expandedDbs.value.delete(dbName)
    expandedDbs.value = new Set(expandedDbs.value)
    return
  }
  await ensureDbExpanded(dbName)
}

function onTableClick(dbName: string, tableName: string) {
  const table = databases.value.find(d => d.name === dbName)?.tables.find(t => t.name === tableName)
  selectedDb.value = dbName
  selectedTable.value = tableName
  emit('selectTable', dbName, tableName, table?.type === 'view')
}

function onTableDblClick(dbName: string, table: TableInfo) {
  selectedDb.value = dbName
  selectedTable.value = table.name
  emit('selectTable', dbName, table.name, table.type === 'view')
}

const filteredDbs = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return databases.value
  return databases.value.map(db => ({
    ...db,
    tables: db.tables.filter(t => t.name.toLowerCase().includes(q))
  }))
})

watch(searchQuery, (q) => {
  if (q.trim()) {
    const all = new Set(databases.value.map(d => d.name))
    for (const db of databases.value) {
      if (!db.loaded) {
        GetTables(props.sessionId, db.name).then(tables => {
          db.tables = tables
          db.loaded = true
        }).catch(() => {})
      }
    }
    expandedDbs.value = all
  }
})

// ── Context menu ──

interface DbMenuCtx {
  type: 'db' | 'table' | 'blank'
  dbName: string
  tableName: string
  tableType: string
}

const ctxMenuVisible = ref(false)
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const ctxDbName = ref('')
const ctxTableName = ref('')
const ctxTableType = ref('')

function openDbMenu(e: MouseEvent, item: DbMenuCtx) {
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, item)
}

function onDbContextMenu(e: MouseEvent, dbName: string) {
  ctxDbName.value = dbName
  ctxTableName.value = ''
  openDbMenu(e, { type: 'db', dbName, tableName: '', tableType: '' })
}

function onTableContextMenu(e: MouseEvent, dbName: string, table: TableInfo) {
  selectedDb.value = dbName
  selectedTable.value = table.name
  // 右键表节点时直接切换到该表数据页，同时弹出菜单
  emit('selectTable', dbName, table.name, table.type === 'view')
  ctxDbName.value = dbName
  ctxTableName.value = table.name
  ctxTableType.value = table.type || ''
  openDbMenu(e, { type: 'table', dbName, tableName: table.name, tableType: table.type || '' })
}

function onTreeContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('.db-header') || target.closest('.table-item')) return
  ctxDbName.value = ''
  ctxTableName.value = ''
  openDbMenu(e, { type: 'blank', dbName: '', tableName: '', tableType: '' })
}

function onCtxListDatabase() {
  emit('openDatabase', ctxDbName.value, 'objects')
  ctxMenuVisible.value = false
}

function onCtxNewQuery() {
  emit('newQuery', ctxDbName.value)
  ctxMenuVisible.value = false
}

function onCtxNewQueryBlank() {
  emit('newQuery')
  ctxMenuVisible.value = false
}

function onCtxViewData() {
  emit('selectTable', ctxDbName.value, ctxTableName.value, ctxTableType.value === 'view')
  ctxMenuVisible.value = false
}

function onCtxViewStructure() {
  emit('viewStructure', ctxDbName.value, ctxTableName.value)
  ctxMenuVisible.value = false
}

function onCtxCopyName() {
  navigator.clipboard.writeText(ctxTableName.value).catch(() => {})
  ctxMenuVisible.value = false
}

// ── Export table as .sql ──

async function exportTable(withStructure: boolean, withData: boolean) {
  ctxMenuVisible.value = false
  const dbName = ctxDbName.value
  const tableName = ctxTableName.value
  try {
    const sql = await DumpTable(props.sessionId, dbName, tableName, withStructure, withData)
    const path = await SaveFileDialogFiltered(t('db.exportSQL'), tableName + '.sql', 'SQL File', '*.sql')
    if (!path) return
    await WriteFileBase64(path, encodeBase64(sql))
    msg.success(t('db.exportDone', { name: tableName }))
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function onCtxExportStructure() {
  exportTable(true, false)
}

function onCtxExportData() {
  exportTable(false, true)
}

function onCtxExportStructureData() {
  exportTable(true, true)
}

// ── Run SQL file (database context menu) ──

// Wails v3 rejects the picker promise with "cancelled by user" when the
// dialog is dismissed, instead of resolving with an empty path.
function isDialogCancel(e: unknown): boolean {
  return String(e).toLowerCase().includes('cancel')
}

function decodeBase64(b64: string): string {
  try {
    const bin = atob(b64)
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
    return new TextDecoder('utf-8').decode(bytes)
  } catch {
    return ''
  }
}

const runningSqlFile = ref(false)

async function onCtxRunSqlFile() {
  ctxMenuVisible.value = false
  const dbName = ctxDbName.value
  let path = ''
  try {
    path = await OpenFileDialogFiltered(t('db.runSqlFile'), 'SQL File', '*.sql')
  } catch (e) {
    if (!isDialogCancel(e)) msg.error((e as any)?.message || String(e))
    return
  }
  if (!path) return
  try {
    runningSqlFile.value = true
    const b64 = await ReadFileBase64(path)
    const text = decodeBase64(b64)
    const result = await ExecuteSQLScript(props.sessionId, dbName, text)
    if (result?.failedLine) {
      showScriptFailure(result)
    } else {
      const name = path.split(/[\\/]/).pop() || path
      msg.success(t('db.scriptExecuted', { n: result?.executed ?? 0 }) + ` · ${t('db.affectedRows')}: ${result?.affectedTotal ?? 0} · ${name}`)
    }
  } catch (e: any) {
    msg.error(e?.message || String(e))
  } finally {
    runningSqlFile.value = false
  }
}

// Failure detail dialog: line number alone doesn't tell the user what went
// wrong (e.g. a duplicate-key INSERT on a rerun). Show the driver error and
// the failing statement, matching the query editor's script error panel.
function showScriptFailure(result: { failedLine: number; failedSql?: string; error?: string }) {
  const children = [h('p', { style: 'margin:0;font-weight:600' }, t('db.scriptFailedLine', { line: result.failedLine }))]
  if (result.error) {
    children.push(h('p', { style: 'margin:6px 0 0;color:var(--el-color-error);word-break:break-word;font-family:var(--font-mono,monospace);font-size:12px' }, result.error))
  }
  if (result.failedSql) {
    children.push(h('pre', { style: 'margin:8px 0 0;padding:8px;background:var(--bg-base,#f5f5f5);border-radius:4px;font-family:var(--font-mono,monospace);font-size:12px;white-space:pre-wrap;word-break:break-word;max-height:180px;overflow:auto' }, result.failedSql))
  }
  ElMessageBox.alert(h('div', { style: 'display:flex;flex-direction:column' }, children), t('db.runSqlFile'), {
    confirmButtonText: t('common.confirm'),
    type: 'error',
    customStyle: { maxWidth: '35rem', width: '35rem' },
  }).catch(() => {})
}

// ── Copy table ──

const copyTableVisible = ref(false)
const copySourceTable = ref('')
const copyTableName = ref('')

function onCtxCopyTable() {
  ctxMenuVisible.value = false
  copySourceTable.value = ctxTableName.value
  copyTableName.value = ctxTableName.value + '_copy'
  copyTableVisible.value = true
}

async function onCopyTable() {
  const dbName = ctxDbName.value
  const newName = copyTableName.value.trim()
  if (!copySourceTable.value || !newName) return
  try {
    await CopyTable(props.sessionId, dbName, copySourceTable.value, newName)
    copyTableVisible.value = false
    msg.success(t('db.copyTableDone', { name: newName }))
    await refreshDb(dbName)
  } catch (e: any) {
    console.error('Failed to copy table:', e)
    msg.error(e?.message || String(e))
  }
}

function encodeBase64(text: string): string {
  const bytes = new TextEncoder().encode(text)
  let bin = ''
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i])
  return btoa(bin)
}

// ── Confirm dialog ──

const confirmVisible = ref(false)
const confirmTitle = ref('')
const confirmText = ref('')
const confirmName = ref('')
const confirmInput = ref('')
let confirmAction: (() => Promise<void>) | null = null

function showConfirm(title: string, text: string, name: string, action: () => Promise<void>) {
  confirmTitle.value = title
  confirmText.value = text
  confirmName.value = name
  confirmInput.value = ''
  confirmAction = action
  confirmVisible.value = true
  ctxMenuVisible.value = false
}

async function onConfirm() {
  if (confirmAction) {
    try {
      await confirmAction()
      await loadTree()
    } catch (e: any) {
      console.error(e)
      msg.error(e?.message || String(e))
    }
  }
  confirmVisible.value = false
}

function onCtxDropDatabase() {
  const dbName = ctxDbName.value
  showConfirm(
    t('db.dropDatabase'),
    t('db.dropDatabaseConfirm', { name: dbName }),
    dbName,
    async () => {
      await DropDatabase(props.sessionId, dbName)
      emit('objectRemoved', { dbName, kind: 'database' })
    }
  )
}

function onCtxDropTable() {
  const dbName = ctxDbName.value
  const tableName = ctxTableName.value
  showConfirm(
    t('db.dropTable'),
    t('db.dropTableConfirm', { name: tableName }),
    tableName,
    async () => {
      await DropTable(props.sessionId, dbName, tableName)
      emit('objectRemoved', { dbName, tableName, kind: 'table' })
    }
  )
}

function onCtxDropView() {
  const dbName = ctxDbName.value
  const tableName = ctxTableName.value
  showConfirm(
    t('db.dropView'),
    t('db.dropViewConfirm', { name: tableName }),
    tableName,
    async () => {
      await DropView(props.sessionId, dbName, tableName)
      emit('objectRemoved', { dbName, tableName, kind: 'view' })
    }
  )
}

function onCtxTruncateTable() {
  showConfirm(
    t('db.truncateTable'),
    t('db.truncateTableConfirm', { name: ctxTableName.value }),
    ctxTableName.value,
    async () => { await TruncateTable(props.sessionId, ctxDbName.value, ctxTableName.value) }
  )
}

async function onCtxRefresh() {
  ctxMenuVisible.value = false
  const db = databases.value.find(d => d.name === ctxDbName.value)
  if (db) {
    try {
      db.tables = await GetTables(props.sessionId, ctxDbName.value)
      db.loaded = true
    } catch (e) {
      console.error('Failed to refresh:', e)
    }
  }
}

async function onCtxRefreshDatabases() {
  ctxMenuVisible.value = false
  await loadTree()
}

// Refresh a single database's tables (called from parent after external mutations)
async function refreshDb(dbName: string) {
  const db = databases.value.find(d => d.name === dbName)
  if (db) {
    try {
      db.tables = await GetTables(props.sessionId, dbName)
      db.loaded = true
    } catch (e) {
      console.error('Failed to refresh db:', e)
    }
  }
}

defineExpose({ refreshDb })

// ── Toolbar (search box) refresh + more menu ──

const moreMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const moreMenuVisible = ref(false)

function refreshAll() {
  loadTree()
}

function onMoreNewDatabase() {
  moreMenuVisible.value = false
  newDbName.value = ''
  newDbVisible.value = true
}

function onMoreNewTable() {
  moreMenuVisible.value = false
  newTableDb.value = selectedDb.value || databases.value[0]?.name || ''
  newTableName.value = ''
  newTableVisible.value = true
}

function onMoreRefresh() {
  moreMenuVisible.value = false
  loadTree()
}

// ── New Database / Table dialogs ──

const newDbVisible = ref(false)
const newDbName = ref('')

function onCtxNewDatabase() {
  ctxMenuVisible.value = false
  newDbName.value = ''
  newDbVisible.value = true
}

async function onCreateDatabase() {
  if (!newDbName.value.trim()) return
  try {
    await CreateDatabase(props.sessionId, newDbName.value.trim())
    newDbVisible.value = false
    await loadTree()
  } catch (e: any) {
    console.error('Failed to create database:', e)
    msg.error(e?.message || String(e))
  }
}

const newTableVisible = ref(false)
const newTableName = ref('')
const newTableDb = ref('')

function onCtxNewTable() {
  ctxMenuVisible.value = false
  newTableDb.value = ctxDbName.value
  newTableName.value = ''
  newTableVisible.value = true
}

async function onCreateTable() {
  if (!newTableName.value.trim() || !newTableDb.value) return
  try {
    await CreateTable(props.sessionId, newTableDb.value, newTableName.value.trim())
    newTableVisible.value = false
    const db = databases.value.find(d => d.name === newTableDb.value)
    if (db) {
      db.tables = await GetTables(props.sessionId, newTableDb.value)
      db.loaded = true
      expandedDbs.value = new Set([...expandedDbs.value, newTableDb.value])
    }
  } catch (e: any) {
    console.error('Failed to create table:', e)
    msg.error(e?.message || String(e))
  }
}
</script>

<style scoped>
.db-tree-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel-header {
  padding: 0.5rem 0.75rem 0.25rem;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  flex-shrink: 0;
}
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
  cursor: pointer;
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

/* Confirm dialog */
.confirm-body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.confirm-text {
  font-family: var(--font-ui);
  font-size: 0.875rem;
  color: var(--text-primary);
  margin: 0;
}
.confirm-hint {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}
</style>
