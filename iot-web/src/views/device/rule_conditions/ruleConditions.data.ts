import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '主键',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '规则ID',
    dataIndex: 'ruleId',
    width: 160,
  },
  {
    title: '条件类型',
    dataIndex: 'conditionType',
    width: 160,
  },
  {
    title: '设备唯一标识',
    dataIndex: 'did',
    width: 160,
  },
  {
    title: '产品标识',
    dataIndex: 'pid',
    width: 160,
  },
  {
    title: '服务ID',
    dataIndex: 'serviceId',
    width: 160,
  },
  {
    title: '属性ID',
    dataIndex: 'propertiesId',
    width: 160,
  },
  {
    title: '比较模式',
    dataIndex: 'comparisonMode',
    width: 160,
  },
  {
    title: '比较值',
    dataIndex: 'comparisonValue',
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
    label: '规则ID',
    field: 'ruleId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '条件类型',
    field: 'conditionType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '设备唯一标识',
    field: 'did',
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
    label: '服务ID',
    field: 'serviceId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '属性ID',
    field: 'propertiesId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '比较模式',
    field: 'comparisonMode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '比较值',
    field: 'comparisonValue',
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
    label: '规则ID',
    field: 'ruleId',
    required: true,
    component: 'Input',
  },
  {
    label: '条件类型',
    field: 'conditionType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
    component: 'Input',
  },
  {
    label: '服务ID',
    field: 'serviceId',
    component: 'Input',
  },
  {
    label: '属性ID',
    field: 'propertiesId',
    component: 'Input',
  },
  {
    label: '比较模式',
    field: 'comparisonMode',
    component: 'Input',
  },
  {
    label: '比较值',
    field: 'comparisonValue',
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
    label: '规则ID',
    field: 'ruleId',
    required: true,
    component: 'Input',
  },
  {
    label: '条件类型',
    field: 'conditionType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
  },
  {
    label: '产品标识',
    field: 'pid',
    component: 'Input',
  },
  {
    label: '服务ID',
    field: 'serviceId',
    component: 'Input',
  },
  {
    label: '属性ID',
    field: 'propertiesId',
    component: 'Input',
  },
  {
    label: '比较模式',
    field: 'comparisonMode',
    component: 'Input',
  },
  {
    label: '比较值',
    field: 'comparisonValue',
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
