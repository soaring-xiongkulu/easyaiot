<template>
  <div class="panel">
    <a-row :gutter="16" class="row" style="height: 100%">
      <a-col :span="15" class="col" style="height: 100%">
        <BasicTable v-if="state.outboxTableMode" @register="registerOutboxTable">
          <template #toolbar>
            <Button @click="refreshOutbox">刷新出站队列</Button>
            <Button preIcon="ant-design:swap-outlined" @click="swapOutboxView">切换视图</Button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'action'">
              <TableAction
                :actions="[{ label: '再推', onClick: handleReplayOutbox.bind(null, record.id) }]"
              />
            </template>
          </template>
        </BasicTable>
        <div v-else class="card-wrap">
          <TransformCardList
            title="出站队列（Outbox）"
            :api="getTransformOutboxList"
            :fields="outboxCardFields"
            :cover="COVER_OUTBOX"
            badge="OUT"
            title-key="id"
            status-key="status"
            @get-method="(m) => (outboxCardReload = m)"
          >
            <template #header>
              <Button @click="refreshOutbox">刷新出站队列</Button>
              <Button preIcon="ant-design:swap-outlined" @click="swapOutboxView">切换视图</Button>
            </template>
            <template #actions="{ record }">
              <OverlayBtn title="再推" @click="handleReplayOutbox(record.id)">
                <RedoOutlined />
              </OverlayBtn>
            </template>
          </TransformCardList>
        </div>
      </a-col>

      <a-col :span="9" class="col" style="height: 100%">
        <BasicTable v-if="state.dlqTableMode" @register="registerDlqTable">
          <template #toolbar>
            <Button @click="refreshDlq">刷新失败列表</Button>
            <Button preIcon="ant-design:swap-outlined" @click="swapDlqView">切换视图</Button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'action'">
              <TableAction
                :actions="[{ label: '再推', onClick: handleReplayDlq.bind(null, record.id) }]"
              />
            </template>
          </template>
        </BasicTable>
        <div v-else class="card-wrap">
          <TransformCardList
            title="失败列表（DLQ）"
            :api="getTransformDlqList"
            :fields="getDlqCardFields()"
            :cover="COVER_DLQ"
            badge="DLQ"
            title-key="id"
            @get-method="(m) => (dlqCardReload = m)"
          >
            <template #header>
              <Button @click="refreshDlq">刷新失败列表</Button>
              <Button preIcon="ant-design:swap-outlined" @click="swapDlqView">切换视图</Button>
            </template>
            <template #actions="{ record }">
              <OverlayBtn title="再推" @click="handleReplayDlq(record.id)">
                <RedoOutlined />
              </OverlayBtn>
            </template>
          </TransformCardList>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { RedoOutlined } from '@ant-design/icons-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  getTransformDlqList,
  getTransformOutboxList,
  getTransformPartyList,
  replayTransformDlq,
  replayTransformOutbox,
} from '@/api/device/transform'
import {
  getDlqCardFields,
  getDlqColumns,
  getOutboxCardFields,
  getOutboxColumns,
} from '../data'
import { COVER_DLQ, COVER_OUTBOX } from '../covers'
import TransformCardList from './TransformCardList.vue'
import OverlayBtn from './OverlayBtn.vue'

defineOptions({ name: 'TransformTracePanel' })

const { createMessage } = useMessage()
const parties = ref<Recordable[]>([])
const state = reactive({
  outboxTableMode: false,
  dlqTableMode: false,
})

type ReloadFn = (opts?: { resetPage?: boolean }) => Promise<void>
let outboxCardReload: ReloadFn = async () => {}
let dlqCardReload: ReloadFn = async () => {}

function partyName(id?: string) {
  if (!id) return '—'
  const target = parties.value.find((item) => item.id === id)
  return target ? target.name : id
}

const outboxCardFields = computed(() => getOutboxCardFields(partyName))

const [registerOutboxTable, { reload: reloadOutbox, setColumns }] = useTable({
  title: '出站队列（Outbox）',
  api: getTransformOutboxList,
  columns: getOutboxColumns(partyName),
  pagination: { pageSize: 10 },
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

const [registerDlqTable, { reload: reloadDlq }] = useTable({
  title: '失败列表（DLQ）',
  api: getTransformDlqList,
  columns: getDlqColumns(),
  pagination: { pageSize: 10 },
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

async function refreshOutbox() {
  parties.value = await getTransformPartyList()
  if (state.outboxTableMode) {
    setColumns(getOutboxColumns(partyName))
    try {
      await reloadOutbox()
    } catch {
      // ignore
    }
  } else {
    await outboxCardReload()
  }
}

async function refreshDlq() {
  if (state.dlqTableMode) {
    try {
      await reloadDlq()
    } catch {
      // ignore
    }
  } else {
    await dlqCardReload()
  }
}

async function swapOutboxView() {
  state.outboxTableMode = !state.outboxTableMode
  await nextTick()
  if (state.outboxTableMode) {
    await nextTick()
    setColumns(getOutboxColumns(partyName))
    try {
      await reloadOutbox()
    } catch {
      // ignore
    }
  } else {
    await outboxCardReload()
  }
}

async function swapDlqView() {
  state.dlqTableMode = !state.dlqTableMode
  await nextTick()
  if (state.dlqTableMode) {
    await nextTick()
    try {
      await reloadDlq()
    } catch {
      // ignore
    }
  } else {
    await dlqCardReload()
  }
}

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

onMounted(async () => {
  parties.value = await getTransformPartyList()
})

defineExpose({
  refresh: async () => {
    await Promise.all([refreshOutbox(), refreshDlq()])
  },
})
</script>

<style lang="less" scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.row {
  flex: 1;
  min-height: 0;
  height: 100%;
}

.col {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
