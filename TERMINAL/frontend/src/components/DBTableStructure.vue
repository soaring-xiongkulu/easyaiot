<template>
  <div class="db-table-structure">
    <div v-if="!tableName" class="placeholder">{{ t('db.selectTableHint') }}</div>
    <template v-else>
      <div v-if="loading" class="loading-overlay">
        <div class="loading-box">
          <div class="spinner" />
          <span class="loading-text">{{ t('db.loading') }}</span>
          <button class="btn btn-default" @click="onCancelLoad">{{ t('common.cancel') }}</button>
        </div>
      </div>
      <div class="section">
        <div class="section-header">
          <div class="section-title">{{ t('db.columns') }}</div>
          <button class="btn btn-default btn-sm" @click="startAddColumn">
            <Plus :size="'0.875rem'" /> {{ t('db.addColumn') }}
          </button>
        </div>
        <el-table :data="schema?.columns || []" border size="small" style="width:100%">
          <el-table-column prop="name" :label="t('db.colName')" />
          <el-table-column prop="type" :label="t('db.colType')" />
          <el-table-column :label="t('db.colNullable')" :width="uiPx(80)">
            <template #default="{ row }">
              {{ row.nullable ? 'YES' : 'NO' }}
            </template>
          </el-table-column>
          <el-table-column prop="defaultVal" :label="t('db.colDefault')" />
          <el-table-column :label="t('db.colPrimary')" :width="uiPx(50)">
            <template #default="{ row }">
              <span v-if="row.isPrimary">PK</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('db.colAutoIncrement')" :width="uiPx(50)">
            <template #default="{ row }">
              <span v-if="row.defaultType === 'auto'">AI</span>
            </template>
          </el-table-column>
          <el-table-column
            v-if="caps?.['supportsComment']"
            prop="comment"
            :label="t('db.colComment')"
            :min-width="uiPx(120)"
            show-overflow-tooltip
          />
          <el-table-column :label="t('db.actions')" :width="uiPx(80)">
            <template #default="{ row }">
              <button v-if="caps?.['supportsModifyColumn']" class="btn btn-ghost btn-icon btn-sm" :title="t('common.edit')" @click="startEditColumn(row)"><Pencil :size="'0.875rem'" /></button>
              <button class="btn btn-ghost btn-icon btn-sm danger" :title="t('common.delete')" @click="onDropColumn(row.name)"><Trash2 :size="'0.875rem'" /></button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="section">
        <div class="section-header">
          <div class="section-title">{{ t('db.indexes') }}</div>
          <button class="btn btn-default btn-sm" @click="startAddIndex">
            <Plus :size="'0.875rem'" /> {{ t('db.addIndex') }}
          </button>
        </div>
        <el-table :data="schema?.indexes || []" border size="small" style="width:100%">
          <el-table-column prop="name" :label="t('db.idxName')" />
          <el-table-column :label="t('db.idxColumns')">
            <template #default="{ row }">
              {{ row.columns?.join(', ') }}
            </template>
          </el-table-column>
          <el-table-column :label="t('db.idxType')" :width="uiPx(100)">
            <template #default="{ row }">
              <span v-if="row.isPrimary" class="idx-type idx-type-pk">{{ t('db.primary') }}</span>
              <span v-else-if="row.unique" class="idx-type idx-type-uq">{{ t('db.unique') }}</span>
              <span v-else class="idx-type idx-type-idx">{{ t('db.index') }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('db.actions')" :width="uiPx(80)">
            <template #default="{ row }">
              <button class="btn btn-ghost btn-icon btn-sm danger" :title="t('common.delete')" @click="onDropIndex(row)"><Trash2 :size="'0.875rem'" /></button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog append-to-body v-model="editDialogVisible" :title="t('db.editColumn')" width="28.125rem">
        <el-form v-if="editingColumn" label-width="6.25rem">
          <el-form-item :label="t('db.colName')">
            <el-input v-model="editingColumn.name" disabled />
          </el-form-item>
          <el-form-item :label="t('db.colType')">
            <el-autocomplete
              v-model="editColumnType"
              :fetch-suggestions="filterTypeSuggestions"
              :placeholder="'INT, VARCHAR(255)...'"
              style="width:100%"
            />
          </el-form-item>
          <el-form-item :label="t('db.colDefault')">
            <div class="default-toggle-group">
              <button type="button" :class="['toggle-btn', { active: editDefaultType === 'none' }]" @click="editDefaultType = 'none'">{{ t('db.defaultNone') }}</button>
              <button type="button" :class="['toggle-btn', { active: editDefaultType === 'null' }]" @click="editDefaultType = 'null'">{{ t('db.defaultNull') }}</button>
              <button type="button" v-if="caps?.['supportsAutoIncrement']" :class="['toggle-btn', { active: editDefaultType === 'auto' }]" :disabled="hasAutoIncrementCol && editingColumn?.defaultType !== 'auto'" @click="editDefaultType = 'auto'">{{ t('db.defaultAuto') }}</button>
              <button type="button" :class="['toggle-btn', { active: editDefaultType === 'value' }]" @click="editDefaultType = 'value'">{{ t('db.defaultValue') }}</button>
            </div>
          </el-form-item>
          <el-form-item v-if="editDefaultType === 'value'" :label="t('db.colDefaultValue')">
            <el-input v-model="editColumnDefault" />
          </el-form-item>
          <el-form-item :label="t('db.colNullable')">
            <el-switch v-model="editColumnNullable" :disabled="editDefaultType === 'auto' && caps?.['autoIncrementForcesNotNull']" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsOnUpdate']" :label="t('db.colOnUpdate')">
            <el-switch v-model="editColumnOnUpdate" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsComment']" :label="t('db.colComment')">
            <el-input v-model="editColumnComment" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsCollation']" :label="t('db.colCollation')">
            <el-autocomplete
              v-model="editColumnCollation"
              :fetch-suggestions="filterCollationSuggestions"
              placeholder="utf8mb4_general_ci"
              style="width:100%"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="onSaveColumnEdit">{{ t('common.save') }}</el-button>
        </template>
      </el-dialog>

      <el-dialog append-to-body v-model="addColVisible" :title="t('db.addColumn')" width="28.125rem">
        <el-form label-width="6.25rem">
          <el-form-item :label="t('db.colName')">
            <el-input v-model="addColName" />
          </el-form-item>
          <el-form-item :label="t('db.colType')">
            <el-autocomplete
              v-model="addColType"
              :fetch-suggestions="filterTypeSuggestions"
              placeholder="INT, VARCHAR(255)..."
              style="width:100%"
            />
          </el-form-item>
          <el-form-item :label="t('db.colDefault')">
            <div class="default-toggle-group">
              <button type="button" :class="['toggle-btn', { active: addDefaultType === 'none' }]" @click="addDefaultType = 'none'">{{ t('db.defaultNone') }}</button>
              <button type="button" :class="['toggle-btn', { active: addDefaultType === 'null' }]" @click="addDefaultType = 'null'">{{ t('db.defaultNull') }}</button>
              <button type="button" v-if="caps?.['supportsAutoIncrement']" :class="['toggle-btn', { active: addDefaultType === 'auto' }]" :disabled="hasAutoIncrementCol" @click="addDefaultType = 'auto'">{{ t('db.defaultAuto') }}</button>
              <button type="button" :class="['toggle-btn', { active: addDefaultType === 'value' }]" @click="addDefaultType = 'value'">{{ t('db.defaultValue') }}</button>
            </div>
          </el-form-item>
          <el-form-item v-if="addDefaultType === 'value'" :label="t('db.colDefaultValue')">
            <el-input v-model="addColDefault" />
          </el-form-item>
          <el-form-item :label="t('db.colNullable')">
            <el-switch v-model="addColNullable" :disabled="addDefaultType === 'auto' && caps?.['autoIncrementForcesNotNull']" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsOnUpdate']" :label="t('db.colOnUpdate')">
            <el-switch v-model="addColOnUpdate" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsComment']" :label="t('db.colComment')">
            <el-input v-model="addColComment" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsCollation']" :label="t('db.colCollation')">
            <el-autocomplete
              v-model="addColCollation"
              :fetch-suggestions="filterCollationSuggestions"
              placeholder="utf8mb4_general_ci"
              style="width:100%"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="addColVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="onAddColumn">{{ t('common.save') }}</el-button>
        </template>
      </el-dialog>

      <el-dialog append-to-body v-model="addIdxVisible" :title="t('db.addIndex')" width="25rem">
        <el-form label-width="6.25rem">
          <el-form-item :label="t('db.idxName')">
            <el-input v-model="addIdxName" />
          </el-form-item>
          <el-form-item :label="t('db.idxColumns')">
            <el-select
              v-model="addIdxColumns"
              multiple
              style="width:100%"
              :placeholder="t('db.idxColumns')"
            >
              <el-option
                v-for="col in (schema?.columns || [])"
                :key="col.name"
                :label="col.name"
                :value="col.name"
              />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('db.idxUnique')">
            <el-switch v-model="addIdxUnique" :disabled="addIdxPrimary" />
          </el-form-item>
          <el-form-item v-if="caps?.['supportsPrimaryKey']" :label="t('db.idxPrimary')">
            <el-switch v-model="addIdxPrimary" :disabled="hasPrimaryKey" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="addIdxVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="onAddIndex">{{ t('common.save') }}</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Pencil, Trash2, Plus } from '@lucide/vue'
import { ElMessageBox } from 'element-plus'
import { msg } from '../services/message'
import { useI18n } from '../i18n'
import { GetTableSchema, AddColumn, ModifyColumn, DropColumn, AddIndex, DropIndexOp, GetDBCapabilities } from '../../bindings/easyaiot/terminal/app'
import type { SchemaResult, ColumnInfo, IndexInfo } from '../types/database'
import { uiPx } from '../utils/uiScale'

const { t } = useI18n()

const props = defineProps<{
  sessionId: string
  tableName: string
  dbName: string
  loadTrigger: number
}>()

const emit = defineEmits<{
  refresh: []
  schemaLoaded: [pks: string[]]
}>()

const caps = ref<Record<string, any> | null>(null)

const schema = ref<SchemaResult | null>(null)
const loading = ref(false)
let cancelled = false

const editDialogVisible = ref(false)
const editingColumn = ref<ColumnInfo | null>(null)
const editColumnType = ref('')
const editColumnNullable = ref(false)
const editColumnDefault = ref('')
const editDefaultType = ref('none')
const editColumnComment = ref('')
const editColumnCollation = ref('')
const editColumnOnUpdate = ref(false)

async function loadSchema() {
  if (!props.tableName) return
  loading.value = true
  cancelled = false
  try {
    const result = await GetTableSchema(props.sessionId, props.dbName, props.tableName)
    if (!cancelled) {
      schema.value = result
      const pks = result.columns.filter(c => c.isPrimary).map(c => c.name)
      emit('schemaLoaded', pks)
    }
  } catch (e) {
    if (!cancelled) {
      console.error('Failed to load schema:', e)
      msg.error((e as any)?.message || String(e))
    }
  } finally {
    loading.value = false
  }
}

function onCancelLoad() {
  cancelled = true
  loading.value = false
}

function startEditColumn(col: ColumnInfo) {
  editingColumn.value = col
  editColumnType.value = col.type
  editColumnNullable.value = col.nullable
  editColumnDefault.value = col.defaultVal
  editDefaultType.value = col.defaultType || 'none'
  editColumnComment.value = col.comment
  editColumnCollation.value = col.collation
  editColumnOnUpdate.value = col.onUpdate
  editDialogVisible.value = true
}

async function onSaveColumnEdit() {
  if (!editingColumn.value) return
  if (editDefaultType.value === 'auto') {
    const upperType = (editColumnType.value || '').toUpperCase().trim()
    if (!((caps.value?.['intTypes'] as string[]) || []).some(t => upperType.startsWith(t))) {
      msg.warning(t('db.autoIncrementTypeWarn'))
      return
    }
  }
  try {
    await ModifyColumn(props.sessionId, props.dbName, props.tableName, {
      name: editingColumn.value.name,
      type: editColumnType.value,
      nullable: editColumnNullable.value,
      defaultVal: editColumnDefault.value,
      defaultType: editDefaultType.value,
      comment: editColumnComment.value,
      collation: editColumnCollation.value,
      onUpdate: editColumnOnUpdate.value,
    })
    editDialogVisible.value = false
    await loadSchema()
    emit('refresh')
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function onDropColumn(colName: string) {
  try {
    await ElMessageBox.confirm(t('db.dropColumnConfirm', { name: colName }), t('common.confirm'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await DropColumn(props.sessionId, props.dbName, props.tableName, colName)
    await loadSchema()
    emit('refresh')
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function onDropIndex(idx: IndexInfo) {
  try {
    await ElMessageBox.confirm(t('db.dropIndexConfirm', { name: idx.name }), t('common.confirm'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
  } catch {
    return
  }

  const autoIncCols = idx.isPrimary
    ? (schema.value?.columns || []).filter(c => idx.columns.includes(c.name) && c.defaultType === 'auto').map(c => c.name)
    : []

  try {
    await DropIndexOp(props.sessionId, props.dbName, props.tableName, idx.name, idx.isPrimary, autoIncCols)
    await loadSchema()
    emit('refresh')
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

// ── Add column ──

const addColVisible = ref(false)
const addColName = ref('')
const addColType = ref('')
const addColNullable = ref(true)
const addColDefault = ref('')
const addDefaultType = ref('none')
const addColComment = ref('')
const addColCollation = ref('')
const addColOnUpdate = ref(false)

function startAddColumn() {
  addColName.value = ''
  addColType.value = ''
  addColNullable.value = true
  addColDefault.value = ''
  addDefaultType.value = 'none'
  addColComment.value = ''
  addColCollation.value = ''
  addColOnUpdate.value = false
  addColVisible.value = true
}

async function onAddColumn() {
  if (!addColName.value.trim()) return
  if (addDefaultType.value === 'auto') {
    const upperType = (addColType.value || '').toUpperCase().trim()
    if (!((caps.value?.['intTypes'] as string[]) || []).some(t => upperType.startsWith(t))) {
      msg.warning(t('db.autoIncrementTypeWarn'))
      return
    }
  }
  try {
    await AddColumn(props.sessionId, props.dbName, props.tableName, {
      name: addColName.value.trim(),
      type: addColType.value || 'VARCHAR(255)',
      nullable: addColNullable.value,
      defaultVal: addColDefault.value,
      defaultType: addDefaultType.value,
      comment: addColComment.value,
      collation: addColCollation.value,
      onUpdate: addColOnUpdate.value,
    })
    addColVisible.value = false
    await loadSchema()
    emit('refresh')
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

// ── Add index ──

const addIdxVisible = ref(false)
const addIdxName = ref('')
const addIdxColumns = ref<string[]>([])
const addIdxUnique = ref(false)
const addIdxPrimary = ref(false)
const hasPrimaryKey = computed(() =>
  schema.value?.indexes?.some(i => i.isPrimary) ?? false
)

const hasAutoIncrementCol = computed(() =>
  schema.value?.columns?.some(c => c.defaultType === 'auto') ?? false
)

async function loadCapabilities() {
  try {
    caps.value = await GetDBCapabilities(props.sessionId)
  } catch (e) {
    console.error('Failed to load capabilities:', e)
  }
}

watch(() => props.loadTrigger, async () => {
  if (!props.tableName || props.loadTrigger === 0) return
  await loadSchema()
  if (!caps.value) await loadCapabilities()
}, { immediate: true })

watch(addDefaultType, (val) => {
  if (val === 'auto') addColNullable.value = false
})
watch(editDefaultType, (val) => {
  if (val === 'auto') editColumnNullable.value = false
})

function filterTypeSuggestions(queryString: string, cb: Function) {
  const list = (caps.value?.['columnTypes'] as string[]) || []
  const results = queryString
    ? list.filter(t => t.toLowerCase().includes(queryString.toLowerCase())).map(t => ({ value: t }))
    : list.map(t => ({ value: t }))
  cb(results)
}

const COLLATIONS = [
  'utf8mb4_general_ci', 'utf8mb4_unicode_ci', 'utf8mb4_bin',
  'utf8_general_ci', 'utf8_unicode_ci', 'utf8_bin',
  'latin1_general_ci', 'latin1_swedish_ci',
  'gbk_chinese_ci', 'gb2312_chinese_ci',
]

function filterCollationSuggestions(queryString: string, cb: Function) {
  const results = queryString
    ? COLLATIONS.filter(t => t.toLowerCase().includes(queryString.toLowerCase())).map(t => ({ value: t }))
    : COLLATIONS.map(t => ({ value: t }))
  cb(results)
}

function startAddIndex() {
  addIdxName.value = ''
  addIdxColumns.value = []
  addIdxUnique.value = false
  addIdxPrimary.value = false
  addIdxVisible.value = true
}

async function onAddIndex() {
  if (addIdxPrimary.value) {
    if (addIdxColumns.value.length === 0) return

    const nullableCols = (schema.value?.columns || [])
      .filter(c => addIdxColumns.value.includes(c.name) && c.nullable)
    if (nullableCols.length > 0) {
      try {
        await ElMessageBox.confirm(
          t('db.addPkNullableWarn', { columns: nullableCols.map(c => c.name).join(', ') }),
          t('common.confirm'),
          { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
        )
      } catch {
        return
      }
    }

    try {
      await AddIndex(props.sessionId, props.dbName, props.tableName, {
        name: '',
        columns: addIdxColumns.value,
        unique: false,
        isPrimary: true,
      })
      addIdxVisible.value = false
      await loadSchema()
      emit('refresh')
    } catch (e: any) {
      msg.error(e?.message || String(e))
    }
    return
  }
  if (!addIdxName.value.trim() || addIdxColumns.value.length === 0) return
  try {
    await AddIndex(props.sessionId, props.dbName, props.tableName, {
      name: addIdxName.value.trim(),
      columns: addIdxColumns.value,
      unique: addIdxUnique.value,
      isPrimary: false,
    })
    addIdxVisible.value = false
    await loadSchema()
    emit('refresh')
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}
</script>

<style scoped>
.db-table-structure {
  height: 100%;
  overflow: auto;
  padding: 0.5rem;
  position: relative;
}
.placeholder {
  font-family: var(--font-ui);
  color: var(--text-secondary);
  text-align: center;
  padding: 2.5rem 0;
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
.section {
  margin-bottom: 1rem;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.section-header .btn { margin-left: auto; }
.section-title {
  font-family: var(--font-ui);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}
.default-toggle-group {
  display: flex;
  gap: 0;
}
.toggle-btn {
  padding: 0.3125rem 0.875rem;
  border: 1px solid var(--border-subtle);
  background: var(--bg-base);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
}
.toggle-btn:first-child {
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
}
.toggle-btn:last-child {
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.toggle-btn + .toggle-btn {
  border-left: none;
}
.toggle-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.toggle-btn.active {
  background: var(--accent);
  color: var(--on-accent);
  border-color: var(--accent);
}
.toggle-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.exec-btn { margin-top: 0.25rem; }
.idx-type {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 1px 0.375rem;
  border-radius: var(--radius-sm);
}
.idx-type-pk { color: var(--accent); }
.idx-type-uq { color: var(--info); }
.idx-type-idx { color: var(--text-secondary); }
</style>

<style>
.el-autocomplete__popper {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-sm) !important;
}
.el-autocomplete-suggestion {
  background: var(--bg-elevated);
}
.el-autocomplete-suggestion__list {
  padding: 0.25rem 0;
}
.el-autocomplete-suggestion__item {
  color: var(--text-primary);
  padding: 0.25rem 0.75rem;
  font-size: 0.8125rem;
}
.el-autocomplete-suggestion__item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.el-autocomplete-suggestion__item.highlighted {
  background: var(--bg-hover);
}
</style>
