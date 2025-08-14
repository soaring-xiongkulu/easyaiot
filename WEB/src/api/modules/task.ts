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
  const { page, pageSize, ...data } = _data;
  const url = `${Api.historyQuery}?page=${page}&pageSize=${pageSize}`;
  return commonApi('post', url, { data });
};
