import {defHttp} from '@/utils/http/axios';

// GB28181 API 前缀
const GB28181_PREFIX = '/api/device/query';
const CHANNEL_PREFIX = '/api/common/channel';
const SERVER_PREFIX = '/api/server';
const PROXY_PREFIX = '/api/proxy';
const PLAYBACK_PREFIX = '/api/playback';
const GB_RECORD_PREFIX = '/api/gb_record';
const CLOUD_RECORD_PREFIX = '/api/cloud/record';

/**
 * 通用请求封装
 */
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url: string, params: any = {}, isTransformResponse = true) => {
  return defHttp[method](
    {
      url,
      ...(method === 'get' ? { params } : { data: params }),
    },
    {
      isTransformResponse,
    },
  );
};

// ====================== 设备管理接口 ======================

/**
 * 分页查询国标设备列表
 * @param params 查询参数
 */
export const queryVideoList = (params: {
  page?: number;
  count?: number;
  query?: string;
  status?: boolean;
}) => {
  return commonApi('get', `${GB28181_PREFIX}/devices`, params);
};

/**
 * 查询单个设备
 * @param deviceId 设备国标编号
 */
export const getDevice = (deviceId: string) => {
  return commonApi('get', `${GB28181_PREFIX}/devices/${deviceId}`);
};

/**
 * 添加设备
 * @param device 设备信息
 */
export const addDevice = (device: any) => {
  return commonApi('post', `${GB28181_PREFIX}/device/add`, device);
};

/**
 * 更新设备
 * @param device 设备信息
 */
export const updateDevice = (device: any) => {
  return commonApi('post', `${GB28181_PREFIX}/device/update`, device);
};

/**
 * 删除设备
 * @param deviceId 设备国标编号
 */
export const deleteDevice = (deviceId: string) => {
  return commonApi('delete', `${GB28181_PREFIX}/devices/${deviceId}/delete`);
};

/**
 * 同步设备通道
 * @param deviceId 设备国标编号
 */
export const refreshChannelList = (deviceId: string) => {
  return commonApi('get', `${GB28181_PREFIX}/devices/${deviceId}/sync`);
};

/**
 * 获取通道同步状态
 * @param deviceId 设备国标编号
 */
export const getSyncStatus = (deviceId: string) => {
  return commonApi('get', `${GB28181_PREFIX}/sync_status`, { deviceId });
};

// ====================== 通道管理接口 ======================

/**
 * 分页查询通道列表
 * @param params 查询参数
 */
export const queryChannelList = (params: {
  page?: number;
  count?: number;
  query?: string;
  online?: boolean;
  channelType?: number;
  deviceId?: string;
  deviceIdentification?: string;
}) => {
  if (params.deviceId || params.deviceIdentification) {
    // 查询指定设备的通道
    const deviceId = params.deviceId || params.deviceIdentification;
    return commonApi('get', `${GB28181_PREFIX}/devices/${deviceId}/channels`, {
      page: params.page,
      count: params.count,
      query: params.query,
      online: params.online,
    });
  } else {
    // 查询全局通道列表
    return commonApi('get', `${CHANNEL_PREFIX}/list`, {
      page: params.page,
      count: params.count,
      query: params.query,
      online: params.online,
      channelType: params.channelType,
    });
  }
};

/**
 * 获取单个通道详情
 * @param channelId 通道数据库ID
 */
export const getChannel = (channelId: number) => {
  return commonApi('get', `${CHANNEL_PREFIX}/one`, { id: channelId });
};

/**
 * 更新通道
 * @param channel 通道信息
 */
export const updateChannel = (channel: any) => {
  return commonApi('post', `${CHANNEL_PREFIX}/update`, channel);
};

/**
 * 添加通道
 * @param channel 通道信息
 */
export const addChannel = (channel: any) => {
  return commonApi('post', `${CHANNEL_PREFIX}/add`, channel);
};

/**
 * 请求截图
 * @param deviceId 设备国标编号
 * @param channelId 通道国标编号
 * @param mark 标识（可选）
 */
export const snapshot = (deviceId: string, channelId: string, mark?: string) => {
  let url = `${GB28181_PREFIX}/snap/${deviceId}/${channelId}`;
  if (mark) {
    url += `?mark=${mark}`;
  }
  return defHttp.get({
    url,
    responseType: 'blob',
  }, {
    isTransformResponse: false,
  }).then((response: any) => {
    // 将blob转换为URL
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    return { data: url };
  });
};

/**
 * 播放通道
 * @param channelId 通道数据库ID
 */
export const play = (channelId: number) => {
  return commonApi('get', `${CHANNEL_PREFIX}/play`, { channelId }, false);
};

/**
 * 停止播放
 * @param channelId 通道数据库ID
 */
export const stopPlay = (channelId: number) => {
  return commonApi('get', `${CHANNEL_PREFIX}/play/stop`, { channelId });
};

// ====================== 媒体服务器管理接口 ======================

/**
 * 获取媒体服务器列表
 */
export const getMediaServerList = () => {
  return commonApi('get', `${SERVER_PREFIX}/media_server/list`);
};

/**
 * 获取在线媒体服务器列表
 */
export const getOnlineMediaServerList = () => {
  return commonApi('get', `${SERVER_PREFIX}/media_server/online/list`);
};

/**
 * 获取单个媒体服务器
 * @param id 媒体服务器ID
 */
export const getMediaServer = (id: string) => {
  return commonApi('get', `${SERVER_PREFIX}/media_server/one/${id}`);
};

/**
 * 测试媒体服务器
 * @param params 测试参数
 */
export const checkMediaServer = (params: {
  ip: string;
  port: number;
  secret: string;
  type?: string;
}) => {
  return commonApi('get', `${SERVER_PREFIX}/media_server/check`, params);
};

/**
 * 保存或更新媒体服务器
 * @param mediaServer 媒体服务器信息
 */
export const saveOrUpdateMediaServer = (mediaServer: any) => {
  return commonApi('post', `${SERVER_PREFIX}/media_server/save`, mediaServer);
};

/**
 * 删除媒体服务器
 * @param id 媒体服务器ID
 */
export const deleteMediaServer = (id: string) => {
  return commonApi('delete', `${SERVER_PREFIX}/media_server/delete`, { id });
};

// ====================== 拉流代理接口 ======================

/**
 * 分页查询拉流代理列表
 * @param params 查询参数
 */
export const getPullProxyList = (params: {
  page?: number;
  count?: number;
  query?: string;
  pulling?: boolean;
  mediaServerId?: string;
}) => {
  return commonApi('get', `${PROXY_PREFIX}/list`, params);
};

/**
 * 查询单个拉流代理
 * @param app 应用名
 * @param stream 流ID
 */
export const getPullProxy = (app: string, stream: string) => {
  return commonApi('get', `${PROXY_PREFIX}/one`, { app, stream });
};

/**
 * 添加拉流代理
 * @param proxy 代理信息
 */
export const addPullProxy = (proxy: any) => {
  return commonApi('post', `${PROXY_PREFIX}/add`, proxy);
};

/**
 * 更新拉流代理
 * @param proxy 代理信息
 */
export const updatePullProxy = (proxy: any) => {
  return commonApi('post', `${PROXY_PREFIX}/update`, proxy);
};

/**
 * 保存拉流代理（新增或更新）
 * @param proxy 代理信息
 */
export const savePullProxy = (proxy: any) => {
  if (proxy.id && proxy.id > 0) {
    return updatePullProxy(proxy);
  } else {
    return addPullProxy(proxy);
  }
};

/**
 * 删除拉流代理
 * @param app 应用名
 * @param stream 流ID
 */
export const deletePullProxy = (app: string, stream: string) => {
  return commonApi('delete', `${PROXY_PREFIX}/del`, { app, stream });
};

/**
 * 启动拉流代理
 * @param idOrApp 代理ID或应用名
 * @param stream 流ID（当第一个参数是app时必填）
 */
export const startPullProxy = async (idOrApp: number | string, stream?: string) => {
  if (typeof idOrApp === 'number') {
    // 通过ID启动
    return commonApi('get', `${PROXY_PREFIX}/start`, { id: idOrApp }, false);
  } else {
    // 通过app和stream启动
    const proxy = await getPullProxy(idOrApp, stream!);
    if (proxy && proxy.id) {
      return commonApi('get', `${PROXY_PREFIX}/start`, { id: proxy.id }, false);
    }
    throw new Error('拉流代理不存在');
  }
};

/**
 * 停止拉流代理
 * @param idOrApp 代理ID或应用名
 * @param stream 流ID（当第一个参数是app时必填）
 */
export const stopPullProxy = async (idOrApp: number | string, stream?: string) => {
  if (typeof idOrApp === 'number') {
    // 通过ID停止
    return commonApi('get', `${PROXY_PREFIX}/stop`, { id: idOrApp });
  } else {
    // 通过app和stream停止
    const proxy = await getPullProxy(idOrApp, stream!);
    if (proxy && proxy.id) {
      return commonApi('get', `${PROXY_PREFIX}/stop`, { id: proxy.id });
    }
    throw new Error('拉流代理不存在');
  }
};

// ====================== 录像回放接口 ======================

/**
 * 查询设备录像列表
 * @param deviceId 设备国标编号
 * @param channelId 通道国标编号
 * @param startTime 开始时间
 * @param endTime 结束时间
 */
export const getDeviceRecordList = (deviceId: string, channelId: string, startTime: string, endTime: string) => {
  return commonApi('get', `${GB_RECORD_PREFIX}/query/${deviceId}/${channelId}`, {
    startTime,
    endTime,
  }, false);
};

/**
 * 设备录像回放
 * @param deviceId 设备国标编号
 * @param channelId 通道国标编号
 * @param startTime 开始时间
 * @param endTime 结束时间
 */
export const playBack = (deviceId: string, channelId: string, startTime: string, endTime: string) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/start/${deviceId}/${channelId}`, {
    startTime,
    endTime,
  }, false);
};

/**
 * 停止设备录像回放
 * @param deviceId 设备国标编号
 * @param channelId 通道国标编号
 */
export const stopPlayBack = (deviceId: string, channelId: string) => {
  return commonApi('get', `${PLAYBACK_PREFIX}/stop/${deviceId}/${channelId}`);
};

/**
 * 查询云端录像日期列表
 * @param app 应用名
 * @param stream 流ID
 * @param year 年（可选）
 * @param month 月（可选）
 * @param mediaServerId 流媒体ID（可选）
 */
export const getCloudRecordDateList = (params: {
  app: string;
  stream: string;
  year?: number;
  month?: number;
  mediaServerId?: string;
}) => {
  return commonApi('get', `${CLOUD_RECORD_PREFIX}/date/list`, params);
};

/**
 * 查询云端录像列表
 * @param params 查询参数
 */
export const getCloudRecordList = (params: {
  app: string;
  stream: string;
  startTime: number;
  endTime: number;
  mediaServerId?: string;
}) => {
  return commonApi('get', `${CLOUD_RECORD_PREFIX}/list`, params);
};

/**
 * 云端录像回放
 * @param params 回放参数
 */
export const cloudplayBack = (params: {
  app: string;
  stream: string;
  startTime: number;
  endTime: number;
  mediaServerId?: string;
}) => {
  return commonApi('get', `${CLOUD_RECORD_PREFIX}/play`, params, false);
};

/**
 * 停止云端录像回放
 * @param params 停止参数
 */
export const stopCloudPlayBack = (params: {
  app: string;
  stream: string;
  mediaServerId?: string;
}) => {
  return commonApi('get', `${CLOUD_RECORD_PREFIX}/play/stop`, params);
};

// ====================== 通道回放接口（通用通道） ======================

/**
 * 查询通道录像
 * @param channelId 通道数据库ID
 * @param startTime 开始时间
 * @param endTime 结束时间
 */
export const queryChannelRecord = (channelId: number, startTime: string, endTime: string) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/query`, {
    channelId,
    startTime,
    endTime,
  }, false);
};

/**
 * 通道录像回放
 * @param channelId 通道数据库ID
 * @param startTime 开始时间
 * @param endTime 结束时间
 */
export const channelPlayback = (channelId: number, startTime: string, endTime: string) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback`, {
    channelId,
    startTime,
    endTime,
  }, false);
};

/**
 * 停止通道录像回放
 * @param channelId 通道数据库ID
 * @param stream 流ID
 */
export const stopChannelPlayback = (channelId: number, stream: string) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/stop`, {
    channelId,
    stream,
  });
};

/**
 * 暂停通道录像回放
 * @param channelId 通道数据库ID
 * @param stream 流ID
 */
export const pauseChannelPlayback = (channelId: number, stream: string) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/pause`, {
    channelId,
    stream,
  });
};

/**
 * 恢复通道录像回放
 * @param channelId 通道数据库ID
 * @param stream 流ID
 */
export const resumeChannelPlayback = (channelId: number, stream: string) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/resume`, {
    channelId,
    stream,
  });
};

/**
 * 拖动通道录像回放
 * @param channelId 通道数据库ID
 * @param stream 流ID
 * @param seekTime 目标时间戳
 */
export const seekChannelPlayback = (channelId: number, stream: string, seekTime: number) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/seek`, {
    channelId,
    stream,
    seekTime,
  });
};

/**
 * 设置通道录像回放倍速
 * @param channelId 通道数据库ID
 * @param stream 流ID
 * @param speed 倍速
 */
export const speedChannelPlayback = (channelId: number, stream: string, speed: number) => {
  return commonApi('get', `${CHANNEL_PREFIX}/playback/speed`, {
    channelId,
    stream,
    speed,
  });
};

// ====================== 设备控制接口 ======================

/**
 * 远程启动设备
 * @param deviceId 设备国标编号
 */
export const teleBoot = (deviceId: string) => {
  return commonApi('get', `/api/device/control/teleboot/${deviceId}`);
};

/**
 * 录像控制
 * @param deviceId 设备国标编号
 * @param channelId 通道国标编号
 * @param recordCmdStr 命令：Record（手动录像），StopRecord（停止手动录像）
 */
export const recordControl = (deviceId: string, channelId: string, recordCmdStr: string) => {
  return commonApi('get', `/api/device/control/record`, {
    deviceId,
    channelId,
    recordCmdStr,
  }, false);
};

/**
 * 设备状态查询
 * @param deviceId 设备国标编号
 */
export const queryDeviceStatus = (deviceId: string) => {
  return commonApi('get', `${GB28181_PREFIX}/devices/${deviceId}/status`, {}, false);
};

/**
 * 设备信息查询
 * @param deviceId 设备国标编号
 */
export const queryDeviceInfo = (deviceId: string) => {
  return commonApi('get', `${GB28181_PREFIX}/info`, { deviceId }, false);
};

/**
 * 设备报警查询
 * @param params 查询参数
 */
export const queryDeviceAlarm = (params: {
  deviceId: string;
  startPriority?: string;
  endPriority?: string;
  alarmMethod?: string;
  alarmType?: string;
  startTime?: string;
  endTime?: string;
}) => {
  return commonApi('get', `${GB28181_PREFIX}/alarm`, params, false);
};

// ====================== 树形结构接口 ======================

/**
 * 获取通道树形结构（用于地图等）
 * @param params 查询参数
 */
export const getTree = (params?: {
  query?: string;
  online?: boolean;
  hasRecordPlan?: boolean;
  channelType?: number;
}) => {
  return commonApi('get', `${CHANNEL_PREFIX}/map/list`, params || {});
};

// ====================== 其他工具接口 ======================

/**
 * 获取FFmpeg命令模板
 * @param mediaServerId 流媒体服务器ID
 */
export const getFFmpegCMDs = (mediaServerId: string) => {
  return commonApi('get', `${PROXY_PREFIX}/ffmpeg_cmd/list`, { mediaServerId });
};

/**
 * 修改通道音频开关
 * @param channelId 通道数据库ID
 * @param audio 是否开启音频
 */
export const changeChannelAudio = (channelId: number, audio: boolean) => {
  return commonApi('post', `${GB28181_PREFIX}/channel/audio`, {
    channelId,
    audio,
  });
};

/**
 * 修改数据流传输模式
 * @param deviceId 设备国标编号
 * @param streamMode 传输模式：UDP/TCP-ACTIVE/TCP-PASSIVE
 */
export const updateTransport = (deviceId: string, streamMode: string) => {
  return commonApi('post', `${GB28181_PREFIX}/transport/${deviceId}/${streamMode}`);
};

/**
 * 开启/关闭目录订阅
 * @param id 设备数据库ID
 * @param cycle 订阅周期（0表示关闭）
 */
export const subscribeCatalog = (id: number, cycle: number) => {
  return commonApi('get', `${GB28181_PREFIX}/subscribe/catalog`, { id, cycle });
};

/**
 * 开启/关闭移动位置订阅
 * @param id 设备数据库ID
 * @param cycle 订阅周期（0表示关闭）
 * @param interval 报送间隔
 */
export const subscribeMobilePosition = (id: number, cycle: number, interval: number) => {
  return commonApi('get', `${GB28181_PREFIX}/subscribe/mobile-position`, {
    id,
    cycle,
    interval,
  });
};

