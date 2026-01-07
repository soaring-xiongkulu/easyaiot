import {defHttp} from '@/utils/http/axios';

enum Api {
  Packages = '/packages',
  Versions = '/versions',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params = {}, headers = {}) => {
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
      isTransformResponse: true,
    },
  );
};

export const fetchPkgList = (params) => {
  return commonApi('get', Api.Packages, {params});
};

export const addOtaApp = (params) => {
  return commonApi('post', Api.Packages + "/add", {params});
};

export const updateOtaApp = (params) => {
  return commonApi('put', Api.Packages, {params});
};

export const deleteOtaApp = (packageId) => {
  return commonApi('delete', `${Api.Packages}/${packageId}`);
};

export const addVersion = (params) => {
  return commonApi('post', Api.Versions, {params});
};

export const updateVersion = (params) => {
  return commonApi('put', Api.Versions, {params});
};

export const batchPushUpgradePackage = (params) => {
  return commonApi('post', Api.Versions + '/batch-push', {params});
};

export const deleteOtaVerification = (ids) => {
  return commonApi('post', Api.Versions + '/verification/delete', {params: {ids}});
};

export const fetchWhiteList = (params) => {
  return commonApi('get', Api.Versions + '/white-list', {params});
};

export const fetchWhiteGroupList = (params) => {
  return commonApi('get', Api.Versions + '/white-group-list', {params});
};

export const batchAddDeviceTestList = (params) => {
  return commonApi('post', Api.Versions + '/batch-add-device-test-list', {params});
};
