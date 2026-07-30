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
          新增数据目的
        </Button>
        <Button preIcon="ant-design:reload-outlined" @click="handleRefresh">刷新</Button>
      </div>
    </div>

    <div class="panel-body">
      <BasicTable @register="registerTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'name'">
            <div class="name-cell">
              <span class="type-mark" :style="{ background: typeColor(record.type) }" />
              <div>
                <a class="name-main link" @click="() => openDrawer(true, { isView: true, isUpdate: true, record })">
                  {{ record.name }}
                </a>
                <div class="name-sub">{{ record.id }}</div>
              </div>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'type'">
            <Tag :color="typeTagColor(record.type)">{{ systemTypeLabel(record.type) }}</Tag>
          </template>
          <template v-else-if="column.dataIndex === 'config'">
            <div v-if="record?.config?.baseUrl" class="config-cell">
              <code class="addr">{{ record.config.baseUrl }}</code>
              <div class="config-meta">
                超时 {{ record.config.timeoutSeconds || 10 }}s
                <template v-if="record.config.partySecret || record.config.authToken">
                  · 已配置鉴权
                </template>
              </div>
            </div>
            <div v-else class="config-warn">
              <span class="muted">未配置基础地址</span>
              <a class="fix-link" @click="() => openDrawer(true, { isUpdate: true, record })">去配置</a>
            </div>
          </template>
          <template v-else-if="column.dataIndex === 'enabled'">
            <Switch
              :checked="!!record.enabled"
              checked-children="可用"
              un-checked-children="停用"
              @change="(checked) => toggleEnabled(record, !!checked)"
            />
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction :actions="getTableActions(record)" />
          </template>
        </template>
      </BasicTable>
    </div>

    <PartyDrawer @register="registerDrawer" @success="handleRefresh" />
  </div>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { Switch, Tag } from 'ant-design-vue'
import { CountTo } from '@/components/CountTo'
import { Icon } from '@/components/Icon'
import { RadioButtonGroup } from '@/components/Form'
import { BasicTable, TableAction, useTable, type ActionItem, type BasicColumn } from '@/components/Table'
import { Button } from '@/components/Button'
import { useDrawer } from '@/components/Drawer'
import { useMessage } from '@/hooks/web/useMessage'
import { deleteTransformParty, getTransformPartyList, updateTransformParty } from '@/api/device/transform'
import { systemTypeLabel } from '../data'
import PartyDrawer from './PartyDrawer.vue'

defineOptions({ name: 'TransformPartyPanel' })

defineEmits<{ (e: 'goto', key: string): void }>()
const { createMessage } = useMessage()
const [registerDrawer, { openDrawer }] = useDrawer()

const allList = ref<Recordable[]>([])
const state = reactive({ statusFilter: '' })

const enabledCount = computed(() => allList.value.filter((i) => !!i.enabled).length)
const disabledCount = computed(() => allList.value.filter((i) => !i.enabled).length)

const overviewCards = computed(() => [
  {
    key: 'total',
    label: '目的地总数',
    value: allList.value.length,
    icon: 'ant-design:cloud-server-outlined',
    bg: '#e8ffea',
    color: '#00b42a',
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
    key: 'disabled',
    label: '停用',
    value: disabledCount.value,
    icon: 'ant-design:stop-outlined',
    bg: '#f2f3f5',
    color: '#86909c',
  },
  {
    key: 'types',
    label: '系统类型',
    value: new Set(allList.value.map((i) => i.type).filter(Boolean)).size,
    icon: 'ant-design:appstore-outlined',
    bg: '#f0f5ff',
    color: '#266cfb',
  },
])

const filterOptions = computed(() => [
  { label: `全部 (${allList.value.length})`, value: '' },
  { label: `可用 (${enabledCount.value})`, value: 'enabled' },
  { label: `停用 (${disabledCount.value})`, value: 'disabled' },
])

const typeColors: Recordable = {
  'mes.rest': '#00b42a',
  'erp.rest': '#266cfb',
  'wms.rest': '#ff7d00',
  'crm.rest': '#722ed1',
  'oa.rest': '#86909c',
  'custom.rest': '#14c9c9',
}

const typeTagColors: Recordable = {
  'mes.rest': 'success',
  'erp.rest': 'blue',
  'wms.rest': 'orange',
  'crm.rest': 'purple',
  'oa.rest': 'default',
  'custom.rest': 'cyan',
}

function typeColor(type?: string) {
  return (type && typeColors[type]) || '#266cfb'
}

function typeTagColor(type?: string) {
  return (type && typeTagColors[type]) || 'default'
}

const columns: BasicColumn[] = [
  { title: '目的地', dataIndex: 'name', width: 260 },
  { title: '系统类型', dataIndex: 'type', width: 180 },
  { title: '基础地址', dataIndex: 'config', width: 320, ellipsis: true },
  { title: '状态', dataIndex: 'enabled', width: 100 },
  { title: '操作', dataIndex: 'action', width: 90 },
]

async function fetchList() {
  const list = await getTransformPartyList()
  allList.value = list || []
  if (state.statusFilter === 'enabled') return allList.value.filter((i) => !!i.enabled)
  if (state.statusFilter === 'disabled') return allList.value.filter((i) => !i.enabled)
  return allList.value
}

const [registerTable, { reload }] = useTable({
  api: fetchList,
  columns,
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
        title: `确认删除数据目的「${record.name}」？`,
        placement: 'topRight',
        confirm: () => handleDelete(record),
      },
    },
  ]
}

async function handleRefresh() {
  try {
    await reload()
  } catch {
    // ignore
  }
}

async function toggleEnabled(record: Recordable, enabled: boolean) {
  try {
    await updateTransformParty(record.id, { ...record, enabled })
    createMessage.success(`数据目的已${enabled ? '启用' : '停用'}`)
  } catch (error: any) {
    createMessage.error(error?.message || '启停失败')
  }
  await handleRefresh()
}

async function handleDelete(record: Recordable) {
  await deleteTransformParty(record.id)
  createMessage.success('数据目的已删除')
  await handleRefresh()
}

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
  display: block;
  margin-top: 2px;
  font-size: 20px;
  font-weight: 600;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
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
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-mark {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.name-main {
  font-weight: 550;
  color: @tf-text-primary;
}

.link {
  color: @tf-primary;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.name-sub {
  margin-top: 2px;
  font-size: 12px;
  color: @tf-text-muted;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.config-cell {
  min-width: 0;
}

.config-meta {
  margin-top: 2px;
  font-size: 12px;
  color: @tf-text-muted;
}

.config-warn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fix-link {
  font-size: 12px;
  color: @tf-primary;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.addr {
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

.muted {
  color: #c9cdd4;
  font-size: 13px;
}
</style>
