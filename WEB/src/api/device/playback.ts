import {defHttp} from '@/utils/http/axios';

const PLAYBACK_PREFIX = '/video/playback';

// 通用请求封装
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params } : { data: params })
  }, { isTransformResponse: isTransformResponse });
};

// ====================== 录像回放管理接口 ======================

/**
 * 获取录像回放列表
 * @param params 查询参数
 */
export const getPlaybackList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  device_id?: string;
  start_time?: string;
  end_time?: string;
}) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/list`, params);
};

/**
 * 获取单个录像回放详情
 * @param playback_id 录像回放ID
 */
export const getPlaybackInfo = (playback_id: number) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/${playback_id}`);
};

/**
 * 创建录像回放记录
 * @param data 录像回放数据
 */
export const createPlayback = (data: {
  file_path: string;
  event_time: string;
  device_id: string;
  device_name: string;
  duration: number;
  thumbnail_path?: string;
  file_size?: number;
}) => {
  return commonApi('post', `${PLAYBACK_PREFIX}/`, data);
};

/**
 * 更新录像回放记录
 * @param playback_id 录像回放ID
 * @param data 更新数据
 */
export const updatePlayback = (playback_id: number, data: {
  file_path?: string;
  event_time?: string;
  device_id?: string;
  device_name?: string;
  duration?: number;
  thumbnail_path?: string;
  file_size?: number;
}) => {
  return commonApi('put', `${PLAYBACK_PREFIX}/${playback_id}`, data);
};

/**
 * 删除录像回放记录
 * @param playback_id 录像回放ID
 */
export const deletePlayback = (playback_id: number) => {
  return commonApi('delete', `${PLAYBACK_PREFIX}/${playback_id}`);
};

/**
 * 获取录像回放封面图
 * @param playback_id 录像回放ID
 */
export const getPlaybackThumbnail = (playback_id: number) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/thumbnail/${playback_id}`);
};

/**
 * 获取录像回放统计信息
 * @param params 查询参数
 */
export const getPlaybackStatistics = (params?: {
  device_id?: string;
  start_time?: string;
  end_time?: string;
}) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/statistics`, params || {});
};

// ====================== 类型定义 ======================

export interface PlaybackInfo {
  id: number;
  file_path: string;
  event_time: string;
  device_id: string;
  device_name: string;
  duration: number;
  thumbnail_path?: string;
  file_size?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PlaybackListResponse {
  code: number;
  msg: string;
  data: PlaybackInfo[];
  total: number;
}

export interface PlaybackStatistics {
  total_count: number;
  total_duration: number;
  total_size: number;
}

export interface PlaybackStatisticsResponse {
  code: number;
  msg: string;
  data: PlaybackStatistics;
}

