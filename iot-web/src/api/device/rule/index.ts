import { defHttp } from '@/utils/http/axios'

// 查询规则信息列表
export function getRulePage(params) {
  return defHttp.get({ url: '/rule/page', params })
}

// 查询规则信息详情
export function getRule(id: number) {
  return defHttp.get({ url: `/rule/get?id=${id}` })
}

// 新增规则信息
export function createRule(data) {
  return defHttp.post({ url: '/rule/create', data })
}

// 修改规则信息
export function updateRule(data) {
  return defHttp.put({ url: '/rule/update', data })
}

// 删除规则信息
export function deleteRule(id: number) {
  return defHttp.delete({ url: `/rule/delete?id=${id}` })
}

// 导出规则信息 Excel
export function exportRule(params) {
  return defHttp.download({ url: '/rule/export-excel', params }, '规则信息.xls')
}
