<template>
  <div class="quick-commands-panel">
    <!-- Toolbar: search + actions -->
    <div class="qc-toolbar">
      <el-input
        ref="searchInputRef"
        v-model="searchQuery"
        :placeholder="t('quickCommands.searchPlaceholder')"
        clearable
       
        class="qc-search-input"
        @keydown="onListKeydown"
      />
      <button class="qc-icon-btn" :title="t('quickCommands.addCommand')" @click.stop="addMenuRef?.toggle($event.currentTarget)">
        <Plus :size="'0.9375rem'" />
      </button>
      <Menu ref="addMenuRef" v-model:visible="addMenuVisible" align="end">
        <MenuItem @click="onAddCommand()">{{ t('quickCommands.addCommand') }}</MenuItem>
        <MenuItem @click="onAddGroup">{{ t('quickCommands.addGroup') }}</MenuItem>
      </Menu>
    </div>

    <!-- Command list -->
    <div class="qc-list" ref="listRef" tabindex="0" @keydown="onListKeydown">
      <template v-for="group in store.groups" :key="group.id">
        <div
          class="qc-group-header"
          :class="{ 'drag-over': dragOverGroupId === group.id }"
          @click="toggleGroup(group.id)"
          @contextmenu.prevent="onGroupContextMenu($event, group)"
          @dragover.prevent="onGroupDragOver($event, group.id)"
          @dragleave="onGroupDragLeave(group.id)"
          @drop.prevent="onGroupDrop(group.id, $event)"
        >
          <span class="qc-group-arrow">
            <el-icon v-if="expandedGroups.has(group.id)"><ChevronDown :size="'0.875rem'" /></el-icon>
            <el-icon v-else><ChevronRight :size="'0.875rem'" /></el-icon>
          </span>
          <span class="qc-group-name">{{ group.name }}</span>

        </div>

        <template v-if="expandedGroups.has(group.id)">
          <div
            v-for="cmd in store.getCommandsByGroup(group.id).filter(matchesSearch)"
            :key="cmd.id"
            class="qc-item indented"
            :class="{ active: selectedId === cmd.id }"
            draggable="true"
            @dragstart="onCommandDragStart($event, cmd)"
            @click="selectCommand(cmd.id)"
            @dblclick="runCommand(cmd)"
            @contextmenu.prevent="onCommandContextMenu($event, cmd)"
            @mouseenter="hoveredId = cmd.id"
            @mouseleave="hoveredId = null"
          >
            <div class="qc-item-content">
              <div v-if="cmd.name" class="qc-item-name">{{ cmd.name }}</div>
              <div class="qc-item-cmd" :class="{ 'qc-item-cmd-only': !cmd.name }">{{ cmd.command }}</div>
            </div>
            <div v-if="selectedId === cmd.id || hoveredId === cmd.id" class="qc-item-actions">
              <button class="btn btn-ghost btn-icon qc-action-btn run" @click.stop="runCommand(cmd)" :title="t('quickCommands.run')">
                <Play :size="'1rem'" />
              </button>
              <button class="btn btn-ghost btn-icon qc-action-btn paste" @click.stop="pasteCommand(cmd)" :title="t('quickCommands.paste')">
                <Clipboard :size="'1rem'" />
              </button>
              <button class="btn btn-ghost btn-icon qc-action-btn" @click.stop="copyCommand(cmd)" :title="t('quickCommands.copy')">
                <Copy :size="'1rem'" />
              </button>
            </div>
          </div>
        </template>
      </template>

      <!-- Flat ungrouped commands (only when no real groups exist) -->
      <template v-if="store.groups.length === 0">
        <div
          v-for="cmd in store.getCommandsByGroup(undefined).filter(matchesSearch)"
          :key="cmd.id"
          class="qc-item"
          :class="{ active: selectedId === cmd.id }"
          draggable="true"
          @dragstart="onCommandDragStart($event, cmd)"
          @click="selectCommand(cmd.id)"
          @dblclick="runCommand(cmd)"
          @contextmenu.prevent="onCommandContextMenu($event, cmd)"
          @mouseenter="hoveredId = cmd.id"
          @mouseleave="hoveredId = null"
        >
          <div class="qc-item-content">
            <div v-if="cmd.name" class="qc-item-name">{{ cmd.name }}</div>
            <div class="qc-item-cmd" :class="{ 'qc-item-cmd-only': !cmd.name }">{{ cmd.command }}</div>
          </div>
          <div v-if="selectedId === cmd.id || hoveredId === cmd.id" class="qc-item-actions">
            <button class="btn btn-ghost btn-icon qc-action-btn run" @click.stop="runCommand(cmd)" :title="t('quickCommands.run')">
              <Play :size="'1rem'" />
            </button>
            <button class="btn btn-ghost btn-icon qc-action-btn paste" @click.stop="pasteCommand(cmd)" :title="t('quickCommands.paste')">
              <Clipboard :size="'1rem'" />
            </button>
            <button class="btn btn-ghost btn-icon qc-action-btn" @click.stop="copyCommand(cmd)" :title="t('quickCommands.copy')">
              <Copy :size="'1rem'" />
            </button>
          </div>
        </div>
      </template>

      <!-- Virtual (No Group) group - only when real groups exist -->
      <template v-if="store.groups.length > 0 && store.getCommandsByGroup(undefined).filter(matchesSearch).length > 0">
        <div
          class="qc-group-header"
          :class="{ 'drag-over': dragOverGroupId === '__ungrouped__' }"
          @click="toggleGroup('__ungrouped__')"
          @dragover.prevent="onGroupDragOver($event, '__ungrouped__')"
          @dragleave="onGroupDragLeave('__ungrouped__')"
          @drop.prevent="onGroupDrop('__ungrouped__', $event)"
        >
          <span class="qc-group-arrow">
            <el-icon v-if="expandedGroups.has('__ungrouped__')"><ChevronDown :size="'0.875rem'" /></el-icon>
            <el-icon v-else><ChevronRight :size="'0.875rem'" /></el-icon>
          </span>
          <span class="qc-group-name">{{ t('quickCommands.noGroup') }}</span>
        </div>
        <template v-if="expandedGroups.has('__ungrouped__')">
          <div
            v-for="cmd in store.getCommandsByGroup(undefined).filter(matchesSearch)"
            :key="cmd.id"
            class="qc-item indented"
            :class="{ active: selectedId === cmd.id }"
            draggable="true"
            @dragstart="onCommandDragStart($event, cmd)"
            @click="selectCommand(cmd.id)"
            @dblclick="runCommand(cmd)"
            @contextmenu.prevent="onCommandContextMenu($event, cmd)"
            @mouseenter="hoveredId = cmd.id"
            @mouseleave="hoveredId = null"
          >
            <div class="qc-item-content">
              <div v-if="cmd.name" class="qc-item-name">{{ cmd.name }}</div>
              <div class="qc-item-cmd" :class="{ 'qc-item-cmd-only': !cmd.name }">{{ cmd.command }}</div>
            </div>
            <div v-if="selectedId === cmd.id || hoveredId === cmd.id" class="qc-item-actions">
              <button class="btn btn-ghost btn-icon qc-action-btn run" @click.stop="runCommand(cmd)" :title="t('quickCommands.run')">
                <Play :size="'1rem'" />
              </button>
              <button class="btn btn-ghost btn-icon qc-action-btn paste" @click.stop="pasteCommand(cmd)" :title="t('quickCommands.paste')">
                <Clipboard :size="'1rem'" />
              </button>
              <button class="btn btn-ghost btn-icon qc-action-btn" @click.stop="copyCommand(cmd)" :title="t('quickCommands.copy')">
                <Copy :size="'1rem'" />
              </button>
            </div>
          </div>
        </template>
      </template>

      <!-- Empty state -->
      <div v-if="store.commands.length === 0" class="qc-empty">
        {{ t('quickCommands.empty') }}
      </div>
    </div>

    <!-- Context menu (right-click on commands / groups) -->
    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
      <template v-if="current && (current as CtxPayload).kind === 'command'">
        <MenuItem @click="runCommand((current as CtxPayload).cmd); ctxMenuVisible = false">{{ t('quickCommands.run') }}</MenuItem>
        <MenuItem @click="pasteCommand((current as CtxPayload).cmd); ctxMenuVisible = false">{{ t('quickCommands.paste') }}</MenuItem>
        <MenuItem @click="copyCommand((current as CtxPayload).cmd); ctxMenuVisible = false">{{ t('quickCommands.copy') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="editCommand((current as CtxPayload).cmd)">{{ t('quickCommands.editCommand') }}</MenuItem>
        <MenuItem class="danger" @click="deleteCommand((current as CtxPayload).cmd)">{{ t('quickCommands.deleteCommand') }}</MenuItem>
      </template>

      <template v-else-if="current && (current as CtxPayload).kind === 'group'">
        <MenuItem @click="addCommand((current as CtxPayload).group.id)">{{ t('quickCommands.addCommand') }}</MenuItem>
        <MenuItem @click="renameGroup((current as CtxPayload).group)">{{ t('quickCommands.renameGroup') }}</MenuItem>
        <MenuItem class="danger" @click="deleteGroupDialog((current as CtxPayload).group)">{{ t('quickCommands.deleteGroup') }}</MenuItem>
      </template>
    </Menu>

    <!-- Delete group dialog -->
    <el-dialog append-to-body
      v-model="deleteGroupDialogVisible"
      :title="t('quickCommands.deleteGroupTitle')"
      width="25rem"
      :close-on-click-modal="false"
    >
      <p>{{ t('quickCommands.deleteGroupDesc') }}</p>
      <div class="delete-group-actions">
        <el-button @click="doDeleteGroup(false)">{{ t('quickCommands.moveToUngrouped') }}</el-button>
        <el-button type="danger" @click="doDeleteGroup(true)">{{ t('quickCommands.deleteCommands') }}</el-button>
      </div>
    </el-dialog>

    <!-- Group name dialog (add + rename) -->
    <el-dialog append-to-body
      v-model="groupNameDialogVisible"
      :title="renamingGroup ? t('quickCommands.renameGroup') : t('quickCommands.addGroup')"
      width="22.5rem"
      :close-on-click-modal="false"
    >
      <el-input v-model="groupNameInput" :placeholder="t('quickCommands.groupName')" maxlength="30" @keyup.enter="doSaveGroupName" />
      <template #footer>
        <el-button @click="groupNameDialogVisible = false">{{ t('quickCommands.cancel') }}</el-button>
        <el-button type="primary" :disabled="!groupNameInput.trim()" @click="doSaveGroupName">
          {{ t('quickCommands.save') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Command edit dialog -->
    <QuickCommandEditDialog
      v-model="editDialogVisible"
      :editing-id="editingCmdId"
      :initial-name="editingCmdName"
      :initial-command="editingCmdCommand"
      :initial-group-id="editingCmdGroupId"
      :initial-remark="editingCmdRemark"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import {
  Plus, Play, Clipboard, Copy,
  ChevronDown, ChevronRight
} from '@lucide/vue'
import {
  useQuickCommandStore, type QuickCommand, type QuickCommandGroup,
  expandedFromCollapsed, collapsedFromExpanded
} from '../stores/quickCommandStore'
import { useLocalStateStore } from '../stores/localStateStore'
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
const store = useQuickCommandStore()
const localState = useLocalStateStore()
const tabStore = useTabStore()
const panelStore = usePanelStore()

const selectedId = ref<string | null>(null)
const focusedId = ref<string | null>(null)
const listRef = ref<HTMLDivElement | null>(null)
const hoveredId = ref<string | null>(null)
const searchQuery = ref('')
const searchInputRef = ref<any>(null)
const expandedGroups = ref<Set<string>>(new Set())

function focusSearch() {
  const input = searchInputRef.value?.$el?.querySelector('input')
  if (input instanceof HTMLInputElement) {
    input.focus()
    input.select()
  }
}

defineExpose({ focusSearch })

const dragOverGroupId = ref<string | null>(null)

// All expandable ids: group ids plus the "__ungrouped__" sentinel.
function allExpandableIds(): string[] {
  return [...store.groups.map(g => g.id), '__ungrouped__']
}

// Persist only collapsed ids (like the connections sidebar) so new or
// renamed groups stay expanded by default.
function persistCollapsedGroups() {
  localState.update({
    collapsedQuickCommandGroupIds: collapsedFromExpanded(allExpandableIds(), expandedGroups.value)
  })
}

const ctxMenuVisible = ref(false)
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
// Right-click context menu payload (command or group), exposed via Menu slot `current`.
type CtxPayload =
  | { kind: 'command'; cmd: QuickCommand }
  | { kind: 'group'; group: QuickCommandGroup }

const deleteGroupDialogVisible = ref(false)
const deletingGroup = ref<QuickCommandGroup | null>(null)

const groupNameDialogVisible = ref(false)
const groupNameInput = ref('')
const renamingGroup = ref<QuickCommandGroup | null>(null)

const editDialogVisible = ref(false)
const editingCmdId = ref<string | undefined>(undefined)
const editingCmdName = ref<string | undefined>(undefined)
const editingCmdCommand = ref('')
const editingCmdGroupId = ref<string | undefined>(undefined)
const editingCmdRemark = ref<string | undefined>(undefined)

onMounted(async () => {
  await store.load()
  await localState.init()
  expandedGroups.value = expandedFromCollapsed(
    allExpandableIds(),
    localState.state.collapsedQuickCommandGroupIds ?? []
  )
})


function toggleGroup(id: string) {
  if (expandedGroups.value.has(id)) expandedGroups.value.delete(id)
  else expandedGroups.value.add(id)
  persistCollapsedGroups()
}

function matchesSearch(cmd: QuickCommand): boolean {
  if (!searchQuery.value.trim()) return true
  const q = searchQuery.value.toLowerCase()
  if (cmd.name && cmd.name.toLowerCase().includes(q)) return true
  if (cmd.command.toLowerCase().includes(q)) return true
  return false
}

function getAllVisibleIds(): string[] {
  const ids: string[] = []
  for (const g of store.groups) {
    if (expandedGroups.value.has(g.id)) {
      for (const c of store.getCommandsByGroup(g.id).filter(matchesSearch)) {
        ids.push(c.id)
      }
    }
  }
  // ungrouped
  if (store.groups.length > 0) {
    if (expandedGroups.value.has('__ungrouped__')) {
      for (const c of store.getCommandsByGroup(undefined).filter(matchesSearch)) {
        ids.push(c.id)
      }
    }
  } else {
    for (const c of store.getCommandsByGroup(undefined).filter(matchesSearch)) {
      ids.push(c.id)
    }
  }
  return ids
}

function onListKeydown(e: KeyboardEvent) {
  const ids = getAllVisibleIds()
  if (ids.length === 0) return
  const idx = ids.indexOf(focusedId.value || '')

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const nextIdx = idx >= 0 && idx < ids.length - 1 ? idx + 1 : 0
    focusedId.value = ids[nextIdx]
    selectedId.value = ids[nextIdx]
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const prevIdx = idx > 0 ? idx - 1 : ids.length - 1
    focusedId.value = ids[prevIdx]
    selectedId.value = ids[prevIdx]
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (focusedId.value) {
      const cmd = store.commands.find(c => c.id === focusedId.value)
      if (cmd) runCommand(cmd)
    }
  } else if (e.key === 'Delete') {
    e.preventDefault()
    if (focusedId.value) {
      const cmd = store.commands.find(c => c.id === focusedId.value)
      if (cmd) deleteCommand(cmd)
    }
  }
}

function selectCommand(id: string) {
  selectedId.value = id
  focusedId.value = id
}

function getTargetSessionIds(): string[] {
  const activeTabId = tabStore.activeTabId
  if (!activeTabId) return []
  const tab = tabStore.tabs.find(t => t.id === activeTabId)
  if (!tab) return []

  // Broadcast mode: send to broadcasting SSH/local panels in the workspace
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

  // Normal mode: send to active panel only
  const activePanelId = tab.type === 'workspace' ? tab.activePanelId : (tab.type === 'terminal' ? tab.panelId : null)
  if (!activePanelId) return []
  const panel = panelStore.getPanel(activePanelId)
  if (!panel?.sessionId) return []
  return [panel.sessionId]
}

async function sendCommand(cmd: QuickCommand, mode: 'run' | 'paste') {
  const sids = getTargetSessionIds()
  if (sids.length === 0) return

  for (const sid of sids) {
    if (mode === 'paste') {
      queuedSessionWrite(sid, cmd.command)
      continue
    }
    const text = cmd.command.replace(/\r\n?/g, '\n')
    const lines = text.split('\n').filter(l => l.length > 0)
    for (let i = 0; i < lines.length; i++) {
      queuedSessionWrite(sid, lines[i] + '\r')
      if (i < lines.length - 1) await new Promise(r => setTimeout(r, 100))
    }
  }
  // Return focus to the terminal so the user can press Enter/edit without
  // an extra mouse click (issue #285). In broadcast mode, focus the active
  // panel — the one the user is looking at.
  focusActivePanelTerminal()
}

function runCommand(cmd: QuickCommand) { sendCommand(cmd, 'run') }
function pasteCommand(cmd: QuickCommand) { sendCommand(cmd, 'paste') }

async function copyCommand(cmd: QuickCommand) {
  try {
    await navigator.clipboard.writeText(cmd.command)
    msg.success(t('quickCommands.copied'))
  } catch {
    msg.error(t('quickCommands.copyFailed'))
  }
}

function onCommandContextMenu(e: MouseEvent, cmd: QuickCommand) {
  e.stopPropagation()
  selectCommand(cmd.id)
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, { kind: 'command', cmd })
}
function onGroupContextMenu(e: MouseEvent, group: QuickCommandGroup) {
  e.stopPropagation()
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, { kind: 'group', group })
}

function editCommand(cmd: QuickCommand) {
  editingCmdId.value = cmd.id
  editingCmdName.value = cmd.name
  editingCmdCommand.value = cmd.command
  editingCmdGroupId.value = cmd.groupId
  editingCmdRemark.value = cmd.remark
  editDialogVisible.value = true
  ctxMenuVisible.value = false
}

function deleteCommand(cmd: QuickCommand) {
  store.deleteCommand(cmd.id)
  if (selectedId.value === cmd.id) selectedId.value = null
  if (focusedId.value === cmd.id) focusedId.value = null
  ctxMenuVisible.value = false
}

function addCommand(groupId?: string) {
  editingCmdId.value = undefined
  editingCmdName.value = undefined
  editingCmdCommand.value = ''
  editingCmdGroupId.value = groupId
  editingCmdRemark.value = undefined
  editDialogVisible.value = true
  ctxMenuVisible.value = false
}

function addGroup() {
  renamingGroup.value = null
  groupNameInput.value = ''
  groupNameDialogVisible.value = true
}

const addMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const addMenuVisible = ref(false)
function onAddCommand() {
  addMenuVisible.value = false
  addCommand()
}
function onAddGroup() {
  addMenuVisible.value = false
  addGroup()
}

function renameGroup(group: QuickCommandGroup) {
  renamingGroup.value = group
  groupNameInput.value = group.name
  groupNameDialogVisible.value = true
  ctxMenuVisible.value = false
}

function doSaveGroupName() {
  const name = groupNameInput.value.trim()
  if (!name) return
  if (renamingGroup.value) store.renameGroup(renamingGroup.value.id, name)
  else {
    const g = store.addGroup(name)
    expandedGroups.value.add(g.id)
  }
  groupNameDialogVisible.value = false
}

function deleteGroupDialog(group: QuickCommandGroup) {
  deletingGroup.value = group
  deleteGroupDialogVisible.value = true
  ctxMenuVisible.value = false
}

function doDeleteGroup(deleteCommands: boolean) {
  if (deletingGroup.value) store.deleteGroup(deletingGroup.value.id, deleteCommands)
  deleteGroupDialogVisible.value = false
  deletingGroup.value = null
}

// Drag and drop
function onCommandDragStart(e: DragEvent, cmd: QuickCommand) {
  if (!e.dataTransfer) return
  e.dataTransfer.setData('application/qc-id', cmd.id)
  e.dataTransfer.effectAllowed = 'move'
}

function onGroupDragOver(e: DragEvent, groupId: string) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  dragOverGroupId.value = groupId
}

function onGroupDragLeave(groupId: string) {
  if (dragOverGroupId.value === groupId) {
    dragOverGroupId.value = null
  }
}

async function onGroupDrop(groupId: string, e: DragEvent) {
  e.preventDefault()
  dragOverGroupId.value = null
  const cmdId = e.dataTransfer?.getData('application/qc-id')
  if (!cmdId) return
  const targetGroupId = groupId === '__ungrouped__' ? undefined : groupId
  const cmd = store.commands.find(c => c.id === cmdId)
  if (cmd) {
    store.updateCommand(cmd.id, cmd.name, cmd.command, targetGroupId, cmd.remark)
  }
}

// Search: expand all groups and auto-select first match
watch(searchQuery, (q) => {
  if (q.trim()) {
    store.groups.forEach(g => expandedGroups.value.add(g.id))
    expandedGroups.value.add('__ungrouped__')
  }
  const ids = getAllVisibleIds()
  if (ids.length > 0) {
    focusedId.value = ids[0]
    selectedId.value = ids[0]
  } else {
    focusedId.value = null
    selectedId.value = null
  }
})
</script>

<style scoped>
.quick-commands-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.qc-toolbar {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0 0.625rem 0.375rem;
  flex-shrink: 0;
}

.qc-search-input {
  flex: 1;
  min-width: 0;
}

.qc-icon-btn {
  width: 1.875rem;
  height: 1.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.qc-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.qc-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem 0.5rem;
}

.qc-group-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.625rem 0.375rem 0.375rem;
  cursor: pointer;
  user-select: none;
  border-radius: var(--radius-sm);
  transition: background 0.12s ease;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.qc-group-header:hover {
  background: var(--bg-hover);
}

.qc-group-header.drag-over {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.qc-group-arrow {
  display: inline-flex;
  align-items: center;
  width: 1rem;
  color: var(--text-disabled);
}

.qc-group-name {
  font-weight: 600;
  flex: 1;
}


.qc-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.375rem 0.625rem;
  min-height: 2.25rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.12s ease;
  margin-bottom: 0.125rem;
  user-select: none;
}

.qc-item.indented {
  padding-left: 1.625rem;
}

.qc-item:hover {
  background: var(--bg-hover);
}

.qc-item.active {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.qc-item.active .qc-item-name {
  color: var(--accent);
}

.qc-item-content {
  flex: 1;
  min-width: 0;
  line-height: 1.4;
}

.qc-item-name {
  font-size: 0.75rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qc-item-cmd {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-family: var(--font-mono, 'Consolas', 'Courier New', monospace);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qc-item-cmd-only {
  font-size: 0.75rem;
}

.qc-item-actions {
  display: flex;
  gap: 0.125rem;
  flex-shrink: 0;
}

.qc-action-btn {
  width: 1.875rem;
  height: 1.875rem;
}

.qc-empty {
  padding: 1.5rem 0.75rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
}

.delete-group-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}
</style>
