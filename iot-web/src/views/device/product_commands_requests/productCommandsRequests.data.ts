import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '服务ID',
    dataIndex: 'serviceId',
    width: 160,
  },
  {
    title: '命令ID',
    dataIndex: 'commandsId',
    width: 160,
  },
  {
    title: '数据类型',
    dataIndex: 'datatype',
    width: 160,
  },
  {
    title: '枚举值',
    dataIndex: 'enumlist',
    width: 160,
  },
  {
    title: '最大值',
    dataIndex: 'max',
    width: 160,
  },
  {
    title: '字符串长度',
    dataIndex: 'maxlength',
    width: 160,
  },
  {
    title: '最小值',
    dataIndex: 'min',
    width: 160,
  },
  {
    title: '参数描述',
    dataIndex: 'parameterDescription',
    width: 160,
  },
  {
    title: '参数名称',
    dataIndex: 'parameterName',
    width: 160,
  },
  {
    title: '是否必填',
    dataIndex: 'required',
    width: 160,
  },
  {
    title: '步长。',
    dataIndex: 'step',
    width: 160,
  },
  {
    title: '单位',
    dataIndex: 'unit',
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
    label: '服务ID',
    field: 'serviceId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '命令ID',
    field: 'commandsId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '数据类型',
    field: 'datatype',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '枚举值',
    field: 'enumlist',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '最大值',
    field: 'max',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '字符串长度',
    field: 'maxlength',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '最小值',
    field: 'min',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '参数描述',
    component: 'Input',
    component: 'Input',
    field: 'parameterDescription',
    colProps: { span: 8 },
  },
  {
    label: '参数名称',
    field: 'parameterName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '是否必填',
    field: 'required',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '步长。',
    field: 'step',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '单位',
    field: 'unit',
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
    label: '服务ID',
    field: 'serviceId',
    required: true,
    component: 'Input',
  },
  {
    label: '命令ID',
    field: 'commandsId',
    required: true,
    component: 'Input',
  },
  {
    label: '数据类型',
    field: 'datatype',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '枚举值',
    field: 'enumlist',
    component: 'Input',
  },
  {
    label: '最大值',
    field: 'max',
    component: 'Input',
  },
  {
    label: '字符串长度',
    field: 'maxlength',
    component: 'Input',
  },
  {
    label: '最小值',
    field: 'min',
    component: 'Input',
  },
  {
    label: '参数描述',
    component: 'Input',
    field: 'parameterDescription',
    component: 'Input',
  },
  {
    label: '参数名称',
    field: 'parameterName',
    component: 'Input',
  },
  {
    label: '是否必填',
    field: 'required',
    required: true,
    component: 'Input',
  },
  {
    label: '步长。',
    field: 'step',
    component: 'Input',
  },
  {
    label: '单位',
    field: 'unit',
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
    label: '服务ID',
    field: 'serviceId',
    required: true,
    component: 'Input',
  },
  {
    label: '命令ID',
    field: 'commandsId',
    required: true,
    component: 'Input',
  },
  {
    label: '数据类型',
    field: 'datatype',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '枚举值',
    field: 'enumlist',
    component: 'Input',
  },
  {
    label: '最大值',
    field: 'max',
    component: 'Input',
  },
  {
    label: '字符串长度',
    field: 'maxlength',
    component: 'Input',
  },
  {
    label: '最小值',
    field: 'min',
    component: 'Input',
  },
  {
    label: '参数描述',
    component: 'Input',
    field: 'parameterDescription',
    component: 'Input',
  },
  {
    label: '参数名称',
    field: 'parameterName',
    component: 'Input',
  },
  {
    label: '是否必填',
    field: 'required',
    required: true,
    component: 'Input',
  },
  {
    label: '步长。',
    field: 'step',
    component: 'Input',
  },
  {
    label: '单位',
    field: 'unit',
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
