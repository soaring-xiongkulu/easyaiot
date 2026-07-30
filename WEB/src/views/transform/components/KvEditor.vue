<template>
  <div class="kv-editor" :class="{ 'kv-editor--disabled': disabled }">
    <div class="kv-editor__toolbar">
      <span class="kv-editor__hint">{{ hint }}</span>
      <Button
        size="small"
        type="dashed"
        preIcon="ant-design:plus-outlined"
        :disabled="disabled"
        @click="addRow"
      >
        添加
      </Button>
    </div>
    <div v-if="!rows.length" class="kv-editor__empty">暂无配置项，点击「添加」开始配置</div>
    <div v-for="(row, index) in rows" :key="row._key" class="kv-editor__row">
      <Input
        v-model:value="row.key"
        :placeholder="keyPlaceholder"
        class="kv-editor__key"
        :disabled="disabled"
        @change="emitChange"
      />
      <Input
        v-model:value="row.value"
        :placeholder="valuePlaceholder"
        class="kv-editor__value"
        :disabled="disabled"
        @change="emitChange"
      />
      <Button
        type="text"
        danger
        class="kv-editor__del"
        preIcon="ant-design:delete-outlined"
        :disabled="disabled"
        @click="() => removeRow(index)"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { Input } from 'ant-design-vue'
import { Button } from '@/components/Button'

defineOptions({ name: 'TransformKvEditor' })

const props = withDefaults(
  defineProps<{
    value?: Recordable
    hint?: string
    keyPlaceholder?: string
    valuePlaceholder?: string
    disabled?: boolean
  }>(),
  {
    value: () => ({}),
    hint: '键值对配置',
    keyPlaceholder: '键',
    valuePlaceholder: '值',
    disabled: false,
  },
)

const emit = defineEmits<{
  (e: 'update:value', value: Recordable): void
}>()

type Row = { _key: string; key: string; value: string }
const rows = ref<Row[]>([])
let syncing = false

function toRows(map: Recordable): Row[] {
  return Object.entries(map || {}).map(([key, value], i) => ({
    _key: `k-${i}-${key}`,
    key,
    value: value === null || value === undefined ? '' : String(value),
  }))
}

function toMap(list: Row[]): Recordable {
  const result: Recordable = {}
  for (const row of list) {
    const key = row.key?.trim()
    if (!key) continue
    result[key] = row.value
  }
  return result
}

function emitChange() {
  emit('update:value', toMap(rows.value))
}

function addRow() {
  if (props.disabled) return
  rows.value.push({ _key: `n-${Date.now()}-${Math.random()}`, key: '', value: '' })
}

function removeRow(index: number) {
  if (props.disabled) return
  rows.value.splice(index, 1)
  emitChange()
}

watch(
  () => props.value,
  (val) => {
    if (syncing) return
    const next = toRows(val || {})
    const current = toMap(rows.value)
    const same =
      Object.keys(current).length === Object.keys(val || {}).length &&
      Object.keys(val || {}).every((k) => String((val || {})[k] ?? '') === String(current[k] ?? ''))
    if (!same) rows.value = next
  },
  { immediate: true, deep: true },
)

watch(
  rows,
  () => {
    syncing = true
    emitChange()
    Promise.resolve().then(() => {
      syncing = false
    })
  },
  { deep: true },
)
</script>

<style lang="less" scoped>
.kv-editor {
  width: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
  padding: 12px;

  &--disabled {
    opacity: 0.85;
  }
}

.kv-editor__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.kv-editor__hint {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.kv-editor__empty {
  padding: 20px 0;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.kv-editor__row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.kv-editor__key {
  width: 220px;
  flex-shrink: 0;
}

.kv-editor__value {
  flex: 1;
}

.kv-editor__del {
  flex-shrink: 0;
}
</style>
