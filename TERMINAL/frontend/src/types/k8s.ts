export interface K8sContextInfo {
  name: string
  cluster: string
  user: string
  namespace: string
  current: boolean
}

export interface K8sResponse {
  status: number
  body: string
}

export interface K8sTab {
  type: 'k8s'
  id: string
  panelId: string
  name: string
  connectionId: string   // 对应 connections.json 里的 ConnectionConfig.id
  connId: string | null  // 后端 k8sManager 返回的连接 ID（连接建立后填）
  namespace: string      // '' = all namespaces
  locked?: boolean
}

// Watch 事件通用形状。
export interface K8sWatchEvent {
  type: 'ADDED' | 'MODIFIED' | 'DELETED' | 'BOOKMARK'
  object: any
}

export interface ParsedCRD {
  group: string
  version: string
  plural: string
  kind: string
  scope: 'Namespaced' | 'Cluster'
  printerColumns: { name: string; jsonPath: string; type?: string }[]
}

export type NavFrame =
  | { kind: 'list'; resourceKey: string; namespace: string }
  | { kind: 'owned'; resourceKey: string; ownerKind: string; ownerName: string; ownerUid: string; namespace: string }
  | { kind: 'custom'; crd: ParsedCRD; namespace: string }
