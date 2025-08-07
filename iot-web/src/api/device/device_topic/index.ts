import { defHttp } from '@/utils/http/axios'

// 查询设备Topic数据列表
export function getDeviceTopicPage(params) {
  return defHttp.get({ url: '/device/topic/page', params })
}

// 查询设备Topic数据详情
export function getDeviceTopic(id: number) {
  return defHttp.get({ url: `/device/topic/get?id=${id}` })
}

// 新增设备Topic数据
export function createDeviceTopic(data) {
  return defHttp.post({ url: '/device/topic/create', data })
}

// 修改设备Topic数据
export function updateDeviceTopic(data) {
  return defHttp.put({ url: '/device/topic/update', data })
}

// 删除设备Topic数据
export function deleteDeviceTopic(id: number) {
  return defHttp.delete({ url: `/device/topic/delete?id=${id}` })
}

// 导出设备Topic数据 Excel
export function exportDeviceTopic(params) {
  return defHttp.download({ url: '/device/topic/export-excel', params }, '设备Topic数据.xls')
}
