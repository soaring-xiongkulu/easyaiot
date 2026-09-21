export interface EsIndexInfo {
  name: string
  health: string
  status: string
  docsCount: number
  storeSize: string
  pri: number
  rep: number
}

export interface EsClusterHealth {
  clusterName: string
  status: string
  numberOfNodes: number
  numberOfDataNodes: number
  activePrimaryShards: number
  activeShards: number
  relocatingShards: number
  initializingShards: number
  unassignedShards: number
}

export interface EsClusterInfo {
  name: string
  clusterName: string
  clusterUUID: string
  version: string
  tagline: string
}

export interface EsSearchResult {
  hits: string[]
  total: number
  from: number
  size: number
  took: number
}

export interface EsRestResult {
  status: number
  body: string
}
