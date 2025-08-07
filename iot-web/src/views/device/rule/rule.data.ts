import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '主键',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '应用ID',
    dataIndex: 'appId',
    width: 160,
  },
  {
    title: '规则标识',
    dataIndex: 'ruleCode',
    width: 160,
  },
  {
    title: '规则名称',
    dataIndex: 'ruleName',
    width: 160,
  },
  {
    title: '任务标识',
    dataIndex: 'jobCode',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 160,
  },
  {
    title: '触发机制',
    dataIndex: 'triggering',
    width: 160,
  },
  {
    title: '规则描述，可以为空',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '创建人',
    dataIndex: 'createBy',
    width: 160,
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '更新人',
    dataIndex: 'updateBy',
    width: 160,
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '应用ID',
    field: 'appId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '规则标识',
    field: 'ruleCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '规则名称',
    field: 'ruleName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '任务标识',
    field: 'jobCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '状态',
    field: 'status',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '触发机制',
    field: 'triggering',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '规则描述，可以为空',
    field: 'remark',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '创建人',
    field: 'createBy',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '创建时间',
    field: 'createTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '更新人',
    field: 'updateBy',
    component: 'Input',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '规则标识',
    field: 'ruleCode',
    required: true,
    component: 'Input',
  },
  {
    label: '规则名称',
    field: 'ruleName',
    required: true,
    component: 'Input',
  },
  {
    label: '任务标识',
    field: 'jobCode',
    required: true,
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '触发机制',
    field: 'triggering',
    component: 'Input',
  },
  {
    label: '规则描述，可以为空',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建人',
    field: 'createBy',
    component: 'Input',
  },
  {
    label: '更新人',
    field: 'updateBy',
    component: 'Input',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '规则标识',
    field: 'ruleCode',
    required: true,
    component: 'Input',
  },
  {
    label: '规则名称',
    field: 'ruleName',
    required: true,
    component: 'Input',
  },
  {
    label: '任务标识',
    field: 'jobCode',
    required: true,
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '触发机制',
    field: 'triggering',
    component: 'Input',
  },
  {
    label: '规则描述，可以为空',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建人',
    field: 'createBy',
    component: 'Input',
  },
  {
    label: '更新人',
    field: 'updateBy',
    component: 'Input',
  },
]
