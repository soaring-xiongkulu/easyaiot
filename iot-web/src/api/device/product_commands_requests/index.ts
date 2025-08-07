import { defHttp } from '@/utils/http/axios'

// 查询产品模型设备下发服务命令属性列表
export function getProductCommandsRequestsPage(params) {
  return defHttp.get({ url: '/product/commands-requests/page', params })
}

// 查询产品模型设备下发服务命令属性详情
export function getProductCommandsRequests(id: number) {
  return defHttp.get({ url: `/product/commands-requests/get?id=${id}` })
}

// 新增产品模型设备下发服务命令属性
export function createProductCommandsRequests(data) {
  return defHttp.post({ url: '/product/commands-requests/create', data })
}

// 修改产品模型设备下发服务命令属性
export function updateProductCommandsRequests(data) {
  return defHttp.put({ url: '/product/commands-requests/update', data })
}

// 删除产品模型设备下发服务命令属性
export function deleteProductCommandsRequests(id: number) {
  return defHttp.delete({ url: `/product/commands-requests/delete?id=${id}` })
}

// 导出产品模型设备下发服务命令属性 Excel
export function exportProductCommandsRequests(params) {
  return defHttp.download({ url: '/product/commands-requests/export-excel', params }, '产品模型设备下发服务命令属性.xls')
}
