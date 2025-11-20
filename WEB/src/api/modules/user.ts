import { defHttp } from '/@/utils/http/axios';

enum Api {
  // 用户
  message_preview_user_add = '/message/preview/user/add',
  message_preview_user_update = '/message/preview/user/update',
  message_preview_user_delete = '/message/preview/user/delete',
  message_preview_user_query = '/message/preview/user/query',
  message_preview_user_exportExcel = '/message/preview/user/exportExcel',
  message_preview_user_import = '/message/preview/user/import',
  // 用户分组
  message_preview_user_group_add = '/message/preview/user/group/add',
  message_preview_user_group_update = '/message/preview/user/group/update',
  message_preview_user_group_delete = '/message/preview/user/group/delete',
  message_preview_user_group_query = '/message/preview/user/group/query',
  message_preview_user_group_queryByMsgType = '/message/preview/user/group/queryByMsgType',
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

// 添加
export const messagePreviewUserAdd = (data) => {
  return commonApi('post', Api.message_preview_user_add, { data });
};

// 更新
export const messagePreviewUserUpdate = (data) => {
  return commonApi('post', Api.message_preview_user_update, { data });
};

// 删除
export const messagePreviewUserDelete = (params) => {
  return commonApi('get', Api.message_preview_user_delete, { params });
};

// 列表
export const messagePreviewUserQuery = (data) => {
  const { pageNo, pageSize, ...res } = data;
  const url = `${Api.message_preview_user_query}?page=${pageNo}&pageSize=${pageSize}`;
  return commonApi('get', url, { data: res });
};

// 模版下载
export const messagePreviewUserExportExcel = () => {
  return Api.message_preview_user_exportExcel;
};

// 导入用户
export const messagePreviewUserImport = (data) => {
  return commonApi(
    'post',
    Api.message_preview_user_import,
    { data },
    { 'Content-Type': 'multipart/form-data' },
  );
};

// 分组添加
export const userGroupAdd = (data) => {
  return commonApi('post', Api.message_preview_user_group_add, { data });
};
// 分组更新
export const userGroupUpdate = (data) => {
  return commonApi('post', Api.message_preview_user_group_update, { data });
};

// 分组删除
export const userGroupDelete = (params) => {
  return commonApi('get', Api.message_preview_user_group_delete, { params });
};
// 分组查询
export const userGroupQuery = (data) => {
  const { pageNo, pageSize, ...res } = data;
  const url = `${Api.message_preview_user_group_query}?page=${pageNo}&pageSize=${pageSize}`;
  return commonApi('get', url, { data: res });
};
// 根据消息类型
export const userGroupQueryByMsgType = (params) => {
  return commonApi('get', Api.message_preview_user_group_queryByMsgType, { params });
};

// import {messagePreviewUserQuery} from '/@/api/modules/user';
