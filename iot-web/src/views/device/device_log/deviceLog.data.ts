import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '设备唯一标识',
    dataIndex: 'did',
    width: 160,
  },
  {
    title: '文件地址',
    dataIndex: 'fileUrl',
    width: 160,
  },
  {
    title: '上传时间',
    dataIndex: 'uploadTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '文件名称',
    dataIndex: 'fileName',
    width: 160,
  },
  {
    title: '文件大小',
    dataIndex: 'fileSize',
    width: 160,
  },
  {
    title: '备注',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 160,
  },
  {
    title: '创建者',
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
    title: '更新者',
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
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '文件地址',
    field: 'fileUrl',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '上传时间',
    field: 'uploadTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '文件名称',
    field: 'fileName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '文件大小',
    field: 'fileSize',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '备注',
    field: 'remark',
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
    label: '创建者',
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
    label: '更新者',
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
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
  },
  {
    label: '文件地址',
    field: 'fileUrl',
    component: 'Input',
  },
  {
    label: '上传时间',
    field: 'uploadTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '文件名称',
    field: 'fileName',
    component: 'Input',
  },
  {
    label: '文件大小',
    field: 'fileSize',
    component: 'Input',
  },
  {
    label: '备注',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '创建者',
    field: 'createdBy',
    component: 'Input',
  },
  {
    label: '创建时间',
    field: 'createdTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '更新者',
    field: 'updatedBy',
    component: 'Input',
  },
  {
    label: '更新时间',
    field: 'updatedTime',
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
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
  },
  {
    label: '文件地址',
    field: 'fileUrl',
    component: 'Input',
  },
  {
    label: '上传时间',
    field: 'uploadTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '文件名称',
    field: 'fileName',
    component: 'Input',
  },
  {
    label: '文件大小',
    field: 'fileSize',
    component: 'Input',
  },
  {
    label: '备注',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '创建者',
    field: 'createdBy',
    component: 'Input',
  },
  {
    label: '创建时间',
    field: 'createdTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '更新者',
    field: 'updatedBy',
    component: 'Input',
  },
  {
    label: '更新时间',
    field: 'updatedTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
]
