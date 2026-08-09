import {defHttp} from '@/utils/http/axios';
import { computeSegmentScanHttpTimeoutMs } from '@/views/camera/utils/segmentScanTargetsValidate';

const CAMERA_PREFIX = '/video/camera';

// 通用请求封装
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params = {}, headers = {}, isTransformResponse = true) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method]({
    url,
    headers: { ...headers },
    ...(method === 'get' ? { params } : { data: params })
  }, { isTransformResponse: isTransformResponse });
};

// ====================== 流地址 secure_link 签名票据 ======================
export interface StreamTicketResp {
  /** 过期 unix 秒 */
  e: number;
  /** url-safe base64 的 md5 签名 */
  st: string;
}

/**
 * 为受保护的流路径（/ai /live /rtp）签发短期 secure_link 票据。
 * 需登录；未登录/会话过期返回 401，由 axios 拦截器统一跳登录。
 * @param path 流地址的 pathname，例如 /rtp/xxx.live.flv
 * @param ttl  有效期（秒），默认 90
 */
export const signStreamTicket = (path: string, ttl = 90): Promise<StreamTicketResp> => {
  return commonApi('post', `${CAMERA_PREFIX}/stream/ticket/sign`, { path, ttl }) as Promise<StreamTicketResp>;
};

// ====================== 流媒体转发接口 ======================
/**
 * 启动FFmpeg转发RTSP流到RTMP服务器
 * @param device_id 设备ID
 * @param silent 为 true 时不弹出全局错误提示（推理/预览场景）
 */
export const startStreamForwarding = (device_id: string, silent = false) => {
  return defHttp.post({
    url: `${CAMERA_PREFIX}/device/${device_id}/stream/start`,
    data: {},
    headers: { 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') },
  }, {
    isTransformResponse: false,
    errorMessageMode: silent ? 'none' : 'message',
  });
};

/**
 * 停止FFmpeg转发进程
 * @param device_id 设备ID
 * @returns 操作结果
 */
export const stopStreamForwarding = (device_id: string) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/stream/stop`, {}, {}, false);
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
export interface NvrInfo {
  id?: number;
  ip: string;
  port?: number;
  scheme?: string;
  web_url?: string;
  username?: string;
  password?: string;
  /** 库中是否已保存 Web 登录密码（详情接口不回传明文） */
  has_password?: boolean;
  name?: string;
  device_name?: string;
  model?: string;
  vendor?: string;
  vendor_label?: string;
  serial_number?: string;
  serial?: string;
  firmware_version?: string;
  firmware?: string;
  device_type?: string;
  mac?: string;
  rtsp_url?: string;
  source?: string;
  rtsp_template?: string;
  rtsp_port?: number;
  camera_count?: number;
  cameras?: Array<{
    id: string;
    name?: string;
    ip?: string;
    port?: number;
    nvr_channel?: number;
    source?: string;
    rtsp_url?: string;
    rtmp_stream?: string;
    http_stream?: string;
    ai_rtmp_stream?: string;
    ai_http_stream?: string;
    rtsp_direct?: string;
    model?: string;
    serial?: string;
    online?: boolean;
    online_text?: string;
    connection_status?: string;
  }>;
}

export const registerDevice = (data: {
  id?: string;
  name: string;
  ip?: string;
  port?: number;
  username?: string;
  password?: string;
  skylink_token?: string;
  source?: string;
  cameraType?: string;
  stream?: number;
  enable_forward?: boolean;
  rtmp_stream?: string;
  http_stream?: string;
  ai_rtmp_stream?: string;
  ai_http_stream?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  hardware_id?: string;
  firmware_version?: string;
  nvr_id?: number | null;
  nvr_channel?: number;
  nvr?: NvrInfo;
  nvr_ip?: string;
  nvr_port?: number;
  nvr_name?: string;
  nvr_vendor?: string;
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/register/device`, data);
};

export interface FlighthubConfig {
  allowed_ips: string[];
  workspace_id: string;
  workspace_name: string;
  platform_name: string;
  platform_host: string;
  openapi_host?: string;
  live_start_path?: string;
  mqtt_enabled: boolean;
  mqtt_broker_uri: string;
  mqtt_client_id: string;
  mqtt_username: string;
}

export const getFlighthubConfig = (): Promise<FlighthubConfig> => {
  return commonApi('get', `${CAMERA_PREFIX}/flighthub/config`) as Promise<FlighthubConfig>;
};

/** 大疆机场 / 无人机共用司空 OpenAPI，仅 device_type 元数据不同 */
export interface DjiLiveRegisterPayload {
  name: string;
  source: string;
  device_type: 'dock' | 'drone';
  serial_number?: string;
  dock_sn?: string;
  drone_sn?: string;
  workspace_id?: string;
  workspace_name?: string;
  platform_name?: string;
  platform_host?: string;
  enable_forward?: boolean;
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
}

export const registerDjiLiveDevice = (data: DjiLiveRegisterPayload) => {
  return commonApi('post', `${CAMERA_PREFIX}/register/device/dji-live`, data);
};

export interface DjiSkylinkStartPayload extends Omit<DjiLiveRegisterPayload, 'source'> {
  user_token: string;
  project_uuid: string;
  api_host: string;
  api_path?: string;
  sn: string;
  camera_index: string;
  video_expire: number;
  quality_type: 'adaptive' | 'smooth' | 'ultra_high_definition';
}

export const startDjiSkylinkLive = (data: DjiSkylinkStartPayload) => {
  return commonApi('post', `${CAMERA_PREFIX}/flighthub/live-stream/start`, data, {}, false);
};

export const refreshDjiSkylinkLiveByDevice = (deviceId: string, data?: Partial<DjiSkylinkStartPayload>) => {
  return commonApi('post', `${CAMERA_PREFIX}/flighthub/live-stream/refresh-device/${deviceId}`, data || {}, {}, false);
};

export const getNvrList = (includeCameras = false) => {
  return commonApi('get', `${CAMERA_PREFIX}/nvr/list`, {
    include_cameras: includeCameras ? 'true' : 'false',
  });
};

export const getNvrDetail = (nvrId: number, includeCameras = true) => {
  return commonApi('get', `${CAMERA_PREFIX}/nvr/${nvrId}`, {
    include_cameras: includeCameras ? 'true' : 'false',
  });
};

export const upsertNvr = (data: NvrInfo) => {
  return commonApi('post', `${CAMERA_PREFIX}/nvr/upsert`, data);
};

export interface NvrRegisterChannelsResult extends NvrInfo {
  msg?: string;
  stats?: {
    registered?: number;
    skipped?: number;
    pruned?: number;
    errors?: string[];
  };
}

/** 登记 NVR 并批量挂载通道；未传 channels 时由服务端枚举 */
export const registerNvrWithChannels = (data: {
  ip: string;
  port?: number;
  username?: string;
  password?: string;
  credentials?: CredentialPair[];
  timeout?: number;
  vendor?: string;
  name?: string;
  model?: string;
  serial_number?: string;
  rtsp_url?: string;
  scheme?: string;
  channels?: NvrChannelRow[];
  rtsp_template?: string;
  rtsp_port?: number;
  channel_count?: number;
}): Promise<NvrRegisterChannelsResult> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp
    .post(
      {
        url: `${CAMERA_PREFIX}/nvr/register-channels`,
        data,
        timeout: 300 * 1000,
      },
      { isTransformResponse: false, errorMessageMode: 'none' },
    )
    .then((res: { data?: { code?: number; msg?: string; data?: NvrInfo; stats?: NvrRegisterChannelsResult['stats'] } }) => {
      const body = res?.data ?? {};
      const code = body.code;
      if (code !== 0 && code !== 200) {
        throw { msg: body.msg || 'NVR 登记失败' };
      }
      return {
        ...(body.data || {}),
        msg: body.msg,
        stats: body.stats,
      } as NvrRegisterChannelsResult;
    });
};

export const deleteNvr = (nvrId: number) => {
  return commonApi('delete', `${CAMERA_PREFIX}/nvr/${nvrId}`);
};

export const batchDeleteNvrs = (nvrIds: number[]) => {
  return commonApi('post', `${CAMERA_PREFIX}/nvr/batch-delete`, {
    nvr_ids: nvrIds,
  });
};

/**
 * 通过ONVIF搜索并自动注册摄像头
 * @param data 包含IP、端口、密码的对象
 * @returns 注册结果
 */
export const registerDeviceByOnvif = (data: {
  ip: string;
  port: number;
  username?: string;
  password: string;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/register/device/onvif`, data);
};

function cameraDevicePath(device_id: string) {
  return `${CAMERA_PREFIX}/device/${encodeURIComponent(device_id)}`;
}

export const getDeviceInfo = (device_id: string, params?: { name?: string }) => {
  return commonApi('get', cameraDevicePath(device_id), params || {});
};

/** 确保设备已有关联的抓拍空间与录像空间（缺失则自动创建） */
export const ensureDeviceSpaces = (device_id: string) => {
  return commonApi('post', `${cameraDevicePath(device_id)}/ensure-spaces`, {}, {}, false);
};

/** 获取设备坐标（地图选点弹窗；国标虚拟通道不存在时后端按需入库） */
export const getDeviceLocation = (device_id: string, params?: { name?: string }) => {
  return commonApi('get', `${cameraDevicePath(device_id)}/location`, params || {}, {}, false);
};

export const updateDevice = (device_id: string, data: {
  name?: string;
  ip?: string;
  port?: number;
  username?: string;
  password?: string;
  source?: string;
  cameraType?: string;
  stream?: number;
  enable_forward?: boolean;
  rtmp_stream?: string;
  http_stream?: string;
  ai_rtmp_stream?: string;
  ai_http_stream?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  hardware_id?: string;
  nvr_id?: number | null;
  nvr_channel?: number;
  nvr?: NvrInfo;
  nvr_ip?: string;
  nvr_port?: number;
  nvr_name?: string;
  nvr_vendor?: string;
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
  heading?: number | null;
}) => {
  return commonApi('put', `${CAMERA_PREFIX}/device/${device_id}`, data);
};

export interface DeviceLocationInfo {
  id: string;
  name: string;
  source: string;
  directory_id?: number | null;
  online?: boolean;
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
  heading?: number | null;
  location_source?: string | null;
  location_updated_at?: string | null;
  has_location?: boolean;
  device_kind?: string;
  /** 是否支持云台转动(PTZ)，用于地图区分球机/枪机 */
  support_move?: boolean | null;
  /** 是否支持变倍(zoom) */
  support_zoom?: boolean | null;
  /** GB28181 摄像机结构: 1球机 2半球 3固定枪机 4遥控枪机 5遥控半球 6/7多目 */
  ptz_type?: number | null;
  /** GB28181 监视方位(光轴): 1东2西3南4北5东南6东北7西南8西北 */
  direction_type?: number | null;
  /** GB28181 位置类型: 1检查站2党政3车站4广场5体育场馆6商业中心7宗教8校园9治安复杂10交通干线 */
  position_type?: number | null;
  /** GB28181 安装位置: 1室外 2室内 */
  room_type?: number | null;
  /** GB28181 用途: 1治安 2交通 3重点 */
  use_type?: number | null;
  /** GB28181 补光: 1无 2红外 3白光 4激光 9其他 */
  supply_light_type?: number | null;
  /** GB28181 分辨率(可多值) */
  resolution?: string | null;
}

/** 查询摄像头位置列表（地图/轨迹等场景） */
export const getDeviceLocations = (params?: {
  directory_id?: number;
  has_location?: boolean;
}) => {
  return commonApi('get', `${CAMERA_PREFIX}/locations`, {
    ...(params?.directory_id != null ? { directory_id: params.directory_id } : {}),
    ...(params?.has_location === false ? { has_location: 'false' } : {}),
  });
};

export interface BatchLocationItem {
  device_id: string;
  longitude: number;
  latitude: number;
  address?: string | null;
  altitude?: number | null;
  heading?: number | null;
}

export interface BatchLocationResult {
  updated: number;
  total: number;
  errors: Array<{ device_id?: string | null; msg: string; index?: number | null }>;
}

/** 批量更新摄像头坐标 */
export const batchUpdateDeviceLocations = (items: BatchLocationItem[]) => {
  return commonApi('post', `${CAMERA_PREFIX}/locations/batch`, { items });
};

export interface UpdateDeviceLocationPayload {
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
  heading?: number | null;
  location_source?: string | null;
  /** 国标虚拟设备首次入库时的展示名称 */
  name?: string | null;
}

/** 更新单个摄像头坐标（地图选点抽屉） */
export const updateDeviceLocation = (
  device_id: string,
  data: UpdateDeviceLocationPayload,
) => {
  return commonApi('put', `${cameraDevicePath(device_id)}/location`, data, {}, false);
};

export interface DeviceTrackSessionInfo {
  id: number;
  device_id: string;
  title?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  point_count?: number;
  distance_m?: number | null;
  source?: string;
}

export interface DeviceTrackPointInfo {
  id: number;
  device_id: string;
  session_id?: number | null;
  recorded_at: string;
  longitude: number;
  latitude: number;
  altitude?: number | null;
  speed?: number | null;
  direction?: number | null;
}

export const getDeviceTrackSessions = (params?: {
  device_id?: string;
  begin_datetime?: string;
  end_datetime?: string;
  limit?: number;
}) => {
  return commonApi('get', `${CAMERA_PREFIX}/tracks/sessions`, params);
};

export const getDeviceTrackPoints = (params: {
  session_id?: number | string;
  device_id?: string;
  begin_datetime?: string;
  end_datetime?: string;
  limit?: number;
}) => {
  return commonApi('get', `${CAMERA_PREFIX}/tracks/points`, params);
};

export const deleteDevice = (device_id: string) => {
  return commonApi('delete', `${CAMERA_PREFIX}/device/${device_id}`);
};

export const batchDeleteDevices = (deviceIds: string[]) => {
  return commonApi('post', `${CAMERA_PREFIX}/devices/batch-delete`, {
    device_ids: deviceIds,
  });
};

export const getDeviceList = (params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
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
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/ptz`, data, {}, false);
};

export interface OnvifPresetItem {
  token: string;
  name: string;
}

/** 查询 ONVIF 设备预置点列表 */
export const queryOnvifPresets = (device_id: string) =>
  commonApi('get', `${CAMERA_PREFIX}/device/${device_id}/onvif/presets`, {}, {}, false);

/** 保存 ONVIF 预置点（preset_token 可选，用于覆盖已有预置点） */
export const setOnvifPreset = (
  device_id: string,
  data: { name: string; preset_token?: string },
) => commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/onvif/presets`, data, {}, false);

/** 调用 ONVIF 预置点 */
export const callOnvifPreset = (device_id: string, preset_token: string) =>
  commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/onvif/presets/call`, { preset_token }, {}, false);

/** 删除 ONVIF 预置点 */
export const deleteOnvifPreset = (device_id: string, preset_token: string) =>
  commonApi('delete', `${CAMERA_PREFIX}/device/${device_id}/onvif/presets/${encodeURIComponent(preset_token)}`, {}, {}, false);

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
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${CAMERA_PREFIX}/discovery`,
      timeout: 120 * 1000,
    },
    { isTransformResponse: true },
  );
};

export const refreshDevices = () => {
  return commonApi('post', `${CAMERA_PREFIX}/refresh`);
};

/** Web 登录凭证（按顺序尝试，与 hiktoolno -c user:pass 一致） */
export interface CredentialPair {
  username: string;
  password?: string;
}

/** 网段扫描设备（hiktools HTTP 指纹） */
export interface SegmentScanParams {
  targets: string;
  /** @deprecated 请使用 credentials；保留兼容，取第一组 */
  username?: string;
  password?: string;
  /** 多组凭证，从上到下按顺序尝试 */
  credentials?: CredentialPair[];
  ports?: string;
  concurrency?: number;
  timeout?: number;
  only_hits?: boolean;
  /** true 时仅返回识别为 NVR 的设备 */
  nvr_only?: boolean;
  exclude_nvr?: boolean;
}

export interface SegmentScanDeviceRow {
  ip: string;
  port: number;
  ports?: number[];
  vendor?: string;
  vendor_label?: string;
  device_role?: string;
  role_label?: string;
  is_nvr?: boolean;
  is_recognized?: boolean;
  confidence?: number;
  model?: string;
  serial?: string;
  device_name?: string;
  mac?: string;
  rtsp_url?: string;
  /** 扫描时认证成功的用户名 */
  auth_username?: string;
  devices?: SegmentScanDeviceRow[];
}

export const scanSegmentDevices = (data: SegmentScanParams) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const httpTimeoutMs = computeSegmentScanHttpTimeoutMs(data);
  return defHttp.post(
    {
      url: `${CAMERA_PREFIX}/scan/segment`,
      data,
      timeout: httpTimeoutMs,
    },
    { isTransformResponse: true },
  );
};

export interface NvrChannelRow {
  channel_id: number;
  name?: string;
  camera_ip?: string;
  camera_port?: number;
  online?: boolean;
  rtsp_url?: string;
  rtsp_direct?: string;
  model?: string;
  serial?: string;
  vendor?: string;
  probe_error?: string;
  connection_status?: string;
}

export interface NvrInventoryResult {
  nvr_ip: string;
  nvr_port: number;
  nvr_vendor?: string;
  nvr_model?: string;
  nvr_serial?: string;
  nvr_device_name?: string;
  /** 枚举时认证成功的用户名 */
  auth_username?: string;
  channels: NvrChannelRow[];
  error?: string;
}

export const enumerateNvrChannels = (data: {
  ip: string;
  port: number;
  username?: string;
  password?: string;
  credentials?: CredentialPair[];
  timeout?: number;
  vendor?: string;
  /** 是否逐台探测 IPC（登记 NVR 时建议 false，仅拉 ISAPI 通道列表） */
  probe_cameras?: boolean;
}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${CAMERA_PREFIX}/scan/nvr/channels`,
      data,
      timeout: 300 * 1000,
    },
    { isTransformResponse: true },
  );
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
  ai_rtmp_stream?: string;
  ai_http_stream?: string;
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
  enable_forward: boolean;
  cover_image_path?: string;
  nvr_id?: number | null;
  nvr_channel?: number;
  nvr_label?: string | null;
  nvr?: NvrInfo | null;
  device_kind?: 'direct' | 'gb28181' | 'gb28181_sip' | 'nvr' | 'nvr_channel' | string;
  rtsp_direct?: string | null;
  channel_online?: boolean | null;
  connection_status?: string | null;
  channel_count?: number;
  longitude?: number | null;
  latitude?: number | null;
  altitude?: number | null;
  address?: string | null;
  heading?: number | null;
  location_source?: string | null;
  location_updated_at?: string | null;
  has_location?: boolean;
  created_at: string;
  updated_at: string;
}

export interface DeviceListResponse {
  code: number;
  msg: string;
  data: DeviceInfo[];
  total: number;
}

// ====================== 设备目录管理接口 ======================
export interface DeviceDirectory {
  id: number;
  name: string;
  parent_id: number | null;
  description?: string;
  sort_order: number;
  device_count?: number;
  is_default?: boolean;
  snap_save_time?: number;
  record_save_time?: number;
  children?: DeviceDirectory[];
  created_at?: string;
  updated_at?: string;
}

export interface DirectoryListResponse {
  code: number;
  msg: string;
  data: DeviceDirectory[];
}

/** 分屏监控树 - 设备节点 */
export interface MonitorTreeDeviceNode {
  type: 'device';
  id: string;
  name: string;
  http_stream?: string;
  rtmp_stream?: string;
  ai_http_stream?: string;
  ai_rtmp_stream?: string;
  online?: boolean;
  directory_id?: number | null;
  device_kind?: 'direct' | 'gb28181' | 'nvr_channel' | string;
  source?: string | null;
  nvr_id?: number | null;
  nvr_channel?: number;
  nvr_label?: string | null;
}

/** 分屏监控树 - 目录节点 */
export interface MonitorTreeDirectoryNode {
  type: 'directory';
  id: number;
  name: string;
  parent_id?: number | null;
  sort_order?: number;
  device_count?: number;
  is_default?: boolean;
  snap_save_time?: number;
  record_save_time?: number;
  children: MonitorTreeDirectoryNode[];
  devices: MonitorTreeDeviceNode[];
}

export interface DirectoryMonitorTreeData {
  tree: MonitorTreeDirectoryNode[];
  unassigned_devices: MonitorTreeDeviceNode[];
}

export interface DirectoryMonitorTreeResponse {
  code: number;
  msg: string;
  data: DirectoryMonitorTreeData;
}

export interface DirectoryInfoResponse {
  code: number;
  msg: string;
  data: {
    id: number;
    name: string;
    parent_id: number | null;
    description?: string;
    sort_order: number;
    device_count: number;
    children_count: number;
    created_at?: string;
    updated_at?: string;
  };
}

/**
 * 获取目录列表（树形结构）
 */
export const getDirectoryList = () => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    { url: `${CAMERA_PREFIX}/directory/list`, timeout: 30 * 1000 },
    { isTransformResponse: true },
  );
};

/**
 * 获取分屏监控用目录设备树（目录 + 设备，单次请求）
 * @param skipSync 为 true 时跳过服务端 WVP 全量同步（默认），加快首屏与后台刷新
 */
export const getDirectoryMonitorTree = (options?: { skipSync?: boolean }) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const skipSync = options?.skipSync !== false;
  return defHttp.get(
    {
      url: `${CAMERA_PREFIX}/directory/monitor-tree`,
      params: skipSync ? { skip_sync: 1 } : {},
      timeout: 60 * 1000,
    },
    { isTransformResponse: true, errorMessageMode: 'none' },
  );
};

export interface SyncGb28181DevicesResult {
  created: number;
  total_gb_devices: number;
}

/** 前端经 dev-api/gb28181 拉取后提交给 VIDEO 入库的通道项 */
export interface Gb28181ChannelSyncItem {
  sipDeviceId: string;
  channelId: string;
  name?: string;
}

export interface Gb28181SyncResult {
  created?: number;
  total_gb_devices?: number;
  wvp_device_count?: number;
  channels_seen?: number;
  api_base?: string;
  upsert_errors?: string[];
}

/** 解析 VIDEO 接口在 isTransformResponse:false 时的 { code, data } 信封 */
function unwrapVideoApiData<T>(res: unknown): T {
  const body = (res as { data?: unknown })?.data ?? res;
  if (body && typeof body === 'object' && body !== null && 'code' in body && 'data' in body) {
    return (body as { data: T }).data;
  }
  return body as T;
}

/**
 * 从 WVP 同步国标通道到设备目录（默认分组）。
 * 传入 channels 时由前端经 dev-api/gb28181 拉取后提交；否则由 VIDEO 直连 WVP。
 */
export const syncGb28181Devices = async (
  channels?: Gb28181ChannelSyncItem[],
): Promise<Gb28181SyncResult> => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const res = await defHttp.post(
    {
      url: `${CAMERA_PREFIX}/directory/sync-gb28181`,
      data: channels?.length ? { channels } : {},
      timeout: 120 * 1000,
    },
    { isTransformResponse: false, successMessageMode: 'none' },
  );
  return unwrapVideoApiData<Gb28181SyncResult>(res);
};

/** 校验设备目录 JSON（摄像头不可重复等） */
export const validateDirectoryJson = (tree: unknown[]) => {
  return commonApi('post', `${CAMERA_PREFIX}/directory/validate-json`, { tree }, {}, false);
};

/** 按 JSON 同步设备目录（服务端校验并写入） */
export const syncDirectoryFromJson = (tree: unknown[]) => {
  return commonApi('post', `${CAMERA_PREFIX}/directory/sync-json`, { tree }, {}, false);
};

/**
 * 获取目录详情
 * @param directory_id 目录ID
 */
export const getDirectoryInfo = (directory_id: number) => {
  return commonApi('get', `${CAMERA_PREFIX}/directory/${directory_id}`);
};

/**
 * 创建目录
 * @param data 目录信息
 */
export const createDirectory = (data: {
  name: string;
  parent_id?: number | null;
  description?: string;
  sort_order?: number;
}) => {
  return commonApi('post', `${CAMERA_PREFIX}/directory`, data);
};

/**
 * 更新目录
 * @param directory_id 目录ID
 * @param data 目录信息
 */
export const updateDirectory = (directory_id: number, data: {
  name?: string;
  parent_id?: number | null;
  description?: string;
  sort_order?: number;
  snap_save_time?: number;
  record_save_time?: number;
}) => {
  return commonApi('put', `${CAMERA_PREFIX}/directory/${directory_id}`, data);
};

/**
 * 删除目录
 * @param directory_id 目录ID
 */
export const deleteDirectory = (directory_id: number) => {
  return commonApi('delete', `${CAMERA_PREFIX}/directory/${directory_id}`);
};

/**
 * 获取目录下的设备列表
 * @param directory_id 目录ID
 * @param params 查询参数
 */
export const getDirectoryDevices = (directory_id: number, params: {
  pageNo?: number;
  pageSize?: number;
  search?: string;
}) => {
  return commonApi('get', `${CAMERA_PREFIX}/directory/${directory_id}/devices`, params);
};

/**
 * 移动设备到目录
 * @param device_id 设备ID
 * @param directory_id 目录ID（0表示移动到根目录，即无目录）
 */
export const moveDeviceToDirectory = (device_id: string, directory_id: number | null) => {
  return commonApi('put', `${CAMERA_PREFIX}/device/${device_id}/directory`, {
    directory_id: directory_id === 0 ? null : directory_id
  });
};

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

// ====================== RTSP抓拍接口 ======================
/**
 * 从RTSP流抓取一帧图片
 * @param device_id 设备ID
 * @returns 包含图片ID和URL的响应
 */
export const captureSnapshot = (device_id: string) => {
  return commonApi('post', `${CAMERA_PREFIX}/device/${device_id}/snapshot`, {}, {}, false);
};

// ====================== 摄像头冲突检查接口 ======================
/**
 * 获取正在使用的摄像头ID列表（用于推流转发或算法任务）
 * @param task_type 任务类型：'stream_forward'（推流转发）或 'algorithm'（算法任务），不传则返回所有冲突的摄像头
 * @returns 包含冲突摄像头ID列表的响应
 */
export const getDeviceConflicts = (task_type?: 'stream_forward' | 'algorithm') => {
  return commonApi<{ code: number; msg: string; data: string[] }>(
    'get',
    `${CAMERA_PREFIX}/device/conflicts`,
    task_type ? { task_type } : {}
  );
};
