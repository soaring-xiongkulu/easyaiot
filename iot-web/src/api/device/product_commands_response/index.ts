import { defHttp } from '@/utils/http/axios'

// 查询产品模型设备响应服务命令属性列表
export function getProductCommandsResponsePage(params) {
  return defHttp.get({ url: '/product/commands-response/page', params })
}

// 查询产品模型设备响应服务命令属性详情
export function getProductCommandsResponse(id: number) {
  return defHttp.get({ url: `/product/commands-response/get?id=${id}` })
}

// 新增产品模型设备响应服务命令属性
export function createProductCommandsResponse(data) {
  return defHttp.post({ url: '/product/commands-response/create', data })
}

// 修改产品模型设备响应服务命令属性
export function updateProductCommandsResponse(data) {
  return defHttp.put({ url: '/product/commands-response/update', data })
}

// 删除产品模型设备响应服务命令属性
export function deleteProductCommandsResponse(id: number) {
  return defHttp.delete({ url: `/product/commands-response/delete?id=${id}` })
}

// 导出产品模型设备响应服务命令属性 Excel
export function exportProductCommandsResponse(params) {
  return defHttp.download({ url: '/product/commands-response/export-excel', params }, '产品模型设备响应服务命令属性.xls')
}
