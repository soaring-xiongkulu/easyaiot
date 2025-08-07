import { defHttp } from '@/utils/http/axios'

// 查询产品分类列表
export function getProductTypePage(params) {
  return defHttp.get({ url: '/product/type/page', params })
}

// 查询产品分类详情
export function getProductType(id: number) {
  return defHttp.get({ url: `/product/type/get?id=${id}` })
}

// 新增产品分类
export function createProductType(data) {
  return defHttp.post({ url: '/product/type/create', data })
}

// 修改产品分类
export function updateProductType(data) {
  return defHttp.put({ url: '/product/type/update', data })
}

// 删除产品分类
export function deleteProductType(id: number) {
  return defHttp.delete({ url: `/product/type/delete?id=${id}` })
}

// 导出产品分类 Excel
export function exportProductType(params) {
  return defHttp.download({ url: '/product/type/export-excel', params }, '产品分类.xls')
}
