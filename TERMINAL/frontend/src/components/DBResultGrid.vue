<template>
  <div class="db-result-grid" tabindex="0">
    <el-table
      :key="tableKey"
      ref="tableRef"
      :data="rows"
      border
      size="small"
      height="100%"
      style="width: 100%"
      class="db-result-table"
      :empty-text="emptyText"
      @sort-change="onSortChange"
      @cell-dblclick="onCellDblClick"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.name"
        :prop="col.name"
        :label="colTitle(col)"
        :min-width="uiPx(110)"
        sortable="custom"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <div
            v-if="canEdit && editingRow === row && editingField === col.name"
            class="cell-edit-wrap"
            @mousedown.stop
          >
            <input
              ref="cellInputEl"
              v-model="draftValue"
              class="cell-edit-input"
              :placeholder="isNullable(col.name) ? t('db.null') : ''"
              @input="onDraftInput"
              @keydown.enter.prevent="onCellEditConfirm"
              @keydown.escape.prevent="onCellEditCancel"
              @blur="onCellEditConfirm"
            />
            <button
              v-if="isNullable(col.name)"
              type="button"
              class="null-btn"
              title="N"
              @mousedown.prevent
              @click.prevent="setDraftNull"
            >
              N
            </button>
          </div>
          <span
            v-else-if="row[col.name] === null"
            class="cell-null"
            :class="{ 'cell-pending': isPending(row, col.name) }"
          >{{ t('db.null') }}</span>
          <span
            v-else
            class="cell-value"
            :class="{ 'cell-pending': isPending(row, col.name) }"
          >{{ formatCell(row[col.name]) }}</span>
        </template>
      </el-table-column>

      <el-table-column
        v-if="canEdit"
        :label="actionsLabel"
        :width="uiPx(88)"
        fixed="right"
        class-name="db-action-cell"
        :resizable="false"
      >
        <template #default="{ row }">
          <div class="row-actions" @mousedown.stop @click.stop>
            <button
              type="button"
              class="btn btn-ghost btn-icon btn-sm"
              :title="editLabel"
              @click.stop.prevent="emit('edit-row', row)"
            >
              <Pencil :size="'0.875rem'" />
            </button>
            <button
              type="button"
              class="btn btn-ghost btn-icon btn-sm danger"
              :title="deleteLabel"
              @click.stop.prevent="emit('delete-row', row)"
            >
              <Trash2 :size="'0.875rem'" />
            </button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { Pencil, Trash2 } from '@lucide/vue'
import type { QueryResultColumn, ColumnInfo } from '../types/database'
import { useI18n } from '../i18n'
import { uiPx } from '../utils/uiScale'

const { t } = useI18n()

const props = defineProps<{
  rows: Record<string, any>[]
  columns: QueryResultColumn[]
  canEdit: boolean
  primaryKeys?: string[]
  tableColumns?: ColumnInfo[]
  emptyText?: string
  actionsLabel?: string
  editLabel?: string
  deleteLabel?: string
}>()

const emit = defineEmits<{
  /** A staged, unsaved cell edit changed; payload = number of pending edits. */
  'pending-change': [count: number]
  'edit-row': [row: Record<string, any>]
  'delete-row': [row: Record<string, any>]
  'sort-change': [payload: { field: string; order: 'asc' | 'desc' | null }]
}>()

const tableRef = ref<any>(null)
const cellInputEl = ref<HTMLInputElement | null>(null)

const tableKey = computed(() => `edit-${props.canEdit ? 1 : 0}-cols-${props.columns.map(c => c.name).join('|')}`)

/** Currently edited cell (row + column name). */
const editingRow = ref<Record<string, any> | null>(null)
const editingField = ref<string | null>(null)
const draftValue = ref('')
const draftIsNull = ref(false)
let snapOldValue: any = undefined

interface StagedCell { old: any; newVal: any }
interface StagedRow { pk: Record<string, any>; fields: Map<string, StagedCell> }

/** Unsaved edits, keyed by the row object they belong to. Reactive for cell highlight. */
const pending = reactive(new Map<Record<string, any>, StagedRow>())

function changedCellCount() {
  let n = 0
  for (const rec of pending.values()) n += rec.fields.size
  return n
}
function bumpPending() {
  emit('pending-change', changedCellCount())
}

function findMeta(colName: string) {
  const lower = colName.toLowerCase()
  return props.tableColumns?.find(c => c.name === colName || c.name.toLowerCase() === lower)
}
function colTitle(col: QueryResultColumn) {
  const meta = findMeta(col.name)
  if (meta?.isPrimary) return `${col.name} 🔑`
  return col.name
}
function isNullable(colName: string) {
  return findMeta(colName)?.nullable ?? true
}
function formatCell(v: any) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'object') {
    try { return JSON.stringify(v) } catch { return String(v) }
  }
  return String(v)
}
function valuesEqual(a: any, b: any) {
  if (a === b) return true
  if (a === null || b === null || a === undefined || b === undefined) return false
  return String(a) === String(b)
}
function snapshotPk(row: Record<string, any>) {
  const pk: Record<string, any> = {}
  for (const k of props.primaryKeys || []) pk[k] = row[k] ?? null
  return pk
}
function isPending(row: Record<string, any>, field: string) {
  return pending.get(row)?.fields.has(field) ?? false
}

function startEdit(row: Record<string, any>, field: string) {
  if (editingRow.value === row && editingField.value === field) return
  if (editingRow.value) onCellEditConfirm() // stage pending edit first
  editingRow.value = row
  editingField.value = field
  draftIsNull.value = row[field] === null
  draftValue.value = row[field] === null || row[field] === undefined ? '' : String(row[field])
  snapOldValue = row[field]
  document.addEventListener('mousedown', onEditOutsideMousedown)
  document.addEventListener('keydown', onEditKeydown)
  nextTick(() => {
    cellInputEl.value?.focus()
    cellInputEl.value?.select()
  })
}

// Dismissal must not depend on the input's focus/blur: focus via the el-table
// slot ref is fragile, so listen globally while editing instead.
function onEditOutsideMousedown(e: MouseEvent) {
  const target = e.target as HTMLElement | null
  if (target?.closest('.cell-edit-wrap')) return
  onCellEditConfirm()
}
function onEditKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') onCellEditCancel()
}
function onEditDismissCleanup() {
  document.removeEventListener('mousedown', onEditOutsideMousedown)
  document.removeEventListener('keydown', onEditKeydown)
}

// el-table's @cell-dblclick passes positional args (row, column, cell, event)
function onCellDblClick(row: Record<string, any>, column?: { property?: string }) {
  if (!props.canEdit) return
  const field = column?.property
  if (!field) return
  if (!props.columns.some(c => c.name === field)) return
  startEdit(row, field)
}

function onDraftInput() {
  draftIsNull.value = false
}
function setDraftNull() {
  draftIsNull.value = true
  draftValue.value = ''
}

function onCellEditConfirm() {
  const row = editingRow.value
  const field = editingField.value
  if (!row || !field) return
  editingRow.value = null
  editingField.value = null
  onEditDismissCleanup()
  const newVal: any = draftIsNull.value ? null : draftValue.value
  const oldVal = snapOldValue
  snapOldValue = undefined
  draftIsNull.value = false
  if (valuesEqual(oldVal, newVal)) {
    row[field] = oldVal
    return
  }
  // Stage instead of saving: reflect the change live, mark dirty, wait for explicit save.
  row[field] = newVal
  let rec = pending.get(row)
  if (!rec) {
    rec = { pk: snapshotPk(row), fields: new Map() }
    pending.set(row, rec)
  }
  const existing = rec.fields.get(field)
  const original = existing ? existing.old : oldVal
  if (valuesEqual(original, newVal)) {
    // Edited back to the committed value — drop the staged edit for this field.
    rec.fields.delete(field)
    if (rec.fields.size === 0) pending.delete(row)
    bumpPending()
    return
  }
  rec.fields.set(field, { old: original, newVal })
  bumpPending()
}

function onCellEditCancel() {
  const row = editingRow.value
  const field = editingField.value
  if (row && field) {
    const rec = pending.get(row)
    const staged = rec?.fields.get(field)
    row[field] = staged ? staged.newVal : snapOldValue
  }
  editingRow.value = null
  editingField.value = null
  onEditDismissCleanup()
  snapOldValue = undefined
  draftIsNull.value = false
}

function onSortChange({ prop, order }: { prop?: string; order?: string | null }) {
  const field = prop || ''
  const ord: 'asc' | 'desc' | null =
    order === 'ascending' || order === 'asc' ? 'asc'
      : order === 'descending' || order === 'desc' ? 'desc'
        : null
  emit('sort-change', { field, order: ord })
}

/** Discard all staged edits for a row and restore its committed values. */
function revertRow(row: Record<string, any>) {
  const rec = pending.get(row)
  if (!rec) return
  for (const [field, cell] of rec.fields) row[field] = cell.old
  pending.delete(row)
  bumpPending()
}
/** Discard every staged edit. */
function revertAll() {
  for (const [row, rec] of pending) {
    for (const [field, cell] of rec.fields) row[field] = cell.old
  }
  pending.clear()
  bumpPending()
}
/** Mark a staged edit as persisted (after a successful save). */
function markCommitted(row: Record<string, any>, field: string) {
  const rec = pending.get(row)
  if (!rec) return
  rec.fields.delete(field)
  if (rec.fields.size === 0) pending.delete(row)
  bumpPending()
}

/** Snapshot of all currently staged edits, ready for DBUpdateRow calls. */
function getPendingEdits(): Array<{
  row: Record<string, any>
  field: string
  newValue: any
  oldValue: any
  where: Record<string, any>
}> {
  const out: ReturnType<typeof getPendingEdits> = []
  for (const [row, rec] of pending) {
    for (const [field, cell] of rec.fields) {
      out.push({ row, field, newValue: cell.newVal, oldValue: cell.old, where: { ...rec.pk } })
    }
  }
  return out
}

function clearEdit() {
  onCellEditConfirm()
}

onBeforeUnmount(onEditDismissCleanup)

watch(() => props.rows, () => {
  if (pending.size) {
    pending.clear()
    bumpPending()
  }
})

defineExpose({
  getPendingEdits,
  revertRow,
  revertAll,
  markCommitted,
  clearEdit,
  getSelectedRows: () => [],
})
</script>

<style scoped>
.db-result-grid {
  flex: 1;
  min-height: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
  outline: none;
}
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
.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
}
.row-actions :deep(svg) { pointer-events: none; }
.cell-null {
  color: var(--text-muted);
  font-style: italic;
}
.cell-value {
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
}
.cell-pending {
  background-color: var(--accent-subtle, rgba(64, 128, 255, 0.12));
  box-shadow: inset 0 -0.125rem 0 var(--accent);
}
.cell-edit-wrap {
  display: flex;
  align-items: stretch;
  width: 100%;
  gap: 0.125rem;
}
.cell-edit-input {
  flex: 1;
  min-width: 0;
  height: 1.5rem;
  padding: 0 0.375rem;
  border: 1px solid var(--accent);
  border-radius: 0.125rem;
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  outline: none;
}
.null-btn {
  flex-shrink: 0;
  width: 1.375rem;
  border: 1px solid var(--border-subtle);
  border-radius: 0.125rem;
  background: var(--bg-elevated, var(--bg-hover));
  color: var(--text-muted);
  font-size: 0.625rem;
  font-weight: 700;
  cursor: pointer;
  font-style: italic;
}
.null-btn:hover {
  color: var(--text-primary);
  border-color: var(--accent);
}
</style>