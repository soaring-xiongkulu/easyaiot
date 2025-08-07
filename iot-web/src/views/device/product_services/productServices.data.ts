import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '服务id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '服务编码:支持英文大小写、数字、下划线和中划线',
    dataIndex: 'serviceCode',
    width: 160,
  },
  {
    title: '服务名称',
    dataIndex: 'serviceName',
    width: 160,
  },
  {
    title: '产品模版标识',
    dataIndex: 'templateCode',
    width: 160,
  },
  {
    title: '产品标识',
    dataIndex: 'pid',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
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
    label: '服务编码:支持英文大小写、数字、下划线和中划线',
    field: 'serviceCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '服务名称',
    field: 'serviceName',
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
    label: '产品标识',
    field: 'pid',
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
    label: '描述',
    field: 'description',
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
    label: '服务编码:支持英文大小写、数字、下划线和中划线',
    field: 'serviceCode',
    required: true,
    component: 'Input',
  },
  {
    label: '服务名称',
    field: 'serviceName',
    required: true,
    component: 'Input',
  },
  {
    label: '产品模版标识',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
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
    label: '服务编码:支持英文大小写、数字、下划线和中划线',
    field: 'serviceCode',
    required: true,
    component: 'Input',
  },
  {
    label: '服务名称',
    field: 'serviceName',
    required: true,
    component: 'Input',
  },
  {
    label: '产品模版标识',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
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
