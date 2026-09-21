// frontend/src/services/k8sCrd.ts
import type { ParsedCRD } from '../types/k8s'

export function parseCRD(obj: any): ParsedCRD {
  const spec = obj?.spec || {}
  const versions = spec.versions || []
  const chosen =
    versions.find((v: any) => v.served && v.storage) ||
    versions.find((v: any) => v.served) ||
    versions[0] || {}
  const printerColumns = (chosen.additionalPrinterColumns || []).map((c: any) => ({
    name: c.name,
    jsonPath: c.jsonPath || c.JSONPath || '',
    type: c.type,
  }))
  return {
    group: spec.group || '',
    version: chosen.name || '',
    plural: spec.names?.plural || '',
    kind: spec.names?.kind || '',
    scope: spec.scope === 'Cluster' ? 'Cluster' : 'Namespaced',
    printerColumns,
  }
}

// Minimal JSONPath: leading '.', dotted keys, optional [index]. Returns '' on any miss.
export function evalJsonPath(obj: any, path: string): string {
  if (!path) return ''
  const clean = path.startsWith('.') ? path.slice(1) : path
  let cur: any = obj
  for (const seg of clean.split('.')) {
    if (cur == null) return ''
    const m = seg.match(/^([^[\]]+)(?:\[(\d+)\])?$/)
    if (!m) return ''
    cur = cur[m[1]]
    if (m[2] != null) {
      if (!Array.isArray(cur)) return ''
      cur = cur[Number(m[2])]
    }
  }
  if (cur == null) return ''
  return typeof cur === 'object' ? JSON.stringify(cur) : String(cur)
}

export function crdListPath(crd: ParsedCRD, ns: string): string {
  const base = crd.scope === 'Namespaced' && ns
    ? `/apis/${crd.group}/${crd.version}/namespaces/${encodeURIComponent(ns)}/${crd.plural}`
    : `/apis/${crd.group}/${crd.version}/${crd.plural}`
  return `${base}?limit=500`
}
