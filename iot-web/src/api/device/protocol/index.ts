import { defHttp } from '@/utils/http/axios'

// 查询协议信息列表
export function getProtocolPage(params) {
  return defHttp.get({ url: '/protocol/page', params })
}

// 查询协议信息详情
export function getProtocol(id: number) {
  return defHttp.get({ url: `/protocol/get?id=${id}` })
}

// 新增协议信息
export function createProtocol(data) {
  return defHttp.post({ url: '/protocol/create', data })
}

// 修改协议信息
export function updateProtocol(data) {
  return defHttp.put({ url: '/protocol/update', data })
}

// 删除协议信息
export function deleteProtocol(id: number) {
  return defHttp.delete({ url: `/protocol/delete?id=${id}` })
}

// 导出协议信息 Excel
export function exportProtocol(params) {
  return defHttp.download({ url: '/protocol/export-excel', params }, '协议信息.xls')
}
