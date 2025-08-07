import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '规则告警ID',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '规则ID',
    dataIndex: 'ruleId',
    width: 160,
  },
  {
    title: '规则名称',
    dataIndex: 'ruleAlarmName',
    width: 160,
  },
  {
    title: '告警状态',
    dataIndex: 'ruleAlarmStatus',
    width: 160,
  },
  {
    title: '规则描述',
    dataIndex: 'ruleAlarmRemark',
    width: 160,
  },
  {
    title: '告警级别',
    dataIndex: 'ruleLevel',
    width: 160,
  },
  {
    title: '通知方式',
    dataIndex: 'noticeType',
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
    label: '规则名称',
    field: 'ruleAlarmName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '告警状态',
    field: 'ruleAlarmStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '规则描述',
    field: 'ruleAlarmRemark',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '告警级别',
    field: 'ruleLevel',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '通知方式',
    field: 'noticeType',
    component: 'Select',
    componentProps: {
      options: [],
    },
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
    component: 'Input',
  },
  {
    label: '规则名称',
    field: 'ruleAlarmName',
    component: 'Input',
  },
  {
    label: '告警状态',
    field: 'ruleAlarmStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '规则描述',
    field: 'ruleAlarmRemark',
    component: 'Input',
  },
  {
    label: '告警级别',
    field: 'ruleLevel',
    component: 'Input',
  },
  {
    label: '通知方式',
    field: 'noticeType',
    component: 'Select',
    componentProps: {
      options: [],
    },
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
    component: 'Input',
  },
  {
    label: '规则名称',
    field: 'ruleAlarmName',
    component: 'Input',
  },
  {
    label: '告警状态',
    field: 'ruleAlarmStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '规则描述',
    field: 'ruleAlarmRemark',
    component: 'Input',
  },
  {
    label: '告警级别',
    field: 'ruleLevel',
    component: 'Input',
  },
  {
    label: '通知方式',
    field: 'noticeType',
    component: 'Select',
    componentProps: {
      options: [],
    },
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
