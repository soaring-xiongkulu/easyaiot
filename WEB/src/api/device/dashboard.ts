import { defHttp } from '@/utils/http/axios';

enum Api {
  message_volume = '/indicatorApi/data/MessageVolume',
  device_information = '/indicatorApi/data/deviceInformation',
  monthWarningCount = '/indicatorApi/data/monthWarningCount',
  deviceCount = '/indicatorApi/data/deviceCount',
  deviceStatus = '/indicatorApi/data/deviceStatus',
  deviceTypeCount = '/indicatorApi/data/deviceTypeCount',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params, headers = {}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method](
    {
      url,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        ...headers,
      },
      ...params,
    },
    {
      isTransformResponse: true,
    },
  );
};
// 消息量
export const messageVolume = (data) => {
  return commonApi('post', Api.message_volume, { data });
};

// 设备信息
export const deviceInformation = (data) => {
  return commonApi('post', Api.device_information, { data });
};
// 月告警量接口
export const monthWarningCount = () => {
  return commonApi('post', Api.monthWarningCount, {});
};
// 产品总数接口
export const deviceCount = (data) => {
  return commonApi('post', Api.deviceCount, { data });
};
// 设备状态统计接口
export const deviceStatus = (data) => {
  return commonApi('post', Api.deviceStatus, { data });
};
// 设备类型数量统计接口
export const deviceTypeCount = (data) => {
  return commonApi('post', Api.deviceTypeCount, { data });
};

// import {deviceTypeCount} from '@/api/device/dashboard';
