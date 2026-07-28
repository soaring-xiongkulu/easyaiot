<template>
  <div class="panel">
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <Button type="primary" @click="openModal(true, { isUpdate: false })">新增推送规则</Button>
        <Button @click="handleRefresh">刷新</Button>
        <Button preIcon="ant-design:swap-outlined" @click="handleClickSwap">切换视图</Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <div v-else class="card-wrap">
      <TransformCardList
        title="推送规则"
        :api="getTransformContractList"
        :fields="contractCardFields"
        :cover="COVER_CONTRACT"
        badge="RL"
        title-key="id"
        status-key="enabled"
        @get-method="getCardMethod"
      >
        <template #header>
          <Button type="primary" @click="openModal(true, { isUpdate: false })">新增推送规则</Button>
          <Button @click="handleRefresh">刷新</Button>
          <Button preIcon="ant-design:swap-outlined" @click="handleClickSwap">切换视图</Button>
        </template>
        <template #actions="{ record }">
          <OverlayBtn title="编辑" @click="openModal(true, { isUpdate: true, record })">
            <EditOutlined />
          </OverlayBtn>
          <Popconfirm
            :title="`确认删除推送规则「${record.id}」？`"
            @confirm="handleDelete(record)"
          >
            <OverlayBtn title="删除" danger>
              <DeleteOutlined />
            </OverlayBtn>
          </Popconfirm>
        </template>
      </TransformCardList>
    </div>

    <ContractModal @register="registerModal" @success="handleRefresh" />
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { Popconfirm } from 'ant-design-vue'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useModal } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import {
  deleteTransformContract,
  getTransformContractList,
  getTransformPartyList,
} from '@/api/device/transform'
import { getContractCardFields, getContractColumns } from '../data'
import { COVER_CONTRACT } from '../covers'
import ContractModal from './ContractModal.vue'
import TransformCardList from './TransformCardList.vue'
import OverlayBtn from './OverlayBtn.vue'

defineOptions({ name: 'TransformContractPanel' })

const { createMessage } = useMessage()
const [registerModal, { openModal }] = useModal()
const parties = ref<Recordable[]>([])
const state = reactive({ isTableMode: false })
let cardReload: (opts?: { resetPage?: boolean }) => Promise<void> = async () => {}

function partyName(id?: string) {
  if (!id) return '—'
  const target = parties.value.find((item) => item.id === id)
  return target ? target.name : id
}

const contractCardFields = computed(() => getContractCardFields(partyName))

const [registerTable, { reload, setColumns }] = useTable({
  title: '推送规则',
  api: getTransformContractList,
  columns: getContractColumns(partyName),
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

function getCardMethod(m: typeof cardReload) {
  cardReload = m
}

function getTableActions(record: Recordable) {
  return [
    {
      icon: 'ant-design:edit-filled',
      tooltip: { title: '编辑', placement: 'top' },
      onClick: openModal.bind(null, true, { isUpdate: true, record }),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: { title: '删除', placement: 'top' },
      danger: true,
      popConfirm: {
        title: `确认删除推送规则「${record.id}」？`,
        placement: 'topRight',
        confirm: handleDelete.bind(null, record),
      },
    },
  ]
}

async function loadParties() {
  parties.value = await getTransformPartyList()
  if (state.isTableMode) {
    setColumns(getContractColumns(partyName))
  }
}

async function handleRefresh() {
  await loadParties()
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
    setColumns(getContractColumns(partyName))
    try {
      await reload()
    } catch {
      // ignore
    }
  } else {
    await cardReload()
  }
}

async function handleDelete(record: Recordable) {
  await deleteTransformContract(record.id)
  createMessage.success('推送规则已删除')
  await handleRefresh()
}

onMounted(loadParties)

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

.card-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
