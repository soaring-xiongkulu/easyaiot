import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  { title: '编号', dataIndex: 'id', width: 90 },
  { title: '用户组名称', dataIndex: 'name', width: 200 },
  { title: '描述', dataIndex: 'description', width: 260 },
  { title: '成员数', dataIndex: 'memberUserIds', width: 100 },
  {
    title: '状态',
    dataIndex: 'status',
    width: 110,
    customRender: ({ text }) => {
      return useRender.renderTag(text === 0 ? '开启' : '关闭', text === 0 ? 'success' : 'error')
    },
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    width: 180,
    customRender: ({ text }) => useRender.renderDate(text),
  },
]

export const searchFormSchema: FormSchema[] = [
  { label: '用户组名称', field: 'name', component: 'Input', colProps: { span: 8 } },
  {
    label: '状态',
    field: 'status',
    component: 'Select',
    componentProps: {
      options: [
        { label: '开启', value: 0 },
        { label: '关闭', value: 1 },
      ],
      allowClear: true,
    },
    colProps: { span: 8 },
  },
]
