import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '主键',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '任务ID',
    dataIndex: 'taskId',
    width: 160,
  },
  {
    title: '设备标识',
    dataIndex: 'did',
    width: 160,
  },
  {
    title: '升级状态',
    dataIndex: 'upgradeStatus',
    width: 160,
  },
  {
    title: '升级进度（百分比）',
    dataIndex: 'progress',
    width: 160,
  },
  {
    title: '错误代码',
    dataIndex: 'errorCode',
    width: 160,
  },
  {
    title: '错误信息',
    dataIndex: 'errorMessage',
    width: 160,
  },
  {
    title: '升级开始时间',
    dataIndex: 'startTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '升级结束时间',
    dataIndex: 'endTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '升级成功详细信息',
    dataIndex: 'successDetails',
    width: 160,
  },
  {
    title: '升级失败详细信息',
    dataIndex: 'failureDetails',
    width: 160,
  },
  {
    title: '升级过程日志',
    dataIndex: 'logDetails',
    width: 160,
  },
  {
    title: '描述',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '记录创建时间',
    dataIndex: 'createdTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '创建人',
    dataIndex: 'createdBy',
    width: 160,
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
    label: '任务ID',
    field: 'taskId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备标识',
    field: 'did',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级状态',
    field: 'upgradeStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '升级进度（百分比）',
    field: 'progress',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '错误代码',
    field: 'errorCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '错误信息',
    field: 'errorMessage',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级开始时间',
    field: 'startTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '升级结束时间',
    field: 'endTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '升级成功详细信息',
    field: 'successDetails',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级失败详细信息',
    field: 'failureDetails',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '升级过程日志',
    field: 'logDetails',
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
    label: '记录创建时间',
    field: 'createdTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
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
    label: '任务ID',
    field: 'taskId',
    required: true,
    component: 'Input',
  },
  {
    label: '设备标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: '升级状态',
    field: 'upgradeStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '升级进度（百分比）',
    field: 'progress',
    required: true,
    component: 'Input',
  },
  {
    label: '错误代码',
    field: 'errorCode',
    component: 'Input',
  },
  {
    label: '错误信息',
    field: 'errorMessage',
    component: 'Input',
  },
  {
    label: '升级开始时间',
    field: 'startTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '升级结束时间',
    field: 'endTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '升级成功详细信息',
    field: 'successDetails',
    component: 'Input',
  },
  {
    label: '升级失败详细信息',
    field: 'failureDetails',
    component: 'Input',
  },
  {
    label: '升级过程日志',
    field: 'logDetails',
    component: 'Input',
  },
  {
    label: '描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '记录创建时间',
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
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
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
    label: '任务ID',
    field: 'taskId',
    required: true,
    component: 'Input',
  },
  {
    label: '设备标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: '升级状态',
    field: 'upgradeStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '升级进度（百分比）',
    field: 'progress',
    required: true,
    component: 'Input',
  },
  {
    label: '错误代码',
    field: 'errorCode',
    component: 'Input',
  },
  {
    label: '错误信息',
    field: 'errorMessage',
    component: 'Input',
  },
  {
    label: '升级开始时间',
    field: 'startTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '升级结束时间',
    field: 'endTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '升级成功详细信息',
    field: 'successDetails',
    component: 'Input',
  },
  {
    label: '升级失败详细信息',
    field: 'failureDetails',
    component: 'Input',
  },
  {
    label: '升级过程日志',
    field: 'logDetails',
    component: 'Input',
  },
  {
    label: '描述',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '记录创建时间',
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
    label: '创建人',
    field: 'createdBy',
    component: 'Input',
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
