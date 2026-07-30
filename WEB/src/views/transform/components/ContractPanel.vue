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
            <span v-if="item.suffix" class="metric-item__suffix">{{ item.suffix }}</span>
          </span>
        </div>
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
        <Button
          type="primary"
          preIcon="ant-design:plus-outlined"
          @click="() => openDrawer(true, { isUpdate: false })"
        >
          新建转发规则
        </Button>
        <Button preIcon="ant-design:reload-outlined" @click="handleRefresh">刷新</Button>
      </div>
    </div>

    <div class="panel-body">
      <BasicTable @register="registerTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'id'">
            <div class="rule-cell">
              <a class="link" @click="() => openDrawer(true, { isView: true, isUpdate: true, record })">
                {{ record.id }}
              </a>
              <div class="rule-sub">
                <span class="dot" :class="record.enabled ? 'dot--on' : 'dot--off'" />
                {{ record.enabled ? '运行中' : '已停止' }}
                <span v-if="headerCount(record)" class="rule-meta">
                  · {{ headerCount(record) }} 个请求头
                </span>
              </div>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'flow'">
            <FlowPath
              :source="flowTypeLabel(record.flowType)"
              :mapping="mappingName(record.mappingId)"
              :destination="partyName(record.partyId)"
            />
          </template>
          <template v-else-if="column.dataIndex === 'channel'">
            <Tag>{{ channelLabel(record.channel) }}</Tag>
          </template>
          <template v-else-if="column.dataIndex === 'endpoint'">
            <Tooltip :title="record.endpoint">
              <code class="endpoint">{{ record.endpoint || '—' }}</code>
            </Tooltip>
          </template>
          <template v-else-if="column.dataIndex === 'enabled'">
            <Switch
              :checked="!!record.enabled"
              checked-children="运行"
              un-checked-children="停止"
              @change="(checked) => toggleEnabled(record, !!checked)"
            />
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction :actions="getTableActions(record)" />
          </template>
        </template>
      </BasicTable>
    </div>

    <ContractDrawer @register="registerDrawer" @success="handleRefresh" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Switch, Tag, Tooltip } from 'ant-design-vue'
import { CountTo } from '@/components/CountTo'
import { Icon } from '@/components/Icon'
import { RadioButtonGroup } from '@/components/Form'
import { BasicTable, TableAction, useTable, type ActionItem, type BasicColumn } from '@/components/Table'
import { Button } from '@/components/Button'
import { useDrawer } from '@/components/Drawer'
import { useMessage } from '@/hooks/web/useMessage'
import {
  deleteTransformContract,
  getTransformContractList,
  getTransformMappingList,
  getTransformOverview,
  getTransformPartyList,
  updateTransformContract,
} from '@/api/device/transform'
import { channelLabel, flowTypeLabel } from '../data'
import ContractDrawer from './ContractDrawer.vue'
import FlowPath from './FlowPath.vue'

defineOptions({ name: 'TransformContractPanel' })

defineEmits<{ (e: 'goto', key: string): void }>()
const { createMessage } = useMessage()
const [registerDrawer, { openDrawer }] = useDrawer()

const parties = ref<Recordable[]>([])
const mappings = ref<Recordable[]>([])
const overview = ref<Recordable>({})
const allContracts = ref<Recordable[]>([])
const state = reactive({ statusFilter: '' })

function partyName(id?: string) {
  if (!id) return '—'
  return parties.value.find((item) => item.id === id)?.name || id
}

function mappingName(id?: string) {
  if (!id) return '透传'
  return mappings.value.find((item) => item.id === id)?.name || id
}

const runningCount = computed(() => allContracts.value.filter((c) => !!c.enabled).length)
const stoppedCount = computed(() => allContracts.value.filter((c) => !c.enabled).length)

const overviewCards = computed(() => [
  {
    key: 'total',
    label: '规则总数',
    value: allContracts.value.length,
    icon: 'ant-design:apartment-outlined',
    bg: '#fff7e8',
    color: '#ff7d00',
  },
  {
    key: 'running',
    label: '运行中',
    value: runningCount.value,
    icon: 'ant-design:play-circle-outlined',
    bg: '#e8ffea',
    color: '#00b42a',
  },
  {
    key: 'party',
    label: '数据目的',
    value: overview.value.parties || 0,
    icon: 'ant-design:cloud-server-outlined',
    bg: '#e8ffea',
    color: '#00b42a',
  },
  {
    key: 'mapping',
    label: '映射模板',
    value: overview.value.mappings || 0,
    icon: 'ant-design:swap-outlined',
    bg: '#f5e8ff',
    color: '#722ed1',
  },
  {
    key: 'dlq',
    label: '失败队列',
    value: overview.value.dlq || 0,
    suffix: (overview.value.dlq || 0) > 0 ? ' 待处理' : '',
    icon: 'ant-design:warning-outlined',
    bg: '#fff7e8',
    color: '#ff7d00',
  },
])

const filterOptions = computed(() => [
  { label: `全部 (${allContracts.value.length})`, value: '' },
  { label: `运行中 (${runningCount.value})`, value: 'running' },
  { label: `已停止 (${stoppedCount.value})`, value: 'stopped' },
])

function getColumns(): BasicColumn[] {
  return [
    { title: '规则', dataIndex: 'id', width: 200, ellipsis: true },
    { title: '转发链路', dataIndex: 'flow', width: 380 },
    { title: '通道', dataIndex: 'channel', width: 120 },
    { title: '投递地址', dataIndex: 'endpoint', width: 260, ellipsis: true },
    { title: '启停', dataIndex: 'enabled', width: 100 },
    { title: '操作', dataIndex: 'action', width: 90 },
  ]
}

async function fetchContracts() {
  const list = await getTransformContractList()
  allContracts.value = list || []
  if (state.statusFilter === 'running') return allContracts.value.filter((c) => !!c.enabled)
  if (state.statusFilter === 'stopped') return allContracts.value.filter((c) => !c.enabled)
  return allContracts.value
}

const [registerTable, { reload, setColumns }] = useTable({
  api: fetchContracts,
  columns: getColumns(),
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  inset: true,
  rowKey: 'id',
})

watch(
  () => state.statusFilter,
  async () => {
    try {
      await reload()
    } catch {
      // ignore
    }
  },
)

function headerCount(record: Recordable) {
  return Object.keys(record.headers || {}).length
}

function getTableActions(record: Recordable): ActionItem[] {
  return [
    {
      icon: 'ant-design:eye-filled',
      tooltip: { title: '查看', placement: 'top' },
      onClick: () => openDrawer(true, { isView: true, isUpdate: true, record }),
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: { title: '编辑', placement: 'top' },
      onClick: () => openDrawer(true, { isUpdate: true, record }),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: { title: '删除', placement: 'top' },
      danger: true,
      popConfirm: {
        title: record.enabled
          ? '运行中的规则不可删除，请先停止'
          : `确认删除转发规则「${record.id}」？`,
        placement: 'topRight',
        confirm: () => handleDelete(record),
      },
    },
  ]
}

async function loadRefs() {
  const [partyList, mappingList, overviewData] = await Promise.all([
    getTransformPartyList(),
    getTransformMappingList(),
    getTransformOverview(),
  ])
  parties.value = partyList
  mappings.value = mappingList
  overview.value = overviewData || {}
  setColumns(getColumns())
}

async function handleRefresh() {
  await loadRefs()
  try {
    await reload()
  } catch {
    // ignore
  }
}

async function handleDelete(record: Recordable) {
  if (record.enabled) {
    createMessage.warning('请先停止规则再删除')
    return
  }
  await deleteTransformContract(record.id)
  createMessage.success('转发规则已删除')
  await handleRefresh()
}

async function toggleEnabled(record: Recordable, enabled: boolean) {
  try {
    await updateTransformContract(record.id, { ...record, enabled })
    createMessage.success(`规则已${enabled ? '启动' : '停止'}`)
  } catch (error: any) {
    createMessage.error(error?.message || '启停失败')
  }
  await handleRefresh()
}

onMounted(loadRefs)

defineExpose({ refresh: handleRefresh })
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
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 2px;
  font-size: 20px;
  font-weight: 600;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.metric-item__suffix {
  font-size: 12px;
  font-weight: 500;
  color: @tf-text-muted;
}

.panel-bar {
  .tf-panel-bar();
}

.panel-bar__label {
  font-size: 13px;
  color: @tf-text-muted;
  flex-shrink: 0;
}

.panel-bar__actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.panel-body {
  .tf-panel-body();
}

.rule-cell {
  line-height: 1.35;
}

.link {
  color: @tf-primary;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.rule-sub {
  margin-top: 3px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: @tf-text-muted;
}

.rule-meta {
  color: #c9cdd4;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;

  &--on {
    background: #00b42a;
    box-shadow: 0 0 0 3px rgba(0, 180, 42, 0.15);
  }

  &--off {
    background: #c9cdd4;
  }
}

.endpoint {
  display: inline-block;
  max-width: 100%;
  padding: 0 6px;
  border-radius: 3px;
  background: #f7f8fa;
  color: @tf-text-secondary;
  font-size: 12px;
  line-height: 22px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
