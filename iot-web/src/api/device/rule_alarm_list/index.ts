import { defHttp } from '@/utils/http/axios'

// 查询告警规则列列表
export function getRuleAlarmListPage(params) {
  return defHttp.get({ url: '/rule/alarm-list/page', params })
}

// 查询告警规则列详情
export function getRuleAlarmList(id: number) {
  return defHttp.get({ url: `/rule/alarm-list/get?id=${id}` })
}

// 新增告警规则列
export function createRuleAlarmList(data) {
  return defHttp.post({ url: '/rule/alarm-list/create', data })
}

// 修改告警规则列
export function updateRuleAlarmList(data) {
  return defHttp.put({ url: '/rule/alarm-list/update', data })
}

// 删除告警规则列
export function deleteRuleAlarmList(id: number) {
  return defHttp.delete({ url: `/rule/alarm-list/delete?id=${id}` })
}

// 导出告警规则列 Excel
export function exportRuleAlarmList(params) {
  return defHttp.download({ url: '/rule/alarm-list/export-excel', params }, '告警规则列.xls')
}
