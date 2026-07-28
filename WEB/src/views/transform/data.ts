import type { BasicColumn, FormSchema } from '@/components/Table'
import { Tag } from 'ant-design-vue'
import { h } from 'vue'

export const partyTypeOptions = [
  { label: 'MES（制造执行）', value: 'mes.rest' },
  { label: 'ERP（企业资源）', value: 'erp.rest' },
  { label: 'WMS（仓储）', value: 'wms.rest' },
  { label: 'CRM（客户）', value: 'crm.rest' },
  { label: 'OA（办公）', value: 'oa.rest' },
]

export const flowTypeOptions = [
  { label: '设备数据', value: 'DATA' },
  { label: '传感器数据', value: 'SENSOR' },
  { label: '告警事件', value: 'ALERT' },
  { label: '视觉识别结果', value: 'VIDEO_META' },
]

export const channelOptions = [
  { label: '系统接口', value: 'party' },
  { label: 'HTTP 推送', value: 'http' },
  { label: 'MQTT', value: 'mqtt' },
  { label: '写对方数据库', value: 'jdbc' },
  { label: 'Kafka', value: 'kafka' },
]

export function systemTypeLabel(type?: string) {
  return partyTypeOptions.find((item) => item.value === type)?.label || type || '—'
}

export function flowTypeLabel(flow?: string) {
  return flowTypeOptions.find((item) => item.value === flow)?.label || flow || '—'
}

export function channelLabel(channel?: string) {
  return channelOptions.find((item) => item.value === channel)?.label || channel || '—'
}

export function deliveryStatusLabel(status?: string) {
  const map: Recordable = {
    PENDING: '待推送',
    RELAYING: '推送中',
    SENT: '已发出',
    FAILED: '失败',
    DELIVERED: '已送达',
    DEAD: '已放弃',
  }
  return (status && map[status]) || status || '—'
}

export function formatHeartbeat(value: any) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (!Number.isNaN(num) && num > 1e9) {
    const ms = num > 1e12 ? num : num * 1000
    const d = new Date(ms)
    if (!Number.isNaN(d.getTime())) {
      const pad = (n: number) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(
        d.getMinutes(),
      )}:${pad(d.getSeconds())}`
    }
  }
  return String(value)
}

function renderEnabled(text: boolean) {
  return h(Tag, { color: text ? 'green' : 'default' }, () => (text ? '启用' : '停用'))
}

function renderOnline(text: boolean) {
  return h(Tag, { color: text ? 'green' : 'default' }, () => (text ? '在线' : '离线'))
}

function renderDeliveryStatus(text?: string) {
  const failed = text === 'FAILED' || text === 'DEAD'
  return h(Tag, { color: failed ? 'red' : 'blue' }, () => deliveryStatusLabel(text))
}

export function getInstanceColumns(): BasicColumn[] {
  return [
    { title: '实例 ID', dataIndex: 'instanceId', width: 220, ellipsis: true },
    { title: '节点', dataIndex: 'nodeId', width: 120, customRender: ({ text }) => text || '—' },
    { title: '主机', dataIndex: 'host', width: 140 },
    { title: '角色', dataIndex: 'role', width: 90 },
    {
      title: '自适应',
      dataIndex: 'adaptDecision',
      width: 100,
      customRender: ({ text }) => text || 'KEEP',
    },
    { title: '状态', dataIndex: 'online', width: 90, customRender: ({ text }) => renderOnline(!!text) },
    {
      title: '最后心跳',
      dataIndex: 'lastHeartbeatTime',
      width: 180,
      customRender: ({ text }) => formatHeartbeat(text),
    },
    { title: '操作', dataIndex: 'action', width: 100 },
  ]
}

export function getPartyColumns(): BasicColumn[] {
  return [
    { title: '系统编码', dataIndex: 'id', width: 160 },
    { title: '系统名称', dataIndex: 'name', width: 160 },
    {
      title: '系统类型',
      dataIndex: 'type',
      width: 160,
      customRender: ({ text }) => systemTypeLabel(text),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 90,
      customRender: ({ text }) => renderEnabled(!!text),
    },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getContractColumns(partyNameFn: (id?: string) => string): BasicColumn[] {
  return [
    { title: '规则编码', dataIndex: 'id', width: 180 },
    {
      title: '对接系统',
      dataIndex: 'partyId',
      width: 160,
      customRender: ({ text }) => partyNameFn(text),
    },
    {
      title: '数据类型',
      dataIndex: 'flowType',
      width: 120,
      customRender: ({ text }) => flowTypeLabel(text),
    },
    {
      title: '推送通道',
      dataIndex: 'channel',
      width: 120,
      customRender: ({ text }) => channelLabel(text),
    },
    { title: '投递地址', dataIndex: 'endpoint', width: 240, ellipsis: true },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 90,
      customRender: ({ text }) => renderEnabled(!!text),
    },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getMappingColumns(): BasicColumn[] {
  return [
    { title: '模板编码', dataIndex: 'id', width: 140 },
    { title: '模板名称', dataIndex: 'name', width: 140 },
    {
      title: '字段数',
      dataIndex: 'fields',
      width: 90,
      customRender: ({ text }) => Object.keys(text || {}).length,
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 90,
      customRender: ({ text }) => renderEnabled(!!text),
    },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getPipelineColumns(mappingNameFn: (id?: string) => string): BasicColumn[] {
  return [
    { title: '流程编码', dataIndex: 'id', width: 140 },
    { title: '流程名称', dataIndex: 'name', width: 140 },
    {
      title: '数据类型',
      dataIndex: 'flowType',
      width: 120,
      customRender: ({ text }) => flowTypeLabel(text),
    },
    {
      title: '映射模板',
      dataIndex: 'mappingId',
      width: 160,
      customRender: ({ text }) => mappingNameFn(text),
    },
    { title: '启用', dataIndex: 'enabled', width: 90 },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getOutboxColumns(partyNameFn: (id?: string) => string): BasicColumn[] {
  return [
    { title: '记录编号', dataIndex: 'id', width: 180, ellipsis: true },
    { title: '事件编号', dataIndex: 'eventId', width: 160, ellipsis: true },
    {
      title: '对接系统',
      dataIndex: 'partyId',
      width: 140,
      customRender: ({ text }) => partyNameFn(text),
    },
    {
      title: '通道',
      dataIndex: 'channel',
      width: 100,
      customRender: ({ text }) => channelLabel(text),
    },
    {
      title: '投递状态',
      dataIndex: 'status',
      width: 100,
      customRender: ({ text }) => renderDeliveryStatus(text),
    },
    { title: '重试次数', dataIndex: 'attempts', width: 90 },
    { title: '操作', dataIndex: 'action', width: 90 },
  ]
}

export function getDlqColumns(): BasicColumn[] {
  return [
    { title: '死信编号', dataIndex: 'id', width: 180, ellipsis: true },
    { title: '失败来源', dataIndex: 'source', width: 120 },
    { title: '失败原因', dataIndex: 'reason', width: 220, ellipsis: true },
    { title: '操作', dataIndex: 'action', width: 90 },
  ]
}

/** 卡片视图字段定义（与表格列对齐） */
export function getInstanceCardFields() {
  return [
    { key: 'nodeId', label: '节点', render: (r: Recordable) => r.nodeId || '—' },
    { key: 'host', label: '主机' },
    { key: 'role', label: '角色' },
    {
      key: 'adaptDecision',
      label: '自适应',
      render: (r: Recordable) => r.adaptDecision || 'KEEP',
    },
    {
      key: 'lastHeartbeatTime',
      label: '心跳',
      render: (r: Recordable) => formatHeartbeat(r.lastHeartbeatTime),
    },
  ]
}

export function getPartyCardFields() {
  return [
    { key: 'id', label: '系统编码' },
    { key: 'type', label: '系统类型', render: (r: Recordable) => systemTypeLabel(r.type) },
  ]
}

export function getContractCardFields(partyNameFn: (id?: string) => string) {
  return [
    { key: 'partyId', label: '对接系统', render: (r: Recordable) => partyNameFn(r.partyId) },
    { key: 'flowType', label: '数据类型', render: (r: Recordable) => flowTypeLabel(r.flowType) },
    { key: 'channel', label: '推送通道', render: (r: Recordable) => channelLabel(r.channel) },
    { key: 'endpoint', label: '投递地址' },
  ]
}

export function getMappingCardFields() {
  return [
    { key: 'id', label: '模板编码' },
    {
      key: 'fields',
      label: '字段数',
      render: (r: Recordable) => String(Object.keys(r.fields || {}).length),
    },
  ]
}

export function getPipelineCardFields(mappingNameFn: (id?: string) => string) {
  return [
    { key: 'id', label: '流程编码' },
    { key: 'flowType', label: '数据类型', render: (r: Recordable) => flowTypeLabel(r.flowType) },
    {
      key: 'mappingId',
      label: '映射模板',
      render: (r: Recordable) => mappingNameFn(r.mappingId),
    },
  ]
}

export function getOutboxCardFields(partyNameFn: (id?: string) => string) {
  return [
    { key: 'eventId', label: '事件编号' },
    { key: 'partyId', label: '对接系统', render: (r: Recordable) => partyNameFn(r.partyId) },
    { key: 'channel', label: '通道', render: (r: Recordable) => channelLabel(r.channel) },
    { key: 'attempts', label: '重试次数' },
  ]
}

export function getDlqCardFields() {
  return [
    { key: 'source', label: '失败来源' },
    { key: 'reason', label: '失败原因' },
  ]
}

export function getPartyFormSchema(isEdit: boolean): FormSchema[] {
  return [
    {
      field: 'id',
      label: '系统编码',
      component: 'Input',
      required: true,
      componentProps: { disabled: isEdit, placeholder: '如 demo-mes' },
    },
    {
      field: 'name',
      label: '系统名称',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 产线 MES' },
    },
    {
      field: 'type',
      label: '系统类型',
      component: 'Select',
      required: true,
      componentProps: { options: partyTypeOptions },
    },
    {
      field: 'enabled',
      label: '启用状态',
      component: 'Switch',
      defaultValue: true,
    },
    {
      field: 'configText',
      label: '系统配置(JSON)',
      component: 'InputTextArea',
      defaultValue: '{}',
      componentProps: { rows: 4, placeholder: '{"baseUrl":"http://..."}' },
    },
  ]
}

export function getContractFormSchema(
  isEdit: boolean,
  partyOptions: { label: string; value: string }[],
  mappingOptions: { label: string; value: string }[],
): FormSchema[] {
  return [
    {
      field: 'id',
      label: '规则编码',
      component: 'Input',
      required: true,
      componentProps: { disabled: isEdit },
    },
    {
      field: 'partyId',
      label: '对接系统',
      component: 'Select',
      required: true,
      componentProps: { options: partyOptions, placeholder: '请选择对接系统' },
    },
    {
      field: 'flowType',
      label: '数据类型',
      component: 'Select',
      required: true,
      componentProps: { options: flowTypeOptions },
    },
    {
      field: 'channel',
      label: '推送通道',
      component: 'Select',
      required: true,
      componentProps: { options: channelOptions },
    },
    {
      field: 'endpoint',
      label: '投递地址',
      component: 'Input',
      required: true,
      componentProps: { placeholder: 'http://host/path' },
    },
    {
      field: 'mappingId',
      label: '映射模板',
      component: 'Select',
      componentProps: { options: mappingOptions, allowClear: true, placeholder: '可选' },
    },
    {
      field: 'enabled',
      label: '启用状态',
      component: 'Switch',
      defaultValue: true,
    },
    {
      field: 'headersText',
      label: '请求头(JSON)',
      component: 'InputTextArea',
      defaultValue: '{}',
      componentProps: { rows: 4 },
    },
  ]
}

export function getMappingFormSchema(isEdit: boolean): FormSchema[] {
  return [
    {
      field: 'id',
      label: '模板编码',
      component: 'Input',
      required: true,
      componentProps: { disabled: isEdit },
    },
    {
      field: 'name',
      label: '模板名称',
      component: 'Input',
      required: true,
    },
    {
      field: 'enabled',
      label: '启用状态',
      component: 'Switch',
      defaultValue: true,
    },
    {
      field: 'fieldsText',
      label: '字段映射(JSON)',
      component: 'InputTextArea',
      required: true,
      defaultValue: '{}',
      componentProps: {
        rows: 6,
        placeholder: '{"orderId":"$.eventId"}',
      },
      helpMessage: 'key=目标字段，value=源字段',
    },
  ]
}

export function getPipelineFormSchema(
  isEdit: boolean,
  mappingOptions: { label: string; value: string }[],
): FormSchema[] {
  return [
    {
      field: 'id',
      label: '流程编码',
      component: 'Input',
      required: true,
      componentProps: { disabled: isEdit },
    },
    {
      field: 'name',
      label: '流程名称',
      component: 'Input',
      required: true,
    },
    {
      field: 'flowType',
      label: '数据类型',
      component: 'Select',
      required: true,
      componentProps: { options: flowTypeOptions },
    },
    {
      field: 'mappingId',
      label: '映射模板',
      component: 'Select',
      componentProps: { options: mappingOptions, allowClear: true, placeholder: '可选' },
    },
    {
      field: 'enabled',
      label: '启用状态',
      component: 'Switch',
      defaultValue: true,
    },
  ]
}

export function parseJsonField(text: string, label: string) {
  try {
    return text?.trim() ? JSON.parse(text) : {}
  } catch {
    throw new Error(`${label} 不是合法 JSON`)
  }
}
