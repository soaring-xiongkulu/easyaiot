/**
 * POST 外置插件登记 / 启停（无市场）
 */
import { defHttp } from '@/utils/http/axios';

const PREFIX = '/video/post';

const api = <T = any>(
  method: 'get' | 'post' | 'delete' | 'put' | 'patch',
  url: string,
  options: { params?: any; data?: any } = {},
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp[method](
    {
      url,
      headers: { ignoreCancelToken: true } as any,
      ...(method === 'get' || method === 'delete'
        ? { params: options.params }
        : { data: options.data || options.params }),
    },
    { isTransformResponse: true },
  ) as Promise<T>;
};

export interface PostPluginServiceInfo {
  plugin_id: string;
  version: string;
  replicas: number;
  status: string;
  endpoint?: string;
  deploy_mode?: string;
  binding?: any;
  updated_at?: string;
}

export interface PostPluginItem {
  id: string;
  name: string;
  latest_version?: string;
  runtime: string;
  enabled: boolean;
  manifest?: Record<string, any>;
  service?: PostPluginServiceInfo | null;
  created_at?: string;
  updated_at?: string;
}

export interface PostPluginTaskRef {
  id: number;
  task_name?: string;
  task_type?: string;
  is_enabled?: boolean;
  run_status?: string;
}

export interface PostDebugTraceStep {
  plugin?: string;
  detections_in?: number;
  detections_out?: number;
  decision?: string;
  drop_reason?: string;
  enrichment_patch?: Record<string, any>;
  latency_ms?: number;
}

export interface PostDebugPipelineResult {
  result?: string;
  drop_reason?: string;
  trace?: PostDebugTraceStep[];
  alert_payload?: Record<string, any> | null;
  [key: string]: any;
}

export const listPostPlugins = (params?: { enabled?: boolean }) =>
  api<PostPluginItem[]>('get', `${PREFIX}/plugins`, { params });

export const getPostPlugin = (id: string) =>
  api<PostPluginItem>('get', `${PREFIX}/plugins/${encodeURIComponent(id)}`);

export const registerPostPlugin = (data: { manifest: Record<string, any>; endpoint?: string }) =>
  api<PostPluginItem>('post', `${PREFIX}/plugins`, { data });

export const updatePostPlugin = (id: string, data: { enabled?: boolean; manifest?: Record<string, any> }) =>
  api<PostPluginItem>('patch', `${PREFIX}/plugins/${encodeURIComponent(id)}`, { data });

export const deletePostPlugin = (id: string, force = false) =>
  api('delete', `${PREFIX}/plugins/${encodeURIComponent(id)}`, { params: { force } });

export const startPostPlugin = (
  id: string,
  data?: {
    deploy_mode?: 'endpoint' | 'docker';
    endpoint?: string;
    replicas?: number;
    version?: string;
    target_node_id?: number;
  },
) => api<PostPluginServiceInfo>('post', `${PREFIX}/plugins/${encodeURIComponent(id)}/start`, { data });

export const stopPostPlugin = (id: string, data?: { version?: string }) =>
  api<PostPluginServiceInfo>('post', `${PREFIX}/plugins/${encodeURIComponent(id)}/stop`, { data });

export const scalePostPlugin = (id: string, replicas: number, version?: string) =>
  api<PostPluginServiceInfo>('put', `${PREFIX}/plugins/${encodeURIComponent(id)}/replicas`, {
    data: { replicas, version },
  });

export const listPostPluginTasks = (id: string) =>
  api<PostPluginTaskRef[]>('get', `${PREFIX}/plugins/${encodeURIComponent(id)}/tasks`);

/** 经 VIDEO 代理调 POST /debug/pipeline（推荐） */
export const debugPostPipeline = (body: Record<string, any>) =>
  api<PostDebugPipelineResult>('post', `${PREFIX}/debug/pipeline`, { data: body });

/** 直连 POST 引擎（高级兜底；需 POST_DEBUG_HTTP=true） */
export const debugPostPipelineDirect = (baseUrl: string, body: Record<string, any>) => {
  const url = `${baseUrl.replace(/\/$/, '')}/debug/pipeline`;
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(async (r) => {
    const text = await r.text();
    let data: any = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { raw: text };
    }
    if (!r.ok) {
      throw new Error(data?.error || data?.msg || text || `HTTP ${r.status}`);
    }
    return data as PostDebugPipelineResult;
  });
};
