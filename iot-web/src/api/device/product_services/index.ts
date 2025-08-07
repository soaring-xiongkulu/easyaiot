import { defHttp } from '@/utils/http/axios'

// 查询产品模型服务列表
export function getProductServicesPage(params) {
  return defHttp.get({ url: '/product/services/page', params })
}

// 查询产品模型服务详情
export function getProductServices(id: number) {
  return defHttp.get({ url: `/product/services/get?id=${id}` })
}

// 新增产品模型服务
export function createProductServices(data) {
  return defHttp.post({ url: '/product/services/create', data })
}

// 修改产品模型服务
export function updateProductServices(data) {
  return defHttp.put({ url: '/product/services/update', data })
}

// 删除产品模型服务
export function deleteProductServices(id: number) {
  return defHttp.delete({ url: `/product/services/delete?id=${id}` })
}

// 导出产品模型服务 Excel
export function exportProductServices(params) {
  return defHttp.download({ url: '/product/services/export-excel', params }, '产品模型服务.xls')
}
