import { defHttp } from '@/utils/http/axios';

enum Api {
  telemetry = '/plugins/telemetry/',
  Alarm = '/deviceEvent',
  Services = '/deviceService',
  Relations = '/relations/info',
  OperateRelation = '/relation',
  Log = '/audit/logs/entity/',
  IotData = '/iotData/search',
  IotDataExport = '/iotData/export',

  Devices = '/tenant/devices',
  AssetInfos = '/tenant/assetInfos',
  EntityViewInfos = '/tenant/entityViewInfos',
  Tenant = '/tenant/',
  Customers = '/customers',
  Dashboards = '/tenant/dashboards',
}

/**
 * @description: 服务端属性列表
 */
export const getAttribute = ({ module, id, scope }) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.telemetry + `${module}/${id}/values/attributes/${scope}`,
    },
   { isTransformResponse: true },
  );
};

/**
 * @description: 服务端属性列表(module, id, params, scope)
 */
export const postPluginsTelemetry = (module, id, params, scope) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp.post(
    {
      url: Api.telemetry + `${module}/${id}/${scope}`,
      params,
    },
   { isTransformResponse: true },
  );
};

/**
 * @description: 删除服务端属性(module, id, params, scope)
 */
export const deletePluginsTelemetry = (module, id, params, scope) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

  return defHttp.delete(
    {
      url: Api.telemetry + `${module}/${id}/${scope}?keys=` + params.keys,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 告警列表
 */
export const getEventList = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Alarm + '/list',
      params,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 服务列表
 */
export const getServices = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Services + '/list',
      params,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 关联列表
 */
export const getRelations = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Relations,
      params,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 关联删除
 */
export const delRelation = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: Api.OperateRelation,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        'content-type': 'application/x-www-form-urlencoded',
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 新增编辑关联
 */
export const postRelation = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.OperateRelation,
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
 * @description: 审计日志列表
 */
export const getLog = ({ module, id, params }) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Log + `${module}/${id}`,
      params,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 数据上传列表
 */
export const getIotData = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.IotData,
      params,
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 数据上传导出
 */
export const postIotDataExport = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.IotDataExport,
      params,
      responseType: 'blob',
    },
    { isReturnNativeResponse: true },
  );
};

/**
 * @description: 获得设备列表
 */
export const getDevices = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Devices,
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
 * @description: 获得资产列表
 */
export const getAssetInfos = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.AssetInfos,
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
 * @description: 获得实体视图列表
 */
export const getEntityViewInfos = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.EntityViewInfos,
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
 * @description: 获得租户列表
 */
export const getTenant = (id) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Tenant + `/${id}`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
/**
 * @description: 获得客户列表
 */
export const getCustomers = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Customers,
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
 * @description: 获得设备列表
 */
export const getDashboards = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Dashboards,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
