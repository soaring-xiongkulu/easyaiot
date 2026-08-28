import { defHttp } from '@/utils/http/axios'

/** 任务状态：-2 跳过 / 0 待审批 / 1 审批中(多实例) / 2 审批通过 / 3 审批不通过 / 4 已取消 / 5 退回 */
export type FlowTaskStatus = -2 | 0 | 1 | 2 | 3 | 4 | 5 | 7

export interface FlowTaskVO {
  id: string
  name: string
  processInstanceId: string
  processInstanceName?: string
  processDefinitionKey?: string
  processDefinitionName?: string
  assigneeUser?: { id: number; nickname: string; avatar?: string; deptName?: string }
  ownerUser?: { id: number; nickname: string }
  status: FlowTaskStatus
  reason?: string
  create_time?: string
  createTime?: string
  endTime?: string
  durationInMillis?: number
  summary?: { key: string; value: string }[]
  startUser?: { id: number; nickname: string; avatar?: string }
}

export interface FlowTaskPageReqVO extends PageParam {
  name?: string
  processInstanceName?: string
  createTime?: string[]
}

// 待办任务分页
export function getTaskTodoPage(params: FlowTaskPageReqVO) {
  return defHttp.get({ url: '/flow/task/todo-page', params })
}

// 已办任务分页
export function getTaskDonePage(params: FlowTaskPageReqVO) {
  return defHttp.get({ url: '/flow/task/done-page', params })
}

// 管理员任务分页
export function getTaskManagerPage(params: FlowTaskPageReqVO) {
  return defHttp.get({ url: '/flow/task/manager-page', params })
}

// 待办数量（角标轮询）
export function getTaskTodoCount() {
  return defHttp.get({ url: '/flow/task/todo-count' })
}

// 通过审批
export function approveTask(data: { id: string; reason?: string; variables?: Recordable }) {
  return defHttp.put({ url: '/flow/task/approve', data })
}

// 拒绝审批
export function rejectTask(data: { id: string; reason?: string }) {
  return defHttp.put({ url: '/flow/task/reject', data })
}

// 退回到指定节点
export function returnTask(data: { id: string; targetTaskDefinitionKey: string; reason: string }) {
  return defHttp.put({ url: '/flow/task/return', data })
}

// 委派任务
export function delegateTask(data: { id: string; assigneeUserId: number; reason?: string }) {
  return defHttp.put({ url: '/flow/task/delegate', data })
}

// 转办任务
export function transferTask(data: { id: string; assigneeUserId: number; reason?: string }) {
  return defHttp.put({ url: '/flow/task/transfer', data })
}

// 加签（在当前任务前后追加临时审批人）
export function createSignTask(data: { id: string; userIds: number[]; type: 'AFTER' | 'BEFORE'; reason: string }) {
  return defHttp.put({ url: '/flow/task/create-sign', data })
}

// 减签
export function deleteSignTask(data: { id: string; reason: string }) {
  return defHttp.put({ url: '/flow/task/delete-sign', data })
}

// 抄送任务
export function copyTask(data: { id: string; userIds: number[]; reason?: string }) {
  return defHttp.put({ url: '/flow/task/copy', data })
}

// 撤回已审批任务（下一节点未审批前）
export function withdrawTask(data: { id: string; reason: string }) {
  return defHttp.put({ url: '/flow/task/withdraw', data })
}

// 查询流程实例的任务列表
export function getTaskListByProcessInstanceId(processInstanceId: string) {
  return defHttp.get({ url: '/flow/task/list-by-process-instance-id', params: { processInstanceId } })
}

// 查询可退回的节点列表
export function getTaskListByReturn(id: string) {
  return defHttp.get({ url: '/flow/task/list-by-return', params: { id } })
}
