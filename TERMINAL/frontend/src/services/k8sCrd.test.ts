import { describe, it, expect } from 'vitest'
import { parseCRD, evalJsonPath, crdListPath } from './k8sCrd'

const crd = {
  spec: {
    group: 'example.com',
    names: { plural: 'widgets', kind: 'Widget' },
    scope: 'Namespaced',
    versions: [
      { name: 'v1alpha1', served: true, storage: false, additionalPrinterColumns: [] },
      { name: 'v1', served: true, storage: true, additionalPrinterColumns: [
        { name: 'Size', jsonPath: '.spec.size', type: 'string' },
        { name: 'Phase', jsonPath: '.status.phase' },
      ] },
    ],
  },
}

describe('k8sCrd', () => {
  it('parseCRD picks the storage version and its printer columns', () => {
    const p = parseCRD(crd)
    expect(p.group).toBe('example.com')
    expect(p.version).toBe('v1')
    expect(p.plural).toBe('widgets')
    expect(p.kind).toBe('Widget')
    expect(p.scope).toBe('Namespaced')
    expect(p.printerColumns.map(c => c.name)).toEqual(['Size', 'Phase'])
  })
  it('parseCRD falls back to first served version when none marked storage', () => {
    const noStorage = { spec: { ...crd.spec, versions: [{ name: 'v2', served: true, storage: false }] } }
    expect(parseCRD(noStorage).version).toBe('v2')
  })
  it('evalJsonPath reads nested + indexed paths', () => {
    const obj = { spec: { size: 'L' }, status: { conditions: [{ type: 'Ready' }] } }
    expect(evalJsonPath(obj, '.spec.size')).toBe('L')
    expect(evalJsonPath(obj, '.status.conditions[0].type')).toBe('Ready')
    expect(evalJsonPath(obj, '.missing.path')).toBe('')
  })
  it('crdListPath respects scope + namespace', () => {
    const p = parseCRD(crd)
    expect(crdListPath(p, 'default')).toBe('/apis/example.com/v1/namespaces/default/widgets?limit=500')
    const cluster = parseCRD({ spec: { ...crd.spec, scope: 'Cluster' } })
    expect(crdListPath(cluster, '')).toBe('/apis/example.com/v1/widgets?limit=500')
  })
})
