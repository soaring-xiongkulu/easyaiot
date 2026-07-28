<template>
  <div class="panel">
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <Button type="primary" @click="openModal(true, { isUpdate: false })">新增对接系统</Button>
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
        title="对接系统"
        :api="getTransformPartyList"
        :fields="getPartyCardFields()"
        :cover="COVER_PARTY"
        badge="SYS"
        status-key="enabled"
        @get-method="getCardMethod"
      >
        <template #header>
          <Button type="primary" @click="openModal(true, { isUpdate: false })">新增对接系统</Button>
          <Button @click="handleRefresh">刷新</Button>
          <Button preIcon="ant-design:swap-outlined" @click="handleClickSwap">切换视图</Button>
        </template>
        <template #actions="{ record }">
          <OverlayBtn title="编辑" @click="openModal(true, { isUpdate: true, record })">
            <EditOutlined />
          </OverlayBtn>
          <Popconfirm
            :title="`确认删除对接系统「${record.name}」？`"
            @confirm="handleDelete(record)"
          >
            <OverlayBtn title="删除" danger>
              <DeleteOutlined />
            </OverlayBtn>
          </Popconfirm>
        </template>
      </TransformCardList>
    </div>

    <PartyModal @register="registerModal" @success="handleRefresh" />
  </div>
</template>

<script lang="ts" setup>
import { nextTick, reactive } from 'vue'
import { Popconfirm } from 'ant-design-vue'
import { DeleteOutlined, EditOutlined } from '@ant-design/icons-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useModal } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import { deleteTransformParty, getTransformPartyList } from '@/api/device/transform'
import { getPartyCardFields, getPartyColumns } from '../data'
import { COVER_PARTY } from '../covers'
import PartyModal from './PartyModal.vue'
import TransformCardList from './TransformCardList.vue'
import OverlayBtn from './OverlayBtn.vue'

defineOptions({ name: 'TransformPartyPanel' })

const { createMessage } = useMessage()
const [registerModal, { openModal }] = useModal()
const state = reactive({ isTableMode: false })
let cardReload: (opts?: { resetPage?: boolean }) => Promise<void> = async () => {}

const [registerTable, { reload }] = useTable({
  title: '对接系统',
  api: getTransformPartyList,
  columns: getPartyColumns(),
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
        title: `确认删除对接系统「${record.name}」？`,
        placement: 'topRight',
        confirm: handleDelete.bind(null, record),
      },
    },
  ]
}

async function handleRefresh() {
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

async function handleDelete(record: Recordable) {
  await deleteTransformParty(record.id)
  createMessage.success('对接系统已删除')
  await handleRefresh()
}

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
