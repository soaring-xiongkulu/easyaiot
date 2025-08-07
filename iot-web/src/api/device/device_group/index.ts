import { defHttp } from '@/utils/http/axios'

// 查询设备分组列表
export function getDeviceGroupPage(params) {
  return defHttp.get({ url: '/device/group/page', params })
}

// 查询设备分组详情
export function getDeviceGroup(id: number) {
  return defHttp.get({ url: `/device/group/get?id=${id}` })
}

// 新增设备分组
export function createDeviceGroup(data) {
  return defHttp.post({ url: '/device/group/create', data })
}

// 修改设备分组
export function updateDeviceGroup(data) {
  return defHttp.put({ url: '/device/group/update', data })
}

// 删除设备分组
export function deleteDeviceGroup(id: number) {
  return defHttp.delete({ url: `/device/group/delete?id=${id}` })
}

// 导出设备分组 Excel
export function exportDeviceGroup(params) {
  return defHttp.download({ url: '/device/group/export-excel', params }, '设备分组.xls')
}
