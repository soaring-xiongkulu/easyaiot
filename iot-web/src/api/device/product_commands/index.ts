import { defHttp } from '@/utils/http/axios'

// 查询产品模型设备服务命令列表
export function getProductCommandsPage(params) {
  return defHttp.get({ url: '/product/commands/page', params })
}

// 查询产品模型设备服务命令详情
export function getProductCommands(id: number) {
  return defHttp.get({ url: `/product/commands/get?id=${id}` })
}

// 新增产品模型设备服务命令
export function createProductCommands(data) {
  return defHttp.post({ url: '/product/commands/create', data })
}

// 修改产品模型设备服务命令
export function updateProductCommands(data) {
  return defHttp.put({ url: '/product/commands/update', data })
}

// 删除产品模型设备服务命令
export function deleteProductCommands(id: number) {
  return defHttp.delete({ url: `/product/commands/delete?id=${id}` })
}

// 导出产品模型设备服务命令 Excel
export function exportProductCommands(params) {
  return defHttp.download({ url: '/product/commands/export-excel', params }, '产品模型设备服务命令.xls')
}
