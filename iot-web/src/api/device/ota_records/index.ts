import { defHttp } from '@/utils/http/axios'

// 查询OTA升级记录列表
export function getOtaRecordsPage(params) {
  return defHttp.get({ url: '/ota/records/page', params })
}

// 查询OTA升级记录详情
export function getOtaRecords(id: number) {
  return defHttp.get({ url: `/ota/records/get?id=${id}` })
}

// 新增OTA升级记录
export function createOtaRecords(data) {
  return defHttp.post({ url: '/ota/records/create', data })
}

// 修改OTA升级记录
export function updateOtaRecords(data) {
  return defHttp.put({ url: '/ota/records/update', data })
}

// 删除OTA升级记录
export function deleteOtaRecords(id: number) {
  return defHttp.delete({ url: `/ota/records/delete?id=${id}` })
}

// 导出OTA升级记录 Excel
export function exportOtaRecords(params) {
  return defHttp.download({ url: '/ota/records/export-excel', params }, 'OTA升级记录.xls')
}
