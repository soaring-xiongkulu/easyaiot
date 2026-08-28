import { defHttp } from '@/utils/http/axios'

/** 流程模型 VO（对应 iot-flow flow_process_definition_info / Flowable ACT_RE_MODEL 扩展） */
export interface FlowModelVO {
  id: string
  formType: number
  formConf?: string
  formFields?: string[]
  formCustomCreatePath?: string
  formCustomViewPath?: string
  icon?: string
  description?: string
  type: number
  simpleModel?: any
  category?: string
  name: string
  key: string
  startUserIds?: number[]
  managerUserIds?: number[]
  processDefinition?: FlowDefinitionVO
}

export interface FlowDefinitionVO {
  id: string
  key: string
  name: string
  version: number
  state?: string
  suspensionState?: number
  deploymentTime?: string
  modelId?: string
}

export interface FlowModelPageReqVO extends PageParam {
  key?: string
  name?: string
  category?: string
}

// 查询流程模型分页
export function getModelPage(params: FlowModelPageReqVO) {
  return defHttp.get({ url: '/flow/model/page', params })
}

// 查询流程模型详情
export function getModel(id: string) {
  return defHttp.get({ url: `/flow/model/get?id=${id}` })
}

// 新建流程模型
export function createModel(data: Partial<FlowModelVO>) {
  return defHttp.post({ url: '/flow/model/create', data })
}

// 修改流程模型基本信息
export function updateModel(data: Partial<FlowModelVO>) {
  return defHttp.put({ url: '/flow/model/update', data })
}

// 修改流程模型 Simple 设计器 JSON
export function updateModelSimple(data: { id: string; simpleModel: any }) {
  return defHttp.put({ url: '/flow/model/simple/update', data })
}

// 读取流程模型 Simple 设计器 JSON
export function getModelSimple(id: string) {
  return defHttp.get({ url: `/flow/model/simple/get?id=${id}` })
}

// 部署流程模型
export function deployModel(id: string) {
  return defHttp.post({ url: `/flow/model/deploy?id=${id}` })
}

// 修改模型状态（挂起/激活）
export function updateModelState(id: string, state: number) {
  return defHttp.put({ url: '/flow/model/update-state', data: { id, state } })
}

// 删除流程模型
export function deleteModel(id: string) {
  return defHttp.delete({ url: `/flow/model/delete?id=${id}` })
}

// 复制流程模型
export function copyModel(id: string) {
  return defHttp.post({ url: `/flow/model/copy?id=${id}` })
}
