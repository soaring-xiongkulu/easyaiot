import { defHttp } from '/@/utils/http/axios';

enum Api {
  // 消息配置
  message_config_add = '/message/config/add',
  message_config_update = '/message/config/update',
  message_config_delete = '/message/config/delete',
  message_config_query = '/message/config/query',
  message_config_mailSendTest = '/message/config/mailSendTest',

  // 消息准备
  message_prepare_add = '/message/prepare/add',
  message_prepare_update = '/message/prepare/update',
  message_prepare_delete = '/message/prepare/delete',
  message_prepare_query = '/message/prepare/query',
  message_file_upload = '/message/file/upload',
  message_preview_user_queryByMsgType = '/message/preview/user/queryByMsgType',
  // 消息推送
  message_send = '/message/send',
}

const commonApi = (method: 'get' | 'post' | 'delete' | 'put', url, params, headers = {}, isTransformResponse = true) => {
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
      isTransformResponse: isTransformResponse,
    },
  );
};

// 添加
export const messageConfigAdd = (data) => {
  return commonApi('post', Api.message_config_add, { data });
};
// 更新
export const messageConfigUpdate = (data) => {
  return commonApi('post', Api.message_config_update, { data });
};

// 删除
export const messageConfigDelete = (params) => {
  return commonApi('get', Api.message_config_delete, { params });
};

// 查询
export const messageConfigQuery = (data) => {
  return commonApi('get', Api.message_config_query, { data });
};

// 根据邮件调试
export const messageConfigMailSendTest = (tos) => {
  return commonApi('get', `${Api.message_config_mailSendTest}?tos=${tos}`, {});
};

// 添加
export const messagePrepareAdd = (data) => {
  return commonApi('post', Api.message_prepare_add, { data });
};

// 更新
export const messagePrepareUpdate = (data) => {
  return commonApi('post', Api.message_prepare_update, { data });
};

// 删除
export const messagePrepareDelete = (params) => {
  return commonApi('get', Api.message_prepare_delete, { params });
};

// 查询
export const messagePrepareQuery = (data) => {
  const { pageNo, pageSize, ...res } = data;
  // 将所有参数（包括分页参数和其他查询参数）作为 params 传递
  return commonApi('get', Api.message_prepare_query, { 
    params: {
      page: pageNo,
      pageSize: pageSize,
      ...res
    }
  });
};
// 邮件上传
export const messageFileUpload = (data) => {
  return commonApi(
    'post',
    Api.message_file_upload,
    { data },
    { 'Content-Type': 'multipart/form-data' },
  );
};

// 根据消息类型查询目标用户列表
export const messagePreviewUserQueryByMsgType = (params) => {
  return commonApi(
    'get',
    `${Api.message_preview_user_queryByMsgType}?msgType=${params?.msgType}`,
    {},
  );
};

// 消息推送
export const messageSend = ({ msgId, msgType }) => {
  return commonApi('post', `${Api.message_send}?msgId=${msgId}&msgType=${msgType}`, {}, {}, false);
};

// import {messageFileUpload} from '/@/api/modules/notice';
