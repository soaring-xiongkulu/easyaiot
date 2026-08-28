import { defHttp } from '@/utils/http/axios'

/** 流程实例状态：1 审批中 / 2 审批通过 / 3 审批不通过 / 4 已取消 */
export type ProcessInstanceStatus = -1 | 1 | 2 | 3 | 4

export interface FlowProcessInstanceVO {
  id: string
  name: string
  startUserId: number
  startUserNickname?: string
  processDefinitionId: string
  processDefinitionKey?: string
  processDefinitionName?: string
  categoryId?: string
  status: ProcessInstanceStatus
  reason?: string
  businessKey?: string
  taskName?: string
  tasks?: any[]
  startTime: string
  endTime?: string
  durationInMillis?: number
  processVariables?: Recordable
  summary?: { key: string; value: string }[]
}

export interface FlowProcessInstancePageReqVO extends PageParam {
  name?: string
  processDefinitionKey?: string
  categoryId?: string
  status?: number
  createTime?: string[]
}

// 新建流程实例（用户自发起，P1 通用审批）
export function createProcessInstance(data: {
  processDefinitionId?: string
  processDefinitionKey?: string
  variables?: Recordable
  startUserSelectAssignees?: Recordable
}) {
  return defHttp.post({ url: '/flow/process-instance/create', data })
}

// 我发起的流程实例分页
export function getMyProcessInstancePage(params: FlowProcessInstancePageReqVO) {
  return defHttp.get({ url: '/flow/process-instance/my-page', params })
}

// 管理员查询全部流程实例分页
export function getManagerProcessInstancePage(params: FlowProcessInstancePageReqVO) {
  return defHttp.get({ url: '/flow/process-instance/manager-page', params })
}

// 查询流程实例详情
export function getProcessInstance(id: string) {
  return defHttp.get({ url: `/flow/process-instance/get?id=${id}` })
}

// 发起人取消流程实例
export function cancelProcessInstanceByStartUser(id: string, reason: string) {
  return defHttp.delete({ url: '/flow/process-instance/cancel-by-start-user', data: { id, reason } })
}

// 管理员终止流程实例
export function cancelProcessInstanceByAdmin(id: string, reason: string) {
  return defHttp.delete({ url: '/flow/process-instance/cancel-by-admin', data: { id, reason } })
}

// 审批详情聚合接口（流程实例 + 节点审批进度 + 表单字段权限）
export function getApprovalDetail(params: { id: string; taskId?: string; activityId?: string }) {
  return defHttp.get({ url: '/flow/process-instance/get-approval-detail', params })
}

// Simple 模型运行视图（含节点染色 ID 集合）
export function getProcessInstanceBpmnModelView(id: string) {
  return defHttp.get({ url: '/flow/process-instance/get-bpmn-model-view', params: { id } })
}

// 预测下一审批节点（发起前校验用）
export function getNextApprovalNodes(params: { processDefinitionId: string; activityId?: string; variables?: Recordable }) {
  return defHttp.get({ url: '/flow/process-instance/get-next-approval-nodes', params })
}

// 抄送我的分页
export function getProcessInstanceCopyPage(params: PageParam & { processInstanceName?: string; createTime?: string[] }) {
  return defHttp.get({ url: '/flow/process-instance/copy/page', params })
}
