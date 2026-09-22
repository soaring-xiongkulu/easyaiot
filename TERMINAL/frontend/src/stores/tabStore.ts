import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'
import type { Tab, TerminalTab, WorkspaceTab, StartTab, PanelLayout, LayoutNode } from '../types/workspace'
import type { IProgressState } from '@xterm/addon-progress'
import { usePanelStore } from './panelStore'
import { t } from '../i18n'

const tabState = reactive<{
  tabs: Tab[]
  activeTabId: string | null
  // Id of the tab currently being dragged (set at dragstart, cleared at
  // dragend). dataTransfer.getData is unavailable outside the drop event, so
  // dragover handlers need this to recognize the dragged tab.
  draggingTabId: string | null
  // Id of the workspace panel currently being dragged — same rationale as
  // draggingTabId: dragover handlers need it to detect "over itself".
  draggingPanelId: string | null
  broadcastPanelIds: Set<string>
  tabNotifications: Record<string, boolean>
  /** OSC 9;4 progress state per tab (null = no active progress). Fed by the
   * ProgressAddon via terminalManager; rendered as a mini bar in TabItem. */
  tabProgress: Record<string, IProgressState | null>
}>({
  tabs: [],
  activeTabId: null,
  draggingTabId: null,
  draggingPanelId: null,
  broadcastPanelIds: new Set<string>(),
  tabNotifications: {},
  tabProgress: {}
})

let idCounter = 0
function genId(prefix: string): string {
  return `${prefix}-${Date.now()}-${++idCounter}`
}

function generateWorkspaceName(existingTabs: Tab[]): string {
  const base = t('workspace.defaultName')
  const existingNames = existingTabs.filter(t => t.type === 'workspace').map(t => t.name)
  if (!existingNames.includes(base)) return base
  let i = 2
  while (existingNames.includes(`${base} (${i})`)) i++
  return `${base} (${i})`
}

export const useTabStore = defineStore('tab', () => {
  const tabs = computed(() => tabState.tabs)
  const activeTabId = computed(() => tabState.activeTabId)
  const draggingTabId = computed(() => tabState.draggingTabId)
  const draggingPanelId = computed(() => tabState.draggingPanelId)
  const activeTab = computed(() =>
    tabState.tabs.find(t => t.id === tabState.activeTabId) || null
  )
  const broadcastPanelIds = computed(() => tabState.broadcastPanelIds)

  // Panel-level: whether a specific panel is participating in broadcast.
  function isPanelBroadcasting(panelId: string): boolean {
    return tabState.broadcastPanelIds.has(panelId)
  }

  // Workspace-level: any panel in the workspace is participating.
  // Used for the button's active-highlight fallback and for legacy
  // "if broadcasting, send to all" call sites (history / quick commands).
  function isBroadcasting(workspaceId: string): boolean {
    const tab = tabState.tabs.find(t => t.id === workspaceId)
    if (!tab || tab.type !== 'workspace') return false
    return tab.panelIds.some(id => tabState.broadcastPanelIds.has(id))
  }

  // Return the set of panels broadcasting within a given workspace.
  function getBroadcastPanelIdsInWorkspace(workspaceId: string): string[] {
    const tab = tabState.tabs.find(t => t.id === workspaceId)
    if (!tab || tab.type !== 'workspace') return []
    return tab.panelIds.filter(id => tabState.broadcastPanelIds.has(id))
  }

  // Plain click: if any panel in this workspace broadcasts, turn all off;
  // otherwise turn all ssh/local panels on.
  function toggleBroadcast(workspaceId: string) {
    const tab = tabState.tabs.find(t => t.id === workspaceId)
    if (!tab || tab.type !== 'workspace') return
    const panelStore = usePanelStore()
    const anyOn = tab.panelIds.some(id => tabState.broadcastPanelIds.has(id))
    if (anyOn) {
      for (const id of tab.panelIds) tabState.broadcastPanelIds.delete(id)
    } else {
      for (const id of tab.panelIds) {
        const p = panelStore.getPanel(id)
        if (p && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')) {
          tabState.broadcastPanelIds.add(id)
        }
      }
    }
  }

  // Ctrl+click: toggle just this panel's participation.
  function toggleBroadcastPanel(panelId: string) {
    if (tabState.broadcastPanelIds.has(panelId)) {
      tabState.broadcastPanelIds.delete(panelId)
    } else {
      tabState.broadcastPanelIds.add(panelId)
    }
  }

  // Tab-level broadcast target helpers. A tab is a "broadcast target" when any
  // broadcastable (ssh/local) panel it holds participates in broadcast — a
  // single panel for terminal tabs, every ssh/local panel for workspace tabs.
  // These are derived from broadcastPanelIds, so tab icons and the panel
  // broadcast buttons always stay in sync.

  function isTabBroadcastTarget(tabId: string): boolean {
    const tab = tabState.tabs.find(t => t.id === tabId)
    if (!tab) return false
    if (tab.type === 'workspace') {
      return tab.panelIds.some(id => tabState.broadcastPanelIds.has(id))
    }
    if ('panelId' in tab) return tabState.broadcastPanelIds.has(tab.panelId)
    return false
  }

  // Turn on broadcast for every ssh/local panel the tab holds.
  function enableBroadcastForTab(tabId: string) {
    const tab = tabState.tabs.find(t => t.id === tabId)
    if (!tab) return
    const panelStore = usePanelStore()
    const ids = tab.type === 'workspace' ? tab.panelIds : 'panelId' in tab ? [tab.panelId] : []
    for (const id of ids) {
      const p = panelStore.getPanel(id)
      if (p && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')) {
        tabState.broadcastPanelIds.add(id)
      }
    }
  }

  // Turn off broadcast for every panel the tab holds.
  function disableBroadcastForTab(tabId: string) {
    const tab = tabState.tabs.find(t => t.id === tabId)
    if (!tab) return
    const ids = tab.type === 'workspace' ? tab.panelIds : 'panelId' in tab ? [tab.panelId] : []
    for (const id of ids) tabState.broadcastPanelIds.delete(id)
  }

  // Every panel participating in broadcast across all tabs. Cross-tab: the
  // input router uses this instead of workspace-scoped targets.
  function getAllBroadcastPanelIds(): string[] {
    return [...tabState.broadcastPanelIds]
  }

  // ── Create tabs ──

  function createTerminalTab(name: string, panelId: string): TerminalTab {
    const tab: TerminalTab = {
      type: 'terminal',
      id: genId('term-tab'),
      panelId,
      name
    }
    tabState.tabs.push(tab)
    tabState.activeTabId = tab.id
    return tab
  }

  function createTerminalTabAt(name: string, panelId: string, index: number): TerminalTab {
    const tab: TerminalTab = {
      type: 'terminal',
      id: genId('term-tab'),
      panelId,
      name
    }
    tabState.tabs.splice(index, 0, tab)
    tabState.activeTabId = tab.id
    return tab
  }

  // Remove the start tab at startTabId and create a terminal tab in its
  // position — atomic replacement that avoids flicker and auto-create races.
  function replaceStartTab(startTabId: string, name: string, panelId: string): TerminalTab {
    const startIdx = tabState.tabs.findIndex(t => t.id === startTabId)
    if (startIdx === -1) {
      return createTerminalTab(name, panelId)
    }
    tabState.tabs.splice(startIdx, 1)
    return createTerminalTabAt(name, panelId, startIdx)
  }

  // Generic replacement: remove start tab and insert any tab type at its position.
  function replaceStartWithTab(startTabId: string, tab: Tab): Tab {
    const startIdx = tabState.tabs.findIndex(t => t.id === startTabId)
    if (startIdx === -1) {
      tabState.tabs.push(tab)
    } else {
      tabState.tabs.splice(startIdx, 1, tab)
    }
    tabState.activeTabId = tab.id
    return tab
  }

  // Single factory for the uniform tab kinds — push + activate, parameterized
  // by tab type. `extra` carries the fields only some kinds have (k8s:
  // connectionId/namespace, container: runtime/connectionId). Terminal tabs
  // keep dedicated creators (insert-at-index, start-tab replacement);
  // workspace/start tabs build richer state.
  function createTab(type: Tab['type'], name: string, panelId: string, extra?: Record<string, unknown>): Tab {
    const tab = { type, id: genId(`${type}-tab`), panelId, name, ...extra } as Tab
    tabState.tabs.push(tab)
    tabState.activeTabId = tab.id
    return tab
  }

  function createStartTab(): StartTab {
    const tab: StartTab = {
      type: 'start',
      id: genId('start-tab'),
      name: t('startTab.defaultName'),
      viewMode: 'home'
    }
    tabState.tabs.push(tab)
    tabState.activeTabId = tab.id
    return tab
  }

  function createWorkspaceTab(name: string, panelIds: string[], layout: PanelLayout): WorkspaceTab {
    const tab: WorkspaceTab = {
      type: 'workspace',
      id: genId('ws-tab'),
      name,
      panelIds: [...panelIds],
      layout,
      activePanelId: panelIds[0] || null
    }
    tabState.tabs.push(tab)
    tabState.activeTabId = tab.id
    return tab
  }

  // ── Close tab ──

  function closeTab(id: string): string[] {
    const idx = tabState.tabs.findIndex(t => t.id === id)
    if (idx === -1) return []
    const removed = tabState.tabs.splice(idx, 1)[0]

    if (tabState.activeTabId === id) {
      // Activate nearest tab (prefer right, then left)
      if (tabState.tabs.length > 0) {
        const newIdx = Math.min(idx, tabState.tabs.length - 1)
        tabState.activeTabId = tabState.tabs[newIdx].id
      } else {
        tabState.activeTabId = null
      }
    }

    // Collect panel ids removed with this tab so callers can clean up
    // per-panel state (e.g. broadcast participation).
    const removedPanelIds: string[] = (() => {
      if (removed.type === 'start') return []
      if (removed.type === 'workspace') return removed.panelIds
      return [removed.panelId]
    })()

    for (const pid of removedPanelIds) {
      tabState.broadcastPanelIds.delete(pid)
    }

    return removedPanelIds
  }

  // ── Activate / reorder / rename ──

  function setDraggingTabId(id: string | null) {
    tabState.draggingTabId = id
  }

  function setDraggingPanelId(id: string | null) {
    tabState.draggingPanelId = id
  }

  function setActiveTab(id: string) {
    tabState.activeTabId = id
    // Clear notification dot when user switches to this tab
    tabState.tabNotifications[id] = false
  }

  // ── Notification dots ──

  function markTabNotification(tabId: string) {
    tabState.tabNotifications[tabId] = true
  }

  function clearTabNotification(tabId: string) {
    tabState.tabNotifications[tabId] = false
  }

  function hasTabNotification(tabId: string): boolean {
    return !!tabState.tabNotifications[tabId]
  }

  // ── Progress indicators (OSC 9;4) ──

  function setTabProgress(tabId: string, state: IProgressState | null) {
    tabState.tabProgress[tabId] = state
  }

  function getTabProgress(tabId: string): IProgressState | null {
    return tabState.tabProgress[tabId] ?? null
  }

  function nextTab() {
    const idx = tabState.tabs.findIndex(t => t.id === tabState.activeTabId)
    if (idx < 0) return
    const next = tabState.tabs[(idx + 1) % tabState.tabs.length]
    tabState.activeTabId = next.id
  }

  function prevTab() {
    const idx = tabState.tabs.findIndex(t => t.id === tabState.activeTabId)
    if (idx < 0) return
    const next = tabState.tabs[(idx - 1 + tabState.tabs.length) % tabState.tabs.length]
    tabState.activeTabId = next.id
  }

  function getActivePanelId(): string | null {
    const t = tabState.tabs.find(t => t.id === tabState.activeTabId)
    if (!t) return null
    if (t.type === 'workspace') return t.activePanelId || t.panelIds[0] || null
    if ('panelId' in t) return (t as any).panelId as string
    return null
  }

  function moveTab(fromIdx: number, toIdx: number) {
    const [t] = tabState.tabs.splice(fromIdx, 1)
    tabState.tabs.splice(toIdx, 0, t)
  }

  function renameTab(id: string, name: string) {
    const t = tabState.tabs.find(x => x.id === id)
    if (t) t.name = name
    // Sync panel title for terminal tabs
    if (t && t.type === 'terminal') {
      const panelStore = usePanelStore()
      const panel = panelStore.getPanel(t.panelId)
      if (panel) panelStore.updateTitle(panel.id, name)
    }
  }

  // ── Workspace panel management ──

  function setActivePanel(tabId: string, panelId: string) {
    const t = tabState.tabs.find(x => x.id === tabId)
    if (t && t.type === 'workspace') {
      t.activePanelId = panelId
      if (t.maximizedPanelId) t.maximizedPanelId = panelId
    }
  }

  function toggleWorkspacePanelMaximize(tabId: string) {
    const t = tabState.tabs.find(x => x.id === tabId)
    if (!t || t.type !== 'workspace' || !t.activePanelId) return null
    t.maximizedPanelId = t.maximizedPanelId ? null : t.activePanelId
    return t.maximizedPanelId
  }

  function updateWorkspaceLayout(tabId: string, layout: PanelLayout) {
    const t = tabState.tabs.find(x => x.id === tabId)
    if (t && t.type === 'workspace') {
      t.layout = layout
      // Sync panelIds from layout
      t.panelIds = collectPanelIds(layout.root)
    }
  }

  // ── Merge: two terminal tabs → workspace tab ──

  function mergeToWorkspace(
    terminalTabAId: string,
    terminalTabBId: string,
    direction: 'horizontal' | 'vertical',
    insertBefore: boolean
  ): WorkspaceTab | null {
    const idxA = tabState.tabs.findIndex(t => t.id === terminalTabAId)
    const idxB = tabState.tabs.findIndex(t => t.id === terminalTabBId)
    if (idxA === -1 || idxB === -1) return null

    const tabA = tabState.tabs[idxA] as TerminalTab
    const tabB = tabState.tabs[idxB] as TerminalTab
    if (tabA.type !== 'terminal' || tabB.type !== 'terminal') return null

    const children = insertBefore
      ? [{ type: 'leaf' as const, panelId: tabA.panelId }, { type: 'leaf' as const, panelId: tabB.panelId }]
      : [{ type: 'leaf' as const, panelId: tabB.panelId }, { type: 'leaf' as const, panelId: tabA.panelId }]

    const layout: PanelLayout = {
      root: {
        type: 'split',
        direction,
        sizes: [0.5, 0.5],
        children
      }
    }

    const workspaceTab: WorkspaceTab = {
      type: 'workspace',
      id: genId('ws-tab'),
      name: generateWorkspaceName(tabState.tabs),
      panelIds: [tabA.panelId, tabB.panelId],
      layout,
      activePanelId: tabB.panelId
    }

    // Remove in reverse order to preserve indices
    const removeIdxA = tabState.tabs.findIndex(t => t.id === terminalTabAId)
    const removeIdxB = tabState.tabs.findIndex(t => t.id === terminalTabBId)
    if (removeIdxA > removeIdxB) {
      tabState.tabs.splice(removeIdxA, 1)
      tabState.tabs.splice(removeIdxB, 1)
    } else {
      tabState.tabs.splice(removeIdxB, 1)
      tabState.tabs.splice(removeIdxA, 1)
    }

    // Re-associate panels with the new workspace tab
    const panelStore = usePanelStore()
    panelStore.movePanelToTab(tabA.panelId, workspaceTab.id)
    panelStore.movePanelToTab(tabB.panelId, workspaceTab.id)

    // Insert workspace tab at the position of the first removed tab
    const insertIdx = Math.min(removeIdxA, removeIdxB)
    tabState.tabs.splice(insertIdx, 0, workspaceTab)
    tabState.activeTabId = workspaceTab.id

    // The dragged tab is gone; its source element unmounts before dragend can
    // fire, so clear the drag tracking here.
    tabState.draggingTabId = null

    return workspaceTab
  }

  // ── Merge: terminal tab → existing workspace tab ──

  function addPanelToWorkspaceTab(
    terminalTabId: string,
    workspaceTabId: string,
    targetPanelId: string,
    direction: 'horizontal' | 'vertical',
    insertBefore: boolean
  ) {
    const termIdx = tabState.tabs.findIndex(t => t.id === terminalTabId)
    const wsTab = tabState.tabs.find(t => t.id === workspaceTabId)
    if (termIdx === -1 || !wsTab || wsTab.type !== 'workspace') return

    const termTab = tabState.tabs[termIdx] as TerminalTab
    if (termTab.type !== 'terminal') return

    const panelStore = usePanelStore()
    const newPanelId = termTab.panelId

    // Remove terminal tab
    tabState.tabs.splice(termIdx, 1)

    if (wsTab.panelIds.length === 0) {
      // Empty workspace shell (placeholder root): the panel takes the whole
      // layout instead of splitting against a non-existent target.
      wsTab.layout = { root: { type: 'leaf', panelId: newPanelId } }
      wsTab.panelIds = [newPanelId]
      wsTab.activePanelId = newPanelId
      if (wsTab.maximizedPanelId) wsTab.maximizedPanelId = newPanelId
      panelStore.movePanelToTab(newPanelId, workspaceTabId)
      tabState.activeTabId = workspaceTabId
      tabState.draggingTabId = null
      return
    }

    // Add panel to workspace
    wsTab.panelIds.push(newPanelId)
    wsTab.layout = {
      root: insertPanelIntoLayout(wsTab.layout.root, targetPanelId, newPanelId, direction, insertBefore)
    }
    wsTab.panelIds = collectPanelIds(wsTab.layout.root)
    wsTab.activePanelId = newPanelId
    if (wsTab.maximizedPanelId) wsTab.maximizedPanelId = newPanelId
    panelStore.movePanelToTab(newPanelId, workspaceTabId)
    tabState.activeTabId = workspaceTabId

    // The dragged tab is gone; its source element unmounts before dragend can
    // fire, so clear the drag tracking here.
    tabState.draggingTabId = null
  }

  // Add a newly-created panel directly to an existing workspace. Unlike
  // addPanelToWorkspaceTab, there is no temporary terminal tab to remove.
  // direction/insertBefore control where the panel splits in (defaults keep
  // the historical beside-active horizontal behavior).
  function addNewPanelToWorkspace(
    workspaceTabId: string,
    newPanelId: string,
    targetPanelId?: string,
    direction: 'horizontal' | 'vertical' = 'horizontal',
    insertBefore = false,
  ): boolean {
    const wsTab = tabState.tabs.find(t => t.id === workspaceTabId)
    if (!wsTab || wsTab.type !== 'workspace') return false

    const target = targetPanelId && wsTab.panelIds.includes(targetPanelId)
      ? targetPanelId
      : wsTab.activePanelId || wsTab.panelIds[wsTab.panelIds.length - 1]
    if (!target) {
      // Empty workspace (shell with the placeholder root): take the whole
      // layout instead of splitting. This is how dialog-created and restored
      // workspaces land their first member.
      if (wsTab.panelIds.length === 0) {
        wsTab.layout = { root: { type: 'leaf', panelId: newPanelId } }
        wsTab.panelIds = [newPanelId]
        wsTab.activePanelId = newPanelId
        if (wsTab.maximizedPanelId) wsTab.maximizedPanelId = newPanelId
        tabState.activeTabId = workspaceTabId
        return true
      }
      return false
    }

    wsTab.layout = {
      root: insertPanelIntoLayout(wsTab.layout.root, target, newPanelId, direction, insertBefore),
    }
    wsTab.panelIds = collectPanelIds(wsTab.layout.root)
    wsTab.activePanelId = newPanelId
    if (wsTab.maximizedPanelId) wsTab.maximizedPanelId = newPanelId
    tabState.activeTabId = workspaceTabId
    return true
  }

  // ── Detach: panel from workspace ──
  // Returns the detached panelId; caller is responsible for creating a terminal
  // tab with the correct name. Handles workspace cleanup (auto-convert to
  // terminal tab when 1 panel remains, close when empty).

  function removePanelFromWorkspaceTab(workspaceTabId: string, panelId: string): string | null {
    const wsTab = tabState.tabs.find(t => t.id === workspaceTabId)
    if (!wsTab || wsTab.type !== 'workspace') return null

    const wsIdx = tabState.tabs.findIndex(t => t.id === workspaceTabId)

    // Remove panel from workspace
    wsTab.panelIds = wsTab.panelIds.filter(id => id !== panelId)
    tabState.broadcastPanelIds.delete(panelId)
    if (wsTab.activePanelId === panelId) {
      wsTab.activePanelId = wsTab.panelIds[0] || null
    }
    if (wsTab.maximizedPanelId === panelId) {
      wsTab.maximizedPanelId = null
    }

    // Keep AI lock when panel is detached from workspace — the
    // locked session should remain locked regardless of whether
    // the panel is in a workspace or standalone tab.

    if (wsTab.panelIds.length === 1) {
      // Auto-convert remaining workspace to terminal tab
      const panelStore = usePanelStore()
      const remainingPanelId = wsTab.panelIds[0]
      const remainingPanel = panelStore.getPanel(remainingPanelId)
      const convertedTab: TerminalTab = {
        type: 'terminal',
        id: genId('term-tab'),
        panelId: remainingPanelId,
        name: remainingPanel?.title || 'Terminal'
      }
      tabState.tabs.splice(wsIdx, 1, convertedTab)
      panelStore.movePanelToTab(remainingPanelId, convertedTab.id)
      tabState.activeTabId = convertedTab.id
    } else if (wsTab.panelIds.length === 0) {
      tabState.tabs.splice(wsIdx, 1)
    } else {
      wsTab.layout = { root: removeFromLayout(wsTab.layout.root, panelId) }
    }

    return panelId
  }

  // ── Dissolve: workspace tab → individual terminal tabs ──
  // The inverse of mergeToWorkspace: every member panel returns to the top
  // tab bar as a live terminal tab (sessions stay alive), broadcast
  // participation is cleared, and the workspace tab is removed.

  function dissolveWorkspace(workspaceTabId: string): TerminalTab[] {
    const idx = tabState.tabs.findIndex(t => t.id === workspaceTabId)
    if (idx === -1) return []
    const wsTab = tabState.tabs[idx]
    if (wsTab.type !== 'workspace') return []

    const panelStore = usePanelStore()
    // Visual order: layout tree first; append any panelIds stragglers
    // defensively so membership state can never orphan a panel.
    const orderedIds = collectPanelIds(wsTab.layout.root)
    for (const id of wsTab.panelIds) {
      if (!orderedIds.includes(id)) orderedIds.push(id)
    }

    const created: TerminalTab[] = []
    let insertIdx = idx
    for (const panelId of orderedIds) {
      tabState.broadcastPanelIds.delete(panelId)
      const panel = panelStore.getPanel(panelId)
      const tab: TerminalTab = {
        type: 'terminal',
        id: genId('term-tab'),
        panelId,
        name: panel?.title || 'Terminal'
      }
      tabState.tabs.splice(insertIdx, 0, tab)
      panelStore.movePanelToTab(panelId, tab.id)
      created.push(tab)
      insertIdx++
    }

    // The workspace tab has been shifted right by the inserted tabs.
    tabState.tabs.splice(insertIdx, 1)
    if (created.length > 0) {
      tabState.activeTabId = created[0].id
    } else if (tabState.tabs.length > 0) {
      const newIdx = Math.min(idx, tabState.tabs.length - 1)
      tabState.activeTabId = tabState.tabs[newIdx].id
    } else {
      tabState.activeTabId = null
    }

    // The workspace tab element unmounts; if this ran mid-drag the dragend
    // would never fire (same rationale as mergeToWorkspace).
    tabState.draggingTabId = null
    return created
  }

  // Apply a complete layout to a workspace (restore flow). Leaves referencing
  // panels that no longer exist are pruned so skipped members never render as
  // empty panes; returns false when nothing survives (caller removes the tab).
  function applyWorkspaceLayout(workspaceTabId: string, layout: PanelLayout): boolean {
    const t = tabState.tabs.find(x => x.id === workspaceTabId)
    if (!t || t.type !== 'workspace') return false

    const panelStore = usePanelStore()
    const root = pruneDeadLeaves(layout.root, id => !!panelStore.getPanel(id))
    const ids = collectPanelIds(root)
    if (ids.length === 0) return false

    t.layout = { root }
    t.panelIds = ids
    if (!t.activePanelId || !ids.includes(t.activePanelId)) {
      t.activePanelId = ids[0]
    }
    if (t.maximizedPanelId && !ids.includes(t.maximizedPanelId)) {
      t.maximizedPanelId = null
    }
    return true
  }

  // Link/unlink a live workspace tab with its saved-workspace connection.
  function setWorkspaceSavedId(tabId: string, savedId: string | undefined) {
    const t = tabState.tabs.find(x => x.id === tabId)
    if (t && t.type === 'workspace') t.savedWorkspaceId = savedId
  }

  // ── Workspace internal: move panel to new position ──

  function movePanelInWorkspace(
    workspaceTabId: string,
    panelId: string,
    targetPanelId: string,
    direction: 'horizontal' | 'vertical',
    insertBefore: boolean
  ) {
    const wsTab = tabState.tabs.find(t => t.id === workspaceTabId)
    if (!wsTab || wsTab.type !== 'workspace' || panelId === targetPanelId) return

    // Remove panel from old position
    let tempLayout = { root: removeFromLayout(wsTab.layout.root, panelId) }
    // Insert at new position
    tempLayout = {
      root: insertPanelIntoLayout(tempLayout.root, targetPanelId, panelId, direction, insertBefore)
    }
    wsTab.layout = tempLayout
    wsTab.panelIds = collectPanelIds(tempLayout.root)
  }

  // ── Tab lock ──

  function toggleTabLock(tabId: string) {
    const t = tabState.tabs.find(x => x.id === tabId)
    if (t) t.locked = !t.locked
  }

  // ── Layout helpers ──

  function collectPanelIds(node: LayoutNode): string[] {
    if (node.type === 'leaf') return node.panelId ? [node.panelId] : []
    return node.children.flatMap(collectPanelIds)
  }

  // Drop leaves whose panels are gone (skipped restore members, closed
  // panels), collapsing emptied splits — same collapse rules as
  // removeFromLayout. Splits keep only sizes that match their remaining
  // children (re-equalized after a prune).
  function pruneDeadLeaves(node: LayoutNode, panelExists: (id: string) => boolean): LayoutNode {
    if (node.type === 'leaf') {
      return node.panelId && panelExists(node.panelId) ? node : { type: 'leaf', panelId: '' }
    }
    const children = node.children
      .map(child => pruneDeadLeaves(child, panelExists))
      .filter(child => !(child.type === 'leaf' && child.panelId === ''))
    if (children.length === 0) return { type: 'leaf', panelId: '' }
    if (children.length === 1) return children[0]
    return { ...node, children, sizes: children.map(() => 1 / children.length) }
  }

  // Balanced grid layout for a batch of panels: pairwise splits with
  // alternating direction and area-proportional sizes, so 4+ members don't
  // degenerate into a long chain of thin panes.
  function buildGridLayout(panelIds: string[]): PanelLayout {
    if (panelIds.length === 0) return { root: { type: 'leaf', panelId: '' } }
    if (panelIds.length === 1) return { root: { type: 'leaf', panelId: panelIds[0] } }
    const build = (ids: string[], depth: number): LayoutNode => {
      if (ids.length === 1) return { type: 'leaf', panelId: ids[0] }
      const mid = Math.floor(ids.length / 2)
      const direction = depth % 2 === 0 ? 'horizontal' : 'vertical'
      return {
        type: 'split',
        direction,
        sizes: [mid / ids.length, (ids.length - mid) / ids.length],
        children: [build(ids.slice(0, mid), depth + 1), build(ids.slice(mid), depth + 1)]
      }
    }
    return { root: build(panelIds, 0) }
  }

  function hasPanelInNode(node: LayoutNode, panelId: string): boolean {
    if (node.type === 'leaf') return node.panelId === panelId
    return node.children.some(child => hasPanelInNode(child, panelId))
  }

  function insertPanelIntoLayout(
    node: LayoutNode,
    targetId: string,
    newId: string,
    direction: 'horizontal' | 'vertical',
    before: boolean
  ): LayoutNode {
    if (node.type === 'leaf') {
      if (node.panelId === targetId) {
        const children = before
          ? [{ type: 'leaf' as const, panelId: newId }, node]
          : [node, { type: 'leaf' as const, panelId: newId }]
        return { type: 'split', direction, sizes: [0.5, 0.5], children }
      }
      return node
    }
    const hasTarget = node.children.some(child => hasPanelInNode(child, targetId))
    if (hasTarget) {
      return {
        ...node,
        children: node.children.map(child =>
          insertPanelIntoLayout(child, targetId, newId, direction, before)
        )
      }
    }
    return node
  }

  function removeFromLayout(node: LayoutNode, panelId: string): LayoutNode {
    if (node.type === 'leaf') {
      return node.panelId === panelId
        ? { type: 'leaf' as const, panelId: '' }
        : node
    }
    const newChildren = node.children
      .map(child => removeFromLayout(child, panelId))
      .filter(child => !(child.type === 'leaf' && child.panelId === ''))

    if (newChildren.length === 0) {
      return { type: 'leaf' as const, panelId: '' }
    }
    if (newChildren.length === 1) {
      return newChildren[0]
    }
    return { ...node, children: newChildren }
  }

  function updateNodeInTree(
    node: LayoutNode,
    oldNode: LayoutNode,
    newNode: LayoutNode
  ): LayoutNode {
    if (node === oldNode) return newNode
    if (node.type === 'leaf') return node
    return {
      ...node,
      children: node.children.map(child => updateNodeInTree(child, oldNode, newNode))
    }
  }

  return {
    tabs,
    activeTabId,
    draggingTabId,
    draggingPanelId,
    activeTab,
    createTerminalTab,
    createTerminalTabAt,
    replaceStartTab,
    createTab,
    replaceStartWithTab,
    createStartTab,
    createWorkspaceTab,
    closeTab,
    setActiveTab,
    setDraggingTabId,
    setDraggingPanelId,
    nextTab,
    prevTab,
    getActivePanelId,
    moveTab,
    renameTab,
    setActivePanel,
    toggleWorkspacePanelMaximize,
    updateWorkspaceLayout,
    mergeToWorkspace,
    addPanelToWorkspaceTab,
    addNewPanelToWorkspace,
    removePanelFromWorkspaceTab,
    dissolveWorkspace,
    applyWorkspaceLayout,
    setWorkspaceSavedId,
    buildGridLayout,
    movePanelInWorkspace,
    toggleTabLock,
    broadcastPanelIds,
    getAllBroadcastPanelIds,
    toggleBroadcast,
    toggleBroadcastPanel,
    isBroadcasting,
    isPanelBroadcasting,
    isTabBroadcastTarget,
    enableBroadcastForTab,
    disableBroadcastForTab,
    getBroadcastPanelIdsInWorkspace,
    markTabNotification,
    clearTabNotification,
    hasTabNotification,
    setTabProgress,
    getTabProgress,
    // Expose helpers for components
    generateWorkspaceName,
    collectPanelIds,
    insertPanelIntoLayout,
    removeFromLayout,
    updateNodeInTree
  }
})
