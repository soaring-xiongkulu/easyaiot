<template>
  <div class="panel">
    <div class="metric-strip">
      <div
        v-for="item in overviewCards"
        :key="item.key"
        class="metric-item"
        :class="{ 'metric-item--active': state.subKey === item.key, 'metric-item--warn': item.warn }"
        @click="state.subKey = item.key"
      >
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
      <span class="panel-bar__label">队列</span>
      <RadioButtonGroup
        v-model:value="state.subKey"
        :options="segmentOptions"
        size="small"
        button-style="solid"
      />
      <div class="panel-bar__actions">
        <Button size="small" preIcon="ant-design:reload-outlined" @click="refreshCurrent">
          刷新
        </Button>
      </div>
    </div>

    <div class="panel-body">
      <BasicTable v-if="state.subKey === 'outbox'" @register="registerOutboxTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'id'">
            <Tooltip :title="record.id">
              <code class="id-code">{{ shortId(record.id) }}</code>
            </Tooltip>
          </template>
          <template v-else-if="column.dataIndex === 'eventId'">
            <Tooltip :title="record.eventId">
              <code class="id-code">{{ shortId(record.eventId) }}</code>
            </Tooltip>
          </template>
          <template v-else-if="column.dataIndex === 'status'">
            <Tag :color="statusColor(record.status)">{{ deliveryStatusLabel(record.status) }}</Tag>
          </template>
          <template v-else-if="column.dataIndex === 'error'">
            <Tooltip v-if="record.error" :title="record.error">
              <span class="error-text">{{ record.error }}</span>
            </Tooltip>
            <span v-else class="muted">—</span>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction
              :actions="[
                { label: '详情', onClick: () => showOutboxDetail(record) },
                { label: '再推', onClick: () => handleReplayOutbox(record.id) },
              ]"
            />
          </template>
        </template>
      </BasicTable>

      <BasicTable v-else @register="registerDlqTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'id'">
            <Tooltip :title="record.id">
              <code class="id-code">{{ shortId(record.id) }}</code>
            </Tooltip>
          </template>
          <template v-else-if="column.dataIndex === 'reason'">
            <Tooltip v-if="record.reason" :title="record.reason">
              <span class="error-text">{{ record.reason }}</span>
            </Tooltip>
            <span v-else class="muted">—</span>
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction
              :actions="[
                { label: '详情', onClick: () => showDlqDetail(record) },
                { label: '再推', onClick: () => handleReplayDlq(record.id) },
              ]"
            />
          </template>
        </template>
      </BasicTable>
    </div>

    <BasicModal
      :title="detailTitle"
      :width="720"
      :show-ok-btn="false"
      cancel-text="关闭"
      @register="registerDetailModal"
    >
      <pre class="detail-pre">{{ detailJson }}</pre>
    </BasicModal>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Tag, Tooltip } from 'ant-design-vue'
import { CountTo } from '@/components/CountTo'
import { Icon } from '@/components/Icon'
import { RadioButtonGroup } from '@/components/Form'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { BasicModal, useModal } from '@/components/Modal'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  getTransformDlqList,
  getTransformOutboxList,
  getTransformOverview,
  getTransformPartyList,
  replayTransformDlq,
  replayTransformOutbox,
} from '@/api/device/transform'
import { deliveryStatusLabel, getDlqColumns, getOutboxColumns } from '../data'

defineOptions({ name: 'TransformTracePanel' })

const { createMessage } = useMessage()
const [registerDetailModal, { openModal: openDetailModal }] = useModal()
const parties = ref<Recordable[]>([])
const overview = ref<Recordable>({})
const detailTitle = ref('')
const detailJson = ref('')
const state = reactive({ subKey: 'outbox' })

const segmentOptions = [
  { label: '出站队列', value: 'outbox' },
  { label: '失败队列', value: 'dlq' },
]

const overviewCards = computed(() => [
  {
    key: 'outbox',
    label: '出站队列',
    value: overview.value.outbox || 0,
    icon: 'ant-design:send-outlined',
    bg: '#f0f5ff',
    color: '#266cfb',
  },
  {
    key: 'dlq',
    label: '失败队列',
    value: overview.value.dlq || 0,
    warn: (overview.value.dlq || 0) > 0,
    icon: 'ant-design:warning-outlined',
    bg: '#fff7e8',
    color: '#ff7d00',
  },
])

function partyName(id?: string) {
  if (!id) return '—'
  return parties.value.find((item) => item.id === id)?.name || id
}

function statusColor(status?: string) {
  if (status === 'FAILED' || status === 'DEAD') return 'error'
  if (status === 'DELIVERED' || status === 'SENT') return 'success'
  if (status === 'RELAYING') return 'processing'
  return 'default'
}

function shortId(id?: string) {
  if (!id) return '—'
  if (id.length <= 18) return id
  return `${id.slice(0, 8)}…${id.slice(-6)}`
}

const [registerOutboxTable, { reload: reloadOutbox, setColumns }] = useTable({
  api: getTransformOutboxList,
  columns: getOutboxColumns(partyName),
  pagination: { pageSize: 10 },
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  inset: true,
  rowKey: 'id',
})

const [registerDlqTable, { reload: reloadDlq }] = useTable({
  api: getTransformDlqList,
  columns: getDlqColumns(),
  pagination: { pageSize: 10 },
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: false,
  inset: true,
  rowKey: 'id',
})

async function loadOverview() {
  overview.value = (await getTransformOverview()) || {}
}

async function refreshOutbox() {
  parties.value = await getTransformPartyList()
  setColumns(getOutboxColumns(partyName))
  try {
    await reloadOutbox()
  } catch {
    // ignore
  }
  await loadOverview()
}

async function refreshDlq() {
  try {
    await reloadDlq()
  } catch {
    // ignore
  }
  await loadOverview()
}

async function refreshCurrent() {
  if (state.subKey === 'outbox') await refreshOutbox()
  else await refreshDlq()
}

watch(
  () => state.subKey,
  async (key) => {
    if (key === 'dlq') await refreshDlq()
  },
)

async function handleReplayOutbox(id: string) {
  await replayTransformOutbox(id)
  createMessage.success('已发起再推')
  await refreshOutbox()
}

async function handleReplayDlq(id: string) {
  await replayTransformDlq(id)
  createMessage.success('失败记录已再推')
  await refreshDlq()
}

function showOutboxDetail(record: Recordable) {
  detailTitle.value = `投递详情 · ${shortId(record.id)}`
  detailJson.value = JSON.stringify(
    {
      id: record.id,
      eventId: record.eventId,
      partyId: record.partyId,
      contractId: record.contractId,
      channel: record.channel,
      status: record.status,
      attempts: record.attempts,
      error: record.error || null,
      createdAt: record.createdAt,
      updatedAt: record.updatedAt,
      envelope: record.envelope || null,
    },
    null,
    2,
  )
  openDetailModal(true)
}

function showDlqDetail(record: Recordable) {
  detailTitle.value = `死信详情 · ${shortId(record.id)}`
  detailJson.value = JSON.stringify(
    {
      id: record.id,
      source: record.source,
      reason: record.reason,
      outboxId: record.outboxId,
      createdAt: record.createdAt,
      envelope: record.envelope || null,
    },
    null,
    2,
  )
  openDetailModal(true)
}

onMounted(async () => {
  parties.value = await getTransformPartyList()
  setColumns(getOutboxColumns(partyName))
  await loadOverview()
})

defineExpose({
  refresh: async () => {
    await Promise.all([refreshOutbox(), refreshDlq()])
  },
})
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
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: #f5f8ff;
  }

  &--active {
    background: #f0f5ff;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 2px;
      background: @tf-primary;
    }
  }

  &--warn {
    background: #fffaf0;
  }
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

.id-code {
  padding: 1px 6px;
  border-radius: 3px;
  background: #f7f8fa;
  color: #4e5969;
  font-size: 12px;
}

.error-text {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #f53f3f;
  font-size: 12px;
  vertical-align: bottom;
}

.muted {
  color: #c9cdd4;
}

.detail-pre {
  margin: 0;
  max-height: 420px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.55;
  background: @tf-soft;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid @tf-border;
  color: @tf-text-body;
}
</style>
