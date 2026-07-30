<template>
  <div class="panel">
    <div class="metric-strip">
      <div v-for="item in overviewCards" :key="item.key" class="metric-item">
        <div class="metric-item__icon" :style="{ background: item.bg, color: item.color }">
          <Icon :icon="item.icon" :size="16" />
        </div>
        <div class="metric-item__body">
          <span class="metric-item__label">{{ item.label }}</span>
          <span class="metric-item__value">
            <CountTo :start-val="0" :end-val="item.value" :duration="700" />
          </span>
        </div>
      </div>
    </div>

    <div class="pipeline-bar">
      <div class="pipeline-bar__left">
        <div>
          <div class="pipeline-bar__title">
            全局预处理
            <Tag :color="primaryPipeline?.enabled ? 'success' : 'default'">
              {{ primaryPipeline?.enabled ? '已开启' : '未开启' }}
            </Tag>
          </div>
          <div v-if="pipelineSummary" class="pipeline-bar__desc">{{ pipelineSummary }}</div>
        </div>
      </div>
      <div class="pipeline-bar__right">
        <Switch
          v-if="primaryPipeline"
          :checked="!!primaryPipeline.enabled"
          checked-children="开"
          un-checked-children="关"
          @change="(checked) => togglePipeline(primaryPipeline, !!checked)"
        />
        <Button size="small" @click="editOrCreatePipeline">
          {{ primaryPipeline ? '编辑预处理' : '配置预处理' }}
        </Button>
      </div>
    </div>

    <div class="panel-bar">
      <span class="panel-bar__label">状态</span>
      <RadioButtonGroup
        v-model:value="state.statusFilter"
        :options="filterOptions"
        size="small"
        button-style="solid"
      />
      <div class="panel-bar__actions">
        <Button type="primary" @click="() => openMappingDrawer(true, { isUpdate: false })">
          新增模板
        </Button>
        <Button @click="reloadAll">刷新</Button>
      </div>
    </div>

    <div class="panel-body">
      <BasicTable @register="registerMappingTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'name'">
            <div class="name-cell">
              <div class="name-main">{{ record.name }}</div>
              <div class="name-sub">{{ record.id }}</div>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'fields'">
            <div class="field-cell">
              <span class="field-num">{{ Object.keys(record.fields || {}).length }}</span>
              <span class="field-unit">字段</span>
              <div class="field-bar">
                <i :style="{ width: fieldBarWidth(record) }" />
              </div>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'enabled'">
            <Tag :color="record.enabled ? 'success' : 'default'">
              {{ record.enabled ? '可用' : '停用' }}
            </Tag>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction :actions="getMappingTableActions(record)" />
          </template>
        </template>
      </BasicTable>
    </div>

    <MappingDrawer @register="registerMappingDrawer" @success="reloadAll" />
    <PipelineDrawer @register="registerPipelineDrawer" @success="reloadAll" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Switch, Tag } from 'ant-design-vue'
import { CountTo } from '@/components/CountTo'
import { Icon } from '@/components/Icon'
import { RadioButtonGroup } from '@/components/Form'
import { BasicTable, TableAction, useTable, type ActionItem, type BasicColumn } from '@/components/Table'
import { Button } from '@/components/Button'
import { useDrawer } from '@/components/Drawer'
import { useMessage } from '@/hooks/web/useMessage'
import {
  deleteTransformMapping,
  enableTransformPipeline,
  getTransformMappingList,
  getTransformPipelineList,
} from '@/api/device/transform'
import { flowTypeLabel } from '../data'
import MappingDrawer from './MappingDrawer.vue'
import PipelineDrawer from './PipelineDrawer.vue'

defineOptions({ name: 'TransformMappingPanel' })

const { createMessage } = useMessage()
const [registerMappingDrawer, { openDrawer: openMappingDrawer }] = useDrawer()
const [registerPipelineDrawer, { openDrawer: openPipelineDrawer }] = useDrawer()

const allList = ref<Recordable[]>([])
const mappings = ref<Recordable[]>([])
const pipelines = ref<Recordable[]>([])
const state = reactive({ statusFilter: '' })

const primaryPipeline = computed(() => pipelines.value[0] || null)
const enabledCount = computed(() => allList.value.filter((i) => !!i.enabled).length)
const disabledCount = computed(() => allList.value.filter((i) => !i.enabled).length)
const fieldTotal = computed(() =>
  allList.value.reduce((sum, item) => sum + Object.keys(item.fields || {}).length, 0),
)

const pipelineSummary = computed(() => {
  const p = primaryPipeline.value
  if (!p) return ''
  const mapName = mappings.value.find((m) => m.id === p.mappingId)?.name || p.mappingId || '透传'
  return `${flowTypeLabel(p.flowType)} → ${mapName}`
})

const overviewCards = computed(() => [
  {
    key: 'total',
    label: '模板总数',
    value: allList.value.length,
    icon: 'ant-design:swap-outlined',
    bg: '#f5e8ff',
    color: '#722ed1',
  },
  {
    key: 'enabled',
    label: '可用',
    value: enabledCount.value,
    icon: 'ant-design:check-circle-outlined',
    bg: '#e8ffea',
    color: '#00b42a',
  },
  {
    key: 'fields',
    label: '映射字段',
    value: fieldTotal.value,
    icon: 'ant-design:unordered-list-outlined',
    bg: '#f0f5ff',
    color: '#266cfb',
  },
  {
    key: 'pipeline',
    label: '全局预处理',
    value: primaryPipeline.value?.enabled ? 1 : 0,
    icon: 'ant-design:filter-outlined',
    bg: primaryPipeline.value?.enabled ? '#e8ffea' : '#f2f3f5',
    color: primaryPipeline.value?.enabled ? '#00b42a' : '#86909c',
  },
])

const filterOptions = computed(() => [
  { label: `全部 (${allList.value.length})`, value: '' },
  { label: `可用 (${enabledCount.value})`, value: 'enabled' },
  { label: `停用 (${disabledCount.value})`, value: 'disabled' },
])

function fieldBarWidth(record: Recordable) {
  const count = Object.keys(record.fields || {}).length
  const pct = Math.min(100, count * 12)
  return `${Math.max(8, pct)}%`
}

const mappingColumns: BasicColumn[] = [
  { title: '模板', dataIndex: 'name', width: 280 },
  { title: '字段映射', dataIndex: 'fields', width: 180 },
  { title: '状态', dataIndex: 'enabled', width: 100 },
  { title: '操作', dataIndex: 'action', width: 90 },
]

async function fetchMappings() {
  const list = await getTransformMappingList()
  allList.value = list || []
  mappings.value = allList.value
  if (state.statusFilter === 'enabled') return allList.value.filter((i) => !!i.enabled)
  if (state.statusFilter === 'disabled') return allList.value.filter((i) => !i.enabled)
  return allList.value
}

const [registerMappingTable, { reload: reloadMappings }] = useTable({
  api: fetchMappings,
  columns: mappingColumns,
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

watch(
  () => state.statusFilter,
  async () => {
    try {
      await reloadMappings()
    } catch {
      // ignore
    }
  },
)

function getMappingTableActions(record: Recordable): ActionItem[] {
  return [
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => openMappingDrawer(true, { isUpdate: true, record }),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      danger: true,
      popConfirm: {
        title: `确认删除映射模板「${record.name}」？`,
        placement: 'topRight',
        confirm: () => handleDeleteMapping(record),
      },
    },
  ]
}

function editOrCreatePipeline() {
  if (primaryPipeline.value) {
    openPipelineDrawer(true, { isUpdate: true, record: primaryPipeline.value })
  } else {
    openPipelineDrawer(true, { isUpdate: false })
  }
}

async function reloadAll() {
  pipelines.value = await getTransformPipelineList()
  try {
    await reloadMappings()
  } catch {
    // ignore
  }
}

async function handleDeleteMapping(record: Recordable) {
  await deleteTransformMapping(record.id)
  createMessage.success('映射模板已删除')
  await reloadAll()
}

async function togglePipeline(record: Recordable, enabled: boolean) {
  try {
    await enableTransformPipeline(record.id, enabled)
    createMessage.success(`预处理已${enabled ? '开启' : '关闭'}`)
  } catch (error: any) {
    createMessage.error(error?.message || '启停失败')
  }
  await reloadAll()
}

onMounted(reloadAll)

defineExpose({ refresh: reloadAll })
</script>

<style lang="less" scoped>
@import '../theme.less';

.panel {
  .tf-panel();
}

.metric-strip {
  .tf-metric-strip();
}

.metric-item {
  .tf-metric-item();
}

.metric-item__icon {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-item__label {
  display: block;
  font-size: 12px;
  color: @tf-text-secondary;
  line-height: 1.2;
}

.metric-item__value {
  display: block;
  margin-top: 2px;
  font-size: 20px;
  font-weight: 600;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.pipeline-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 16px;
  border-bottom: 1px solid @tf-border;
  background: @tf-bg;
}

.pipeline-bar__left {
  min-width: 0;
}

.pipeline-bar__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: @tf-text-primary;
}

.pipeline-bar__desc {
  margin-top: 2px;
  font-size: 12px;
  color: @tf-text-muted;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.pipeline-bar__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.panel-bar {
  .tf-panel-bar();
}

.panel-bar__label {
  font-size: 13px;
  color: @tf-text-muted;
}

.panel-bar__actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.panel-body {
  .tf-panel-body();
}

.name-cell {
  line-height: 1.35;
}

.name-main {
  color: @tf-text-primary;
  font-weight: 550;
}

.name-sub {
  margin-top: 2px;
  font-size: 12px;
  color: @tf-text-muted;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.field-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 120px;
}

.field-num {
  font-size: 16px;
  font-weight: 650;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;
}

.field-unit {
  font-size: 12px;
  color: @tf-text-muted;
}

.field-bar {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: #f2f3f5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #722ed1, #b37feb);
  }
}
</style>
