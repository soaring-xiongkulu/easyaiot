import { defHttp } from '@/utils/http/axios'

// 查询产品模型事件列表
export function getProductEventPage(params) {
  return defHttp.get({ url: '/product/event/page', params })
}

// 查询产品模型事件详情
export function getProductEvent(id: number) {
  return defHttp.get({ url: `/product/event/get?id=${id}` })
}

// 新增产品模型事件
export function createProductEvent(data) {
  return defHttp.post({ url: '/product/event/create', data })
}

// 修改产品模型事件
export function updateProductEvent(data) {
  return defHttp.put({ url: '/product/event/update', data })
}

// 删除产品模型事件
export function deleteProductEvent(id: number) {
  return defHttp.delete({ url: `/product/event/delete?id=${id}` })
}

// 导出产品模型事件 Excel
export function exportProductEvent(params) {
  return defHttp.download({ url: '/product/event/export-excel', params }, '产品模型事件.xls')
}
