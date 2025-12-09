import { defHttp } from '@/utils/http/axios';

const STREAM_FORWARD_PREFIX = '/video/stream-forward';

// 通用请求封装
const commonApi = <T = any>(
  method: 'get' | 'post' | 'delete' | 'put',
  url: string,
  data?: any,
  headers = {},
  isTransformResponse = true,
  errorMessageMode?: 'none' | 'message' | 'modal' // 如果未指定，使用默认值（message）
) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]<T>({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params: data } : { data })
  }, { isTransformResponse, errorMessageMode });
};

// ====================== 类型定义 ======================
export interface StreamForwardTask {
  id: number;
  task_name: string;
  task_code: string;
  device_ids: string[];
  device_names: string[];
  output_format: 'rtmp' | 'rtsp';
  output_quality: 'low' | 'medium' | 'high';
  output_bitrate?: string;
  status: number;
  is_enabled: boolean;
  run_status: 'running' | 'stopped' | 'restarting';
  exception_reason?: string;
  service_server_ip?: string;
  service_port?: number;
  service_process_id?: number;
  service_last_heartbeat?: string;
  service_log_path?: string;
  total_streams: number;
  last_process_time?: string;
  last_success_time?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface StreamForwardTaskListResponse {
  code: number;
  msg: string;
  data: StreamForwardTask[];
  total: number;
}

// ====================== 推流转发任务管理接口 ======================
/**
 * 获取推流转发任务列表
 */
export const listStreamForwardTasks = (params?: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  device_id?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<StreamForwardTaskListResponse>('get', `${STREAM_FORWARD_PREFIX}/task/list`, { params });
};

/**
 * 获取推流转发任务详情
 */
export const getStreamForwardTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'get',
    `${STREAM_FORWARD_PREFIX}/task/${task_id}`
  );
};

/**
 * 创建推流转发任务
 */
export const createStreamForwardTask = (data: {
  task_name: string;
  device_ids?: string[];
  output_format?: 'rtmp' | 'rtsp';
  output_quality?: 'low' | 'medium' | 'high';
  output_bitrate?: string;
  description?: string;
  is_enabled?: boolean;
}) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'post',
    `${STREAM_FORWARD_PREFIX}/task`,
    data,
    {},
    true,
    'none' // 不自动显示错误，由组件处理
  );
};

/**
 * 更新推流转发任务
 */
export const updateStreamForwardTask = (task_id: number, data: Partial<StreamForwardTask>) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'put',
    `${STREAM_FORWARD_PREFIX}/task/${task_id}`,
    data,
    {},
    true,
    'none' // 不自动显示错误，由组件处理
  );
};

/**
 * 删除推流转发任务
 */
export const deleteStreamForwardTask = (task_id: number) => {
  return commonApi('delete', `${STREAM_FORWARD_PREFIX}/task/${task_id}`);
};

/**
 * 启动推流转发任务
 */
export const startStreamForwardTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'post',
    `${STREAM_FORWARD_PREFIX}/task/${task_id}/start`
  );
};

/**
 * 停止推流转发任务
 */
export const stopStreamForwardTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'post',
    `${STREAM_FORWARD_PREFIX}/task/${task_id}/stop`
  );
};

/**
 * 重启推流转发任务
 */
export const restartStreamForwardTask = (task_id: number) => {
  return commonApi<{ code: number; msg: string; data: StreamForwardTask }>(
    'post',
    `${STREAM_FORWARD_PREFIX}/task/${task_id}/restart`
  );
};

/**
 * 获取推流转发任务服务状态
 */
export const getStreamForwardTaskStatus = (task_id: number) => {
  return commonApi<{
    code: number;
    msg: string;
    data: {
      task_id: number;
      task_name: string;
      server_ip?: string;
      port?: number;
      process_id?: number;
      last_heartbeat?: string;
      log_path?: string;
      status: 'running' | 'stopped';
      run_status: 'running' | 'stopped' | 'restarting';
      total_streams: number;
    };
  }>('get', `${STREAM_FORWARD_PREFIX}/task/${task_id}/status`);
};

/**
 * 获取推流转发任务日志
 */
export const getStreamForwardTaskLogs = (task_id: number, params?: {
  lines?: number;
  date?: string;
}) => {
  return commonApi<{
    code: number;
    msg: string;
    data: {
      logs: string;
      total_lines: number;
      log_file: string;
      is_all_file: boolean;
    };
  }>('get', `${STREAM_FORWARD_PREFIX}/task/${task_id}/logs`, params);
};

/**
 * 获取推流转发任务关联的摄像头推流地址列表
 */
export const getStreamForwardTaskStreams = (task_id: number) => {
  return commonApi<{
    code: number;
    msg: string;
    data: Array<{
      device_id: string;
      device_name: string;
      rtmp_stream: string;
      http_stream: string;
      source: string;
      cover_image_path?: string;
    }>;
  }>('get', `${STREAM_FORWARD_PREFIX}/task/${task_id}/streams`);
};

