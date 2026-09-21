export interface ContainerInfo {
  id: string
  name: string
  image: string
  state: string
  status: string
  ports: string
  createdAt: string
}

export interface PortMapping {
  hostIp?: string
  hostPort: string
  containerPort: string
  protocol: string
}

export interface ContainerMount {
  source: string
  destination: string
  rw: boolean
}

export interface ContainerDetail {
  id: string
  name: string
  image: string
  state: string
  status: string
  startedAt: string
  finishedAt: string
  exitCode?: number
  oomKilled: boolean
  pid: number
  restartPolicy: string
  entrypoint: string
  command: string
  workDir: string
  user: string
  networkMode: string
  ip: string
  gateway: string
  ports: PortMapping[]
  mounts: ContainerMount[]
  env: string[]
}

export interface InspectResult {
  detail: ContainerDetail
  raw: string
}

export interface ContainerImage {
  id: string
  repository: string
  tag: string
  size: string
  createdAt: string
}

export interface ContainerStats {
  id: string
  name: string
  cpuPercent: string
  memUsage: string
  memPercent: string
  netIO: string
  blockIO: string
}

export interface ContainerCreateOptions {
  image: string
  name: string
  ports: PortMapping[]
  volumes: string[]
  env: string[]
  restart: string
  command: string[]
}

export interface ContainerTab {
  type: 'container'
  id: string
  panelId: string
  name: string
  connectionId: string // 保存的连接配置 ID（= 后端 conn key）
  runtime: 'docker' | 'podman' | 'nerdctl' | 'wslc'
  locked?: boolean
}
