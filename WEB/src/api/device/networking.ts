import { defHttp } from '@/utils/http/axios';

enum Api {
  Networking = '/networkConfig/page',
  NetworkingStart = '/networkConfig/start/',
  NetworkingShutdown = '/networkConfig/shutdown/',
  DelNetworking = '/networkConfig/delete/',
  CertificateList = '/certificate/list',
  InsertNetworking = '/networkConfig/insert',
  NetworkingDetail = '/networkConfig/getById/',
  NetworkingUpdate = '/networkConfig/update',
}

/**
 * @description: 网络组件列表
 */
export const getNetworkingList = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  const { page, pageSize } = params;
  delete params.page;
  delete params.pageSize;
  return defHttp.post(
    {
      url: Api.Networking + `?page=${page}&pageSize=${pageSize}`,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 网络组件启用
 */
export const getNetworkingStart = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.NetworkingStart + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 网络组件禁用
 */
export const getNetworkingShutdown = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.NetworkingShutdown + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 删除网络组件
 */
export const getDelNetworking = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.DelNetworking + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
};
/**
 * @description: 证书列表
 */
export const getCertificateList = () => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.CertificateList,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 新增网络组件
 */
export const postInsertNetworking = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.InsertNetworking,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
};
/**
 * @description: 编辑网络组件
 */
export const postNetworkingUpdate = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.NetworkingUpdate,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
};
/**
 * @description: 网络组件详情
 */
export const getNetworkingDetail = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.NetworkingDetail + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
