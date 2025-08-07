import { defHttp } from '@/utils/http/axios'

// 查询规则条件列表
export function getRuleConditionsPage(params) {
  return defHttp.get({ url: '/rule/conditions/page', params })
}

// 查询规则条件详情
export function getRuleConditions(id: number) {
  return defHttp.get({ url: `/rule/conditions/get?id=${id}` })
}

// 新增规则条件
export function createRuleConditions(data) {
  return defHttp.post({ url: '/rule/conditions/create', data })
}

// 修改规则条件
export function updateRuleConditions(data) {
  return defHttp.put({ url: '/rule/conditions/update', data })
}

// 删除规则条件
export function deleteRuleConditions(id: number) {
  return defHttp.delete({ url: `/rule/conditions/delete?id=${id}` })
}

// 导出规则条件 Excel
export function exportRuleConditions(params) {
  return defHttp.download({ url: '/rule/conditions/export-excel', params }, '规则条件.xls')
}
