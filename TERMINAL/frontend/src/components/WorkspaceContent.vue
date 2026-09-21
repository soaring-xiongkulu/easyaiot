<template>
  <div
    class="workspace-content"
    @dragover.prevent="onWorkspaceDragOver"
  >
    <!-- Empty workspace: drop target for sidebar connections / terminal tabs -->
    <div
      v-if="tab.panelIds.length === 0"
      class="ws-empty"
      :class="{ 'drag-over': emptyDragOver }"
      @dragover.prevent="onEmptyDragOver"
      @dragleave="onEmptyDragLeave"
      @drop="onEmptyDrop"
    >
      <LayoutDashboard class="ws-empty-icon" />
      <div class="ws-empty-text">{{ t('workspace.dropHint') }}</div>
    </div>
    <PanelGrid
      v-else
      :layout="tab.layout"
      :panel-ids="tab.panelIds"
      :active-panel-id="tab.activePanelId"
      :maximized-panel-id="tab.maximizedPanelId || null"
      :tab-id="tab.id"
      @close-panel="closePanel"
      @toggle-ai-lock="onToggleAiLock"
      @duplicate="onDuplicatePanel"
      @rename="onRenamePanel"
      @panel-drag-start="onPanelDragStart"
      @panel-drop="onPanelDrop"
      @resize="onResize"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'WorkspaceContent' })

import { ref } from 'vue'
import { LayoutDashboard } from '@lucide/vue'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { useCompanionStore } from '../stores/companionStore'
import { useConnectionStore } from '../stores/connectionStore'
import type { WorkspaceTab } from '../types/workspace'
import { useDuplicateSession } from '../composables/useDuplicateSession'
import PanelGrid from './PanelGrid.vue'
import { CloseSession } from '../../bindings/easyaiot/terminal/app'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'

const props = defineProps<{
  tab: WorkspaceTab
}>()

const tabStore = useTabStore()
const panelStore = usePanelStore()
const sessionStore = useSessionStore()
const companionStore = useCompanionStore()
const connectionStore = useConnectionStore()
const { t } = useI18n()
const { duplicateSession } = useDuplicateSession()

async function closePanel(panelId: string) {
  const panel = panelStore.getPanel(panelId)
  const connected = !!panel?.sessionId && sessionStore.getStatus(panel.sessionId) === 'connected'
  if (connected) {
    try {
      await ElMessageBox.confirm(
        t('tab.closeConnectedConfirm'),
        t('tab.closeConfirmTitle'),
        { confirmButtonText: t('tab.close'), cancelButtonText: t('conn.cancel'), type: 'warning' }
      )
    } catch {
      return
    }
  }
  if (panel?.sessionId) {
    try { await CloseSession(panel.sessionId) } catch (_) {}
  }
  companionStore.disposeForPanel(panelId).catch(() => {})
  tabStore.removePanelFromWorkspaceTab(props.tab.id, panelId)
  if (panel) {
    panelStore.removePanel(panel.id)
  }
}

function onToggleAiLock(panelId: string) {
  if (tabStore.isPanelAILocked(panelId)) {
    tabStore.removeAILockedPanel(panelId)
  } else {
    tabStore.addAILockedPanel(panelId)
  }
}

async function onDuplicatePanel(panelId: string) {
  const panel = panelStore.getPanel(panelId)
  if (!panel) return
  await duplicateSession(
    { type: 'terminal', panelId, title: panel.title },
    { workspaceId: props.tab.id, targetPanelId: panelId },
  )
}

function onRenamePanel(panelId: string, newName: string) {
  panelStore.updateTitle(panelId, newName)
  // Sync tab name for terminal tabs
  const tab = tabStore.tabs.find(t => t.type === 'terminal' && t.panelId === panelId)
  if (tab) tab.name = newName
}

function onPanelDragStart(e: DragEvent, panelId: string) {
  if (e.dataTransfer) {
    e.dataTransfer.setData('application/panel-id', panelId)
    e.dataTransfer.setData('application/source-tab-id', props.tab.id)
    e.dataTransfer.effectAllowed = 'move'
  }
}

function onPanelDrop(e: DragEvent, targetPanelId: string, targetRect?: DOMRect) {
  const draggedPanelId = e.dataTransfer?.getData('application/panel-id')
  const draggedTabId = e.dataTransfer?.getData('application/tab-id')
  const sourceTabId = e.dataTransfer?.getData('application/source-tab-id')
  const draggedConnId = e.dataTransfer?.getData('application/conn-id')

  // Case 0: Sidebar connection dragged in — connect it and split at the drop
  // position. Connecting must go through App (credentials, CreateSession, PTY
  // sizing), so hand off via the window event App listens for.
  if (draggedConnId && !draggedPanelId && !draggedTabId) {
    const conn = connectionStore.connections.find(c => c.id === draggedConnId)
    if (!conn) return

    const rect = targetRect || (e.currentTarget as HTMLElement).getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const xRatio = x / rect.width
    const yRatio = y / rect.height

    let direction: 'horizontal' | 'vertical'
    let insertBefore: boolean
    if (Math.abs(xRatio - 0.5) >= Math.abs(yRatio - 0.5)) {
      direction = 'horizontal'
      insertBefore = xRatio < 0.5
    } else {
      direction = 'vertical'
      insertBefore = yRatio < 0.5
    }

    window.dispatchEvent(new CustomEvent('app:connect-workspace-panel', {
      detail: { config: conn, workspaceTabId: props.tab.id, targetPanelId, direction, insertBefore }
    }))
    return
  }

  // Case 1: Terminal tab dragged into workspace (from TabBar)
  if (draggedTabId && !draggedPanelId) {
    const draggedTab = tabStore.tabs.find(t => t.id === draggedTabId)
    if (!draggedTab || draggedTab.type !== 'terminal') return

    // Save the tab that was active before the drop, so dropping a background
    // terminal tab into this workspace doesn't steal the user's focus
    const adjacentTabId = tabStore.activeTabId

    const rect = targetRect || (e.currentTarget as HTMLElement).getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const xRatio = x / rect.width
    const yRatio = y / rect.height

    let direction: 'horizontal' | 'vertical'
    let insertBefore: boolean

    if (Math.abs(xRatio - 0.5) >= Math.abs(yRatio - 0.5)) {
      direction = 'horizontal'
      insertBefore = xRatio < 0.5
    } else {
      direction = 'vertical'
      insertBefore = yRatio < 0.5
    }

    tabStore.addPanelToWorkspaceTab(draggedTabId, props.tab.id, targetPanelId, direction, insertBefore)
    panelStore.movePanelToTab(draggedTab.panelId, props.tab.id)

    // Restore adjacent tab activation instead of letting workspace take focus
    if (adjacentTabId && adjacentTabId !== draggedTabId) {
      tabStore.setActiveTab(adjacentTabId)
    }
    return
  }

  // Case 2: Panel reposition within same workspace or from another workspace
  if (!draggedPanelId || draggedPanelId === targetPanelId) return

  const draggedPanel = panelStore.getPanel(draggedPanelId)
  if (!draggedPanel) return

  const rect = targetRect || (e.currentTarget as HTMLElement).getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const xRatio = x / rect.width
  const yRatio = y / rect.height

  let direction: 'horizontal' | 'vertical'
  let insertBefore: boolean

  if (Math.abs(xRatio - 0.5) >= Math.abs(yRatio - 0.5)) {
    direction = 'horizontal'
    insertBefore = xRatio < 0.5
  } else {
    direction = 'vertical'
    insertBefore = yRatio < 0.5
  }

  // If dragged from a different tab (workspace or terminal tab)
  if (sourceTabId && sourceTabId !== props.tab.id) {
    const sourceTab = tabStore.tabs.find(t => t.id === sourceTabId)
    if (sourceTab?.type === 'workspace') {
      tabStore.removePanelFromWorkspaceTab(sourceTabId, draggedPanelId)
    }
    // Add to this workspace
    props.tab.panelIds.push(draggedPanelId)
    panelStore.movePanelToTab(draggedPanelId, props.tab.id)
    const newLayout = tabStore.insertPanelIntoLayout(
      props.tab.layout.root,
      targetPanelId,
      draggedPanelId,
      direction,
      insertBefore
    )
    tabStore.updateWorkspaceLayout(props.tab.id, { root: newLayout })
  } else {
    // Same workspace reposition
    tabStore.movePanelInWorkspace(props.tab.id, draggedPanelId, targetPanelId, direction, insertBefore)
  }
}

function onWorkspaceDragOver(e: DragEvent) {
  const types = e.dataTransfer?.types ? Array.from(e.dataTransfer.types) : []
  const hasPanel = types.includes('application/panel-id')
  const hasTab = types.includes('application/tab-id')
  if (hasPanel || hasTab) {
    e.dataTransfer!.dropEffect = 'move'
  }
}

// ── Empty workspace: drop connections / terminal tabs to join ──

const emptyDragOver = ref(false)

function onEmptyDragOver(e: DragEvent) {
  const types = e.dataTransfer?.types ? Array.from(e.dataTransfer.types) : []
  const accepts = types.includes('application/conn-id') || types.includes('application/tab-id')
  if (!accepts) return
  emptyDragOver.value = true
  e.dataTransfer!.dropEffect = 'move'
}

function onEmptyDragLeave(e: DragEvent) {
  const related = e.relatedTarget as HTMLElement | null
  const el = e.currentTarget as HTMLElement
  if (!related || !el.contains(related)) emptyDragOver.value = false
}

function onEmptyDrop(e: DragEvent) {
  emptyDragOver.value = false
  const connId = e.dataTransfer?.getData('application/conn-id')
  const draggedTabId = e.dataTransfer?.getData('application/tab-id')

  // Sidebar connection dropped in → connect through App (credentials,
  // CreateSession, PTY sizing) and land it via the empty-shell branch.
  if (connId) {
    const conn = connectionStore.connections.find(c => c.id === connId)
    if (conn) {
      window.dispatchEvent(new CustomEvent('app:connect-workspace-panel', {
        detail: { config: conn, workspaceTabId: props.tab.id }
      }))
    }
    return
  }

  // Terminal tab dropped in → fold the tab into this workspace.
  if (draggedTabId) {
    const draggedTab = tabStore.tabs.find(t => t.id === draggedTabId)
    if (draggedTab?.type !== 'terminal') return
    tabStore.addPanelToWorkspaceTab(draggedTabId, props.tab.id, '', 'horizontal', false)
    tabStore.setActiveTab(props.tab.id)
  }
}

function onResize(payload: { node: any, index: number, delta: number }) {
  const { node, index, delta } = payload
  if (node.type !== 'split') return

  const newSizes = [...node.sizes]
  newSizes[index] = Math.max(0.1, Math.min(0.9, newSizes[index] + delta))
  newSizes[index + 1] = Math.max(0.1, Math.min(0.9, newSizes[index + 1] - delta))

  const total = newSizes.reduce((a, b) => a + b, 0)
  const normalized = newSizes.map(s => s / total)

  const newNode = { ...node, sizes: normalized }
  const newRoot = tabStore.updateNodeInTree(props.tab.layout.root, node, newNode)
  tabStore.updateWorkspaceLayout(props.tab.id, { root: newRoot })
}
</script>

<style scoped>
.workspace-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-base);
  position: relative;
}

.ws-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-secondary);
  user-select: none;
  outline: 2px dashed transparent;
  outline-offset: -0.75rem;
  transition: outline-color 0.12s, background 0.12s;
}
.ws-empty.drag-over {
  outline-color: var(--accent);
  background: var(--accent-subtle);
}
.ws-empty-icon {
  width: 2rem;
  height: 2rem;
  opacity: 0.5;
}
.ws-empty-text {
  font-size: 0.875rem;
}
</style>
