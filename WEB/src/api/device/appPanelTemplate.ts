import {defHttp} from '@/utils/http/axios';

enum Api {
  AppPanelTemplate = '/appPanelTemplate',
}

const authHeaders = () => ({
  'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
  // @ts-ignore
  ignoreCancelToken: true,
});

export interface AppPanelTemplateItem {
  id: number | string;
  templateCode: string;
  templateName: string;
  productIdentification?: string;
  status?: string; // DRAFT / PUBLISHED / DISABLED
  version?: number;
  panelSchema?: string;
  remark?: string;
  createdTime?: string;
  updatedTime?: string;
}

// 创建 App 面板模板
export const createAppPanelTemplate = (data: Partial<AppPanelTemplateItem>) => {
  return defHttp.post({url: `${Api.AppPanelTemplate}/create`, data, headers: authHeaders()}, {isTransformResponse: true});
};

// 更新 App 面板模板（编码与版本号随发布管理，不可直接修改）
export const updateAppPanelTemplate = (data: Partial<AppPanelTemplateItem>) => {
  return defHttp.put({url: `${Api.AppPanelTemplate}/update`, data, headers: authHeaders()}, {isTransformResponse: true});
};

// 删除 App 面板模板
export const deleteAppPanelTemplate = (id) => {
  return defHttp.delete({url: `${Api.AppPanelTemplate}/delete?id=${id}`, headers: authHeaders()}, {isTransformResponse: true});
};

// 模板详情
export const getAppPanelTemplate = (id) => {
  return defHttp.get({url: `${Api.AppPanelTemplate}/get`, params: {id}, headers: authHeaders()}, {isTransformResponse: true});
};

// 分页查询模板列表
export const getAppPanelTemplatePage = (params) => {
  return defHttp.get({url: `${Api.AppPanelTemplate}/page`, params, headers: authHeaders()}, {isTransformResponse: true});
};

// 发布模板：同产品其他已发布模板自动下线，版本号自增
export const publishAppPanelTemplate = (id) => {
  return defHttp.put(
    {url: `${Api.AppPanelTemplate}/publish?id=${id}`, headers: authHeaders()},
    {isTransformResponse: true},
  );
};

// 停用模板
export const unpublishAppPanelTemplate = (id) => {
  return defHttp.put(
    {url: `${Api.AppPanelTemplate}/unpublish?id=${id}`, headers: authHeaders()},
    {isTransformResponse: true},
  );
};

// 按产品标识取当前生效的已发布模板（APP 下发入口）
export const getPublishedPanelByProduct = (productIdentification) => {
  return defHttp.get(
    {
      url: `${Api.AppPanelTemplate}/get-by-product`,
      params: {productIdentification},
      headers: authHeaders(),
    },
    {isTransformResponse: true},
  );
};
