import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: '命令id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '服务ID',
    dataIndex: 'serviceId',
    width: 160,
  },
  {
    title: '命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令，支持英文大小写、数字及下划线，长度[2,50]',
    dataIndex: 'name',
    width: 160,
  },
  {
    title: '命令描述。',
    dataIndex: 'description',
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
    label: '命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。支持英文大小写、数字及下划线，长度[2,50]',
    field: 'name',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '命令描述',
    field: 'description',
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
    label: '命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令。支持英文大小写、数字及下划线，长度[2,50]',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '命令描述。',
    field: 'description',
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
    label: '命令的名字，如门磁的LOCK命令、摄像头的VIDEO_RECORD命令，命令名与参数共同构成一个完整的命令，支持英文大小写、数字及下划线，长度[2,50]',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '命令描述。',
    field: 'description',
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
