import { defHttp } from '@/utils/http/axios';

enum API {
  CommandsRequest = '/product/commands/requests',
  CommandsResponse = '/product/commands/response',
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

export const getCommandsRequestList = (params) => {
  //alert(JSON.stringify(params));
  return commonApi('get', API.CommandsRequest + '/list', params);
};

export const saveCommandsRequest = (params) => {
  return commonApi('post', API.CommandsRequest, params);
};

export const updateCommandsRequest = (params) => {
  return commonApi('put', API.CommandsRequest, params);
};

export const deleteCommandsRequests = (ids) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: `${API.CommandsRequest}/${ids}`,
    },
    { isTransformResponse: true },
  );
};

export const getCommandsResponseList = (params) => {
  return commonApi('get', API.CommandsResponse + '/list', params);
};

export const saveCommandsResponse = (params) => {
  return commonApi('post', API.CommandsResponse, params);
};

export const updateCommandsResponse = (params) => {
  return commonApi('put', API.CommandsResponse, params);
};

export const deleteCommandsResponses = (ids) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: `${API.CommandsResponse}/${ids}`,
    },
    { isTransformResponse: true },
  );
};
