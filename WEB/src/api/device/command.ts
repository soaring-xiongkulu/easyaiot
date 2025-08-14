import { defHttp } from '@/utils/http/axios';

enum API {
  Commands = '/productCommands',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp[method](
    {
      url,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    {
      isTransformResponse: true,
    },
  );
};

// 服务命令列表查询接口
export const getCommandsList = (params) => {
  return commonApi('get', API.Commands + '/list', params);
};

// 保存物模型-属性
export const saveCommand = (params) => {
  return commonApi('post', API.Commands, params);
};

// 修改物模型-属性
export const updateCommand = (params) => {
  return commonApi('put', API.Commands, params);
};

export const deleteCommands = (ids) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: `${API.Commands}/${ids}`,
    },
    { isTransformResponse: true },
  );
};
