<template>
  <div class="es-index-view">
    <!-- Sub-tabs -->
    <div class="iv-tabs">
      <button class="iv-tab" :class="{ active: activeSubTab === 'docs' }" @click="activeSubTab = 'docs'">
        {{ t('es.docsTab') }}
      </button>
      <button class="iv-tab" :class="{ active: activeSubTab === 'mapping' }" @click="switchToMapping">
        {{ t('es.mappingTab') }}
      </button>
      <button class="iv-tab" :class="{ active: activeSubTab === 'settings' }" @click="switchToSettings">
        {{ t('es.settingsTab') }}
      </button>
    </div>

    <!-- Documents -->
    <div v-if="activeSubTab === 'docs'" class="docs-section">
      <div class="editor-top" :style="{ height: topHeight + 'px' }">
        <div class="editor-toolbar">
          <el-radio-group v-model="queryMode" size="small">
            <el-radio-button value="simple">{{ t('es.querySimple') }}</el-radio-button>
            <el-radio-button value="dsl">{{ t('es.queryDsl') }}</el-radio-button>
          </el-radio-group>
          <button class="btn btn-primary btn-sm search-btn" title="Ctrl+Enter" @click="runSearch">{{ t('es.search') }}</button>
        </div>
        <div v-if="queryMode === 'simple'" class="simple-query-wrap">
          <input
            v-model="simpleQuery"
            class="search-input"
            :placeholder="t('es.simpleQueryPlaceholder')"
            @keydown.enter="runSearch"
          />
        </div>
        <div v-else class="query-editor-wrap">
          <SyntaxEditor
            v-model="dslBody"
            lang="json"
            compact
            @execute="runSearch"
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
          </div>
        </div>

        <div v-if="columns.length > 0" class="result-toolbar">
          <input
            v-model="resultFilter"
            class="result-filter"
            :placeholder="t('db.filterResults')"
          />
          <button class="btn btn-default btn-sm result-toolbar-add" @click="openNewDocument">
            <Plus :size="'0.875rem'" /> {{ t('es.newDocument') }}
          </button>
        </div>

        <div v-if="columns.length > 0" class="result-grid">
          <div class="result-table-wrap">
            <el-table
              :data="filteredTableData"
              border
              size="small"
              style="width:100%"
              class="db-result-table"
              :empty-text="t('db.noData')"
              @row-click="onRowClick"
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
            <span class="result-count" v-if="searchResult">
              {{ filteredTableData.length }}{{ resultFilter ? ` / ${tableData.length}` : '' }} hits · {{ searchResult.took }}ms
            </span>
            <el-pagination
              background
              layout="sizes, prev, pager, next"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="pageSize"
              :total="searchResult?.total || 0"
              :current-page="currentPage"
              :pager-count="5"
              small
              @size-change="onPageSizeChange"
              @current-change="onPageChange"
            />
          </div>
        </div>
        <div v-else-if="!queryLoading && !queryError" class="select-hint">{{ t('es.selectHint') }}</div>
      </div>
    </div>

    <!-- Mapping -->
    <div v-else-if="activeSubTab === 'mapping'" class="json-pane">
      <div v-if="mappingLoading" class="tree-loading">{{ t('db.loading') }}</div>
      <pre v-else class="json-pre">{{ mappingText || t('es.noData') }}</pre>
    </div>

    <!-- Settings -->
    <div v-else-if="activeSubTab === 'settings'" class="json-pane">
      <div v-if="settingsLoading" class="tree-loading">{{ t('db.loading') }}</div>
      <pre v-else class="json-pre">{{ settingsText || t('es.noData') }}</pre>
    </div>

    <!-- Document editor dialog -->
    <el-dialog
      v-model="docDialogVisible"
      :title="docDialogMode === 'create' ? t('es.newDocument') : t('es.editDocument')"
      width="40rem"
      destroy-on-close
    >
      <el-form label-width="5rem">
        <el-form-item v-if="docDialogMode === 'create'" :label="t('es.documentId')">
          <el-input v-model="docEditId" :placeholder="t('es.documentIdAuto')" />
        </el-form-item>
        <el-form-item :label="t('es.docBody')">
          <SyntaxEditor v-model="docEditText" lang="json" class="doc-editor" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="docDialogVisible = false">{{ t('settings.cancel') }}</el-button>
        <el-button type="primary" :loading="docSaving" @click="saveDocument">{{ t('redis.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Pencil, Trash2, Plus } from '@lucide/vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { uiPx } from '../utils/uiScale'
import {
  EsSearch,
  EsGetMapping,
  EsGetSettings,
  EsIndexDoc,
  EsUpdateDoc,
  EsDeleteDoc,
} from '../../bindings/easyaiot/terminal/app'
import type { EsSearchResult } from '../types/elasticsearch'
import SyntaxEditor from './SyntaxEditor.vue'

defineOptions({ name: 'ElasticsearchIndexView' })

const { t } = useI18n()

const props = defineProps<{
  sessionId: string
  indexName: string
}>()

const topHeight = ref(200)
const activeSubTab = ref<'docs' | 'mapping' | 'settings'>('docs')

const queryMode = ref<'simple' | 'dsl'>('simple')
const simpleQuery = ref('')
const dslBody = ref('{\n  "query": { "match_all": {} }\n}')
const queryLoading = ref(false)
const queryError = ref('')
const searchResult = ref<EsSearchResult | null>(null)
const pageFrom = ref(0)
const pageSize = ref(50)
const selectedRowId = ref('')

const mappingText = ref('')
const mappingLoading = ref(false)
const settingsText = ref('')
const settingsLoading = ref(false)

const docDialogVisible = ref(false)
const docDialogMode = ref<'create' | 'edit'>('create')
const docEditId = ref('')
const docEditText = ref('{\n  \n}')
const docSaving = ref(false)

const tableData = computed(() => {
  if (!searchResult.value) return []
  return searchResult.value.hits.map(h => {
    try { return JSON.parse(h) } catch { return { _raw: h } }
  })
})

const resultFilter = ref('')

const filteredTableData = computed(() => {
  const q = resultFilter.value.trim().toLowerCase()
  if (!q) return tableData.value
  return tableData.value.filter(row => JSON.stringify(row).toLowerCase().includes(q))
})

const columns = computed(() => {
  const cols = new Set<string>()
  cols.add('_id')
  for (const row of tableData.value) {
    for (const k of Object.keys(row)) {
      if (k !== '_index' && k !== '_score') cols.add(k)
    }
  }
  // Prefer _id first, then sorted field names (cap columns)
  const rest = [...cols].filter(c => c !== '_id').sort()
  return ['_id', ...rest].slice(0, 40)
})

const currentPage = computed(() => Math.floor(pageFrom.value / pageSize.value) + 1)

onMounted(() => {
  runSearch()
})

function buildSearchBody(): string {
  if (queryMode.value === 'dsl') {
    return dslBody.value.trim() || '{}'
  }
  const q = simpleQuery.value.trim()
  if (!q) return '{"query":{"match_all":{}}}'
  return JSON.stringify({
    query: {
      query_string: { query: q, default_field: '*' },
    },
  })
}

async function runSearch() {
  if (!props.sessionId || !props.indexName) return
  queryLoading.value = true
  queryError.value = ''
  try {
    searchResult.value = await EsSearch(
      props.sessionId,
      props.indexName,
      buildSearchBody(),
      pageFrom.value,
      pageSize.value,
    ) as EsSearchResult
  } catch (e: any) {
    queryError.value = e?.message || String(e)
    searchResult.value = null
  }
  queryLoading.value = false
}

function onPageChange(page: number) {
  pageFrom.value = (page - 1) * pageSize.value
  runSearch()
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  pageFrom.value = 0
  runSearch()
}

function formatCellValue(v: unknown): string {
  if (v === null || v === undefined) return 'null'
  if (typeof v === 'object') {
    const s = JSON.stringify(v)
    return s.length > 120 ? s.slice(0, 117) + '…' : s
  }
  const s = String(v)
  return s.length > 120 ? s.slice(0, 117) + '…' : s
}

function onRowClick(row: any) {
  selectedRowId.value = row?._id || ''
}

function onRowDblClick(row: any) {
  docDialogMode.value = 'edit'
  docEditId.value = row?._id || ''
  const copy = { ...row }
  delete copy._score
  delete copy._index
  docEditText.value = JSON.stringify(copy, null, 2)
  docDialogVisible.value = true
}

function openNewDocument() {
  docDialogMode.value = 'create'
  docEditId.value = ''
  docEditText.value = '{\n  \n}'
  docDialogVisible.value = true
}

async function saveDocument() {
  if (!props.sessionId || !props.indexName) return
  let parsed: any
  try {
    parsed = JSON.parse(docEditText.value)
  } catch {
    msg.error(t('es.invalidJSON'))
    return
  }
  const id = docDialogMode.value === 'edit' ? docEditId.value : (docEditId.value || parsed._id || '')
  const body = { ...parsed }
  delete body._id
  delete body._index
  delete body._score
  docSaving.value = true
  try {
    if (docDialogMode.value === 'edit') {
      if (!id) throw new Error('document _id required')
      await EsUpdateDoc(props.sessionId, props.indexName, id, JSON.stringify(body))
      msg.success(t('es.updateSuccess'))
    } else {
      await EsIndexDoc(props.sessionId, props.indexName, id, JSON.stringify(body))
      msg.success(t('es.insertSuccess'))
    }
    docDialogVisible.value = false
    await runSearch()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
  docSaving.value = false
}

async function deleteDocument(row: any) {
  const id = row?._id
  if (!id || !props.sessionId || !props.indexName) return
  try {
    await ElMessageBox.confirm(t('es.deleteConfirm'))
  } catch {
    return
  }
  try {
    await EsDeleteDoc(props.sessionId, props.indexName, id)
    msg.success(t('es.deleteSuccess'))
    await runSearch()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function switchToMapping() {
  activeSubTab.value = 'mapping'
  await loadMapping()
}

async function switchToSettings() {
  activeSubTab.value = 'settings'
  await loadSettings()
}

async function loadMapping() {
  if (!props.sessionId || !props.indexName) return
  mappingLoading.value = true
  try {
    mappingText.value = await EsGetMapping(props.sessionId, props.indexName)
  } catch (e: any) {
    mappingText.value = e?.message || String(e)
  }
  mappingLoading.value = false
}

async function loadSettings() {
  if (!props.sessionId || !props.indexName) return
  settingsLoading.value = true
  try {
    settingsText.value = await EsGetSettings(props.sessionId, props.indexName)
  } catch (e: any) {
    settingsText.value = e?.message || String(e)
  }
  settingsLoading.value = false
}

function onTopResizeStart(e: MouseEvent) {
  e.preventDefault()
  const startY = e.clientY
  const startH = topHeight.value
  const onMove = (ev: MouseEvent) => {
    topHeight.value = Math.max(100, Math.min(400, startH + ev.clientY - startY))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.es-index-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.iv-tabs {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  padding: 0 0.5rem;
  min-height: 2rem;
}
.iv-tab {
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
.iv-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.iv-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}

.docs-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.editor-top {
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  overflow: hidden;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  flex-shrink: 0;
}
.search-btn { margin-left: auto; }
.simple-query-wrap { flex: 1; min-height: 0; display: flex; }
.simple-query-wrap .search-input { height: 100%; }
.search-input {
  width: 100%;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.query-editor-wrap { flex: 1; min-height: 0; display: flex; overflow: hidden; }
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
  flex-shrink: 0;
}
.editor-resizer:hover { background: var(--border-subtle); }
.editor-bottom {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
  position: relative;
  overflow: hidden;
}
.result-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.result-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
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
  font-family: var(--font-mono);
  font-size: 0.75rem;
}
.cell-null {
  color: var(--text-muted);
  font-style: italic;
}
.result-footer {
  padding-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-shrink: 0;
}
.result-count {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.error-msg {
  color: var(--error);
  padding: 0.5rem;
  background: var(--error-subtle);
  border-radius: var(--radius-sm);
  margin-bottom: 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  white-space: pre-wrap;
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
  gap: 0.5rem;
}
.spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 0.125rem solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: iv-spin 0.8s linear infinite;
}
@keyframes iv-spin { to { transform: rotate(360deg); } }
.loading-text { font-size: 0.75rem; color: var(--text-secondary); }

.select-hint {
  padding: 1rem;
  color: var(--text-muted);
  font-size: 0.8125rem;
  text-align: center;
}
.json-pane {
  flex: 1;
  overflow: auto;
  padding: 0.75rem;
}
.json-pre {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-break: break-word;
  user-select: text;
}
.tree-loading {
  padding: 0.75rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.doc-editor {
  width: 100%;
  height: 20rem;
}
</style>
