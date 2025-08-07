import { defHttp } from '@/utils/http/axios'

// 查询OTA升级任务列表
export function getOtaTasksPage(params) {
  return defHttp.get({ url: '/ota/tasks/page', params })
}

// 查询OTA升级任务详情
export function getOtaTasks(id: number) {
  return defHttp.get({ url: `/ota/tasks/get?id=${id}` })
}

// 新增OTA升级任务
export function createOtaTasks(data) {
  return defHttp.post({ url: '/ota/tasks/create', data })
}

// 修改OTA升级任务
export function updateOtaTasks(data) {
  return defHttp.put({ url: '/ota/tasks/update', data })
}

// 删除OTA升级任务
export function deleteOtaTasks(id: number) {
  return defHttp.delete({ url: `/ota/tasks/delete?id=${id}` })
}

// 导出OTA升级任务 Excel
export function exportOtaTasks(params) {
  return defHttp.download({ url: '/ota/tasks/export-excel', params }, 'OTA升级任务.xls')
}
