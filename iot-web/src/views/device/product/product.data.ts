import type { BasicColumn, FormSchema } from '@/components/Table'
import { useRender } from '@/components/Table'

export const columns: BasicColumn[] = [
  {
    title: 'id',
    dataIndex: 'id',
    width: 160,
  },
  {
    title: '模板code',
    dataIndex: 'templateCode',
    width: 160,
  },
  {
    title: '产品名称',
    dataIndex: 'name',
    width: 160,
  },
  {
    title: '产品唯一标识',
    dataIndex: 'pid',
    width: 160,
  },
  {
    title: '厂商名称 :支持中文、英文大小写、数字、下划线和中划线',
    dataIndex: 'manufacturerName',
    width: 160,
  },
  {
    title: '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线',
    dataIndex: 'model',
    width: 160,
  },
  {
    title: '数据格式，默认为JSON无需修改。',
    dataIndex: 'dataFormat',
    width: 160,
  },
  {
    title: '设备接入平台的协议类型，默认为MQTT无需修改。',
    dataIndex: 'protocolType',
    width: 160,
  },
  {
    title: '状态',
    dataIndex: 'enabledStatus',
    width: 160,
  },
  {
    title: '产品描述',
    dataIndex: 'remark',
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
    title: '认证方式',
    dataIndex: 'authMode',
    width: 160,
  },
  {
    title: '用户名',
    dataIndex: 'userName',
    width: 160,
  },
  {
    title: '密码',
    dataIndex: 'password',
    width: 160,
  },
  {
    title: '连接实例',
    dataIndex: 'connector',
    width: 160,
  },
  {
    title: '签名密钥',
    dataIndex: 'signKey',
    width: 160,
  },
  {
    title: '协议加密方式 0：不加密 1：SM4加密 2：AES加密',
    dataIndex: 'encryptMethod',
    width: 160,
  },
  {
    title: '加密密钥',
    dataIndex: 'encryptKey',
    width: 160,
  },
  {
    title: '加密向量',
    dataIndex: 'encryptVector',
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
    title: '厂商Code:支持英文大小写，数字，下划线和中划线',
    dataIndex: 'manufacturerCode',
    width: 160,
  },
]

export const searchFormSchema: FormSchema[] = [
  {
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品名称',
    field: 'name',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '厂商名称 :支持中文、英文大小写、数字、下划线和中划线',
    field: 'manufacturerName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线',
    field: 'model',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '数据格式，默认为JSON无需修改。',
    field: 'dataFormat',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '设备接入平台的协议类型，默认为MQTT无需修改。',
    field: 'protocolType',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '状态',
    field: 'enabledStatus',
    component: 'Select',
    componentProps: {
      options: [],
    },
    colProps: { span: 8 },
  },
  {
    label: '产品描述',
    field: 'remark',
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
    label: '认证方式',
    field: 'authMode',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '用户名',
    field: 'userName',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '密码',
    field: 'password',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '连接实例',
    field: 'connector',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '签名密钥',
    field: 'signKey',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '协议加密方式 0：不加密 1：SM4加密 2：AES加密',
    field: 'encryptMethod',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '加密密钥',
    field: 'encryptKey',
    component: 'Input',
    colProps: { span: 8 },
  },
  {
    label: '加密向量',
    field: 'encryptVector',
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
    label: '厂商Code:支持英文大小写，数字，下划线和中划线',
    field: 'manufacturerCode',
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
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    required: true,
    component: 'Input',
  },
  {
    label: '厂商名称 :支持中文、英文大小写、数字、下划线和中划线',
    field: 'manufacturerName',
    required: true,
    component: 'Input',
  },
  {
    label: '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线',
    field: 'model',
    required: true,
    component: 'Input',
  },
  {
    label: '数据格式，默认为JSON无需修改。',
    field: 'dataFormat',
    required: true,
    component: 'Input',
  },
  {
    label: '设备接入平台的协议类型，默认为MQTT无需修改。',
    field: 'protocolType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '状态',
    field: 'enabledStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品描述',
    field: 'remark',
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
    label: '认证方式',
    field: 'authMode',
    component: 'Input',
  },
  {
    label: '用户名',
    field: 'userName',
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    component: 'Input',
  },
  {
    label: '连接实例',
    field: 'connector',
    component: 'Input',
  },
  {
    label: '签名密钥',
    field: 'signKey',
    component: 'Input',
  },
  {
    label: '协议加密方式 0：不加密 1：SM4加密 2：AES加密',
    field: 'encryptMethod',
    component: 'Input',
  },
  {
    label: '加密密钥',
    field: 'encryptKey',
    component: 'Input',
  },
  {
    label: '加密向量',
    field: 'encryptVector',
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
    label: '厂商Code:支持英文大小写，数字，下划线和中划线',
    field: 'manufacturerCode',
    required: true,
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
    label: '模板code',
    field: 'templateCode',
    component: 'Input',
  },
  {
    label: '产品名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '产品唯一标识',
    field: 'pid',
    required: true,
    component: 'Input',
  },
  {
    label: '厂商名称 :支持中文、英文大小写、数字、下划线和中划线',
    field: 'manufacturerName',
    required: true,
    component: 'Input',
  },
  {
    label: '产品型号，建议包含字母或数字来保证可扩展性。支持英文大小写、数字、下划线和中划线',
    field: 'model',
    required: true,
    component: 'Input',
  },
  {
    label: '数据格式，默认为JSON无需修改。',
    field: 'dataFormat',
    required: true,
    component: 'Input',
  },
  {
    label: '设备接入平台的协议类型，默认为MQTT无需修改。',
    field: 'protocolType',
    required: true,
    component: 'Select',
    componentProps: {
      options: [],
    },
  },
  {
    label: '状态',
    field: 'enabledStatus',
    required: true,
    component: 'RadioButtonGroup',
    componentProps: {
      options: [],
    },
  },
  {
    label: '产品描述',
    field: 'remark',
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
    label: '认证方式',
    field: 'authMode',
    component: 'Input',
  },
  {
    label: '用户名',
    field: 'userName',
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    component: 'Input',
  },
  {
    label: '连接实例',
    field: 'connector',
    component: 'Input',
  },
  {
    label: '签名密钥',
    field: 'signKey',
    component: 'Input',
  },
  {
    label: '协议加密方式 0：不加密 1：SM4加密 2：AES加密',
    field: 'encryptMethod',
    component: 'Input',
  },
  {
    label: '加密密钥',
    field: 'encryptKey',
    component: 'Input',
  },
  {
    label: '加密向量',
    field: 'encryptVector',
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
    label: '厂商Code:支持英文大小写，数字，下划线和中划线',
    field: 'manufacturerCode',
    required: true,
    component: 'Input',
  },
]
