import { ColumnsType } from 'ant-design-vue/lib/table/interface'

export function presetColumns(): ColumnsType {
  return [
    {
      title: 'ID',
      dataIndex: 'presetId',
      fixed: 'left',
      width: 100,
    },
    {
      title: '名称',
      dataIndex: 'presetName',
      fixed: 'left',
      width: 160,
    },
    {
      title: '操作',
      dataIndex: 'operation',
      width: 240,
      fixed: 'right',
    },
  ]
}
