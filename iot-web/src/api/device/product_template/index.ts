import { defHttp } from '@/utils/http/axios'

// 查询产品模板列表
export function getProductTemplatePage(params) {
  return defHttp.get({ url: '/product/template/page', params })
}

// 查询产品模板详情
export function getProductTemplate(id: number) {
  return defHttp.get({ url: `/product/template/get?id=${id}` })
}

// 新增产品模板
export function createProductTemplate(data) {
  return defHttp.post({ url: '/product/template/create', data })
}

// 修改产品模板
export function updateProductTemplate(data) {
  return defHttp.put({ url: '/product/template/update', data })
}

// 删除产品模板
export function deleteProductTemplate(id: number) {
  return defHttp.delete({ url: `/product/template/delete?id=${id}` })
}

// 导出产品模板 Excel
export function exportProductTemplate(params) {
  return defHttp.download({ url: '/product/template/export-excel', params }, '产品模板.xls')
}
