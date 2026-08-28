<script lang="ts" setup>
/**
 * 待办 / 已办任务列表（共用组件，按 type 区分列与操作）
 */
import { useRouter } from 'vue-router'
import { Tag } from 'ant-design-vue'
import type { FormSchema } from '@/components/Table'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { getTaskDonePage, getTaskTodoPage } from '@/api/flow/task'
import { formatToDateTime } from '@/utils/dateUtil'

defineOptions({ name: 'FlowTaskTable' })

const props = defineProps<{
  type: 'todo' | 'done'
}>()

const router = useRouter()

const todoColumns = [
  { title: '流程名称', dataIndex: 'processInstanceName', width: 240 },
  { title: '当前节点', dataIndex: 'name', width: 160 },
  { title: '发起人', dataIndex: 'startUser', width: 120 },
  { title: '发起时间', dataIndex: 'createTime', width: 170 },
  { title: '等待时长', dataIndex: 'durationInMillis', width: 120 },
]

const doneColumns = [
  { title: '流程名称', dataIndex: 'processInstanceName', width: 240 },
  { title: '审批节点', dataIndex: 'name', width: 160 },
  { title: '发起人', dataIndex: 'startUser', width: 120 },
  { title: '审批意见', dataIndex: 'reason', width: 200 },
  { title: '结果', dataIndex: 'status', width: 90 },
  { title: '完成时间', dataIndex: 'endTime', width: 170 },
]

const searchFormSchema: FormSchema[] = [
  { label: '流程名称', field: 'processInstanceName', component: 'Input', colProps: { span: 8 } },
]

const [registerTable] = useTable({
  api: props.type === 'todo' ? getTaskTodoPage : getTaskDonePage,
  columns: props.type === 'todo' ? todoColumns : doneColumns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: { width: 120, title: '操作', dataIndex: 'action', fixed: 'right' },
})

const TASK_STATUS_MAP: Record<number, { text: string; color: string }> = {
  0: { text: '待审批', color: 'orange' },
  1: { text: '审批中', color: 'processing' },
  2: { text: '通过', color: 'success' },
  3: { text: '拒绝', color: 'error' },
  4: { text: '已取消', color: 'default' },
  5: { text: '已退回', color: 'warning' },
  7: { text: '审批中', color: 'processing' },
}

function formatDuration(millis: number) {
  if (!millis) {
    return '—'
  }
  const minutes = Math.floor(millis / 60000)
  if (minutes < 60) {
    return `${minutes} 分钟`
  }
  const hours = Math.floor(minutes / 60)
  if (hours < 24) {
    return `${hours} 小时`
  }
  return `${Math.floor(hours / 24)} 天`
}

function handleApprove(record: Recordable) {
  router.push({ path: '/flow/process-instance/detail', query: { id: record.processInstanceId, taskId: record.id } })
}
</script>

<template>
  <BasicTable @register="registerTable">
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'startUser'">
        <span>{{ record.startUser?.nickname || '系统发起' }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'createTime'">
        <span>{{ record.createTime ? formatToDateTime(record.createTime) : '—' }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'endTime'">
        <span>{{ record.endTime ? formatToDateTime(record.endTime) : '—' }}</span>
      </template>
      <template v-else-if="column.dataIndex === 'durationInMillis'">
        <Tag :color="formatDuration(record.durationInMillis) === '—' ? 'default' : 'blue'">
          {{ formatDuration(record.durationInMillis) }}
        </Tag>
      </template>
      <template v-else-if="column.dataIndex === 'status'">
        <Tag :color="TASK_STATUS_MAP[record.status]?.color ?? 'default'">
          {{ TASK_STATUS_MAP[record.status]?.text ?? record.status }}
        </Tag>
      </template>
      <template v-else-if="column.dataIndex === 'reason'">
        <span :title="record.reason">{{ record.reason || '—' }}</span>
      </template>
      <template v-else-if="column.key === 'action'">
        <TableAction
          :actions="[
            {
              icon: props.type === 'todo' ? 'ant-design:audit-outlined' : 'ant-design:eye-outlined',
              label: props.type === 'todo' ? '审批' : '详情',
              onClick: handleApprove.bind(null, record),
            },
          ]"
        />
      </template>
    </template>
  </BasicTable>
</template>
