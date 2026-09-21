import { BasicColumn, FormProps } from '@/components/Table'
import { getProjectTypeLabel } from '@/utils/visualizeEditor'

export function getBasicColumns(): BasicColumn[] {
  return [
    {
      title: '项目ID',
      dataIndex: 'id',
      width: 90,
    },
    {
      title: '项目名称',
      dataIndex: 'projectName',
      width: 160,
    },
    {
      title: '类型',
      dataIndex: 'projectType',
      width: 90,
      customRender: ({ text }) => getProjectTypeLabel(text),
    },
    {
      title: '发布状态',
      dataIndex: 'state',
      width: 100,
      customRender: ({ text }) => (Number(text) === 1 ? '已发布' : '未发布'),
    },
    {
      title: '备注',
      dataIndex: 'remarks',
      width: 180,
      customRender: ({ text }) => text || '--',
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      width: 170,
      customRender: ({ text }) => formatDateTime(text),
    },
    {
      title: '更新时间',
      dataIndex: 'updateTime',
      width: 170,
      customRender: ({ text }) => formatDateTime(text),
    },
    {
      width: 160,
      title: '操作',
      dataIndex: 'action',
      fixed: 'right',
    },
  ]
}

export function getFormConfig(): Partial<FormProps> {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    schemas: [
      {
        field: 'projectName',
        label: '项目名称',
        component: 'Input',
      },
      {
        field: 'projectType',
        label: '项目类型',
        component: 'Select',
        componentProps: {
          allowClear: true,
          options: [
            { label: '大屏', value: 'dashboard' },
            { label: '组态', value: 'scada' },
            { label: '数字孪生', value: 'twin' },
          ],
        },
      },
      {
        field: 'state',
        label: '发布状态',
        component: 'Select',
        componentProps: {
          allowClear: true,
          options: [
            { label: '未发布', value: -1 },
            { label: '已发布', value: 1 },
          ],
        },
      },
    ],
  }
}

function formatDateTime(dateString: string): string {
  if (!dateString) return '--'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return String(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}
