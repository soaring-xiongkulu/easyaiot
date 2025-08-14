import {defHttp} from '@/utils/http/axios';

enum Api {
  Model = '/calculate/model',
  Video = '/calculate/video',
  Alarm = '/calculate/alarm',
  Customer = '/calculate/customer',
  Nvr = '/calculate/nvr',
  PushLog = '/calculate/pushlog',
  Task = '/calculate/task',
  Playback = '/calculate/playback',
  Box = '/api/device/box',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}, isTransformResponse = true) => {
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
    },
    {
      isTransformResponse: isTransformResponse,
    },
  );
};

// ONVIF搜索局域网内设备
export const searchCamera = () => {
  return commonApi('get', Api.Video + '/searchCamera');
};
