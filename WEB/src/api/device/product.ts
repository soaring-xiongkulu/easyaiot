import {defHttp} from '@/utils/http/axios';

enum Api {
  DeviceProfile = '/product',
  DeviceProfileTemplate = '/productTemplate',
  Topic = '/topic',
  RuleChains = '/ruleChains',
  RuleChain = '/ruleChain',
  Queues = '/queues',
  gateway_device_query = '/device/list',
  image_upload = '/deviceprofile/image/upload',
  image_download = '/deviceProfile/image/download/',
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
      }
    },
   { isTransformResponse: true },
  );
};

// 在线调试
export const issueCommands = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.DeviceProfile}/issueCommands`,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: true },
  );
};

// 添加产品
export const addDeviceProfile = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.DeviceProfile}`,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: true },
  );
};

// 编辑产品
export const editDeviceProfile = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.put(
    {
      url: `${Api.DeviceProfile}`,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: true },
  );
};

// 获取产品列表
export const getDeviceProfiles = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${Api.DeviceProfile}/list`,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
  { isTransformResponse: true },
  );
};

// 设置默认
export const setDeviceProfilesDefault = (id) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.DeviceProfile}/${id}/default`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
    { isTransformResponse: true },
  );
};

// 删除
export const deleteDeviceProfile = (ids) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.delete(
    {
      url: `${Api.DeviceProfile}/${ids}`,
    },
    { isTransformResponse: true },
  );
};

// 获取详情
export const getDeviceProfileDetail = (id) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${Api.DeviceProfile}/${id}`,
    },
    { isTransformResponse: true },
  );
};

// 获取产品模板列表
export const getProductTemplateList = () => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${Api.DeviceProfileTemplate}/query`,
    },
    { isTransformResponse: true },
  );
};

// 规则链
export const getRuleChains = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.RuleChains,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};

// 获取规则链详情
export const getRuleChain = (id) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${Api.RuleChain}/${id}`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};

// 任务队列
export const getQueues = (params) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: Api.Queues,
      params,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};

// 根据产品标识获取设备列表
export const getDvicesQuery = (params) => {
  const url = `${Api.gateway_device_query}`;
  return commonApi('get', url, params);
};
// 设备接入详情
export const getTopicsDeviceSelectById = (params) => {
  //alert(JSON.stringify(params));
  return commonApi('get', `${Api.Topic}` + '/list', params);
}

// 图片上传
export const imageUpload = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: Api.image_upload,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
        'Content-Type': 'multipart/form-data',
      },
    },

  );
};

// 获取图片
export const imageDownload = (params) => commonApi('get', Api.image_download, params);

// import {imageUpload,imageDownload} from '@/api/device/product';
