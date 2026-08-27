import { h } from 'vue';
import type { BasicColumn, FormSchema } from '@/components/Table';
import { useRender } from '@/components/Table';
import type { DescItem } from '@/components/Description';
import { formatToDateTime } from '@/utils/dateUtil';
import {
  NODE_METRIC,
  NODE_FUNCTION_MAP,
  NODE_FUNCTION_DESC,
  NODE_FUNCTION_OPTIONS,
  NODE_STATUS_MAP,
  NODE_TERM,
  CEPH_POOL_OPTIONS,
  STORAGE_TAG_DEFAULTS,
  MQTT_TAG_DEFAULTS,
  readStorageTagsFromTags,
  readMqttPortsFromTags,
  readCephMountFromTags,
  formatGpuSummary,
  parseNodeFunctions,
  formatNodeFunctions,
  nodeHasFunction,
} from './utils/constants';
import {
  formatSshUsername,
  renderNodeNameWithPlatformBadge,
  renderNodeRoleBadge,
  renderNodeStatusBadge,
  renderCephMountBadge,
} from './utils/nodeDisplay';

function formHasFunction(values: Record<string, any> | undefined, fn: string) {
  return nodeHasFunction({ functions: values?.functions, nodeRole: values?.nodeRole }, fn);
}

function formHasLive(values: Record<string, any> | undefined) {
  return formHasFunction(values, 'live') || formHasFunction(values, 'forward');
}

export { NODE_FUNCTION_MAP as NODE_ROLE_MAP, NODE_STATUS_MAP };

export const columns: BasicColumn[] = [
  {
    title: '节点名称',
    dataIndex: 'name',
    width: 180,
    ellipsis: true,
    customRender: ({ text, record }) => renderNodeNameWithPlatformBadge(text, record),
  },
  {
    title: '主机',
    dataIndex: 'host',
    width: 140,
    ellipsis: true,
    customRender: ({ text }) =>
      h('span', { style: { fontFamily: 'Consolas, monospace', fontSize: '12px' } }, text || '-'),
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 96,
    customRender: ({ text }) => renderNodeStatusBadge(text),
  },
  {
    title: '功能',
    dataIndex: 'functions',
    width: 180,
    customRender: ({ record }) => renderNodeRoleBadge(record),
  },
  {
    title: 'GPU',
    dataIndex: 'maxGpuCount',
    width: 70,
    customRender: ({ text }) => (text != null && text > 0 ? text : '-'),
  },
  {
    title: NODE_METRIC.cpu,
    dataIndex: 'cpuPercent',
    width: 80,
    customRender: ({ text }) => (text != null ? `${text}%` : '-'),
  },
  {
    title: NODE_METRIC.mem,
    dataIndex: 'memPercent',
    width: 80,
    customRender: ({ text }) => (text != null ? `${text}%` : '-'),
  },
  {
    title: NODE_METRIC.runningTasks,
    dataIndex: 'activeTasks',
    width: 70,
    customRender: ({ text }) => text ?? 0,
  },
  {
    title: '最近心跳',
    dataIndex: 'lastHeartbeatAt',
    width: 160,
    customRender: ({ text }) => (text ? useRender.renderDate(text) : '-'),
  },
];

export const searchFormSchema: FormSchema[] = [
  {
    label: '节点名称',
    field: 'name',
    component: 'Input',
    componentProps: { placeholder: '请输入节点名称' },
  },
  {
    label: '主机地址',
    field: 'host',
    component: 'Input',
    componentProps: { placeholder: '请输入主机地址' },
  },
  {
    label: '状态',
    field: 'status',
    component: 'Select',
    componentProps: {
      placeholder: '全部状态',
      options: Object.entries(NODE_STATUS_MAP).map(([value, { text }]) => ({ label: text, value })),
      allowClear: true,
    },
  },
  {
    label: '节点功能',
    field: 'function',
    component: 'Select',
    componentProps: {
      placeholder: '全部功能',
      options: NODE_FUNCTION_OPTIONS,
      allowClear: true,
    },
  },
];

export function getNodeFormConfig() {
  return {
    labelWidth: 80,
    baseColProps: { span: 6 },
    showAdvancedButton: false,
    autoSubmitOnEnter: true,
    actionColOptions: { span: 6 },
    schemas: searchFormSchema,
  };
}

export const formSchema: FormSchema[] = [
  { label: '编号', field: 'id', show: false, component: 'Input' },
  {
    field: 'dividerBasic',
    component: 'Divider',
    label: '基本信息',
    colProps: { span: 24 },
  },
  {
    label: '节点名称',
    field: 'name',
    required: true,
    component: 'Input',
    slot: 'name',
    colProps: { span: 12 },
    itemProps: { autoLink: false },
  },
  {
    label: '主机地址',
    field: 'host',
    required: true,
    component: 'Input',
    colProps: { span: 12 },
    componentProps: { placeholder: '10.0.0.11 或 node-a.internal' },
  },
  {
    label: '节点功能',
    field: 'functions',
    required: true,
    component: 'CheckboxGroup',
    defaultValue: ['algorithm'],
    colProps: { span: 24 },
    componentProps: {
      options: NODE_FUNCTION_OPTIONS,
    },
    helpMessage: '按这台机器要承担的业务勾选；可多选。保存前会 SSH 预检 Python、磁盘、Agent 端口和控制面连通，不通过则不会添加。运行时由控制面离线分发，节点无公网也可纳管。GPU 是硬件属性，不作为角色。',
  },
  {
    label: 'GPU 数量',
    field: 'maxGpuCount',
    component: 'InputNumber',
    defaultValue: 0,
    colProps: { span: 12 },
    componentProps: { min: 0, max: 16, placeholder: '节点 GPU 卡数，没有则填 0' },
    helpMessage: 'Agent 上线后会根据实际上报自动校正',
  },
  {
    label: '区域',
    field: 'region',
    component: 'Input',
    colProps: { span: 12 },
    componentProps: { placeholder: 'dc-a / 机房A' },
  },
  { label: '备注', field: 'remark', component: 'InputTextArea', colProps: { span: 24 } },
  {
    field: 'dividerConn',
    component: 'Divider',
    label: '连接配置',
    colProps: { span: 24 },
  },
  {
    label: 'SSH 端口',
    field: 'sshPort',
    component: 'InputNumber',
    defaultValue: 22,
    colProps: { span: 8 },
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: NODE_TERM.agentPort,
    field: 'agentPort',
    component: 'InputNumber',
    colProps: { span: 8 },
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'SSH 用户名',
    field: 'sshUsername',
    component: 'Input',
    defaultValue: 'root',
    colProps: { span: 8 },
    componentProps: { placeholder: 'root' },
  },
  {
    label: 'SSH 认证',
    field: 'sshAuthType',
    component: 'Select',
    defaultValue: 'password',
    colProps: { span: 8 },
    componentProps: {
      options: [
        { label: '密码', value: 'password' },
        { label: '私钥', value: 'private_key' },
      ],
    },
  },
  {
    label: 'SSH 密码',
    field: 'sshPassword',
    component: 'InputPassword',
    slot: 'sshPassword',
    colProps: { span: 16 },
    ifShow: ({ values }) => values.sshAuthType !== 'private_key',
    componentProps: {
      placeholder: '更换目标服务器时请重新填写密码',
    },
  },
  {
    label: 'SSH 私钥',
    field: 'sshPrivateKey',
    component: 'InputTextArea',
    slot: 'sshPrivateKey',
    colProps: { span: 24 },
    ifShow: ({ values }) => values.sshAuthType === 'private_key',
    componentProps: { rows: 4, placeholder: '-----BEGIN RSA PRIVATE KEY-----' },
  },
  {
    field: 'dividerMedia',
    component: 'Divider',
    label: `${NODE_TERM.mediaPort}（直播接入 / 推流转发）`,
    colProps: { span: 24 },
    ifShow: ({ values }) => formHasLive(values),
  },
  {
    label: '录像存储',
    field: 'recordingStorageMode',
    component: 'Select',
    defaultValue: 'central_shared',
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: {
      options: [
        { label: '中心共享存储（简化部署）', value: 'central_shared' },
        { label: '边缘本地存储（降低中心带宽）', value: 'edge_local' },
      ],
    },
    helpMessage: '中心共享：边缘节点必须实际挂载与中心相同的 NFS/CephFS，普通本地目录即使可写也不符合要求；边缘本地：持续录像保留在本节点，只同步事件图片、事件片段和索引，主节点按需代理播放。',
  },
  {
    label: '',
    field: 'centralStorageHint',
    component: 'Input',
    slot: 'centralStorageHint',
    colProps: { span: 24 },
    ifShow: ({ values }) => formHasLive(values) && values.recordingStorageMode === 'central_shared',
  },
  {
    label: '录像访问地址',
    field: 'mediaPublicUrl',
    component: 'Input',
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasLive(values) && values.recordingStorageMode === 'edge_local',
    componentProps: { placeholder: '如：http://edge-node.example:6000' },
    dynamicRules: ({ values }) => values.recordingStorageMode === 'edge_local'
      ? [
          { required: true, message: '边缘本地存储必须填写录像访问地址', trigger: ['change', 'blur'] },
          { pattern: /^https?:\/\//i, message: '请输入以 http:// 或 https:// 开头的地址', trigger: ['change', 'blur'] },
        ]
      : [],
    helpMessage: '填写主节点可以访问的边缘媒体 API 根地址，不要使用 localhost/127.0.0.1。',
  },
  {
    label: 'SRS RTMP 端口',
    field: 'srsRtmpPort',
    component: 'InputNumber',
    defaultValue: 1935,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'SRS HTTP 端口',
    field: 'srsHttpPort',
    component: 'InputNumber',
    defaultValue: 8080,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'SRS API 端口',
    field: 'srsApiPort',
    component: 'InputNumber',
    defaultValue: 1985,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'SRS WebRTC 端口',
    field: 'srsRtcPort',
    component: 'InputNumber',
    defaultValue: 8000,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
    helpMessage: 'SRS rtc_server 监听端口，勿与 ZLM WebRTC 端口相同',
  },
  {
    label: 'ZLM HTTP 端口',
    field: 'zlmHttpPort',
    component: 'InputNumber',
    defaultValue: 6080,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'ZLM RTMP 端口',
    field: 'zlmRtmpPort',
    component: 'InputNumber',
    defaultValue: 10935,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'ZLM RTSP 端口',
    field: 'zlmRtspPort',
    component: 'InputNumber',
    defaultValue: 8554,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'ZLM WebRTC 端口',
    field: 'zlmRtcPort',
    component: 'InputNumber',
    defaultValue: 8800,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
    helpMessage: 'ZLM [rtc] 监听端口，默认 8800，避免与 SRS WebRTC(8000) 冲突',
  },
  {
    label: 'ZLM RTP 端口起',
    field: 'zlmRtpPortMin',
    component: 'InputNumber',
    defaultValue: 30000,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'ZLM RTP 端口止',
    field: 'zlmRtpPortMax',
    component: 'InputNumber',
    slot: 'zlmRtpPortMax',
    defaultValue: 30500,
    colProps: { span: 16 },
    ifShow: ({ values }) => formHasLive(values),
    componentProps: { min: 1, max: 65535 },
  },
  {
    field: 'dividerMqtt',
    component: 'Divider',
    label: `${NODE_TERM.mqttPort}（物联接入）`,
    colProps: { span: 24 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
  },
  {
    label: 'MQTT TCP 端口',
    field: 'mqttTcpPort',
    component: 'InputNumber',
    defaultValue: 1883,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'MQTT SSL 端口',
    field: 'mqttSslPort',
    component: 'InputNumber',
    defaultValue: 8883,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'MQTT WS 端口',
    field: 'mqttWsPort',
    component: 'InputNumber',
    defaultValue: 8083,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'MQTT WSS 端口',
    field: 'mqttWssPort',
    component: 'InputNumber',
    defaultValue: 8084,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: 'Dashboard 端口',
    field: 'emqxDashboardPort',
    component: 'InputNumber',
    defaultValue: 18083,
    colProps: { span: 8 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { min: 1, max: 65535 },
  },
  {
    label: '集群 Cookie',
    field: 'emqxCookie',
    component: 'Input',
    defaultValue: 'emqxsecretcookie',
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { placeholder: '同集群 Cookie 必须一致' },
    helpMessage: 'EMQX 集群节点间认证 Cookie，多节点部署时保持一致',
  },
  {
    label: '集群 Seeds',
    field: 'emqxClusterSeeds',
    component: 'Input',
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'mqtt'),
    componentProps: { placeholder: 'emqx@10.0.0.31,emqx@10.0.0.32（单节点可留空）' },
    helpMessage: 'static discovery 种子列表；留空则自动使用本节点',
  },
  {
    field: 'dividerStorage',
    component: 'Divider',
    label: 'NFS 共享存储',
    colProps: { span: 24 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
  },
  {
    label: 'Ceph 存储池',
    field: 'cephPool',
    component: 'Select',
    defaultValue: STORAGE_TAG_DEFAULTS.cephPool,
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
    componentProps: {
      options: CEPH_POOL_OPTIONS.map(({ label, value }) => ({ label, value })),
    },
    helpMessage: '该 OSD 节点主要服务的 Ceph 存储池',
  },
  {
    label: 'OSD 数据路径',
    field: 'cephOsdPath',
    component: 'Input',
    defaultValue: STORAGE_TAG_DEFAULTS.cephOsdPath,
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
    componentProps: { placeholder: '/var/lib/ceph/osd' },
    helpMessage: 'Ceph OSD 数据目录',
  },
  {
    label: 'CephFS 名称',
    field: 'cephfsName',
    component: 'Input',
    defaultValue: STORAGE_TAG_DEFAULTS.cephfsName,
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
    componentProps: { placeholder: 'easyaiot' },
    helpMessage: '客户端挂载使用的 CephFS 文件系统名',
  },
  {
    label: 'Ceph MON 地址',
    field: 'cephMonHost',
    component: 'Input',
    defaultValue: STORAGE_TAG_DEFAULTS.cephMonHost,
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
    componentProps: { placeholder: 'storage-ceph 或 10.0.0.21' },
    helpMessage: 'Ceph Monitor 集群 VIP 或主机名',
  },
  {
    label: 'CephFS 挂载根路径',
    field: 'mediaMountPath',
    component: 'Input',
    defaultValue: STORAGE_TAG_DEFAULTS.mediaMountPath,
    colProps: { span: 12 },
    ifShow: ({ values }) => formHasFunction(values, 'nfs'),
    componentProps: { placeholder: '/mnt/easyaiot-media' },
    helpMessage: 'CephFS 客户端挂载 easyaiot 媒体存储的根路径',
  },
];

/** 添加中心节点抽屉 */
export const controlPlanePeerFormSchema: FormSchema[] = [
  {
    field: 'dividerPeer',
    component: 'Divider',
    label: '互联信息',
    colProps: { span: 24 },
  },
  {
    label: '中心节点名称',
    field: 'name',
    required: true,
    component: 'Input',
    colProps: { span: 12 },
    componentProps: { placeholder: '如：机房 B 控制面' },
  },
  {
    label: 'API 根地址',
    field: 'apiBaseUrl',
    required: true,
    component: 'Input',
    colProps: { span: 12 },
    componentProps: { placeholder: 'http://10.0.0.2:48080/admin-api' },
    helpMessage: '对端中心节点的管理 API 根路径，需网络可达',
  },
  {
    field: 'dividerAuth',
    component: 'Divider',
    label: '认证与备注',
    colProps: { span: 24 },
  },
  {
    label: '互联令牌',
    field: 'peerToken',
    component: 'Input',
    colProps: { span: 12 },
    componentProps: { placeholder: '双方协商一致；留空则自动生成' },
  },
  {
    label: '备注',
    field: 'remark',
    component: 'Input',
    colProps: { span: 12 },
  },
];

export const basicDetailSchema: DescItem[] = [
  { field: 'id', label: '节点 ID' },
  { field: 'host', label: '主机地址' },
  { field: 'sshPort', label: 'SSH 端口', render: (val) => val ?? 22 },
  { field: 'agentPort', label: NODE_TERM.agentPort, render: (val) => val ?? 9100 },
  {
    field: 'functions',
    label: '节点功能',
    render: (_val, data) => formatNodeFunctions(data),
  },
  {
    field: 'functionsDesc',
    label: '功能说明',
    span: 2,
    render: (_val, data) => {
      const ids = parseNodeFunctions(data);
      if (!ids.length) return '-';
      return ids.map((id) => NODE_FUNCTION_DESC[id] || id).join('；');
    },
  },
  { field: 'region', label: '区域', render: (val) => val || '-' },
  {
    field: 'gpuInfo',
    label: 'GPU 硬件',
    render: (_val, data) => formatGpuSummary(data?.gpuInfo),
  },
  {
    field: 'maxGpuCount',
    label: 'GPU 数量',
    render: (val) => {
      if (val != null && val > 0) return val;
      return '无';
    },
  },
  { field: 'activeTasks', label: NODE_METRIC.runningTasks, render: (val) => val ?? 0 },
  {
    field: 'lastHeartbeatAt',
    label: '最近心跳',
    span: 2,
    render: (val) => (val ? formatToDateTime(val) : '-'),
  },
  {
    field: 'sshLastTestOk',
    label: 'SSH 测试',
    span: 2,
    render(val, data) {
      const tag =
        val === true
          ? useRender.renderTag('最近测试通过', 'success')
          : val === false
            ? useRender.renderTag('最近测试失败', 'error')
            : useRender.renderTag('未测试', 'default');
      const time = data?.sshLastTestAt
        ? h('span', { style: { marginLeft: '8px', color: '#888' } }, formatToDateTime(data.sshLastTestAt))
        : null;
      return h('span', {}, [tag, time]);
    },
  },
  {
    field: 'remark',
    label: '备注',
    span: 2,
    show: (data) => !!data?.remark,
  },
];

/** 节点纳管抽屉 — 节点概览 */
export const nodeSetupSummarySchema: DescItem[] = [
  { field: 'name', label: '节点名称', labelMinWidth: 108 },
  {
    field: 'status',
    label: '节点状态',
    labelMinWidth: 108,
    render: (val) => renderNodeStatusBadge(val),
  },
  {
    field: 'functions',
    label: '节点功能',
    labelMinWidth: 108,
    render: (_val, data) => renderNodeRoleBadge(data),
  },
  { field: 'host', label: '主机地址', labelMinWidth: 108 },
  { field: 'id', label: '节点 ID', labelMinWidth: 108 },
  {
    field: 'sshUsername',
    label: 'SSH 用户名',
    labelMinWidth: 108,
    render: (val, data) => formatSshUsername(val, data),
  },
  {
    field: 'sshPort',
    label: 'SSH 端口',
    labelMinWidth: 108,
    render: (val) => val ?? 22,
  },
  {
    field: 'agentPort',
    label: NODE_TERM.agentPort,
    labelMinWidth: 108,
    render: (val) => val ?? 9100,
  },
];

export const mediaDetailSchema: DescItem[] = [
  {
    field: 'recordingStorageMode',
    label: '录像存储模式',
    render: (val) => val === 'edge_local' ? '边缘本地存储' : '中心共享存储',
  },
  {
    field: 'recordingStorageState',
    label: '配置状态',
    render: (val, data) => {
      if (val === 'active') return useRender.renderTag(`已生效 · v${data?.recordingStorageGeneration ?? 1}`, 'success');
      if (val === 'failed') return useRender.renderTag('应用失败', 'error');
      return useRender.renderTag('等待应用', 'warning');
    },
  },
  {
    field: 'mediaPublicUrl',
    label: '边缘录像地址',
    span: 2,
    show: (data) => data?.recordingStorageMode === 'edge_local',
    render: (val) => val || '-',
  },
  {
    field: 'recordingStorageError',
    label: '应用错误',
    span: 2,
    show: (data) => !!data?.recordingStorageError,
    render: (val) => val || '-',
  },
  {
    field: 'tags.srs_rtmp_port',
    label: 'SRS RTMP',
    render: (_val, data) => data?.tags?.srs_rtmp_port ?? 1935,
  },
  {
    field: 'tags.srs_http_port',
    label: 'SRS HTTP',
    render: (_val, data) => data?.tags?.srs_http_port ?? 8080,
  },
  {
    field: 'tags.srs_api_port',
    label: 'SRS API',
    render: (_val, data) => data?.tags?.srs_api_port ?? 1985,
  },
  {
    field: 'tags.srs_rtc_port',
    label: 'SRS WebRTC',
    render: (_val, data) => data?.tags?.srs_rtc_port ?? 8000,
  },
  {
    field: 'tags.zlm_http_port',
    label: 'ZLM HTTP',
    render: (_val, data) => data?.tags?.zlm_http_port ?? 6080,
  },
  {
    field: 'tags.zlm_rtmp_port',
    label: 'ZLM RTMP',
    render: (_val, data) => data?.tags?.zlm_rtmp_port ?? 10935,
  },
  {
    field: 'tags.zlm_rtsp_port',
    label: 'ZLM RTSP',
    render: (_val, data) => data?.tags?.zlm_rtsp_port ?? 8554,
  },
  {
    field: 'tags.zlm_rtc_port',
    label: 'ZLM WebRTC',
    render: (_val, data) => data?.tags?.zlm_rtc_port ?? 8800,
  },
  {
    field: 'tags.zlm_rtp_port_min',
    label: 'ZLM RTP 范围',
    span: 2,
    render: (_val, data) =>
      `${data?.tags?.zlm_rtp_port_min ?? 30000} - ${data?.tags?.zlm_rtp_port_max ?? 30500}`,
  },
];

export const mqttDetailSchema: DescItem[] = [
  {
    field: 'tags.mqtt_tcp_port',
    label: 'MQTT TCP',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).mqttTcpPort,
  },
  {
    field: 'tags.mqtt_ssl_port',
    label: 'MQTT SSL',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).mqttSslPort,
  },
  {
    field: 'tags.mqtt_ws_port',
    label: 'MQTT WS',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).mqttWsPort,
  },
  {
    field: 'tags.mqtt_wss_port',
    label: 'MQTT WSS',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).mqttWssPort,
  },
  {
    field: 'tags.emqx_dashboard_port',
    label: 'Dashboard',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).emqxDashboardPort,
  },
  {
    field: 'tags.emqx_cookie',
    label: '集群 Cookie',
    render: (_val, data) => readMqttPortsFromTags(data?.tags).emqxCookie || MQTT_TAG_DEFAULTS.emqxCookie,
  },
  {
    field: 'tags.emqx_cluster_seeds',
    label: '集群 Seeds',
    span: 2,
    render: (_val, data) => readMqttPortsFromTags(data?.tags).emqxClusterSeeds || '（单节点）',
  },
];

export const storageDetailSchema: DescItem[] = [
  {
    field: 'tags.ceph_pool',
    label: 'Ceph 存储池',
    render: (_val, data) => readStorageTagsFromTags(data?.tags).cephPool,
  },
  {
    field: 'tags.ceph_osd_path',
    label: 'OSD 数据路径',
    render: (_val, data) => readStorageTagsFromTags(data?.tags).cephOsdPath,
  },
  {
    field: 'tags.cephfs_name',
    label: 'CephFS 名称',
    render: (_val, data) => readStorageTagsFromTags(data?.tags).cephfsName,
  },
  {
    field: 'tags.ceph_mon_host',
    label: 'Ceph MON',
    render: (_val, data) => readStorageTagsFromTags(data?.tags).cephMonHost,
  },
  {
    field: 'tags.media_mount_path',
    label: 'CephFS 挂载根路径',
    span: 2,
    render: (_val, data) => readStorageTagsFromTags(data?.tags).mediaMountPath,
  },
];

export const cephMountDetailSchema: DescItem[] = [
  {
    field: 'tags.ceph_mount_ready',
    label: '客户端挂载',
    render: (_val, data) => renderCephMountBadge(data?.tags),
  },
  {
    field: 'tags.ceph_mount_path',
    label: '挂载路径',
    render: (_val, data) => {
      const { mountPath, status } = readCephMountFromTags(data?.tags);
      if (mountPath) return mountPath;
      return status === 'unknown' ? '等待 Agent 心跳上报' : '-';
    },
  },
  {
    field: 'tags.cluster_mode',
    label: '集群模式',
    span: 2,
    render: (_val, data) => {
      const raw = data?.tags?.cluster_mode;
      if (raw == null || raw === '') return '未上报';
      return ['true', '1', 'yes'].includes(String(raw).toLowerCase()) ? '已启用' : '未启用';
    },
  },
];

export const gpuColumns: BasicColumn[] = [
  { title: '序号', dataIndex: 'id', width: 60 },
  { title: '型号', dataIndex: 'name', ellipsis: true },
  {
    title: NODE_METRIC.gpuUtil,
    dataIndex: 'util',
    width: 90,
    customRender: ({ text }) => (text != null ? `${text}%` : '-'),
  },
  {
    title: NODE_METRIC.vram,
    dataIndex: 'mem_total_mb',
    width: 120,
    customRender: ({ record }) =>
      record.mem_total_mb
        ? `${Math.round(record.mem_used_mb ?? 0)}/${Math.round(record.mem_total_mb)}M`
        : '-',
  },
];
