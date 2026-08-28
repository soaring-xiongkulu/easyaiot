import { defHttp } from '@/utils/http/axios'

/** 匹配操作符 */
export type AlertMatchOp = 'EQ' | 'NE' | 'IN' | 'PREFIX' | 'REGEX'

/** 单条匹配条件：field 取告警快照字段（object/event/taskType/taskId/taskName/deviceId/deviceName/nodeId/edgeNodeId） */
export interface AlertMatchCondition {
  field: string
  op: AlertMatchOp
  value: string
}

/** 告警→流程 路由规则 */
export interface FlowAlertRouteRuleVO {
  id?: number
  ruleName: string
  priority: number
  processDefinitionKey: string
  matchConditions: AlertMatchCondition[]
  dedupWindowSeconds: number
  enabled: boolean
  startUserId?: number
  remark?: string
  createTime?: string
}

// 规则列表
export function getAlertRouteRuleList(params?: { ruleName?: string; enabled?: boolean }) {
  return defHttp.get({ url: '/flow/alert-route-rule/list', params })
}

// 规则分页
export function getAlertRouteRulePage(params: PageParam & { ruleName?: string; enabled?: boolean }) {
  return defHttp.get({ url: '/flow/alert-route-rule/page', params })
}

// 创建规则
export function createAlertRouteRule(data: FlowAlertRouteRuleVO) {
  return defHttp.post({ url: '/flow/alert-route-rule/create', data })
}

// 修改规则
export function updateAlertRouteRule(data: FlowAlertRouteRuleVO) {
  return defHttp.put({ url: '/flow/alert-route-rule/update', data })
}

// 启用/停用规则
export function updateAlertRouteRuleEnabled(id: number, enabled: boolean) {
  return defHttp.put({ url: '/flow/alert-route-rule/update-enabled', data: { id, enabled } })
}

// 删除规则
export function deleteAlertRouteRule(id: number) {
  return defHttp.delete({ url: `/flow/alert-route-rule/delete?id=${id}` })
}

// 规则试匹配（传告警样例，返回命中的规则）
export function previewAlertRouteMatch(data: Recordable) {
  return defHttp.post({ url: '/flow/alert-route-rule/preview-match', data })
}
