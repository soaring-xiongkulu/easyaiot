import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '事件名称',
    dataIndex: 'eventName',
    width: 160,
  },
  {
    title: '事件code',
    dataIndex: 'eventCode',
    width: 160,
  },
  {
    title: '事件类型',
    dataIndex: 'eventType',
    width: 160,
  },
  {
    title: '模板code',
    dataIndex: 'templateCode',
    width: 160,
  },
  {
    title: '产品唯一标识',
    dataIndex: 'pid',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'enabledStatus',
    width: 160,
  },
  {
    title: '描述',
    dataIndex: 'description',
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
    label: '事件名称',
    field: 'eventName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '事件code',
    field: 'eventCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '事件类型',
    field: 'eventType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '状态',
    field: 'enabledStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '描述',
    component: 'Input',
    field: 'description',
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
    label: '事件名称',
    field: 'eventName',
    required: true,
    component: 'Input',
  },
  {
    label: '事件code',
    field: 'eventCode',
    required: true,
    component: 'Input',
  },
  {
    label: '事件类型',
    field: 'eventType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'enabledStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '描述',
    field: 'description',
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
    label: '事件名称',
    field: 'eventName',
    required: true,
    component: 'Input',
  },
  {
    label: '事件code',
    field: 'eventCode',
    required: true,
    component: 'Input',
  },
  {
    label: '事件类型',
    field: 'eventType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'enabledStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '描述',
    field: 'description',
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
