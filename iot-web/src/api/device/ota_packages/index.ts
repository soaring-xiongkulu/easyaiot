import { defHttp } from '@/utils/http/axios'

// 查询OTA升级包列表
export function getOtaPackagesPage(params) {
  return defHttp.get({ url: '/ota/packages/page', params })
}

// 查询OTA升级包详情
export function getOtaPackages(id: number) {
  return defHttp.get({ url: `/ota/packages/get?id=${id}` })
}

// 新增OTA升级包
export function createOtaPackages(data) {
  return defHttp.post({ url: '/ota/packages/create', data })
}

// 修改OTA升级包
export function updateOtaPackages(data) {
  return defHttp.put({ url: '/ota/packages/update', data })
}

// 删除OTA升级包
export function deleteOtaPackages(id: number) {
  return defHttp.delete({ url: `/ota/packages/delete?id=${id}` })
}

// 导出OTA升级包 Excel
export function exportOtaPackages(params) {
  return defHttp.download({ url: '/ota/packages/export-excel', params }, 'OTA升级包.xls')
}
