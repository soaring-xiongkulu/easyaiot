import { defHttp } from '/@/utils/http/axios';

enum Api {
  // 推送历史列表查询
  historyQuery = '/message/push/history/query',
}
const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params, headers = {}) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });

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
// 推送历史列表查询
export const historyQuery = (_data) => {
  const { pageNo, pageSize, ...data } = _data;
  // 将所有参数（包括分页参数和其他查询参数）作为 params 传递
  return commonApi('get', Api.historyQuery, { 
    params: {
      page: pageNo,
      pageSize: pageSize,
      ...data
    }
  });
};
