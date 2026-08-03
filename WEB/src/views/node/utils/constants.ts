import { getCachedPlatformLanIp, fetchPlatformLanIp, needsPlatformLanIp } from './platformHost';

/** 阿里云控制台风格主色与排版 */
export const NODE_THEME = {
  primary: '#266cfb',
  primaryHover: '#1a5ae8',
  primaryLight: '#e8f0ff',
  primaryBg: '#f0f5ff',
  bg: '#ffffff',
  border: '#ebebeb',
  textPrimary: '#181818',
  textBody: '#333333',
  textSecondary: '#666666',
  textMuted: '#999999',
  fontTitle: '18px',
  fontSubtitle: '16px',
  fontBody: '14px',
  fontCaption: '13px',
  cardShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
  cardShadowHover: '0 6px 20px rgba(38, 108, 251, 0.12)',
  borderRadius: '8px',
} as const;

/**
 * 节点模块 — 用户可见术语规范（全模块唯一引用来源）
 *
 * 概念分层：
 * - 纳管：将节点纳入平台管理的过程（状态：待纳管 → 在线）
 * - 上线：节点变为「在线」，监测代理心跳正常
 * - 接入：网络与配置连通（平台接入地址、SSH）
 * - 部署：远程安装或更新组件（监测代理、流媒体引擎）
 * - 运维：对已部署服务的启停与卸载
 *
 * 固定用词：
 * - 监测代理（UI 不写 Agent / 节点代理 / 代理服务）
 * - 代理令牌（UI 不写 Agent Token）
 * - 流媒体引擎（UI 不写 流媒体服务 / 媒体栈）
 * - 平台接入地址（UI 不写 控制面 / 远程接入地址）
 * - 部署（UI 不写 安装）
 * - 纳管前检查（UI 不写 接入检查）
 * - 验证上线（纳管末步，不写 上线检查）
 * - 接入诊断（连通性排查，与纳管前检查区分）
 *
 * 页面 Tab 命名（按部署链路排序，不写 VIDEO / AI 等模块代号）：
 * 集群概览 → 节点管理 → 监测代理 → 分布式存储 → 流媒体引擎 → MQTT 网关
 * → 音视频转码 → 视频分析运行时 → 模型推理与训练
 */
export const NODE_TERM = {
  agent: '监测代理',
  agentToken: '代理令牌',
  agentPort: '监测代理端口',
  mediaService: '流媒体引擎',
  mqttService: 'MQTT 网关',
  storageService: 'Ceph 存储',
  mediaPort: '流媒体端口',
  mqttPort: 'MQTT 端口',
  platformUrl: '平台接入地址',
  remotePlatformUrl: '目标机平台接入地址',
  onboard: '纳管',
  onboardDrawer: '节点纳管',
  continueOnboard: '继续纳管',
  completeOnboard: '完成纳管',
  verifyOnline: '验证上线',
  preCheck: '纳管前检查',
  accessDiagnostic: '接入诊断',
  serviceDeploy: '服务部署',
  resourceMonitor: '资源监控',
  nodeConfig: '节点配置',
  nodeDetail: '节点详情',
  nodeInventory: '节点管理',
  clusterOverview: '集群概览',
  workloadBundleDistribute: '运行时分发',
  clusterEnvAgent: '监测代理',
  clusterEnvStorage: '分布式存储',
  clusterEnvMedia: '流媒体引擎',
  clusterEnvMqtt: 'MQTT 网关',
  clusterEnvFfmpeg: '音视频转码',
  clusterEnvVideo: '视频分析运行时',
  clusterEnvAi: '模型推理与训练',
  clusterEnvLlm: '大模型推理',
  clusterEnvTransform: '数据转发',
  pendingTitle: '节点待纳管',
  offlineTitle: '节点离线',
  maintenanceTitle: '维护模式',
  onlineSuccess: '节点已上线',
  notOnlineYet: '节点尚未上线',
  deploy: '部署',
  redeploy: '重新部署',
  remoteDeploy: '远程部署',
  ops: '运维操作',
  deployCheck: '部署检测',
  sshCheck: 'SSH 连通性检测',
  editNode: '编辑节点',
  addNode: '添加节点',
  viewDetail: '详情',
  attentionNodes: '需关注节点',
  controlPlaneNode: '控制面节点',
  controlPlaneNodeReadonly: '控制面节点仅可查看，不可编辑',
  centralNode: '中心节点',
  workerNode: '工作节点',
  swimlaneView: '泳道视图',
  tableView: '表格视图',
  cardView: '卡片视图',
  addCentralNode: '添加中心节点',
  syncCentralNode: '同步互联',
  currentCentralNode: '当前中心节点',
  laneWorkers: '工作节点',
  laneBatchSelectAll: '全选本泳道',
  laneBatchMaintenanceOn: '批量维护',
  laneBatchMaintenanceOff: '退出维护',
  laneBatchAgent: '批量部署监测代理',
  laneBatchStorage: '批量部署分布式存储',
  laneBatchMedia: '批量部署流媒体引擎',
  laneBatchMqtt: '批量部署 MQTT 网关',
  laneBatchFfmpeg: '批量分发音视频转码',
  laneBatchVideo: '批量分发视频分析',
  laneBatchAi: '批量分发模型训练',
  laneBatchLlm: '批量分发大模型推理',
  laneScrollLeft: '向左滚动',
  laneScrollRight: '向右滚动',
  laneRemoteHint: '远程中心节点（只读展示，操控请在对端操作）',
} as const;

export const NODE_STATUS_MAP: Record<string, { text: string; color: string }> = {
  pending: { text: '待纳管', color: 'processing' },
  online: { text: '在线', color: 'success' },
  offline: { text: '离线', color: 'error' },
  maintenance: { text: '维护中', color: 'warning' },
};

/** 卡片状态徽标样式 */
export const NODE_STATUS_BADGE: Record<string, { bg: string; color: string; border: string }> = {
  pending: { bg: '#f0f5ff', color: '#2f54eb', border: '#adc6ff' },
  online: { bg: '#f6ffed', color: '#389e0d', border: '#b7eb8f' },
  offline: { bg: '#fff1f0', color: '#cf1322', border: '#ffa39e' },
  maintenance: { bg: '#fffbe6', color: '#d48806', border: '#ffe58f' },
};

export const NODE_ROLE_MAP: Record<string, string> = {
  compute: '计算节点',
  gpu: 'GPU 节点',
  media: '媒体节点',
  mqtt: 'MQTT网关节点',
  storage: '存储节点',
  hybrid: '混合节点',
};

export const NODE_ROLE_DESC: Record<string, string> = {
  compute: '无 GPU，用于 CPU 推理、轻量算法或推流转发',
  gpu: '配备 GPU，用于模型推理、深度学习算法等算力密集型任务',
  media: '用于 SRS/ZLM 流媒体集群，设备拉流/推流',
  mqtt: '用于 EMQX MQTT 集群，设备物联网协议接入',
  storage: 'Ceph OSD 节点，承载录像/抓拍分布式存储',
  hybrid: '同时承担计算与媒体调度',
};

/** 可参与计算工作负载调度的节点角色 */
export const SCHEDULABLE_COMPUTE_ROLES = ['compute', 'gpu', 'hybrid'] as const;

export function isSchedulableComputeNode(node?: { nodeRole?: string | null } | null): boolean {
  const role = node?.nodeRole;
  return !!role && (SCHEDULABLE_COMPUTE_ROLES as readonly string[]).includes(role);
}

/**
 * 节点监控术语规范（全模块统一引用，避免歧义）
 *
 * - 内存：系统 RAM，与 GPU 显存严格区分
 * - 显存：GPU VRAM，不以「GPU」单独指代显存占用
 * - 磁盘：本地文件系统根分区，与对象存储（MinIO）区分
 * - 使用率：百分比占用指标的统一后缀
 * - 利用率：仅用于 GPU 算力（compute util）
 */
export const NODE_METRIC = {
  cpu: 'CPU',
  cpuUsage: 'CPU 使用率',
  mem: '内存',
  memUsage: '内存使用率',
  vram: '显存',
  vramUsage: '显存使用率',
  gpuUtil: 'GPU 利用率',
  disk: '磁盘',
  diskUsage: '磁盘使用率',
  runningTasks: '运行任务',
} as const;

/** 集群概览「查看节点」下拉中表示全部节点的 sentinel 值（避免与真实 nodeId=0 冲突） */
export const OVERVIEW_ALL_NODES_ID = -1;

/** 折线图采样间隔（秒） */
export const TREND_SAMPLE_INTERVAL_DEFAULT = 5;
export const TREND_SAMPLE_INTERVAL_OPTIONS = [
  { label: '1 秒', value: 1 },
  { label: '5 秒', value: 5 },
  { label: '10 秒', value: 10 },
] as const;
export type TrendSampleIntervalSec = (typeof TREND_SAMPLE_INTERVAL_OPTIONS)[number]['value'];

export const NODE_DASHBOARD = {
  statTotal: '节点总数',
  statGpuCount: 'GPU 卡数',
  statRunningTasks: '运行任务',
  statVramCapacity: '显存',
  statMemCapacity: '内存',
  statDiskCapacity: '磁盘',
  statCapacityUsageAvg: '平均',
  statOnlineRate: '节点在线率',
  overviewNodeFocus: '查看节点',
  overviewNodeFocusAll: '全部节点（集群汇总）',
  overviewCentralNode: '中心节点',
  overviewCentralNodeLocal: '本机中心节点',
  overviewCentralNodeAll: '全部中心节点',
  overviewBackToAll: '返回全部节点',
  overviewNodeFocusHint: '选择单个节点后，下方资源图表仅展示该节点数据',
  openPanel: '容器运维控制台',
  openPanelHint: '容器管理、一键部署与运行诊断',
  openPanelAction: '打开控制台',
  clusterLoad: '集群资源负载',
  sectionVram: '节点显存分布',
  sectionVramHint: '各 GPU 卡的显存使用率',
  sectionDisk: '节点磁盘使用',
  sectionDiskHint: '根分区磁盘使用率，按使用率从高到低排列',
  sectionResource: '节点资源概览',
  sectionResourceHint: 'CPU、内存、显存、磁盘一览',
  avgVramUsage: '平均显存',
  avgCpuUsage: '平均 CPU',
  avgMemUsage: '平均内存',
  avgDiskUsage: '平均磁盘',
  trendViewCluster: '集群平均',
  trendViewNode: '按节点',
  trendMetricLabel: '指标',
  trendNodeFilter: '节点筛选',
  trendNodeFilterAll: '全部节点',
  trendClusterHint: '按节点展示 CPU 使用率（%）及内存 / 显存 / 磁盘已用量',
  trendClusterMetricHint: '左轴：各节点 CPU 使用率（%）；右轴：各节点内存 / 显存 / 磁盘已用量',
  trendNodeHint: '按节点对比单一指标；CPU 为用量（%），内存 / 显存 / 磁盘为已用量',
  trendNodeVolumeHint: '当前指标（已用量）：',
  trendNodePercentHint: '当前指标（GPU 利用率）：',
  trendAxisPercent: 'CPU 使用率 %',
  trendAxisVolume: '已用量',
  trendSampleIntervalLabel: '采样间隔',
  trendSampleIntervalHint: '折线图追加数据点的时间间隔，间隔内仅更新最新点',
  wsConnected: '实时推送中',
  wsConnecting: '连接中…',
  wsDisconnected: '连接已断开，正在重连',
  vramTight: '显存不足',
  diskTight: '磁盘不足',
  usageHigh: '使用率偏高',
  diskWarningNodes: (count: number) => `${count} 台节点磁盘不足`,
  colName: '名称',
  colHost: 'IP 地址',
  colStatus: '状态',
  diskColUsage: '使用率',
  diskColCapacity: '容量',
  vramColUsed: '已用',
  noComputeNodes: '暂无计算节点数据',
  noVramData: '暂无在线节点的显存数据。请确认已安装 NVIDIA 驱动，且监测代理心跳正常上报。',
  noDiskData: '暂无磁盘使用数据。请确认监测代理已上线并正常上报心跳。',
} as const;

/** 节点详情抽屉 */
export const NODE_DETAIL = {
  title: NODE_TERM.nodeDetail,
  tabResource: NODE_TERM.resourceMonitor,
  tabConfig: NODE_TERM.nodeConfig,
  tabAccess: NODE_TERM.preCheck,
  tabMediaDeploy: NODE_TERM.mediaService,
  tabMqttDeploy: NODE_TERM.mqttService,
  tabStorageDeploy: NODE_TERM.storageService,
  tabAgentDeploy: NODE_TERM.agent,
  sectionStorage: 'Ceph 存储',
  sectionResource: '资源使用',
  sectionResourceHint: 'CPU、内存、显存、磁盘占用，与集群概览维度一致',
  sectionConfig: NODE_TERM.nodeConfig,
  sectionAccess: NODE_TERM.preCheck,
  sectionMedia: NODE_TERM.mediaService,
  sectionMqtt: NODE_TERM.mqttService,
  sectionAgent: NODE_TERM.agent,
  sectionVerify: NODE_TERM.verifyOnline,
  gpuSection: 'GPU 算力与显存',
  gpuSectionHint: 'GPU 利用率与显存使用率分开展示',
  noMetrics: '暂无资源数据。节点上线且监测代理心跳正常后将自动上报。',
  pendingAlert: `节点待纳管，请前往「${NODE_TERM.clusterEnvMedia}」或「${NODE_TERM.clusterEnvAgent}」完成组件部署。`,
  offlineAlert: `节点离线，请检查${NODE_TERM.agent}、网络连通性或维护模式设置。`,
  maintenanceAlert: '节点处于维护模式，不会参与任务调度。',
  actionEdit: NODE_TERM.editNode,
  actionSetup: NODE_TERM.continueOnboard,
  actionRefresh: '刷新状态',
  actionMaintenance: '维护模式',
  actionResetToken: `重置${NODE_TERM.agentToken}`,
  footerClose: '关闭',
  pendingMessage: NODE_TERM.pendingTitle,
  offlineMessage: NODE_TERM.offlineTitle,
  maintenanceMessage: NODE_TERM.maintenanceTitle,
} as const;

/**
 * 页面级 Tab（index.vue 顺序即推荐部署链路）
 * 1 集群概览 → 2 节点管理 → 3 监测代理 → 4 分布式存储 → 5 流媒体引擎
 * → 6 音视频转码 → 7 视频分析运行时 → 8 模型推理与训练
 */
export const NODE_PAGE = {
  clusterOverview: NODE_TERM.clusterOverview,
  nodeInventory: NODE_TERM.nodeInventory,
  workloadBundleDistribute: NODE_TERM.workloadBundleDistribute,
  clusterEnvAgent: NODE_TERM.clusterEnvAgent,
  clusterEnvStorage: NODE_TERM.clusterEnvStorage,
  clusterEnvMedia: NODE_TERM.clusterEnvMedia,
  clusterEnvMqtt: NODE_TERM.clusterEnvMqtt,
  clusterEnvFfmpeg: NODE_TERM.clusterEnvFfmpeg,
  clusterEnvVideo: NODE_TERM.clusterEnvVideo,
  clusterEnvAi: NODE_TERM.clusterEnvAi,
  clusterEnvLlm: NODE_TERM.clusterEnvLlm,
  clusterEnvTransform: NODE_TERM.clusterEnvTransform,
} as const;

/** 服务部署 Tab 键（与 index.vue TabPane key 一致） */
export const NODE_SERVICE_TAB = {
  agent: '3',
  storage: '4',
  media: '5',
  ffmpeg: '6',
  video: '7',
  ai: '8',
  llm: '9',
  mqtt: '10',
} as const;

/** 泳道批量「组件分发」跳转（按部署链路排序） */
export const LANE_BATCH_DEPLOY_ACTIONS = [
  { tab: NODE_SERVICE_TAB.agent, label: NODE_TERM.laneBatchAgent, icon: 'ant-design:cloud-upload-outlined' },
  { tab: NODE_SERVICE_TAB.storage, label: NODE_TERM.laneBatchStorage, icon: 'ant-design:database-outlined' },
  { tab: NODE_SERVICE_TAB.media, label: NODE_TERM.laneBatchMedia, icon: 'ant-design:play-circle-outlined' },
  { tab: NODE_SERVICE_TAB.mqtt, label: NODE_TERM.laneBatchMqtt, icon: 'ant-design:api-outlined' },
  { tab: NODE_SERVICE_TAB.ffmpeg, label: NODE_TERM.laneBatchFfmpeg, icon: 'ant-design:video-camera-outlined' },
  { tab: NODE_SERVICE_TAB.video, label: NODE_TERM.laneBatchVideo, icon: 'ant-design:deployment-unit-outlined' },
  { tab: NODE_SERVICE_TAB.ai, label: NODE_TERM.laneBatchAi, icon: 'ant-design:experiment-outlined' },
  { tab: NODE_SERVICE_TAB.llm, label: NODE_TERM.laneBatchLlm, icon: 'ant-design:robot-outlined' },
] as const;

export type NodeServiceTabKey = keyof typeof NODE_SERVICE_TAB;

/** 待纳管节点应跳转的服务部署 Tab */
export function resolveOnboardServiceTab(nodeRole?: string | null): string {
  if (nodeRole === 'storage') return NODE_SERVICE_TAB.storage;
  if (nodeRole === 'media' || nodeRole === 'hybrid') return NODE_SERVICE_TAB.media;
  if (nodeRole === 'mqtt') return NODE_SERVICE_TAB.mqtt;
  return NODE_SERVICE_TAB.agent;
}

/** 集群环境初始化 — 节点角色筛选 */
export const CLUSTER_NODE_ROLE_FILTERS = {
  /** 计算/推理工作负载节点 */
  computeWorkload: ['compute', 'gpu', 'hybrid'] as const,
  /** GPU 大模型推理节点 */
  gpuWorkload: ['gpu', 'hybrid'] as const,
  /** 需部署监测代理的全部角色（不含平台节点） */
  allManaged: ['compute', 'gpu', 'hybrid', 'media', 'mqtt', 'storage'] as const,
  /** 流媒体引擎节点 */
  media: ['media', 'hybrid'] as const,
  /** MQTT 网关节点 */
  mqtt: ['mqtt'] as const,
  /** Ceph 存储/MON 节点 */
  storage: ['storage'] as const,
  /** 需挂载 CephFS 的节点 */
  cephClient: ['compute', 'gpu', 'hybrid', 'media'] as const,
} as const;

export type ClusterNodeRoleFilterKey = keyof typeof CLUSTER_NODE_ROLE_FILTERS;

/** 工作负载 bundle 分发（目标机默认无外网，控制面离线打包 pip wheels） */
export const WORKLOAD_BUNDLE_TYPES = [
  {
    key: 'stream_forward',
    label: '推流转发',
    module: 'VIDEO',
    remoteRoot: '/opt/easyaiot/VIDEO',
    pythonLauncher: '/opt/easyaiot/VIDEO/.bundles/stream_forward/run-python.sh',
    scriptMarker: 'services/stream_forward_service/run_deploy.py',
    desc: '批量分发推流转发 run_deploy.py 及离线 Python 运行时（opencv/flask/sqlalchemy 等）',
  },
  {
    key: 'algorithm_realtime',
    label: '实时视频分析',
    module: 'VIDEO',
    remoteRoot: '/opt/easyaiot/VIDEO',
    pythonLauncher: '/opt/easyaiot/VIDEO/.bundles/algorithm_realtime/run-python.sh',
    scriptMarker: 'services/realtime_algorithm_service/run_deploy.py',
    desc: '批量分发实时视频分析运行时与部署脚本（含 onnxruntime 等）',
  },
  {
    key: 'algorithm_snap',
    label: '抓拍分析',
    module: 'VIDEO',
    remoteRoot: '/opt/easyaiot/VIDEO',
    pythonLauncher: '/opt/easyaiot/VIDEO/.bundles/algorithm_snap/run-python.sh',
    scriptMarker: 'services/snapshot_algorithm_service/run_deploy.py',
    desc: '批量分发抓拍分析运行时与部署脚本',
  },
  {
    key: 'algorithm_patrol',
    label: '轮巡分析',
    module: 'VIDEO',
    remoteRoot: '/opt/easyaiot/VIDEO',
    pythonLauncher: '/opt/easyaiot/VIDEO/.bundles/algorithm_patrol/run-python.sh',
    scriptMarker: 'services/patrol_algorithm_service/run_deploy.py',
    desc: '批量分发轮巡分析运行时与部署脚本',
  },
  {
    key: 'post_process',
    label: 'AI 后处理',
    module: 'VIDEO',
    remoteRoot: '/opt/easyaiot/VIDEO',
    pythonLauncher: '/opt/easyaiot/VIDEO/.bundles/post_process/run-python.sh',
    scriptMarker: 'services/post_process_worker/run_worker.py',
    desc: '批量分发 AI 后处理 Kafka Worker/Sink 运行时与脚本（集群订阅处理与落库）',
  },
  {
    key: 'transform_runtime',
    label: '数据转发 Runtime',
    module: 'TRANSFORM',
    remoteRoot: '/opt/easyaiot/TRANSFORM',
    pythonLauncher: '/opt/easyaiot/TRANSFORM/scripts/run-runtime.sh',
    scriptMarker: 'transform-runtime/target/transform-runtime-1.0.0.jar',
    desc: '无镜像则打包 gzip → SSH 分发 load → Agent 多容器 → iot_transform_heartbeat 验收；节点维部署',
  },
  {
    key: 'ai_service',
    label: '模型服务',
    module: 'AI',
    remoteRoot: '/opt/easyaiot/AI',
    pythonLauncher: '/opt/easyaiot/AI/.bundles/ai_service/run-python.sh',
    scriptMarker: 'services/ai_service/run_deploy.py',
    desc: '批量分发模型服务 run_deploy.py 及离线运行时（flask/onnxruntime/ultralytics 等）',
  },
  {
    key: 'auto_label',
    label: '智能标注',
    module: 'AI',
    remoteRoot: '/opt/easyaiot/AI',
    pythonLauncher: '/opt/easyaiot/AI/.bundles/ai_service/run-python.sh',
    scriptMarker: 'services/auto_label_worker/run_worker.py',
    desc: '分发智能标注运行时（SAM 辅助 + YOLO 量产），集群标注流水线必需',
  },
  {
    key: 'model_train',
    label: '模型训练',
    module: 'AI',
    remoteRoot: '/opt/easyaiot/AI',
    pythonLauncher: '/opt/easyaiot/AI/.bundles/model_train/run-python.sh',
    scriptMarker: 'services/train_worker/run_worker.py',
    desc: '分发模型训练运行时（YOLO 训练 + CephFS 共享数据集/输出目录）',
  },
  {
    key: 'llm_service',
    label: '大模型推理',
    module: 'AI',
    remoteRoot: '/opt/easyaiot/AI',
    pythonLauncher: '/opt/easyaiot/AI/.bundles/llm_service/run-python.sh',
    scriptMarker: 'services/llm_service/run_deploy.py',
    desc: '分发 Qwen 大模型 vLLM 运行时与部署脚本（transformers/vllm/torch 等）',
  },
] as const;

export const VIDEO_WORKLOAD_BUNDLE_TYPES = WORKLOAD_BUNDLE_TYPES.filter((b) => b.module === 'VIDEO');
export const AI_WORKLOAD_BUNDLE_TYPES = WORKLOAD_BUNDLE_TYPES.filter((b) => b.module === 'AI');
export const TRANSFORM_WORKLOAD_BUNDLE_TYPES = WORKLOAD_BUNDLE_TYPES.filter(
  (b) => b.module === 'TRANSFORM',
);

export type WorkloadBundleType = (typeof WORKLOAD_BUNDLE_TYPES)[number]['key'];

/** 旧版「运行时分发」Tab 跳转：按 bundle 类型映射到新 Tab key */
export function resolveLegacyWorkloadTab(bundleKey?: string): '7' | '8' | '9' | '11' {
  if (bundleKey === 'llm_service') return '9';
  if (bundleKey === 'transform_runtime') return '11';
  if (bundleKey && AI_WORKLOAD_BUNDLE_TYPES.some((b) => b.key === bundleKey)) return '8';
  return '7';
}

export const WORKLOAD_BUNDLE_COPY = {
  offlineHint:
    '目标服务器默认无外网：控制面在有网环境自动下载 pip wheel 并 SSH 同步至节点离线安装，无需节点联网。',
  selectNodes: '选择目标节点（需已配置 SSH 凭据，建议 compute / gpu / hybrid 角色）',
  targetNodes: '目标节点',
  deployEnv: '分发运行时',
  deployScripts: '分发脚本',
  deployFull: '全量分发',
  check: '检测',
  removeEnv: '删除运行时',
  removeScripts: '删除脚本',
  remotePythonTip:
    '分发完成后，请在对应业务控制面设置 NODE_REMOTE_PYTHON 为 run-python.sh 路径，或在节点 agent.env 中配置。',
  ffmpegHint:
    '推流与分析节点需 FFmpeg：控制面下载 BtbN 静态二进制包，SSH 同步至 /opt/easyaiot/tools/ffmpeg（无外网可离线安装）。全量分发视频分析运行时时会自动安装 FFmpeg。',
  ffmpegPath: '/opt/easyaiot/tools/ffmpeg/bin/ffmpeg',
  ffmpegDeploy: '分发 FFmpeg',
  ffmpegCheck: '检测 FFmpeg',
  ffmpegRemove: '删除 FFmpeg',
} as const;

/** 集群洞察文案 */
export const NODE_INSIGHT = {
  noNodesTitle: '尚未接入计算节点',
  noNodesDesc: `添加节点并完成${NODE_TERM.agent}纳管后，可在此查看推理调度能力与资源余量。`,
  noNodesAction: `切换到「${NODE_TERM.nodeInventory}」添加节点`,
  clusterDownTitle: '集群当前不可用',
  clusterDownDesc: '全部节点离线，模型部署与算法任务将无法被调度到任何机器。',
  clusterDownAction: `请检查${NODE_TERM.agent}、网络连通性或维护模式设置`,
  taskPressureTitle: '推理任务接近容量上限',
  overloadedTitle: (n: number) => `${n} 台节点资源紧张`,
  overloadedDesc: '部分计算节点 CPU、内存或磁盘使用率偏高，可能影响推理时延或模型落盘。',
  overloadedAction: '查看下方节点列表，考虑迁移任务或扩容',
  notReadyTitle: (n: number) => `${n} 台计算节点未就绪`,
  notReadyDesc: '离线或待纳管的节点不会参与调度，可用算力低于集群总量。',
  notReadyAction: `在「${NODE_TERM.nodeInventory}」添加节点，并在对应部署页完成纳管`,
  healthyTitle: '集群运行正常',
  pendingReason: `待完成${NODE_TERM.agent}纳管`,
  nodeOffline: '节点离线',
} as const;

export interface GpuInfoItem {
  id?: number;
  name?: string;
  util?: number;
  mem_used_mb?: number;
  mem_total_mb?: number;
}

export function parseGpuInfo(raw?: string | GpuInfoItem[] | null): GpuInfoItem[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function formatGpuSummary(raw?: string | GpuInfoItem[] | null): string {
  const list = parseGpuInfo(raw);
  if (!list.length) return '-';
  if (list.length === 1) return list[0].name || `GPU ${list[0].id ?? 0}`;
  return `${list.length} 张 GPU`;
}


export function getControlPlaneAgentUrl(): string {
  const envBase = import.meta.env.VITE_GLOB_BASE_URL?.trim();
  const windowBase =
    typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '';
  const base = resolveControlPlaneBase(envBase, windowBase, getCachedPlatformLanIp());
  return `${String(base).replace(/\/$/, '')}/admin-api/node/agent`;
}

/** 异步解析平台接入地址（localhost 时自动探测宿主机 IP） */
export async function resolveControlPlaneAgentUrl(): Promise<string> {
  const envBase = import.meta.env.VITE_GLOB_BASE_URL?.trim();
  const windowBase =
    typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '';
  if (needsPlatformLanIp(envBase, windowBase)) {
    await fetchPlatformLanIp();
  }
  return getControlPlaneAgentUrl();
}

/** 解析平台接入根地址：env/浏览器为 localhost 时使用探测到的宿主机 IP + 48080 */
function resolveControlPlaneBase(envBase?: string, windowBase?: string, lanIp?: string): string {
  const gatewayPort = '48080';
  const protocol =
    (() => {
      try {
        if (envBase) return new URL(envBase).protocol;
        if (windowBase) return new URL(windowBase).protocol;
      } catch {
        /* ignore */
      }
      return 'http:';
    })();

  const resolveWithLanIp = (port: string) => {
    if (lanIp && !isLoopbackHost(lanIp)) {
      return `${protocol}//${lanIp}:${port}`;
    }
    return null;
  };

  if (!envBase) {
    if (windowBase) {
      try {
        const win = new URL(windowBase);
        if (!isLoopbackHost(win.hostname)) {
          return `${win.protocol}//${win.hostname}:${gatewayPort}`;
        }
        const lanBase = resolveWithLanIp(gatewayPort);
        if (lanBase) return lanBase;
      } catch {
        /* ignore */
      }
    }
    const lanBase = resolveWithLanIp(gatewayPort);
    if (lanBase) return lanBase;
    return windowBase || `http://${lanIp || 'localhost'}:${gatewayPort}`;
  }
  try {
    const env = new URL(envBase);
    const port = env.port || gatewayPort;
    if (isLoopbackHost(env.hostname)) {
      if (windowBase) {
        const win = new URL(windowBase);
        if (!isLoopbackHost(win.hostname)) {
          return `${win.protocol}//${win.hostname}:${port}`;
        }
      }
      const lanBase = resolveWithLanIp(port);
      if (lanBase) return lanBase;
    }
    return envBase;
  } catch {
    return envBase;
  }
}

function isLoopbackHost(host?: string): boolean {
  const h = host?.trim().toLowerCase();
  return !h || h === 'localhost' || h === '127.0.0.1';
}

export function isLocalControlPlaneUrl(url?: string): boolean {
  if (!url?.trim()) return false;
  try {
    const host = new URL(url.trim()).hostname;
    return host === 'localhost' || host === '127.0.0.1';
  } catch {
    return /localhost|127\.0\.0\.1/.test(url);
  }
}

const CONTROL_PLANE_URL_STORAGE_PREFIX = 'easyaiot_node_control_plane_url:';

/** 读取纳管抽屉中为节点保存的平台接入地址（跨步骤共享） */
export function loadNodeControlPlaneUrl(nodeId?: number): string {
  const fallback = getControlPlaneAgentUrl();
  if (!nodeId) return fallback;
  try {
    const saved = sessionStorage.getItem(`${CONTROL_PLANE_URL_STORAGE_PREFIX}${nodeId}`);
    if (saved?.trim() && !isLocalControlPlaneUrl(saved)) return saved.trim();
  } catch {
    /* ignore */
  }
  return fallback;
}

/** 异步加载平台接入地址：忽略 session 中的 localhost，并自动探测宿主机 IP */
export async function loadNodeControlPlaneUrlAsync(nodeId?: number): Promise<string> {
  if (nodeId) {
    try {
      const saved = sessionStorage.getItem(`${CONTROL_PLANE_URL_STORAGE_PREFIX}${nodeId}`);
      if (saved?.trim() && !isLocalControlPlaneUrl(saved)) return saved.trim();
    } catch {
      /* ignore */
    }
  }
  return resolveControlPlaneAgentUrl();
}

export function saveNodeControlPlaneUrl(nodeId: number | undefined, url: string) {
  if (!nodeId || !url?.trim()) return;
  try {
    sessionStorage.setItem(`${CONTROL_PLANE_URL_STORAGE_PREFIX}${nodeId}`, url.trim());
  } catch {
    /* ignore */
  }
}

/** Gateway 地址，供 SRS/ZLM Hook 回调 VIDEO 服务 */
export function getControlPlaneHookEndpoint(): { host: string; port: number } {
  const envBase = import.meta.env.VITE_GLOB_BASE_URL?.trim();
  const windowBase =
    typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '';
  const base = resolveControlPlaneBase(envBase, windowBase, getCachedPlatformLanIp());
  try {
    const url = new URL(base);
    const port = url.port ? Number(url.port) : url.protocol === 'https:' ? 443 : 80;
    return { host: url.hostname, port };
  } catch {
    const lanIp = getCachedPlatformLanIp();
    return { host: lanIp || '127.0.0.1', port: 48080 };
  }
}

function sanitizeNodeName(name?: string): string {
  const raw = (name || 'media-node').trim().toLowerCase();
  const slug = raw.replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '');
  return slug || 'media-node';
}

/** 存储节点 tags 默认值（与 Ceph 集群规范一致） */
export const STORAGE_TAG_DEFAULTS = {
  cephPool: 'easyaiot-playbacks',
  cephOsdPath: '/var/lib/ceph/osd',
  cephfsName: 'easyaiot',
  cephMonHost: 'storage-ceph',
  mediaMountPath: '/mnt/easyaiot-media',
} as const;

export const CEPH_POOL_OPTIONS = [
  { label: 'easyaiot-playbacks（录像缓冲池）', value: 'easyaiot-playbacks' },
  { label: 'easyaiot-snaps（抓拍池）', value: 'easyaiot-snaps' },
] as const;

export interface StorageTagFields {
  cephPool: string;
  cephOsdPath: string;
  cephfsName: string;
  cephMonHost: string;
  mediaMountPath: string;
}

function tagString(tags: Record<string, string | undefined> | undefined, key: string, fallback: string): string {
  const raw = tags?.[key];
  return raw != null && raw !== '' ? raw : fallback;
}

/** 从节点 tags 解析存储配置（表单/详情共用；兼容旧 gluster_* 键） */
export function readStorageTagsFromTags(tags?: Record<string, string | undefined>): StorageTagFields {
  const legacyPool = tags?.gluster_volume;
  const legacyPoolMap: Record<string, string> = {
    'gv-playbacks': 'easyaiot-playbacks',
    'gv-snaps': 'easyaiot-snaps',
  };
  const cephPool =
    tagString(tags, 'ceph_pool', '') ||
    (legacyPool ? legacyPoolMap[legacyPool] || legacyPool : STORAGE_TAG_DEFAULTS.cephPool);
  return {
    cephPool,
    cephOsdPath: tagString(
      tags,
      'ceph_osd_path',
      tagString(tags, 'gluster_brick_path', STORAGE_TAG_DEFAULTS.cephOsdPath),
    ),
    cephfsName: tagString(tags, 'cephfs_name', STORAGE_TAG_DEFAULTS.cephfsName),
    cephMonHost: tagString(tags, 'ceph_mon_host', STORAGE_TAG_DEFAULTS.cephMonHost),
    mediaMountPath: tagString(tags, 'media_mount_path', STORAGE_TAG_DEFAULTS.mediaMountPath),
  };
}

/** CephFS 客户端挂载状态（Agent 心跳写入 tags.ceph_mount_ready） */
export type CephMountStatus = 'ready' | 'not_ready' | 'unknown';

export const CEPH_MOUNT_LABELS: Record<CephMountStatus, string> = {
  ready: 'Ceph 已挂载',
  not_ready: 'Ceph 未就绪',
  unknown: 'Ceph 未上报',
};

export function isClusterComputeRole(role?: string): boolean {
  return ['compute', 'gpu', 'hybrid'].includes(role || '');
}

export function readCephMountFromTags(tags?: Record<string, string | undefined>): {
  status: CephMountStatus;
  mountPath?: string;
} {
  const raw = tags?.ceph_mount_ready;
  const mountPath = tags?.ceph_mount_path || tags?.media_mount_path || undefined;
  if (raw == null || raw === '') {
    return { status: 'unknown', mountPath };
  }
  const ok = ['true', '1', 'yes', 'on'].includes(String(raw).toLowerCase());
  return { status: ok ? 'ready' : 'not_ready', mountPath };
}

/** 将表单存储配置写入节点 tags */
export function buildStorageTags(values: Record<string, unknown>): Record<string, string> {
  const d = STORAGE_TAG_DEFAULTS;
  return {
    ceph_pool: String(values.cephPool ?? d.cephPool),
    ceph_osd_path: String(values.cephOsdPath ?? d.cephOsdPath),
    cephfs_name: String(values.cephfsName ?? d.cephfsName),
    ceph_mon_host: String(values.cephMonHost ?? d.cephMonHost),
    media_mount_path: String(values.mediaMountPath ?? d.mediaMountPath),
  };
}

export const STORAGE_CLUSTER_REMOTE_DIR = '/opt/easyaiot/storage-cluster';

export const STORAGE_STACK_DEPLOY_PENDING_STEPS = [
  '同步 storage-cluster',
  'OSD 节点准备',
  '创建 Ceph 存储池',
  'CephFS 客户端挂载',
  '健康验证',
] as const;

export interface StorageStackScriptParams {
  host?: string;
  name?: string;
  nodeRole?: string;
  cephPool?: string;
  cephOsdPath?: string;
  cephfsName?: string;
  cephMonHost?: string;
  mediaMountPath?: string;
}

export interface StorageStackGuideState {
  isStorageRole: boolean;
  isReady: boolean;
  pendingItems: { key: string; label: string; done: boolean; hint?: string }[];
  readySummary: string;
}

function isValidStorageHost(host?: string): boolean {
  const h = host?.trim();
  return !!h && !h.includes('<') && !h.includes('>');
}

/** 存储栈脚本是否可生成 */
export function isStorageStackScriptReady(params?: StorageStackScriptParams): boolean {
  if (!params || params.nodeRole !== 'storage') return false;
  return isValidStorageHost(params.host) && !!params.cephMonHost?.trim() && !!params.mediaMountPath?.trim();
}

export function getStorageStackGuideState(params?: StorageStackScriptParams): StorageStackGuideState {
  const isStorageRole = params?.nodeRole === 'storage';
  const hostDone = isValidStorageHost(params?.host);
  const configDone =
    !!params?.cephMonHost?.trim() &&
    !!params?.cephfsName?.trim() &&
    !!params?.mediaMountPath?.trim() &&
    !!params?.cephOsdPath?.trim();
  const pendingItems = [
    { key: 'host', label: '主机地址', done: hostDone, hint: '存储节点 IP 或主机名' },
    { key: 'config', label: 'Ceph 配置', done: configDone, hint: 'MON 地址、CephFS 名称与挂载路径' },
  ];
  const isReady = isStorageStackScriptReady(params);
  let readySummary = '';
  if (isReady && params?.host) {
    readySummary =
      `目标机 ${params.host}：MON ${params.cephMonHost}，` +
      `CephFS ${params.cephfsName} 挂载至 ${params.mediaMountPath}，` +
      `OSD 路径 ${params.cephOsdPath}，存储池 ${params.cephPool || STORAGE_TAG_DEFAULTS.cephPool}`;
  }
  return { isStorageRole, isReady, pendingItems, readySummary };
}

export function buildStorageManualContent(params: StorageStackScriptParams = {}): string {
  const host = params.host?.trim() || '<目标服务器>';
  const mon = params.cephMonHost?.trim() || STORAGE_TAG_DEFAULTS.cephMonHost;
  const fs = params.cephfsName?.trim() || STORAGE_TAG_DEFAULTS.cephfsName;
  const mount = params.mediaMountPath?.trim() || STORAGE_TAG_DEFAULTS.mediaMountPath;
  return `# ========== 步骤 1：在 Ceph MON 节点创建存储池与 CephFS ==========
bash .scripts/media-cluster/ceph/pool-create.sh

# ========== 步骤 2：在各 OSD 存储节点准备 ==========
ssh root@${host} 'bash -s' < .scripts/media-cluster/ceph/install_ceph_osd.sh

# ========== 步骤 3：在客户端节点挂载 CephFS ==========
CEPH_MON=${mon} CEPHFS_NAME=${fs} MOUNT_ROOT=${mount} \\
  bash .scripts/media-cluster/ceph/mount-all.sh

# 健康检查
CEPH_MON=${mon} CEPHFS_NAME=${fs} MOUNT_ROOT=${mount} \\
  bash .scripts/media-cluster/ceph/check_ceph_health.sh`;
}

/** 媒体节点端口默认值（与 iot-node tags、install_media_stack.sh 一致） */
export const MEDIA_PORT_DEFAULTS = {
  srsRtmpPort: 1935,
  srsHttpPort: 8080,
  srsApiPort: 1985,
  srsRtcPort: 8000,
  zlmHttpPort: 6080,
  zlmRtmpPort: 10935,
  zlmRtspPort: 8554,
  zlmRtcPort: 8800,
  zlmRtpPortMin: 30000,
  zlmRtpPortMax: 30500,
} as const;

export interface MediaPortFields {
  srsRtmpPort: number;
  srsHttpPort: number;
  srsApiPort: number;
  srsRtcPort: number;
  zlmHttpPort: number;
  zlmRtmpPort: number;
  zlmRtspPort: number;
  zlmRtcPort: number;
  zlmRtpPortMin: number;
  zlmRtpPortMax: number;
}

function tagPort(tags: Record<string, string | undefined> | undefined, key: string, fallback: number): number {
  const raw = tags?.[key];
  if (raw == null || raw === '') return fallback;
  const n = Number(raw);
  return Number.isFinite(n) ? n : fallback;
}

/** 从节点 tags 解析媒体端口（表单/部署脚本共用） */
export function readMediaPortsFromTags(tags?: Record<string, string | undefined>): MediaPortFields {
  return {
    srsRtmpPort: tagPort(tags, 'srs_rtmp_port', MEDIA_PORT_DEFAULTS.srsRtmpPort),
    srsHttpPort: tagPort(tags, 'srs_http_port', MEDIA_PORT_DEFAULTS.srsHttpPort),
    srsApiPort: tagPort(tags, 'srs_api_port', MEDIA_PORT_DEFAULTS.srsApiPort),
    srsRtcPort: tagPort(tags, 'srs_rtc_port', MEDIA_PORT_DEFAULTS.srsRtcPort),
    zlmHttpPort: tagPort(tags, 'zlm_http_port', MEDIA_PORT_DEFAULTS.zlmHttpPort),
    zlmRtmpPort: tagPort(tags, 'zlm_rtmp_port', MEDIA_PORT_DEFAULTS.zlmRtmpPort),
    zlmRtspPort: tagPort(tags, 'zlm_rtsp_port', MEDIA_PORT_DEFAULTS.zlmRtspPort),
    zlmRtcPort: tagPort(tags, 'zlm_rtc_port', MEDIA_PORT_DEFAULTS.zlmRtcPort),
    zlmRtpPortMin: tagPort(tags, 'zlm_rtp_port_min', MEDIA_PORT_DEFAULTS.zlmRtpPortMin),
    zlmRtpPortMax: tagPort(tags, 'zlm_rtp_port_max', MEDIA_PORT_DEFAULTS.zlmRtpPortMax),
  };
}

/** 将表单媒体端口写入节点 tags */
export function buildMediaPortTags(values: Record<string, unknown>): Record<string, string> {
  const d = MEDIA_PORT_DEFAULTS;
  return {
    srs_rtmp_port: String(values.srsRtmpPort ?? d.srsRtmpPort),
    srs_http_port: String(values.srsHttpPort ?? d.srsHttpPort),
    srs_api_port: String(values.srsApiPort ?? d.srsApiPort),
    srs_rtc_port: String(values.srsRtcPort ?? d.srsRtcPort),
    zlm_http_port: String(values.zlmHttpPort ?? d.zlmHttpPort),
    zlm_rtmp_port: String(values.zlmRtmpPort ?? d.zlmRtmpPort),
    zlm_rtsp_port: String(values.zlmRtspPort ?? d.zlmRtspPort),
    zlm_rtc_port: String(values.zlmRtcPort ?? d.zlmRtcPort),
    zlm_rtp_port_min: String(values.zlmRtpPortMin ?? d.zlmRtpPortMin),
    zlm_rtp_port_max: String(values.zlmRtpPortMax ?? d.zlmRtpPortMax),
  };
}

export interface MediaStackScriptParams {
  name?: string;
  host?: string;
  srsRtmpPort?: number;
  srsHttpPort?: number;
  srsApiPort?: number;
  srsRtcPort?: number;
  zlmHttpPort?: number;
  zlmRtmpPort?: number;
  zlmRtspPort?: number;
  zlmRtcPort?: number;
  zlmRtpPortMin?: number;
  zlmRtpPortMax?: number;
}

function isValidHost(host?: string): boolean {
  const h = host?.trim();
  if (!h || h.includes('<') || h.includes('>')) return false;
  const ipv4 = /^(\d{1,3}\.){3}\d{1,3}$/;
  if (ipv4.test(h)) {
    return h.split('.').every((octet) => {
      const n = Number(octet);
      return Number.isInteger(n) && n >= 0 && n <= 255;
    });
  }
  return /^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$/.test(h);
}

function isValidPort(port?: number): boolean {
  return typeof port === 'number' && Number.isFinite(port) && port >= 1 && port <= 65535;
}

function areMediaPortsValid(params?: MediaStackScriptParams): boolean {
  if (!params) return false;
  const ports = [
    params.srsRtmpPort,
    params.srsHttpPort,
    params.srsApiPort,
    params.srsRtcPort,
    params.zlmHttpPort,
    params.zlmRtmpPort,
    params.zlmRtspPort,
    params.zlmRtcPort,
    params.zlmRtpPortMin,
    params.zlmRtpPortMax,
  ];
  if (!ports.every(isValidPort)) return false;
  if ((params.zlmRtpPortMin as number) > (params.zlmRtpPortMax as number)) return false;
  if (params.srsRtcPort === params.zlmRtcPort) return false;
  return true;
}

/** 媒体栈脚本是否可生成（角色为 media/hybrid 且 IP、端口已填写有效） */
export function isMediaStackScriptReady(
  params: (MediaStackScriptParams & { nodeRole?: string }) | undefined,
): boolean {
  if (!params || (params.nodeRole !== 'media' && params.nodeRole !== 'hybrid')) return false;
  return isValidHost(params.host) && areMediaPortsValid(params);
}

export interface MediaStackGuideItem {
  key: string;
  label: string;
  done: boolean;
  hint?: string;
}

export interface MediaStackGuideState {
  isMediaRole: boolean;
  isReady: boolean;
  pendingItems: MediaStackGuideItem[];
  readySummary: string;
}

/** 媒体栈部署引导状态（用于 UI 展示待填项与就绪摘要） */
export function getMediaStackGuideState(
  params: (MediaStackScriptParams & { nodeRole?: string }) | undefined,
): MediaStackGuideState {
  const isMediaRole = params?.nodeRole === 'media' || params?.nodeRole === 'hybrid';
  const hostDone = isValidHost(params?.host);
  const portsDone = areMediaPortsValid(params);
  const hook = getControlPlaneHookEndpoint();

  const pendingItems: MediaStackGuideItem[] = [
    {
      key: 'host',
      label: '主机地址',
      done: hostDone,
      hint: '目标节点 IP 或主机名',
    },
    {
      key: 'ports',
      label: '媒体端口',
      done: portsDone,
      hint: 'SRS/ZLM 监听端口，默认配置适用于空闲节点',
    },
  ];

  const isReady = isMediaStackScriptReady(params);
  let readySummary = '';
  if (isReady && params?.host) {
    readySummary =
      `目标机 ${params.host}：` +
      `SRS RTMP ${params.srsRtmpPort} / HTTP ${params.srsHttpPort} / API ${params.srsApiPort} / WebRTC ${params.srsRtcPort}，` +
      `ZLM HTTP ${params.zlmHttpPort} / RTMP ${params.zlmRtmpPort} / RTSP ${params.zlmRtspPort} / WebRTC ${params.zlmRtcPort}，` +
      `RTP ${params.zlmRtpPortMin}-${params.zlmRtpPortMax}，` +
      `Hook 回调 ${hook.host}:${hook.port}`;
  }

  return { isMediaRole, isReady, pendingItems, readySummary };
}

/** 流媒体远程自动部署进度步骤（与后端返回步骤名一致） */
export const MEDIA_STACK_DEPLOY_PENDING_STEPS = [
  '准备离线镜像',
  'SSH 连接',
  '端口占用检测',
  '检测已有服务',
  'Docker',
  '清理旧目录',
  '同步 media-cluster',
  'Docker Compose',
  '导入镜像',
  '启动服务',
  '服务验证',
] as const;

export const MEDIA_CLUSTER_REMOTE_DIR = '/opt/easyaiot/media-cluster';

export const MEDIA_CLUSTER_DIR = '.scripts/media-cluster';

/** MQTT 网关节点端口默认值（与 iot-node tags、install_mqtt_stack.sh 一致） */
export const MQTT_PORT_DEFAULTS = {
  mqttTcpPort: 1883,
  mqttSslPort: 8883,
  mqttWsPort: 8083,
  mqttWssPort: 8084,
  emqxDashboardPort: 18083,
} as const;

export const MQTT_TAG_DEFAULTS = {
  emqxCookie: 'emqxsecretcookie',
  emqxClusterSeeds: '',
  mqttAuthPort: 8090,
  mqttAuthPath: '/mqtt/auth',
} as const;

export interface MqttPortFields {
  mqttTcpPort: number;
  mqttSslPort: number;
  mqttWsPort: number;
  mqttWssPort: number;
  emqxDashboardPort: number;
  emqxCookie: string;
  emqxClusterSeeds: string;
}

/** 从节点 tags 解析 MQTT 端口与集群配置 */
export function readMqttPortsFromTags(tags?: Record<string, string | undefined>): MqttPortFields {
  return {
    mqttTcpPort: tagPort(tags, 'mqtt_tcp_port', MQTT_PORT_DEFAULTS.mqttTcpPort),
    mqttSslPort: tagPort(tags, 'mqtt_ssl_port', MQTT_PORT_DEFAULTS.mqttSslPort),
    mqttWsPort: tagPort(tags, 'mqtt_ws_port', MQTT_PORT_DEFAULTS.mqttWsPort),
    mqttWssPort: tagPort(tags, 'mqtt_wss_port', MQTT_PORT_DEFAULTS.mqttWssPort),
    emqxDashboardPort: tagPort(tags, 'emqx_dashboard_port', MQTT_PORT_DEFAULTS.emqxDashboardPort),
    emqxCookie: tagString(tags, 'emqx_cookie', MQTT_TAG_DEFAULTS.emqxCookie),
    emqxClusterSeeds: tagString(tags, 'emqx_cluster_seeds', MQTT_TAG_DEFAULTS.emqxClusterSeeds),
  };
}

/** 将表单 MQTT 配置写入节点 tags */
export function buildMqttPortTags(values: Record<string, unknown>): Record<string, string> {
  const d = MQTT_PORT_DEFAULTS;
  const t = MQTT_TAG_DEFAULTS;
  return {
    mqtt_tcp_port: String(values.mqttTcpPort ?? d.mqttTcpPort),
    mqtt_ssl_port: String(values.mqttSslPort ?? d.mqttSslPort),
    mqtt_ws_port: String(values.mqttWsPort ?? d.mqttWsPort),
    mqtt_wss_port: String(values.mqttWssPort ?? d.mqttWssPort),
    emqx_dashboard_port: String(values.emqxDashboardPort ?? d.emqxDashboardPort),
    emqx_cookie: String(values.emqxCookie ?? t.emqxCookie),
    emqx_cluster_seeds: String(values.emqxClusterSeeds ?? t.emqxClusterSeeds),
  };
}

export interface MqttStackScriptParams {
  name?: string;
  host?: string;
  mqttTcpPort?: number;
  mqttSslPort?: number;
  mqttWsPort?: number;
  mqttWssPort?: number;
  emqxDashboardPort?: number;
  emqxCookie?: string;
  emqxClusterSeeds?: string;
}

function areMqttPortsValid(params?: MqttStackScriptParams): boolean {
  if (!params) return false;
  return [params.mqttTcpPort, params.mqttSslPort, params.mqttWsPort, params.mqttWssPort, params.emqxDashboardPort].every(
    isValidPort,
  );
}

export function isMqttStackScriptReady(
  params: (MqttStackScriptParams & { nodeRole?: string }) | undefined,
): boolean {
  if (!params || params.nodeRole !== 'mqtt') return false;
  return isValidHost(params.host) && areMqttPortsValid(params);
}

export interface MqttStackGuideState {
  isMqttRole: boolean;
  isReady: boolean;
  pendingItems: MediaStackGuideItem[];
  readySummary: string;
}

export function getMqttStackGuideState(
  params: (MqttStackScriptParams & { nodeRole?: string }) | undefined,
): MqttStackGuideState {
  const isMqttRole = params?.nodeRole === 'mqtt';
  const hostDone = isValidHost(params?.host);
  const portsDone = areMqttPortsValid(params);
  const pendingItems: MediaStackGuideItem[] = [
    { key: 'host', label: '主机地址', done: hostDone, hint: '目标节点 IP 或主机名' },
    { key: 'ports', label: 'MQTT 端口', done: portsDone, hint: 'EMQX 监听端口，默认配置适用于空闲节点' },
  ];
  const isReady = isMqttStackScriptReady(params);
  let readySummary = '';
  if (isReady && params?.host) {
    readySummary =
      `目标机 ${params.host}：` +
      `MQTT ${params.mqttTcpPort} / SSL ${params.mqttSslPort} / WS ${params.mqttWsPort} / WSS ${params.mqttWssPort}，` +
      `Dashboard ${params.emqxDashboardPort}` +
      (params.emqxClusterSeeds ? `，集群 seeds ${params.emqxClusterSeeds}` : '（单节点）');
  }
  return { isMqttRole, isReady, pendingItems, readySummary };
}

export const MQTT_STACK_DEPLOY_PENDING_STEPS = [
  '准备离线镜像',
  'SSH 连接',
  '端口占用检测',
  '检测已有服务',
  'Docker',
  '清理旧目录',
  '同步 mqtt-cluster',
  'Docker Compose',
  '导入镜像',
  '启动服务',
  '服务验证',
] as const;

export const MQTT_CLUSTER_REMOTE_DIR = '/opt/easyaiot/mqtt-cluster';
export const MQTT_CLUSTER_DIR = '.scripts/mqtt-cluster';

export function buildMqttStackExportImagesCommand(): string {
  return `bash ${MQTT_CLUSTER_DIR}/export_mqtt_images.sh`;
}

export function buildMqttStackManualContent(params: MqttStackScriptParams = {}): string {
  const host = params.host?.trim() || '<目标服务器>';
  const exportCmd = buildMqttStackExportImagesCommand();
  const cleanRemote = `ssh root@${host} 'rm -rf ${MQTT_CLUSTER_REMOTE_DIR}/emqx; rm -f ${MQTT_CLUSTER_REMOTE_DIR}/install_mqtt_stack.sh ${MQTT_CLUSTER_REMOTE_DIR}/install_docker.sh ${MQTT_CLUSTER_REMOTE_DIR}/docker-compose.mqtt-node.yml; mkdir -p ${MQTT_CLUSTER_REMOTE_DIR}/images'`;
  const rsync = `rsync -avz --progress ${MQTT_CLUSTER_DIR}/ root@${host}:${MQTT_CLUSTER_REMOTE_DIR}/`;
  const deployScript = buildMqttStackInstallScript(params);
  return `# ========== 步骤 1：在本机（平台服务器）拉取并导出 EMQX 离线镜像 ==========
${exportCmd}

# ========== 步骤 2：清理目标机旧配置并增量同步 ==========
${cleanRemote}
${rsync}

# ========== 步骤 3：SSH 登录目标主机，docker load 导入并启动 EMQX ==========
${deployScript}`;
}

export function buildMqttStackInstallScript(params: MqttStackScriptParams = {}): string {
  const hook = getControlPlaneHookEndpoint();
  const nodeName = sanitizeNodeName(params.name || params.host).replace('media-node', 'mqtt-node');
  const host = params.host?.trim() || '';
  const mqttTcp = params.mqttTcpPort ?? MQTT_PORT_DEFAULTS.mqttTcpPort;
  const mqttSsl = params.mqttSslPort ?? MQTT_PORT_DEFAULTS.mqttSslPort;
  const mqttWs = params.mqttWsPort ?? MQTT_PORT_DEFAULTS.mqttWsPort;
  const mqttWss = params.mqttWssPort ?? MQTT_PORT_DEFAULTS.mqttWssPort;
  const dashboard = params.emqxDashboardPort ?? MQTT_PORT_DEFAULTS.emqxDashboardPort;
  const cookie = params.emqxCookie || MQTT_TAG_DEFAULTS.emqxCookie;
  const seeds = params.emqxClusterSeeds || '';

  return `#!/usr/bin/env bash
# EasyAIoT MQTT 网关节点 — EMQX 一键部署
set -euo pipefail

export MQTT_CLUSTER_ROOT="/opt/easyaiot/mqtt-cluster"
export MQTT_NODE_NAME="${nodeName}"
export MQTT_NODE_HOST="${host}"
export MQTT_AUTH_HOST="${hook.host}"
export MQTT_AUTH_PORT="${MQTT_TAG_DEFAULTS.mqttAuthPort}"
export MQTT_AUTH_PATH="${MQTT_TAG_DEFAULTS.mqttAuthPath}"
export MQTT_TCP_PORT=${mqttTcp}
export MQTT_SSL_PORT=${mqttSsl}
export MQTT_WS_PORT=${mqttWs}
export MQTT_WSS_PORT=${mqttWss}
export EMQX_DASHBOARD_PORT=${dashboard}
export EMQX_NODE_COOKIE="${cookie}"
export EMQX_CLUSTER_SEEDS="${seeds}"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] 未安装 Docker"
  exit 1
fi
if [[ ! -f "\${MQTT_CLUSTER_ROOT}/install_mqtt_stack.sh" ]]; then
  echo "[ERROR] 未找到 \${MQTT_CLUSTER_ROOT}/install_mqtt_stack.sh"
  echo "请先将仓库 .scripts/mqtt-cluster 同步到目标机"
  exit 1
fi

bash "\${MQTT_CLUSTER_ROOT}/install_mqtt_stack.sh"
echo "[OK] MQTT 网关部署完成"
echo "  MQTT: mqtt://\${MQTT_NODE_HOST}:\${MQTT_TCP_PORT}"
echo "  Dashboard: http://\${MQTT_NODE_HOST}:\${EMQX_DASHBOARD_PORT}"`;
}

/** 在本机导出 SRS/ZLM 离线镜像 */
export function buildMediaStackExportImagesCommand(): string {
  return `bash ${MEDIA_CLUSTER_DIR}/export_media_images.sh`;
}

/** 手动部署完整指引（含导出镜像、同步、目标机执行） */
export function buildMediaStackManualContent(params: MediaStackScriptParams = {}): string {
  const host = params.host?.trim() || '<目标服务器>';
  const exportCmd = buildMediaStackExportImagesCommand();
  const cleanRemote = `ssh root@${host} 'rm -rf ${MEDIA_CLUSTER_REMOTE_DIR}/srs ${MEDIA_CLUSTER_REMOTE_DIR}/zlm; rm -f ${MEDIA_CLUSTER_REMOTE_DIR}/install_media_stack.sh ${MEDIA_CLUSTER_REMOTE_DIR}/install_docker.sh ${MEDIA_CLUSTER_REMOTE_DIR}/docker-compose.media-node.yml; mkdir -p ${MEDIA_CLUSTER_REMOTE_DIR}/images'`;
  const rsync = `rsync -avz --progress ${MEDIA_CLUSTER_DIR}/ root@${host}:${MEDIA_CLUSTER_REMOTE_DIR}/`;
  const deployScript = buildMediaStackInstallScript(params);

  return `# ========== 步骤 1：在本机（平台服务器）拉取并导出离线镜像（必须） ==========
# 目标机不联网拉取镜像，所有镜像均在本机下载后通过 rsync 同步
${exportCmd}

# 导出产物（自动部署也会在本机缺失时执行此步骤）：
#   ${MEDIA_CLUSTER_DIR}/images/ossrs-srs-5.tar
#   ${MEDIA_CLUSTER_DIR}/images/zlmediakit-master.tar

# ========== 步骤 2：清理目标机旧配置并增量同步 ==========
# 仅清理脚本/配置目录，保留已有 images/*.tar；目标机已有 Docker 镜像时可跳过对应 tar
${cleanRemote}
${rsync}

# ========== 步骤 3：SSH 登录目标主机，docker load 导入并启动 SRS/ZLM ==========
${deployScript}`;
}

/** 生成可在媒体节点直接复制执行的 SRS + ZLM 部署脚本 */
export function buildMediaStackInstallScript(params: MediaStackScriptParams = {}): string {
  const hook = getControlPlaneHookEndpoint();
  const nodeName = sanitizeNodeName(params.name || params.host);
  const host = params.host?.trim() || '';
  const srsRtmp = params.srsRtmpPort ?? 1935;
  const srsHttp = params.srsHttpPort ?? 8080;
  const srsApi = params.srsApiPort ?? MEDIA_PORT_DEFAULTS.srsApiPort;
  const srsRtc = params.srsRtcPort ?? MEDIA_PORT_DEFAULTS.srsRtcPort;
  const zlmHttp = params.zlmHttpPort ?? MEDIA_PORT_DEFAULTS.zlmHttpPort;
  const zlmRtmp = params.zlmRtmpPort ?? MEDIA_PORT_DEFAULTS.zlmRtmpPort;
  const zlmRtsp = params.zlmRtspPort ?? MEDIA_PORT_DEFAULTS.zlmRtspPort;
  const zlmRtc = params.zlmRtcPort ?? MEDIA_PORT_DEFAULTS.zlmRtcPort;
  const zlmRtpMin = params.zlmRtpPortMin ?? 30000;
  const zlmRtpMax = params.zlmRtpPortMax ?? 30500;

  return `#!/usr/bin/env bash
# EasyAIoT 媒体节点 — SRS + ZLMediaKit 一键部署
# 在目标服务器 ${host} 上执行；若 SRS/ZLM 已在运行则自动跳过。
set -euo pipefail

# ---------- 1. 配置（与控制台表单一致，可按需修改） ----------
export MEDIA_CLUSTER_ROOT="/opt/easyaiot/media-cluster"
export MEDIA_NODE_NAME="${nodeName}"
export MEDIA_NODE_HOST="${host}"
export MEDIA_HOOK_HOST="${hook.host}"
export MEDIA_HOOK_PORT="${hook.port}"
export MEDIA_HOOK_PATH_PREFIX="/admin-api"
export SRS_CANDIDATE_IP="${host}"
export SRS_RTMP_PORT=${srsRtmp}
export SRS_HTTP_PORT=${srsHttp}
export SRS_API_PORT=${srsApi}
export SRS_RTC_PORT=${srsRtc}
export ZLM_HTTP_PORT=${zlmHttp}
export ZLM_RTMP_PORT=${zlmRtmp}
export ZLM_RTSP_PORT=${zlmRtsp}
export ZLM_RTP_PORT_MIN=${zlmRtpMin}
export ZLM_RTP_PORT_MAX=${zlmRtpMax}
export ZLM_RTC_PORT=${zlmRtc}
export ZLM_RTC_EXTERN_IP="${host}"
export ZLM_SECRET="EasyAIoT_Media_Secret"

# ---------- 2. 前置检查 ----------
if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] 未安装 Docker，请先安装 Docker Engine"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] Docker 未运行或无权限（可尝试 sudo 或 usermod -aG docker \\$USER）"
  exit 1
fi
if [[ ! -f "\${MEDIA_CLUSTER_ROOT}/install_media_stack.sh" ]]; then
  echo "[ERROR] 未找到 \${MEDIA_CLUSTER_ROOT}/install_media_stack.sh"
  echo "请先将仓库 .scripts/media-cluster 同步到目标机，例如:"
  echo "  rsync -avz .scripts/media-cluster/ root@${host}:\${MEDIA_CLUSTER_ROOT}/"
  exit 1
fi

# ---------- 3. 执行部署（已运行则跳过） ----------
echo ">>> 开始部署媒体栈: \${MEDIA_NODE_NAME} @ \${MEDIA_NODE_HOST}"
echo ">>> Hook 回调: \${MEDIA_HOOK_HOST}:\${MEDIA_HOOK_PORT}"
bash "\${MEDIA_CLUSTER_ROOT}/install_media_stack.sh"

echo ""
echo "[OK] 媒体栈部署完成"
echo "  SRS API: http://\${MEDIA_NODE_HOST}:\${SRS_API_PORT}/api/v1/versions"
echo "  ZLM API: http://\${MEDIA_NODE_HOST}:\${ZLM_HTTP_PORT}/index/api/getServerConfig"`;
}

/** 常见服务默认端口，随机生成时尽量避开 */
const COMMON_SERVICE_PORTS = new Set([
  22, 80, 443, 554, 8554, 873, 1935, 1985, 2181, 3306, 4379, 5432, 5672, 6379, 8080, 8443, 9000, 9001,
  9100, 9200, 9300, 9848, 10909, 10911, 10912, 48080, 6080, 10935, 5540,
]);

function randomInt(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1));
}

function pickUniquePort(used: Set<number>, min: number, max: number): number {
  for (let i = 0; i < 200; i++) {
    const port = randomInt(min, max);
    if (!used.has(port) && !COMMON_SERVICE_PORTS.has(port)) {
      used.add(port);
      return port;
    }
  }
  for (let port = min; port <= max; port++) {
    if (!used.has(port) && !COMMON_SERVICE_PORTS.has(port)) {
      used.add(port);
      return port;
    }
  }
  return min;
}

export interface RandomDeployPorts {
  agentPort: number;
  srsRtmpPort?: number;
  srsHttpPort?: number;
  srsApiPort?: number;
  srsRtcPort?: number;
  zlmHttpPort?: number;
  zlmRtmpPort?: number;
  zlmRtspPort?: number;
  zlmRtcPort?: number;
}

/** 生成一组互不冲突的部署端口（不含 RTP 范围端口） */
export function generateRandomDeployPorts(nodeRole?: string): RandomDeployPorts {
  const used = new Set<number>();
  const agentPort = pickUniquePort(used, 19100, 19999);
  const isMedia = nodeRole === 'media' || nodeRole === 'hybrid';
  if (!isMedia) {
    return { agentPort };
  }
  const anchor = 22000 + Math.floor(Math.random() * 80) * 100;
  return {
    agentPort,
    srsRtmpPort: pickUniquePort(used, anchor, anchor + 80),
    srsHttpPort: pickUniquePort(used, anchor + 100, anchor + 180),
    srsApiPort: pickUniquePort(used, anchor + 200, anchor + 280),
    srsRtcPort: pickUniquePort(used, anchor + 280, anchor + 360),
    zlmHttpPort: pickUniquePort(used, anchor + 400, anchor + 480),
    zlmRtmpPort: pickUniquePort(used, anchor + 500, anchor + 580),
    zlmRtspPort: pickUniquePort(used, anchor + 600, anchor + 680),
    zlmRtcPort: pickUniquePort(used, anchor + 700, anchor + 780),
  };
}

/** 添加节点时生成随机 Agent 监听端口（19100–19999，避开常见服务端口） */
export function generateDefaultAgentPort(): number {
  return generateRandomDeployPorts().agentPort;
}

export const AGENT_INSTALL_DIR = '/opt/easyaiot/node-agent';

export function buildAgentEnvContent(node: {
  id?: number;
  agentPort?: number;
  agentToken?: string;
  controlPlaneUrl?: string;
}): string {
  const port = node.agentPort ?? 9100;
  const controlPlane = node.controlPlaneUrl?.trim() || getControlPlaneAgentUrl();
  return `# EasyAIoT Node Agent 配置
NODE_ID=${node.id ?? ''}
AGENT_TOKEN=${node.agentToken ?? 'your-agent-token-here'}
CONTROL_PLANE_URL=${controlPlane}
HEARTBEAT_INTERVAL=10
AGENT_LISTEN_HOST=0.0.0.0
AGENT_LISTEN_PORT=${port}
AI_ROOT=/opt/easyaiot/AI
VIDEO_ROOT=/opt/easyaiot/VIDEO
MEDIA_CLUSTER_ROOT=/opt/easyaiot/media-cluster
MQTT_CLUSTER_ROOT=/opt/easyaiot/mqtt-cluster
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-secret
`;
}

/** 从控制面同步 Agent 文件到目标主机 */
export function buildAgentRsyncCommand(host?: string, sshUsername = 'root'): string {
  const targetHost = host?.trim() || '<目标服务器>';
  const user = sshUsername?.trim() || 'root';
  return `rsync -avz NODE/ ${user}@${targetHost}:${AGENT_INSTALL_DIR}/\n# 若 pip-wheels/ 为空，请先在平台服务器安装 pip 并执行: bash NODE/export_pip_wheels.sh`;
}

/** 目标主机上写入配置、安装并启动 Agent */
export function buildAgentInstallCommands(node: {
  id?: number;
  agentPort?: number;
  agentToken?: string;
  host?: string;
  controlPlaneUrl?: string;
}): string {
  const host = node.host?.trim() || '<目标服务器>';
  const env = buildAgentEnvContent(node).trimEnd();
  return `# 在目标服务器 ${host} 上执行
sudo mkdir -p ${AGENT_INSTALL_DIR}
cd ${AGENT_INSTALL_DIR}
sudo tee agent.env > /dev/null <<'EOF'
${env}
EOF
sudo bash install.sh install
sudo bash install.sh status`;
}

/** 一键部署脚本（需先完成 rsync 同步） */
export function buildAgentDeployScript(node: {
  id?: number;
  agentPort?: number;
  agentToken?: string;
  host?: string;
  controlPlaneUrl?: string;
}): string {
  return `${buildAgentRsyncCommand(node.host)}\n\n# 同步完成后 SSH 登录目标主机，执行：\n${buildAgentInstallCommands(node)}`;
}

/** 纳管抽屉表单布局（与模型管理抽屉一致） */
export const SETUP_FORM_LABEL_COL = { style: { width: '150px' } };
export const SETUP_FORM_WRAPPER_COL = { span: 21 };

/**
 * 节点纳管流程 — 步骤标题（引用 NODE_TERM，避免与详情 Tab 混用不同说法）
 */
export const SETUP_STEP_LABELS = {
  overview: { title: '确认配置', description: '检查信息' },
  storage: { title: NODE_TERM.storageService, description: 'Ceph OSD / CephFS' },
  media: { title: NODE_TERM.mediaService, description: 'SRS / ZLM' },
  mqtt: { title: NODE_TERM.mqttService, description: 'EMQX 集群' },
  agent: { title: NODE_TERM.agent, description: NODE_TERM.remoteDeploy },
  verify: { title: NODE_TERM.verifyOnline, description: '心跳确认' },
} as const;

/** 验证上线 — 平台状态自动轮询（间隔 × 次数 ≈ 总时长） */
export const VERIFY_STATUS_POLL_INTERVAL_MS = 4000;
export const VERIFY_STATUS_POLL_MAX_ATTEMPTS = 15;

export const SETUP_COPY = {
  agentName: NODE_TERM.agent,
  mediaService: NODE_TERM.mediaService,
  mqttService: NODE_TERM.mqttService,
  deployMode: '部署方式',
  deployModeAuto: `${NODE_TERM.remoteDeploy}（推荐）`,
  deployModeManual: '手动部署',
  deployConfig: '部署配置',
  deployScript: '部署脚本',
  deployProgress: '执行进度',
  credentials: '接入凭证',
  preCheck: NODE_TERM.preCheck,
  verifySection: NODE_TERM.verifyOnline,
  verifyUrlSection: NODE_TERM.platformUrl,
  verifyPolling: '自动检测平台状态',
  verifyPollingExhausted: `自动检测已结束，${NODE_TERM.notOnlineYet}。请运行${NODE_TERM.accessDiagnostic}排查，或确认${NODE_TERM.agent}已启动后手动刷新。`,
  verifyRetryPolling: '重新自动检测',
  verifyRefreshStatus: '刷新平台状态',
  verifyExpectedUrl: NODE_TERM.platformUrl,
  verifyRemoteUrl: '目标机 agent.env 配置值',
  verifyRunDiagnostic: NODE_TERM.accessDiagnostic,
  verifyDiagnosticHint: `${NODE_TERM.agent}启动后会向平台上报心跳；若长时间未上线，通常是 CONTROL_PLANE_URL 配置错误或网络不通。`,
  verifyIntro: `进入本步骤后将自动轮询平台节点状态（最多 15 次，约 1 分钟）；也可随时运行 ${NODE_TERM.accessDiagnostic} 排查问题。`,
  remoteDeploy: NODE_TERM.remoteDeploy,
  deployMediaBtn: `部署${NODE_TERM.mediaService}`,
  deployMqttBtn: `部署${NODE_TERM.mqttService}`,
  mediaDeployCheck: NODE_TERM.deployCheck,
  mqttDeployCheck: NODE_TERM.deployCheck,
  checkMediaDeployBtn: '检测部署状态',
  checkMqttDeployBtn: '检测部署状态',
  mediaPortCheck: '端口占用检测',
  mqttPortCheck: '端口占用检测',
  checkMediaPortBtn: '检测端口占用',
  checkMqttPortBtn: '检测端口占用',
  mediaOps: NODE_TERM.ops,
  mqttOps: NODE_TERM.ops,
  stopSrsBtn: '停止 SRS',
  stopZlmBtn: '停止 ZLMediaKit',
  stopEmqxBtn: '停止 EMQX',
  removeContainerBtn: '删除容器',
  removeImageBtn: '删除镜像',
  agentDeployCheck: NODE_TERM.deployCheck,
  checkAgentDeployBtn: '检测部署状态',
  agentPortCheck: '端口占用检测',
  checkAgentPortBtn: '检测端口占用',
  generateRandomPortsBtn: '生成随机端口',
  generateRandomPortsSuccess: '已生成随机端口',
  agentOps: NODE_TERM.ops,
  stopAgentBtn: `停止${NODE_TERM.agent}`,
  removeAgentBtn: `删除${NODE_TERM.agent}`,
  deployAgentBtn: `部署${NODE_TERM.agent}`,
  redeployAgentBtn: `${NODE_TERM.redeploy}${NODE_TERM.agent}`,
  redeployAgentHint: `检测到目标机已有${NODE_TERM.agent}，将依次执行：停止 → 删除 → ${NODE_TERM.redeploy}`,
  flowMedia: `部署${NODE_TERM.mediaService} → 部署${NODE_TERM.agent} → ${NODE_TERM.verifyOnline}`,
  flowMqtt: `部署${NODE_TERM.mqttService} → 部署${NODE_TERM.agent} → ${NODE_TERM.verifyOnline}`,
  flowStorage: `部署${NODE_TERM.storageService} → 部署${NODE_TERM.agent} → ${NODE_TERM.verifyOnline}`,
  flowCompute: `部署${NODE_TERM.agent} → ${NODE_TERM.verifyOnline}`,
  readinessReady: '可以开始部署',
  readinessPending: '请先完善配置',
  nodeInfo: '节点信息',
  sshConnectivity: NODE_TERM.sshCheck,
  mediaPortConfigured: `${NODE_TERM.mediaService}${NODE_TERM.mediaPort}已配置`,
  mqttPortConfigured: `${NODE_TERM.mqttService}${NODE_TERM.mqttPort}已配置`,
  completeOnboard: NODE_TERM.completeOnboard,
  editNode: NODE_TERM.editNode,
} as const;
