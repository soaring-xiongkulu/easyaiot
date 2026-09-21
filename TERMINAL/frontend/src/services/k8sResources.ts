// ResourceDescriptor 表驱动 K8sTree + K8sResourceList。
// 每种资源在这里加一条，不写新组件。

import { parseCpu, parseMemory, formatCpu, formatMemory, percent } from './k8sQuantity'

export interface ColoredCell { text: string; tone?: 'ok' | 'warn' | 'err' }

// 指标列需要该行的实时用量（cpu 毫核 / mem 字节），由 K8sResourceList 从
// metricsMap 注入；纯对象列忽略第二参数。
export interface RowUsage { cpu: number; mem: number }

export interface ColumnDef {
  header: string
  value: (obj: any, usage?: RowUsage | null) => string | number | ColoredCell
  width?: number
  filterable?: { type: 'enum' }
  // 顶部筛选框会匹配该列文本（除 name 外，name 始终参与）。
  searchable?: boolean
  // 排序数值：带单位/百分比等文本列（cpu 毫核、内存字节等）返回可比数字，
  // 优先于文本比较，避免 "10m" < "2m" 这类字母序错误。
  sortValue?: (obj: any, usage?: RowUsage | null) => number
}

export type ResourceGroup = 'workloads' | 'network' | 'config' | 'storage' | 'rbac' | 'cluster'

export type ResourceAction =
  | 'detail' | 'delete' | 'restart' | 'scale' | 'viewPods' | 'logs' | 'terminal' | 'cordon' | 'drain'

export interface DetailField {
  label: string
  value: (obj: any) => string | { text: string; color?: string }
  link?: (obj: any) => void
}
export interface DetailSection { label: string; fields: DetailField[] }

export interface ResourceDescriptor {
  key: string
  kind: string
  apiVersion: string
  namespaced: boolean
  group: ResourceGroup
  icon: string          // lucide 图标名
  label: string
  listPath: (ns: string) => string
  watchPath: (ns: string, rv: string) => string
  columns: ColumnDef[]
  actions?: ResourceAction[]
  detailSections?: DetailSection[]
  canCreate?: boolean
  createTemplate?: (ns: string) => string
  createPath?: (ns: string) => string
  metrics?: 'pod' | 'node'
  // 行健康度：返回 'warn'/'err' 时整行着色（对齐 k9s 高亮非就绪项）；
  // 返回 '' / undefined 表示正常。
  rowTone?: (obj: any) => '' | 'warn' | 'err'
}

// ── 通用列生成器 ────────────────────────────────────────────────

export function age(ts: string | undefined): string {
  if (!ts) return '—'
  const diff = Date.now() - new Date(ts).getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  return `${Math.floor(h / 24)}d`
}

function podReady(p: any): string {
  const cs = p.status?.containerStatuses || []
  const ready = cs.filter((c: any) => c.ready).length
  return `${ready}/${cs.length}`
}

function podRestarts(p: any): number {
  const cs = p.status?.containerStatuses || []
  return cs.reduce((sum: number, c: any) => sum + (c.restartCount || 0), 0)
}

// pod 各容器 requests/limits 的合计（cpu 毫核 / mem 字节）。
function podResourceTotals(p: any): { cpuReq: number; cpuLim: number; memReq: number; memLim: number } {
  let cpuReq = 0, cpuLim = 0, memReq = 0, memLim = 0
  for (const c of p.spec?.containers || []) {
    cpuReq += parseCpu(c.resources?.requests?.cpu || '')
    cpuLim += parseCpu(c.resources?.limits?.cpu || '')
    memReq += parseMemory(c.resources?.requests?.memory || '')
    memLim += parseMemory(c.resources?.limits?.memory || '')
  }
  return { cpuReq, cpuLim, memReq, memLim }
}

// k9s 风格的 pod 状态：优先反映容器/初始化异常，而非只看 phase。
function podStatus(p: any): string {
  if (p.metadata?.deletionTimestamp) return 'Terminating'
  const reason = p.status?.reason
  if (reason) return reason
  const css = p.status?.containerStatuses || []
  for (const cs of css) {
    const w = cs.state?.waiting?.reason
    const term = cs.state?.terminated?.reason
    if (w && w !== 'ContainerCreating') return w
    if (term && term !== 'Completed') return term
  }
  return p.status?.phase || ''
}

// pod 行健康度：Running/Succeeded 且容器全就绪为正常；否则告警/错误。
function podTone(p: any): '' | 'warn' | 'err' {
  if (p.metadata?.deletionTimestamp) return 'warn'
  const st = podStatus(p)
  if (st === 'Running' || st === 'Completed' || st === 'Succeeded') {
    const cs = p.status?.containerStatuses || []
    if (cs.length && !cs.every((c: any) => c.ready) && st === 'Running') return 'warn'
    return ''
  }
  if (st === 'Pending' || st === 'ContainerCreating' || st === 'PodInitializing') return 'warn'
  return 'err'
}

// 副本类工作负载：ready < desired 视为告警。
function replicaTone(ready: number, desired: number): '' | 'warn' | 'err' {
  if (desired > 0 && ready < desired) return ready === 0 ? 'err' : 'warn'
  return ''
}

// duration between two ISO timestamps, formatted like age().
function durationBetween(start?: string, end?: string): string {
  if (!start) return '—'
  const s = new Date(start).getTime()
  const e = end ? new Date(end).getTime() : Date.now()
  const diff = Math.floor((e - s) / 1000)
  if (diff < 0) return '—'
  if (diff < 60) return `${diff}s`
  const m = Math.floor(diff / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  return `${Math.floor(h / 24)}d`
}

// k9s Service ports 格式：`name:port►nodePort╱protocol`，多个用空格分隔。
function servicePorts(s: any): string {
  return (s.spec?.ports || []).map((p: any) => {
    const name = p.name ? `${p.name}:` : ''
    const proto = (p.protocol && p.protocol !== 'TCP') ? `╱${p.protocol}` : ''
    return `${name}${p.port}►${p.nodePort || 0}${proto}`
  }).join(' ')
}

// NetworkPolicy ingress/egress 的端口与 block CIDR 提取。
function npPorts(rules: any[]): string {
  const set = new Set<string>()
  for (const r of rules || []) for (const p of r.ports || []) set.add(`${p.port ?? '*'}/${p.protocol || 'TCP'}`)
  return Array.from(set).join(',') || '—'
}
function npBlocks(rules: any[], peerKey: string): string {
  const set = new Set<string>()
  for (const r of rules || []) for (const peer of r[peerKey] || []) if (peer.ipBlock?.cidr) set.add(peer.ipBlock.cidr)
  return Array.from(set).join(',') || '—'
}

function kv(obj: Record<string, any> | undefined): string {
  return Object.entries(obj || {}).map(([k, v]) => `${k}=${v}`).join('\n') || '—'
}

// ResourceQuota 的 requests.*/limits.* 用量，形如 `cpu: 2/4`。
function quotaByPrefix(q: any, prefix: string): string {
  const used = q.status?.used || {}
  const hard = q.status?.hard || {}
  const keys = Object.keys(hard).filter(k => k.startsWith(prefix))
  return keys.map(k => `${k.slice(prefix.length)}: ${used[k] ?? 0}/${hard[k]}`).join(', ') || '—'
}
function quotaRequest(q: any): string { return quotaByPrefix(q, 'requests.') }
function quotaLimit(q: any): string { return quotaByPrefix(q, 'limits.') }

// RBAC 规则简表：`apiGroups|resources → verbs`，逐行。
function rbacRules(o: any): string {
  return (o.rules || []).map((r: any) => {
    const groups = (r.apiGroups || ['']).map((g: string) => g || 'core').join(',')
    const res = (r.resources || []).join(',')
    const verbs = (r.verbs || []).join(',')
    return `${groups}/${res} → ${verbs}`
  }).join('\n') || '—'
}

// RBAC 主体简表：`Kind/name`，逐行。
function rbacSubjects(o: any): string {
  return (o.subjects || []).map((s: any) => `${s.kind}/${s.namespace ? s.namespace + ':' : ''}${s.name}`).join('\n') || '—'
}

// 通用 Metadata 详情段，供各资源的 detailSections 复用。
function metaSection(): DetailSection {
  return { label: 'Metadata', fields: [
    { label: 'Name', value: (o: any) => o.metadata?.name || '' },
    { label: 'Namespace', value: (o: any) => o.metadata?.namespace || 'cluster' },
    { label: 'UID', value: (o: any) => o.metadata?.uid || '' },
    { label: 'Created', value: (o: any) => o.metadata?.creationTimestamp || '' },
    { label: 'Labels', value: (o: any) => kv(o.metadata?.labels) },
    { label: 'Annotations', value: (o: any) => kv(o.metadata?.annotations) },
    { label: 'Owner', value: (o: any) => (o.metadata?.ownerReferences || []).map((r: any) => `${r.kind}/${r.name}`).join(', ') || '—' },
  ] }
}

// metaSection + 额外字段段，减少各资源重复。
function withMeta(...sections: DetailSection[]): DetailSection[] {
  return [metaSection(), ...sections]
}

// 资源未定义 detailSections 时的兜底：完整 Metadata + 常见 Spec/Status 概要。
export function genericDetailSections(): DetailSection[] {
  return [
    metaSection(),
    { label: 'Status', fields: [
      { label: 'Phase', value: (o: any) => o.status?.phase || o.status?.state || '—' },
      { label: 'Conditions', value: (o: any) => (o.status?.conditions || []).map((c: any) => `${c.type}=${c.status}`).join('\n') || '—' },
    ] },
  ]
}

// 工作负载（Deployment/StatefulSet/DaemonSet/ReplicaSet）通用的 Spec + Status 段。
function selectorText(o: any): string {
  return kv(o.spec?.selector?.matchLabels)
}

// Endpoints 展开为 `ip:port,ip:port,...`（address × port 笛卡尔积）。
function endpointsText(e: any): string {
  const out: string[] = []
  for (const s of e.subsets || []) {
    const ports = (s.ports || []).map((p: any) => p.port)
    for (const a of s.addresses || []) {
      if (ports.length) for (const p of ports) out.push(`${a.ip}:${p}`)
      else out.push(a.ip)
    }
  }
  return out.join(',') || '<none>'
}

// HPA current/target 指标，形如 `cpu: 40%/80%`；多指标用逗号分隔。
function hpaTargets(h: any): string {
  const cur = new Map<string, string>()
  for (const m of h.status?.currentMetrics || []) {
    if (m.resource) cur.set(m.resource.name, m.resource.current?.averageUtilization != null ? `${m.resource.current.averageUtilization}%` : (m.resource.current?.averageValue || '?'))
  }
  const specs = (h.spec?.metrics || []).map((m: any) => {
    if (m.resource) {
      const tgt = m.resource.target?.averageUtilization != null ? `${m.resource.target.averageUtilization}%` : (m.resource.target?.averageValue || '?')
      return `${cur.get(m.resource.name) || '?'}/${tgt}`
    }
    return '?'
  })
  return specs.join(',') || '<none>'
}

// ── 路径 helper ────────────────────────────────────────────────

function coreListPath(plural: string, ns: string): string {
  return ns
    ? `/api/v1/namespaces/${encodeURIComponent(ns)}/${plural}?limit=500`
    : `/api/v1/${plural}?limit=500`
}

function coreWatchPath(plural: string, ns: string, rv: string): string {
  const base = ns
    ? `/api/v1/namespaces/${encodeURIComponent(ns)}/${plural}`
    : `/api/v1/${plural}`
  return `${base}?watch=true&allowWatchBookmarks=true&resourceVersion=${encodeURIComponent(rv || '')}`
}

function apisListPath(group: string, version: string, plural: string, ns: string): string {
  return ns
    ? `/apis/${group}/${version}/namespaces/${encodeURIComponent(ns)}/${plural}?limit=500`
    : `/apis/${group}/${version}/${plural}?limit=500`
}

function apisWatchPath(group: string, version: string, plural: string, ns: string, rv: string): string {
  const base = ns
    ? `/apis/${group}/${version}/namespaces/${encodeURIComponent(ns)}/${plural}`
    : `/apis/${group}/${version}/${plural}`
  return `${base}?watch=true&allowWatchBookmarks=true&resourceVersion=${encodeURIComponent(rv || '')}`
}

// ── 描述器 ────────────────────────────────────────────────────

export const RESOURCES: ResourceDescriptor[] = [
  // ── Workloads ───────────────────────────────────────────────
  {
    key: 'pods', kind: 'Pod', apiVersion: 'v1',
    namespaced: true, group: 'workloads', icon: 'Box', label: 'Pods',
    listPath: ns => coreListPath('pods', ns),
    watchPath: (ns, rv) => coreWatchPath('pods', ns, rv),
    columns: [
      { header: 'Name', value: p => p.metadata?.name || '' },
      { header: 'Namespace', value: p => p.metadata?.namespace || '', filterable: { type: 'enum' } },
      { header: 'Ready', value: podReady, filterable: { type: 'enum' } },
      { header: 'Status', value: podStatus, filterable: { type: 'enum' }, searchable: true },
      { header: 'Restarts', value: podRestarts },
      { header: 'CPU', value: (_p, u) => u ? formatCpu(u.cpu) : '—', width: 80, sortValue: (_p, u) => u?.cpu ?? -1 },
      { header: 'MEM', value: (_p, u) => u ? formatMemory(u.mem) : '—', width: 80, sortValue: (_p, u) => u?.mem ?? -1 },
      { header: '%CPU/R', value: (p, u) => u ? percent(u.cpu, podResourceTotals(p).cpuReq) : '—', width: 80 },
      { header: '%CPU/L', value: (p, u) => u ? percent(u.cpu, podResourceTotals(p).cpuLim) : '—', width: 80 },
      { header: '%MEM/R', value: (p, u) => u ? percent(u.mem, podResourceTotals(p).memReq) : '—', width: 80 },
      { header: '%MEM/L', value: (p, u) => u ? percent(u.mem, podResourceTotals(p).memLim) : '—', width: 80 },
      { header: 'IP', value: p => p.status?.podIP || '', width: 120, searchable: true },
      { header: 'Node', value: p => p.spec?.nodeName || '', filterable: { type: 'enum' }, searchable: true },
      { header: 'Age', value: p => age(p.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'logs', 'terminal', 'delete'],
    canCreate: true,
    metrics: 'pod',
    rowTone: podTone,
    detailSections: [
      { label: 'Metadata', fields: [
        { label: 'Name', value: p => p.metadata?.name || '' },
        { label: 'Namespace', value: p => p.metadata?.namespace || '' },
        { label: 'UID', value: p => p.metadata?.uid || '' },
        { label: 'Created', value: p => p.metadata?.creationTimestamp || '' },
        { label: 'Labels', value: p => Object.entries(p.metadata?.labels || {}).map(([k, v]) => `${k}=${v}`).join('\n') || '—' },
        { label: 'Annotations', value: p => Object.entries(p.metadata?.annotations || {}).map(([k, v]) => `${k}=${v}`).join('\n') || '—' },
        { label: 'Owner', value: p => (p.metadata?.ownerReferences || []).map((o: any) => `${o.kind}/${o.name}`).join(', ') || '—' },
      ]},
      { label: 'Status', fields: [
        { label: 'Phase', value: p => p.status?.phase || '' },
        { label: 'Pod IP', value: p => p.status?.podIP || '' },
        { label: 'Host IP', value: p => p.status?.hostIP || '' },
        { label: 'QoS', value: p => p.status?.qosClass || '' },
        { label: 'Start Time', value: p => p.status?.startTime || '' },
        { label: 'Restarts', value: p => String(podRestarts(p)) },
        { label: 'Conditions', value: p => (p.status?.conditions || []).map((c: any) => `${c.type}=${c.status}`).join('\n') || '—' },
        { label: 'Message', value: p => p.status?.message || '—' },
      ]},
      { label: 'Scheduling', fields: [
        { label: 'Node', value: p => p.spec?.nodeName || '' },
        { label: 'Service Account', value: p => p.spec?.serviceAccountName || p.spec?.serviceAccount || 'default' },
        { label: 'Restart Policy', value: p => p.spec?.restartPolicy || '' },
        { label: 'Node Selector', value: p => Object.entries(p.spec?.nodeSelector || {}).map(([k, v]) => `${k}=${v}`).join('\n') || '—' },
        { label: 'Tolerations', value: p => (p.spec?.tolerations || []).map((t: any) => t.key ? `${t.key}${t.operator === 'Exists' ? '' : '=' + (t.value || '')}${t.effect ? ':' + t.effect : ''}` : (t.operator || '')).join('\n') || '—' },
        { label: 'Priority Class', value: p => p.spec?.priorityClassName || '—' },
      ]},
      { label: 'Containers', fields: [
        { label: 'Containers', value: p => {
          const st = new Map((p.status?.containerStatuses || []).map((s: any) => [s.name, s]))
          return (p.spec?.containers || []).map((c: any) => {
            const s: any = st.get(c.name)
            const state = s?.state ? Object.keys(s.state)[0] : '?'
            const ports = (c.ports || []).map((pt: any) => `${pt.containerPort}/${pt.protocol || 'TCP'}`).join(',')
            const req = c.resources?.requests ? `req ${c.resources.requests.cpu || '-'}/${c.resources.requests.memory || '-'}` : ''
            const lim = c.resources?.limits ? `lim ${c.resources.limits.cpu || '-'}/${c.resources.limits.memory || '-'}` : ''
            return [
              `▸ ${c.name}`,
              `   image: ${c.image}`,
              `   state: ${state}  ready: ${s?.ready ? 'yes' : 'no'}  restarts: ${s?.restartCount ?? 0}`,
              ports ? `   ports: ${ports}` : '',
              (req || lim) ? `   resources: ${[req, lim].filter(Boolean).join('  ')}` : '',
            ].filter(Boolean).join('\n')
          }).join('\n\n')
        } },
      ]},
      { label: 'Volumes', fields: [
        { label: 'Volumes', value: p => (p.spec?.volumes || []).map((v: any) => {
          const type = Object.keys(v).find(k => k !== 'name') || '?'
          return `${v.name} (${type})`
        }).join('\n') || '—' },
      ]},
    ],
  },
  {
    key: 'deployments', kind: 'Deployment', apiVersion: 'apps/v1',
    namespaced: true, group: 'workloads', icon: 'Layers', label: 'Deployments',
    listPath: ns => apisListPath('apps', 'v1', 'deployments', ns),
    watchPath: (ns, rv) => apisWatchPath('apps', 'v1', 'deployments', ns, rv),
    columns: [
      { header: 'Name', value: d => d.metadata?.name || '' },
      { header: 'Namespace', value: d => d.metadata?.namespace || '' },
      { header: 'Ready', value: d => `${d.status?.readyReplicas || 0}/${d.spec?.replicas ?? 0}` },
      { header: 'Up-to-date', value: d => d.status?.updatedReplicas || 0 },
      { header: 'Available', value: d => d.status?.availableReplicas || 0 },
      { header: 'Age', value: d => age(d.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'restart', 'scale', 'delete'],
    canCreate: true,
    rowTone: d => replicaTone(d.status?.readyReplicas || 0, d.spec?.replicas ?? 0),
    createTemplate: ns => `apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
  namespace: ${ns}
  labels:
    app: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: nginx:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Replicas', value: d => String(d.spec?.replicas ?? 0) },
        { label: 'Strategy', value: d => d.spec?.strategy?.type || '' },
        { label: 'Selector', value: selectorText },
        { label: 'Min Ready Seconds', value: d => String(d.spec?.minReadySeconds ?? 0) },
      ]},
      { label: 'Status', fields: [
        { label: 'Ready', value: d => `${d.status?.readyReplicas || 0}/${d.spec?.replicas ?? 0}` },
        { label: 'Updated', value: d => String(d.status?.updatedReplicas || 0) },
        { label: 'Available', value: d => String(d.status?.availableReplicas || 0) },
        { label: 'Unavailable', value: d => String(d.status?.unavailableReplicas || 0) },
        { label: 'Conditions', value: d => (d.status?.conditions || []).map((c: any) => `${c.type}=${c.status}`).join('\n') || '—' },
      ]},
    ),
  },
  {
    key: 'statefulsets', kind: 'StatefulSet', apiVersion: 'apps/v1',
    namespaced: true, group: 'workloads', icon: 'Boxes', label: 'StatefulSets',
    listPath: ns => apisListPath('apps', 'v1', 'statefulsets', ns),
    watchPath: (ns, rv) => apisWatchPath('apps', 'v1', 'statefulsets', ns, rv),
    columns: [
      { header: 'Name', value: s => s.metadata?.name || '' },
      { header: 'Namespace', value: s => s.metadata?.namespace || '' },
      { header: 'Ready', value: s => `${s.status?.readyReplicas || 0}/${s.spec?.replicas ?? 0}` },
      { header: 'Service', value: s => s.spec?.serviceName || '' },
      { header: 'Age', value: s => age(s.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'restart', 'scale', 'delete'],
    canCreate: true,
    rowTone: s => replicaTone(s.status?.readyReplicas || 0, s.spec?.replicas ?? 0),
    createTemplate: ns => `apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: my-statefulset
  namespace: ${ns}
spec:
  serviceName: my-service
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: nginx:latest
          ports:
            - containerPort: 80
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Replicas', value: s => String(s.spec?.replicas ?? 0) },
        { label: 'Service Name', value: s => s.spec?.serviceName || '' },
        { label: 'Update Strategy', value: s => s.spec?.updateStrategy?.type || '' },
        { label: 'Pod Mgmt Policy', value: s => s.spec?.podManagementPolicy || '' },
        { label: 'Selector', value: selectorText },
      ]},
      { label: 'Status', fields: [
        { label: 'Ready', value: s => `${s.status?.readyReplicas || 0}/${s.spec?.replicas ?? 0}` },
        { label: 'Current', value: s => String(s.status?.currentReplicas || 0) },
        { label: 'Updated', value: s => String(s.status?.updatedReplicas || 0) },
      ]},
    ),
  },
  {
    key: 'daemonsets', kind: 'DaemonSet', apiVersion: 'apps/v1',
    namespaced: true, group: 'workloads', icon: 'GitFork', label: 'DaemonSets',
    listPath: ns => apisListPath('apps', 'v1', 'daemonsets', ns),
    watchPath: (ns, rv) => apisWatchPath('apps', 'v1', 'daemonsets', ns, rv),
    columns: [
      { header: 'Name', value: d => d.metadata?.name || '' },
      { header: 'Namespace', value: d => d.metadata?.namespace || '' },
      { header: 'Desired', value: d => d.status?.desiredNumberScheduled || 0 },
      { header: 'Current', value: d => d.status?.currentNumberScheduled || 0 },
      { header: 'Ready', value: d => d.status?.numberReady || 0 },
      { header: 'Up-to-date', value: d => d.status?.updatedNumberScheduled || 0 },
      { header: 'Available', value: d => d.status?.numberAvailable || 0 },
      { header: 'Age', value: d => age(d.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'restart', 'delete'],
    canCreate: true,
    rowTone: d => replicaTone(d.status?.numberReady || 0, d.status?.desiredNumberScheduled || 0),
    createTemplate: ns => `apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: my-daemonset
  namespace: ${ns}
spec:
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: nginx:latest
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Update Strategy', value: d => d.spec?.updateStrategy?.type || '' },
        { label: 'Selector', value: selectorText },
      ]},
      { label: 'Status', fields: [
        { label: 'Desired', value: d => String(d.status?.desiredNumberScheduled || 0) },
        { label: 'Current', value: d => String(d.status?.currentNumberScheduled || 0) },
        { label: 'Ready', value: d => String(d.status?.numberReady || 0) },
        { label: 'Up-to-date', value: d => String(d.status?.updatedNumberScheduled || 0) },
        { label: 'Available', value: d => String(d.status?.numberAvailable || 0) },
        { label: 'Misscheduled', value: d => String(d.status?.numberMisscheduled || 0) },
      ]},
    ),
  },
  {
    key: 'jobs', kind: 'Job', apiVersion: 'batch/v1',
    namespaced: true, group: 'workloads', icon: 'PlayCircle', label: 'Jobs',
    listPath: ns => apisListPath('batch', 'v1', 'jobs', ns),
    watchPath: (ns, rv) => apisWatchPath('batch', 'v1', 'jobs', ns, rv),
    columns: [
      { header: 'Name', value: j => j.metadata?.name || '' },
      { header: 'Namespace', value: j => j.metadata?.namespace || '' },
      { header: 'Completions', value: j => `${j.status?.succeeded || 0}/${j.spec?.completions ?? 1}` },
      { header: 'Duration', value: j => durationBetween(j.status?.startTime, j.status?.completionTime) },
      { header: 'Age', value: j => age(j.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'delete'],
    canCreate: true,
    rowTone: j => {
      if (j.status?.failed) return 'err'
      const done = (j.status?.succeeded || 0) >= (j.spec?.completions ?? 1)
      return done ? '' : 'warn'
    },
    createTemplate: ns => `apiVersion: batch/v1
kind: Job
metadata:
  name: my-job
  namespace: ${ns}
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 4
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: job
          image: busybox:latest
          command: ["sh", "-c", "echo hello && sleep 5"]
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Completions', value: j => String(j.spec?.completions ?? 1) },
        { label: 'Parallelism', value: j => String(j.spec?.parallelism ?? 1) },
        { label: 'Backoff Limit', value: j => String(j.spec?.backoffLimit ?? '') },
        { label: 'Selector', value: selectorText },
      ]},
      { label: 'Status', fields: [
        { label: 'Active', value: j => String(j.status?.active || 0) },
        { label: 'Succeeded', value: j => String(j.status?.succeeded || 0) },
        { label: 'Failed', value: j => String(j.status?.failed || 0) },
        { label: 'Start Time', value: j => j.status?.startTime || '' },
        { label: 'Completion Time', value: j => j.status?.completionTime || '' },
        { label: 'Duration', value: j => durationBetween(j.status?.startTime, j.status?.completionTime) },
      ]},
    ),
  },
  {
    key: 'cronjobs', kind: 'CronJob', apiVersion: 'batch/v1',
    namespaced: true, group: 'workloads', icon: 'Clock', label: 'CronJobs',
    listPath: ns => apisListPath('batch', 'v1', 'cronjobs', ns),
    watchPath: (ns, rv) => apisWatchPath('batch', 'v1', 'cronjobs', ns, rv),
    columns: [
      { header: 'Name', value: c => c.metadata?.name || '' },
      { header: 'Namespace', value: c => c.metadata?.namespace || '' },
      { header: 'Schedule', value: c => c.spec?.schedule || '' },
      { header: 'Suspend', value: c => c.spec?.suspend ? 'true' : 'false' },
      { header: 'Active', value: c => (c.status?.active || []).length },
      { header: 'Last Schedule', value: c => age(c.status?.lastScheduleTime) },
      { header: 'Age', value: c => age(c.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    createTemplate: ns => `apiVersion: batch/v1
kind: CronJob
metadata:
  name: my-cronjob
  namespace: ${ns}
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Allow
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: job
              image: busybox:latest
              command: ["sh", "-c", "date; echo hello"]
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Schedule', value: c => c.spec?.schedule || '' },
        { label: 'Suspend', value: c => c.spec?.suspend ? 'true' : 'false' },
        { label: 'Concurrency Policy', value: c => c.spec?.concurrencyPolicy || '' },
        { label: 'Starting Deadline', value: c => String(c.spec?.startingDeadlineSeconds ?? '') },
      ]},
      { label: 'Status', fields: [
        { label: 'Active', value: c => String((c.status?.active || []).length) },
        { label: 'Last Schedule', value: c => c.status?.lastScheduleTime || '' },
        { label: 'Last Successful', value: c => c.status?.lastSuccessfulTime || '' },
      ]},
    ),
  },
  {
    key: 'replicasets', kind: 'ReplicaSet', apiVersion: 'apps/v1',
    namespaced: true, group: 'workloads', icon: 'Copy', label: 'ReplicaSets',
    listPath: ns => apisListPath('apps', 'v1', 'replicasets', ns),
    watchPath: (ns, rv) => apisWatchPath('apps', 'v1', 'replicasets', ns, rv),
    columns: [
      { header: 'Name', value: r => r.metadata?.name || '' },
      { header: 'Namespace', value: r => r.metadata?.namespace || '' },
      { header: 'Desired', value: r => r.spec?.replicas ?? 0 },
      { header: 'Current', value: r => r.status?.replicas || 0 },
      { header: 'Ready', value: r => r.status?.readyReplicas || 0 },
      { header: 'Age', value: r => age(r.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'scale', 'delete'],
    canCreate: true,
    rowTone: r => replicaTone(r.status?.readyReplicas || 0, r.spec?.replicas ?? 0),
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Replicas', value: r => String(r.spec?.replicas ?? 0) },
        { label: 'Selector', value: selectorText },
      ]},
      { label: 'Status', fields: [
        { label: 'Replicas', value: r => String(r.status?.replicas || 0) },
        { label: 'Ready', value: r => String(r.status?.readyReplicas || 0) },
        { label: 'Available', value: r => String(r.status?.availableReplicas || 0) },
      ]},
    ),
  },
  // ── Network ─────────────────────────────────────────────────
  {
    key: 'services', kind: 'Service', apiVersion: 'v1',
    namespaced: true, group: 'network', icon: 'Network', label: 'Services',
    listPath: ns => coreListPath('services', ns),
    watchPath: (ns, rv) => coreWatchPath('services', ns, rv),
    columns: [
      { header: 'Name', value: s => s.metadata?.name || '' },
      { header: 'Namespace', value: s => s.metadata?.namespace || '' },
      { header: 'Type', value: s => s.spec?.type || '', filterable: { type: 'enum' }, searchable: true },
      { header: 'Cluster-IP', value: s => s.spec?.clusterIP || '', searchable: true },
      { header: 'Ports', value: servicePorts, width: 260, searchable: true },
      { header: 'Age', value: s => age(s.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: Service
metadata:
  name: my-service
  namespace: ${ns}
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Type', value: s => s.spec?.type || '' },
        { label: 'Cluster IP', value: s => s.spec?.clusterIP || '' },
        { label: 'External IPs', value: s => (s.spec?.externalIPs || []).join(',') || '—' },
        { label: 'Session Affinity', value: s => s.spec?.sessionAffinity || '' },
        { label: 'Selector', value: s => kv(s.spec?.selector) },
        { label: 'Ports', value: s => (s.spec?.ports || []).map((p: any) => `${p.name ? p.name + ' ' : ''}${p.port}→${p.targetPort}/${p.protocol || 'TCP'}${p.nodePort ? ' (node ' + p.nodePort + ')' : ''}`).join('\n') || '—' },
      ]},
      { label: 'Status', fields: [
        { label: 'LoadBalancer', value: s => (s.status?.loadBalancer?.ingress || []).map((g: any) => g.ip || g.hostname).join(',') || '—' },
      ]},
    ),
  },
  {
    key: 'ingresses', kind: 'Ingress', apiVersion: 'networking.k8s.io/v1',
    namespaced: true, group: 'network', icon: 'Globe', label: 'Ingresses',
    listPath: ns => apisListPath('networking.k8s.io', 'v1', 'ingresses', ns),
    watchPath: (ns, rv) => apisWatchPath('networking.k8s.io', 'v1', 'ingresses', ns, rv),
    columns: [
      { header: 'Name', value: i => i.metadata?.name || '' },
      { header: 'Namespace', value: i => i.metadata?.namespace || '' },
      { header: 'Class', value: i => i.spec?.ingressClassName || '', searchable: true },
      { header: 'Hosts', value: i => (i.spec?.rules || []).map((r: any) => r.host).filter(Boolean).join(',') || '*', searchable: true },
      { header: 'Address', value: i => (i.status?.loadBalancer?.ingress || []).map((g: any) => g.ip || g.hostname).filter(Boolean).join(','), searchable: true },
      { header: 'Ports', value: i => (i.spec?.tls?.length ? '80,443' : '80') },
      { header: 'Age', value: i => age(i.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    createTemplate: ns => `apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  namespace: ${ns}
spec:
  ingressClassName: nginx
  rules:
    - host: example.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Class', value: i => i.spec?.ingressClassName || '' },
        { label: 'TLS', value: i => (i.spec?.tls || []).map((t: any) => (t.hosts || []).join(',') + (t.secretName ? ` → ${t.secretName}` : '')).join('\n') || '—' },
        { label: 'Rules', value: i => (i.spec?.rules || []).flatMap((r: any) =>
            (r.http?.paths || []).map((p: any) => `${r.host || '*'}${p.path || '/'} → ${p.backend?.service?.name || ''}:${p.backend?.service?.port?.number || p.backend?.service?.port?.name || ''}`)
          ).join('\n') || '—' },
      ]},
      { label: 'Status', fields: [
        { label: 'Address', value: i => (i.status?.loadBalancer?.ingress || []).map((g: any) => g.ip || g.hostname).join(',') || '—' },
      ]},
    ),
  },
  // ── Config ──────────────────────────────────────────────────
  {
    key: 'configmaps', kind: 'ConfigMap', apiVersion: 'v1',
    namespaced: true, group: 'config', icon: 'FileText', label: 'ConfigMaps',
    listPath: ns => coreListPath('configmaps', ns),
    watchPath: (ns, rv) => coreWatchPath('configmaps', ns, rv),
    columns: [
      { header: 'Name', value: c => c.metadata?.name || '' },
      { header: 'Namespace', value: c => c.metadata?.namespace || '' },
      { header: 'Data', value: c => Object.keys(c.data || {}).length },
      { header: 'Age', value: c => age(c.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: ConfigMap
metadata:
  name: my-configmap
  namespace: ${ns}
data:
  key1: value1
  config.yaml: |
    foo: bar
`,
    detailSections: withMeta(
      { label: 'Data', fields: [
        { label: 'Keys', value: c => Object.keys(c.data || {}).join('\n') || '—' },
      ]},
    ),
  },
  {
    key: 'secrets', kind: 'Secret', apiVersion: 'v1',
    namespaced: true, group: 'config', icon: 'Lock', label: 'Secrets',
    listPath: ns => coreListPath('secrets', ns),
    watchPath: (ns, rv) => coreWatchPath('secrets', ns, rv),
    columns: [
      { header: 'Name', value: s => s.metadata?.name || '' },
      { header: 'Namespace', value: s => s.metadata?.namespace || '' },
      { header: 'Type', value: s => s.type || '' },
      { header: 'Data', value: s => Object.keys(s.data || {}).length },
      { header: 'Age', value: s => age(s.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: Secret
metadata:
  name: my-secret
  namespace: ${ns}
type: Opaque
stringData:
  username: admin
  password: changeme
`,
    detailSections: withMeta(
      { label: 'Data', fields: [
        { label: 'Type', value: s => s.type || '' },
        { label: 'Keys', value: s => Object.keys(s.data || {}).join('\n') || '—' },
      ]},
    ),
  },
  // ── Storage ─────────────────────────────────────────────────
  {
    key: 'persistentvolumeclaims', kind: 'PersistentVolumeClaim', apiVersion: 'v1',
    namespaced: true, group: 'storage', icon: 'HardDrive', label: 'PVCs',
    listPath: ns => coreListPath('persistentvolumeclaims', ns),
    watchPath: (ns, rv) => coreWatchPath('persistentvolumeclaims', ns, rv),
    columns: [
      { header: 'Name', value: p => p.metadata?.name || '' },
      { header: 'Namespace', value: p => p.metadata?.namespace || '' },
      { header: 'Status', value: p => p.status?.phase || '', filterable: { type: 'enum' } },
      { header: 'Volume', value: p => p.spec?.volumeName || '', searchable: true },
      { header: 'Capacity', value: p => p.status?.capacity?.storage || '' },
      { header: 'Storage Class', value: p => p.spec?.storageClassName || '', searchable: true },
      { header: 'Age', value: p => age(p.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    rowTone: p => (p.status?.phase === 'Bound' ? '' : 'warn'),
    createTemplate: ns => `apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
  namespace: ${ns}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Access Modes', value: p => (p.spec?.accessModes || []).join(',') },
        { label: 'Storage Class', value: p => p.spec?.storageClassName || '' },
        { label: 'Volume Name', value: p => p.spec?.volumeName || '' },
        { label: 'Volume Mode', value: p => p.spec?.volumeMode || '' },
        { label: 'Requested', value: p => p.spec?.resources?.requests?.storage || '' },
      ]},
      { label: 'Status', fields: [
        { label: 'Phase', value: p => p.status?.phase || '' },
        { label: 'Capacity', value: p => p.status?.capacity?.storage || '' },
      ]},
    ),
  },
  {
    key: 'persistentvolumes', kind: 'PersistentVolume', apiVersion: 'v1',
    namespaced: false, group: 'storage', icon: 'Database', label: 'PVs',
    listPath: () => coreListPath('persistentvolumes', ''),
    watchPath: (_ns, rv) => coreWatchPath('persistentvolumes', '', rv),
    columns: [
      { header: 'Name', value: p => p.metadata?.name || '' },
      { header: 'Capacity', value: p => p.spec?.capacity?.storage || '' },
      { header: 'Access Modes', value: p => (p.spec?.accessModes || []).join(',') },
      { header: 'Reclaim Policy', value: p => p.spec?.persistentVolumeReclaimPolicy || '' },
      { header: 'Status', value: p => p.status?.phase || '', filterable: { type: 'enum' } },
      { header: 'Claim', value: p => p.spec?.claimRef ? `${p.spec.claimRef.namespace}/${p.spec.claimRef.name}` : '', searchable: true },
      { header: 'Storage Class', value: p => p.spec?.storageClassName || '', searchable: true },
      { header: 'Reason', value: p => p.status?.reason || '' },
      { header: 'Age', value: p => age(p.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: true,
    rowTone: p => (p.status?.phase === 'Bound' || p.status?.phase === 'Available' ? '' : 'warn'),
    createTemplate: () => `apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Capacity', value: p => p.spec?.capacity?.storage || '' },
        { label: 'Access Modes', value: p => (p.spec?.accessModes || []).join(',') },
        { label: 'Reclaim Policy', value: p => p.spec?.persistentVolumeReclaimPolicy || '' },
        { label: 'Storage Class', value: p => p.spec?.storageClassName || '' },
        { label: 'Volume Mode', value: p => p.spec?.volumeMode || '' },
        { label: 'Source', value: p => Object.keys(p.spec || {}).find(k => !['capacity','accessModes','persistentVolumeReclaimPolicy','storageClassName','volumeMode','claimRef','mountOptions','nodeAffinity'].includes(k)) || '—' },
      ]},
      { label: 'Status', fields: [
        { label: 'Phase', value: p => p.status?.phase || '' },
        { label: 'Claim', value: p => p.spec?.claimRef ? `${p.spec.claimRef.namespace}/${p.spec.claimRef.name}` : '—' },
        { label: 'Reason', value: p => p.status?.reason || '—' },
      ]},
    ),
  },
  // ── Cluster ─────────────────────────────────────────────────
  {
    key: 'nodes', kind: 'Node', apiVersion: 'v1',
    namespaced: false, group: 'cluster', icon: 'Server', label: 'Nodes',
    listPath: () => coreListPath('nodes', ''),
    watchPath: (_ns, rv) => coreWatchPath('nodes', '', rv),
    columns: [
      { header: 'Name', value: n => n.metadata?.name || '' },
      { header: 'Status', value: n => {
        const c = (n.status?.conditions || []).find((c: any) => c.type === 'Ready')
        return c?.status === 'True' ? 'Ready' : 'NotReady'
      }, filterable: { type: 'enum' } },
      { header: 'Roles', value: n => Object.keys(n.metadata?.labels || {})
          .filter(l => l.startsWith('node-role.kubernetes.io/'))
          .map(l => l.substring('node-role.kubernetes.io/'.length))
          .join(',') || '<none>', searchable: true },
      { header: 'Taints', value: n => (n.spec?.taints || []).length || 0, width: 70 },
      { header: 'Version', value: n => n.status?.nodeInfo?.kubeletVersion || '', searchable: true },
      { header: 'Internal-IP', value: n => (n.status?.addresses || []).find((a: any) => a.type === 'InternalIP')?.address || '', searchable: true },
      { header: 'Pods', value: n => n.status?.allocatable?.pods || n.status?.capacity?.pods || '', width: 70 },
      { header: 'CPU', value: (_n, u) => u ? formatCpu(u.cpu) : '—', width: 80, sortValue: (_n, u) => u?.cpu ?? -1 },
      { header: 'MEM', value: (_n, u) => u ? formatMemory(u.mem) : '—', width: 80, sortValue: (_n, u) => u?.mem ?? -1 },
      { header: '%CPU', value: (n, u) => u ? percent(u.cpu, parseCpu(n.status?.allocatable?.cpu)) : '—', width: 70 },
      { header: '%MEM', value: (n, u) => u ? percent(u.mem, parseMemory(n.status?.allocatable?.memory)) : '—', width: 70 },
      { header: 'OS', value: n => n.status?.nodeInfo?.osImage || '' },
      { header: 'Kernel', value: n => n.status?.nodeInfo?.kernelVersion || '' },
      { header: 'Container-Runtime', value: n => n.status?.nodeInfo?.containerRuntimeVersion || '' },
      { header: 'Age', value: n => age(n.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'viewPods', 'cordon', 'drain'],
    canCreate: false,
    metrics: 'node',
    rowTone: n => {
      const c = (n.status?.conditions || []).find((x: any) => x.type === 'Ready')
      if (c?.status !== 'True') return 'err'
      return n.spec?.unschedulable ? 'warn' : ''
    },
    detailSections: withMeta(
      { label: 'Info', fields: [
        { label: 'Kubelet', value: n => n.status?.nodeInfo?.kubeletVersion || '' },
        { label: 'OS Image', value: n => n.status?.nodeInfo?.osImage || '' },
        { label: 'Kernel', value: n => n.status?.nodeInfo?.kernelVersion || '' },
        { label: 'Container Runtime', value: n => n.status?.nodeInfo?.containerRuntimeVersion || '' },
        { label: 'Architecture', value: n => n.status?.nodeInfo?.architecture || '' },
        { label: 'Roles', value: n => Object.keys(n.metadata?.labels || {}).filter(l => l.startsWith('node-role.kubernetes.io/')).map(l => l.substring('node-role.kubernetes.io/'.length)).join(',') || '<none>' },
      ]},
      { label: 'Scheduling', fields: [
        { label: 'Unschedulable', value: n => n.spec?.unschedulable ? 'true' : 'false' },
        { label: 'Taints', value: n => (n.spec?.taints || []).map((t: any) => `${t.key}${t.value ? '=' + t.value : ''}:${t.effect}`).join('\n') || '—' },
      ]},
      { label: 'Capacity', fields: [
        { label: 'CPU', value: n => n.status?.capacity?.cpu || '' },
        { label: 'Memory', value: n => n.status?.capacity?.memory || '' },
        { label: 'Pods', value: n => n.status?.capacity?.pods || '' },
      ]},
      { label: 'Addresses', fields: [
        { label: 'Addresses', value: n => (n.status?.addresses || []).map((a: any) => `${a.type}: ${a.address}`).join('\n') || '—' },
      ]},
      { label: 'Conditions', fields: [
        { label: 'Conditions', value: n => (n.status?.conditions || []).map((c: any) => `${c.type}=${c.status}`).join('\n') || '—' },
      ]},
    ),
  },
  {
    key: 'namespaces', kind: 'Namespace', apiVersion: 'v1',
    namespaced: false, group: 'cluster', icon: 'Folder', label: 'Namespaces',
    listPath: () => coreListPath('namespaces', ''),
    watchPath: (_ns, rv) => coreWatchPath('namespaces', '', rv),
    columns: [
      { header: 'Name', value: n => n.metadata?.name || '' },
      { header: 'Status', value: n => n.status?.phase || '', filterable: { type: 'enum' } },
      { header: 'Age', value: n => age(n.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'],
    canCreate: false,
    detailSections: withMeta(
      { label: 'Status', fields: [
        { label: 'Phase', value: n => n.status?.phase || '' },
      ]},
    ),
  },
  {
    key: 'events', kind: 'Event', apiVersion: 'v1',
    namespaced: true, group: 'cluster', icon: 'Bell', label: 'Events',
    listPath: ns => coreListPath('events', ns),
    watchPath: (ns, rv) => coreWatchPath('events', ns, rv),
    columns: [
      { header: 'Type', value: e => e.type || '', filterable: { type: 'enum' } },
      { header: 'Reason', value: e => e.reason || '', searchable: true },
      { header: 'Object', value: e => `${e.involvedObject?.kind}/${e.involvedObject?.name || ''}`, searchable: true },
      { header: 'Message', value: e => e.message || '', searchable: true },
      { header: 'Namespace', value: e => e.metadata?.namespace || '' },
      { header: 'Age', value: e => age(e.metadata?.creationTimestamp || e.lastTimestamp) },
    ],
    actions: ['detail'],
    canCreate: false,
  },
  // ── Workloads (autoscaling) ─────────────────────────────────
  {
    key: 'horizontalpodautoscalers', kind: 'HorizontalPodAutoscaler', apiVersion: 'autoscaling/v2',
    namespaced: true, group: 'workloads', icon: 'CircleGauge', label: 'HPAs',
    listPath: ns => apisListPath('autoscaling', 'v2', 'horizontalpodautoscalers', ns),
    watchPath: (ns, rv) => apisWatchPath('autoscaling', 'v2', 'horizontalpodautoscalers', ns, rv),
    columns: [
      { header: 'Name', value: h => h.metadata?.name || '' },
      { header: 'Namespace', value: h => h.metadata?.namespace || '' },
      { header: 'Reference', value: h => `${h.spec?.scaleTargetRef?.kind || ''}/${h.spec?.scaleTargetRef?.name || ''}`, searchable: true },
      { header: 'Targets', value: hpaTargets, width: 140 },
      { header: 'MinPods', value: h => h.spec?.minReplicas ?? 0, width: 80 },
      { header: 'MaxPods', value: h => h.spec?.maxReplicas ?? 0, width: 80 },
      { header: 'Replicas', value: h => h.status?.currentReplicas ?? 0, width: 80 },
      { header: 'Age', value: h => age(h.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-hpa
  namespace: ${ns}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-deployment
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Reference', value: h => `${h.spec?.scaleTargetRef?.kind || ''}/${h.spec?.scaleTargetRef?.name || ''}` },
        { label: 'Min Replicas', value: h => String(h.spec?.minReplicas ?? 0) },
        { label: 'Max Replicas', value: h => String(h.spec?.maxReplicas ?? 0) },
        { label: 'Targets', value: hpaTargets },
      ]},
      { label: 'Status', fields: [
        { label: 'Current Replicas', value: h => String(h.status?.currentReplicas ?? 0) },
        { label: 'Desired Replicas', value: h => String(h.status?.desiredReplicas ?? 0) },
        { label: 'Last Scale', value: h => h.status?.lastScaleTime || '—' },
      ]},
    ),
  },
  // ── Network ─────────────────────────────────────────────────
  {
    key: 'networkpolicies', kind: 'NetworkPolicy', apiVersion: 'networking.k8s.io/v1',
    namespaced: true, group: 'network', icon: 'BrickWallShield', label: 'NetworkPolicies',
    listPath: ns => apisListPath('networking.k8s.io', 'v1', 'networkpolicies', ns),
    watchPath: (ns, rv) => apisWatchPath('networking.k8s.io', 'v1', 'networkpolicies', ns, rv),
    columns: [
      { header: 'Name', value: n => n.metadata?.name || '' },
      { header: 'Namespace', value: n => n.metadata?.namespace || '' },
      { header: 'Ing-Ports', value: n => npPorts(n.spec?.ingress) },
      { header: 'Ing-Block', value: n => npBlocks(n.spec?.ingress, 'from') },
      { header: 'Egr-Ports', value: n => npPorts(n.spec?.egress) },
      { header: 'Egr-Block', value: n => npBlocks(n.spec?.egress, 'to') },
      { header: 'Age', value: n => age(n.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-networkpolicy
  namespace: ${ns}
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 80
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Pod Selector', value: n => kv(n.spec?.podSelector?.matchLabels) },
        { label: 'Policy Types', value: n => (n.spec?.policyTypes || []).join(',') || '—' },
        { label: 'Ingress Ports', value: n => npPorts(n.spec?.ingress) },
        { label: 'Ingress Block', value: n => npBlocks(n.spec?.ingress, 'from') },
        { label: 'Egress Ports', value: n => npPorts(n.spec?.egress) },
        { label: 'Egress Block', value: n => npBlocks(n.spec?.egress, 'to') },
      ]},
    ),
  },
  {
    key: 'endpoints', kind: 'Endpoints', apiVersion: 'v1',
    namespaced: true, group: 'network', icon: 'Cable', label: 'Endpoints',
    listPath: ns => coreListPath('endpoints', ns),
    watchPath: (ns, rv) => coreWatchPath('endpoints', ns, rv),
    columns: [
      { header: 'Name', value: e => e.metadata?.name || '' },
      { header: 'Namespace', value: e => e.metadata?.namespace || '' },
      { header: 'Endpoints', value: endpointsText, width: 320, searchable: true },
      { header: 'Age', value: e => age(e.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: false,
    detailSections: withMeta(
      { label: 'Subsets', fields: [
        { label: 'Endpoints', value: endpointsText },
      ]},
    ),
  },
  // ── Config (quota) ──────────────────────────────────────────
  {
    key: 'resourcequotas', kind: 'ResourceQuota', apiVersion: 'v1',
    namespaced: true, group: 'config', icon: 'File', label: 'ResourceQuotas',
    listPath: ns => coreListPath('resourcequotas', ns),
    watchPath: (ns, rv) => coreWatchPath('resourcequotas', ns, rv),
    columns: [
      { header: 'Name', value: q => q.metadata?.name || '' },
      { header: 'Namespace', value: q => q.metadata?.namespace || '' },
      { header: 'Request', value: quotaRequest, width: 200 },
      { header: 'Limit', value: quotaLimit, width: 200 },
      { header: 'Age', value: q => age(q.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: ResourceQuota
metadata:
  name: my-quota
  namespace: ${ns}
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "20"
`,
    detailSections: withMeta(
      { label: 'Quota', fields: [
        { label: 'Hard', value: q => kv(q.spec?.hard) },
        { label: 'Used', value: q => kv(q.status?.used) },
      ]},
    ),
  },
  {
    key: 'limitranges', kind: 'LimitRange', apiVersion: 'v1',
    namespaced: true, group: 'config', icon: 'File', label: 'LimitRanges',
    listPath: ns => coreListPath('limitranges', ns),
    watchPath: (ns, rv) => coreWatchPath('limitranges', ns, rv),
    columns: [
      { header: 'Name', value: l => l.metadata?.name || '' },
      { header: 'Namespace', value: l => l.metadata?.namespace || '' },
      { header: 'Age', value: l => age(l.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: LimitRange
metadata:
  name: my-limitrange
  namespace: ${ns}
spec:
  limits:
    - type: Container
      default:
        cpu: 500m
        memory: 512Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
`,
  },
  // ── Storage ─────────────────────────────────────────────────
  {
    key: 'storageclasses', kind: 'StorageClass', apiVersion: 'storage.k8s.io/v1',
    namespaced: false, group: 'storage', icon: 'Package2', label: 'StorageClasses',
    listPath: () => apisListPath('storage.k8s.io', 'v1', 'storageclasses', ''),
    watchPath: (_ns, rv) => apisWatchPath('storage.k8s.io', 'v1', 'storageclasses', '', rv),
    columns: [
      { header: 'Name', value: s => s.metadata?.name || '' },
      { header: 'Provisioner', value: s => s.provisioner || '', searchable: true },
      { header: 'Reclaim Policy', value: s => s.reclaimPolicy || '' },
      { header: 'Volume Binding Mode', value: s => s.volumeBindingMode || '' },
      { header: 'Allow Expansion', value: s => s.allowVolumeExpansion ? 'true' : 'false' },
      { header: 'Age', value: s => age(s.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: () => `apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: my-storageclass
provisioner: kubernetes.io/no-provisioner
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
`,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Provisioner', value: s => s.provisioner || '' },
        { label: 'Reclaim Policy', value: s => s.reclaimPolicy || '' },
        { label: 'Volume Binding Mode', value: s => s.volumeBindingMode || '' },
        { label: 'Allow Expansion', value: s => s.allowVolumeExpansion ? 'true' : 'false' },
        { label: 'Parameters', value: s => kv(s.parameters) },
      ]},
    ),
  },
  // ── RBAC ────────────────────────────────────────────────────
  {
    key: 'serviceaccounts', kind: 'ServiceAccount', apiVersion: 'v1',
    namespaced: true, group: 'rbac', icon: 'Lock', label: 'ServiceAccounts',
    listPath: ns => coreListPath('serviceaccounts', ns),
    watchPath: (ns, rv) => coreWatchPath('serviceaccounts', ns, rv),
    columns: [
      { header: 'Name', value: s => s.metadata?.name || '' },
      { header: 'Namespace', value: s => s.metadata?.namespace || '' },
      { header: 'Secrets', value: s => (s.secrets || []).length },
      { header: 'Age', value: s => age(s.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-serviceaccount
  namespace: ${ns}
`,
    detailSections: withMeta(
      { label: 'Detail', fields: [
        { label: 'Secrets', value: s => (s.secrets || []).map((x: any) => x.name).join('\n') || '—' },
        { label: 'Image Pull Secrets', value: s => (s.imagePullSecrets || []).map((x: any) => x.name).join('\n') || '—' },
      ]},
    ),
  },
  {
    key: 'roles', kind: 'Role', apiVersion: 'rbac.authorization.k8s.io/v1',
    namespaced: true, group: 'rbac', icon: 'Lock', label: 'Roles',
    listPath: ns => apisListPath('rbac.authorization.k8s.io', 'v1', 'roles', ns),
    watchPath: (ns, rv) => apisWatchPath('rbac.authorization.k8s.io', 'v1', 'roles', ns, rv),
    columns: [
      { header: 'Name', value: r => r.metadata?.name || '' },
      { header: 'Namespace', value: r => r.metadata?.namespace || '' },
      { header: 'Age', value: r => age(r.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-role
  namespace: ${ns}
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
`,
    detailSections: withMeta(
      { label: 'Rules', fields: [ { label: 'Rules', value: rbacRules } ] },
    ),
  },
  {
    key: 'rolebindings', kind: 'RoleBinding', apiVersion: 'rbac.authorization.k8s.io/v1',
    namespaced: true, group: 'rbac', icon: 'Lock', label: 'RoleBindings',
    listPath: ns => apisListPath('rbac.authorization.k8s.io', 'v1', 'rolebindings', ns),
    watchPath: (ns, rv) => apisWatchPath('rbac.authorization.k8s.io', 'v1', 'rolebindings', ns, rv),
    columns: [
      { header: 'Name', value: r => r.metadata?.name || '' },
      { header: 'Namespace', value: r => r.metadata?.namespace || '' },
      { header: 'Role', value: r => r.roleRef?.name || '', searchable: true },
      { header: 'Kind', value: r => r.roleRef?.kind || '' },
      { header: 'Subjects', value: r => (r.subjects || []).map((s: any) => s.name).join(',') || '—', width: 200, searchable: true },
      { header: 'Age', value: r => age(r.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: ns => `apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-rolebinding
  namespace: ${ns}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: my-role
subjects:
  - kind: ServiceAccount
    name: my-serviceaccount
    namespace: ${ns}
`,
    detailSections: withMeta(
      { label: 'Binding', fields: [
        { label: 'Role Ref', value: r => `${r.roleRef?.kind || ''}/${r.roleRef?.name || ''}` },
        { label: 'Subjects', value: rbacSubjects },
      ]},
    ),
  },
  {
    key: 'clusterroles', kind: 'ClusterRole', apiVersion: 'rbac.authorization.k8s.io/v1',
    namespaced: false, group: 'rbac', icon: 'Lock', label: 'ClusterRoles',
    listPath: () => apisListPath('rbac.authorization.k8s.io', 'v1', 'clusterroles', ''),
    watchPath: (_ns, rv) => apisWatchPath('rbac.authorization.k8s.io', 'v1', 'clusterroles', '', rv),
    columns: [
      { header: 'Name', value: r => r.metadata?.name || '' },
      { header: 'Age', value: r => age(r.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: () => `apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: my-clusterrole
rules:
  - apiGroups: [""]
    resources: ["pods", "nodes"]
    verbs: ["get", "list", "watch"]
`,
    detailSections: withMeta(
      { label: 'Rules', fields: [ { label: 'Rules', value: rbacRules } ] },
    ),
  },
  {
    key: 'clusterrolebindings', kind: 'ClusterRoleBinding', apiVersion: 'rbac.authorization.k8s.io/v1',
    namespaced: false, group: 'rbac', icon: 'Lock', label: 'ClusterRoleBindings',
    listPath: () => apisListPath('rbac.authorization.k8s.io', 'v1', 'clusterrolebindings', ''),
    watchPath: (_ns, rv) => apisWatchPath('rbac.authorization.k8s.io', 'v1', 'clusterrolebindings', '', rv),
    columns: [
      { header: 'Name', value: r => r.metadata?.name || '' },
      { header: 'ClusterRole', value: r => r.roleRef?.name || '', searchable: true },
      { header: 'Subject-Kind', value: r => Array.from(new Set((r.subjects || []).map((s: any) => s.kind))).join(',') || '—' },
      { header: 'Subjects', value: r => (r.subjects || []).map((s: any) => s.name).join(',') || '—', width: 240, searchable: true },
      { header: 'Age', value: r => age(r.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    createTemplate: () => `apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: my-clusterrolebinding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: my-clusterrole
subjects:
  - kind: ServiceAccount
    name: my-serviceaccount
    namespace: default
`,
    detailSections: withMeta(
      { label: 'Binding', fields: [
        { label: 'Role Ref', value: r => `${r.roleRef?.kind || ''}/${r.roleRef?.name || ''}` },
        { label: 'Subjects', value: rbacSubjects },
      ]},
    ),
  },
  // ── Cluster (CRD) ───────────────────────────────────────────
  {
    key: 'customresourcedefinitions', kind: 'CustomResourceDefinition', apiVersion: 'apiextensions.k8s.io/v1',
    namespaced: false, group: 'cluster', icon: 'Component', label: 'CRDs',
    listPath: () => apisListPath('apiextensions.k8s.io', 'v1', 'customresourcedefinitions', ''),
    watchPath: (_ns, rv) => apisWatchPath('apiextensions.k8s.io', 'v1', 'customresourcedefinitions', '', rv),
    columns: [
      { header: 'Name', value: c => c.metadata?.name || '' },
      { header: 'Group', value: c => c.spec?.group || '', searchable: true },
      { header: 'Kind', value: c => c.spec?.names?.kind || '', searchable: true },
      { header: 'Version', value: c => (c.spec?.versions || []).map((v: any) => v.name).join(',') || c.spec?.version || '' },
      { header: 'Scope', value: c => c.spec?.scope || '' },
      { header: 'Age', value: c => age(c.metadata?.creationTimestamp) },
    ],
    actions: ['detail', 'delete'], canCreate: true,
    detailSections: withMeta(
      { label: 'Spec', fields: [
        { label: 'Group', value: c => c.spec?.group || '' },
        { label: 'Kind', value: c => c.spec?.names?.kind || '' },
        { label: 'Plural', value: c => c.spec?.names?.plural || '' },
        { label: 'Scope', value: c => c.spec?.scope || '' },
        { label: 'Versions', value: c => (c.spec?.versions || []).map((v: any) => `${v.name}${v.served ? ' (served)' : ''}${v.storage ? ' (storage)' : ''}`).join('\n') || '—' },
      ]},
    ),
  },
]

export function getResource(key: string): ResourceDescriptor | undefined {
  return RESOURCES.find(r => r.key === key)
}
