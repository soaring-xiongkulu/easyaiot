/**
 * 算法任务、抽帧器、排序器管理接口
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
import {defHttp} from '@/utils/http/axios';

const ALGORITHM_PREFIX = '/video/algorithm';

// 通用请求封装
const commonApi = <T = any>(method: 'get' | 'post' | 'delete' | 'put', url: string, options: { params?: any; data?: any; errorMessageMode?: 'none' | 'message' | 'modal'; timeout?: number } = {}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: {
      // @ts-ignore
      ignoreCancelToken: true,
    },
    // 单接口超时覆盖（默认全局 10s）：停止/启动/重启需要等待进程清理，耗时较长
    ...(options.timeout ? { timeout: options.timeout } : {}),
    ...(method === 'get' ? { params: options.params } : { data: options.data || options.params }),
  }, {
    isTransformResponse: true,
    errorMessageMode: options.errorMessageMode, // 如果未指定，使用默认值（message）
  }) as Promise<T>;
};

// ====================== 算法任务管理接口 ======================
export interface AlgorithmTask {
  id: number;
  task_name: string;
  task_code: string;
  task_type: 'realtime' | 'snap' | 'patrol';
  /** 执行后端：python（默认）| cpp（本机 RUNTIME） */
  executor?: 'python' | 'cpp' | string;
  runtime_bin_path?: string;
  runtime_control_port?: number;
  device_ids?: string[];
  device_names?: string[];
  pusher_id?: number;
  pusher_name?: string;
  // 模型配置（直接选择模型列表，不再依赖模型服务接口）
  model_ids?: number[]; // 关联的模型ID列表
  model_names?: string; // 关联的模型名称列表（逗号分隔，冗余字段，用于快速显示）
  /** YOLO 检测置信度阈值（0~1，默认 0.5） */
  detect_conf?: number;
  // 实时算法任务配置
  extract_interval?: number; // 抽帧间隔（每N帧抽一次）
  motion_gate_enabled?: boolean;
  motion_gate_config?: { preset?: string; [key: string]: unknown };
  // 追踪配置
  tracking_enabled?: boolean; // 是否启用目标追踪
  tracking_similarity_threshold?: number; // 追踪相似度阈值
  tracking_max_age?: number; // 追踪目标最大存活帧数
  tracking_smooth_alpha?: number; // 追踪平滑系数
  // 告警配置
  alert_event_enabled?: boolean; // 是否启用告警事件
  alert_event_suppress_time?: number; // 告警事件抑制时间（秒），减轻 Kafka 积压
  /** 告警触发类别标签：仅检测到所选标签时才触发告警 */
  alert_class_names?: string[];
  face_detection_enabled?: boolean; // 是否启用人脸检测
  plate_detection_enabled?: boolean; // 是否启用车牌检测
  face_matching_enabled?: boolean; // 是否启用人脸匹配（默认关闭）
  face_library_ids?: number[]; // 关联人脸库（可多选）
  face_library_names?: string[];
  face_matching_threshold?: number; // 匹配阈值（可选，覆盖人脸库默认）
  plate_matching_enabled?: boolean; // 是否启用车牌匹配（默认关闭）
  plate_library_ids?: number[]; // 关联车牌库（可多选）
  plate_library_names?: string[];
  /** 匹配业务标签：非空时在所有标签相交的启用库中检索；留空则仅匹配关联库 */
  matching_business_tags?: string[];
  alert_notification_enabled?: boolean; // 是否启用告警通知
  alert_notification_config?: {
    channels: Array<{
      method: string; // 通知方式: sms, email, wxcp, http, ding, feishu
      template_id: string | number; // 模板ID
      template_name?: string; // 模板名称
    }>;
  };
  alarm_suppress_time?: number; // 告警通知抑制时间（秒）
  // 抓拍相关字段（仅抓拍算法任务）
  cron_expression?: string;
  frame_skip?: number;
  total_captures?: number;
  last_capture_time?: string;
  // 通用字段
  status: number; // 0:正常, 1:异常
  is_enabled: boolean; // true:运行中, false:已停止
  exception_reason?: string;
  total_frames: number;
  total_detections: number;
  last_process_time?: string;
  last_success_time?: string;
  algorithm_services?: AlgorithmModelService[]; // 保留以兼容旧数据
  sam_supplement_enabled?: boolean;
  sam_supplement_config?: {
    pipeline_mode?: 'none' | 'refine_mask' | 'open_vocab' | 'alert_verify';
    text_prompts?: string[];
    conf?: number;
    trigger?: 'always' | 'on_interval' | 'on_alert' | 'on_yolo_empty';
    interval_frames?: number;
    merge_iou?: number;
    return_masks?: boolean;
  };
  /** 是否启用人体姿态分析 */
  pose_analysis_enabled?: boolean;
  /** 人体姿态分析配置 */
  pose_analysis_config?: {
    model_file_path?: string;
    conf?: number;
    trigger?: 'always' | 'on_interval' | 'on_person';
    interval_frames?: number;
  };
  service_names?: string; // 关联的算法服务名称列表（逗号分隔，冗余字段，用于快速显示）
  defense_mode?: string; // 布防模式: full(全防), half(半防), day(白天), night(夜间)
  defense_schedule?: string | number[][]; // 布防时段: JSON字符串或二维数组，7天×24小时
  /** 调度策略: local(本机) | auto(自动调度) | node(指定节点) */
  schedule_policy?: 'local' | 'auto' | 'node';
  /** 自动调度时是否优先 GPU 节点 */
  prefer_gpu?: boolean;
  /** 指定部署节点 ID（schedule_policy=node 时） */
  target_node_id?: number | null;
  /** 实际运行节点 ID（只读，启动后由控制面写入） */
  node_id?: number | null;
  /** 是否启用 AI 后处理脚本 */
  post_process_enabled?: boolean;
  /** 后处理脚本文件名 */
  post_process_script?: string;
  /** 后处理 Worker 副本数 */
  post_process_replicas?: number;
  /** POST 定制后处理 pipeline JSON */
  post_pipeline?: Array<{
    plugin: string;
    version?: string;
    enabled?: boolean;
    params?: Record<string, unknown>;
    fail_strategy?: string;
    endpoint?: string;
  }> | null;
  created_at?: string;
  updated_at?: string;
}

export interface AlgorithmTaskListResponse {
  code: number;
  msg: string;
  data: AlgorithmTask[];
  total: number;
}

export const listAlgorithmTasks = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  device_id?: string;
  task_type?: 'realtime' | 'snap';
  is_enabled?: boolean;
}) => {
  return commonApi<AlgorithmTaskListResponse>('get', `${ALGORITHM_PREFIX}/task/list`, { params });
};

export const getAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}`
  );
};

/** 本机 VIDEO 侧 RUNTIME 版本与就绪状态 */
export interface RuntimeInfo {
  ready?: boolean;
  binPath?: string | null;
  version?: string | null;
  git?: string | null;
  builtAt?: string | null;
  arch?: string | null;
  buildMode?: string | null;
  ort?: string | null;
  source?: string | null;
  versionFile?: string | null;
}

export const getRuntimeInfo = () => {
  return commonApi<RuntimeInfo>('get', `${ALGORITHM_PREFIX}/runtime/info`, {
    errorMessageMode: 'none',
  });
};

export const createAlgorithmTask = (data: {
  task_name: string;
  task_type?: 'realtime' | 'snap';
  pusher_id?: number;
  device_ids?: string[];
  // 模型配置
  model_ids?: number[];
  /** YOLO 检测置信度阈值（0~1，默认 0.5） */
  detect_conf?: number;
  // 实时算法任务配置
  extract_interval?: number;
  // 追踪配置
  tracking_enabled?: boolean;
  tracking_similarity_threshold?: number;
  tracking_max_age?: number;
  tracking_smooth_alpha?: number;
  // 告警配置
  alert_event_enabled?: boolean;
  alert_event_suppress_time?: number;
  alert_class_names?: string[];
  face_detection_enabled?: boolean;
  plate_detection_enabled?: boolean;
  face_matching_enabled?: boolean;
  face_library_ids?: number[];
  face_matching_threshold?: number;
  plate_matching_enabled?: boolean;
  plate_library_ids?: number[];
  matching_business_tags?: string[];
  alert_notification_enabled?: boolean;
  alert_notification_config?: {
    channels: Array<{
      method: string;
      template_id: string | number;
      template_name?: string;
    }>;
  };
  alarm_suppress_time?: number;
  // 抓拍算法任务配置
  cron_expression?: string;
  frame_skip?: number;
  // 通用配置
  is_enabled?: boolean;
  defense_mode?: string;
  defense_schedule?: string;
  /** 是否启用人体姿态分析 */
  pose_analysis_enabled?: boolean;
  pose_analysis_config?: {
    model_file_path?: string;
    conf?: number;
    trigger?: 'always' | 'on_interval' | 'on_person';
    interval_frames?: number;
  };
  /** 是否启用 AI 后处理脚本，默认关闭 */
  post_process_enabled?: boolean;
  /** 后处理 Worker 副本数 */
  post_process_replicas?: number;
}) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task`,
    { data, errorMessageMode: 'none' } // 不自动显示错误，由组件处理
  );
};

export const updateAlgorithmTask = (task_id: number, data: Partial<AlgorithmTask>) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'put',
    `${ALGORITHM_PREFIX}/task/${task_id}`,
    { data, errorMessageMode: 'none' } // 不自动显示错误，由组件处理
  );
};

export const deleteAlgorithmTask = (task_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/task/${task_id}`);
};

export const startAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/start`,
    { timeout: 30000 }
  );
};

export const stopAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/stop`,
    { timeout: 30000 }
  );
};

export const restartAlgorithmTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/restart`,
    { timeout: 30000 }
  );
};

// ====================== 抽帧器管理接口 ======================
export interface FrameExtractor {
  id: number;
  extractor_name: string;
  extractor_code: string;
  extractor_type: string; // interval:按间隔, time:按时间
  interval: number;
  description?: string;
  is_enabled: boolean;
  status?: string; // running:运行中, stopped:已停止, error:错误
  server_ip?: string;
  port?: number;
  process_id?: number;
  last_heartbeat?: string;
  log_path?: string;
  task_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface FrameExtractorListResponse {
  code: number;
  msg: string;
  data: FrameExtractor[];
  total: number;
}

export const listFrameExtractors = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi<FrameExtractorListResponse>('get', `${ALGORITHM_PREFIX}/extractor/list`, { params });
};

export const getFrameExtractor = (extractor_id: number) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'get',
    `${ALGORITHM_PREFIX}/extractor/${extractor_id}`
  );
};

export const createFrameExtractor = (data: {
  extractor_name: string;
  extractor_type?: string;
  interval?: number;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'post',
    `${ALGORITHM_PREFIX}/extractor`,
    { data }
  );
};

export const updateFrameExtractor = (extractor_id: number, data: Partial<FrameExtractor>) => {
  return commonApi<{ code: number; msg: string; data: FrameExtractor }>(
    'put',
    `${ALGORITHM_PREFIX}/extractor/${extractor_id}`,
    { data }
  );
};

export const deleteFrameExtractor = (extractor_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/extractor/${extractor_id}`);
};

// ====================== 排序器管理接口 ======================
export interface Sorter {
  id: number;
  sorter_name: string;
  sorter_code: string;
  sorter_type: string; // confidence:置信度, time:时间, score:分数
  sort_order: string; // asc:升序, desc:降序
  description?: string;
  is_enabled: boolean;
  status?: string; // running:运行中, stopped:已停止, error:错误
  server_ip?: string;
  port?: number;
  process_id?: number;
  last_heartbeat?: string;
  log_path?: string;
  task_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SorterListResponse {
  code: number;
  msg: string;
  data: Sorter[];
  total: number;
}

export const listSorters = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi<SorterListResponse>('get', `${ALGORITHM_PREFIX}/sorter/list`, { params });
};

export const getSorter = (sorter_id: number) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'get',
    `${ALGORITHM_PREFIX}/sorter/${sorter_id}`
  );
};

export const createSorter = (data: {
  sorter_name: string;
  sorter_type?: string;
  sort_order?: string;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'post',
    `${ALGORITHM_PREFIX}/sorter`,
    { data }
  );
};

export const updateSorter = (sorter_id: number, data: Partial<Sorter>) => {
  return commonApi<{ code: number; msg: string; data: Sorter }>(
    'put',
    `${ALGORITHM_PREFIX}/sorter/${sorter_id}`,
    { data }
  );
};

export const deleteSorter = (sorter_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/sorter/${sorter_id}`);
};

// ====================== 算法任务的服务管理接口 ======================
export interface AlgorithmModelService {
  id: number;
  task_id: number;
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method: string;
  request_headers?: any;
  request_body_template?: any;
  timeout: number;
  is_enabled: boolean;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export const listTaskServices = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService[] }>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/services`
  );
};

export const createTaskService = (task_id: number, data: {
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: any;
  request_body_template?: any;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/service`,
    { data }
  );
};

export const updateTaskService = (service_id: number, data: Partial<AlgorithmModelService>) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmModelService }>(
    'put',
    `${ALGORITHM_PREFIX}/task/service/${service_id}`,
    { data }
  );
};

export const deleteTaskService = (service_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/task/service/${service_id}`);
};

// ====================== 推送器管理接口 ======================
export interface Pusher {
  id: number;
  pusher_name: string;
  pusher_code: string;
  video_stream_enabled: boolean;
  video_stream_url?: string;
  video_stream_format: string; // rtmp:RTMP, rtsp:RTSP, webrtc:WebRTC
  video_stream_quality: string; // low:低, medium:中, high:高
  event_alert_enabled: boolean;
  event_alert_url?: string;
  event_alert_method: string; // http:HTTP, websocket:WebSocket, kafka:Kafka
  event_alert_format: string; // json:JSON, xml:XML
  event_alert_headers?: any;
  event_alert_template?: any;
  description?: string;
  is_enabled: boolean;
  status?: string; // running:运行中, stopped:已停止, error:错误
  server_ip?: string;
  port?: number;
  process_id?: number;
  last_heartbeat?: string;
  log_path?: string;
  task_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PusherListResponse {
  code: number;
  msg: string;
  data: Pusher[];
  total: number;
}

export const listPushers = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<PusherListResponse>('get', `${ALGORITHM_PREFIX}/pusher/list`, { params });
};

export const getPusher = (pusher_id: number) => {
  return commonApi<{ code: number; msg: string; data: Pusher }>(
    'get',
    `${ALGORITHM_PREFIX}/pusher/${pusher_id}`
  );
};

export const createPusher = (data: {
  pusher_name: string;
  video_stream_enabled?: boolean;
  video_stream_url?: string;
  video_stream_format?: string;
  video_stream_quality?: string;
  event_alert_enabled?: boolean;
  event_alert_url?: string;
  event_alert_method?: string;
  event_alert_format?: string;
  event_alert_headers?: any;
  event_alert_template?: any;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: Pusher }>(
    'post',
    `${ALGORITHM_PREFIX}/pusher`,
    { data }
  );
};

export const updatePusher = (pusher_id: number, data: Partial<Pusher>) => {
  return commonApi<{ code: number; msg: string; data: Pusher }>(
    'put',
    `${ALGORITHM_PREFIX}/pusher/${pusher_id}`,
    { data }
  );
};

export const deletePusher = (pusher_id: number) => {
  return commonApi('delete', `${ALGORITHM_PREFIX}/pusher/${pusher_id}`);
};

// ====================== 服务状态查询接口 ======================
export interface RealtimeServiceStatus {
  task_id: number;
  task_name: string;
  server_ip?: string;
  port?: number;
  process_id?: number;
  last_heartbeat?: string;
  log_path?: string;
  status: 'running' | 'stopped';
  run_status: string;
}

export interface TaskServicesStatus {
  extractor: FrameExtractor | null;
  sorter: Sorter | null;
  pusher: Pusher | null;
  realtime_service: RealtimeServiceStatus | null;
}

export interface TaskServicesStatusResponse {
  code: number;
  msg: string;
  data: TaskServicesStatus;
}

export const getTaskServicesStatus = (task_id: number) => {
  return commonApi<TaskServicesStatusResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/services/status`
  );
};

// ====================== 日志查看接口 ======================
export interface ServiceLogsResponse {
  code: number;
  msg: string;
  data: {
    logs: string;
    total_lines: number;
    log_file: string;
    is_all_file: boolean;
  };
}

// 响应转换器会将 data.data 直接返回，所以实际返回的是这个类型
export interface ServiceLogsData {
  logs: string;
  total_lines: number;
  log_file: string;
  is_all_file: boolean;
}

export const getTaskExtractorLogs = (task_id: number, params?: {
  lines?: number;
  date?: string;
}) => {
  return commonApi<ServiceLogsData | ServiceLogsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/extractor/logs`,
    { params }
  );
};

export const getTaskSorterLogs = (task_id: number, params?: {
  lines?: number;
  date?: string;
}) => {
  return commonApi<ServiceLogsData | ServiceLogsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/sorter/logs`,
    { params }
  );
};

export const getTaskPusherLogs = (task_id: number, params?: {
  lines?: number;
  date?: string;
}) => {
  return commonApi<ServiceLogsData | ServiceLogsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/pusher/logs`,
    { params }
  );
};

export const getTaskRealtimeLogs = (task_id: number, params?: {
  lines?: number;
  date?: string;
}) => {
  return commonApi<ServiceLogsData | ServiceLogsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/realtime/logs`,
    { params }
  );
};

// ====================== 推流地址查询接口 ======================
export interface CameraStreamInfo {
  task_id: number;
  task_name?: string;
  model_names?: string;
  stream_key: string;
  device_id: string;
  device_name: string;
  http_stream?: string;
  rtmp_stream?: string;
  source?: string;
  pusher_rtmp_url?: string;
  pusher_http_url?: string;
  // 任务级 AI HTTP 流地址
  ai_http_stream?: string;
  // 任务级 AI RTMP 流地址
  ai_rtmp_stream?: string;
  // 设备封面图路径
  cover_image_path?: string;
  source_mode?: 'pending' | 'shared' | 'direct' | 'direct_fallback';
  configured_source_mode?: 'shared' | 'direct';
  source_status?: 'starting' | 'source_waiting' | 'inferencing' | 'publishing' | 'degraded' | 'stopped' | 'failed';
  source_subscriber_count?: number;
  source_decode_fps?: number;
  last_frame_time?: string;
  last_detection_time?: string;
  last_alert_time?: string;
  runtime_error?: string;
}

export interface TaskStreamsResponse {
  code: number;
  msg: string;
  data: CameraStreamInfo[];
}

export const getTaskStreams = (task_id: number) => {
  return commonApi<TaskStreamsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/streams`
  );
};

/** 查询摄像头所有运行中算法任务的独立画框流 */
export const getDeviceTaskStreams = (device_id: string) => {
  return commonApi<TaskStreamsResponse>(
    'get',
    `${ALGORITHM_PREFIX}/device/${encodeURIComponent(device_id)}/task-streams`
  );
};

export interface CameraSourceRuntimeStatus {
  source_id: string;
  device_id: string;
  status: 'starting' | 'source_waiting' | 'streaming' | 'stopped' | 'failed';
  subscriber_count: number;
  subscriber_task_ids: string[];
  decode_fps: number;
  frame_count: number;
  last_frame_time?: number;
  reconnect_count: number;
  error_message?: string;
}

export const getCameraSourceStatus = async (device_id?: string): Promise<CameraSourceRuntimeStatus[]> => {
  const response = await commonApi<CameraSourceRuntimeStatus[] | { code: number; msg: string; data: CameraSourceRuntimeStatus[] }>(
    'get',
    `${ALGORITHM_PREFIX}/source/status`,
    { params: { device_id } }
  );
  if (Array.isArray(response)) {
    return response;
  }
  return Array.isArray(response?.data) ? response.data : [];
};

// ====================== AI 后处理 ======================
export interface PostProcessStatus {
  task_id: number;
  post_process_enabled: boolean;
  post_process_script: string;
  script_exists: boolean;
  workspace_path: string;
  ide_url: string;
  workspace_root: string;
}

export interface PostProcessIdeUrl {
  ide_url: string;
  task_id: number;
  task_name: string;
}

export const getPostProcessStatus = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: PostProcessStatus }>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/post-process/status`,
    { errorMessageMode: 'none' },
  );
};

export const initPostProcessWorkspace = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: Record<string, unknown> }>(
    'post',
    `${ALGORITHM_PREFIX}/task/${task_id}/post-process/init`,
    { errorMessageMode: 'none' },
  );
};

export const getPostProcessIdeUrl = (task_id: number) => {
  return commonApi<PostProcessIdeUrl>(
    'get',
    `${ALGORITHM_PREFIX}/task/${task_id}/post-process/ide-url`,
    { errorMessageMode: 'none' },
  );
};

export const togglePostProcess = (
  task_id: number,
  enabled: boolean,
  post_process_replicas?: number,
) => {
  return commonApi<{ code: number; msg: string; data: AlgorithmTask }>(
    'put',
    `${ALGORITHM_PREFIX}/task/${task_id}/post-process/toggle`,
    {
      data: {
        enabled,
        ...(post_process_replicas != null ? { post_process_replicas } : {}),
      },
      errorMessageMode: 'none',
    },
  );
};

export interface PostProcessResultItem {
  id: number;
  task_id: number;
  task_name?: string;
  task_type?: string;
  device_id: string;
  device_name?: string;
  frame_number?: number;
  event_time?: string;
  counts?: Record<string, number>;
  events?: Record<string, unknown>[];
  alerts?: Record<string, unknown>[];
  payload?: Record<string, unknown>;
  correlation_id?: string;
  created_at?: string;
}

export const listPostProcessResults = (
  task_id: number,
  params?: {
    pageNo?: number;
    pageSize?: number;
    device_id?: string;
    begin_datetime?: string;
    end_datetime?: string;
  },
) => {
  return commonApi<{
    code: number;
    msg: string;
    items: PostProcessResultItem[];
    total: number;
    page_no: number;
    page_size: number;
  }>('get', `${ALGORITHM_PREFIX}/task/${task_id}/post-process/results`, {
    params,
    errorMessageMode: 'none',
  });
};
// ====================== POST 后处理规则链 ======================
export interface PostPipelineCatalogResponse {
  builtins: Array<{
    id: string;
    name: string;
    kinds: string[];
    builtin: boolean;
    description?: string;
    params_schema?: Record<string, unknown>;
    version?: string;
  }>;
  externals: Array<{
    id: string;
    name: string;
    kinds: string[];
    builtin: boolean;
    description?: string;
    params_schema?: Record<string, unknown>;
    version?: string;
    service?: Record<string, unknown>;
  }>;
}

export interface PostPipelineDebugPayload {
  pipeline_override?: AlgorithmTask['post_pipeline'];
  until_plugin?: string;
  task_id?: number;
  task_name?: string;
  task_type?: string;
  device_ids?: string[];
  event?: Record<string, unknown>;
  regions?: Record<string, unknown>[];
}

export interface PostPipelineDebugResponse {
  result?: string;
  drop_reason?: string;
  trace?: Array<Record<string, unknown>>;
  alert_payload?: Record<string, unknown> | null;
  error?: string;
}

export const getPostPipelineCatalog = () => {
  return commonApi<PostPipelineCatalogResponse>(
    'get',
    `${ALGORITHM_PREFIX}/task/post-pipeline/catalog`,
    { errorMessageMode: 'none' },
  );
};

export const debugPostPipeline = (payload: PostPipelineDebugPayload, taskId?: number | null) => {
  const url = taskId
    ? `${ALGORITHM_PREFIX}/task/${taskId}/post-pipeline/debug`
    : `${ALGORITHM_PREFIX}/task/post-pipeline/debug`;
  return commonApi<PostPipelineDebugResponse>('post', url, {
    data: payload,
    errorMessageMode: 'none',
  });
};
