import { http } from '@/http/http'

export interface ComputeNode {
  id: number
  name: string
  host: string
  status?: string
  nodeRole?: string
  functions?: string[]
}

export interface NodePageResult {
  list?: ComputeNode[]
  total?: number
}

/** 获取在线计算节点分页 */
export function getNodePage(params?: { pageNo?: number, pageSize?: number, status?: string }) {
  return http.get<NodePageResult>('/node/page', params)
}
