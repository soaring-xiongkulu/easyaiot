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
    title: '产品标识',
    dataIndex: 'pid',
    width: 160,
  },
  {
    title: '协议名称',
    dataIndex: 'protocolName',
    width: 160,
  },
  {
    title: '协议标识',
    dataIndex: 'protocolCode',
    width: 160,
  },
  {
    title: '协议版本',
    dataIndex: 'protocolVersion',
    width: 160,
  },
  {
    title: '协议类型',
    dataIndex: 'protocolType',
    width: 160,
  },
  {
    title: '协议语言',
    dataIndex: 'protocolVoice',
    width: 160,
  },
  {
    title: '类名',
    dataIndex: 'className',
    width: 160,
  },
  {
    title: '文件地址',
    dataIndex: 'filePath',
    width: 160,
  },
  {
    title: '内容',
    dataIndex: 'content',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
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
    label: '应用ID',
    field: 'appId',
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
    label: '协议名称',
    field: 'protocolName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '协议标识',
    field: 'protocolCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '协议版本',
    field: 'protocolVersion',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '协议类型',
    field: 'protocolType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '协议语言',
    field: 'protocolVoice',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '类名',
    field: 'className',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '文件地址',
    field: 'filePath',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '内容',
    field: 'content',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
    required: true,
    component: 'Input',
  },
  {
    label: '协议名称',
    field: 'protocolName',
    component: 'Input',
  },
  {
    label: '协议标识',
    field: 'protocolCode',
    component: 'Input',
  },
  {
    label: '协议版本',
    field: 'protocolVersion',
    component: 'Input',
  },
  {
    label: '协议类型',
    field: 'protocolType',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '协议语言',
    field: 'protocolVoice',
    component: 'Input',
  },
  {
    label: '类名',
    field: 'className',
    component: 'Input',
  },
  {
    label: '文件地址',
    field: 'filePath',
    component: 'Input',
  },
  {
    label: '内容',
    field: 'content',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
    required: true,
    component: 'Input',
  },
  {
    label: '协议名称',
    field: 'protocolName',
    component: 'Input',
  },
  {
    label: '协议标识',
    field: 'protocolCode',
    component: 'Input',
  },
  {
    label: '协议版本',
    field: 'protocolVersion',
    component: 'Input',
  },
  {
    label: '协议类型',
    field: 'protocolType',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '协议语言',
    field: 'protocolVoice',
    component: 'Input',
  },
  {
    label: '类名',
    field: 'className',
    component: 'Input',
  },
  {
    label: '文件地址',
    field: 'filePath',
    component: 'Input',
  },
  {
    label: '内容',
    field: 'content',
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
