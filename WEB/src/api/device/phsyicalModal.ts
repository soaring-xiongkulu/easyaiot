import { defHttp } from '@/utils/http/axios';

enum API {
  PropertiesLIST = '/productProperties/list',
  ServicesLIST = '/productServices/list',
  EventsLIST = '/productEvent/list',
  PRODUCT_PROPERTIES = '/productProperties',
  PRODUCT_SERVICE = '/productServices',
  PRODUCT_EVENTS = '/productEvent',
  PRODUCT_EVENTS_RESPONSE = '/productEventResponse',
  CHECKIDENTIFIER = '/thingModel/check',
  DEL_PROPERTIES = '/productProperties/',
  DEL_SERVICE = '/productServices/',
  DEL_EVENTS = '/productEvent/',
  RELEASE = '/thingModel/',
  DETAIL = '/thingModel/',
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

// 物模型属性列表查询接口
export const getPropertiesList = (params) => {
  return commonApi('get', API.PropertiesLIST, params);
};

// 物模型服务列表查询接口
export const getServicesList = (params) => {
  return commonApi('get', API.ServicesLIST, params);
};

// 物模型事件列表查询接口
export const getEventsList = (params) => {
  return commonApi('get', API.EventsLIST, params);
};

//{"accessMode":"w","dataType":"INT","propertyName":"湿度","propertyCode":"humidity","min":"20","max":"40","step":2,"unit":"m㎡","remark":"描述湿度属性。"}
// 保存物模型-属性
export const savePhsyicalProperties = (params) => {
  return commonApi('post', API.PRODUCT_PROPERTIES, params);
};

// 保存物模型-服务
export const savePhsyicalService = (params) => {
  return commonApi('post', API.PRODUCT_SERVICE, params);
};

// 保存物模型-事件
export const savePhsyicalEvent = (params) => {
  return commonApi('post', API.PRODUCT_EVENTS, params);
};

// 保存物模型-事件-输出参数
export const savePhsyicalEventResponse = (params) => {
  return commonApi('post', API.PRODUCT_EVENTS_RESPONSE, params);
};

// 修改物模型-属性
export const updatePhsyicalProperties = (params) => {
  return commonApi('put', API.PRODUCT_PROPERTIES, params);
};

// 修改物模型-服务
export const updatePhsyicalService = (params) => {
  return commonApi('put', API.PRODUCT_SERVICE, params);
};

// 修改物模型-事件
export const updatePhsyicalEvent = (params) => {
  return commonApi('put', API.PRODUCT_EVENTS, params);
};

// 修改物模型-事件-输出参数
export const updatePhsyicalEventResponse = (params) => {
  return commonApi('put', API.PRODUCT_EVENTS_RESPONSE, params);
};

// 校验标识是否重复
export const checkIdentifier = (params) => commonApi('post', API.CHECKIDENTIFIER, params);

// 删除物模型-属性
export const delPhsyicalProperties = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: API.DEL_PROPERTIES + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
}

// 删除物模型-服务
export const delPhsyicalService = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: API.DEL_SERVICE + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
}

// 删除物模型-事件
export const delPhsyicalEvent = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: API.DEL_EVENTS + params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isReturnNativeResponse: true },
  );
}

// 发布物模型
export const releasePhsyical = (params) => commonApi('put', API.RELEASE, params);

// 获取物模型
export const getPhsyical = (params) => commonApi('get', API.DETAIL, params);
