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
