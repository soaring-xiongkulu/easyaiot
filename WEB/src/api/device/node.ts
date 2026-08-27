import { defHttp } from '@/utils/http/axios';

enum Api {
  Node = '/node',
}

type NodeRequestOptions = {
  errorMessageMode?: 'none' | 'message' | 'modal';
  isTransformResponse?: boolean;
  timeout?: number;
  signal?: AbortSignal;
};

const commonApi = (
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  params = {},
  options: NodeRequestOptions = {},
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const { isTransformResponse = true, errorMessageMode, timeout } = options;
  return defHttp[method](
    {
      url,
      headers: { ignoreCancelToken: true },
      timeout,
      ...params,
    },
    { isTransformResponse, errorMessageMode },
  );
};

export interface ComputeNodeVO {
  id?: number;
  name: string;
  host: string;
  sshPort?: number;
  agentPort?: number;
  status?: string;
  nodeRole?: string;
  functions?: string[];
  region?: string;
  tags?: Record<string, string>;
  capabilities?: Record<string, boolean>;
  maxGpuCount?: number;
  maxTaskCount?: number;
  weight?: number;
  remark?: string;
  agentToken?: string;
  sshUsername?: string;
  sshAuthType?: string;
  sshCredentialConfigured?: boolean;
  sshPassword?: string;
  sshPrivateKey?: string;
  sshLastTestAt?: string;
  sshLastTestOk?: boolean;
  lastHeartbeatAt?: string;
  cpuPercent?: number;
  memPercent?: number;
  memUsedBytes?: number;
  memTotalBytes?: number;
  diskPercent?: number;
  diskUsedBytes?: number;
  diskTotalBytes?: number;
  activeTasks?: number;
  gpuInfo?: string;
  isPlatform?: boolean;
  controlPlaneId?: number;
  isRemote?: boolean;
  peerId?: number;
  recordingStorageMode?: 'central_shared' | 'edge_local';
  recordingStorageState?: 'applying' | 'active' | 'failed' | string;
  recordingStorageGeneration?: number;
  recordingStorageUpdatedAt?: string;
  recordingStorageError?: string;
  mediaPublicUrl?: string;
  sentinelAutoDeployStarted?: boolean;
  createTime?: string;
  updateTime?: string;
}

export const createNode = (data: ComputeNodeVO, options?: Pick<NodeRequestOptions, 'errorMessageMode' | 'timeout'>) => {
  return commonApi('post', Api.Node + '/create', { data }, { timeout: 120000, ...options });
};

export const preflightNode = (data: ComputeNodeVO) => {
  return commonApi('post', Api.Node + '/preflight', { data }, { timeout: 60000, errorMessageMode: 'none' });
};

export interface NodePreflightCheckVO {
  name: string;
  ok: boolean;
  detail: string;
  required: boolean;
}

export interface NodePreflightResultVO {
  ok: boolean;
  message?: string;
  checks: NodePreflightCheckVO[];
}

function normalizePreflightResult(res: unknown): NodePreflightResultVO {
  const empty = { ok: false, message: '预检响应格式异常', checks: [] };
  if (!res || typeof res !== 'object') return empty;
  const value = res as Record<string, unknown>;
  const payload = value.ok != null ? value : value.data;
  if (!payload || typeof payload !== 'object') return empty;
  const result = payload as Record<string, unknown>;
  return {
    ok: result.ok === true,
    message: typeof result.message === 'string' ? result.message : undefined,
    checks: Array.isArray(result.checks) ? (result.checks as NodePreflightCheckVO[]) : [],
  };
}

export const preflightRecordingStorage = async (
  nodeId: number,
  mode: 'central_shared' | 'edge_local',
  mediaPublicUrl?: string,
): Promise<NodePreflightResultVO> => {
  const res = await commonApi('get', Api.Node + '/recording-storage/preflight', {
    params: { nodeId, mode, mediaPublicUrl: mediaPublicUrl || undefined },
  });
  return normalizePreflightResult(res);
};

export const updateNode = (data: ComputeNodeVO) => {
  return commonApi('put', Api.Node + '/update', { data });
};

export const deleteNode = (id: number) => {
  return commonApi('delete', `${Api.Node}/delete?id=${id}`);
};

export const getNode = (id: number) => {
  return commonApi('get', Api.Node + '/get', { params: { id } });
};

export interface NodeSentinelRemediateLogVO {
  id?: number;
  nodeId?: number;
  componentId?: string;
  mark?: string;
  action?: string;
  success?: boolean;
  exhausted?: boolean;
  attemptCount?: number;
  maxAttempts?: number;
  probeState?: string;
  message?: string;
  logs?: Array<Record<string, unknown>>;
  createTime?: string;
}

export interface NodeSentinelVO {
  nodeId?: number;
  nodeProfile?: string;
  nodeFunctions?: string[];
  sentinelVersion?: string;
  probeLevel?: string;
  components?: Array<Record<string, unknown>>;
  schedulableCapabilities?: Record<string, Record<string, unknown>>;
  summary?: Record<string, unknown>;
  environmentProfile?: Record<string, unknown>;
  declaredCapabilities?: Record<string, unknown>;
  operationalState?: string;
  remediation?: Record<string, unknown>;
  lastProbeAt?: string;
  fresh?: boolean;
  remediateLogs?: NodeSentinelRemediateLogVO[];
}

export const getNodeSentinel = async (nodeId: number): Promise<NodeSentinelVO> => {
  const res = await commonApi('get', Api.Node + '/sentinel/get', { params: { nodeId } });
  if (res && typeof res === 'object') {
    const r = res as Record<string, unknown>;
    if (r.nodeId != null || r.components) {
      return r as NodeSentinelVO;
    }
    const wrapped = r.data as NodeSentinelVO | undefined;
    if (wrapped) return wrapped;
  }
  return {};
};

export const probeNodeSentinel = async (
  nodeId: number,
  level = 'L1',
): Promise<NodeSentinelVO> => {
  const res = await commonApi('post', Api.Node + '/sentinel/probe', { data: { nodeId, level } });
  if (res && typeof res === 'object') {
    const r = res as Record<string, unknown>;
    if (r.nodeId != null || r.components) {
      return r as NodeSentinelVO;
    }
    const wrapped = r.data as NodeSentinelVO | undefined;
    if (wrapped) return wrapped;
  }
  return {};
};

export const resyncNodeSentinel = async (nodeId: number): Promise<NodeSentinelVO> => {
  const res = await commonApi('post', Api.Node + '/sentinel/resync', { params: { nodeId } });
  if (res && typeof res === 'object') {
    const r = res as Record<string, unknown>;
    if (r.nodeId != null || r.components) {
      return r as NodeSentinelVO;
    }
    const wrapped = r.data as NodeSentinelVO | undefined;
    if (wrapped) return wrapped;
  }
  return {};
};

export interface NodePageResult {
  data: {
    list: ComputeNodeVO[];
    total: number;
  };
}

/** 统一分页响应结构，兼容 axios 原生响应与 transform 后的多种形态 */
function normalizeNodePageResult(res: unknown): NodePageResult {
  const empty: NodePageResult = { data: { list: [], total: 0 } };
  if (!res || typeof res !== 'object') return empty;

  const r = res as Record<string, unknown>;

  if (Array.isArray(r.list)) {
    return { data: { list: r.list as ComputeNodeVO[], total: Number(r.total ?? 0) } };
  }

  const wrapped = r.data as Record<string, unknown> | undefined;
  if (wrapped && Array.isArray(wrapped.list)) {
    return { data: { list: wrapped.list as ComputeNodeVO[], total: Number(wrapped.total ?? 0) } };
  }

  // isTransformResponse: false 时返回 AxiosResponse，业务数据在 data.data
  const envelope = r.data as Record<string, unknown> | undefined;
  const page = envelope?.data as Record<string, unknown> | undefined;
  if (page && Array.isArray(page.list)) {
    return { data: { list: page.list as ComputeNodeVO[], total: Number(page.total ?? 0) } };
  }

  return empty;
}

export const getNodePage = async (
  params: Record<string, unknown>,
  options?: NodeRequestOptions,
): Promise<NodePageResult> => {
  const res = await commonApi('get', Api.Node + '/page', { params }, options);
  return normalizeNodePageResult(res);
};

export interface NodeMetricTrendPointVO {
  collectedAt: string;
  cpuPercent?: number;
  memPercent?: number;
  diskPercent?: number;
  gpuMemPercent?: number;
  gpuUtilPercent?: number;
  memUsedBytes?: number;
  diskUsedBytes?: number;
  gpuMemUsedBytes?: number;
  activeTasks?: number;
}

export interface NodeMetricTrendSeriesVO {
  nodeId: number;
  nodeName: string;
  host: string;
  status?: string;
  points: NodeMetricTrendPointVO[];
}

export interface NodeMetricTrendResult {
  series: NodeMetricTrendSeriesVO[];
}

export const getNodeMetricTrend = async (params?: {
  nodeIds?: number[];
  minutes?: number;
  maxPoints?: number;
}): Promise<NodeMetricTrendResult> => {
  const query: Record<string, unknown> = {
    minutes: params?.minutes ?? 30,
    maxPoints: params?.maxPoints ?? 120,
  };
  if (params?.nodeIds?.length) {
    query.nodeIds = params.nodeIds;
  }
  const res = await commonApi('get', Api.Node + '/metric-trend', { params: query });
  if (res && typeof res === 'object') {
    const r = res as Record<string, unknown>;
    if (Array.isArray(r.series)) {
      return { series: r.series as NodeMetricTrendSeriesVO[] };
    }
    const wrapped = r.data as Record<string, unknown> | undefined;
    if (wrapped && Array.isArray(wrapped.series)) {
      return { series: wrapped.series as NodeMetricTrendSeriesVO[] };
    }
  }
  return { series: [] };
};

export const testNodeSsh = (id: number) => {
  return commonApi('post', `${Api.Node}/test-ssh?id=${id}`);
};

export const resetAgentToken = (id: number) => {
  return commonApi('post', `${Api.Node}/reset-agent-token?id=${id}`);
};

/** 获取待纳管节点的 Agent 配置（含 Token，仅 pending 状态可用） */
export const getAgentSetup = (id: number) => {
  return commonApi('get', Api.Node + '/agent-setup', { params: { id } });
};

export interface PlatformHostVO {
  host: string;
  port: number;
}

/** 获取平台宿主机 IP（供 Agent 平台接入地址自动填充） */
export const getPlatformHost = () => {
  return commonApi('get', Api.Node + '/platform-host', { params: {} });
};

export const setNodeMaintenance = (id: number, enabled: boolean) => {
  return commonApi('post', `${Api.Node}/maintenance?id=${id}&enabled=${enabled}`);
};

export interface DeviceMediaBindingVO {
  deviceId: string;
  srsLiveNodeId?: number;
  srsAiNodeId?: number;
  zlmNodeId?: number;
  rtmpStream?: string;
  httpStream?: string;
  aiRtmpStream?: string;
  aiHttpStream?: string;
  zlmHost?: string;
  zlmHttpPort?: number;
  zlmRtmpPort?: number;
  region?: string;
  status?: string;
}

export const allocateDeviceMedia = (data: {
  deviceId: string;
  needSrsLive?: boolean;
  needSrsAi?: boolean;
  needZlm?: boolean;
  region?: string;
  httpPlayHost?: string;
}) => {
  return commonApi('post', Api.Node + '/media/allocate', { data });
};

export const deployMediaStack = (data: {
  nodeId: number;
  stackType: 'srs_live' | 'srs_ai' | 'zlm';
  env?: Record<string, string>;
}) => {
  return commonApi('post', Api.Node + '/media/deploy-stack', { data });
};

export interface MediaDeployStepVO {
  name: string;
  status: string;
  output?: string;
}

export interface MediaRemoteDeployResult {
  success?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export interface MediaStackCheckResult {
  success?: boolean;
  deployed?: boolean;
  srsRunning?: boolean;
  zlmRunning?: boolean;
  dockerReady?: boolean;
  composeReady?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export interface MqttStackCheckResult {
  success?: boolean;
  deployed?: boolean;
  emqxRunning?: boolean;
  dockerReady?: boolean;
  composeReady?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export interface StorageStackCheckResult {
  success?: boolean;
  deployed?: boolean;
  /** 兼容字段：NFS 服务端健康 */
  cephHealthy?: boolean;
  nfsHealthy?: boolean;
  /** 兼容：NFS 2049 / 服务在线 */
  osdRunning?: boolean;
  nfsPortOk?: boolean;
  /** 兼容：挂载就绪 */
  cephfsReady?: boolean;
  poolExists?: boolean;
  mountReady?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export interface StorageMountCheckResult {
  success?: boolean;
  mountReady?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

/** NFS / 共享媒体拓扑节点 */
export interface CephTopologyNodeVO {
  nodeId: number;
  name?: string;
  host?: string;
  nodeRole?: string;
  functions?: string[];
  status?: string;
  agentPort?: number;
  /** platform | nfs_primary | nfs_standby | nfs_client | nfs_candidate（兼容 storage_nfs / ceph_client） */
  kind?: string;
  isPlatform?: boolean;
  /** primary | standby | client | candidate */
  nfsClusterRole?: string;
  cephMountReady?: boolean;
  cephMountPath?: string;
  cephMonHost?: string;
  cephPool?: string;
  cephfsName?: string;
  nfsMountReady?: boolean;
  /** 真 NFS Export（exportfs）是否就绪 */
  nfsExportReady?: boolean;
  nfsMountPath?: string;
  nfsServerHost?: string;
  nfsExportPath?: string;
  storageBackend?: string;
  nfsProbeAt?: string;
  nfsProbeSummary?: string;
  nfsMountSource?: string;
  alertImagesDir?: string;
  playbacksDir?: string;
  snapsDir?: string;
  lastHeartbeatAt?: string;
  sshCredentialConfigured?: boolean;
}

export interface CephTopologyLinkVO {
  sourceNodeId?: number;
  targetNodeId?: number;
  relation?: string;
}

export interface CephTopologySummaryVO {
  totalNodes?: number;
  storageNodes?: number;
  clientNodes?: number;
  primaryCount?: number;
  standbyCount?: number;
  candidateCount?: number;
  primaryReady?: boolean;
  primaryNodeId?: number;
  primaryHost?: string;
  standbyNodeId?: number;
  standbyHost?: string;
  mountReadyCount?: number;
  mountNotReadyCount?: number;
  offlineCount?: number;
  coveragePercent?: number;
  lastProbeAt?: string;
  unprobedCount?: number;
}

export interface CephTopologyResult {
  center?: CephTopologyNodeVO;
  nodes?: CephTopologyNodeVO[];
  links?: CephTopologyLinkVO[];
  summary?: CephTopologySummaryVO;
}

export interface NfsBatchRefreshPayload {
  nodeIds?: number[];
  auto?: boolean;
}

export interface NfsBatchRefreshResult {
  success?: boolean;
  message?: string;
  results?: Array<{
    nodeId?: number;
    nodeName?: string;
    host?: string;
    success?: boolean;
    message?: string;
    steps?: MediaDeployStepVO[];
  }>;
  topology?: CephTopologyResult;
}

export interface NfsOpLogItem {
  id?: number;
  nodeId?: number;
  opType?: string;
  success?: boolean;
  message?: string;
  createTime?: string;
  steps?: MediaDeployStepVO[];
}

export interface NfsOpLogPageResult {
  list?: NfsOpLogItem[];
  total?: number;
}

export interface NfsFileEntry {
  name?: string;
  directory?: boolean;
  size?: number;
  mtime?: string;
  relativePath?: string;
}

export interface NfsFileListResult {
  mountRoot?: string;
  relativePath?: string;
  absolutePath?: string;
  entries?: NfsFileEntry[];
}

export interface AgentCheckResult {
  success?: boolean;
  deployed?: boolean;
  installDirReady?: boolean;
  serviceRunning?: boolean;
  healthOk?: boolean;
  configOk?: boolean;
  nodeIdMatch?: boolean;
  tokenMatch?: boolean;
  controlPlaneReachable?: boolean;
  controlPlaneUrl?: string;
  expectedControlPlaneUrl?: string;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export interface PortCheckItemVO {
  name: string;
  port: number;
  status: 'free' | 'occupied' | 'allowed';
  process?: string;
}

export interface PortCheckResult {
  success?: boolean;
  portsReady?: boolean;
  message?: string;
  ports?: PortCheckItemVO[];
  steps?: MediaDeployStepVO[];
}

/** 解析 isTransformResponse:false 时的 AxiosResponse / { code, data } 信封 */
function unwrapNodeApiData<T>(res: unknown): T {
  // isTransformResponse:false 时 axios 返回完整 AxiosResponse，业务在 res.data
  const body = (res as { data?: unknown })?.data ?? res;
  if (body && typeof body === 'object' && body !== null && 'code' in body) {
    const envelope = body as { code?: number; data?: T; msg?: string; message?: string };
    const code = envelope.code;
    if (code !== undefined && code !== 0 && code !== 200) {
      throw new Error(envelope.msg || envelope.message || `请求失败(code=${code})`);
    }
    if ('data' in envelope) {
      return envelope.data as T;
    }
  }
  return body as T;
}

/** 通过 SSH 自动部署 SRS + ZLM 媒体栈（本机导出+同步离线镜像，超时 45 分钟） */
export const deployMediaStackBySsh = async (
  nodeId: number,
  options?: { signal?: AbortSignal },
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/deploy-ssh?nodeId=${nodeId}`,
    { signal: options?.signal },
    { isTransformResponse: false, timeout: 45 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 停止目标机 SRS 或 ZLMediaKit */
export const stopMediaServiceBySsh = async (
  nodeId: number,
  service: 'srs' | 'zlm',
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/stop-ssh?nodeId=${nodeId}&service=${service}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 删除目标机 SRS/ZLM 媒体容器 */
export const removeMediaContainerBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/remove-container-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 删除目标机 SRS/ZLM Docker 镜像 */
export const removeMediaImageBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/remove-image-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 检测目标机 SRS/ZLM 是否已部署 */
export const checkMediaStackBySsh = async (nodeId: number): Promise<MediaStackCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/check-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaStackCheckResult>(res);
};

/** 通过 SSH 检测目标机流媒体部署端口占用 */
export const checkMediaPortsBySsh = async (nodeId: number): Promise<PortCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/media/check-ports-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<PortCheckResult>(res);
};

/** 通过 SSH 自动部署 EMQX MQTT 网关（本机导出+同步离线镜像，超时 45 分钟） */
export const deployMqttStackBySsh = async (
  nodeId: number,
  options?: { signal?: AbortSignal },
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/deploy-ssh?nodeId=${nodeId}`,
    { signal: options?.signal },
    { isTransformResponse: false, timeout: 45 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const stopMqttServiceBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/stop-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const removeMqttContainerBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/remove-container-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const removeMqttImageBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/remove-image-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const checkMqttStackBySsh = async (nodeId: number): Promise<MqttStackCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/check-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<MqttStackCheckResult>(res);
};

export const checkMqttPortsBySsh = async (nodeId: number): Promise<PortCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/mqtt/check-ports-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<PortCheckResult>(res);
};

/** 通过 SSH 检测 Ceph 存储节点集群状态 */
export const checkStorageStackBySsh = async (nodeId: number): Promise<StorageStackCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/check-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<StorageStackCheckResult>(res);
};

/** NFS 共享媒体节点拓扑（原 getCephTopology，字段兼容） */
export const getCephTopology = async (): Promise<CephTopologyResult> => {
  const res = await commonApi('get', `${Api.Node}/storage/topology`, {}, { isTransformResponse: false });
  const data = unwrapNodeApiData<CephTopologyResult | null>(res);
  if (!data || typeof data !== 'object') {
    return { nodes: [], links: [] };
  }
  return {
    ...data,
    nodes: Array.isArray(data.nodes) ? data.nodes : [],
    links: Array.isArray(data.links) ? data.links : [],
  };
};

export interface NfsClusterAssignPayload {
  serverNodeId?: number;
  standbyNodeId?: number;
  clientNodeIds?: number[];
  mountRoot?: string;
  nfsExport?: string;
  nfsMountOpts?: string;
}

/** 分配/切换 NFS 集群（主/备 + 客户端 tags） */
export const assignNfsCluster = async (payload: NfsClusterAssignPayload): Promise<CephTopologyResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/assign-nfs-cluster`,
    payload,
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<CephTopologyResult>(res);
};

/** 软 HA：升主 NFS 服务端 */
export const promoteNfsPrimary = async (nodeId: number): Promise<CephTopologyResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/promote-nfs-primary?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<CephTopologyResult>(res);
};

export interface NfsClusterVO {
  id?: number;
  name?: string;
  laneKey?: string;
  controlPlaneId?: number;
  primaryNodeId?: number;
  primaryHost?: string;
  primaryName?: string;
  standbyNodeId?: number;
  standbyHost?: string;
  standbyName?: string;
  mountRoot?: string;
  nfsExport?: string;
  isActive?: boolean;
  status?: string;
  primaryReady?: boolean;
  clientCount?: number;
  clientReadyCount?: number;
}

export interface NfsBridgeVO {
  id?: number;
  name?: string;
  sourceClusterId?: number;
  sourceClusterName?: string;
  targetClusterId?: number;
  targetClusterName?: string;
  sourceRelPaths?: string;
  targetRelPath?: string;
  scheduleCron?: string;
  enabled?: boolean;
  status?: string;
  lastRunAt?: string;
  lastSuccess?: boolean;
  lastMessage?: string;
  createTime?: string;
}

export interface NfsMultiClusterOverview {
  activeClusterId?: number;
  activeClusterName?: string;
  clusters?: NfsClusterVO[];
  bridges?: NfsBridgeVO[];
}

export const getNfsMultiClusterOverview = async (): Promise<NfsMultiClusterOverview> => {
  const res = await commonApi(
    'get',
    `${Api.Node}/storage/multi-cluster/overview`,
    {},
    { isTransformResponse: false },
  );
  return normalizeNfsMultiClusterOverview(unwrapNodeApiData<NfsMultiClusterOverview | null>(res));
};

function normalizeNfsMultiClusterOverview(
  raw: NfsMultiClusterOverview | null | undefined,
): NfsMultiClusterOverview {
  if (!raw || typeof raw !== 'object') {
    return { clusters: [], bridges: [] };
  }
  return {
    ...raw,
    clusters: Array.isArray(raw.clusters) ? raw.clusters : [],
    bridges: Array.isArray(raw.bridges) ? raw.bridges : [],
  };
}

export const activateNfsCluster = async (payload: {
  clusterId: number;
  forceStopBridges?: boolean;
}): Promise<NfsMultiClusterOverview> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/multi-cluster/activate`,
    payload,
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return normalizeNfsMultiClusterOverview(unwrapNodeApiData<NfsMultiClusterOverview | null>(res));
};

export const createNfsBridge = async (payload: {
  name?: string;
  sourceClusterId: number;
  targetClusterId: number;
  sourceRelPaths?: string;
  targetRelPath?: string;
  scheduleCron?: string;
}): Promise<NfsMultiClusterOverview> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/multi-cluster/bridge/create`,
    payload,
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return normalizeNfsMultiClusterOverview(unwrapNodeApiData<NfsMultiClusterOverview | null>(res));
};

export const stopNfsBridge = async (bridgeId: number): Promise<NfsMultiClusterOverview> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/multi-cluster/bridge/stop?bridgeId=${bridgeId}`,
    {},
    { isTransformResponse: false },
  );
  return normalizeNfsMultiClusterOverview(unwrapNodeApiData<NfsMultiClusterOverview | null>(res));
};

export const runNfsBridge = async (bridgeId: number): Promise<NfsMultiClusterOverview> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/multi-cluster/bridge/run?bridgeId=${bridgeId}`,
    {},
    { isTransformResponse: false, timeout: 30 * 60 * 1000 },
  );
  return normalizeNfsMultiClusterOverview(unwrapNodeApiData<NfsMultiClusterOverview | null>(res));
};

/** 批量 SSH 刷新 NFS 现状并落库 */
export const batchRefreshNfsBySsh = async (
  payload: NfsBatchRefreshPayload = {},
): Promise<NfsBatchRefreshResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/batch-refresh-ssh`,
    payload,
    { isTransformResponse: false, timeout: 30 * 60 * 1000 },
  );
  return unwrapNodeApiData<NfsBatchRefreshResult>(res);
};

/** NFS 运维操作日志分页 */
export const getNfsOpLogs = async (params: {
  nodeId?: number;
  opType?: string;
  pageNo?: number;
  pageSize?: number;
}): Promise<NfsOpLogPageResult> => {
  const res = await commonApi('get', `${Api.Node}/storage/op-logs`, { params }, { isTransformResponse: false });
  return unwrapNodeApiData<NfsOpLogPageResult>(res);
};

/** 只读列出节点媒体挂载根 */
export const listNfsMediaFiles = async (nodeId: number, path?: string): Promise<NfsFileListResult> => {
  const res = await commonApi(
    'get',
    `${Api.Node}/storage/files/list`,
    { params: { nodeId, path: path || '' } },
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<NfsFileListResult>(res);
};

/** 只读下载节点媒体文件（返回 blob） */
export const downloadNfsMediaFile = async (nodeId: number, path: string): Promise<Blob> => {
  const res = await commonApi(
    'get',
    `${Api.Node}/storage/files/download`,
    { params: { nodeId, path }, responseType: 'blob' },
    { isTransformResponse: false, timeout: 5 * 60 * 1000 },
  );
  // commonApi 可能已解包；兼容直接 blob
  if (res instanceof Blob) return res;
  const data = (res as { data?: Blob })?.data;
  if (data instanceof Blob) return data;
  return new Blob([res as any]);
};

export interface NfsFileOpsResult {
  success?: boolean;
  message?: string;
  relativePath?: string;
}

/** 在媒体根内创建目录 */
export const mkdirNfsMediaDir = async (
  nodeId: number,
  name: string,
  path?: string,
): Promise<NfsFileOpsResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/files/mkdir`,
    { params: { nodeId, name, path: path || '' } },
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<NfsFileOpsResult>(res);
};

/** 上传文件到媒体根当前目录 */
export const uploadNfsMediaFile = async (
  nodeId: number,
  file: File,
  path?: string,
): Promise<NfsFileOpsResult> => {
  const form = new FormData();
  form.append('file', file);
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const res = await defHttp.post(
    {
      url: `${Api.Node}/storage/files/upload`,
      params: { nodeId, path: path || '' },
      data: form,
      headers: {
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
      timeout: 5 * 60 * 1000,
    },
    { isTransformResponse: false },
  );
  return unwrapNodeApiData<NfsFileOpsResult>(res);
};

/** 删除媒体根内文件或目录 */
export const deleteNfsMediaPath = async (nodeId: number, path: string): Promise<NfsFileOpsResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/files/delete`,
    { params: { nodeId, path } },
    { isTransformResponse: false, timeout: 5 * 60 * 1000 },
  );
  return unwrapNodeApiData<NfsFileOpsResult>(res);
};

/** 同目录重命名 */
export const renameNfsMediaPath = async (
  nodeId: number,
  path: string,
  newName: string,
): Promise<NfsFileOpsResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/files/rename`,
    { params: { nodeId, path, newName } },
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<NfsFileOpsResult>(res);
};

/** 通过 SSH 检测 NFS 客户端挂载 */
export const checkStorageMountBySsh = async (nodeId: number): Promise<StorageMountCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/check-mount-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<StorageMountCheckResult>(res);
};

/** 通过 SSH 在存储节点准备 Ceph OSD */
export const deployStorageOsdBySsh = async (
  nodeId: number,
  options?: { signal?: AbortSignal },
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/deploy-osd-ssh?nodeId=${nodeId}`,
    { signal: options?.signal },
    { isTransformResponse: false, timeout: 30 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 在目标节点挂载 CephFS */
export const deployStorageClientBySsh = async (
  nodeId: number,
  options?: { signal?: AbortSignal },
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/deploy-client-ssh?nodeId=${nodeId}`,
    { signal: options?.signal },
    { isTransformResponse: false, timeout: 15 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 在 MON 节点创建 Ceph 存储池 */
export const deployStoragePoolBySsh = async (
  nodeId: number,
  options?: { signal?: AbortSignal },
): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/deploy-pool-ssh?nodeId=${nodeId}`,
    { signal: options?.signal },
    { isTransformResponse: false, timeout: 15 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const stopStorageOsdBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/stop-osd-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const unmountStorageBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/storage/unmount-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 检测目标机 Node Agent 是否已部署 */
export const checkAgentBySsh = async (
  nodeId: number,
  controlPlaneUrl?: string,
): Promise<AgentCheckResult> => {
  const query = new URLSearchParams({ nodeId: String(nodeId) });
  if (controlPlaneUrl?.trim()) {
    query.set('controlPlaneUrl', controlPlaneUrl.trim());
  }
  const res = await commonApi(
    'post',
    `${Api.Node}/check-agent-ssh?${query.toString()}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<AgentCheckResult>(res);
};

/** 通过 SSH 检测目标机 Node Agent 部署端口占用 */
export const checkAgentPortBySsh = async (nodeId: number): Promise<PortCheckResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/check-agent-port-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 2 * 60 * 1000 },
  );
  return unwrapNodeApiData<PortCheckResult>(res);
};

/** 通过 SSH 停止目标机 Node Agent 服务 */
export const stopAgentBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/stop-agent-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 删除目标机 Node Agent 服务及安装目录 */
export const removeAgentBySsh = async (nodeId: number): Promise<MediaRemoteDeployResult> => {
  const res = await commonApi(
    'post',
    `${Api.Node}/remove-agent-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

/** 通过 SSH 自动部署 Node Agent（耗时较长，超时 5 分钟） */
export const deployAgentBySsh = async (
  nodeId: number,
  controlPlaneUrl?: string,
): Promise<MediaRemoteDeployResult> => {
  const query = new URLSearchParams({ nodeId: String(nodeId) });
  if (controlPlaneUrl?.trim()) {
    query.set('controlPlaneUrl', controlPlaneUrl.trim());
  }
  const res = await commonApi(
    'post',
    `${Api.Node}/deploy-agent-ssh?${query.toString()}`,
    {},
    { isTransformResponse: false, timeout: 5 * 60 * 1000 },
  );
  return unwrapNodeApiData<MediaRemoteDeployResult>(res);
};

export const getDeviceMediaBinding = (deviceId: string) => {
  return commonApi('get', Api.Node + '/media/binding', { params: { deviceId } });
};

export const releaseDeviceMedia = (deviceId: string) => {
  return commonApi('post', `${Api.Node}/media/release?deviceId=${encodeURIComponent(deviceId)}`);
};

const SCHEDULABLE_COMPUTE_FUNCTIONS = [
  'algorithm',
  'forward',
  'train',
  'llm',
  'label',
  'infer',
  'transform',
] as const;

function nodeFunctionIds(node?: Pick<ComputeNodeVO, 'functions' | 'nodeRole'> | null): string[] {
  if (node?.functions?.length) {
    return node.functions.map((id) => String(id).trim()).filter(Boolean);
  }
  return String(node?.nodeRole || '')
    .split(/[,\s]+/)
    .map((id) => id.trim())
    .filter(Boolean);
}

function isSchedulableComputeNode(node?: Pick<ComputeNodeVO, 'functions' | 'nodeRole'> | null): boolean {
  const set = new Set(nodeFunctionIds(node));
  return SCHEDULABLE_COMPUTE_FUNCTIONS.some((fn) => set.has(fn));
}

/** 获取可用于计算工作负载调度的在线节点 */
export const listScheduleNodes = async () => {
  const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
  const list = res?.data?.list ?? [];
  return list.filter((node: ComputeNodeVO) => isSchedulableComputeNode(node));
};

/** 获取可用于媒体调度的在线节点（直播接入 / 推流转发） */
export const listMediaNodes = async () => {
  const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
  const list = res?.data?.list ?? [];
  return list.filter((node: ComputeNodeVO) => {
    const set = new Set(nodeFunctionIds(node));
    return set.has('live') || set.has('forward');
  });
};

// ---------- 工作负载 bundle 批量分发 ----------

export type WorkloadBundleTypeKey =
  | 'stream_forward'
  | 'algorithm_realtime'
  | 'algorithm_snap'
  | 'algorithm_patrol'
  | 'post_process'
  | 'ai_service'
  | 'llm_service'
  | 'auto_label'
  | 'model_train'
  | 'transform_runtime';

export interface WorkloadBundleBatchReq {
  nodeIds: number[];
  bundleType: WorkloadBundleTypeKey;
  /** TRANSFORM 全量分发后拉起的容器副本数 */
  replicas?: number;
}

export const stopNodeWorkload = (
  nodeId: number,
  workloadType: string,
  workloadId: string,
) => {
  return commonApi('post', `${Api.Node}/workload/stop`, {
    params: { nodeId, workloadType, workloadId },
  });
};

/** 心跳未带 TRANSFORM_NODE_ID 时，按绑定表反查节点硬停 */
export const stopNodeWorkloadById = (workloadType: string, workloadId: string) => {
  return commonApi('post', `${Api.Node}/workload/stop-by-id`, {
    params: { workloadType, workloadId },
  });
};

export const deployNodeWorkload = (data: {
  nodeId: number;
  workloadType: string;
  workloadId: string;
  runtime?: string;
  image?: string;
  env?: Record<string, string>;
  command?: string[];
}) => {
  return commonApi('post', `${Api.Node}/workload/deploy`, { data });
};

export interface WorkloadBundleNodeResult {
  nodeId?: number;
  nodeName?: string;
  host?: string;
  success?: boolean;
  message?: string;
  version?: string;
  controlPlaneVersion?: string;
  versionMatch?: boolean;
  steps?: MediaDeployStepVO[];
}

export interface WorkloadBundleBatchResult {
  bundleType?: string;
  success?: boolean;
  message?: string;
  results?: WorkloadBundleNodeResult[];
}

export interface WorkloadBundleCheckResult {
  bundleType?: string;
  envReady?: boolean;
  scriptsReady?: boolean;
  pythonLauncher?: string;
  success?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

const BUNDLE_API = `${Api.Node}/workload-bundle`;
const BUNDLE_TIMEOUT = 45 * 60 * 1000;

export const checkWorkloadBundleBySsh = async (
  nodeId: number,
  bundleType: WorkloadBundleTypeKey,
): Promise<WorkloadBundleCheckResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/check-ssh?nodeId=${nodeId}&bundleType=${encodeURIComponent(bundleType)}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<WorkloadBundleCheckResult>(res);
};

export const batchCheckWorkloadBundleBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-check-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchDeployWorkloadBundleEnvBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-deploy-env-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchDeployWorkloadBundleScriptsBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-deploy-scripts-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchDeployWorkloadBundleFullBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-deploy-full-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchRemoveWorkloadBundleEnvBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-remove-env-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchRemoveWorkloadBundleScriptsBySsh = async (
  data: WorkloadBundleBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/batch-remove-scripts-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

// ---------- FFmpeg 离线分发 ----------

export interface NodeFfmpegBatchReq {
  nodeIds: number[];
}

export interface NodeFfmpegCheckResult {
  ffmpegReady?: boolean;
  ffmpegPath?: string;
  success?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export const checkFfmpegBySsh = async (nodeId: number): Promise<NodeFfmpegCheckResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/ffmpeg/check-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<NodeFfmpegCheckResult>(res);
};

export const batchCheckFfmpegBySsh = async (data: NodeFfmpegBatchReq): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/ffmpeg/batch-check-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchDeployFfmpegBySsh = async (data: NodeFfmpegBatchReq): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/ffmpeg/batch-deploy-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchRemoveFfmpegBySsh = async (data: NodeFfmpegBatchReq): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/ffmpeg/batch-remove-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

// ---------- RUNTIME(C++) 离线分发 ----------

export interface NodeRuntimeCppBatchReq {
  nodeIds: number[];
}

export interface NodeRuntimeCppCheckResult {
  runtimeReady?: boolean;
  runtimePath?: string;
  version?: string;
  git?: string;
  builtAt?: string;
  controlPlaneVersion?: string;
  versionMatch?: boolean;
  success?: boolean;
  message?: string;
  steps?: MediaDeployStepVO[];
}

export const checkRuntimeCppBySsh = async (nodeId: number): Promise<NodeRuntimeCppCheckResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/runtime-cpp/check-ssh?nodeId=${nodeId}`,
    {},
    { isTransformResponse: false, timeout: 3 * 60 * 1000 },
  );
  return unwrapNodeApiData<NodeRuntimeCppCheckResult>(res);
};

export const batchCheckRuntimeCppBySsh = async (
  data: NodeRuntimeCppBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/runtime-cpp/batch-check-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchDeployRuntimeCppBySsh = async (
  data: NodeRuntimeCppBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/runtime-cpp/batch-deploy-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

export const batchRemoveRuntimeCppBySsh = async (
  data: NodeRuntimeCppBatchReq,
): Promise<WorkloadBundleBatchResult> => {
  const res = await commonApi(
    'post',
    `${BUNDLE_API}/runtime-cpp/batch-remove-ssh`,
    { data },
    { isTransformResponse: false, timeout: BUNDLE_TIMEOUT },
  );
  return unwrapNodeApiData<WorkloadBundleBatchResult>(res);
};

// ── 中心节点联邦 / 泳道 ──

export interface ClusterLaneVO {
  laneKey: string;
  controlPlaneId?: number;
  isLocal?: boolean;
  peerId?: number;
  centralNode?: ComputeNodeVO;
  workerNodes?: ComputeNodeVO[];
  syncStatus?: string;
}

export interface ControlPlanePeerVO {
  id?: number;
  name: string;
  apiBaseUrl: string;
  host?: string;
  status?: string;
  remotePlatformNodeId?: number;
  lastSyncAt?: string;
  remark?: string;
}

export interface ControlPlanePeerSaveVO {
  name: string;
  apiBaseUrl: string;
  peerToken?: string;
  remark?: string;
}

export interface ClusterLaneBatchReq {
  laneKey?: string;
  nodeIds: number[];
  action?: 'maintenance_on' | 'maintenance_off';
}

export interface ClusterLanePageResult {
  data: {
    list: ClusterLaneVO[];
    total: number;
  };
}

function normalizeClusterLanePageResult(res: unknown): ClusterLanePageResult {
  const empty: ClusterLanePageResult = { data: { list: [], total: 0 } };
  if (!res || typeof res !== 'object') return empty;

  const r = res as Record<string, unknown>;

  if (Array.isArray(r.list)) {
    return { data: { list: r.list as ClusterLaneVO[], total: Number(r.total ?? 0) } };
  }

  const wrapped = r.data as Record<string, unknown> | undefined;
  if (wrapped && Array.isArray(wrapped.list)) {
    return { data: { list: wrapped.list as ClusterLaneVO[], total: Number(wrapped.total ?? 0) } };
  }

  const envelope = r.data as Record<string, unknown> | undefined;
  const page = envelope?.data as Record<string, unknown> | undefined;
  if (page && Array.isArray(page.list)) {
    return { data: { list: page.list as ClusterLaneVO[], total: Number(page.total ?? 0) } };
  }

  if (Array.isArray(r)) {
    return { data: { list: r as ClusterLaneVO[], total: r.length } };
  }

  if (Array.isArray(wrapped)) {
    return { data: { list: wrapped as ClusterLaneVO[], total: wrapped.length } };
  }

  return empty;
}

export const getClusterLanes = async (params?: { pageNo?: number; pageSize?: number }): Promise<ClusterLanePageResult> => {
  const res = await commonApi('get', `${Api.Node}/control-plane/lanes`, {
    params: {
      pageNo: params?.pageNo ?? 1,
      pageSize: params?.pageSize ?? 10,
    },
  });
  return normalizeClusterLanePageResult(res);
};

export const getControlPlanePeers = () => {
  return commonApi('get', `${Api.Node}/control-plane/peers`);
};

export const createControlPlanePeer = (data: ControlPlanePeerSaveVO) => {
  return commonApi('post', `${Api.Node}/control-plane/peers/create`, { data });
};

export const deleteControlPlanePeer = (id: number) => {
  return commonApi('delete', `${Api.Node}/control-plane/peers/delete?id=${id}`);
};

export const syncControlPlanePeer = (id: number) => {
  return commonApi('post', `${Api.Node}/control-plane/peers/sync?id=${id}`);
};

export const batchClusterLaneAction = (data: ClusterLaneBatchReq) => {
  return commonApi('post', `${Api.Node}/control-plane/lane/batch`, { data });
};
