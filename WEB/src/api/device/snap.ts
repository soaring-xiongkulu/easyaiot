import {defHttp} from '@/utils/http/axios';

const SNAP_PREFIX = '/video/snap';

// 通用请求封装
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params } : { data: params })
  }, { isTransformResponse: isTransformResponse });
};

// ====================== 抓拍空间管理接口 ======================
export interface SnapSpace {
  id: number;
  space_name: string;
  space_code: string;
  bucket_name: string;
  save_mode: number; // 0:标准存储, 1:归档存储
  save_time: number; // 0:永久保存, >=7(单位:天)
  description?: string;
  task_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SnapSpaceListResponse {
  code: number;
  msg: string;
  data: SnapSpace[];
  total: number;
}

/**
 * 获取抓拍空间列表
 */
export const getSnapSpaceList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi('get', `${SNAP_PREFIX}/space/list`, params);
};

/**
 * 获取抓拍空间详情
 */
export const getSnapSpace = (space_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/space/${space_id}`);
};

/**
 * 创建抓拍空间
 */
export const createSnapSpace = (data: {
  space_name: string;
  save_mode?: number;
  save_time?: number;
  description?: string;
}) => {
  return commonApi('post', `${SNAP_PREFIX}/space`, data);
};

/**
 * 更新抓拍空间
 */
export const updateSnapSpace = (space_id: number, data: {
  space_name?: string;
  save_mode?: number;
  save_time?: number;
  description?: string;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/space/${space_id}`, data);
};

/**
 * 删除抓拍空间
 */
export const deleteSnapSpace = (space_id: number) => {
  return commonApi('delete', `${SNAP_PREFIX}/space/${space_id}`);
};

// ====================== 抓拍任务管理接口 ======================
export interface SnapTask {
  id: number;
  task_name: string;
  task_code: string;
  space_id: number;
  space_name?: string;
  device_id: string;
  device_name?: string;
  capture_type: number; // 0:抽帧, 1:抓拍
  cron_expression: string;
  frame_skip: number;
  algorithm_enabled: boolean;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_night_mode: boolean;
  alarm_enabled: boolean;
  alarm_type: number; // 0:短信告警, 1:邮箱告警, 2:短信+邮箱
  phone_number?: string;
  email?: string;
  notify_users?: Array<{ id?: number; name?: string; phone?: string; email?: string }> | string; // 通知人列表
  notify_methods?: string; // 通知方式，多个用逗号分割
  alarm_suppress_time?: number; // 告警通知抑制时间（秒）
  last_notify_time?: string; // 最后通知时间
  auto_filename: boolean;
  custom_filename_prefix?: string;
  status: number; // 0:正常, 1:异常
  is_enabled: boolean;
  run_status?: string; // running:运行中, stopped:已停止, restarting:重启中
  exception_reason?: string;
  total_captures: number;
  last_capture_time?: string;
  last_success_time?: string;
  algorithm_services?: AlgorithmModelService[]; // 关联的算法模型服务列表
  created_at?: string;
  updated_at?: string;
}

export interface SnapTaskListResponse {
  code: number;
  msg: string;
  data: SnapTask[];
  total: number;
}

/**
 * 获取抓拍任务列表
 */
export const getSnapTaskList = (params: {
  pageNo?: number;
  pageSize?: number;
  space_id?: number;
  device_id?: string;
  search?: string;
  status?: number;
}) => {
  return commonApi('get', `${SNAP_PREFIX}/task/list`, params);
};

/**
 * 获取抓拍任务详情
 */
export const getSnapTask = (task_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/task/${task_id}`);
};

/**
 * 创建抓拍任务
 */
export const createSnapTask = (data: {
  task_name: string;
  space_id: number;
  device_id: string;
  capture_type?: number;
  cron_expression?: string;
  frame_skip?: number;
  algorithm_enabled?: boolean;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_night_mode?: boolean;
  alarm_enabled?: boolean;
  alarm_type?: number;
  phone_number?: string;
  email?: string;
  notify_users?: Array<{ id?: number; name?: string; phone?: string; email?: string }> | string;
  notify_methods?: string;
  alarm_suppress_time?: number;
  auto_filename?: boolean;
  custom_filename_prefix?: string;
}) => {
  return commonApi('post', `${SNAP_PREFIX}/task`, data);
};

/**
 * 更新抓拍任务
 */
export const updateSnapTask = (task_id: number, data: {
  task_name?: string;
  space_id?: number;
  device_id?: string;
  capture_type?: number;
  cron_expression?: string;
  frame_skip?: number;
  algorithm_enabled?: boolean;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_night_mode?: boolean;
  alarm_enabled?: boolean;
  alarm_type?: number;
  phone_number?: string;
  email?: string;
  notify_users?: Array<{ id?: number; name?: string; phone?: string; email?: string }> | string;
  notify_methods?: string;
  alarm_suppress_time?: number;
  auto_filename?: boolean;
  custom_filename_prefix?: string;
  is_enabled?: boolean;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/task/${task_id}`, data);
};

/**
 * 删除抓拍任务
 */
export const deleteSnapTask = (task_id: number) => {
  return commonApi('delete', `${SNAP_PREFIX}/task/${task_id}`);
};

/**
 * 启动抓拍任务
 */
export const startSnapTask = (task_id: number) => {
  return commonApi('post', `${SNAP_PREFIX}/task/${task_id}/start`);
};

/**
 * 停止抓拍任务
 */
export const stopSnapTask = (task_id: number) => {
  return commonApi('post', `${SNAP_PREFIX}/task/${task_id}/stop`);
};

/**
 * 重启抓拍任务
 */
export const restartSnapTask = (task_id: number) => {
  return commonApi('post', `${SNAP_PREFIX}/task/${task_id}/restart`);
};

/**
 * 获取任务日志
 */
export const getSnapTaskLogs = (task_id: number, params: {
  pageNo?: number;
  pageSize?: number;
  level?: string;
}) => {
  return commonApi('get', `${SNAP_PREFIX}/task/${task_id}/logs`, params);
};

// ====================== 检测区域管理接口 ======================
export interface DetectionRegion {
  id: number;
  task_id: number;
  region_name: string;
  region_type: 'polygon' | 'rectangle';
  points: Array<{ x: number; y: number }>;
  image_id?: number;
  image_path?: string;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_enabled: boolean;
  color: string;
  opacity: number;
  is_enabled: boolean;
  sort_order: number;
  services?: RegionModelService[]; // 关联的区域模型服务列表
  created_at?: string;
  updated_at?: string;
}

/**
 * 获取任务的检测区域列表
 */
export const getDetectionRegions = (task_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/task/${task_id}/regions`);
};

/**
 * 获取检测区域详情
 */
export const getDetectionRegion = (region_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/region/${region_id}`);
};

/**
 * 创建检测区域
 */
export const createDetectionRegion = (data: {
  task_id: number;
  region_name: string;
  region_type?: 'polygon' | 'rectangle';
  points: Array<{ x: number; y: number }>;
  image_id?: number;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_enabled?: boolean;
  color?: string;
  opacity?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('post', `${SNAP_PREFIX}/region`, data);
};

/**
 * 更新检测区域
 */
export const updateDetectionRegion = (region_id: number, data: {
  region_name?: string;
  region_type?: 'polygon' | 'rectangle';
  points?: Array<{ x: number; y: number }>;
  image_id?: number;
  algorithm_type?: string;
  algorithm_model_id?: number;
  algorithm_threshold?: number;
  algorithm_enabled?: boolean;
  color?: string;
  opacity?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/region/${region_id}`, data);
};

/**
 * 删除检测区域
 */
export const deleteDetectionRegion = (region_id: number) => {
  return commonApi('delete', `${SNAP_PREFIX}/region/${region_id}`);
};

// ====================== 算法模型服务配置接口 ======================
export interface AlgorithmModelService {
  id: number;
  task_id?: number;
  region_id?: number;
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method: string; // GET, POST
  request_headers?: Record<string, string>;
  request_body_template?: Record<string, any>;
  timeout: number;
  is_enabled: boolean;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface RegionModelService extends AlgorithmModelService {
  region_id: number;
}

/**
 * 获取任务的算法模型服务配置列表
 */
export const getTaskAlgorithmServices = (task_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/task/${task_id}/services`);
};

/**
 * 创建任务的算法模型服务配置
 */
export const createTaskAlgorithmService = (task_id: number, data: {
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: Record<string, string>;
  request_body_template?: Record<string, any>;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('post', `${SNAP_PREFIX}/task/${task_id}/service`, data);
};

/**
 * 更新任务的算法模型服务配置
 */
export const updateTaskAlgorithmService = (service_id: number, data: {
  service_name?: string;
  service_url?: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: Record<string, string>;
  request_body_template?: Record<string, any>;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/service/${service_id}`, data);
};

/**
 * 删除任务的算法模型服务配置
 */
export const deleteTaskAlgorithmService = (service_id: number) => {
  return commonApi('delete', `${SNAP_PREFIX}/service/${service_id}`);
};

/**
 * 获取区域的算法模型服务配置列表
 */
export const getRegionAlgorithmServices = (region_id: number) => {
  return commonApi('get', `${SNAP_PREFIX}/region/${region_id}/services`);
};

/**
 * 创建区域的算法模型服务配置
 */
export const createRegionAlgorithmService = (region_id: number, data: {
  service_name: string;
  service_url: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: Record<string, string>;
  request_body_template?: Record<string, any>;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('post', `${SNAP_PREFIX}/region/${region_id}/service`, data);
};

/**
 * 更新区域的算法模型服务配置
 */
export const updateRegionAlgorithmService = (service_id: number, data: {
  service_name?: string;
  service_url?: string;
  service_type?: string;
  model_id?: number;
  threshold?: number;
  request_method?: string;
  request_headers?: Record<string, string>;
  request_body_template?: Record<string, any>;
  timeout?: number;
  is_enabled?: boolean;
  sort_order?: number;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/region-service/${service_id}`, data);
};

/**
 * 删除区域的算法模型服务配置
 */
export const deleteRegionAlgorithmService = (service_id: number) => {
  return commonApi('delete', `${SNAP_PREFIX}/region-service/${service_id}`);
};

// ====================== 设备存储配置接口 ======================
export interface DeviceStorageConfig {
  id: number;
  device_id: string;
  snap_storage_bucket?: string;
  snap_storage_max_size?: number;
  snap_storage_cleanup_enabled: boolean;
  snap_storage_cleanup_threshold: number;
  snap_storage_cleanup_ratio: number;
  video_storage_bucket?: string;
  video_storage_max_size?: number;
  video_storage_cleanup_enabled: boolean;
  video_storage_cleanup_threshold: number;
  video_storage_cleanup_ratio: number;
  last_snap_cleanup_time?: string;
  last_video_cleanup_time?: string;
  // 存储信息
  snap_size?: number;
  snap_count?: number;
  snap_usage_ratio?: number;
  video_size?: number;
  video_count?: number;
  video_usage_ratio?: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * 获取设备存储配置和信息
 */
export const getDeviceStorageConfig = (device_id: string) => {
  return commonApi('get', `${SNAP_PREFIX}/device/${device_id}/storage`);
};

/**
 * 更新设备存储配置
 */
export const updateDeviceStorageConfig = (device_id: string, data: {
  snap_storage_bucket?: string;
  snap_storage_max_size?: number;
  snap_storage_cleanup_enabled?: boolean;
  snap_storage_cleanup_threshold?: number;
  snap_storage_cleanup_ratio?: number;
  video_storage_bucket?: string;
  video_storage_max_size?: number;
  video_storage_cleanup_enabled?: boolean;
  video_storage_cleanup_threshold?: number;
  video_storage_cleanup_ratio?: number;
}) => {
  return commonApi('put', `${SNAP_PREFIX}/device/${device_id}/storage`, data);
};

/**
 * 手动触发设备存储清理
 */
export const cleanupDeviceStorage = (device_id: string) => {
  return commonApi('post', `${SNAP_PREFIX}/device/${device_id}/storage/cleanup`);
};

// ====================== 抓拍图片管理接口 ======================
export interface SnapImage {
  object_name: string;
  filename: string;
  size: number;
  last_modified: string;
  etag: string;
  content_type: string;
  url: string;
}

export interface SnapImageListResponse {
  code: number;
  msg: string;
  data: SnapImage[];
  total: number;
}

/**
 * 获取抓拍空间图片列表
 */
export const getSnapImageList = (space_id: number, params: {
  device_id?: string;
  pageNo?: number;
  pageSize?: number;
}) => {
  return commonApi('get', `${SNAP_PREFIX}/space/${space_id}/images`, params);
};

/**
 * 批量删除抓拍图片
 */
export const deleteSnapImages = (space_id: number, object_names: string[]) => {
  return commonApi('delete', `${SNAP_PREFIX}/space/${space_id}/images`, { object_names });
};

/**
 * 清理过期的抓拍图片
 */
export const cleanupSnapImages = (space_id: number, days: number) => {
  return commonApi('post', `${SNAP_PREFIX}/space/${space_id}/images/cleanup`, { days });
};

