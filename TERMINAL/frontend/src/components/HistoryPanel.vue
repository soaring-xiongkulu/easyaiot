<template>
  <div class="history-panel">
    <div class="qc-toolbar">
      <el-input
        v-model="searchQuery"
        :placeholder="t('settings.historySearchPlaceholder')"
        clearable
       
        class="qc-search-input"
        @keydown="onListKeydown"
      />
    </div>

    <div class="qc-list" ref="listRef" tabindex="0" @keydown="onListKeydown">
      <div
        v-for="entry in filteredEntries"
        :key="entry.id"
        class="qc-item"
        :class="{ active: selectedIds.has(entry.id) }"
        @click="onItemClick($event, entry)"
        @dblclick="runCommand(entry)"
        @contextmenu.prevent="onContextMenu($event, entry)"
        @mouseenter="hoveredId = entry.id; showTooltip($event, entry.command)"
        @mouseleave="hoveredId = null; hideTooltip()"
      >
        <span class="history-command">{{ entry.command }}</span>
        <div v-if="selectedIds.size <= 1 && (selectedIds.has(entry.id) || hoveredId === entry.id)" class="qc-item-actions">
          <button class="btn btn-ghost btn-icon btn-sm run" @click.stop="runCommand(entry)" :title="t('quickCommands.run')">
            <Play :size="'0.875rem'" />
          </button>
          <button class="btn btn-ghost btn-icon btn-sm paste" @click.stop="pasteCommand(entry)" :title="t('quickCommands.paste')">
            <Clipboard :size="'0.875rem'" />
          </button>
          <button class="btn btn-ghost btn-icon btn-sm" @click.stop="copyCommand(entry)" :title="t('quickCommands.copy')">
            <Copy :size="'0.875rem'" />
          </button>
        </div>
      </div>

      <div v-if="filteredEntries.length === 0" class="qc-empty">
        {{ searchQuery ? t('sidebar.noSearchResults') : t('settings.historyEmpty') }}
      </div>
    </div>

    <!-- Context menu -->
    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
      <MenuItem :class="{ disabled: selectedIds.size > 1 }" @click="selectedIds.size <= 1 && runCommand(current)">{{ t('quickCommands.run') }}</MenuItem>
      <MenuItem :class="{ disabled: selectedIds.size > 1 }" @click="selectedIds.size <= 1 && pasteCommand(current)">{{ t('quickCommands.paste') }}</MenuItem>
      <MenuItem :class="{ disabled: selectedIds.size > 1 }" @click="selectedIds.size <= 1 && copyCommand(current); ctxMenuVisible = false">{{ t('quickCommands.copy') }}</MenuItem>
      <MenuItem :class="{ disabled: selectedIds.size > 1 }" @click="selectedIds.size <= 1 && saveAsQuickCommand(current)">{{ t('quickCommands.saveAs') }}</MenuItem>
      <MenuDivider />
      <MenuItem class="danger" @click="deleteSelected(); ctxMenuVisible = false">{{ t('sidebar.delete') }}</MenuItem>
    </Menu>

    <!-- Custom tooltip -->
    <div v-show="tooltipVisible" class="qc-tooltip" :style="tooltipStyle">{{ tooltipText }}</div>

    <!-- Quick command edit dialog -->
    <QuickCommandEditDialog
      v-model="editDialogVisible"
      :initial-command="editingCmdCommand"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Play, Clipboard, Copy } from '@lucide/vue'
import { useSuggestions, type HistoryEntry } from '../composables/useSuggestions'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { queuedSessionWrite } from '../services/sessionWriter'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { focusActivePanelTerminal } from '../composables/useFocusTerminal'
import QuickCommandEditDialog from './QuickCommandEditDialog.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'

const { t } = useI18n()
const suggestions = useSuggestions()
const tabStore = useTabStore()
const panelStore = usePanelStore()

const searchQuery = ref('')
const selectedIds = ref<Set<string>>(new Set())
const focusedId = ref<string | null>(null)
const hoveredId = ref<string | null>(null)
const listRef = ref<HTMLDivElement | null>(null)
const lastClickId = ref<string | null>(null)

const ctxMenuVisible = ref(false)
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)

const editDialogVisible = ref(false)
const editingCmdCommand = ref('')

const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipStyle = ref({ left: '0px', top: '0px' })

function showTooltip(e: MouseEvent, text: string) {
  tooltipText.value = text
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  tooltipStyle.value = { left: rect.left + 'px', top: (rect.top - 8) + 'px' }
  tooltipVisible.value = true
}

function hideTooltip() {
  tooltipVisible.value = false
}
const entries = suggestions.historyEntries

onMounted(async () => {
  await suggestions.loadHistory()
})

const filteredEntries = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return entries.value
  return entries.value.filter(e => e.command.toLowerCase().includes(q))
})

function getAllVisibleIds(): string[] {
  return filteredEntries.value.map(e => e.id)
}

function onListKeydown(e: KeyboardEvent) {
  const ids = getAllVisibleIds()
  if (ids.length === 0) return
  const idx = ids.indexOf(focusedId.value || '')

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const nextIdx = idx >= 0 && idx < ids.length - 1 ? idx + 1 : 0
    focusedId.value = ids[nextIdx]
    selectedIds.value = new Set([ids[nextIdx]])
    lastClickId.value = ids[nextIdx]
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const prevIdx = idx > 0 ? idx - 1 : ids.length - 1
    focusedId.value = ids[prevIdx]
    selectedIds.value = new Set([ids[prevIdx]])
    lastClickId.value = ids[prevIdx]
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (selectedIds.value.size === 1 && focusedId.value) {
      const entry = entries.value.find(e => e.id === focusedId.value)
      if (entry) runCommand(entry)
    }
  } else if (e.key === 'Delete') {
    e.preventDefault()
    deleteSelected()
  }
}

function onItemClick(e: MouseEvent, entry: HistoryEntry) {
  if (e.shiftKey && lastClickId.value) {
    const ids = getAllVisibleIds()
    const anchorIdx = ids.indexOf(lastClickId.value)
    const currentIdx = ids.indexOf(entry.id)
    if (anchorIdx >= 0 && currentIdx >= 0) {
      const [start, end] = anchorIdx < currentIdx ? [anchorIdx, currentIdx] : [currentIdx, anchorIdx]
      selectedIds.value = new Set(ids.slice(start, end + 1))
    }
  } else if (e.ctrlKey || e.metaKey) {
    const next = new Set(selectedIds.value)
    if (next.has(entry.id)) next.delete(entry.id)
    else next.add(entry.id)
    selectedIds.value = next
    lastClickId.value = entry.id
    focusedId.value = entry.id
  } else {
    selectedIds.value = new Set([entry.id])
    lastClickId.value = entry.id
    focusedId.value = entry.id
  }
}

function getTargetSessionIds(): string[] {
  const activeTabId = tabStore.activeTabId
  if (!activeTabId) return []
  const tab = tabStore.tabs.find(t => t.id === activeTabId)
  if (!tab) return []
  if (tab.type === 'workspace' && tabStore.isBroadcasting(tab.id)) {
    const ids: string[] = []
    for (const pid of tabStore.getBroadcastPanelIdsInWorkspace(tab.id)) {
      const p = panelStore.getPanel(pid)
      if (p?.sessionId && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')) {
        ids.push(p.sessionId)
      }
    }
    return ids
  }
  const activePanelId = tab.type === 'workspace' ? tab.activePanelId : (tab.type === 'terminal' ? tab.panelId : null)
  if (!activePanelId) return []
  const panel = panelStore.getPanel(activePanelId)
  if (!panel?.sessionId) return []
  return [panel.sessionId]
}

function runCommand(entry: HistoryEntry) {
  const sids = getTargetSessionIds()
  if (sids.length === 0) return
  const text = entry.command.endsWith('\n') ? entry.command : entry.command + '\n'
  for (const sid of sids) {
    queuedSessionWrite(sid, text)
  }
  // Return focus to the terminal (issue #285).
  focusActivePanelTerminal()
}

function pasteCommand(entry: HistoryEntry) {
  const sids = getTargetSessionIds()
  if (sids.length === 0) return
  for (const sid of sids) {
    queuedSessionWrite(sid, entry.command)
  }
  // Return focus to the terminal (issue #285).
  focusActivePanelTerminal()
}

async function copyCommand(entry: HistoryEntry) {
  try {
    await navigator.clipboard.writeText(entry.command)
    msg.success(t('quickCommands.copied'))
  } catch {
    msg.error(t('quickCommands.copyFailed'))
  }
}

function saveAsQuickCommand(entry: HistoryEntry) {
  editingCmdCommand.value = entry.command
  editDialogVisible.value = true
  ctxMenuVisible.value = false
}

function deleteEntries(ids: string[]) {
  suggestions.removeHistoryCommandsById(ids)
  selectedIds.value = new Set()
}

function deleteSelected() {
  const ids = [...selectedIds.value]
  if (ids.length === 0) return
  deleteEntries(ids)
}

function onContextMenu(e: MouseEvent, entry: HistoryEntry) {
  e.stopPropagation()
  if (!selectedIds.value.has(entry.id)) {
    selectedIds.value = new Set([entry.id])
    focusedId.value = entry.id
  }
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, entry)
}

watch(searchQuery, () => {
  const ids = getAllVisibleIds()
  if (ids.length > 0) {
    focusedId.value = ids[0]
    selectedIds.value = new Set([ids[0]])
    lastClickId.value = ids[0]
  } else {
    focusedId.value = null
    selectedIds.value = new Set()
  }
})
</script>

<style scoped>
.history-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.qc-tooltip {
  position: fixed;
  z-index: 10000;
  max-width: 30rem;
  padding: 0.375rem 0.625rem;
  font-family: var(--font-mono, 'Consolas', 'Courier New', monospace);
  font-size: 0.75rem;
  color: var(--text-primary);
  background: var(--bg-overlay);
  border: 1px solid var(--border-subtle);
  border-radius: 0.25rem;
  box-shadow: var(--shadow-md);
  pointer-events: none;
  white-space: pre-wrap;
  word-break: break-all;
  transform: translateY(-100%);
}

.history-command {
  flex: 1;
  font-family: var(--font-mono, 'Consolas', 'Courier New', monospace);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qc-toolbar {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0 0.625rem 0.375rem;
  flex-shrink: 0;
}

.qc-search-input { flex: 1; min-width: 0; }

.qc-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem 0.5rem;
}

.qc-item {
  display: flex;
  align-items: center;
  padding: 0.375rem 0.625rem;
  gap: 0.625rem;
  min-height: 2.25rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.12s ease;
  margin-bottom: 0.125rem;
  user-select: none;
}

.qc-item:hover { background: var(--bg-hover); }

.qc-item.active {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.qc-item.active .history-command { color: var(--accent); }

.qc-item-actions {
  display: flex;
  gap: 0.125rem;
  flex-shrink: 0;
}

.qc-empty {
  padding: 1.5rem 0.75rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
}

</style>
