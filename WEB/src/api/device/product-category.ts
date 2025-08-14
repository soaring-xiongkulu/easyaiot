import { defHttp } from '@/utils/http/axios';

enum Api {
  category_tree = '/device/category/_tree',
  category_save = '/device/category/save',
  category_delete = '/device/category/delete',
}
// 产品分类列表
export const getDeviceCategoryTree = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.category_tree}`,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
// 保存/更新
export const categorySave = (data) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.post(
    {
      url: `${Api.category_save}`,
      data,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
// 产品分类删除ƒƒ
export const categoryDelete = (id) => {
  defHttp.setHeader({ 'X-Authorization': 'Bearer ' + localStorage.getItem('jwt_token') });
  return defHttp.get(
    {
      url: `${Api.category_delete}/${id}`,
      headers: {
        // @ts-ignore
        ignoreCancelToken: true,
      },
    },
   { isTransformResponse: true },
  );
};
