import { defHttp } from '@/utils/http/axios'

// 查询规则告警列表
export function getRuleAlarmPage(params) {
  return defHttp.get({ url: '/rule/alarm/page', params })
}

// 查询规则告警详情
export function getRuleAlarm(id: number) {
  return defHttp.get({ url: `/rule/alarm/get?id=${id}` })
}

// 新增规则告警
export function createRuleAlarm(data) {
  return defHttp.post({ url: '/rule/alarm/create', data })
}

// 修改规则告警
export function updateRuleAlarm(data) {
  return defHttp.put({ url: '/rule/alarm/update', data })
}

// 删除规则告警
export function deleteRuleAlarm(id: number) {
  return defHttp.delete({ url: `/rule/alarm/delete?id=${id}` })
}

// 导出规则告警 Excel
export function exportRuleAlarm(params) {
  return defHttp.download({ url: '/rule/alarm/export-excel', params }, '规则告警.xls')
}
