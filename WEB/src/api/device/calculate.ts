import {defHttp} from '@/utils/http/axios';
import { dedupeRequest } from '@/utils/requestDedupe';

enum Api {
  Alarm = '/video/alert',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}, isTransformResponse = true, responseType = 'json') => {
  defHttp.setHeader({'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token')});

  return defHttp[method](
    {
      url,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        ...headers,
      },
      ...params,
      responseType: responseType,
    },
    {
      isTransformResponse: isTransformResponse,
    },
  );
};

// 告警事件（带请求去重）
export const queryAlarmList = async (params) => {
  const url = Api.Alarm + '/page';
  return dedupeRequest(
    async () => {
      const res = await commonApi('get', url, {params}, {}, false);
      // 后端返回格式: { code: 200, message: "success", data: { alert_list: [], total: 100 } }
      // 当 isTransformResponse: false 时，返回的是整个 Axios 响应对象，需要访问 res.data 获取实际响应
      // 然后访问 res.data.data 获取实际数据
      if (res && res.data && res.data.data) {
        return res.data.data;
      }
      // 兼容处理：如果结构不同，尝试直接返回 res.data
      if (res && res.data) {
        return res.data;
      }
      return res;
    },
    url,
    params,
    1000 // 1秒内相同参数的请求会被去重
  );
};

export const deleteAlarm = (id) => {
  return commonApi('delete', `${Api.Alarm}/delete/${id}`);
};

export const getAlertCount = (params) => {
  return commonApi('get', Api.Alarm + '/count', {device_id: params['id']});
};

export const getAlertImage = (path) => {
  return commonApi('get', Api.Alarm + '/image?path=' + path, {}, {}, false, 'blob');
};

export const getAlertRecord = (path) => {
  return commonApi('get', Api.Alarm + '/record?path=' + path, {}, {}, false, 'blob');
};

// 根据告警时间和设备ID查询对应的录像
export const queryAlertRecord = async (params: {
  device_id: string;
  alert_time: string;
  time_range?: number;
}) => {
  const res = await commonApi('get', Api.Alarm + '/record/query', {params}, {}, false);
  // 处理响应数据
  if (res && res.data) {
    const responseData = res.data;
    // 如果code是400（业务错误），抛出错误让前端处理
    if (responseData.code === 400) {
      const error: any = new Error(responseData.message || '未找到匹配的录像');
      error.response = { data: responseData };
      error.data = responseData;
      throw error;
    }
    // 成功情况，返回数据
    if (responseData.data) {
      return responseData.data;
    }
    return responseData;
  }
  return res;
};

export const generatePlayback = (params) => {
  return commonApi('post', Api.Alarm + '/generatePlayback', {params});
};

// 获取仪表板统计信息（统一接口，带请求去重）
export const getDashboardStatistics = async () => {
  const url = Api.Alarm + '/statistics';
  return dedupeRequest(
    async () => {
      const res = await commonApi('get', url, {}, {}, false);
      // 后端返回格式: { code: 200, message: "success", data: { alarm_count, today_alarm_count, camera_count, algorithm_count, model_count } }
      if (res && res.data && res.data.data) {
        return res.data.data;
      }
      // 兼容处理：如果结构不同，尝试直接返回 res.data
      if (res && res.data) {
        return res.data;
      }
      return res;
    },
    url,
    undefined, // 统计接口无参数
    1000 // 1秒内相同请求会被去重
  );
};
