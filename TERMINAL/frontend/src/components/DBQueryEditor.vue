<template>
  <div ref="rootRef" class="db-query-editor">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-box">
        <div class="spinner" />
        <span class="loading-text">{{ t('db.loading') }}</span>
        <button class="btn btn-default" @click="onCancelQuery">{{ t('common.cancel') }}</button>
      </div>
    </div>
    <div class="editor-top" :style="{ height: topHeight + 'px' }">
      <div class="editor-toolbar">
        <button class="btn btn-default btn-sm" @click="historyOpen = !historyOpen">
          <History :size="'0.875rem'" />
          {{ t('db.queryHistory') }}
        </button>
        <button class="btn btn-ghost btn-icon btn-sm" :title="t('db.runSqlFile')" @click="onOpenScriptFile">
          <FolderOpen :size="'0.875rem'" />
        </button>
        <button class="btn btn-primary btn-sm" title="Ctrl+Enter" @click="onExecute">{{ t('db.execute') }}</button>
      </div>
      <div v-if="historyOpen" class="history-panel">
        <div v-if="history.length === 0" class="history-empty">{{ t('db.noHistory') }}</div>
        <button
          v-for="item in history"
          :key="item.id"
          class="history-item"
          @click="applyHistory(item)"
        >
          <span class="history-sql">{{ item.sql }}</span>
          <span class="history-meta">
            <span v-if="item.error" class="history-err">err</span>
            <span v-else>{{ item.rowCount ?? 0 }} {{ t('db.rows') }}</span>
            ? {{ item.durationMs }}ms
          </span>
        </button>
      </div>
      <div class="sql-editor-wrap">
        <SyntaxEditor
          ref="editorRef"
          v-model="sql"
          file-path="query.sql"
          compact
          @execute="onExecute"
        />
      </div>
    </div>
    <div class="editor-resizer" @mousedown="onResizeStart" />
    <div class="editor-bottom">
      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="scriptResult" class="script-result" :class="{ 'has-error': scriptResult.failedLine }">
        <template v-if="scriptResult.failedLine">
          <div class="script-error-head">{{ t('db.scriptFailedLine', { line: scriptResult.failedLine }) }}</div>
          <div class="script-error-detail">{{ scriptResult.error }}</div>
          <pre class="script-error-sql">{{ scriptResult.failedSql }}</pre>
        </template>
        <template v-else>
          <span class="script-ok">{{ t('db.scriptExecuted', { n: scriptResult.executed }) }}</span>
          <span class="script-affected">{{ t('db.affectedRowsTotal') }}: {{ scriptResult.affectedTotal }}</span>
        </template>
      </div>
      <div v-if="execResult" class="result-info">
        {{ t('db.affectedRows') }}: {{ execResult.affected }}
        <span v-if="lastDurationMs != null" class="result-duration"> · {{ lastDurationMs }}ms</span>
      </div>

      <div v-if="queryResult" class="result-toolbar">
        <input
          v-model="resultFilter"
          class="result-filter"
          :placeholder="t('db.filterResults')"
        />
        <div class="result-toolbar-right">
          <button
            v-if="tableName && !isView"
            class="btn btn-default btn-sm"
            @click="startInsertRow"
          ><Plus :size="'0.875rem'" /> {{ t('db.insertRow') }}</button>
          <button
            ref="exportBtnRef"
            class="btn btn-ghost btn-icon btn-sm"
            :title="t('db.exportResults')"
            @click.stop="exportMenuRef?.toggle($event.currentTarget)"
          >
            <Download :size="'0.875rem'" />
          </button>
          <Menu
            ref="exportMenuRef"
            v-model:visible="exportMenuVisible"
            align="end"
          >
            <MenuItem @click="onExportResults('csv')">CSV</MenuItem>
            <MenuItem @click="onExportResults('txt')">TXT</MenuItem>
            <MenuItem @click="onExportResults('json')">JSON</MenuItem>
          </Menu>
        </div>
      </div>

      <div v-if="queryResult" class="result-grid">
        <DBResultGrid
          ref="resultGridRef"
          :key="`grid-${canEditRows ? 1 : 0}-${queryResult.columns.map(c => c.name).join('|')}`"
          :rows="displayRows"
          :columns="queryResult.columns"
          :can-edit="canEditRows"
          :primary-keys="resolvedPrimaryKeys"
          :table-columns="tableColumns"
          :empty-text="t('db.noData')"
          :actions-label="t('db.actions')"
          :edit-label="t('common.edit')"
          :delete-label="t('common.delete')"
          @pending-change="onPendingChange"
          @edit-row="startEditRowByRow"
          @delete-row="onDeleteRowByRow"
          @sort-change="onSortChange"
        />
      </div>

      <div v-if="queryResult && canEditRows && pendingCount > 0" class="save-bar">
        <span class="save-hint">{{ pendingCount }} {{ t('db.unsavedChanges') }}</span>
        <button class="btn btn-default btn-sm" :disabled="savingRows" @click="onUndoEdits">{{ t('db.undo') }}</button>
        <button class="btn btn-primary btn-sm" :disabled="savingRows" @click="onSaveEdits">{{ t('common.save') }}</button>
      </div>

      <div v-if="queryResult" class="result-footer">
        <span class="result-count">
          {{ displayRows.length }}{{ resultFilter ? ` / ${queryResult.rows.length}` : '' }} {{ t('db.rows') }}
          <span v-if="lastDurationMs != null"> · {{ lastDurationMs }}ms</span>
        </span>
        <el-pagination
          v-if="browseMode"
          small
          background
          layout="sizes, prev, pager, next"
          :total="browsePageTotal"
          :page-size="pageSize"
          :current-page="page + 1"
          :page-sizes="[100, 200, 500]"
          @current-change="onPageChange"
          @size-change="onPageSizeChange"
        />
      </div>

      <el-dialog
        v-model="insertingRow"
        :title="t('db.insertRow')"
        width="40rem"
        append-to-body
        destroy-on-close
      >
        <div class="row-form">
          <div v-for="col in insertColumns" :key="col" class="row-form-row">
            <span class="field-name" :title="col">{{ col }}</span>
            <span class="field-type" :title="getColumnType(col)">{{ getColumnType(col) }}</span>
            <input v-model="insertValues[col]" class="field-input" :disabled="insertNulls[col] || insertAutoIncrement[col]" :placeholder="getColumnPlaceholder(col)" />
            <label v-if="isColumnAuto(col)" class="field-toggle"><input type="checkbox" v-model="insertAutoIncrement[col]" /> {{ t('db.autoIncrement') }}</label>
            <label v-else-if="!isColumnPrimary(col) && getColumnNullable(col)" class="field-toggle"><input type="checkbox" v-model="insertNulls[col]" /> NULL</label>
            <span v-else class="field-toggle"></span>
          </div>
        </div>
        <template #footer>
          <el-button @click="onInsertCancel">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="onInsertConfirm">{{ t('common.confirm') }}</el-button>
        </template>
      </el-dialog>

      <el-dialog
        v-model="editingRow"
        :title="t('common.edit')"
        width="40rem"
        append-to-body
        destroy-on-close
      >
        <div class="row-form">
          <div v-for="col in editRowColumns" :key="col" class="row-form-row">
            <span class="field-name" :title="col">{{ col }}</span>
            <span class="field-type" :title="getColumnType(col)">{{ getColumnType(col) }}</span>
            <input v-model="editRowValues[col]" class="field-input" :disabled="editNulls[col]" />
            <label v-if="!isColumnPrimary(col) && getColumnNullable(col)" class="field-toggle"><input type="checkbox" v-model="editNulls[col]" /> NULL</label>
            <span v-else class="field-toggle"></span>
          </div>
        </div>
        <template #footer>
          <el-button @click="onEditRowCancel">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="onEditRowConfirm">{{ t('common.save') }}</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed, watch, onMounted } from 'vue'
import { History, FolderOpen, Download, Plus } from '@lucide/vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import SyntaxEditor from './SyntaxEditor.vue'
import DBResultGrid from './DBResultGrid.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import { ExecuteQuery, ExecuteStatement, GetTableSchema, DBDefaultTableQuery, DBInsertRow, DBUpdateRow, DBDeleteRow, ExecuteSQLScript, OpenFileDialogFiltered, ReadFileBase64, SaveFileDialogFiltered, WriteFileBase64 } from '../../bindings/easyaiot/terminal/app'
import { msg } from '../services/message'
import { loadSqlHistory, pushSqlHistory } from '../composables/useDbSqlHistory'
import type { QueryResult, ExecResult, ColumnInfo, HistoryEntry } from '../types/database'
import { ScriptResult } from '../../bindings/easyaiot/terminal/backend/database/models'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  sessionId: string
  tableName?: string
  dbName?: string
  dbType?: string
  primaryKeys?: string[]
  tableColumns?: ColumnInfo[]
  isView?: boolean
  autoRun?: boolean
}>(), {
  autoRun: true,
})

const emit = defineEmits<{
  cellUpdated: []
}>()

const sql = ref('')
const queryResult = shallowRef<QueryResult | null>(null)
const execResult = ref<ExecResult | null>(null)
const error = ref('')
const loading = ref(false)
const lastDurationMs = ref<number | null>(null)
const editorRef = ref<InstanceType<typeof SyntaxEditor> | null>(null)
let cancelled = false

const page = ref(0)
const pageSize = ref(100)
const browseMode = ref(false)
const browseHasMore = ref(false)
const resultFilter = ref('')
const sortProp = ref('')
const sortOrder = ref<'ascending' | 'descending' | null>(null)

const historyOpen = ref(false)
const history = ref<HistoryEntry[]>([])

const resolvedPrimaryKeys = computed(() => {
  if (!props.tableName || props.isView || !props.primaryKeys?.length || !queryResult.value) return [] as string[]
  const colMap = new Map(queryResult.value.columns.map(c => [c.name.toLowerCase(), c.name]))
  const resolved: string[] = []
  for (const pk of props.primaryKeys) {
    const actual = colMap.get(pk.toLowerCase())
    if (!actual) return []
    resolved.push(actual)
  }
  return resolved
})

const canEditRows = computed(() => resolvedPrimaryKeys.value.length > 0)

const displayRows = computed(() => {
  let rows = queryResult.value?.rows || []
  const q = resultFilter.value.trim().toLowerCase()
  if (q) {
    rows = rows.filter(row =>
      Object.values(row).some(v => v != null && String(v).toLowerCase().includes(q))
    )
  }
  if (sortProp.value && sortOrder.value) {
    const prop = sortProp.value
    const dir = sortOrder.value === 'ascending' ? 1 : -1
    rows = [...rows].sort((a, b) => {
      const av = a[prop]
      const bv = b[prop]
      if (av == null && bv == null) return 0
      if (av == null) return -1 * dir
      if (bv == null) return 1 * dir
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv), undefined, { numeric: true }) * dir
    })
  }
  return rows
})

const browsePageTotal = computed(() => {
  const rows = queryResult.value?.rows.length ?? 0
  if (browseHasMore.value) return (page.value + 1) * pageSize.value + 1
  return page.value * pageSize.value + rows
})

// ── Export result rows as CSV / TXT / JSON ──

const exportMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const exportMenuVisible = ref(false)

function csvCell(v: unknown): string {
  if (v == null) return ''
  const s = String(v)
  return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s
}

function fmtCell(v: unknown): string {
  if (v == null) return 'NULL'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function buildExportText(format: 'csv' | 'txt' | 'json'): string {
  const cols = queryResult.value?.columns.map(c => c.name) || []
  const rows = displayRows.value
  if (format === 'json') {
    return JSON.stringify(rows.map(r => Object.fromEntries(cols.map(c => [c, r[c] ?? null]))), null, 2)
  }
  if (format === 'txt') {
    // Tab-separated with a header line; matches what spreadsheet tools paste back.
    return [cols.join('\t'), ...rows.map(r => cols.map(c => fmtCell(r[c])).join('\t'))].join('\n')
  }
  // BOM so Excel detects UTF-8; CRLF per RFC 4180.
  return '﻿' + [cols.map(csvCell).join(','), ...rows.map(r => cols.map(c => csvCell(r[c])).join(','))].join('\r\n')
}

async function onExportResults(format: 'csv' | 'txt' | 'json') {
  exportMenuVisible.value = false
  if (!queryResult.value?.rows.length) return
  try {
    const ext = format === 'json' ? 'json' : format === 'txt' ? 'txt' : 'csv'
    const label = format === 'json' ? 'JSON File' : format === 'txt' ? 'Text File' : 'CSV File'
    const defaultName = `${props.tableName || 'query_result'}_${new Date().toISOString().slice(0, 10)}.${ext}`
    const path = await SaveFileDialogFiltered(t('db.exportResults'), defaultName, label, `*.${ext}`)
    if (!path) return
    await WriteFileBase64(path, encodeBase64(buildExportText(format)))
    msg.success(t('db.exportDone', { name: path.split('/').pop() || defaultName }))
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function encodeBase64(text: string): string {
  const bytes = new TextEncoder().encode(text)
  let bin = ''
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i])
  return btoa(bin)
}

function refreshHistory() {
  history.value = loadSqlHistory(props.sessionId)
}

function applyHistory(item: HistoryEntry) {
  sql.value = item.sql
  browseMode.value = false
  historyOpen.value = false
}

function firstStatement(text: string): string {
  const trimmed = text.trim()
  if (!trimmed) return ''
  const parts = trimmed.split(';').map(s => s.trim()).filter(Boolean)
  return parts[0] || trimmed
}

function isQuerySql(text: string): boolean {
  const stmt = firstStatement(text)
  return /^\s*(WITH|SELECT|SHOW|DESCRIBE|DESC|EXPLAIN|PRAGMA)\b/i.test(stmt)
}

function hasMultipleStatements(text: string): boolean {
  return SplitScriptLike(text).length > 1
}

// Lightweight statement count: respects quotes and line comments so a `;`
// inside a literal doesn't count as a separator. Block comments/DELIMITER
// don't matter for the >1 check in practice.
function SplitScriptLike(text: string): string[] {
  const parts: string[] = []
  let cur = ''
  let inSingle = false
  let inDouble = false
  let inBacktick = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    const prev = i > 0 ? text[i - 1] : ''
    if (c === "'" && !inDouble && !inBacktick && prev !== '\\') inSingle = !inSingle
    else if (c === '"' && !inSingle && !inBacktick && prev !== '\\') inDouble = !inDouble
    else if (c === '`' && !inSingle && !inDouble) inBacktick = !inBacktick
    else if (c === ';' && !inSingle && !inDouble && !inBacktick) {
      if (cur.trim()) parts.push(cur)
      cur = ''
      continue
    }
    cur += c
  }
  if (cur.trim()) parts.push(cur)
  return parts
}

function normalizeSql(s: string): string {
  return s.replace(/\s+/g, ' ').trim()
}

async function loadBrowseSql(offset = 0) {
  if (!props.tableName) return
  sql.value = await DBDefaultTableQuery(
    props.sessionId,
    props.dbName || '',
    props.tableName,
    pageSize.value,
    offset,
  )
  browseMode.value = true
}

watch(() => props.tableName, async (name) => {
  insertingRow.value = false
  editingRow.value = false
  if (!name) return
  page.value = 0
  await loadBrowseSql(0)
  if (props.autoRun) await onExecute()
})

onMounted(async () => {
  refreshHistory()
  if (!props.tableName) return
  page.value = 0
  await loadBrowseSql(0)
  if (props.autoRun) await onExecute()
})

async function onExecute() {
  const selected = editorRef.value?.getSelectedOrAll?.() ?? sql.value
  const toRun = selected.trim()
  if (!toRun) return
  error.value = ''
  queryResult.value = null
  execResult.value = null
  scriptResult.value = null
  loading.value = true
  cancelled = false
  resultFilter.value = ''
  const started = performance.now()

  // If user edited away from browse SQL, leave browse mode
  if (browseMode.value && props.tableName) {
    try {
      const expected = await DBDefaultTableQuery(
        props.sessionId,
        props.dbName || '',
        props.tableName,
        pageSize.value,
        page.value * pageSize.value,
      )
      if (normalizeSql(sql.value) !== normalizeSql(expected) && normalizeSql(toRun) !== normalizeSql(expected)) {
        browseMode.value = false
      }
    } catch { /* ignore */ }
  }

  try {
    // Multi-statement scripts must run as a script: ExecuteQuery/Statement
    // would only send the first statement (multiStatements is off in the DSN).
    if (hasMultipleStatements(toRun)) {
      const result = await ExecuteSQLScript(props.sessionId, props.dbName || '', toRun)
      if (!cancelled) {
        scriptResult.value = result
        if (result?.failedLine) emit('cellUpdated')
      }
    } else if (isQuerySql(toRun)) {
      const result = await ExecuteQuery(props.sessionId, props.dbName || '', firstStatement(toRun))
      if (!cancelled) {
        queryResult.value = result
        browseHasMore.value = browseMode.value && result.rows.length >= pageSize.value
        lastDurationMs.value = Math.round(performance.now() - started)
        history.value = pushSqlHistory(props.sessionId, {
          sql: toRun,
          executedAt: new Date().toISOString(),
          durationMs: lastDurationMs.value,
          rowCount: result.rows.length,
        })
      }
    } else {
      const result = await ExecuteStatement(props.sessionId, props.dbName || '', toRun)
      if (!cancelled) {
        execResult.value = result
        lastDurationMs.value = Math.round(performance.now() - started)
        history.value = pushSqlHistory(props.sessionId, {
          sql: toRun,
          executedAt: new Date().toISOString(),
          durationMs: lastDurationMs.value,
          rowCount: result.affected,
        })
      }
    }
  } catch (e: any) {
    if (!cancelled) {
      error.value = e?.message || String(e)
      lastDurationMs.value = Math.round(performance.now() - started)
      history.value = pushSqlHistory(props.sessionId, {
        sql: toRun,
        executedAt: new Date().toISOString(),
        durationMs: lastDurationMs.value,
        error: error.value,
      })
    }
  } finally {
    loading.value = false
  }
}

function onCancelQuery() {
  cancelled = true
  loading.value = false
}

const scriptResult = shallowRef<ScriptResult | null>(null)

// Wails v3 rejects the picker promise with "cancelled by user" when the
// dialog is dismissed, instead of resolving with an empty path.
function isDialogCancel(e: unknown): boolean {
  return String(e).toLowerCase().includes('cancel')
}

// Only load files up to 1MB into the editor; larger ones run without display.
const sqlFileEditorLimit = 1 << 20

async function onOpenScriptFile() {
  let path = ''
  try {
    path = await OpenFileDialogFiltered(t('db.runSqlFile'), 'SQL File', '*.sql')
  } catch (e) {
    if (!isDialogCancel(e)) error.value = (e as any)?.message || String(e)
    return
  }
  if (!path) return
  try {
    const b64 = await ReadFileBase64(path)
    const text = decodeBase64(b64)
    error.value = ''
    queryResult.value = null
    execResult.value = null
    scriptResult.value = null
    if (text.length <= sqlFileEditorLimit) sql.value = text
    loading.value = true
    cancelled = false
    const result = await ExecuteSQLScript(props.sessionId, props.dbName || '', text)
    if (!cancelled) {
      scriptResult.value = result
      if (result?.failedLine) emit('cellUpdated')
    }
  } catch (e: any) {
    if (!cancelled) error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
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

async function onPageChange(p: number) {
  page.value = Math.max(0, p - 1)
  await loadBrowseSql(page.value * pageSize.value)
  await onExecute()
}

async function onPageSizeChange(size: number) {
  pageSize.value = size
  page.value = 0
  await loadBrowseSql(0)
  await onExecute()
}

function onSortChange(payload: { field: string; order: 'asc' | 'desc' | null }) {
  sortProp.value = payload.field || ''
  sortOrder.value = payload.order === 'asc' ? 'ascending' : payload.order === 'desc' ? 'descending' : null
}

const resultGridRef = ref<InstanceType<typeof DBResultGrid> | null>(null)

/** Number of unsaved inline cell edits staged in the result grid. */
const pendingCount = ref(0)
const savingRows = ref(false)

function onPendingChange(count: number) {
  pendingCount.value = count
}

/** Persist every staged cell edit via UPDATE ... WHERE original primary keys. */
async function onSaveEdits() {
  const edits = resultGridRef.value?.getPendingEdits() || []
  if (!edits.length || savingRows.value) return
  savingRows.value = true
  let ok = true
  try {
    for (const ed of edits) {
      try {
        await DBUpdateRow(
          props.sessionId,
          props.dbName || '',
          props.tableName,
          { [ed.field]: ed.newValue },
          ed.where,
        )
        resultGridRef.value?.markCommitted(ed.row, ed.field)
      } catch (e: any) {
        ok = false
        resultGridRef.value?.revertRow(ed.row)
        const m = e?.message || String(e)
        error.value = m
        msg.error(m)
        break
      }
    }
    if (ok) {
      error.value = ''
      emit('cellUpdated')
    }
  } finally {
    savingRows.value = false
  }
}

function onUndoEdits() {
  resultGridRef.value?.revertAll()
}

function rowIndexOf(row: Record<string, any>): number {
  const rows = queryResult.value?.rows
  if (!rows?.length) return -1
  const direct = rows.indexOf(row)
  if (direct >= 0) return direct
  const pks = resolvedPrimaryKeys.value
  if (pks.length > 0) {
    const byPk = rows.findIndex(r => pks.every(pk => r?.[pk] === row?.[pk]))
    if (byPk >= 0) return byPk
  }
  const cols = queryResult.value?.columns?.map(c => c.name) || Object.keys(row)
  return rows.findIndex(r => cols.every(c => r?.[c] === row?.[c]))
}

function startEditRowByRow(row: Record<string, any>) {
  const idx = rowIndexOf(row)
  if (idx < 0) {
    error.value = t('db.noPrimaryKey')
    return
  }
  startEditRow(idx)
}

async function onDeleteRowByRow(row: Record<string, any>) {
  const idx = rowIndexOf(row)
  if (idx < 0) {
    error.value = t('db.noPrimaryKey')
    return
  }
  await onDeleteRow(idx)
}

// ?? Resize splitter ??

const rootRef = ref<HTMLElement | null>(null)
const topHeight = ref(200)
let resizeStartY = 0
let resizeStartHeight = 0

function onResizeStart(e: MouseEvent) {
  resizeStartY = e.clientY
  resizeStartHeight = topHeight.value
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function onResizeMove(e: MouseEvent) {
  const dy = e.clientY - resizeStartY
  const el = rootRef.value
  const maxTop = el ? el.clientHeight - 100 : 600
  topHeight.value = Math.max(100, Math.min(maxTop, resizeStartHeight + dy))
}

function onResizeEnd() {
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

async function onDeleteRow(rowIndex: number) {
  const pks = resolvedPrimaryKeys.value
  if (rowIndex < 0 || !props.tableName || !pks.length) return

  try {
    await ElMessageBox.confirm(t('db.deleteRowConfirm'), t('common.confirm'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
  } catch {
    return
  }

  const row = queryResult.value!.rows[rowIndex]
  const where: Record<string, any> = {}
  for (const pk of pks) {
    where[pk] = row[pk] ?? null
  }

  try {
    await DBDeleteRow(props.sessionId, props.dbName || '', props.tableName, where)
    queryResult.value = {
      ...queryResult.value!,
      rows: queryResult.value!.rows.filter((_, i) => i !== rowIndex)
    }
    error.value = ''
    emit('cellUpdated')
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

const insertingRow = ref(false)
const insertValues = ref<Record<string, string>>({})
const insertNulls = ref<Record<string, boolean>>({})
const insertAutoIncrement = ref<Record<string, boolean>>({})
const insertColumns = ref<string[]>([])

async function startInsertRow() {
  let cols: ColumnInfo[]
  try {
    const schema = await GetTableSchema(props.sessionId, props.dbName || '', props.tableName || '')
    cols = schema.columns
  } catch {
    cols = queryResult.value!.columns.map(c => ({ name: c.name, type: c.type, nullable: true, defaultVal: '', defaultType: 'none', isPrimary: false, collation: '', comment: '', onUpdate: false }))
  }
  insertColumns.value = cols.map(c => c.name)
  insertNulls.value = {}
  insertAutoIncrement.value = {}
  insertValues.value = {}
  for (const col of cols) {
    if (col.defaultType === 'auto') {
      insertAutoIncrement.value[col.name] = true
      insertNulls.value[col.name] = false
      insertValues.value[col.name] = ''
    } else {
      const isNullDefault = col.defaultType === 'null' || (col.nullable && col.defaultType === 'none')
      insertNulls.value[col.name] = isNullDefault
      const rawDefault = col.defaultType === 'value' ? (col.defaultVal ?? '') : ''
      insertValues.value[col.name] = rawDefault === "''" ? '' : rawDefault
    }
  }
  editingRow.value = false
  insertingRow.value = true
}

async function onInsertConfirm() {
  if (!props.tableName) return

  const includedCols = insertColumns.value.filter(c => !insertAutoIncrement.value[c])
  const values: Record<string, any> = {}
  for (const col of includedCols) {
    values[col] = insertNulls.value[col] ? null : (insertValues.value[col] ?? '')
  }

  try {
    await DBInsertRow(props.sessionId, props.dbName || '', props.tableName, values)
    error.value = ''
    insertingRow.value = false
    emit('cellUpdated')
    await onExecute()
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

function onInsertCancel() {
  insertingRow.value = false
}

function getColumnType(colName: string): string {
  return props.tableColumns?.find(c => c.name === colName)?.type ?? ''
}

function isColumnPrimary(colName: string): boolean {
  return props.tableColumns?.find(c => c.name === colName)?.isPrimary ?? false
}

function isColumnAuto(colName: string): boolean {
  if (props.tableColumns) {
    const col = props.tableColumns.find(c => c.name === colName)
    if (col) return col.defaultType === 'auto'
  }
  return insertAutoIncrement.value[colName] === true
}

function getColumnNullable(colName: string): boolean {
  return props.tableColumns?.find(c => c.name === colName)?.nullable ?? true
}

function getColumnPlaceholder(colName: string): string {
  const val = props.tableColumns?.find(c => c.name === colName)?.defaultVal ?? ''
  return val === "''" ? '' : val
}

const editingRow = ref(false)
const editingRowIndex = ref(-1)
const editRowValues = ref<Record<string, string>>({})
const editNulls = ref<Record<string, boolean>>({})
const editRowColumns = ref<string[]>([])

function startEditRow(rowIndex: number) {
  if (rowIndex < 0 || !queryResult.value) return
  editingRowIndex.value = rowIndex
  const row = queryResult.value.rows[rowIndex]
  if (!row) return
  editRowColumns.value = queryResult.value.columns.map(c => c.name)
  editRowValues.value = {}
  editNulls.value = {}
  for (const col of editRowColumns.value) {
    if (row[col] === null) {
      editRowValues.value[col] = ''
      editNulls.value[col] = true
    } else {
      editRowValues.value[col] = String(row[col] ?? '')
      editNulls.value[col] = false
    }
  }
  insertingRow.value = false
  editingRow.value = true
}

async function onEditRowConfirm() {
  if (!props.tableName) return
  const pks = resolvedPrimaryKeys.value
  if (!pks.length) {
    error.value = t('db.noPrimaryKey')
    return
  }
  if (editingRowIndex.value < 0) return

  const row = queryResult.value!.rows[editingRowIndex.value]
  const set: Record<string, any> = {}
  for (const col of editRowColumns.value) {
    if (editNulls.value[col]) {
      if (row[col] !== null) set[col] = null
    } else {
      const newVal = editRowValues.value[col] ?? ''
      const oldVal = String(row[col] ?? '')
      if (newVal !== oldVal) set[col] = newVal
    }
  }
  if (Object.keys(set).length === 0) {
    editingRow.value = false
    return
  }

  const where: Record<string, any> = {}
  for (const pk of pks) {
    where[pk] = row[pk] ?? null
  }

  try {
    await DBUpdateRow(props.sessionId, props.dbName || '', props.tableName, set, where)
    const idx = editingRowIndex.value
    const updatedRow = { ...queryResult.value!.rows[idx] }
    for (const col of editRowColumns.value) {
      updatedRow[col] = editNulls.value[col] ? null : editRowValues.value[col]
    }
    queryResult.value = {
      ...queryResult.value!,
      rows: queryResult.value!.rows.map((r, i) => i === idx ? updatedRow : r)
    }
    error.value = ''
    editingRow.value = false
    emit('cellUpdated')
  } catch (e: any) {
    error.value = e?.message || String(e)
  }
}

function onEditRowCancel() {
  editingRow.value = false
}
</script>

<style scoped>
.db-query-editor {
  height: 100%;
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}
.loading-overlay {
  position: absolute;
  inset: 0;
  background: var(--scrim);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.spinner {
  width: 1.75rem;
  height: 1.75rem;
  border: 0.1875rem solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-text {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-primary);
}
.editor-top {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.5rem 0;
  min-height: 0;
  min-width: 0;
  width: 100%;
  overflow: hidden;
}
.editor-toolbar {
  display: flex;
  gap: 0.375rem;
  margin-bottom: 0.375rem;
  align-items: center;
  flex-shrink: 0;
}
.sql-editor-wrap {
  position: relative;
  flex: 1 1 auto;
  min-height: 5rem;
  min-width: 0;
  width: 100%;
  align-self: stretch;
  overflow: hidden;
}
.history-panel {
  max-height: 8.75rem;
  overflow: auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  margin-bottom: 0.375rem;
  flex-shrink: 0;
}
.history-empty {
  padding: 0.5rem 0.625rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}
.history-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  width: 100%;
  text-align: left;
  padding: 0.375rem 0.625rem;
  border: none;
  border-bottom: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-family: var(--font-mono);
  font-size: 0.75rem;
}
.history-item:hover { background: var(--bg-hover); }
.history-sql {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-meta {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  color: var(--text-muted);
}
.history-err { color: var(--error); }
.editor-resizer {
  height: 0.25rem;
  cursor: row-resize;
  background: transparent;
  flex-shrink: 0;
}
.editor-resizer:hover { background: var(--border-subtle); }
.editor-bottom {
  flex: 1;
  padding: 0 0.5rem 0.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.error-msg {
  color: var(--error);
  padding: 0.5rem;
  background: var(--error-subtle);
  border-radius: var(--radius-sm);
  margin-bottom: 0.5rem;
  user-select: text;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  flex-shrink: 0;
}
.result-info {
  padding: 0.25rem 0;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.script-result {
  padding: 0.375rem 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.script-result.has-error {
  background: var(--error-subtle);
  color: var(--error);
}
.script-ok { color: var(--text-primary); }
.script-affected { margin-left: 0.75rem; }
.script-error-head { font-weight: 600; }
.script-error-detail { margin-top: 0.25rem; font-family: var(--font-mono); font-size: 0.75rem; word-break: break-word; }
.script-error-sql {
  margin: 0.25rem 0 0;
  padding: 0.375rem;
  background: var(--bg-base);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 10rem;
  overflow: auto;
}
.result-duration { color: var(--text-muted); }
.result-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  flex-shrink: 0;
}
.result-filter {
  width: 12.5rem;
  padding: 0.1875rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  font-size: 0.75rem;
  outline: none;
}
.result-filter:focus { border-color: var(--accent); }
.result-toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin-left: auto;
  min-width: 0;
}
.result-grid { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
.result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.25rem 0;
  flex-shrink: 0;
}
.result-count {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.save-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0;
  flex-shrink: 0;
}
.save-hint {
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-right: auto;
}
.insert-row-form {
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  margin-top: 0.25rem;
  flex-shrink: 0;
  overflow: auto;
  max-height: 40%;
}
.row-form {
  display: flex;
  flex-direction: column;
  max-height: 60vh;
  overflow-y: auto;
}
.row-form-row {
  display: grid;
  grid-template-columns: 10rem 5.625rem minmax(0, 1fr) 6.75rem;
  gap: 0.625rem;
  align-items: center;
  padding: 0.3125rem 0;
  border-bottom: 1px solid var(--border-subtle);
}
.row-form-row:last-child { border-bottom: none; }
.field-name {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-type {
  font-family: var(--font-ui);
  font-size: 0.625rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-toggle {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.25rem;
  font-size: 0.625rem;
  cursor: pointer;
  color: var(--text-muted);
  white-space: nowrap;
}
.field-toggle input { cursor: pointer; margin: 0; }
.field-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  background: var(--bg-base);
  color: var(--text-primary);
}
.field-input:disabled {
  background: var(--bg-elevated);
  color: var(--text-muted);
  cursor: not-allowed;
}
</style>
