import { defHttp } from '@/utils/http/axios'

// 查询设备列表
export function getDevicePage(params) {
  return defHttp.get({ url: '/device/page', params })
}

// 查询设备详情
export function getDevice(id: number) {
  return defHttp.get({ url: `/device/get?id=${id}` })
}

// 新增设备
export function createDevice(data) {
  return defHttp.post({ url: '/device/create', data })
}

// 修改设备
export function updateDevice(data) {
  return defHttp.put({ url: '/device/update', data })
}

// 删除设备
export function deleteDevice(id: number) {
  return defHttp.delete({ url: `/device/delete?id=${id}` })
}

// 导出设备 Excel
export function exportDevice(params) {
  return defHttp.download({ url: '/device/export-excel', params }, '设备.xls')
}
