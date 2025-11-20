import {defHttp} from '@/utils/http/axios';

enum Api {
  Packages = '/packages',
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
