import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '主键',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '升级包IDota_upgrades表',
    dataIndex: 'upgradeId',
    width: 160,
  },
  {
    title: '任务名称',
    dataIndex: 'taskName',
    width: 160,
  },
  {
    title: '任务状态',
    dataIndex: 'taskStatus',
    width: 160,
  },
  {
    title: '计划执行时间',
    dataIndex: 'scheduledTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '任务描述',
    dataIndex: 'description',
    width: 160,
  },
  {
    title: '描述',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '创建人',
    dataIndex: 'createdBy',
    width: 160,
  },
  {
    title: '创建时间',
    dataIndex: 'createdTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '更新人',
    dataIndex: 'updatedBy',
    width: 160,
  },
  {
    title: '更新时间',
    dataIndex: 'updatedTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '升级包IDota_upgrades表',
    field: 'upgradeId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '任务名称',
    field: 'taskName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '任务状态',
    field: 'taskStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '计划执行时间',
    field: 'scheduledTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '任务描述',
    field: 'description',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '描述',
    field: 'remark',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '创建时间',
    field: 'createdTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '更新人',
    field: 'updatedBy',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '更新时间',
    field: 'updatedTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
]

export const createFormSchema: FormSchema[] = [
  {
    label: '编号',
    field: 'id',
    show: false,
    component: 'Input',
  },
  {
    label: '升级包IDota_upgrades表',
    field: 'upgradeId',
    required: true,
    component: 'Input',
  },
  {
    label: '任务名称',
    field: 'taskName',
    required: true,
    component: 'Input',
  },
  {
    label: '任务状态',
    field: 'taskStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '计划执行时间',
    field: 'scheduledTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '任务描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
  },
  {
    label: '创建时间',
    field: 'createdTime',
    required: true,
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '更新人',
    field: 'updatedBy',
    component: 'Input',
  },
  {
    label: '更新时间',
    field: 'updatedTime',
    required: true,
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
]

export const updateFormSchema: FormSchema[] = [
  {
    label: '编号',
    field: 'id',
    show: false,
    component: 'Input',
  },
  {
    label: '升级包IDota_upgrades表',
    field: 'upgradeId',
    required: true,
    component: 'Input',
  },
  {
    label: '任务名称',
    field: 'taskName',
    required: true,
    component: 'Input',
  },
  {
    label: '任务状态',
    field: 'taskStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '计划执行时间',
    field: 'scheduledTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '任务描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
  },
  {
    label: '创建时间',
    field: 'createdTime',
    required: true,
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '更新人',
    field: 'updatedBy',
    component: 'Input',
  },
  {
    label: '更新时间',
    field: 'updatedTime',
    required: true,
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
]
