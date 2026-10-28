/**
 * POST 定制后处理：插件目录与调试 API
 */
import { defHttp } from '@/utils/http/axios';

const POST_PREFIX = '/video/post';

export interface PostPipelineStep {
  plugin: string;
  version?: string;
  enabled?: boolean;
  params?: Record<string, unknown>;
  fail_strategy?: 'fail_open' | 'fail_closed' | string;
  endpoint?: string;
}

export interface PostPluginMeta {
  id: string;
  name: string;
  kinds: string[];
  builtin: boolean;
  description?: string;
  params_schema?: Record<string, unknown>;
  version?: string;
  service?: Record<string, unknown> | null;
}

export interface PostPluginCatalog {
  builtins: PostPluginMeta[];
  externals: PostPluginMeta[];
}

export interface PostStepTrace {
  plugin: string;
  detections_in: number;
  detections_out: number;
  decision: string;
  drop_reason?: string;
  enrichment_patch?: Record<string, unknown>;
  latency_ms: number;
}

export interface PostPipelineDebugResult {
  result: 'pass' | 'drop' | string;
  drop_reason?: string;
  trace?: PostStepTrace[];
  alert_payload?: Record<string, unknown> | null;
}

export interface PostPluginDebugResult {
  delta?: Record<string, unknown>;
  detections?: Array<Record<string, unknown>>;
  region?: string;
  plugin?: string;
}

export interface InferEventSample {
  schema: string;
  event_kind: string;
  correlation_id: string;
  task_id: number;
  task_name?: string;
  task_type: string;
  device_id: string;
  timestamp: string;
  frame_width: number;
  frame_height: number;
  detections: Array<{
    bbox: number[];
    class_id?: number;
    class_name: string;
    confidence: number;
    track_id?: number;
  }>;
}

const commonApi = <T = any>(
  method: 'get' | 'post',
  url: string,
  data?: any,
) =>
  defHttp[method]({ url, data, params: method === 'get' ? data : undefined }, {
    isTransformResponse: true,
  }) as Promise<T>;

export const getPostPluginCatalog = () =>
  commonApi<PostPluginCatalog>('get', `${POST_PREFIX}/plugins/catalog`);

export interface PostBusinessResult {
  id: number;
  time: string;
  device_id: string;
  device_name: string;
  region: string;
  results: Record<string, Record<string, any>>;
}

export const getPostBusinessResults = (taskId: number, params: {
  start: string; end: string; page: number; page_size: number; plugin?: string; device_id?: string; region_id?: number;
}) => commonApi<{ items: PostBusinessResult[]; total: number; summary: Record<string, number> }>(
  'get', `${POST_PREFIX}/tasks/${taskId}/results`, params,
);

export interface PostBindingState {
  revision: number;
  task: Record<string, any>;
  pipeline: PostPipelineStep[];
  regions: Array<{ id: number; device_id: string; name: string; type: string; enabled: boolean }>;
  legacy_plugins: string[];
  runtime_sync_status?: string;
}
export const getPostBindings = (taskId: number) => commonApi<PostBindingState>('get', `${POST_PREFIX}/tasks/${taskId}/bindings`);

/** 训练场投放一帧：模拟人经真实 MQTT InferEvent 驱动 POST 插件引擎（生产与隔离回归同一路由） */
export const postTrainFrame = (taskId: number, body: {
  device_id: string;
  actors: Array<{ track_id: number; x: number; y: number }>;
}) => commonApi<{ published: number }>('post', `${POST_PREFIX}/tasks/${taskId}/trainframe`, body);
export const savePostRegionBinding = (taskId: number, regionId: number, body: {
  expected_revision: number; plugin: string; params?: Record<string, unknown>; enabled?: boolean; remove?: boolean;
}) => defHttp.put<PostBindingState>({ url: `${POST_PREFIX}/tasks/${taskId}/regions/${regionId}/binding`, data: body }, { isTransformResponse: true, retryRequest: { isOpenRetry: false, count: 0, waitTime: 0 } });

export const debugPostPipeline = (body: {
  event: InferEventSample;
  pipeline_override?: PostPipelineStep[];
  until_plugin?: string;
  task?: Record<string, unknown>;
  regions?: Array<Record<string, unknown>>;
}) => commonApi<PostPipelineDebugResult>('post', `${POST_PREFIX}/debug/pipeline`, body);

export const debugPostPlugin = (body: {
  plugin: string;
  endpoint?: string;
  event: InferEventSample;
  params?: Record<string, unknown>;
  task?: Record<string, unknown>;
  regions?: Array<Record<string, unknown>>;
}) => commonApi<PostPluginDebugResult>('post', `${POST_PREFIX}/debug/plugin`, body);

export const getPostSampleEvent = (
  taskId: number,
  params?: { device_id?: string; frame_width?: number; frame_height?: number },
) =>
  commonApi<{ event: InferEventSample; regions: Array<Record<string, unknown>> }>(
    'get',
    `${POST_PREFIX}/debug/sample-event/${taskId}`,
    params,
  );
