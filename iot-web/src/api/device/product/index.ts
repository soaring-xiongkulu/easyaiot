import { defHttp } from '@/utils/http/axios'

// 查询产品列表
export function getProductPage(params) {
  return defHttp.get({ url: '/product/page', params })
}

// 查询产品详情
export function getProduct(id: number) {
  return defHttp.get({ url: `/product/get?id=${id}` })
}

// 新增产品
export function createProduct(data) {
  return defHttp.post({ url: '/product/create', data })
}

// 修改产品
export function updateProduct(data) {
  return defHttp.put({ url: '/product/update', data })
}

// 删除产品
export function deleteProduct(id: number) {
  return defHttp.delete({ url: `/product/delete?id=${id}` })
}

// 导出产品 Excel
export function exportProduct(params) {
  return defHttp.download({ url: '/product/export-excel', params }, '产品.xls')
}
