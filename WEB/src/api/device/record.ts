import {defHttp} from '@/utils/http/axios';

const RECORD_PREFIX = '/video/record';

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
  save_time: number; // 0:永久保存, >=7(单位:天)
  description?: string;
  device_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RecordSpaceListResponse {
  code: number;
  msg: string;
  data: RecordSpace[];
  total: number;
}

/**
 * 获取监控录像空间列表
 */
export const getRecordSpaceList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi('get', `${RECORD_PREFIX}/space/list`, params);
};

/**
 * 获取监控录像空间详情
 */
export const getRecordSpace = (space_id: number) => {
  return commonApi('get', `${RECORD_PREFIX}/space/${space_id}`);
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
  description?: string;
}) => {
  return commonApi('put', `${RECORD_PREFIX}/space/${space_id}`, data);
};

/**
 * 删除监控录像空间
 */
export const deleteRecordSpace = (space_id: number) => {
  return commonApi('delete', `${RECORD_PREFIX}/space/${space_id}`);
};

// ====================== 监控录像管理接口 ======================
export interface RecordVideo {
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
 */
export const cleanupRecordVideos = (space_id: number, days: number) => {
  return commonApi('post', `${RECORD_PREFIX}/space/${space_id}/videos/cleanup`, { days });
};

