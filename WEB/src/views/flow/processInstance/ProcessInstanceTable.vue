<script lang="ts" setup>
/**
 * 流程实例列表（type=my 我发起的 / type=manager 管理员全部）
 */
import { useRouter } from 'vue-router'
import { Tag } from 'ant-design-vue'
import type { FormSchema } from '@/components/Table'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { useMessage } from '@/hooks/web/useMessage'
import { cancelProcessInstanceByAdmin, cancelProcessInstanceByStartUser, getManagerProcessInstancePage, getMyProcessInstancePage } from '@/api/flow/processInstance'
import { formatToDateTime } from '@/utils/dateUtil'

defineOptions({ name: 'FlowProcessInstanceTable' })

const props = defineProps<{
  type: 'my' | 'manager'
}>()

const router = useRouter()
const { createMessage, createConfirm } = useMessage()

const columns = [
  { title: '流程名称', dataIndex: 'name', width: 260 },
  { title: '流程分类', dataIndex: 'processDefinitionName', width: 180 },
  { title: '发起人', dataIndex: 'startUser', width: 110 },
  { title: '发起时间', dataIndex: 'startTime', width: 170 },
  { title: '当前节点', dataIndex: 'taskName', width: 150 },
  { title: '状态', dataIndex: 'status', width: 100 },
  { title: '结束时间', dataIndex: 'endTime', width: 170 },
]

const searchFormSchema: FormSchema[] = [
  { label: '流程名称', field: 'name', component: 'Input', colProps: { span: 8 } },
]

const cancelByStartUser = props.type === 'my'

const [registerTable, { reload }] = useTable({
  api: props.type === 'my' ? getMyProcessInstancePage : getManagerProcessInstancePage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: { width: 140, title: '操作', dataIndex: 'action', fixed: 'right' },
})

const INSTANCE_STATUS: Record<number, { text: string; color: string }> = {
  1: { text: '审批中', color: 'processing' },
  2: { text: '已通过', color: 'success' },
  3: { text: '已拒绝', color: 'error' },
  4: { text: '已取消', color: 'default' },
}

function handleView(record: Recordable) {
  router.push({ path: '/flow/process-instance/detail', query: { id: record.id } })
}

function handleCancel(record: Recordable) {
  let reason = ''
  createConfirm({
    title: '取消流程',
    iconType: 'warning',
    content: '确定取消该流程实例吗？取消后立即终止流转。',
    async onOk() {
      reason = '手动取消'
      if (props.type === 'my') {
        await cancelProcessInstanceByStartUser(record.id, reason)
      }
      else {
        await cancelProcessInstanceByAdmin(record.id, reason)
      }
      createMessage.success('已取消')
      reload()
    },
  })
}
</script>

<template>
  <BasicTable @register="registerTable">
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'startUser'">
        <span>{{ typeof record.startUser === 'object' ? record.startUser?.nickname : (record.startUserNickname || '系统发起') }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'startTime'">
        <span>{{ record.startTime ? formatToDateTime(record.startTime) : '—' }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'endTime'">
        <span>{{ record.endTime ? formatToDateTime(record.endTime) : '—' }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'status'">
        <Tag :color="INSTANCE_STATUS[record.status]?.color ?? 'default'">
          {{ INSTANCE_STATUS[record.status]?.text ?? record.status }}
        </Tag>
      </template>
      <template v-else-if="column.dataIndex === 'taskName'">
        <span>{{ record.taskName || '—' }}</span>
      </template>
      <template v-else-if="column.key === 'action'">
        <TableAction
          :actions="[
            {
              icon: 'ant-design:eye-outlined',
              label: '详情',
              onClick: handleView.bind(null, record),
            },
          ]"
          :drop-down-actions="record.status === 1
            ? [
                {
                  icon: 'ant-design:stop-outlined',
                  label: '取消流程',
                  danger: true,
                  auth: cancelByStartUser ? 'flow:process-instance:cancel' : 'flow:process-instance:cancel-by-admin',
                  onClick: handleCancel.bind(null, record),
                },
              ]
            : []"
        />
      </template>
    </template>
  </BasicTable>
</template>
