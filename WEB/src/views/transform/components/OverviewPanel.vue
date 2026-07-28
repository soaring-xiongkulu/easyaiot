<template>
  <div class="panel">
    <a-row :gutter="12" class="metric-row">
      <a-col :xs="12" :sm="8" :md="4" v-for="item in overviewCards" :key="item.label">
        <a-card size="small" :bordered="false" class="metric-card">
          <a-statistic :title="item.label" :value="item.value" />
        </a-card>
      </a-col>
    </a-row>

    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <Button @click="handleRefresh">刷新</Button>
        <Button type="primary" @click="onPingAll">广播 PING</Button>
        <Button @click="onReloadConfig">广播重载配置</Button>
        <Button preIcon="ant-design:swap-outlined" @click="handleClickSwap">切换视图</Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[{ label: 'PING', onClick: onPingOne.bind(null, record.instanceId) }]"
          />
        </template>
      </template>
    </BasicTable>

    <div v-else class="card-wrap">
      <TransformCardList
        title="集群运行实例"
        :api="getTransformInstances"
        :fields="getInstanceCardFields()"
        :cover="COVER_INSTANCE"
        badge="RT"
        row-key="instanceId"
        title-key="instanceId"
        status-key="online"
        @get-method="getCardMethod"
      >
        <template #header>
          <Button @click="handleRefresh">刷新</Button>
          <Button type="primary" @click="onPingAll">广播 PING</Button>
          <Button @click="onReloadConfig">广播重载配置</Button>
          <Button preIcon="ant-design:swap-outlined" @click="handleClickSwap">切换视图</Button>
        </template>
        <template #actions="{ record }">
          <OverlayBtn title="PING" @click="onPingOne(record.instanceId)">
            <ApiOutlined />
          </OverlayBtn>
        </template>
      </TransformCardList>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ApiOutlined } from '@ant-design/icons-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  getTransformInstances,
  getTransformOverview,
  issueTransformCommand,
} from '@/api/device/transform'
import { getInstanceCardFields, getInstanceColumns } from '../data'
import { COVER_INSTANCE } from '../covers'
import TransformCardList from './TransformCardList.vue'
import OverlayBtn from './OverlayBtn.vue'

defineOptions({ name: 'TransformOverviewPanel' })

const { createMessage } = useMessage()
const overview = ref<Recordable>({})
const state = reactive({ isTableMode: false })
let cardReload: (opts?: { resetPage?: boolean }) => Promise<void> = async () => {}

const overviewCards = computed(() => [
  { label: '对接系统', value: overview.value.parties || 0 },
  { label: '推送规则', value: overview.value.contracts || 0 },
  { label: '映射模板', value: overview.value.mappings || 0 },
  { label: '在线实例', value: overview.value.onlineInstances || 0 },
  { label: '出站队列', value: overview.value.outbox || 0 },
  { label: '失败队列', value: overview.value.dlq || 0 },
])

const [registerTable, { reload }] = useTable({
  title: '集群运行实例',
  api: getTransformInstances,
  columns: getInstanceColumns(),
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'instanceId',
})

function getCardMethod(m: typeof cardReload) {
  cardReload = m
}

async function reloadOverview() {
  overview.value = (await getTransformOverview()) || {}
}

async function handleRefresh() {
  await reloadOverview()
  if (state.isTableMode) {
    try {
      await reload()
    } catch {
      // ignore
    }
  } else {
    await cardReload()
  }
}

async function handleClickSwap() {
  state.isTableMode = !state.isTableMode
  await nextTick()
  if (state.isTableMode) {
    await nextTick()
    try {
      await reload()
    } catch {
      // ignore
    }
  } else {
    await cardReload()
  }
}

async function onPingAll() {
  await issueTransformCommand({ type: 'PING', targetInstanceId: '*' })
  createMessage.success('已广播 PING')
}

async function onPingOne(instanceId: string) {
  await issueTransformCommand({ type: 'PING', targetInstanceId: instanceId })
  createMessage.success('已发送节点 PING')
}

async function onReloadConfig() {
  await issueTransformCommand({ type: 'RELOAD_CONFIG', targetInstanceId: '*' })
  createMessage.success('已广播重载配置')
}

onMounted(reloadOverview)

defineExpose({ refresh: handleRefresh })
</script>

<style lang="less" scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.metric-row {
  margin-bottom: 12px;
  flex-shrink: 0;
}

.metric-card {
  border-radius: 8px;
  background: #f7f9fc;
}

.card-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
