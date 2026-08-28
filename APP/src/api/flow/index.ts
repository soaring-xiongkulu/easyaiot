import { http } from '@/http/http'

/** FLOW 工作流接口（与 PC 共用 /admin-api/flow/**，见后端 FlowTaskController / FlowAlertRecordController / FlowProcessInstanceController） */

export interface FlowUserVO {
  id: number
  nickname?: string
}

export interface FlowTaskVO {
  id: string
  name?: string
  processInstanceId: string
  processInstanceName?: string
  processDefinitionKey?: string
  processDefinitionName?: string
  assigneeUser?: FlowUserVO
  ownerUser?: FlowUserVO
  /** -2 跳过 / 0 待审批 / 1 审批中(多实例) / 2 通过 / 3 拒绝 / 4 已取消 / 5 已退回 / 7 审批中 */
  status?: number
  reason?: string
  createTime?: string
  endTime?: string
  durationInMillis?: number
  startUser?: FlowUserVO
}

export interface FlowAlertRecordVO {
  id: number
  alertId?: number
  alertSource?: string
  alertSnapshot?: Record<string, any>
  processInstanceId?: string
  processDefinitionKey?: string
  /** 1 审批中 / 2 通过 / 3 拒绝 / 4 已取消 */
  processInstanceStatus?: number
  currentTaskName?: string
  currentAssignees?: string
  finishTime?: string
  createTime?: string
}

export interface FlowProcessInstanceVO {
  id: string
  name?: string
  startUserId?: number
  startUserNickname?: string
  processDefinitionId?: string
  processDefinitionKey?: string
  processDefinitionName?: string
  categoryId?: string
  /** 1 审批中 / 2 通过 / 3 不通过 / 4 已取消 */
  status?: number
  reason?: string
  businessKey?: string
  taskName?: string
  startTime?: string
  endTime?: string
  durationInMillis?: number
  processVariables?: Record<string, any>
}

export interface FlowActivityNodeTask {
  id: string
  name?: string
  assigneeUser?: FlowUserVO
  status?: number
  reason?: string
  createTime?: string
  endTime?: string
}

export interface FlowActivityNode {
  id: string
  name?: string
  nodeType?: number
  tasks?: FlowActivityNodeTask[]
}

export interface FlowApprovalDetail {
  processInstance: FlowProcessInstanceVO
  activityNodes?: FlowActivityNode[]
}

export interface FlowCopyVO {
  id: number
  processInstanceId: string
  processInstanceName?: string
  category?: string
  taskId?: string
  taskName?: string
  activityId?: string
  startUserId?: number
  reason?: string
  userId?: number
  createTime?: string
}

export interface FlowPageResult<T> {
  list: T[]
  total: number
}

export interface FlowTaskPageParams {
  pageNo?: number
  pageSize?: number
  name?: string
  processInstanceName?: string
}

export interface FlowAlertRecordPageParams {
  pageNo?: number
  pageSize?: number
  alertId?: number
  alertSource?: string
  processInstanceStatus?: number
}

/** 待办任务分页 */
export function getFlowTodoPage(params: FlowTaskPageParams) {
  return http.get<FlowPageResult<FlowTaskVO>>('/flow/task/todo-page', params)
}

/** 已办任务分页 */
export function getFlowDonePage(params: FlowTaskPageParams) {
  return http.get<FlowPageResult<FlowTaskVO>>('/flow/task/done-page', params)
}

/** 待办任务数量（角标） */
export function getFlowTodoCount() {
  return http.get<number>('/flow/task/todo-count')
}

/** 通过审批 */
export function approveFlowTask(data: { id: string, reason?: string }) {
  return http.put<boolean>('/flow/task/approve', data)
}

/** 拒绝审批 */
export function rejectFlowTask(data: { id: string, reason?: string }) {
  return http.put<boolean>('/flow/task/reject', data)
}

/** 告警处理记录分页 */
export function getFlowAlertRecordPage(params: FlowAlertRecordPageParams) {
  return http.get<FlowPageResult<FlowAlertRecordVO>>('/flow/alert-record/page', params)
}

/** 我负责的告警处理记录分页 */
export function getMyFlowAlertRecordPage(params: FlowAlertRecordPageParams) {
  return http.get<FlowPageResult<FlowAlertRecordVO>>('/flow/alert-record/my-page', params)
}

/** 告警处理记录详情 */
export function getFlowAlertRecord(id: number) {
  return http.get<FlowAlertRecordVO>('/flow/alert-record/get', { id })
}

/** 审批详情聚合（实例 + 节点审批进度） */
export function getFlowApprovalDetail(id: string, taskId?: string) {
  return http.get<FlowApprovalDetail>('/flow/process-instance/get-approval-detail', { id, taskId })
}

/** 抄送我的分页 */
export function getFlowCopyPage(params: { pageNo?: number, pageSize?: number, processInstanceName?: string }) {
  return http.get<FlowPageResult<FlowCopyVO>>('/flow/process-instance/copy/page', params)
}

// ==================== 状态展示 ====================

/** 任务状态文案 */
export function formatFlowTaskStatus(status?: number): string {
  switch (status) {
    case -2: return '已跳过'
    case 0: return '待审批'
    case 1:
    case 7: return '审批中'
    case 2: return '已通过'
    case 3: return '已拒绝'
    case 4: return '已取消'
    case 5: return '已退回'
    default: return '-'
  }
}

/** 任务状态 tag 类型（wd-tag） */
export function getFlowTaskStatusType(status?: number): 'success' | 'error' | 'warning' | 'info' | 'primary' {
  switch (status) {
    case 2: return 'success'
    case 3: return 'error'
    case 4: return 'info'
    case 5: return 'warning'
    case 0: return 'warning'
    default: return 'primary'
  }
}

/** 实例状态文案 */
export function formatFlowInstanceStatus(status?: number): string {
  switch (status) {
    case 1: return '审批中'
    case 2: return '已通过'
    case 3: return '已拒绝'
    case 4: return '已取消'
    default: return '-'
  }
}

export function getFlowInstanceStatusType(status?: number): 'success' | 'error' | 'warning' | 'info' | 'primary' {
  switch (status) {
    case 1: return 'primary'
    case 2: return 'success'
    case 3: return 'error'
    case 4: return 'info'
    default: return 'info'
  }
}

/** 解析站内信 deepLink（约定 flow://instance/{processInstanceId}?taskId={taskId}，Flowable ID 为 UUID） */
export function parseFlowDeepLink(content?: string): { processInstanceId: string, taskId?: string } | null {
  if (!content) return null
  const match = content.match(/flow:\/\/instance\/([A-Za-z0-9-]+)(?:\?taskId=([A-Za-z0-9-]+))?/)
  if (!match) return null
  return { processInstanceId: match[1], taskId: match[2] }
}

/** 耗时格式化（毫秒 → x天x小时x分） */
export function formatFlowDuration(ms?: number): string {
  if (!ms || ms <= 0) return '-'
  const totalMinutes = Math.floor(ms / 60000)
  if (totalMinutes < 1) return '少于1分钟'
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  const parts: string[] = []
  if (days) parts.push(`${days}天`)
  if (hours) parts.push(`${hours}小时`)
  if (minutes) parts.push(`${minutes}分钟`)
  return parts.join('')
}
