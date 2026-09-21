import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useTabStore } from './tabStore'
import { usePanelStore } from './panelStore'

describe('tabStore.addNewPanelToWorkspace', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('adds a new panel beside the requested panel and activates it', () => {
    const store = useTabStore()
    const workspace = store.createWorkspaceTab('Workspace', ['panel-a'], {
      root: { type: 'leaf', panelId: 'panel-a' },
    })

    expect(store.addNewPanelToWorkspace(workspace.id, 'panel-b', 'panel-a')).toBe(true)
    expect(workspace.panelIds).toEqual(['panel-a', 'panel-b'])
    expect(workspace.activePanelId).toBe('panel-b')
    expect(workspace.layout.root).toEqual({
      type: 'split',
      direction: 'horizontal',
      sizes: [0.5, 0.5],
      children: [
        { type: 'leaf', panelId: 'panel-a' },
        { type: 'leaf', panelId: 'panel-b' },
      ],
    })
  })

  it('returns false when the target workspace no longer exists', () => {
    const store = useTabStore()
    expect(store.addNewPanelToWorkspace('missing', 'panel-b')).toBe(false)
  })

  it('accepts the first panel on an empty workspace (placeholder root)', () => {
    const store = useTabStore()
    const workspace = store.createWorkspaceTab('Workspace', [], {
      root: { type: 'leaf', panelId: '' },
    })

    expect(store.addNewPanelToWorkspace(workspace.id, 'panel-a')).toBe(true)
    expect(workspace.panelIds).toEqual(['panel-a'])
    expect(workspace.activePanelId).toBe('panel-a')
    expect(workspace.layout.root).toEqual({ type: 'leaf', panelId: 'panel-a' })
  })

  it('honors direction and insertBefore placement (drop-position split)', () => {
    const store = useTabStore()
    const workspace = store.createWorkspaceTab('Workspace', ['panel-a'], {
      root: { type: 'leaf', panelId: 'panel-a' },
    })

    expect(store.addNewPanelToWorkspace(workspace.id, 'panel-b', 'panel-a', 'vertical', true)).toBe(true)
    expect(workspace.layout.root).toEqual({
      type: 'split',
      direction: 'vertical',
      sizes: [0.5, 0.5],
      children: [
        { type: 'leaf', panelId: 'panel-b' },
        { type: 'leaf', panelId: 'panel-a' },
      ],
    })
  })
})

describe('tabStore.dissolveWorkspace', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function seedWorkspace(count: number) {
    const store = useTabStore()
    const panelStore = usePanelStore()
    const panelIds = Array.from({ length: count }, (_, i) => {
      const p = panelStore.createPanel(null, 'ssh')
      panelStore.updateTitle(p.id, `Panel ${i}`)
      return p.id
    })
    const layout = panelIds.length === 1
      ? { root: { type: 'leaf' as const, panelId: panelIds[0] } }
      : {
          root: {
            type: 'split' as const,
            direction: 'horizontal' as const,
            sizes: panelIds.map(() => 1 / panelIds.length),
            children: panelIds.map(id => ({ type: 'leaf' as const, panelId: id })),
          },
        }
    const ws = store.createWorkspaceTab('WS', [...panelIds], layout)
    for (const id of panelIds) panelStore.movePanelToTab(id, ws.id)
    return { store, ws, panelStore, panelIds }
  }

  it('splices member panels back as terminal tabs in visual order', () => {
    const { store, ws, panelStore, panelIds } = seedWorkspace(3)
    const before = store.tabs.length

    const created = store.dissolveWorkspace(ws.id)

    expect(created.map(t => t.panelId)).toEqual(panelIds)
    expect(created.every(t => t.type === 'terminal')).toBe(true)
    // Workspace gone, 3 terminal tabs in its place
    expect(store.tabs.some(t => t.id === ws.id)).toBe(false)
    expect(store.tabs.length).toBe(before - 1 + 3)
    // Panels are re-pointed at the new tabs and still alive in the panel store
    created.forEach(t => expect(panelStore.getPanel(t.panelId)?.tabId).toBe(t.id))
    // First created tab becomes active
    expect(store.activeTabId).toBe(created[0].id)
  })

  it('clears broadcast participation but keeps AI lock', () => {
    const { store, ws, panelIds } = seedWorkspace(2)
    const [a, b] = panelIds
    store.addAILockedPanel(a)
    store.toggleBroadcastPanel(a)
    store.toggleBroadcastPanel(b)
    expect([...store.getAllBroadcastPanelIds()].sort()).toEqual([a, b].sort())

    store.dissolveWorkspace(ws.id)

    expect(store.getAllBroadcastPanelIds()).toEqual([])
    expect(store.isPanelAILocked(a)).toBe(true)
  })

  it('clears drag tracking when dissolving mid-drag', () => {
    const { store, ws } = seedWorkspace(1)
    store.setDraggingTabId(ws.id)

    store.dissolveWorkspace(ws.id)

    expect(store.draggingTabId).toBeNull()
  })

  it('returns empty for a missing workspace', () => {
    const store = useTabStore()
    expect(store.dissolveWorkspace('missing')).toEqual([])
  })
})

describe('tabStore.applyWorkspaceLayout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function seedPanel(id: string) {
    const panelStore = usePanelStore()
    const p = panelStore.createPanel(null, 'ssh')
    // Tests need a deterministic id; re-key the map entry.
    panelStore.panels.delete(p.id)
    p.id = id
    panelStore.panels.set(id, p)
    return p
  }

  it('sets the layout and derives panelIds', () => {
    const store = useTabStore()
    const ws = store.createWorkspaceTab('WS', [], { root: { type: 'leaf', panelId: '' } })
    seedPanel('p1')
    seedPanel('p2')

    const ok = store.applyWorkspaceLayout(ws.id, {
      root: {
        type: 'split',
        direction: 'horizontal',
        sizes: [0.5, 0.5],
        children: [
          { type: 'leaf', panelId: 'p1' },
          { type: 'leaf', panelId: 'p2' },
        ],
      },
    })

    expect(ok).toBe(true)
    expect(ws.panelIds).toEqual(['p1', 'p2'])
    expect(ws.layout.root.type).toBe('split')
  })

  it('prunes leaves referencing dead panels and collapses splits', () => {
    const store = useTabStore()
    const ws = store.createWorkspaceTab('WS', [], { root: { type: 'leaf', panelId: '' } })
    seedPanel('alive')

    store.applyWorkspaceLayout(ws.id, {
      root: {
        type: 'split',
        direction: 'horizontal',
        sizes: [0.5, 0.5],
        children: [
          { type: 'leaf', panelId: 'alive' },
          { type: 'leaf', panelId: 'ghost' },
        ],
      },
    })

    expect(ws.panelIds).toEqual(['alive'])
    expect(ws.layout.root).toEqual({ type: 'leaf', panelId: 'alive' })
  })

  it('rejects a fully-dead layout without corrupting the workspace', () => {
    const store = useTabStore()
    const ws = store.createWorkspaceTab('WS', [], { root: { type: 'leaf', panelId: '' } })

    const ok = store.applyWorkspaceLayout(ws.id, { root: { type: 'leaf', panelId: 'ghost' } })

    expect(ok).toBe(false)
    expect(ws.layout.root).toEqual({ type: 'leaf', panelId: '' })
  })
})

describe('tabStore.buildGridLayout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('returns a single leaf for one panel', () => {
    const store = useTabStore()
    expect(store.buildGridLayout(['p1'])).toEqual({ root: { type: 'leaf', panelId: 'p1' } })
  })

  it('balances three panels into a 1-vs-2 split with equal areas', () => {
    const store = useTabStore()
    const layout = store.buildGridLayout(['p1', 'p2', 'p3'])
    expect(layout.root).toEqual({
      type: 'split',
      direction: 'horizontal',
      sizes: [1 / 3, 2 / 3],
      children: [
        { type: 'leaf', panelId: 'p1' },
        {
          type: 'split',
          direction: 'vertical',
          sizes: [0.5, 0.5],
          children: [
            { type: 'leaf', panelId: 'p2' },
            { type: 'leaf', panelId: 'p3' },
          ],
        },
      ],
    })
  })

  it('handles five panels without degenerate chains', () => {
    const store = useTabStore()
    const root = store.buildGridLayout(['p1', 'p2', 'p3', 'p4', 'p5']).root
    expect(root.type).toBe('split')
    const leaves = store.collectPanelIds(root)
    expect(leaves).toEqual(['p1', 'p2', 'p3', 'p4', 'p5'])
  })
})
