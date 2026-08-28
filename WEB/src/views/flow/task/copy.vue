<script lang="ts" setup>
/**
 * 抄送我的
 */
import { useRouter } from 'vue-router'
import type { FormSchema } from '@/components/Table'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { getProcessInstanceCopyPage } from '@/api/flow/processInstance'

defineOptions({ name: 'FlowTaskCopy' })

const router = useRouter()

const columns = [
  { title: '流程名称', dataIndex: 'processInstanceName', width: 240 },
  { title: '发起人', dataIndex: 'startUser', width: 120 },
  { title: '抄送节点', dataIndex: 'activityName', width: 160 },
  { title: '抄送意见', dataIndex: 'reason', width: 200 },
  { title: '抄送时间', dataIndex: 'createTime', width: 170 },
]

const searchFormSchema: FormSchema[] = [
  { label: '流程名称', field: 'processInstanceName', component: 'Input', colProps: { span: 8 } },
]

const [registerTable] = useTable({
  title: '抄送我的',
  api: getProcessInstanceCopyPage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
  actionColumn: { width: 100, title: '操作', dataIndex: 'action', fixed: 'right' },
})

function handleView(record: Recordable) {
  router.push({ path: '/flow/process-instance/detail', query: { id: record.processInstanceId } })
}
</script>

<template>
  <BasicTable @register="registerTable">
    <template #bodyCell="{ column, record }">
      <template v-if="column.dataIndex === 'startUser'">
        <span>{{ typeof record.startUser === 'object' ? record.startUser?.nickname : record.startUser }}</span>
      </template>
      <template v-else-if="column.key === 'action'">
        <TableAction
          :actions="[
            {
              icon: 'ant-design:eye-outlined',
              label: '查看',
              onClick: handleView.bind(null, record),
            },
          ]"
        />
      </template>
    </template>
  </BasicTable>
</template>
