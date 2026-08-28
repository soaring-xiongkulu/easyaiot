<script lang="ts" setup>
/**
 * 流程定义列表（已部署版本的查询）
 */
import { Tag } from 'ant-design-vue'
import type { FormSchema } from '@/components/Table'
import { BasicTable, useTable } from '@/components/Table'
import { getProcessDefinitionPage } from '@/api/flow/definition'

defineOptions({ name: 'FlowDefinition' })

const columns = [
  { title: '定义编号', dataIndex: 'id', width: 220 },
  { title: '流程标识', dataIndex: 'key', width: 180 },
  { title: '流程名称', dataIndex: 'name', width: 220 },
  { title: '版本', dataIndex: 'version', width: 90 },
  { title: '状态', dataIndex: 'suspensionState', width: 100 },
  { title: '部署时间', dataIndex: 'deploymentTime', width: 180 },
]

const searchFormSchema: FormSchema[] = [
  { label: '流程标识', field: 'key', component: 'Input', colProps: { span: 8 } },
  { label: '流程名称', field: 'name', component: 'Input', colProps: { span: 8 } },
]

const [registerTable] = useTable({
  title: '流程定义',
  api: getProcessDefinitionPage,
  columns,
  formConfig: { labelWidth: 100, schemas: searchFormSchema },
  useSearchForm: true,
  showTableSetting: true,
})
</script>

<template>
  <div>
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'version'">
          <Tag color="blue">v{{ record.version }}.0</Tag>
        </template>
        <template v-else-if="column.dataIndex === 'suspensionState'">
          <Tag :color="record.suspensionState === 2 ? 'red' : 'green'">
            {{ record.suspensionState === 2 ? '已挂起' : '已激活' }}
          </Tag>
        </template>
      </template>
    </BasicTable>
  </div>
</template>
