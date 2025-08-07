import { defHttp } from '@/utils/http/axios'

// 查询设备日志列表
export function getDeviceLogPage(params) {
  return defHttp.get({ url: '/device/log/page', params })
}

// 查询设备日志详情
export function getDeviceLog(id: number) {
  return defHttp.get({ url: `/device/log/get?id=${id}` })
}

// 新增设备日志
export function createDeviceLog(data) {
  return defHttp.post({ url: '/device/log/create', data })
}

// 修改设备日志
export function updateDeviceLog(data) {
  return defHttp.put({ url: '/device/log/update', data })
}

// 删除设备日志
export function deleteDeviceLog(id: number) {
  return defHttp.delete({ url: `/device/log/delete?id=${id}` })
}

// 导出设备日志 Excel
export function exportDeviceLog(params) {
  return defHttp.download({ url: '/device/log/export-excel', params }, '设备日志.xls')
}
