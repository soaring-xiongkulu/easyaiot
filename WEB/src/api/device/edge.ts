import { defHttp } from '@/utils/http/axios';

const EDGE_PREFIX = '/video/edge';

export interface EdgeRemoteAccess {
  enabled?: boolean;
  provider?: string;
  status?: string;
  serviceEnabled?: boolean;
  serviceAccessUrl?: string;
  sshEnabled?: boolean;
  sshAccessHost?: string;
  sshAccessPort?: number;
  sshUsername?: string;
}

export interface EdgePipeline {
  id?: string;
  name?: string;
  status?: string;
  fps?: number;
  models?: string[];
  deviceId?: string;
}

export interface EdgeNodeVO {
  id: number;
  fingerprint?: string;
  name: string;
  host?: string;
  status: 'online' | 'offline' | string;
  enabled: boolean;
  nodeKind?: string;
  hardwareProvider?: string;
  socModel?: string;
  acceleratorType?: string;
  acceleratorCount?: number;
  runtimeTarget?: string;
  runtimeVersion?: string;
  agentVersion?: string;
  agentPort?: number;
  maxTaskCount?: number;
  activeTaskCount?: number;
  cpuPercent?: number;
  memPercent?: number;
  diskPercent?: number;
  temperatureC?: number;
  memUsedBytes?: number;
  memTotalBytes?: number;
  diskUsedBytes?: number;
  diskTotalBytes?: number;
  acceleratorInfo?: Record<string, any>[];
  pipelines?: EdgePipeline[];
  remoteAccess?: EdgeRemoteAccess;
  telemetryTransport?: string;
  lastHeartbeatAt?: string;
  connectedAt?: string;
  disconnectedAt?: string;
  remark?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface EdgeNodeMetric {
  id: number;
  nodeId: number;
  cpuPercent?: number;
  memPercent?: number;
  diskPercent?: number;
  temperatureC?: number;
  activeTasks?: number;
  collectedAt?: string;
}

export interface EdgeNodePageReq {
  pageNo?: number;
  pageSize?: number;
  keyword?: string;
  status?: string;
  socModel?: string;
  enabled?: boolean;
}

export const getEdgeNodePage = (params: EdgeNodePageReq) =>
  defHttp.get<{ data: EdgeNodeVO[]; total: number }>({ url: `${EDGE_PREFIX}/node/page`, params });

export const getEdgeNode = (id: number) =>
  defHttp.get<EdgeNodeVO>({ url: `${EDGE_PREFIX}/node/${id}` });

export const getEdgeNodeMetrics = (id: number, params: { minutes?: number; limit?: number } = {}) =>
  defHttp.get<EdgeNodeMetric[]>({ url: `${EDGE_PREFIX}/node/${id}/metrics`, params });

export const updateEdgeNode = (id: number, data: Partial<Pick<EdgeNodeVO, 'name' | 'remark' | 'enabled'>>) =>
  defHttp.put<EdgeNodeVO>({ url: `${EDGE_PREFIX}/node/${id}`, data });

export const deleteEdgeNode = (id: number) =>
  defHttp.delete<boolean>({ url: `${EDGE_PREFIX}/node/${id}` });

export const sendEdgeNodeCommand = (
  id: number,
  command: 'ping' | 'status' | 'runtime.restart' | 'runtime.reload' | 'frp.restart',
  params: Record<string, any> = {},
) => defHttp.post<{ commandId: string; status: string }>({
  url: `${EDGE_PREFIX}/node/${id}/command`,
  data: { command, params },
});
