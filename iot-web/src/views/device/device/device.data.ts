import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '设备唯一标识',
    dataIndex: 'did',
    width: 160,
  },
  {
    title: '设备名称',
    dataIndex: 'name',
    width: 160,
  },
  {
    title: '设备描述',
    dataIndex: 'description',
    width: 160,
  },
  // {
  //     title: '设备状态',
  //     dataIndex: 'enabledStatus',
  //     width: 80,
  //     customRender: ({ text }) => {
  //         return useRender.renderDict(text, DICT_TYPE.COMMON_STATUS)
  //     },
  // },
  {
    title: '设备状态',
    dataIndex: 'enabledStatus',
    width: 160,
  },
  {
    title: '连接状态',
    dataIndex: 'connectStatus',
    width: 160,
  },
  {
    title: '产品唯一标识',
    dataIndex: 'pid',
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
    title: '备注',
    dataIndex: 'remark',
    width: 160,
  },
  {
    title: '设备版本号',
    dataIndex: 'deviceVersion',
    width: 160,
  },
  {
    title: '设备sn号',
    dataIndex: 'deviceSn',
    width: 160,
  },
  {
    title: 'IP地址',
    dataIndex: 'ipAddress',
    width: 160,
  },
  {
    title: 'MAC地址',
    dataIndex: 'macAddress',
    width: 160,
  },
  {
    title: '激活状态 0:未激活 1:已激活',
    dataIndex: 'activeStatus',
    width: 160,
  },
  {
    title: '扩展json',
    dataIndex: 'extension',
    width: 160,
  },
  {
    title: '激活时间',
    dataIndex: 'activatedTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '最后上线时间',
    dataIndex: 'lastOnlineTime',
    width: 180,
    customRender: ({ text }) => {
      return useRender.renderDate(text)
    },
  },
  {
    title: '设备类型',
    dataIndex: 'deviceType',
    width: 160,
  },
  {
    title: '纬度',
    dataIndex: 'latitude',
    width: 160,
  },
  {
    title: '经度',
    dataIndex: 'longitude',
    width: 160,
  },
  {
    title: '设备所在位置',
    dataIndex: 'locationName',
    width: 160,
  },
  {
    title: '省,直辖市编码',
    dataIndex: 'provinceCode',
    width: 160,
  },
  {
    title: '市编码',
    dataIndex: 'cityCode',
    width: 160,
  },
  {
    title: '区县',
    dataIndex: 'regionCode',
    width: 160,
  },
  {
    title: '产品名称',
    dataIndex: 'productName',
    width: 160,
  },
  {
    title: '是否启用设备影子(0=禁用，1=启用)',
    dataIndex: 'isShadow',
    width: 160,
  },
  {
    title: '物模型值',
    dataIndex: 'thingsModelValue',
    width: 160,
  },
  {
    title: '产品类型ID',
    dataIndex: 'productTypeId',
    width: 160,
  },
  {
    title: '产品类型名称',
    dataIndex: 'productTypeName',
    width: 160,
  },
  {
    title: '分组ID',
    dataIndex: 'groupId',
    width: 160,
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '设备唯一标识',
    field: 'did',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备名称',
    field: 'name',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备描述',
    field: 'description',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备状态',
    field: 'enabledStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '连接状态',
    field: 'connectStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '产品唯一标识',
    field: 'pid',
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
    label: '备注',
    field: 'remark',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备版本号',
    field: 'deviceVersion',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备sn号',
    field: 'deviceSn',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: 'IP地址',
    field: 'ipAddress',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: 'MAC地址',
    field: 'macAddress',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '激活状态 0:未激活 1:已激活',
    field: 'activeStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '扩展json',
    field: 'extension',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '激活时间',
    field: 'activatedTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '最后上线时间',
    field: 'lastOnlineTime',
    component: 'RangePicker',
    colProps: { span: 8 },
  },
  {
    label: '设备类型',
    field: 'deviceType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '纬度',
    field: 'latitude',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '经度',
    field: 'longitude',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备所在位置',
    field: 'locationName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '省,直辖市编码',
    field: 'provinceCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '市编码',
    field: 'cityCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '区县',
    field: 'regionCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品名称',
    field: 'productName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '是否启用设备影子(0=禁用，1=启用)',
    field: 'isShadow',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '物模型值',
    field: 'thingsModelValue',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品类型ID',
    field: 'productTypeId',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品类型名称',
    field: 'productTypeName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '分组ID',
    field: 'groupId',
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
    label: '设备唯一标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: '设备名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '设备描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '设备状态',
    field: 'enabledStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '连接状态',
    field: 'connectStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    required: true,
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
    label: '备注',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '设备版本号',
    field: 'deviceVersion',
    component: 'Input',
  },
  {
    label: '设备sn号',
    field: 'deviceSn',
    required: true,
    component: 'Input',
  },
  {
    label: 'IP地址',
    field: 'ipAddress',
    component: 'Input',
  },
  {
    label: 'MAC地址',
    field: 'macAddress',
    component: 'Input',
  },
  {
    label: '激活状态 0:未激活 1:已激活',
    field: 'activeStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '扩展json',
    field: 'extension',
    component: 'Input',
  },
  {
    label: '激活时间',
    field: 'activatedTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '最后上线时间',
    field: 'lastOnlineTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '设备类型',
    field: 'deviceType',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '纬度',
    field: 'latitude',
    component: 'Input',
  },
  {
    label: '经度',
    field: 'longitude',
    component: 'Input',
  },
  {
    label: '设备所在位置',
    field: 'locationName',
    component: 'Input',
  },
  {
    label: '省,直辖市编码',
    field: 'provinceCode',
    component: 'Input',
  },
  {
    label: '市编码',
    field: 'cityCode',
    component: 'Input',
  },
  {
    label: '区县',
    field: 'regionCode',
    component: 'Input',
  },
  {
    label: '产品名称',
    field: 'productName',
    component: 'Input',
  },
  {
    label: '是否启用设备影子(0=禁用，1=启用)',
    field: 'isShadow',
    component: 'Input',
  },
  {
    label: '物模型值',
    field: 'thingsModelValue',
    component: 'Input',
  },
  {
    label: '产品类型ID',
    field: 'productTypeId',
    component: 'Input',
  },
  {
    label: '产品类型名称',
    field: 'productTypeName',
    component: 'Input',
  },
  {
    label: '分组ID',
    field: 'groupId',
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
    label: '设备唯一标识',
    field: 'did',
    required: true,
    component: 'Input',
  },
  {
    label: '设备名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '设备描述',
    field: 'description',
    component: 'Input',
  },
  {
    label: '设备状态',
    field: 'enabledStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '连接状态',
    field: 'connectStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    required: true,
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
    label: '备注',
    field: 'remark',
    component: 'Input',
  },
  {
    label: '设备版本号',
    field: 'deviceVersion',
    component: 'Input',
  },
  {
    label: '设备sn号',
    field: 'deviceSn',
    required: true,
    component: 'Input',
  },
  {
    label: 'IP地址',
    field: 'ipAddress',
    component: 'Input',
  },
  {
    label: 'MAC地址',
    field: 'macAddress',
    component: 'Input',
  },
  {
    label: '激活状态 0:未激活 1:已激活',
    field: 'activeStatus',
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '扩展json',
    field: 'extension',
    component: 'Input',
  },
  {
    label: '激活时间',
    field: 'activatedTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '最后上线时间',
    field: 'lastOnlineTime',
    component: 'DatePicker',
    componentProps: {
      showTime: true,
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'x',
    },
  },
  {
    label: '设备类型',
    field: 'deviceType',
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '纬度',
    field: 'latitude',
    component: 'Input',
  },
  {
    label: '经度',
    field: 'longitude',
    component: 'Input',
  },
  {
    label: '设备所在位置',
    field: 'locationName',
    component: 'Input',
  },
  {
    label: '省,直辖市编码',
    field: 'provinceCode',
    component: 'Input',
  },
  {
    label: '市编码',
    field: 'cityCode',
    component: 'Input',
  },
  {
    label: '区县',
    field: 'regionCode',
    component: 'Input',
  },
  {
    label: '产品名称',
    field: 'productName',
    component: 'Input',
  },
  {
    label: '是否启用设备影子(0=禁用，1=启用)',
    field: 'isShadow',
    component: 'Input',
  },
  {
    label: '物模型值',
    field: 'thingsModelValue',
    component: 'Input',
  },
  {
    label: '产品类型ID',
    field: 'productTypeId',
    component: 'Input',
  },
  {
    label: '产品类型名称',
    field: 'productTypeName',
    component: 'Input',
  },
  {
    label: '分组ID',
    field: 'groupId',
    component: 'Input',
  },
]
