import { defHttp } from '@/utils/http/axios';

enum Api {
  // 配置
  notice_config_add = '/message/config/add',
  notice_config_update = '/message/config/update',
  notice_config_delete = '/message/config/delete',
  notice_config_query = '/message/config/query',
  notice_config_queryById = '/message/config/queryById',
  notice_config_export = '/message/config/export',
  notice_config_exportPage = '/message/config/exportPage',
  notice_config_import = '/message/config/import',
  notify_config_queryByType = '/message/config/queryByType',
  notify_config_departments = '/message/config/departments',
  notify_config_allCorpUsers = '/message/config/allCorpUsers',
  notify_config_tags = '/message/config/tags',

  // 记录
  notice_history_add = '/message/history/add',
  notice_history_query = '/message/history/query',
  // 模版
  notify_template_add = '/message/template/add',
  notify_template_update = '/message/template/update',
  notify_template_delete = '/message/template/delete',
  notify_template_query = '/message/template/query',
  notify_template_queryById = '/message/template/queryById',
  notify_template_smsTemplates = '/message/template/smsTemplates',
  notify_template_smsSigns = '/message/template/smsSigns',
  notify_template_exportPage = '/message/template/exportPage',
  notify_template_export = '/message/template/export',
  notify_template_import = '/message/template/import',
  notify_template_queryByType = '/message/template/queryByType',
  // 通知发送
  notify_send = '/message/send',
  // 告警通知
  notify_warn_query = '/warn/notify/query',
  notify_warn_updateStatus = '/warn/notify/updateStatus',
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
export const noticeConfigAdd = (data) => {
  return commonApi('post', Api.notice_config_add, { data });
};
// 更新
export const noticeConfigUpdate = (data) => {
  return commonApi('post', Api.notice_config_update, { data });
};
// 删除
export const noticeConfigDelete = (params) => {
  return commonApi('get', Api.notice_config_delete, { params });
};

// 查询
export const noticeConfigQuery = (params) => {
  return commonApi('get', Api.notice_config_query, { params });
};
// 配置详情
export const noticeConfigQueryById = (params) => {
  return commonApi('get', Api.notice_config_queryById, { params });
};

// 导出
export const noticeConfigExport = (data) => {
  return commonApi('post', Api.notice_config_export, { data });
};
// 导出当前页
export const noticeConfigExportPage = (data) => {
  const url = `${Api.notice_config_exportPage}?page=${data?.page}&pageSize=${data?.pageSize}`;
  return commonApi('post', url, {});
};

// 导入
export const noticeConfigImport = (data) => {
  return commonApi(
    'post',
    Api.notice_config_import,
    { data },
    { 'Content-Type': 'multipart/form-data' },
  );
};

// 添加记录
export const noticeConfigHistoryAdd = (data) => {
  return commonApi('post', Api.notice_history_add, { data });
};
// 记录列表查询
export const noticeConfigHistoryQuery = (data) => {
  return commonApi('post', Api.notice_history_query, { data });
};

// 模版新增
export const notifyTemplateAdd = (data) => {
  return commonApi('post', Api.notify_template_add, { data });
};
// 模版更新
export const notifyTemplateUpdate = (data) => {
  return commonApi('post', Api.notify_template_update, { data });
};
// 模版删除
export const notifyTemplateDelete = (params) => {
  return commonApi('get', Api.notify_template_delete, { params });
};

// 模版分页查询
export const notifyTemplateQuery = (data) => {
  const { pageNo, pageSize, ...res } = data;
  const url = `${Api.notify_template_query}?page=${pageNo}&pageSize=${pageSize}`;
  return commonApi('post', url, { data: res });
};

// 模版详情
export const notifyTemplateQueryById = (params) => {
  return commonApi('get', Api.notify_template_queryById, { params });
};
// 短信模版列表
export const notifyTemplateSmsTemplates = (params) => {
  return commonApi('get', Api.notify_template_smsTemplates, { params });
};
// 短信签名列表
export const notifyTemplateSmsSigns = (params) => {
  return commonApi('get', Api.notify_template_smsSigns, { params });
};
// 导出整页
export const notifyTemplateExportPage = (data) => {
  const url = `${Api.notify_template_exportPage}?page=${data?.page}&pageSize=${data?.pageSize}`;
  return commonApi('post', url, {});
};
// 导出单个
export const notifyTemplateExport = (data) => {
  return commonApi('post', Api.notify_template_export, { data });
};

// 导入
export const notifyTemplateImport = (data) => {
  return commonApi(
    'post',
    Api.notify_template_import,
    { data },
    { 'Content-Type': 'multipart/form-data' },
  );
};

// 根据类型查模版
export const notifyConfigQueryByType = (params) => {
  return commonApi('get', Api.notify_config_queryByType, { params });
};

// 根据类型查配置
export const notifyTemplateQueryByType = (params) => {
  return commonApi('get', Api.notify_template_queryByType, { params });
};

// 通知发送
export const notifySend = (params, data) => {
  return commonApi('post', Api.notify_send, { params, data });
};

// 获取企业部门列表
export const notifyConfigDepartments = (params) => {
  return commonApi('get', Api.notify_config_departments, { params });
};
// 获取企业用户列表
export const notifyConfigAllCorpUsers = (params) => {
  return commonApi('get', Api.notify_config_allCorpUsers, { params });
};

// 获取企微信标签列表
export const notifyConfigTags = (params) => {
  return commonApi('get', Api.notify_config_tags, { params });
};

// 告警通知查询
export const notifyWarnQuery = (data) => {
  const { pageNo, pageSize, ...res } = data;
  const url = `${Api.notify_warn_query}?page=${pageNo}&pageSize=${pageSize}`;
  return commonApi('post', url, { data: res });
};
// 告警处理
export const notifyWarnUpdateStatus = (data) => {
  return commonApi('post', Api.notify_warn_updateStatus, { data });
};

// import {notifyWarnQuery} from '@/api/device/notice';
