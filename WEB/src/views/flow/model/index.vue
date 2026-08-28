<script lang="ts" setup>
/**
 * FLOW 流程模型管理：列表 + 新建（弹窗）+ 设计（跳设计器页）+ 发布/停用 + 删除
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Form, FormItem, Input, Modal, Select, Tag, Textarea } from 'ant-design-vue'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import type { FormSchema } from '@/components/Table'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import { Icon } from '@/components/Icon'
import { createModel, deleteModel, deployModel, getModelPage, updateModelState } from '@/api/flow/model'
import { getCategorySimpleList } from '@/api/flow/common'

defineOptions({ name: 'FlowModel' })

const router = useRouter()
const { createMessage, createConfirm } = useMessage()

const categoryOptions = ref<{ label: string; value: string }[]>([])

const columns = [
  { title: '流程名称', dataIndex: 'name', width: 260 },
  { title: '流程标识', dataIndex: 'key', width: 180 },
  { title: '分类', dataIndex: 'category', width: 120 },
  { title: '表单类型', dataIndex: 'formType', width: 100 },
  { title: '最近部署', dataIndex: 'processDefinition', width: 200 },
  { title: '状态', dataIndex: 'suspensionState', width: 90 },
  { title: '更新时间', dataIndex: 'updateTime', width: 170 },
]

const searchFormSchema: FormSchema[] = [
  { label: '流程名称', field: 'name', component: 'Input', colProps: { span: 8 } },
  {
    label: '分类',
    field: 'category',
    component: 'Select',
    componentProps: { options: categoryOptions, allowClear: true },
    colProps: { span: 8 },
  },
]

const [registerTable, { reload }] = useTable({
  title: '流程模型',
  api: getModelPage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: { width: 220, title: '操作', dataIndex: 'action', fixed: 'right' },
})

onMounted(async () => {
  const list = await getCategorySimpleList().catch(() => [])
  categoryOptions.value = (list ?? []).map((item: any) => ({ label: item.name, value: item.code ?? item.id }))
})

function handleDesign(record: Recordable) {
  router.push(`/flow/model/design/${record.id}`)
}

// ---------- 新建模型 ----------
const createModalOpen = ref(false)
const createForm = ref<{ name: string; key: string; category?: string; description: string }>({
  name: '',
  key: '',
  category: undefined,
  description: '',
})

function openCreate() {
  createForm.value = { name: '', key: '', category: undefined, description: '' }
  createModalOpen.value = true
}

async function handleCreateSubmit() {
  if (!createForm.value.name || !createForm.value.key) {
    createMessage.warning('请填写流程名称与流程标识')
    return
  }
  const id = await createModel({
    name: createForm.value.name,
    key: createForm.value.key,
    category: createForm.value.category,
    description: createForm.value.description,
    formType: 20,
    type: 10,
  })
  createModalOpen.value = false
  createMessage.success('创建成功，开始设计流程')
  router.push(`/flow/model/design/${id}`)
}

// ---------- 发布 / 停用 / 删除 ----------
async function handleDeploy(record: Recordable) {
  await deployModel(record.id)
  createMessage.success('部署成功')
  reload()
}

async function handleToggleState(record: Recordable) {
  const state = record.suspensionState === 1 ? 2 : 1
  await updateModelState(record.id, state)
  createMessage.success(state === 2 ? '已挂起' : '已激活')
  reload()
}

function handleDelete(record: Recordable) {
  createConfirm({
    title: '删除流程模型',
    iconType: 'warning',
    content: `确定删除流程「${record.name}」吗？已部署的流程定义不受影响。`,
    async onOk() {
      await deleteModel(record.id)
      createMessage.success('删除成功')
      reload()
    },
  })
}
</script>

<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <Button v-auth="['flow:model:create']" type="primary" preIcon="ant-design:plus-outlined" @click="openCreate">
          新建流程
        </Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'name'">
          <div class="flow-model__name">
            <div class="flow-model__icon">
              <Icon icon="ant-design:partition-outlined" />
            </div>
            <div>
              <div class="flow-model__title">{{ record.name }}</div>
              <div class="flow-model__desc">{{ record.description || '—' }}</div>
            </div>
          </div>
        </template>
        <template v-else-if="column.dataIndex === 'formType'">
          <Tag color="blue">业务表单</Tag>
        </template>
        <template v-else-if="column.dataIndex === 'processDefinition'">
          <template v-if="record.processDefinition">
            <div>v{{ record.processDefinition.version }}</div>
            <div class="flow-model__deploy-time">{{ record.processDefinition.deploymentTime || '—' }}</div>
          </template>
          <span v-else class="flow-model__undeployed">未部署</span>
        </template>
        <template v-else-if="column.dataIndex === 'suspensionState'">
          <Tag :color="record.suspensionState === 2 ? 'red' : 'green'">
            {{ record.suspensionState === 2 ? '已挂起' : '已激活' }}
          </Tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:edit-outlined',
                label: '设计',
                auth: 'flow:model:update',
                onClick: handleDesign.bind(null, record),
              },
              {
                icon: 'ant-design:cloud-upload-outlined',
                label: record.processDefinition ? '重新部署' : '发布',
                auth: 'flow:model:deploy',
                popConfirm: {
                  title: '确认发布该流程？发布后即可被告警规则引用',
                  confirm: handleDeploy.bind(null, record),
                },
              },
            ]"
            :drop-down-actions="[
              {
                icon: record.suspensionState === 2 ? 'ant-design:play-circle-outlined' : 'ant-design:pause-circle-outlined',
                label: record.suspensionState === 2 ? '激活' : '挂起',
                auth: 'flow:model:update',
                onClick: handleToggleState.bind(null, record),
              },
              {
                icon: 'ant-design:delete-outlined',
                label: '删除',
                danger: true,
                auth: 'flow:model:delete',
                onClick: handleDelete.bind(null, record),
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>

    <Modal
      v-model:open="createModalOpen"
      title="新建流程模型"
      :width="480"
      ok-text="创建并设计"
      cancel-text="取消"
      @ok="handleCreateSubmit"
    >
      <Form layout="vertical" style="margin-top: 12px">
        <FormItem label="流程名称" required>
          <Input v-model:value="createForm.name" placeholder="如：告警处理-周界入侵" :maxlength="30" show-count />
        </FormItem>
        <FormItem label="流程标识" required>
          <Input v-model:value="createForm.key" placeholder="如 alarm-handle-perimeter（字母开头，仅含字母数字-）" />
        </FormItem>
        <FormItem label="分类">
          <Select
            v-model:value="createForm.category"
            placeholder="请选择分类"
            :options="categoryOptions"
            allow-clear
          />
        </FormItem>
        <FormItem label="描述">
          <Textarea v-model:value="createForm.description" :rows="3" placeholder="流程用途说明" />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<style lang="less" scoped>
.flow-model__name {
  display: flex;
  gap: 10px;
  align-items: center;
}

.flow-model__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #e8f1ff;
  color: #0a7cff;
  font-size: 18px;
  flex-shrink: 0;
}

.flow-model__title {
  color: #1f2d3d;
  font-weight: 600;
}

.flow-model__desc {
  max-width: 220px;
  overflow: hidden;
  color: #8c94a5;
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.flow-model__deploy-time {
  color: #8c94a5;
  font-size: 12px;
}

.flow-model__undeployed {
  color: #ff943e;
  font-size: 12px;
}
</style>
