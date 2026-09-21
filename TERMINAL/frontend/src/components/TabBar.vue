<template>
  <div
    class="tab-bar"
    :class="{ 'drag-over': dragOverTabs }"
    @dragover.prevent="onTabsDragOver"
    @dragleave="onTabsDragLeave"
    @drop="onTabsDrop"
  >
    <div class="tabs-list" ref="tabsListRef" @wheel="onWheel">
      <template v-for="(tab, index) in tabs" :key="tab.id">
        <!-- Drop indicator before this tab: insert-before this tab, or insert-after previous tab -->
        <div
          v-if="(dragOverTabIndex === index && !dragOverInsertAfter) || (dragOverTabIndex === index - 1 && dragOverInsertAfter)"
          class="tab-drop-indicator"
        ></div>

        <TabItem
          :tab="tab"
          :shortcut-index="index + 1"
          :is-active="tab.id === activeTabId"
          :progress="tabStore.getTabProgress(tab.id)"
          @activate="setActiveTab"
          @close="closeTab"
          @toggle-ai-lock="onToggleAiLock"
          @dragstart="onTabDragStart($event, tab.id)"
          @dragover.prevent="onTabDragOver($event, index)"
          @dragleave="onTabDragLeave"
          @drop="onTabDrop($event, tab.id, index)"
        />
      </template>
      <!-- Drop indicator after last tab -->
      <div
        v-if="dragOverTabIndex === tabs.length - 1 && dragOverInsertAfter"
        class="tab-drop-indicator"
      ></div>
      <!-- Drop indicator at end when dragging over empty tab bar area -->
      <div
        v-if="dragOverTabIndex === null && (dragOverPanel || dragOverTab)"
        class="tab-drop-indicator tab-drop-indicator-end"
      ></div>
    </div>
    <div class="tab-more" v-if="tabs.length > 0">
      <span class="tab-more-btn" :title="t('tab.more')" @click.stop="tabMoreRef?.toggle($event.currentTarget)">
        <el-icon class="tab-more-icon"><MoreHorizontal /></el-icon>
      </span>
      <Menu ref="tabMoreRef" v-model:visible="tabMoreVisible" align="end">
        <MenuItem
          v-for="tab in tabs"
          :key="tab.id"
          :class="{ active: tab.id === activeTabId }"
          @click="onTabMoreSelect(tab.id)"
        >
          {{ tab.name }}
        </MenuItem>
      </Menu>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { MoreHorizontal } from '@lucide/vue'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useI18n } from '../i18n'
import { SftpCancelTransfer, CloseSession, RDPHide } from '../../bindings/easyaiot/terminal/app'
import TabItem from './TabItem.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'

const tabStore = useTabStore()
const panelStore = usePanelStore()
const { t } = useI18n()
const tabs = computed(() => tabStore.tabs)
const activeTabId = computed(() => tabStore.activeTabId)

const dragOverTabs = ref(false)
const dragOverTabIndex = ref<number | null>(null)
const dragOverInsertAfter = ref(false)
const dragOverPanel = ref(false)
const dragOverTab = ref(false)

const tabsListRef = ref<HTMLElement | null>(null)

function onWheel(e: WheelEvent) {
  if (!tabsListRef.value) return
  tabsListRef.value.scrollLeft += e.deltaY
}

const tabMoreRef = ref<InstanceType<typeof Menu> | null>(null)
const tabMoreVisible = ref(false)
watch(tabMoreVisible, (v) => {
  if (v) window.dispatchEvent(new CustomEvent('rdp:overlay-push'))
  else window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
})

function onTabMoreSelect(id: string) {
  tabMoreVisible.value = false
  tabStore.setActiveTab(id)
  scrollToTab(id)
}

function setActiveTab(id: string) {
  tabStore.setActiveTab(id)
  scrollToTab(id)
}

function scrollToTab(tabId: string) {
  if (!tabsListRef.value) return
  const el = tabsListRef.value.querySelector(`[data-tab-id="${tabId}"]`) as HTMLElement | null
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
  }
}

async function closeTab(id: string) {
  const tab = tabs.value.find(t => t.id === id)
  if (tab) {
    const panelIds = tab.type === 'workspace' ? tab.panelIds : 'panelId' in tab ? [tab.panelId] : []

    // Check for active transfers
    let activeCount = 0
    for (const pid of panelIds) {
      const tasks = panelStore.getTransferTasks(pid)
      activeCount += tasks.filter(t => t.status === 'running' || t.status === 'paused').length
    }

    if (activeCount > 0) {
      try {
        await ElMessageBox.confirm(
          t('sftp.closeConfirmTransfer', { count: activeCount }),
          t('sftp.closeConfirmTitle'),
          { confirmButtonText: t('sftp.dialog.confirm'), cancelButtonText: t('sftp.dialog.cancel'), type: 'warning' }
        )
      } catch {
        return
      }

      // Cancel all active transfers
      for (const pid of panelIds) {
        const panel = panelStore.getPanel(pid)
        if (!panel?.sessionId) continue
        const tasks = panelStore.getTransferTasks(pid)
        for (const task of tasks) {
          if (task.status === 'running' || task.status === 'paused') {
            try { await SftpCancelTransfer(panel.sessionId, task.id) } catch {}
          }
        }
      }
    }
  }

  // Clean up RDP session: hide window first, then close Go-side resources
  if (tab && tab.type === 'rdp') {
    const rdpPanel = panelStore.getPanel(tab.panelId)
    if (rdpPanel?.sessionId) {
      await RDPHide(rdpPanel.sessionId)
      try { await CloseSession(rdpPanel.sessionId) } catch (_) {}
    }
  }

  // Clean up VNC session
  if (tab && tab.type === 'vnc') {
    const vncPanel = panelStore.getPanel(tab.panelId)
    if (vncPanel?.sessionId) {
      try { await CloseSession(vncPanel.sessionId) } catch (_) {}
    }
  }

  const panelIds = tabStore.closeTab(id)
  panelIds.forEach(pid => panelStore.removePanel(pid))
}

function onToggleAiLock(panelId: string) {
  if (tabStore.isPanelAILocked(panelId)) {
    tabStore.removeAILockedPanel(panelId)
  } else {
    tabStore.addAILockedPanel(panelId)
  }
}

function onTabDragStart(_e: DragEvent, _tabId: string) {
  // Data is set in TabItem
}

function onTabDragOver(e: DragEvent, index: number) {
  const hasPanel = e.dataTransfer?.types.includes('application/panel-id')
  const hasTab = e.dataTransfer?.types.includes('application/tab-id')
  if (!hasPanel && !hasTab) return

  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  dragOverTabIndex.value = index
  dragOverInsertAfter.value = e.clientX >= rect.left + rect.width / 2
  e.dataTransfer!.dropEffect = 'move'
}

function onTabDragLeave(_e: DragEvent) {
  // Reset handled by onTabDragOver of next tab, or onTabsDragLeave for exit
}

function onTabDrop(e: DragEvent, targetTabId: string, index: number) {
  e.stopPropagation()

  const insertAfter = dragOverInsertAfter.value
  clearDragState()

  const draggedTabId = e.dataTransfer?.getData('application/tab-id')
  const draggedPanelId = e.dataTransfer?.getData('application/panel-id')
  const sourceTabId = e.dataTransfer?.getData('application/source-tab-id')

  // Case 1: Tab reorder
  if (draggedTabId && !draggedPanelId) {
    if (draggedTabId === targetTabId) return
    const fromIdx = tabs.value.findIndex(t => t.id === draggedTabId)
    if (fromIdx === -1) return
    let toIdx = index + (insertAfter ? 1 : 0)
    if (toIdx > fromIdx) toIdx--
    if (fromIdx !== toIdx) {
      tabStore.moveTab(fromIdx, toIdx)
    }
    return
  }

  // Case 2: Panel dropped on existing tab → create terminal tab at position
  if (draggedPanelId) {
    const panel = panelStore.getPanel(draggedPanelId)
    if (!panel) return

    if (sourceTabId) {
      tabStore.removePanelFromWorkspaceTab(sourceTabId, draggedPanelId)
    }

    const tab = tabStore.createTerminalTab(panel.title, draggedPanelId)
    panelStore.movePanelToTab(draggedPanelId, tab.id)

    // Move to the drop position
    const targetIdx = index + (insertAfter ? 1 : 0)
    const currentIdx = tabs.value.findIndex(t => t.id === tab.id)
    if (currentIdx !== targetIdx) {
      tabStore.moveTab(currentIdx, targetIdx)
    }
  }
}

function onTabsDragOver(e: DragEvent) {
  const hasPanel = e.dataTransfer?.types.includes('application/panel-id')
  const hasTab = e.dataTransfer?.types.includes('application/tab-id')
  if (hasPanel || hasTab) {
    dragOverTabs.value = true
    dragOverPanel.value = !!hasPanel
    dragOverTab.value = !!hasTab
    e.dataTransfer!.dropEffect = 'move'
  }
}

function onTabsDragLeave(e: DragEvent) {
  const el = e.currentTarget as HTMLElement
  const relatedTarget = e.relatedTarget as HTMLElement | null
  if (!relatedTarget || !el.contains(relatedTarget)) {
    clearDragState()
  }
}

function onTabsDrop(e: DragEvent) {
  // Handles drops on empty tab bar area only (tab drops handled by onTabDrop)
  const panelId = e.dataTransfer?.getData('application/panel-id')
  const sourceTabId = e.dataTransfer?.getData('application/source-tab-id')

  if (!panelId) {
    clearDragState()
    return
  }

  // Skip if drop landed on a tab item (already handled by onTabDrop)
  const target = e.target as HTMLElement
  if (target.closest('.tab-item') || target.closest('.workspace-tab-item')) {
    clearDragState()
    return
  }

  clearDragState()

  const panel = panelStore.getPanel(panelId)
  if (!panel) return

  if (sourceTabId) {
    tabStore.removePanelFromWorkspaceTab(sourceTabId, panelId)
  }

  const tab = tabStore.createTerminalTab(panel.title, panelId)
  panelStore.movePanelToTab(panelId, tab.id)
}

function clearDragState() {
  dragOverTabs.value = false
  dragOverTabIndex.value = null
  dragOverInsertAfter.value = false
  dragOverPanel.value = false
  dragOverTab.value = false
}
</script>

<style scoped>
.tab-bar {
  display: flex;
  align-items: center;
  height: 2.5rem;
  background: var(--bg-base);
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
  transition: background 0.15s, border-color 0.15s;
}
.tab-bar.drag-over {
  background: var(--accent-subtle);
  border-bottom-color: var(--accent);
}
.tabs-list {
  display: flex;
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  align-items: stretch;
  scrollbar-width: none;
}
.tabs-list::-webkit-scrollbar {
  display: none;
}

.tab-more {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: 0 0.25rem;
}
.tab-more-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 1px;
  user-select: none;
  transition: all 0.15s;
}
.tab-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab-drop-indicator {
  width: 0.125rem;
  min-width: 0.125rem;
  align-self: stretch;
  background: var(--accent);
  opacity: 0.8;
  margin: 0.25rem 0;
  border-radius: 1px;
  flex-shrink: 0;
}
.tab-drop-indicator-end {
  margin-left: auto;
}
</style>
