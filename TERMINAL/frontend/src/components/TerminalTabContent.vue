<template>
  <div
    class="terminal-tab-content"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <Panel
      v-if="panel"
      :key="`${tab.panelId}-${tab.id}`"
      :panel="panel"
      :show-header="false"
      :is-active="true"
      @close="handleClose"
      @toggle-ai-lock="onToggleAiLock"
    />
    <div v-else class="no-panel">Panel not found</div>

    <!-- Drop zone overlay -->
    <div v-if="dragOver" class="drop-zone-overlay">
      <div class="dz dz-left" :class="{ active: dropPos === 'left' }"></div>
      <div class="dz dz-right" :class="{ active: dropPos === 'right' }"></div>
      <div class="dz dz-top" :class="{ active: dropPos === 'top' }"></div>
      <div class="dz dz-bottom" :class="{ active: dropPos === 'bottom' }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'TerminalTabContent' })

import { computed, ref, nextTick } from 'vue'
import { usePanelStore } from '../stores/panelStore'
import { useTabStore } from '../stores/tabStore'
import type { TerminalTab } from '../types/workspace'
import Panel from './Panel.vue'

const props = defineProps<{
  tab: TerminalTab
}>()

const emit = defineEmits<{
  close: [tabId: string]
}>()

const panelStore = usePanelStore()
const tabStore = useTabStore()

const dragOver = ref(false)
const dropPos = ref<string | null>(null)

const panel = computed(() => panelStore.getPanel(props.tab.panelId))

function handleClose(_panelId: string) {
  emit('close', props.tab.id)
}

function onToggleAiLock(panelId: string) {
  if (tabStore.isPanelAILocked(panelId)) {
    tabStore.removeAILockedPanel(panelId)
  } else {
    tabStore.addAILockedPanel(panelId)
  }
}

function onDragOver(e: DragEvent) {
  const types = e.dataTransfer?.types ? Array.from(e.dataTransfer.types) : []
  const hasPanel = types.includes('application/panel-id')
  const hasTab = types.includes('application/tab-id')
  const hasTabType = types.includes('application/tab-type')
  const hasWorkspace = types.includes('application/workspace-id')
  // Allow: panel drags, terminal tab drags (has tab-id + tab-type, NOT workspace)
  const isTerminalTab = hasTab && hasTabType && !hasWorkspace
  if (!hasPanel && !isTerminalTab) return
  // The dragged tab hovering its own visible content can only be the active
  // tab. Switch to the adjacent tab so its content becomes the drop target
  // for merging into a workspace. The switch happens here — not at dragstart
  // — so plain tab-bar reorders never lose the selection; if the drag returns
  // to the tab bar, TabItem's dragend restores the original active tab.
  const draggingTabId = tabStore.draggingTabId
  if (draggingTabId && draggingTabId === props.tab.id) {
    const tabs = tabStore.tabs
    const fromIdx = tabs.findIndex(t => t.id === draggingTabId)
    const adjacentTab = tabs[fromIdx - 1] || tabs[fromIdx + 1]
    if (adjacentTab && tabStore.activeTabId !== adjacentTab.id) {
      tabStore.setActiveTab(adjacentTab.id)
    }
    return
  }

  dragOver.value = true
  e.dataTransfer!.dropEffect = 'move'

  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const xRatio = x / rect.width
  const yRatio = y / rect.height

  if (Math.abs(xRatio - 0.5) >= Math.abs(yRatio - 0.5)) {
    dropPos.value = xRatio < 0.5 ? 'left' : 'right'
  } else {
    dropPos.value = yRatio < 0.5 ? 'top' : 'bottom'
  }
}

function onDragLeave(e: DragEvent) {
  const el = e.currentTarget as HTMLElement
  const relatedTarget = e.relatedTarget as HTMLElement | null
  if (!relatedTarget || !el.contains(relatedTarget)) {
    dragOver.value = false
    dropPos.value = null
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  dropPos.value = null

  // OS file drops must keep bubbling to the document: the Wails runtime's
  // document-level drop handler resolves the real file paths and re-emits
  // them as common:WindowFilesDropped (consumed by BaseTerminal's native
  // drop binding). Only consume panel/tab drags here.
  const types = e.dataTransfer?.types ? Array.from(e.dataTransfer.types) : []
  if (types.includes('Files')) return

  e.stopPropagation()

  const draggedTabId = e.dataTransfer?.getData('application/tab-id')
  const draggedPanelId = e.dataTransfer?.getData('application/panel-id')
  const sourceTabId = e.dataTransfer?.getData('application/source-tab-id')
  const tabType = e.dataTransfer?.getData('application/tab-type')

  // Reject settings tabs and workspace tabs
  if (draggedTabId && tabType !== 'terminal') return

  // Determine drop position
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
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

  // Case 1: Terminal tab dragged onto this terminal tab → merge to workspace
  if (draggedTabId && tabType === 'terminal' && draggedTabId !== props.tab.id) {
    const fromTabId = draggedTabId
    const toTabId = props.tab.id
    // Defer to next tick so the current component's event handling completes
    // before we modify tab state (which would destroy this component).
    nextTick(() => {
      tabStore.mergeToWorkspace(fromTabId, toTabId, direction, insertBefore)
    })
    return
  }

  // Case 2: Panel from workspace dragged onto this terminal tab
  if (draggedPanelId && sourceTabId && sourceTabId !== props.tab.id) {
    const detachedPanelId = tabStore.removePanelFromWorkspaceTab(sourceTabId, draggedPanelId)
    if (!detachedPanelId) return
    const draggedPanel = panelStore.getPanel(detachedPanelId)
    if (!draggedPanel) return
    const newTerminalTab = tabStore.createTerminalTab(draggedPanel.title, detachedPanelId)
    panelStore.movePanelToTab(detachedPanelId, newTerminalTab.id)
    tabStore.mergeToWorkspace(props.tab.id, newTerminalTab.id, direction, insertBefore)
    return
  }
}
</script>

<style scoped>
.terminal-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-base);
  position: relative;
}
.no-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 0.8125rem;
}

.drop-zone-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  pointer-events: none;
}
.dz {
  position: absolute;
  background: var(--accent-subtle);
  transition: background 0.12s;
}
.dz.active {
  background: var(--accent-glow);
}
.dz-left { left: 0; top: 0; width: 50%; height: 100%; }
.dz-right { right: 0; top: 0; width: 50%; height: 100%; }
.dz-top { left: 0; top: 0; width: 100%; height: 50%; }
.dz-bottom { left: 0; bottom: 0; width: 100%; height: 50%; }
</style>
