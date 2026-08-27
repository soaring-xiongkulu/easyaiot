import {defHttp} from '@/utils/http/axios';

const RECORD_PREFIX = '/video/record';

function assertValidSpaceId(space_id: number, label = 'space_id'): void {
  if (!Number.isFinite(space_id) || space_id <= 0) {
    throw new Error(`invalid ${label}`);
  }
}

// 通用请求封装
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params } : { data: params })
  }, { isTransformResponse: isTransformResponse });
};

// ====================== 监控录像空间管理接口 ======================
export interface RecordSpace {
  id: number;
  space_name: string;
  space_code: string;
  bucket_name: string;
  save_mode: number; // 0:标准存储, 1:归档存储
  save_time: number; // 0:永久保存, >=1(单位:小时)
  save_time_custom?: boolean;
  directory_save_time?: number;
  directory_id?: number;
  effective_save_time?: number;
  group_save_time?: number;
  group_type?: 'nvr' | 'gb28181';
  group_key?: string;
  description?: string;
  device_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SpaceBreadcrumbItem {
  key: string;
  name: string;
}

export interface RecordSpaceListResponse {
  code: number;
  msg: string;
  data: RecordSpace[];
  total: number;
  parent_key?: string;
  breadcrumbs?: SpaceBreadcrumbItem[];
  is_search?: boolean;
}

/**
 * 获取监控录像空间列表
 */
export const getRecordSpaceList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  parentKey?: string;
  scope?: 'leaves';
}) => {
  return commonApi('get', `${RECORD_PREFIX}/space/list`, params);
};

/**
 * 获取监控录像空间详情
 */
export const getRecordSpace = (space_id: number) => {
  assertValidSpaceId(space_id);
  return commonApi('get', `${RECORD_PREFIX}/space/${space_id}`);
};

/**
 * 根据设备 ID 获取监控录像空间
 */
export const getRecordSpaceByDeviceId = (device_id: string) => {
  return commonApi('get', `${RECORD_PREFIX}/space/device/${device_id}`);
};

/**
 * 根据告警 ID 定位录像片段
 */
export const resolveAlertRecordSegment = (device_id: string, alert_id: number | string) => {
  return commonApi('get', `${RECORD_PREFIX}/space/device/${device_id}/resolve-alert`, { alert_id });
};

/**
 * 创建监控录像空间
 */
export const createRecordSpace = (data: {
  space_name: string;
  save_mode?: number;
  save_time?: number;
  description?: string;
}) => {
  return commonApi('post', `${RECORD_PREFIX}/space`, data);
};

/**
 * 更新监控录像空间
 */
export const updateRecordSpace = (space_id: number, data: {
  space_name?: string;
  save_mode?: number;
  save_time?: number;
  save_time_custom?: boolean;
  description?: string;
}) => {
  return commonApi('put', `${RECORD_PREFIX}/space/${space_id}`, data);
};

/**
 * 更新 NVR / GB28181 分组默认录像保存时间
 */
export const updateRecordSpaceGroupPolicy = (data: {
  group_type: 'nvr' | 'gb28181';
  group_key: string;
  save_time: number;
}) => {
  return commonApi('put', `${RECORD_PREFIX}/space/group-policy`, data);
};

export interface DeviceRecordingPolicy {
  device_id: string;
  recording_mode: 'continuous' | 'event_only' | 'off';
  retention_hours: number;
  event_pre_seconds: number;
  event_post_seconds: number;
  event_image_sync: boolean;
  event_clip_sync: boolean;
  live_transport_mode: 'always_push';
  playback_route_mode: 'auto' | 'direct' | 'proxy';
  effective_storage?: {
    mode: 'central_shared' | 'edge_local' | 'unknown';
    state: string;
    generation?: number;
    node_id?: number;
  };
}

export const getDeviceRecordingPolicy = (deviceId: string) => {
  return commonApi('get', `/video/recording/policies/${encodeURIComponent(deviceId)}`);
};

export const updateDeviceRecordingPolicy = (
  deviceId: string,
  data: Partial<DeviceRecordingPolicy>,
) => {
  return commonApi('put', `/video/recording/policies/${encodeURIComponent(deviceId)}`, data);
};

/**
 * 删除监控录像空间
 */
export const deleteRecordSpace = (space_id: number) => {
  return commonApi('delete', `${RECORD_PREFIX}/space/${space_id}`);
};

// ====================== 监控录像管理接口 ======================
export interface RecordVideo {
  id?: number;
  object_name: string;
  filename: string;
  size: number;
  duration?: number; // 时长（秒）
  last_modified: string;
  etag: string;
  content_type: string;
  url: string;
  thumbnail_url?: string; // 缩略图URL
}

export interface RecordVideoListResponse {
  code: number;
  msg: string;
  data: RecordVideo[];
  total: number;
}

/**
 * 获取监控录像空间录像列表
 */
export const getRecordVideoList = (space_id: number, params: {
  device_id?: string;
  pageNo?: number;
  pageSize?: number;
  search?: string;
  startTime?: string;
  endTime?: string;
}) => {
  return commonApi('get', `${RECORD_PREFIX}/space/${space_id}/videos`, params);
};

/**
 * 批量删除监控录像
 */
export const deleteRecordVideos = (space_id: number, object_names: string[]) => {
  return commonApi('delete', `${RECORD_PREFIX}/space/${space_id}/videos`, { object_names });
};

/**
 * 清理过期的监控录像
 * @param save_time_hours 保留时长（小时）
 */
export const cleanupRecordVideos = (space_id: number, save_time_hours: number) => {
  return commonApi('post', `${RECORD_PREFIX}/space/${space_id}/videos/cleanup`, { save_time_hours });
};

// ====================== 按日录像回放接口 ======================
export interface RecordVideoDate {
  date: string;
  segment_count: number;
}

export interface RecordDaySegment extends RecordVideo {
  start_time?: string;
  end_time?: string;
  has_alert?: boolean;
  alert_count?: number;
  alerts?: Record<string, unknown>[];
  start_offset_sec?: number;
  end_offset_sec?: number;
}

export interface RecordTimelineItem {
  start_offset_sec: number;
  end_offset_sec: number;
  has_recording: boolean;
  has_alert: boolean;
  segment_id?: number;
  segment_ids?: number[];
  alert_count?: number;
}

export interface RecordSessionGroup {
  group_id: number;
  start_time?: string;
  end_time?: string;
  start_offset_sec: number;
  end_offset_sec: number;
  segment_count: number;
  has_alert: boolean;
  alert_count: number;
  segments: RecordDaySegment[];
}

export interface RecordDayDetail {
  date: string;
  device_id?: string;
  space_id: number;
  segments: RecordDaySegment[];
  timeline: RecordTimelineItem[];
  timeline_merged?: RecordTimelineItem[];
  session_groups?: RecordSessionGroup[];
  total_segments: number;
  total_sessions?: number;
  total_duration_sec: number;
  alert_segment_count: number;
  total_alert_count: number;
  alerts: Record<string, unknown>[];
}

/**
 * 获取有录像的日期列表
 */
export const getRecordVideoDates = (space_id: number, params?: { device_id?: string }) => {
  assertValidSpaceId(space_id);
  return commonApi('get', `${RECORD_PREFIX}/space/${space_id}/videos/dates`, params || {});
};

/**
 * 获取指定日期的录像片段详情（含时间轴与告警关联）
 */
export const getRecordVideosByDay = (space_id: number, params: {
  date: string;
  device_id?: string;
}) => {
  assertValidSpaceId(space_id);
  return commonApi('get', `${RECORD_PREFIX}/space/${space_id}/videos/day`, params);
};
