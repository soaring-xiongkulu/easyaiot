import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  { title: '分类编号', dataIndex: 'id', width: 100 },
  { title: '分类名称', dataIndex: 'name', width: 200 },
  { title: '分类编码', dataIndex: 'code', width: 160 },
  { title: '排序', dataIndex: 'sort', width: 90 },
  {
    title: '状态',
    dataIndex: 'status',
    width: 120,
    customRender: ({ text }) => {
      return useRender.renderTag(text === 0 ? '开启' : '关闭', text === 0 ? 'success' : 'error')
    },
  },
  { title: '描述', dataIndex: 'description', width: 240 },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    width: 180,
    customRender: ({ text }) => useRender.renderDate(text),
  },
]

export const searchFormSchema: FormSchema[] = [
  { label: '分类名称', field: 'name', component: 'Input', colProps: { span: 8 } },
  { label: '分类编码', field: 'code', component: 'Input', colProps: { span: 8 } },
]

export const formSchema: FormSchema[] = [
  { label: '编号', field: 'id', show: false, component: 'Input' },
  { label: '分类名称', field: 'name', required: true, component: 'Input' },
  { label: '分类编码', field: 'code', required: true, component: 'Input', helpMessage: '唯一编码，如 alarm / maintenance' },
  { label: '排序', field: 'sort', defaultValue: 0, component: 'InputNumber' },
  {
    label: '状态',
    field: 'status',
    defaultValue: 0,
    component: 'Select',
    componentProps: {
      options: [
        { label: '开启', value: 0 },
        { label: '关闭', value: 1 },
      ],
    },
  },
  { label: '描述', field: 'description', component: 'InputTextArea' },
]
