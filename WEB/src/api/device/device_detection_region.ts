/**
 * 设备区域检测API
 */
import { defHttp } from '@/utils/http/axios';

const DEVICE_DETECTION_PREFIX = '/video/device-detection';

const commonApi = <T = any>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  params?: any,
  data?: any,
  isTransformResponse = true,
) => {
  return defHttp.request<T>(
    {
      url,
      method,
      params,
      data,
    },
    {
      isTransformResponse,
    },
  ) as Promise<T>;
};

// ====================== 设备区域检测接口 ======================
export interface DeviceDetectionRegion {
  id: number;
  device_id: string;
  region_name: string;
  region_type: 'polygon' | 'line'; // polygon:多边形, line:线条
  points: Array<{ x: number; y: number }>;
  image_id?: number;
  image_path?: string;
  color: string;
  opacity: number;
  is_enabled: boolean;
  sort_order: number;
  model_ids?: number[]; // 关联的算法模型ID列表
  created_at?: string;
  updated_at?: string;
}

/**
 * 获取设备的检测区域列表
 */
export const getDeviceRegions = (device_id: string) => {
  return commonApi<{ code: number; msg: string; data: DeviceDetectionRegion[] }>(
    'get',
    `${DEVICE_DETECTION_PREFIX}/device/${device_id}/regions`,
  );
};

/**
 * 创建设备检测区域
 */
export const createDeviceRegion = (device_id: string, data: {
  region_name: string;
  region_type?: 'polygon' | 'line';
  points: Array<{ x: number; y: number }>;
  image_id?: number;
  color?: string;
  opacity?: number;
  is_enabled?: boolean;
  sort_order?: number;
  model_ids?: number[];
}) => {
  return commonApi<{ code: number; msg: string; data: DeviceDetectionRegion }>(
    'post',
    `${DEVICE_DETECTION_PREFIX}/device/${device_id}/regions`,
    {},
    data,
  );
};

/**
 * 更新设备检测区域
 */
export const updateDeviceRegion = (region_id: number, data: Partial<DeviceDetectionRegion>) => {
  return commonApi<{ code: number; msg: string; data: DeviceDetectionRegion }>(
    'put',
    `${DEVICE_DETECTION_PREFIX}/region/${region_id}`,
    {},
    data,
  );
};

/**
 * 删除设备检测区域
 */
export const deleteDeviceRegion = (region_id: number) => {
  return commonApi<{ code: number; msg: string }>(
    'delete',
    `${DEVICE_DETECTION_PREFIX}/region/${region_id}`,
  );
};

/**
 * 抓拍设备截图（用于区域检测绘制）
 */
export const captureDeviceSnapshot = (device_id: string) => {
  return commonApi<{
    code: number;
    msg: string;
    data: {
      image_id: number;
      image_url: string;
      width: number;
      height: number;
    };
  }>(
    'post',
    `${DEVICE_DETECTION_PREFIX}/device/${device_id}/snapshot`,
    {},
    {},
    false,
  );
};

/**
 * 抓拍并更新设备封面图
 */
export const updateDeviceCoverImage = (device_id: string) => {
  return commonApi<{
    code: number;
    msg: string;
    data: {
      cover_image_path: string;
      image_url: string;
      image_id?: number;
      width?: number;
      height?: number;
    };
  }>(
    'post',
    `${DEVICE_DETECTION_PREFIX}/device/${device_id}/cover-image`,
    {},
    {},
    false,
  );
};

