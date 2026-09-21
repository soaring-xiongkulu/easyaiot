import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// mock k8sClient 底层调用，避免真的走 Wails
const requestJSON = vi.fn()
const startWatch = vi.fn()
const stopWatch = vi.fn()

vi.mock('../services/k8sClient', () => ({
  requestJSON: (...a: any[]) => requestJSON(...a),
  startWatch: (...a: any[]) => startWatch(...a),
}))

import { useK8sStore } from './k8sStore'

function mkPod(name: string, ns = 'default', uid = name) {
  return {
    metadata: { name, namespace: ns, uid, resourceVersion: '1', creationTimestamp: new Date().toISOString() },
    status: { phase: 'Running', containerStatuses: [{ ready: true, restartCount: 0 }] },
    spec: { nodeName: 'n1' },
  }
}

describe('k8sStore.subscribe (generic)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    requestJSON.mockReset()
    startWatch.mockReset()
    stopWatch.mockReset()
    startWatch.mockResolvedValue({ id: 'w1', stop: stopWatch })
  })

  it('subscribe(pods, default) lists then getItems returns items', async () => {
    requestJSON.mockResolvedValue({
      status: 200,
      data: { items: [mkPod('p1'), mkPod('p2')], metadata: { resourceVersion: '99' } },
      raw: '',
    })
    const s = useK8sStore()
    await s.subscribe('c1', 'pods', 'default')
    const items = s.getItems('c1', 'pods', 'default')
    expect(items.map((i: any) => i.metadata.name).sort()).toEqual(['p1', 'p2'])
    expect(requestJSON).toHaveBeenCalledWith('c1', 'GET', '/api/v1/namespaces/default/pods?limit=500')
  })

  it('list HTTP error writes to getError', async () => {
    requestJSON.mockResolvedValue({ status: 403, data: null, raw: 'Forbidden' })
    const s = useK8sStore()
    await s.subscribe('c1', 'pods', 'default')
    expect(s.getError('c1', 'pods', 'default')).toContain('403')
  })

  it('unsubscribe with refCount 0 stops watch and clears items', async () => {
    requestJSON.mockResolvedValue({ status: 200, data: { items: [mkPod('p1')], metadata: { resourceVersion: '1' } }, raw: '' })
    const s = useK8sStore()
    await s.subscribe('c1', 'pods', 'default')
    expect(s.getItems('c1', 'pods', 'default').length).toBe(1)
    s.unsubscribe('c1', 'pods', 'default')
    expect(s.getItems('c1', 'pods', 'default').length).toBe(0)
    expect(stopWatch).toHaveBeenCalled()
  })

  it('subscribing different (resource, ns) pairs keeps independent state', async () => {
    requestJSON.mockResolvedValue({ status: 200, data: { items: [], metadata: { resourceVersion: '1' } }, raw: '' })
    const s = useK8sStore()
    await s.subscribe('c1', 'pods', 'default')
    await s.subscribe('c1', 'pods', 'kube-system')
    expect(s.getError('c1', 'pods', 'default')).toBe('')
    expect(s.getError('c1', 'pods', 'kube-system')).toBe('')
  })

  it('unknown resourceKey writes error and does not throw', async () => {
    const s = useK8sStore()
    await s.subscribe('c1', 'no-such-thing', 'default')
    expect(s.getError('c1', 'no-such-thing', 'default')).toMatch(/unknown resource/i)
    expect(requestJSON).not.toHaveBeenCalled()
  })

  it('cluster-scoped resource (nodes) stores state under empty ns regardless of passed ns', async () => {
    requestJSON.mockResolvedValue({ status: 200, data: { items: [], metadata: { resourceVersion: '1' } }, raw: '' })
    const s = useK8sStore()
    await s.subscribe('c1', 'nodes', 'default')
    // 传 'default'，但 nodes 是集群级：state 挂在空 ns 下
    expect(s.getItems('c1', 'nodes', 'anything-else')).toEqual([])
    // 请求 URL 里没有 namespaces/
    expect(requestJSON).toHaveBeenCalledWith('c1', 'GET', '/api/v1/nodes?limit=500')
  })

  it('subscribe survives unsubscribe mid-list (no NPE, no orphan watch)', async () => {
    // requestJSON never resolves until we let it — simulate a slow list call.
    let resolveList: (v: any) => void = () => {}
    requestJSON.mockImplementation(() => new Promise(r => { resolveList = r }))

    const s = useK8sStore()
    const subP = s.subscribe('c1', 'pods', 'default')  // hangs on await
    // Unsubscribe before list resolves.
    s.unsubscribe('c1', 'pods', 'default')
    // Now let the list finish; subscribe should notice state is gone and bail.
    resolveList({ status: 200, data: { items: [{ metadata: { uid: 'p1', name: 'p1' } }], metadata: { resourceVersion: '1' } }, raw: '' })
    await subP
    // No items visible (state was torn down).
    expect(s.getItems('c1', 'pods', 'default')).toEqual([])
    // Watch never started (guarded by the post-list identity check).
    expect(startWatch).not.toHaveBeenCalled()
  })

  it('subscribe survives unsubscribe mid-startWatch (calls stop on the orphan handle)', async () => {
    requestJSON.mockResolvedValue({ status: 200, data: { items: [], metadata: { resourceVersion: '1' } }, raw: '' })
    // Slow startWatch.
    let resolveWatch: (v: any) => void = () => {}
    const orphanStop = vi.fn()
    startWatch.mockImplementation(() => new Promise(r => { resolveWatch = r }))

    const s = useK8sStore()
    const subP = s.subscribe('c1', 'pods', 'default')
    // Let list finish, but startWatch hangs — unsubscribe now.
    await Promise.resolve()  // yield so list resolves
    await Promise.resolve()  // extra tick for chained then
    s.unsubscribe('c1', 'pods', 'default')
    resolveWatch({ id: 'w-orphan', stop: orphanStop })
    await subP
    // Orphan watch handle's stop() was called.
    expect(orphanStop).toHaveBeenCalled()
  })
})
