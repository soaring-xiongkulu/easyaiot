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
    title: '包名称',
    dataIndex: 'packageName',
    width: 160,
  },
  {
    title: '升级包类型',
    dataIndex: 'packageType',
    width: 160,
  },
  {
    title: '产品标识',
    dataIndex: 'productIdentification',
    width: 160,
  },
  {
    title: '升级包版本',
    dataIndex: 'version',
    width: 160,
  },
  {
    title: '升级包地址',
    dataIndex: 'fileLocation',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 160,
  },
  {
    title: '升级包描述',
    dataIndex: 'description',
    width: 160,
  },
  {
    title: '自定义信息',
    dataIndex: 'customInfo',
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
    label: '应用ID',
    field: 'appId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '包名称',
    field: 'packageName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级包类型',
    field: 'packageType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '产品标识',
    field: 'productIdentification',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级包版本',
    field: 'version',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级包地址',
    field: 'fileLocation',
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
    label: '升级包描述',
    field: 'description',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '自定义信息',
    field: 'customInfo',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '包名称',
    field: 'packageName',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包类型',
    field: 'packageType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品标识',
    field: 'productIdentification',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包版本',
    field: 'version',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包地址',
    field: 'fileLocation',
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
    label: '升级包描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '自定义信息',
    field: 'customInfo',
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
    label: '应用ID',
    field: 'appId',
    required: true,
    component: 'Input',
  },
  {
    label: '包名称',
    field: 'packageName',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包类型',
    field: 'packageType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品标识',
    field: 'productIdentification',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包版本',
    field: 'version',
    required: true,
    component: 'Input',
  },
  {
    label: '升级包地址',
    field: 'fileLocation',
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
    label: '升级包描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '自定义信息',
    field: 'customInfo',
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
