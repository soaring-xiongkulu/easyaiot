import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '主键',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '告警时间',
    dataIndex: 'alarmTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '告警名称',
    dataIndex: 'alarmName',
    width: 160,
  },
  {
    title: '告警级别',
    dataIndex: 'alarmLevel',
    width: 160,
  },
  {
    title: '告警描述',
    dataIndex: 'alarmDescribe',
    width: 160,
  },
  {
    title: '处理结果',
    dataIndex: 'processingResult',
    width: 160,
  },
  {
    title: '处理意见',
    dataIndex: 'processingOpinions',
    width: 160,
  },
  {
    title: '告警内容',
    dataIndex: 'alarmContent',
    width: 160,
  },
  {
    title: '处理人',
    dataIndex: 'processingPeople',
    width: 160,
  },
  {
    title: '处理时间',
    dataIndex: 'processingTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '告警时间',
    field: 'alarmTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '告警名称',
    field: 'alarmName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '告警级别',
    field: 'alarmLevel',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '告警描述',
    field: 'alarmDescribe',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '处理结果',
    field: 'processingResult',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '处理意见',
    field: 'processingOpinions',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '告警内容',
    field: 'alarmContent',
    colProps: { span: 8 },
  },
  {
    label: '处理人',
    field: 'processingPeople',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '处理时间',
    field: 'processingTime',
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
    label: '告警时间',
    field: 'alarmTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '告警名称',
    field: 'alarmName',
    component: 'Input',
  },
  {
    label: '告警级别',
    field: 'alarmLevel',
    component: 'Input',
  },
  {
    label: '告警描述',
    field: 'alarmDescribe',
    component: 'Input',
  },
  {
    label: '处理结果',
    field: 'processingResult',
    component: 'Input',
  },
  {
    label: '处理意见',
    field: 'processingOpinions',
    component: 'Input',
  },
  {
    label: '告警内容',
    field: 'alarmContent',
    component: 'Input',
  },
  {
    label: '处理人',
    field: 'processingPeople',
    component: 'Input',
  },
  {
    label: '处理时间',
    field: 'processingTime',
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
    label: '告警时间',
    field: 'alarmTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '告警名称',
    field: 'alarmName',
    component: 'Input',
  },
  {
    label: '告警级别',
    field: 'alarmLevel',
    component: 'Input',
  },
  {
    label: '告警描述',
    field: 'alarmDescribe',
    component: 'Input',
  },
  {
    label: '处理结果',
    field: 'processingResult',
    component: 'Input',
  },
  {
    label: '处理意见',
    field: 'processingOpinions',
    component: 'Input',
  },
  {
    label: '告警内容',
    field: 'alarmContent',
    component: 'Input',
  },
  {
    label: '处理人',
    field: 'processingPeople',
    component: 'Input',
  },
  {
    label: '处理时间',
    field: 'processingTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
]
