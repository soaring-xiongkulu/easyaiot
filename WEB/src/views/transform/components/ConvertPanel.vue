<template>
  <div class="panel">
    <a-row :gutter="16" class="row" style="height: 100%">
      <a-col :span="12" class="col" style="height: 100%">
        <BasicTable v-if="state.mappingTableMode" @register="registerMappingTable">
          <template #toolbar>
            <Button type="primary" @click="openMappingModal(true, { isUpdate: false })">
              新增映射模板
            </Button>
            <Button @click="reloadAll">刷新</Button>
            <Button preIcon="ant-design:swap-outlined" @click="swapMappingView">切换视图</Button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'action'">
              <TableAction :actions="getMappingTableActions(record)" />
            </template>
          </template>
        </BasicTable>
        <div v-else class="card-wrap">
          <TransformCardList
            title="字段映射模板"
            :api="getTransformMappingList"
            :fields="getMappingCardFields()"
            :cover="COVER_MAPPING"
            badge="MAP"
            status-key="enabled"
            @get-method="(m) => (mappingCardReload = m)"
          >
            <template #header>
              <Button type="primary" @click="openMappingModal(true, { isUpdate: false })">
                新增映射模板
              </Button>
              <Button @click="reloadAll">刷新</Button>
              <Button preIcon="ant-design:swap-outlined" @click="swapMappingView">切换视图</Button>
            </template>
            <template #actions="{ record }">
              <OverlayBtn title="编辑" @click="openMappingModal(true, { isUpdate: true, record })">
                <EditOutlined />
              </OverlayBtn>
              <Popconfirm
                :title="`确认删除映射模板「${record.name}」？`"
                @confirm="handleDeleteMapping(record)"
              >
                <OverlayBtn title="删除" danger>
                  <DeleteOutlined />
                </OverlayBtn>
              </Popconfirm>
            </template>
          </TransformCardList>
        </div>
      </a-col>

      <a-col :span="12" class="col" style="height: 100%">
        <BasicTable v-if="state.pipelineTableMode" @register="registerPipelineTable">
          <template #toolbar>
            <Button type="primary" @click="openPipelineModal(true, { isUpdate: false })">
              新增转换流程
            </Button>
            <Button @click="reloadAll">刷新</Button>
            <Button preIcon="ant-design:swap-outlined" @click="swapPipelineView">切换视图</Button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'enabled'">
              <Switch
                :checked="!!record.enabled"
                @change="(checked) => togglePipeline(record, !!checked)"
              />
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <TableAction :actions="getPipelineTableActions(record)" />
            </template>
          </template>
        </BasicTable>
        <div v-else class="card-wrap">
          <TransformCardList
            title="转换流程"
            :api="getTransformPipelineList"
            :fields="pipelineCardFields"
            :cover="COVER_PIPELINE"
            badge="PL"
            status-key="enabled"
            @get-method="(m) => (pipelineCardReload = m)"
          >
            <template #header>
              <Button type="primary" @click="openPipelineModal(true, { isUpdate: false })">
                新增转换流程
              </Button>
              <Button @click="reloadAll">刷新</Button>
              <Button preIcon="ant-design:swap-outlined" @click="swapPipelineView">切换视图</Button>
            </template>
            <template #actions="{ record }">
              <OverlayBtn
                :title="record.enabled ? '停用' : '启用'"
                @click="togglePipeline(record, !record.enabled)"
              >
                <PauseCircleOutlined v-if="record.enabled" />
                <PlayCircleOutlined v-else />
              </OverlayBtn>
              <OverlayBtn title="编辑" @click="openPipelineModal(true, { isUpdate: true, record })">
                <EditOutlined />
              </OverlayBtn>
              <Popconfirm
                :title="`确认删除转换流程「${record.name}」？`"
                @confirm="handleDeletePipeline(record)"
              >
                <OverlayBtn title="删除" danger>
                  <DeleteOutlined />
                </OverlayBtn>
              </Popconfirm>
            </template>
          </TransformCardList>
        </div>
      </a-col>
    </a-row>

    <MappingModal @register="registerMappingModal" @success="reloadAll" />
    <PipelineModal @register="registerPipelineModal" @success="reloadAll" />
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { Popconfirm, Switch } from 'ant-design-vue'
import {
  DeleteOutlined,
  EditOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useModal } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import {
  deleteTransformMapping,
  deleteTransformPipeline,
  enableTransformPipeline,
  getTransformMappingList,
  getTransformPipelineList,
} from '@/api/device/transform'
import {
  getMappingCardFields,
  getMappingColumns,
  getPipelineCardFields,
  getPipelineColumns,
} from '../data'
import { COVER_MAPPING, COVER_PIPELINE } from '../covers'
import MappingModal from './MappingModal.vue'
import PipelineModal from './PipelineModal.vue'
import TransformCardList from './TransformCardList.vue'
import OverlayBtn from './OverlayBtn.vue'

defineOptions({ name: 'TransformConvertPanel' })

const { createMessage } = useMessage()
const [registerMappingModal, { openModal: openMappingModal }] = useModal()
const [registerPipelineModal, { openModal: openPipelineModal }] = useModal()
const mappings = ref<Recordable[]>([])
const state = reactive({
  mappingTableMode: false,
  pipelineTableMode: false,
})

type ReloadFn = (opts?: { resetPage?: boolean }) => Promise<void>
let mappingCardReload: ReloadFn = async () => {}
let pipelineCardReload: ReloadFn = async () => {}

function mappingName(id?: string) {
  if (!id) return '—'
  const target = mappings.value.find((item) => item.id === id)
  return target ? target.name : id
}

const pipelineCardFields = computed(() => getPipelineCardFields(mappingName))

const [registerMappingTable, { reload: reloadMappings }] = useTable({
  title: '字段映射模板',
  api: getTransformMappingList,
  columns: getMappingColumns(),
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

const [registerPipelineTable, { reload: reloadPipelines, setColumns }] = useTable({
  title: '转换流程',
  api: getTransformPipelineList,
  columns: getPipelineColumns(mappingName),
  pagination: false,
  canResize: true,
  useSearchForm: false,
  showTableSetting: false,
  showIndexColumn: false,
  immediate: true,
  rowKey: 'id',
})

function getMappingTableActions(record: Recordable) {
  return [
    {
      icon: 'ant-design:edit-filled',
      tooltip: { title: '编辑', placement: 'top' },
      onClick: openMappingModal.bind(null, true, { isUpdate: true, record }),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: { title: '删除', placement: 'top' },
      danger: true,
      popConfirm: {
        title: `确认删除映射模板「${record.name}」？`,
        placement: 'topRight',
        confirm: handleDeleteMapping.bind(null, record),
      },
    },
  ]
}

function getPipelineTableActions(record: Recordable) {
  return [
    {
      icon: 'ant-design:edit-filled',
      tooltip: { title: '编辑', placement: 'top' },
      onClick: openPipelineModal.bind(null, true, { isUpdate: true, record }),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: { title: '删除', placement: 'top' },
      danger: true,
      popConfirm: {
        title: `确认删除转换流程「${record.name}」？`,
        placement: 'topRight',
        confirm: handleDeletePipeline.bind(null, record),
      },
    },
  ]
}

async function reloadAll() {
  mappings.value = await getTransformMappingList()
  if (state.pipelineTableMode) {
    setColumns(getPipelineColumns(mappingName))
  }
  if (state.mappingTableMode) {
    try {
      await reloadMappings()
    } catch {
      // ignore
    }
  } else {
    await mappingCardReload()
  }
  if (state.pipelineTableMode) {
    try {
      await reloadPipelines()
    } catch {
      // ignore
    }
  } else {
    await pipelineCardReload()
  }
}

async function swapMappingView() {
  state.mappingTableMode = !state.mappingTableMode
  await nextTick()
  if (state.mappingTableMode) {
    await nextTick()
    try {
      await reloadMappings()
    } catch {
      // ignore
    }
  } else {
    await mappingCardReload()
  }
}

async function swapPipelineView() {
  state.pipelineTableMode = !state.pipelineTableMode
  await nextTick()
  if (state.pipelineTableMode) {
    await nextTick()
    setColumns(getPipelineColumns(mappingName))
    try {
      await reloadPipelines()
    } catch {
      // ignore
    }
  } else {
    await pipelineCardReload()
  }
}

async function handleDeleteMapping(record: Recordable) {
  await deleteTransformMapping(record.id)
  createMessage.success('映射模板已删除')
  await reloadAll()
}

async function handleDeletePipeline(record: Recordable) {
  await deleteTransformPipeline(record.id)
  createMessage.success('转换流程已删除')
  if (state.pipelineTableMode) {
    await reloadPipelines()
  } else {
    await pipelineCardReload()
  }
}

async function togglePipeline(record: Recordable, enabled: boolean) {
  try {
    await enableTransformPipeline(record.id, enabled)
    createMessage.success(`流程已${enabled ? '启用' : '停用'}`)
  } catch (error: any) {
    createMessage.error(error?.message || '启停失败')
  }
  if (state.pipelineTableMode) {
    await reloadPipelines()
  } else {
    await pipelineCardReload()
  }
}

onMounted(async () => {
  mappings.value = await getTransformMappingList()
})

defineExpose({ refresh: reloadAll })
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
