import { describe, it, expect } from 'vitest'
import { RESOURCES, getResource } from './k8sResources'

describe('k8sResources', () => {
  it('exposes at least Pods', () => {
    const pods = getResource('pods')
    expect(pods).toBeTruthy()
    expect(pods!.kind).toBe('Pod')
    expect(pods!.apiVersion).toBe('v1')
    expect(pods!.namespaced).toBe(true)
    expect(pods!.group).toBe('workloads')
  })

  it('pods listPath varies by namespace', () => {
    const pods = getResource('pods')!
    expect(pods.listPath('default')).toBe('/api/v1/namespaces/default/pods?limit=500')
    expect(pods.listPath('')).toBe('/api/v1/pods?limit=500')
  })

  it('pods watchPath includes resourceVersion', () => {
    const pods = getResource('pods')!
    const wp = pods.watchPath('kube-system', '12345')
    expect(wp).toContain('/api/v1/namespaces/kube-system/pods')
    expect(wp).toContain('watch=true')
    expect(wp).toContain('resourceVersion=12345')
    expect(wp).toContain('allowWatchBookmarks=true')
  })

  it('pods columns cover Name / Namespace / Ready / Status / Restarts / Age / Node', () => {
    const pods = getResource('pods')!
    const headers = pods.columns.map(c => c.header)
    // Assert containment rather than exact equality — the metrics columns
    // (CPU / MEM / request-limit percentages / IP) sit between Restarts and
    // Node, and more may be added.
    for (const core of ['Name', 'Namespace', 'Ready', 'Status', 'Restarts', 'Age', 'Node']) {
      expect(headers).toContain(core)
    }
  })

  it('every column value fn returns non-undefined for a minimal pod fixture', () => {
    const pods = getResource('pods')!
    const pod = {
      metadata: { name: 'p', namespace: 'default', uid: 'u1', creationTimestamp: new Date().toISOString() },
      status: { phase: 'Running', containerStatuses: [{ ready: true, restartCount: 0 }] },
      spec: { nodeName: 'n1' },
    }
    for (const col of pods.columns) {
      const v = col.value(pod)
      expect(v).not.toBeUndefined()
    }
  })

  it('RESOURCES array contains pods', () => {
    expect(RESOURCES.find(r => r.key === 'pods')).toBeTruthy()
  })
})

describe('k8sResources completeness', () => {
  const EXPECTED_KEYS = [
    'pods', 'deployments', 'statefulsets', 'daemonsets', 'jobs', 'cronjobs', 'replicasets',
    'services', 'ingresses',
    'configmaps', 'secrets',
    'persistentvolumeclaims', 'persistentvolumes',
    'nodes', 'namespaces', 'events',
  ]

  it('contains all 16 built-in resources', () => {
    const keys = RESOURCES.map(r => r.key).sort()
    expect(keys).toEqual(expect.arrayContaining([...EXPECTED_KEYS].sort()))
  })

  it('cluster-scoped resources are marked namespaced: false', () => {
    const clusterScoped = ['nodes', 'persistentvolumes', 'namespaces']
    for (const k of clusterScoped) {
      const r = getResource(k)!
      expect(r.namespaced).toBe(false)
    }
  })

  it('every descriptor: listPath/watchPath return strings, columns non-empty', () => {
    for (const r of RESOURCES) {
      const lp = r.listPath(r.namespaced ? 'default' : '')
      expect(typeof lp).toBe('string')
      expect(lp.length).toBeGreaterThan(0)
      const wp = r.watchPath(r.namespaced ? 'default' : '', '1')
      expect(wp).toContain('watch=true')
      expect(r.columns.length).toBeGreaterThan(0)
    }
  })

  it('every column value fn tolerates a mostly-empty object', () => {
    const empty = { metadata: { name: 'x', namespace: 'default', uid: 'u', creationTimestamp: new Date().toISOString() } }
    for (const r of RESOURCES) {
      for (const c of r.columns) {
        expect(() => c.value(empty)).not.toThrow()
      }
    }
  })
})

describe('descriptor actions + canCreate', () => {
  it('pods support detail/logs/terminal/delete and canCreate', () => {
    const p = getResource('pods')!
    expect(p.actions).toEqual(['detail', 'logs', 'terminal', 'delete'])
    expect(p.canCreate).toBe(true)
  })
  it('deployments support viewPods/restart/scale', () => {
    const d = getResource('deployments')!
    expect(d.actions).toEqual(expect.arrayContaining(['viewPods', 'restart', 'scale', 'delete']))
  })
  it('nodes support cordon/drain, not creatable', () => {
    const n = getResource('nodes')!
    expect(n.actions).toEqual(expect.arrayContaining(['cordon', 'drain', 'viewPods']))
    expect(n.canCreate).toBe(false)
  })
  it('events are detail-only', () => {
    expect(getResource('events')!.actions).toEqual(['detail'])
  })
})

describe('column filterable', () => {
  it('pod Status column is enum-filterable', () => {
    const status = getResource('pods')!.columns.find(c => c.header === 'Status')!
    expect(status.filterable).toEqual({ type: 'enum' })
  })
  it('service Type column is enum-filterable', () => {
    const t = getResource('services')!.columns.find(c => c.header === 'Type')!
    expect(t.filterable).toEqual({ type: 'enum' })
  })
})

describe('expanded resources', () => {
  const NEW_KEYS = [
    'horizontalpodautoscalers', 'networkpolicies', 'endpoints',
    'resourcequotas', 'limitranges', 'storageclasses',
    'serviceaccounts', 'roles', 'rolebindings', 'clusterroles', 'clusterrolebindings',
    'customresourcedefinitions',
  ]
  it('all new resources present with valid paths', () => {
    for (const k of NEW_KEYS) {
      const r = getResource(k)
      expect(r, k).toBeTruthy()
      expect(r!.listPath(r!.namespaced ? 'default' : '').startsWith('/api')).toBe(true)
    }
  })
  it('rbac resources are in the rbac group', () => {
    expect(getResource('clusterroles')!.group).toBe('rbac')
    expect(getResource('serviceaccounts')!.group).toBe('rbac')
  })
  it('cluster-scoped new resources marked namespaced:false', () => {
    for (const k of ['storageclasses', 'clusterroles', 'clusterrolebindings', 'customresourcedefinitions']) {
      expect(getResource(k)!.namespaced, k).toBe(false)
    }
  })
  it('endpoints not creatable', () => {
    expect(getResource('endpoints')!.canCreate).toBe(false)
  })
})
