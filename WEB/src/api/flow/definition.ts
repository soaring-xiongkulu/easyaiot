import { defHttp } from '@/utils/http/axios'
import type { FlowDefinitionVO } from './model'

export interface FlowDefinitionPageReqVO extends PageParam {
  key?: string
  name?: string
  category?: string
}

// 查询流程定义分页（已部署）
export function getProcessDefinitionPage(params: FlowDefinitionPageReqVO) {
  return defHttp.get({ url: '/flow/process-definition/page', params })
}

// 查询流程定义列表（不分页）
export function getProcessDefinitionList(params?: { key?: string; name?: string; suspensionState?: number }) {
  return defHttp.get({ url: '/flow/process-definition/list', params })
}

// 查询流程定义精简列表（下拉用）
export function getSimpleProcessDefinitionList() {
  return defHttp.get({ url: '/flow/process-definition/simple-list' })
}

// 查询流程定义详情
export function getProcessDefinition(id?: string, key?: string) {
  const params: Recordable = {}
  if (id) params.id = id
  if (key) params.key = key
  return defHttp.get({ url: '/flow/process-definition/get', params })
}

export type { FlowDefinitionVO }
