<template>
  <div class="transform-card-list-wrapper">
    <div class="list-panel">
      <Spin :spinning="loading">
        <List
          :grid="{ gutter: 18, xs: 2, sm: 3, md: 4, lg: 5, xl: 6, xxl: 6 }"
          :data-source="pageData"
          :pagination="paginationProp"
        >
          <template #header>
            <div class="list-header">
              <span class="list-title">{{ title }}</span>
              <div class="list-actions">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="transform-list-item">
              <div
                class="transform-card"
                @mouseenter="hoverId = item[rowKey]"
                @mouseleave="hoverId = null"
              >
                <div class="transform-card-cover">
                  <div
                    class="cover-solid"
                    :style="{ backgroundColor: cover.color }"
                  >
                    <span class="cover-label">{{ cover.label }}</span>
                  </div>
                  <div
                    v-show="hoverId === item[rowKey]"
                    class="transform-card-overlay"
                  >
                    <div class="overlay-actions" @click.stop>
                      <slot name="actions" :record="item"></slot>
                    </div>
                  </div>
                </div>

                <div class="transform-card-badge">
                  <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="18" stroke="#266CFB" stroke-width="1.5" fill="#fff" />
                    <text
                      x="20"
                      y="24"
                      text-anchor="middle"
                      fill="#266CFB"
                      font-size="10"
                      font-weight="700"
                    >
                      {{ badge }}
                    </text>
                  </svg>
                </div>

                <div class="transform-card-body">
                  <h3 class="transform-card-title" :title="resolveTitle(item)">
                    {{ resolveTitle(item) }}
                  </h3>
                  <p class="transform-card-tags" :title="getTagsText(item)">
                    {{ getTagsText(item) }}
                  </p>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
        <div v-if="!loading && allData.length === 0" class="empty-tip">暂无数据</div>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { List, Spin } from 'ant-design-vue'
import { isFunction } from '@/utils/is'

defineOptions({ name: 'TransformCardList' })

export interface CardField {
  key: string
  label: string
  render?: (record: Recordable) => string
}

export interface CoverConfig {
  color: string
  label: string
}

const props = withDefaults(
  defineProps<{
    title: string
    api: Function
    fields: CardField[]
    cover?: CoverConfig
    badge?: string
    rowKey?: string
    titleKey?: string
    statusKey?: string
  }>(),
  {
    cover: () => ({ color: '#5B8FF9', label: 'TRANSFORM' }),
    badge: 'TF',
    rowKey: 'id',
    titleKey: 'name',
    statusKey: '',
  },
)

const emit = defineEmits<{
  (e: 'getMethod', reload: (opts?: { resetPage?: boolean }) => Promise<void>): void
}>()

const ListItem = List.Item
const allData = ref<Recordable[]>([])
const loading = ref(false)
const hoverId = ref<string | number | null>(null)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)

const pageData = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return allData.value.slice(start, start + pageSize.value)
})

const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (t: number) => `总 ${t} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
})

function pageChange(p: number, pz: number) {
  page.value = p
  pageSize.value = pz
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size
  page.value = 1
}

function resolveTitle(item: Recordable) {
  return item[props.titleKey] || item.id || item.instanceId || '—'
}

function resolveField(item: Recordable, field: CardField) {
  if (field.render) return field.render(item) || ''
  const value = item[field.key]
  if (value === null || value === undefined || value === '') return ''
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function statusText(item: Recordable) {
  if (!props.statusKey) return ''
  if (props.statusKey === 'online') return item.online ? '在线' : '离线'
  if (props.statusKey === 'status') {
    const map: Recordable = {
      PENDING: '待推送',
      RELAYING: '推送中',
      SENT: '已发出',
      FAILED: '失败',
      DELIVERED: '已送达',
      DEAD: '已放弃',
    }
    return (item.status && map[item.status]) || item.status || ''
  }
  if (props.statusKey === 'enabled' && typeof item.enabled === 'boolean') {
    return item.enabled ? '启用' : '停用'
  }
  return ''
}

function getTagsText(item: Recordable) {
  const parts: string[] = []
  const status = statusText(item)
  if (status) parts.push(status)
  for (const field of props.fields) {
    const value = resolveField(item, field)
    if (value && value !== '—') parts.push(value)
  }
  if (!parts.length) parts.push(`ID: ${item[props.rowKey] || '—'}`)
  return parts.join('  |  ')
}

async function fetchList() {
  if (!props.api || !isFunction(props.api)) return
  loading.value = true
  try {
    const res = await props.api()
    allData.value = Array.isArray(res) ? res : res?.data || []
    total.value = allData.value.length
    const maxPage = Math.max(1, Math.ceil(total.value / pageSize.value) || 1)
    if (page.value > maxPage) page.value = maxPage
  } catch (error) {
    console.error('卡片列表加载失败', error)
    allData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function reload(opts?: { resetPage?: boolean }) {
  if (opts?.resetPage) {
    page.value = 1
  }
  await fetchList()
}

onMounted(async () => {
  await fetchList()
  emit('getMethod', reload)
})

watch(
  () => props.api,
  () => {
    fetchList()
  },
)

defineExpose({ reload })
</script>

<style lang="less" scoped>
.transform-card-list-wrapper {
  background: #fff;
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.list-panel {
  background: #fff;
  padding: 0 8px 16px;
  flex: 1;
  min-height: 0;

  :deep(.ant-list-header) {
    border: 0;
    padding: 8px 12px 16px;
    background: transparent;
  }

  :deep(.ant-list) {
    padding: 0 8px;
  }

  :deep(.ant-row) {
    display: flex;
    flex-wrap: wrap;
    row-gap: 18px;
  }

  :deep(.ant-col) {
    display: flex;
  }

  :deep(.ant-list-item) {
    margin-bottom: 0;
    padding: 0 !important;
    border: none;
    width: 100%;
    height: 100%;
    display: flex;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    background: transparent;
  }

  :deep(.ant-list-pagination) {
    margin-top: 20px;
    text-align: center;
  }
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-title {
  padding-left: 4px;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: #181818;
}

.list-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.transform-list-item {
  width: 100%;
}

@cover-height: 200px;
@body-height: 96px;
@card-height: @cover-height + @body-height;

.transform-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: @card-height;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.1);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
  cursor: default;

  &:hover {
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-1px);
  }
}

.transform-card-cover {
  position: relative;
  width: 100%;
  height: @cover-height;
  flex-shrink: 0;
  overflow: hidden;
  background: #fafafa;
}

.cover-solid {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-label {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
  user-select: none;
}

.transform-card-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.overlay-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 0 8px;
  align-items: center;
}

.transform-card-badge {
  position: absolute;
  top: @cover-height - 20px;
  right: 14px;
  z-index: 4;
  width: 40px;
  height: 40px;
  pointer-events: none;

  svg {
    width: 40px;
    height: 40px;
    filter: drop-shadow(0 2px 6px rgba(38, 108, 251, 0.2));
  }
}

.transform-card-body {
  flex-shrink: 0;
  height: @body-height;
  padding: 24px 16px 14px;
  box-sizing: border-box;
  overflow: hidden;
}

.transform-card-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  color: #181818;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transform-card-tags {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tip {
  text-align: center;
  color: #94a3b8;
  padding: 48px 0;
}
</style>
