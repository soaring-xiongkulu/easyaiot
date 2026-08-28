import { defHttp } from '@/utils/http/axios'

/** 告警处理记录状态（对齐流程实例状态）：1 处理中 / 2 已处理(通过) / 3 已关闭(误报-拒绝) / 4 已取消 */
export type AlertRecordStatus = 1 | 2 | 3 | 4

export interface FlowAlertRecordVO {
  id: number
  alertId: number
  alertSource: string
  alertSnapshot?: Recordable
  processInstanceId?: string
  processDefinitionKey?: string
  processInstanceStatus: AlertRecordStatus
  currentTaskName?: string
  currentAssignees?: string
  finishTime?: string
  createTime?: string
}

export interface FlowAlertRecordPageReqVO extends PageParam {
  alertId?: number
  alertSource?: string
  processInstanceStatus?: number
  createTime?: string[]
}

// 告警处理记录分页
export function getAlertRecordPage(params: FlowAlertRecordPageReqVO) {
  return defHttp.get({ url: '/flow/alert-record/page', params })
}

// 我负责的告警处理记录分页（当前责任人是登录用户）
export function getMyAlertRecordPage(params: FlowAlertRecordPageReqVO) {
  return defHttp.get({ url: '/flow/alert-record/my-page', params })
}

// 按告警 ID 批量查询处理状态（告警列表页聚合标签）
export function listAlertRecordByAlertIds(alertIds: number[]) {
  return defHttp.get({ url: '/flow/alert-record/list-by-alert-ids', params: { alertIds: alertIds.join(',') } })
}

// 手动为存量告警发起处理流程
export function triggerAlertRecord(data: { alertId: number; processDefinitionKey: string }) {
  return defHttp.post({ url: '/flow/alert-record/trigger', data })
}

// 告警处理记录详情
export function getAlertRecord(id: number) {
  return defHttp.get({ url: `/flow/alert-record/get?id=${id}` })
}
