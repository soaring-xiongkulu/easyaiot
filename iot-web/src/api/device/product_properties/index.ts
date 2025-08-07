import { defHttp } from '@/utils/http/axios'

// 查询产品模型属性列表
export function getProductPropertiesPage(params) {
  return defHttp.get({ url: '/product/properties/page', params })
}

// 查询产品模型属性详情
export function getProductProperties(id: number) {
  return defHttp.get({ url: `/product/properties/get?id=${id}` })
}

// 新增产品模型属性
export function createProductProperties(data) {
  return defHttp.post({ url: '/product/properties/create', data })
}

// 修改产品模型属性
export function updateProductProperties(data) {
  return defHttp.put({ url: '/product/properties/update', data })
}

// 删除产品模型属性
export function deleteProductProperties(id: number) {
  return defHttp.delete({ url: `/product/properties/delete?id=${id}` })
}

// 导出产品模型属性 Excel
export function exportProductProperties(params) {
  return defHttp.download({ url: '/product/properties/export-excel', params }, '产品模型属性.xls')
}
