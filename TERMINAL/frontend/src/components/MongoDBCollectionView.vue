<template>
  <div class="mongo-collection-view">
    <!-- Sub-tabs -->
    <div class="mongo-tabs">
      <button class="mongo-tab" :class="{ active: activeSubTab === 'query' }" @click="activeSubTab = 'query'">
        {{ t('mongodb.queryTab') }}
      </button>
      <button class="mongo-tab" :class="{ active: activeSubTab === 'indexes' }" @click="activeSubTab = 'indexes'; loadIndexes()">
        {{ t('mongodb.indexesTab') }}
      </button>
    </div>

    <!-- Query sub-tab -->
    <div v-if="activeSubTab === 'query'" class="query-section">
      <div class="editor-top" :style="{ height: topHeight + 'px' }">
        <div class="editor-toolbar">
          <input
            v-model="nlInput"
            class="nl-input"
            :placeholder="t('mongodb.aiPlaceholder')"
            @keydown.enter="generateFilter"
          />
          <button class="btn btn-default btn-sm" @click="generateFilter" :disabled="aiGenerating || !nlInput.trim()">
            <Sparkles :size="'0.875rem'" :class="{ 'ai-pulse': aiGenerating }" />
            {{ aiGenerating ? '...' : 'AI' }}
          </button>
          <button class="btn btn-primary btn-sm" title="Ctrl+Enter" @click="onExecute">{{ t('mongodb.executeQuery') }}</button>
        </div>
        <div class="filter-editor-wrap">
          <SyntaxEditor
            v-model="filterText"
            lang="json"
            compact
            @execute="onExecute"
          />
        </div>
      </div>

      <div class="editor-resizer" @mousedown="onTopResizeStart" />

      <div class="editor-bottom">
        <div v-if="queryError" class="error-msg">{{ queryError }}</div>

        <div v-if="queryLoading" class="loading-overlay">
          <div class="loading-box">
            <div class="spinner" />
            <span class="loading-text">{{ t('db.loading') }}</span>
            <button class="btn btn-default" @click="cancelQuery">{{ t('common.cancel') }}</button>
          </div>
        </div>

        <div v-if="columns.length > 0" class="result-toolbar">
          <input
            v-model="resultFilter"
            class="result-filter"
            :placeholder="t('db.filterResults')"
          />
          <button class="btn btn-default btn-sm result-toolbar-add" @click="openNewDocument">
            <Plus :size="'0.875rem'" /> {{ t('mongodb.newDocument') }}
          </button>
        </div>

        <div v-if="filteredTableData.length > 0" class="result-grid">
          <div class="result-table-wrap">
            <el-table
              :data="filteredTableData"
              border
              size="small"
              style="width:100%"
              class="db-result-table"
              :empty-text="t('db.noData')"
              @row-dblclick="onRowDblClick"
            >
              <el-table-column
                v-for="col in columns"
                :key="col"
                :prop="col"
                :label="col"
                :min-width="uiPx(120)"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span
                    class="cell-value"
                    :class="{ 'cell-null': row[col] === null || row[col] === undefined }"
                  >{{ formatCellValue(row[col]) }}</span>
                </template>
              </el-table-column>
              <el-table-column :width="uiPx(80)" fixed="right">
                <template #default="{ row }">
                  <button class="btn btn-ghost btn-icon btn-sm" @click.stop="onRowDblClick(row)">
                    <Pencil :size="'0.875rem'" />
                  </button>
                  <button class="btn btn-ghost btn-icon btn-sm danger" @click.stop="deleteDocument(row)">
                    <Trash2 :size="'0.875rem'" />
                  </button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="result-footer">
            <span class="result-count">
              {{ filteredTableData.length }}{{ resultFilter ? ` / ${tableData.length}` : '' }} {{ t('db.rows') }}
            </span>
            <el-pagination
              background
              layout="sizes, prev, pager, next"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="queryLimit"
              :total="totalDocs"
              :current-page="currentPage"
              :pager-count="5"
              small
              @size-change="onPageSizeChange"
              @current-change="onPageChange"
            />
          </div>
        </div>
        <div v-else-if="!queryLoading" class="db-placeholder">
          <span>{{ t('db.noData') }}</span>
        </div>
      </div>
    </div>

    <!-- Indexes sub-tab -->
    <div v-if="activeSubTab === 'indexes'" class="indexes-section">
      <div v-if="indexLoading" class="loading-overlay">
        <div class="loading-box">
          <div class="spinner" />
          <span class="loading-text">{{ t('db.loading') }}</span>
        </div>
      </div>
      <div style="margin-bottom:0.5rem;display:flex;justify-content:flex-end">
        <button class="btn btn-default btn-sm" @click="openNewIndexDialog">
          <Plus :size="'0.875rem'" /> {{ t('db.addIndex') }}
        </button>
      </div>
      <el-table :data="indexes" border size="small" style="width:100%" :empty-text="t('db.noData')">
        <el-table-column prop="name" :label="t('db.colName')" show-overflow-tooltip />
        <el-table-column label="Fields">
          <template #default="{ row }">
            {{ (row as MongoIndexInfo).keys.join(', ') }}
          </template>
        </el-table-column>
        <el-table-column prop="type" :label="t('db.colType')" />
        <el-table-column prop="unique" label="Unique" :width="uiPx(80)">
          <template #default="{ row }">
            {{ row.unique ? '✓' : '' }}
          </template>
        </el-table-column>
        <el-table-column :width="uiPx(60)">
          <template #default="{ row }">
            <button v-if="row.name !== '_id_'" class="btn btn-ghost btn-icon btn-sm" style="color:var(--error)" @click="dropIndex(row.name)">
              <Trash2 :size="'0.875rem'" />
            </button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Indexes sub-tab -->
    <el-dialog append-to-body v-model="newIndexDialogVisible" :title="t('db.addIndex')" width="25rem">
      <el-form label-width="5rem">
        <el-form-item :label="t('db.colName')">
          <el-input v-model="newIndexName" placeholder="index_name" />
        </el-form-item>
        <el-form-item label="Fields">
          <el-input v-model="newIndexFields" placeholder="field1,-field2" />
        </el-form-item>
        <el-form-item label="Unique">
          <el-switch v-model="newIndexUnique" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newIndexDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newIndexName.trim() || !newIndexFields.trim()" @click="createIndex">
          {{ t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Document editor dialog -->
    <el-dialog append-to-body
      v-model="docDialogVisible"
      :title="docDialogMode === 'insert' ? t('mongodb.newDocument') : t('mongodb.editDocument')"
      width="37.5rem"
    >
      <SyntaxEditor
        v-model="docEditorText"
        lang="json"
        class="doc-editor"
      />
      <div v-if="docEditorError" class="error-msg" style="margin-top:0.5rem">{{ docEditorError }}</div>
      <template #footer>
        <el-button @click="docDialogVisible = false">{{ t('settings.cancel') }}</el-button>
        <el-button type="primary" :loading="docSaving" @click="saveDocument">{{ t('redis.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Pencil, Trash2, Sparkles, Plus } from '@lucide/vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { chat } from '../services/llm'
import { uiPx } from '../utils/uiScale'
import {
  MongoFind,
  MongoInsertOne,
  MongoUpdateOne,
  MongoDeleteOne,
  MongoListIndexes,
  MongoCreateIndex,
  MongoDropIndex,
} from '../../bindings/easyaiot/terminal/app'
import type { MongoIndexInfo, MongoQueryResult } from '../types/mongodb'
import SyntaxEditor from './SyntaxEditor.vue'

defineOptions({ name: 'MongoDBCollectionView' })

const { t } = useI18n()

const props = defineProps<{
  sessionId: string
  dbName: string
  collectionName: string
}>()

// ── Editor resize state ──
const topHeight = ref(200)
let topResizeStartY = 0
let topResizeStartHeight = 0
let topResizing = false

function onTopResizeStart(e: MouseEvent) {
  topResizeStartY = e.clientY
  topResizeStartHeight = topHeight.value
  topResizing = true
  document.addEventListener('mousemove', onTopResizeMove)
  document.addEventListener('mouseup', onTopResizeEnd)
}
function onTopResizeMove(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest('.mongo-collection-view')
  const maxTop = el ? el.clientHeight - 100 : 400
  const dy = e.clientY - topResizeStartY
  topHeight.value = Math.max(80, Math.min(maxTop, topResizeStartHeight + dy))
}
function onTopResizeEnd() {
  topResizing = false
  document.removeEventListener('mousemove', onTopResizeMove)
  document.removeEventListener('mouseup', onTopResizeEnd)
}

// ── Query state ──
const activeSubTab = ref<'query' | 'indexes'>('query')
const filterText = ref('{}')
const nlInput = ref('')
const aiGenerating = ref(false)
const queryLimit = ref(100)
const queryLoading = ref(false)
const queryError = ref('')
const queryResult = ref<MongoQueryResult | null>(null)
const currentSkip = ref(0)

const totalDocs = computed(() => queryResult.value?.total || 0)

const tableData = computed(() => {
  if (!queryResult.value) return []
  return queryResult.value.documents.map(d => {
    try { return JSON.parse(d) } catch { return {} }
  })
})

const resultFilter = ref('')

const filteredTableData = computed(() => {
  const q = resultFilter.value.trim().toLowerCase()
  if (!q) return tableData.value
  return tableData.value.filter(row => JSON.stringify(row).toLowerCase().includes(q))
})

const columns = computed(() => {
  const keySet = new Set<string>()
  for (const row of tableData.value) {
    for (const key of Object.keys(row)) {
      keySet.add(key)
    }
  }
  const cols = Array.from(keySet)
  const idIdx = cols.indexOf('_id')
  if (idIdx > 0) {
    cols.splice(idIdx, 1)
    cols.unshift('_id')
  }
  return cols
})

// ── Index state ──
const indexes = ref<MongoIndexInfo[]>([])
const indexLoading = ref(false)

// ── Dialog state ──
const newIndexDialogVisible = ref(false)
const newIndexName = ref('')
const newIndexFields = ref('')
const newIndexUnique = ref(false)

const docDialogVisible = ref(false)
const docDialogMode = ref<'insert' | 'edit'>('insert')
const docEditorText = ref('{}')
const docEditorError = ref('')
const docSaving = ref(false)
const editingRow = ref<any>(null)

// ── Query methods ──
// User-initiated execution (toolbar button / Ctrl+Enter in editor) restarts from page 1.
function onExecute() {
  currentSkip.value = 0
  executeQuery()
}

async function generateFilter() {
  const input = nlInput.value.trim()
  if (!input || !props.dbName || !props.collectionName) return
  aiGenerating.value = true
  try {
    let sample = ''
    try {
      const result = await MongoFind(props.sessionId, props.dbName, props.collectionName, '{}', 0, 1)
      if (result.documents.length > 0) {
        sample = result.documents[0]
      }
    } catch {}

    const schemaContext = sample
      ? `Collection "${props.collectionName}" in database "${props.dbName}". Sample document:\n${sample}`
      : `Collection "${props.collectionName}" in database "${props.dbName}".`

    let result = ''
    await chat({
      system: `You are a MongoDB query assistant. Convert natural language to MongoDB Extended JSON filter only. Output ONLY the JSON filter (no markdown, no explanation). Use operators like $eq, $gt, $gte, $lt, $lte, $in, $nin, $regex, $exists, $and, $or, $not, $elemMatch. Dates should use ISODate format. ObjectIds should use $oid format.`,
      messages: [
        { role: 'user', content: `Schema context:\n${schemaContext}\n\nQuery: ${input}` }
      ],
      onChunk: (chunk: string) => { result += chunk },
    })
    const cleaned = result.trim()
      .replace(/^```[\w]*\n?/i, '')
      .replace(/\n?```$/i, '')
    JSON.parse(cleaned)
    filterText.value = cleaned
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
  aiGenerating.value = false
}

async function executeQuery() {
  if (!props.dbName || !props.collectionName) return
  queryLoading.value = true
  queryError.value = ''
  try {
    queryResult.value = await MongoFind(
      props.sessionId,
      props.dbName,
      props.collectionName,
      filterText.value,
      currentSkip.value,
      queryLimit.value
    )
  } catch (e: any) {
    queryError.value = e?.message || String(e)
    queryResult.value = null
  }
  queryLoading.value = false
}

function cancelQuery() {
  queryLoading.value = false
}

const currentPage = computed(() => Math.floor(currentSkip.value / queryLimit.value) + 1)

function onPageChange(page: number) {
  currentSkip.value = (page - 1) * queryLimit.value
  executeQuery()
}

function onPageSizeChange(size: number) {
  queryLimit.value = size
  currentSkip.value = 0
  executeQuery()
}

// ── Document CRUD ──
function openNewDocument() {
  docDialogMode.value = 'insert'
  docEditorText.value = '{}'
  docEditorError.value = ''
  editingRow.value = null
  docDialogVisible.value = true
}

// Double-click a row (or the action pencil) to open the document editor.
function onRowDblClick(row: any) {
  docDialogMode.value = 'edit'
  docEditorText.value = JSON.stringify(row, null, 2)
  docEditorError.value = ''
  editingRow.value = row
  docDialogVisible.value = true
}

async function saveDocument() {
  try {
    JSON.parse(docEditorText.value)
  } catch {
    docEditorError.value = t('mongodb.invalidJSON')
    return
  }
  docEditorError.value = ''
  docSaving.value = true
  try {
    if (docDialogMode.value === 'insert') {
      await MongoInsertOne(props.sessionId, props.dbName, props.collectionName, docEditorText.value)
      msg.success(t('mongodb.insertSuccess'))
    } else {
      const filter = JSON.stringify({ _id: editingRow.value._id })
      const updateObj = JSON.parse(docEditorText.value)
      delete updateObj._id
      await MongoUpdateOne(props.sessionId, props.dbName, props.collectionName, filter, JSON.stringify(updateObj))
      msg.success(t('mongodb.updateSuccess'))
    }
    docDialogVisible.value = false
    executeQuery()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
  docSaving.value = false
}

async function deleteDocument(row: any) {
  try {
    await ElMessageBox.confirm(t('mongodb.deleteConfirm'))
  } catch {
    return
  }
  try {
    const filter = JSON.stringify({ _id: row._id })
    await MongoDeleteOne(props.sessionId, props.dbName, props.collectionName, filter)
    msg.success(t('mongodb.deleteSuccess'))
    executeQuery()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

// ── Indexes ──
async function loadIndexes() {
  if (!props.dbName || !props.collectionName) return
  indexLoading.value = true
  try {
    indexes.value = await MongoListIndexes(props.sessionId, props.dbName, props.collectionName)
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
  indexLoading.value = false
}

function openNewIndexDialog() {
  newIndexName.value = ''
  newIndexFields.value = ''
  newIndexUnique.value = false
  newIndexDialogVisible.value = true
}

async function createIndex() {
  const name = newIndexName.value.trim()
  const fields = newIndexFields.value.trim()
  if (!name || !fields || !props.dbName || !props.collectionName) return
  try {
    await MongoCreateIndex(
      props.sessionId, props.dbName, props.collectionName,
      name, fields.split(',').map(s => s.trim()).filter(Boolean),
      newIndexUnique.value
    )
    newIndexDialogVisible.value = false
    loadIndexes()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function dropIndex(name: string) {
  if (!props.dbName || !props.collectionName) return
  try {
    await MongoDropIndex(props.sessionId, props.dbName, props.collectionName, name)
    loadIndexes()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

// ── Helpers ──
function formatCellValue(val: any): string {
  if (val === null || val === undefined) return 'null'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

// ── Lifecycle ──
onMounted(() => {
  executeQuery()
})

onUnmounted(() => {
  if (topResizing) {
    document.removeEventListener('mousemove', onTopResizeMove)
    document.removeEventListener('mouseup', onTopResizeEnd)
  }
})

// Switching collection re-runs the default query
watch(() => [props.dbName, props.collectionName], () => {
  filterText.value = '{}'
  nlInput.value = ''
  resultFilter.value = ''
  currentSkip.value = 0
  queryResult.value = null
  queryError.value = ''
  activeSubTab.value = 'query'
  nextTick(() => executeQuery())
})
</script>

<style scoped>
.mongo-collection-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  position: relative;
}

.mongo-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 0.5rem;
  flex-shrink: 0;
}
.mongo-tab {
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
.mongo-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.mongo-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}

.ai-pulse { animation: fade-pulse 1.2s ease-in-out infinite; }
@keyframes fade-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.query-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}
.editor-top {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0.5rem 0;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  flex-shrink: 0;
}
.nl-input {
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
}
.nl-input:focus { border-color: var(--accent); }
.filter-editor-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}
.result-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  flex-shrink: 0;
}
.result-toolbar-add { margin-left: auto; }
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

.editor-resizer {
  height: 0.25rem;
  cursor: row-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.editor-resizer:hover {
  background: var(--border-subtle);
}

.editor-bottom {
  flex: 1;
  padding: 0 0.5rem 0.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.error-msg {
  color: var(--error);
  padding: 0.5rem;
  background: var(--error-subtle);
  border-radius: var(--radius-sm);
  margin-bottom: 0.5rem;
  user-select: text;
  -webkit-user-select: text;
  cursor: text;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
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

.result-grid {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.result-table-wrap {
  flex: 1;
  overflow: auto;
  min-height: 0;
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
.cell-value {
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  word-break: break-all;
  cursor: default;
}
.cell-null {
  color: var(--text-muted);
  font-style: italic;
}
.result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding-top: 0.5rem;
  flex-shrink: 0;
}
.result-count {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.result-footer :deep(.el-pager li.is-active) {
  background-color: var(--accent);
  color: var(--on-accent);
}
.result-footer :deep(.el-pager li:hover) {
  color: var(--accent);
}
.result-footer :deep(.el-pagination .el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--accent) inset;
}
.result-footer :deep(.el-select__input) {
  color: var(--text-primary);
}

.indexes-section {
  flex: 1;
  overflow: auto;
  padding: 0.5rem;
  position: relative;
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

.doc-editor {
  height: 20rem;
}
</style>
