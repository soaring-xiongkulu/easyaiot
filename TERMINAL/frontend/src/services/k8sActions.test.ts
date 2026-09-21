import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('./k8sClient', () => ({
  requestJSON: vi.fn(async () => ({ status: 200, data: {}, raw: '' })),
}))
import { requestJSON } from './k8sClient'
import {
  podsOfOwner, podsOnNode, restartWorkload, scaleWorkload, cordonNode, createNamespace,
} from './k8sActions'

const mockReq = requestJSON as unknown as ReturnType<typeof vi.fn>
beforeEach(() => mockReq.mockClear())

describe('k8sActions pure filters', () => {
  const rs = { metadata: { uid: 'rs1', ownerReferences: [{ uid: 'deploy1', kind: 'Deployment' }] } }
  const podDirect = { metadata: { name: 'p1', ownerReferences: [{ uid: 'ds1' }] }, spec: { nodeName: 'n1' } }
  const podViaRs = { metadata: { name: 'p2', ownerReferences: [{ uid: 'rs1' }] }, spec: { nodeName: 'n2' } }

  it('podsOfOwner matches direct owner uid', () => {
    const out = podsOfOwner([podDirect, podViaRs], { uid: 'ds1', kind: 'DaemonSet' }, [])
    expect(out.map(p => p.metadata.name)).toEqual(['p1'])
  })
  it('podsOfOwner follows ReplicaSet layer for Deployments', () => {
    const out = podsOfOwner([podDirect, podViaRs], { uid: 'deploy1', kind: 'Deployment' }, [rs])
    expect(out.map(p => p.metadata.name)).toEqual(['p2'])
  })
  it('podsOnNode filters by spec.nodeName', () => {
    expect(podsOnNode([podDirect, podViaRs], 'n1').map(p => p.metadata.name)).toEqual(['p1'])
  })
})

describe('k8sActions request shapes', () => {
  it('restartWorkload PATCHes restartedAt annotation', async () => {
    await restartWorkload('c', 'Deployment', 'default', 'web', '2026-07-25T00:00:00Z')
    const [, method, path, body, ct] = mockReq.mock.calls[0]
    expect(method).toBe('PATCH')
    expect(path).toBe('/apis/apps/v1/namespaces/default/deployments/web')
    expect(JSON.parse(body).spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt']).toBe('2026-07-25T00:00:00Z')
    expect(ct).toBe('application/strategic-merge-patch+json')
  })
  it('scaleWorkload PATCHes /scale with replicas', async () => {
    await scaleWorkload('c', '/apis/apps/v1/namespaces/default/deployments', 'default', 'web', 3)
    const [, method, path, body, ct] = mockReq.mock.calls[0]
    expect(method).toBe('PATCH')
    expect(path).toBe('/apis/apps/v1/namespaces/default/deployments/web/scale')
    expect(JSON.parse(body).spec.replicas).toBe(3)
    expect(ct).toBe('application/merge-patch+json')
  })
  it('cordonNode PATCHes spec.unschedulable', async () => {
    await cordonNode('c', 'n1', true)
    const [, method, path, body] = mockReq.mock.calls[0]
    expect(method).toBe('PATCH')
    expect(path).toBe('/api/v1/nodes/n1')
    expect(JSON.parse(body).spec.unschedulable).toBe(true)
  })
  it('createNamespace POSTs minimal body', async () => {
    await createNamespace('c', 'demo')
    const [, method, path, body] = mockReq.mock.calls[0]
    expect(method).toBe('POST')
    expect(path).toBe('/api/v1/namespaces')
    expect(JSON.parse(body)).toEqual({ apiVersion: 'v1', kind: 'Namespace', metadata: { name: 'demo' } })
  })
})
