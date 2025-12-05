import {defHttp} from '@/utils/http/axios';

enum Api {
  NodeRed = '/nodeRed',
}

/**
 * @description: 规则查询
 */
export const flowsList = () => {
  return defHttp.get({url: Api.NodeRed + '/flows'}, {isTransformResponse: false});
}

/**
 * @description: 新增规则
 */
export const addFlows = (params) =>
  defHttp.post(
    {
      url: Api.NodeRed + '/flow',
      params,
    },
    {isTransformResponse: false},
  );
/**
 * @description: 获取规则链详细信息
 */
export const getFlows = (key: string) => {
  if (!key || key === 'undefined') {
    return Promise.reject(new Error('规则链ID不能为空'));
  }
  return defHttp.get(
    {
      url: Api.NodeRed + '/flow/' + key,
    },
    {isTransformResponse: false},
  );
};
/**
 * @description: 更新规则
 */
export const updateflows = (key, params) => {
  if (!key || key === 'undefined') {
    return Promise.reject(new Error('规则链ID不能为空'));
  }
  return defHttp.put(
    {
      url: Api.NodeRed + '/flow/' + key,
      params,
    },
    {isTransformResponse: false},
  );
};
/**
 * @description: 删除规则
 */
export const deleteflows = (key) => {
  if (!key || key === 'undefined') {
    return Promise.reject(new Error('规则链ID不能为空'));
  }
  return defHttp.delete(
    {
      url: Api.NodeRed + '/flow/' + key,
    },
    {isTransformResponse: false},
  );
};
