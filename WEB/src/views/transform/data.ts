import type { BasicColumn, FormSchema } from '@/components/Table'
import { Tag } from 'ant-design-vue'
import { h } from 'vue'

export const partyTypeOptions = [
  { label: 'MES（制造执行）', value: 'mes.rest' },
  { label: 'ERP（企业资源）', value: 'erp.rest' },
  { label: 'WMS（仓储）', value: 'wms.rest' },
  { label: 'CRM（客户）', value: 'crm.rest' },
  { label: 'OA（办公）', value: 'oa.rest' },
  { label: '自定义 REST', value: 'custom.rest' },
]

export const flowTypeOptions = [
  { label: '设备属性 / 消息', value: 'DATA', desc: '物模型属性上报、设备上行消息' },
  { label: '传感器数据', value: 'SENSOR', desc: '传感器采集与工业协议点位' },
  { label: '告警事件', value: 'ALERT', desc: '规则告警、抓拍告警通知' },
  { label: '视觉识别结果', value: 'VIDEO_META', desc: '人脸 / 车牌 / 后处理结果' },
]

export const channelOptions = [
  { label: '系统接口', value: 'party' },
  { label: 'HTTP 推送', value: 'http' },
  { label: 'MQTT', value: 'mqtt' },
  { label: '写对方数据库', value: 'jdbc' },
  { label: 'Kafka', value: 'kafka' },
]

/** 通道类型卡片（阿里云「数据目的」选择器风格） */
export const channelMetaOptions = [
  {
    value: 'party',
    label: '对接系统接口',
    short: 'SYS',
    color: '#5AD8A6',
    desc: '转发至已配置的 MES / ERP / WMS 等系统',
  },
  {
    value: 'http',
    label: 'HTTP / Webhook',
    short: 'HTTP',
    color: '#5B8FF9',
    desc: 'POST JSON 到任意 HTTP 地址，支持签名',
  },
  {
    value: 'mqtt',
    label: 'MQTT Topic',
    short: 'MQTT',
    color: '#6DC8EC',
    desc: '发布到第三方 MQTT Broker 主题',
  },
  {
    value: 'jdbc',
    label: '业务数据库',
    short: 'JDBC',
    color: '#F6BD16',
    desc: '写入对方业务库表（需配置连接）',
  },
  {
    value: 'kafka',
    label: 'Kafka Topic',
    short: 'KFK',
    color: '#945FB9',
    desc: '投递到指定 Kafka Topic',
  },
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
  return h(Tag, { color: text ? 'green' : 'default' }, () => (text ? '运行中' : '已停止'))
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
    { title: '实例', dataIndex: 'instanceId', width: 200, ellipsis: true },
    { title: '节点', dataIndex: 'nodeId', width: 110, customRender: ({ text }) => text || '—' },
    { title: '主机', dataIndex: 'host', width: 130, ellipsis: true },
    { title: '角色', dataIndex: 'role', width: 90, customRender: ({ text }) => text || '—' },
    { title: '状态', dataIndex: 'online', width: 90, customRender: ({ text }) => renderOnline(!!text) },
    {
      title: 'CPU',
      dataIndex: 'cpuLoad',
      width: 80,
      customRender: ({ text }) => (text == null ? '—' : `${Number(text).toFixed(0)}%`),
    },
    {
      title: '堆内存',
      dataIndex: 'heap',
      width: 110,
      customRender: ({ record }) => {
        const used = record?.heapUsedMb
        const max = record?.heapMaxMb
        if (used == null) return '—'
        return max != null ? `${used}/${max} MB` : `${used} MB`
      },
    },
    {
      title: '消费 Lag',
      dataIndex: 'maxConsumerLag',
      width: 100,
      customRender: ({ text }) => (text == null ? '—' : String(text)),
    },
    {
      title: '投递成功率',
      dataIndex: 'deliverSuccessRate',
      width: 100,
      customRender: ({ text }) =>
        text == null ? '—' : `${(Number(text) * 100).toFixed(1)}%`,
    },
    {
      title: '自适应',
      dataIndex: 'adaptDecision',
      width: 90,
      customRender: ({ text }) => text || 'KEEP',
    },
    {
      title: '最后心跳',
      dataIndex: 'lastHeartbeatTime',
      width: 170,
      customRender: ({ text }) => formatHeartbeat(text),
    },
    { title: '操作', dataIndex: 'action', width: 200 },
  ]
}

/** 运行集群下行指令 */
export const clusterCommandOptions = [
  {
    value: 'PING',
    label: 'PING',
    desc: '探活：实例立即回传 PONG 遥测与指令回执',
  },
  {
    value: 'RELOAD_CONFIG',
    label: '重载配置',
    desc: '确认规则/映射已从库生效，并回传 RELOADED',
  },
  {
    value: 'SHUTDOWN_HINT',
    label: '优雅停机',
    desc: '进程优雅退出；Docker 副本需再调节点 Agent 硬停',
  },
]

export function formatPercentRate(rate?: number | null) {
  if (rate == null || Number.isNaN(Number(rate))) return '—'
  return `${(Number(rate) * 100).toFixed(1)}%`
}

export function formatCpu(load?: number | null) {
  if (load == null || Number.isNaN(Number(load))) return '—'
  return `${Number(load).toFixed(0)}%`
}

export function formatHeap(used?: number | null, max?: number | null) {
  if (used == null) return '—'
  return max != null ? `${used} / ${max} MB` : `${used} MB`
}

export function getPartyColumns(): BasicColumn[] {
  return [
    { title: '目的地编码', dataIndex: 'id', width: 160 },
    { title: '目的地名称', dataIndex: 'name', width: 160 },
    {
      title: '系统类型',
      dataIndex: 'type',
      width: 160,
      customRender: ({ text }) => systemTypeLabel(text),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 100,
      customRender: ({ text }) => renderEnabled(!!text),
    },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getContractColumns(partyNameFn: (id?: string) => string): BasicColumn[] {
  return [
    { title: '规则编码', dataIndex: 'id', width: 180 },
    {
      title: '数据目的',
      dataIndex: 'partyId',
      width: 160,
      customRender: ({ text }) => partyNameFn(text),
    },
    {
      title: '数据源类型',
      dataIndex: 'flowType',
      width: 140,
      customRender: ({ text }) => flowTypeLabel(text),
    },
    {
      title: '转发通道',
      dataIndex: 'channel',
      width: 120,
      customRender: ({ text }) => channelLabel(text),
    },
    { title: '投递地址', dataIndex: 'endpoint', width: 240, ellipsis: true },
    { title: '运行状态', dataIndex: 'enabled', width: 100 },
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
      width: 100,
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
      title: '数据源类型',
      dataIndex: 'flowType',
      width: 140,
      customRender: ({ text }) => flowTypeLabel(text),
    },
    {
      title: '解析器 / 映射',
      dataIndex: 'mappingId',
      width: 160,
      customRender: ({ text }) => mappingNameFn(text),
    },
    { title: '运行状态', dataIndex: 'enabled', width: 100 },
    { title: '操作', dataIndex: 'action', width: 120 },
  ]
}

export function getOutboxColumns(partyNameFn: (id?: string) => string): BasicColumn[] {
  return [
    { title: '记录编号', dataIndex: 'id', width: 160, ellipsis: true },
    { title: '事件编号', dataIndex: 'eventId', width: 140, ellipsis: true },
    {
      title: '数据目的',
      dataIndex: 'partyId',
      width: 120,
      customRender: ({ text }) => partyNameFn(text),
    },
    {
      title: '规则',
      dataIndex: 'contractId',
      width: 140,
      ellipsis: true,
      customRender: ({ text }) => text || '—',
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
    { title: '重试', dataIndex: 'attempts', width: 70 },
    {
      title: '错误信息',
      dataIndex: 'error',
      width: 200,
      ellipsis: true,
      customRender: ({ text }) => text || '—',
    },
    { title: '操作', dataIndex: 'action', width: 140 },
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

/** @deprecated 抽屉改用结构化表单，保留兼容 */
export function getPartyFormSchema(isEdit: boolean): FormSchema[] {
  return [
    {
      field: 'id',
      label: '目的地编码',
      component: 'Input',
      required: true,
      componentProps: { disabled: isEdit, placeholder: '如 demo-mes' },
    },
    {
      field: 'name',
      label: '目的地名称',
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

/** @deprecated */
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
      label: '数据目的',
      component: 'Select',
      required: true,
      componentProps: { options: partyOptions, placeholder: '请选择数据目的' },
    },
    {
      field: 'flowType',
      label: '数据源类型',
      component: 'Select',
      required: true,
      componentProps: { options: flowTypeOptions },
    },
    {
      field: 'channel',
      label: '转发通道',
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

/** @deprecated */
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

/** @deprecated */
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
      label: '数据源类型',
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

export function endpointPlaceholder(channel?: string) {
  switch (channel) {
    case 'mqtt':
      return 'mqtt://broker:1883/topic/device/up'
    case 'kafka':
      return 'iot_transform_outbound'
    case 'jdbc':
      return 'jdbc:mysql://host:3306/db#table=device_data'
    case 'party':
      return 'http://mes.example.com/api/iot/ingest'
    default:
      return 'https://hook.example.com/iot/callback'
  }
}
