/**
 * 设备区域检测API
 */
import { defHttp } from '@/utils/http/axios';

const DEVICE_DETECTION_PREFIX = '/video/device-detection';

type RegionRequestOptions = {
  isTransformResponse?: boolean;
  errorMessageMode?: 'none' | 'message' | 'modal';
  disableRetry?: boolean;
};

const SILENT_REQUEST_OPTIONS: RegionRequestOptions = {
  errorMessageMode: 'none',
  disableRetry: true,
};

const commonApi = <T = any>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  params?: any,
  data?: any,
  options: boolean | RegionRequestOptions = true,
) => {
  const resolved: RegionRequestOptions =
    typeof options === 'boolean' ? { isTransformResponse: options } : options;
  return defHttp.request<T>(
    {
      url,
      method,
      params,
      data,
    },
    {
      isTransformResponse: resolved.isTransformResponse ?? true,
      errorMessageMode: resolved.errorMessageMode,
      ...(resolved.disableRetry
        ? { retryRequest: { isOpenRetry: false, count: 0, waitTime: 0 } }
        : {}),
    },
  ) as Promise<T>;
};

function parseDeviceRegionsResponse(response: unknown): DeviceDetectionRegion[] {
  if (Array.isArray(response)) return response;
  if (response && typeof response === 'object') {
    const obj = response as Record<string, unknown>;
    if (obj.code === 0 && Array.isArray(obj.data)) {
      return obj.data as DeviceDetectionRegion[];
    }
    if (Array.isArray(obj.data)) {
      return obj.data as DeviceDetectionRegion[];
    }
  }
  return [];
}

// ====================== 设备区域检测接口 ======================
export interface DeviceDetectionRegion {
  id: number;
  task_id?: number;
  device_id: string;
  region_name: string;
  region_type: 'polygon' | 'line' | 'rectangle'; // polygon:多边形, line:线条, rectangle:四边形
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
 * 获取指定任务下设备的检测区域列表
 */
export const getDeviceRegions = (device_id: string, task_id: number) => {
  return commonApi<{ code: number; msg: string; data: DeviceDetectionRegion[] }>(
    'get',
    `${DEVICE_DETECTION_PREFIX}/task/${task_id}/device/${device_id}/regions`,
    undefined,
    undefined,
    SILENT_REQUEST_OPTIONS,
  );
};

/**
 * 获取设备区域；404 视为尚未配置（空列表），不弹全局错误、不重试
 */
export async function listDeviceRegionsSafe(
  device_id: string,
  task_id: number,
): Promise<DeviceDetectionRegion[]> {
  try {
    const response = await getDeviceRegions(device_id, task_id);
    return parseDeviceRegionsResponse(response);
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (status === 404) return [];
    throw error;
  }
}

/**
 * 在指定任务下创建设备检测区域
 */
export const createDeviceRegion = (device_id: string, task_id: number, data: {
  region_name: string;
  region_type?: 'polygon' | 'line' | 'rectangle';
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
    `${DEVICE_DETECTION_PREFIX}/task/${task_id}/device/${device_id}/regions`,
    {},
    data,
    SILENT_REQUEST_OPTIONS,
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
    SILENT_REQUEST_OPTIONS,
  );
};

/**
 * 删除设备检测区域
 */
export const deleteDeviceRegion = (region_id: number) => {
  return commonApi<{ code: number; msg: string }>(
    'delete',
    `${DEVICE_DETECTION_PREFIX}/region/${region_id}`,
    undefined,
    undefined,
    SILENT_REQUEST_OPTIONS,
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
    { isTransformResponse: false, ...SILENT_REQUEST_OPTIONS },
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
    { isTransformResponse: false, ...SILENT_REQUEST_OPTIONS },
  );
};
