import {defHttp} from '@/utils/http/axios';

const CAMERA_PREFIX = '/video/camera';
const NVR_PREFIX = '/video/nvr';

// 通用请求封装
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params } : { data: params })
  }, { isTransformResponse: true });
};

// ====================== 流媒体转发接口 ======================
/**
 * 启动FFmpeg转发RTSP流到RTMP服务器
 * @param device_id 设备ID
 * @returns 包含RTMP URL和进程ID的响应
 */
export const startStreamForwarding = (device_id: string) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/stream/start`);
};

/**
 * 停止FFmpeg转发进程
 * @param device_id 设备ID
 * @returns 操作结果
 */
export const stopStreamForwarding = (device_id: string) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/stream/stop`);
};

/**
 * 获取FFmpeg转发状态
 * @param device_id 设备ID
 * @returns 包含状态、RTMP URL和进程信息的响应
 */
export const getStreamStatus = (device_id: string) => {
  return commonApi('get', `${CAMERA_PREFIX}/device/${device_id}/stream/status`);
};

/**
 * 批量获取设备流媒体转发状态
 * @param device_ids 设备ID数组
 * @returns 包含所有设备流媒体状态的响应
 */
export const getBatchStreamStatus = (device_ids: string[]) => {
  return Promise.all(device_ids.map(id => getStreamStatus(id)));
};

// ====================== 设备管理接口 ======================
export const registerDevice = (data: {
  id?: string;
  name: string;
  ip: string;
  port: number;
  username: string;
  password: string;
  stream?: number;
  nvr_id?: string;
  nvr_channel?: number;
  enable_forward?: boolean;
  rtmp_stream?: string;
  http_stream?: string;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/register/device`, data);
};

export const getDeviceInfo = (device_id: string) => {
  return commonApi('get', `${CAMERA_PREFIX}/device/${device_id}`);
};

export const updateDevice = (device_id: string, data: {
  name?: string;
  ip?: string;
  port?: number;
  username?: string;
  password?: string;
  stream?: number;
  nvr_id?: string;
  nvr_channel?: number;
  enable_forward?: boolean;
  rtmp_stream?: string;
  http_stream?: string;
}) => {
  return commonApi('put', `${CAMERA_PREFIX}/device/${device_id}`, data);
};

export const deleteDevice = (device_id: string) => {
  return commonApi('delete', `${CAMERA_PREFIX}/device/${device_id}`);
};

export const getDeviceList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
  nvr_id?: string;
  enable_forward?: boolean;
}) => {
  return commonApi('get', `${CAMERA_PREFIX}/list`, params);
};

export const getDeviceStatus = () => {
  return commonApi('get', `${CAMERA_PREFIX}/device/status`);
};

// ====================== PTZ控制接口 ======================
export const controlPTZ = (device_id: string, data: {
  x: number;
  y: number;
  z: number;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/ptz`, data);
};

// ====================== 截图任务接口 ======================
export const startRtspCapture = (device_id: number, data: {
  rtsp_url?: string;
  interval?: number;
  max_count?: number;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/rtsp/start`, data);
};

export const stopRtspCapture = (device_id: number) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/rtsp/stop`);
};

export const getRtspStatus = (device_id: number) => {
  return commonApi('get', `${CAMERA_PREFIX}/device/${device_id}/rtsp/status`);
};

export const startOnvifCapture = (device_id: number, data: {
  interval?: number;
  max_count?: number;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/onvif/start`, data);
};

export const stopOnvifCapture = (device_id: number) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/onvif/stop`);
};

export const getOnvifStatus = (device_id: number) => {
  return commonApi('get', `${CAMERA_PREFIX}/device/${device_id}/onvif/status`);
};

export const getOnvifProfiles = (device_ip: string, device_port: number, auth: {
  username: string;
  password: string;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/onvif/${device_ip}/${device_port}/profiles`, auth);
};

// ====================== 设备发现接口 ======================
export const discoverDevices = () => {
  return commonApi('get', `${CAMERA_PREFIX}/discovery`);
};

export const refreshDevices = () => {
  return commonApi('post', `${CAMERA_PREFIX}/refresh`);
};

// ====================== MinIO上传接口 ======================
export const uploadScreenshot = (formData: FormData) => {
  return defHttp.post({
    url: `${CAMERA_PREFIX}/upload`,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
    }
  });
};

// ====================== NVR管理接口 ======================
export const registerNVR = (data: {
  name: string;
  ip: string;
  port: number;
  username?: string;
  password?: string;
}) => {
  return commonApi('post', `${NVR_PREFIX}/register`, data);
};

export const getNVRInfo = (nvr_id: number) => {
  return commonApi('get', `${NVR_PREFIX}/info/${nvr_id}`);
};

export const deleteNVR = (nvr_id: number) => {
  return commonApi('delete', `${NVR_PREFIX}/delete/${nvr_id}`);
};

export const addNvrCamera = (nvr_id: number, data: {
  name: string;
  channel: number;
  model?: string;
  stream_type?: string;
}) => {
  return commonApi('post', `${NVR_PREFIX}/create/${nvr_id}/camera`, data);
};

// ====================== 类型定义 ======================
export interface StreamStatusResponse {
  code: number;
  msg: string;
  data: {
    status: 'running' | 'stopped';
    rtmp_url: string | null;
    enable_forward: boolean;
    pid?: number;
    start_time?: string;
  };
}

export interface StartStreamResponse {
  code: number;
  msg: string;
  data: {
    rtmp_url: string;
    process_id: number;
  };
}

export interface DeviceInfo {
  id: string;
  name: string;
  source: string;
  rtmp_stream: string;
  http_stream: string;
  stream: number;
  ip: string;
  port: number;
  username: string;
  password: string;
  mac: string;
  manufacturer: string;
  model: string;
  firmware_version: string;
  serial_number: string;
  hardware_id: string;
  support_move: boolean;
  support_zoom: boolean;
  nvr_id: number | null;
  nvr_channel: number;
  enable_forward: boolean;
  created_at: string;
  updated_at: string;
}

export interface DeviceListResponse {
  code: number;
  msg: string;
  data: DeviceInfo[];
  total: number;
}

// ====================== 流媒体管理工具函数 ======================
/**
 * 切换设备流媒体转发状态
 * @param device_id 设备ID
 * @param currentStatus 当前状态
 * @returns 操作结果
 */
export const toggleStreamForwarding = async (device_id: string, currentStatus: boolean) => {
  try {
    if (currentStatus) {
      return await stopStreamForwarding(device_id);
    } else {
      return await startStreamForwarding(device_id);
    }
  } catch (error) {
    throw new Error(`切换流媒体转发状态失败: ${error}`);
  }
};

/**
 * 检查所有设备的流媒体状态
 * @param deviceIds 设备ID数组
 * @returns 包含所有设备状态的Promise
 */
export const checkAllStreamStatus = async (deviceIds: string[]) => {
  const statusPromises = deviceIds.map(id => getStreamStatus(id));
  return Promise.all(statusPromises);
};

/**
 * 启动所有启用转发的设备
 * @param devices 设备列表
 * @returns 启动结果数组
 */
export const startAllEnabledDevices = async (devices: DeviceInfo[]) => {
  const enabledDevices = devices.filter(device => device.enable_forward);
  const startPromises = enabledDevices.map(device => startStreamForwarding(device.id));
  return Promise.all(startPromises);
};

/**
 * 停止所有设备的流媒体转发
 * @param deviceIds 设备ID数组
 * @returns 停止结果数组
 */
export const stopAllStreams = async (deviceIds: string[]) => {
  const stopPromises = deviceIds.map(id => stopStreamForwarding(id));
  return Promise.all(stopPromises);
};
