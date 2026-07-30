<template>
  <div class="mapping-editor" :class="{ 'mapping-editor--disabled': disabled }">
    <div class="mapping-editor__toolbar">
      <div>
        <div class="mapping-editor__title">字段映射</div>
        <div class="mapping-editor__subtitle">
          左侧为目标字段（对方系统），右侧为源字段（平台数据，支持 JSONPath，如
          <code>$.eventId</code>）
        </div>
      </div>
      <Button
        size="small"
        type="dashed"
        preIcon="ant-design:plus-outlined"
        :disabled="disabled"
        @click="addRow"
      >
        添加映射
      </Button>
    </div>

    <div class="mapping-editor__head">
      <span class="col-target">目标字段</span>
      <span class="col-arrow" />
      <span class="col-source">源字段 / JSONPath</span>
      <span class="col-action" />
    </div>

    <div v-if="!rows.length" class="mapping-editor__empty">
      暂无映射。可点击下方快捷填充，或手动添加：
      <code>orderId ← $.eventId</code>
    </div>

    <div v-for="(row, index) in rows" :key="row._key" class="mapping-editor__row">
      <Input
        v-model:value="row.target"
        placeholder="如 orderId"
        class="col-target"
        :disabled="disabled"
        @change="emitChange"
      />
      <span class="col-arrow">←</span>
      <Input
        v-model:value="row.source"
        placeholder="如 $.payload.temperature"
        class="col-source"
        :disabled="disabled"
        @change="emitChange"
      />
      <Button
        type="text"
        danger
        class="col-action"
        preIcon="ant-design:delete-outlined"
        :disabled="disabled"
        @click="() => removeRow(index)"
      />
    </div>

    <div v-if="!disabled" class="mapping-editor__presets">
      <span class="presets-label">快捷填充：</span>
      <a v-for="p in presets" :key="p.target" @click="applyPreset(p)">
        {{ p.target }} ← {{ p.source }}
      </a>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { Input } from 'ant-design-vue'
import { Button } from '@/components/Button'

defineOptions({ name: 'TransformFieldMappingEditor' })

const props = withDefaults(
  defineProps<{
    value?: Record<string, string>
    disabled?: boolean
  }>(),
  { value: () => ({}), disabled: false },
)

const emit = defineEmits<{
  (e: 'update:value', value: Record<string, string>): void
}>()

type Row = { _key: string; target: string; source: string }
const rows = ref<Row[]>([])
let syncing = false

const presets = [
  { target: 'eventId', source: '$.eventId' },
  { target: 'deviceId', source: '$.deviceId' },
  { target: 'flowType', source: '$.flowType' },
  { target: 'payload', source: '$.payload' },
  { target: 'timestamp', source: '$.ts' },
]

function toRows(map: Record<string, string>): Row[] {
  return Object.entries(map || {}).map(([target, source], i) => ({
    _key: `m-${i}-${target}`,
    target,
    source: source ?? '',
  }))
}

function toMap(list: Row[]): Record<string, string> {
  const result: Record<string, string> = {}
  for (const row of list) {
    const target = row.target?.trim()
    if (!target) continue
    result[target] = row.source?.trim() || ''
  }
  return result
}

function emitChange() {
  emit('update:value', toMap(rows.value))
}

function addRow() {
  if (props.disabled) return
  rows.value.push({ _key: `n-${Date.now()}-${Math.random()}`, target: '', source: '' })
}

function removeRow(index: number) {
  if (props.disabled) return
  rows.value.splice(index, 1)
  emitChange()
}

function applyPreset(p: { target: string; source: string }) {
  if (props.disabled) return
  const exists = rows.value.some((r) => r.target === p.target)
  if (!exists) {
    rows.value.push({
      _key: `p-${Date.now()}-${p.target}`,
      target: p.target,
      source: p.source,
    })
    emitChange()
  }
}

watch(
  () => props.value,
  (val) => {
    if (syncing) return
    const next = toRows(val || {})
    const current = toMap(rows.value)
    const keys = Object.keys(val || {})
    const same =
      keys.length === Object.keys(current).length &&
      keys.every((k) => (val || {})[k] === current[k])
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
.mapping-editor {
  width: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
  padding: 16px;

  &--disabled {
    opacity: 0.9;
  }
}

.mapping-editor__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
}

.mapping-editor__title {
  font-size: 14px;
  font-weight: 600;
  color: #181818;
}

.mapping-editor__subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;

  code {
    padding: 0 4px;
    background: #fff;
    border-radius: 3px;
    font-size: 12px;
  }
}

.mapping-editor__head,
.mapping-editor__row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.mapping-editor__head {
  padding: 0 4px 6px;
  font-size: 12px;
  color: #999;
  border-bottom: 1px dashed #e8e8e8;
  margin-bottom: 10px;
}

.col-target {
  width: 240px;
  flex-shrink: 0;
}

.col-arrow {
  width: 28px;
  text-align: center;
  color: #266cfb;
  font-weight: 600;
  flex-shrink: 0;
}

.col-source {
  flex: 1;
}

.col-action {
  width: 36px;
  flex-shrink: 0;
}

.mapping-editor__empty {
  padding: 24px 8px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;

  code {
    font-size: 12px;
  }
}

.mapping-editor__presets {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e8e8e8;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  align-items: center;
  font-size: 13px;

  .presets-label {
    color: #999;
  }

  a {
    color: #266cfb;
    cursor: pointer;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
