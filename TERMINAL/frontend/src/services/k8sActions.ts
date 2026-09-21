// frontend/src/services/k8sActions.ts
import { requestJSON } from './k8sClient'

const RESTART_PATHS: Record<string, string> = {
  Deployment: 'apps/v1/deployments',
  StatefulSet: 'apps/v1/statefulsets',
  DaemonSet: 'apps/v1/daemonsets',
}

function ensureOk(status: number, raw: string) {
  if (status < 200 || status >= 300) throw new Error(`HTTP ${status}: ${raw?.slice(0, 300) || ''}`)
}

export async function deleteResource(connId: string, selfPath: string, force = false): Promise<void> {
  // force：立即删除（gracePeriodSeconds=0）并后台级联删除从属对象。
  const path = force
    ? `${selfPath}${selfPath.includes('?') ? '&' : '?'}gracePeriodSeconds=0&propagationPolicy=Background`
    : selfPath
  const { status, raw } = await requestJSON(connId, 'DELETE', path)
  ensureOk(status, raw)
}

export async function restartWorkload(connId: string, kind: string, ns: string, name: string, nowIso: string): Promise<void> {
  const seg = RESTART_PATHS[kind]
  if (!seg) throw new Error(`restart not supported for ${kind}`)
  const path = `/apis/${seg.split('/')[0]}/${seg.split('/')[1]}/namespaces/${encodeURIComponent(ns)}/${seg.split('/')[2]}/${encodeURIComponent(name)}`
  const body = JSON.stringify({
    spec: { template: { metadata: { annotations: { 'kubectl.kubernetes.io/restartedAt': nowIso } } } },
  })
  const { status, raw } = await requestJSON(connId, 'PATCH', path, body, 'application/strategic-merge-patch+json')
  ensureOk(status, raw)
}

export async function scaleWorkload(connId: string, apiBase: string, _ns: string, name: string, replicas: number): Promise<void> {
  const path = `${apiBase}/${encodeURIComponent(name)}/scale`
  const body = JSON.stringify({ spec: { replicas } })
  const { status, raw } = await requestJSON(connId, 'PATCH', path, body, 'application/merge-patch+json')
  ensureOk(status, raw)
}

export async function cordonNode(connId: string, name: string, unschedulable: boolean): Promise<void> {
  const body = JSON.stringify({ spec: { unschedulable } })
  const { status, raw } = await requestJSON(connId, 'PATCH', `/api/v1/nodes/${encodeURIComponent(name)}`, body, 'application/merge-patch+json')
  ensureOk(status, raw)
}

function isSkippablePod(pod: any): boolean {
  const refs = pod.metadata?.ownerReferences || []
  if (refs.some((r: any) => r.kind === 'DaemonSet')) return true
  // mirror pod (static)
  if (pod.metadata?.annotations?.['kubernetes.io/config.mirror']) return true
  return false
}

export async function drainNode(
  connId: string, name: string,
  onProgress?: (msg: string) => void,
): Promise<{ evicted: number; skipped: number; errors: string[] }> {
  await cordonNode(connId, name, true)
  const { status, data, raw } = await requestJSON<any>(connId, 'GET', `/api/v1/pods?fieldSelector=spec.nodeName%3D${encodeURIComponent(name)}&limit=500`)
  ensureOk(status, raw)
  const pods = data?.items || []
  let evicted = 0, skipped = 0
  const errors: string[] = []
  for (const pod of pods) {
    const pn = pod.metadata?.name, pns = pod.metadata?.namespace
    if (isSkippablePod(pod)) { skipped++; continue }
    const body = JSON.stringify({ apiVersion: 'policy/v1', kind: 'Eviction', metadata: { name: pn, namespace: pns } })
    const r = await requestJSON(connId, 'POST', `/api/v1/namespaces/${encodeURIComponent(pns)}/pods/${encodeURIComponent(pn)}/eviction`, body, 'application/json')
    if (r.status >= 200 && r.status < 300) { evicted++; onProgress?.(`evicted ${pns}/${pn}`) }
    else errors.push(`${pns}/${pn}: HTTP ${r.status}`)
  }
  return { evicted, skipped, errors }
}

export async function createResource(connId: string, collectionPath: string, bodyYaml: string): Promise<void> {
  const { status, raw } = await requestJSON(connId, 'POST', collectionPath, bodyYaml, 'application/yaml')
  ensureOk(status, raw)
}

export async function createNamespace(connId: string, nsName: string): Promise<void> {
  const body = JSON.stringify({ apiVersion: 'v1', kind: 'Namespace', metadata: { name: nsName } })
  const { status, raw } = await requestJSON(connId, 'POST', '/api/v1/namespaces', body, 'application/json')
  ensureOk(status, raw)
}

// Pure: pods owned by `owner`. For Deployments, follow the ReplicaSet layer.
export function podsOfOwner(pods: any[], owner: { uid: string; kind: string }, replicaSets: any[]): any[] {
  if (owner.kind === 'Deployment') {
    const ownedRsUids = new Set(
      replicaSets
        .filter(rs => (rs.metadata?.ownerReferences || []).some((r: any) => r.uid === owner.uid))
        .map(rs => rs.metadata?.uid),
    )
    return pods.filter(p => (p.metadata?.ownerReferences || []).some((r: any) => ownedRsUids.has(r.uid)))
  }
  return pods.filter(p => (p.metadata?.ownerReferences || []).some((r: any) => r.uid === owner.uid))
}

export function podsOnNode(pods: any[], nodeName: string): any[] {
  return pods.filter(p => p.spec?.nodeName === nodeName)
}
