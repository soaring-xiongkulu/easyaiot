import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '设备标识',
    dataIndex: 'did',
    width: 160,
  },
  {
    title: 'Topic类型',
    dataIndex: 'type',
    width: 160,
  },
  {
    title: 'topic',
    dataIndex: 'topic',
    width: 160,
  },
  {
    title: '发布者',
    dataIndex: 'publisher',
    width: 160,
  },
  {
    title: '订阅者',
    dataIndex: 'subscriber',
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
  {
    title: '备注',
    dataIndex: 'remark',
    width: 160,
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '设备标识',
    field: 'did',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: 'Topic类型',
    field: 'type',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: 'topic',
    field: 'topic',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '发布者',
    field: 'publisher',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '订阅者',
    field: 'subscriber',
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
  {
    label: '备注',
    field: 'remark',
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
    label: '设备标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: 'Topic类型',
    field: 'type',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: 'topic',
    field: 'topic',
    component: 'Input',
  },
  {
    label: '发布者',
    field: 'publisher',
    component: 'Input',
  },
  {
    label: '订阅者',
    field: 'subscriber',
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
  {
    label: '备注',
    field: 'remark',
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
    label: '设备标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: 'Topic类型',
    field: 'type',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: 'topic',
    field: 'topic',
    component: 'Input',
  },
  {
    label: '发布者',
    field: 'publisher',
    component: 'Input',
  },
  {
    label: '订阅者',
    field: 'subscriber',
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
  {
    label: '备注',
    field: 'remark',
    component: 'Input',
  },
]
