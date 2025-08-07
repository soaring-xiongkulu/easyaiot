import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '应用ID',
    dataIndex: 'appId',
    width: 160,
  },
  {
    title: '产品模版标识',
    dataIndex: 'templateCode',
    width: 160,
  },
  {
    title: '模板名称',
    dataIndex: 'templateName',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 160,
  },
  {
    title: '产品模型模板描述',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '创建者',
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
    title: '更新者',
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
    label: '产品模版标识',
    field: 'templateCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '模板名称',
    field: 'templateName',
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
    label: '产品模型模板描述',
    field: 'remark',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '创建者',
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
    label: '更新者',
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
    label: '产品模版标识',
    field: 'templateCode',
    required: true,
    component: 'Input',
  },
  {
    label: '模板名称',
    field: 'templateName',
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
    label: '产品模型模板描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建者',
    field: 'createBy',
    component: 'Input',
  },
  {
    label: '更新者',
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
    label: '产品模版标识',
    field: 'templateCode',
    required: true,
    component: 'Input',
  },
  {
    label: '模板名称',
    field: 'templateName',
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
    label: '产品模型模板描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '创建者',
    field: 'createBy',
    component: 'Input',
  },
  {
    label: '更新者',
    field: 'updateBy',
    component: 'Input',
  },
]
