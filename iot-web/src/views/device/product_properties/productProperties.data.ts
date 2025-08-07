import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '功能名称',
    dataIndex: 'propertyName',
    width: 160,
  },
  {
    title: '属性code',
    dataIndex: 'propertyCode',
    width: 160,
  },
  {
    title: '数据类型',
    dataIndex: 'datatype',
    width: 160,
  },
  {
    title: '属性描述',
    dataIndex: 'description',
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
    title: '访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE',
    dataIndex: 'method',
    width: 160,
  },
  {
    title: '最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。',
    dataIndex: 'min',
    width: 160,
  },
  {
    title: '本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)',
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
  {
    title: '模版code',
    dataIndex: 'templateCode',
    width: 160,
  },
  {
    title: '产品唯一标识',
    dataIndex: 'pid',
    width: 160,
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '功能名称',
    field: 'propertyName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '属性code',
    field: 'propertyCode',
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
    label: '属性描述',
    component: 'Input',
    field: 'description',
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
    label: '访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE',
    field: 'method',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。',
    field: 'min',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)',
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
  {
    label: '模版code',
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
]

export const createFormSchema: FormSchema[] = [
  {
    label: '编号',
    field: 'id',
    show: false,
    component: 'Input',
  },
  {
    label: '功能名称',
    field: 'propertyName',
    required: true,
    component: 'Input',
  },
  {
    label: '属性code',
    field: 'propertyCode',
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
    label: '属性描述',
    component: 'Input',
    field: 'description',
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
    label: '访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE',
    field: 'method',
    component: 'Input',
  },
  {
    label: '最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。',
    field: 'min',
    component: 'Input',
  },
  {
    label: '本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)',
    field: 'required',
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
  {
    label: '模版code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
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
    label: '功能名称',
    field: 'propertyName',
    required: true,
    component: 'Input',
  },
  {
    label: '属性code',
    field: 'propertyCode',
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
    label: '属性描述',
    component: 'Input',
    field: 'description',
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
    label: '访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE',
    field: 'method',
    component: 'Input',
  },
  {
    label: '最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。',
    field: 'min',
    component: 'Input',
  },
  {
    label: '本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)',
    field: 'required',
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
  {
    label: '模版code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    component: 'Input',
  },
]
