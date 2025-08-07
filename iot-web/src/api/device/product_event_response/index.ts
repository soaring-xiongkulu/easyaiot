import { defHttp } from '@/utils/http/axios'

// 查询产品模型事件响应列表
export function getProductEventResponsePage(params) {
  return defHttp.get({ url: '/product/event-response/page', params })
}

// 查询产品模型事件响应详情
export function getProductEventResponse(id: number) {
  return defHttp.get({ url: `/product/event-response/get?id=${id}` })
}

// 新增产品模型事件响应
export function createProductEventResponse(data) {
  return defHttp.post({ url: '/product/event-response/create', data })
}

// 修改产品模型事件响应
export function updateProductEventResponse(data) {
  return defHttp.put({ url: '/product/event-response/update', data })
}

// 删除产品模型事件响应
export function deleteProductEventResponse(id: number) {
  return defHttp.delete({ url: `/product/event-response/delete?id=${id}` })
}

// 导出产品模型事件响应 Excel
export function exportProductEventResponse(params) {
  return defHttp.download({ url: '/product/event-response/export-excel', params }, '产品模型事件响应.xls')
}
