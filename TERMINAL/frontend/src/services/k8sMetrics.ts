// frontend/src/services/k8sMetrics.ts
import { requestJSON } from './k8sClient'
import { parseCpu, parseMemory } from './k8sQuantity'

export interface Usage { cpu: number; mem: number }   // cpu millicores, mem bytes

export function parsePodMetricsList(raw: any): Map<string, Usage> {
  const out = new Map<string, Usage>()
  for (const it of raw?.items || []) {
    const ns = it.metadata?.namespace || ''
    const name = it.metadata?.name || ''
    let cpu = 0, mem = 0
    for (const c of it.containers || []) {
      cpu += parseCpu(c.usage?.cpu || '')
      mem += parseMemory(c.usage?.memory || '')
    }
    out.set(`${ns}/${name}`, { cpu, mem })
  }
  return out
}

export function parseNodeMetricsList(raw: any): Map<string, Usage> {
  const out = new Map<string, Usage>()
  for (const it of raw?.items || []) {
    out.set(it.metadata?.name || '', {
      cpu: parseCpu(it.usage?.cpu || ''),
      mem: parseMemory(it.usage?.memory || ''),
    })
  }
  return out
}

// Returns null when metrics-server is absent (404) — caller renders '—'.
export async function fetchPodMetrics(connId: string, ns: string): Promise<Map<string, Usage> | null> {
  const path = ns
    ? `/apis/metrics.k8s.io/v1beta1/namespaces/${encodeURIComponent(ns)}/pods`
    : `/apis/metrics.k8s.io/v1beta1/pods`
  const { status, data } = await requestJSON<any>(connId, 'GET', path)
  if (status === 404 || !data) return null
  return parsePodMetricsList(data)
}

export async function fetchNodeMetrics(connId: string): Promise<Map<string, Usage> | null> {
  const { status, data } = await requestJSON<any>(connId, 'GET', '/apis/metrics.k8s.io/v1beta1/nodes')
  if (status === 404 || !data) return null
  return parseNodeMetricsList(data)
}
