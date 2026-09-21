<template>
  <div
    class="tab-item"
    :class="{ active: isActive, 'ai-locked': isAILocked }"
    :data-tab-id="tab.id"
    @click="$emit('activate', tab.id)"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
    draggable="true"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @contextmenu="onContextMenu"
  >
    <button
      v-if="!tabCloseRight && hovered && !tab.locked"
      class="tab-close"
      @click.stop="$emit('close', tab.id)"
    ><X /></button>
    <span
      v-if="tabCloseRight || !hovered || tab.locked"
      class="tab-icon-wrapper"
    >
      <component
        :is="tab.locked ? Lock : tabIcon"
        class="tab-type-icon"
      />
      <span
        v-if="isOutputLogOn"
        class="tab-log-dot"
        :title="t('session.recording', { path: outputLogPath })"
      />
      <span v-else-if="!isActive && hasNotification && !tab.locked" class="tab-notification-dot" />
    </span>
    <span v-if="!editing" class="tab-name" :class="{ 'tab-disconnected': isDisconnected }" :title="tab.name + (tabShortcut ? ` (${tabShortcut})` : '')" @dblclick.stop="startEdit">
      <ArrowDownUp v-if="hasActiveTransfers" class="transfer-indicator" :size="'0.875rem'" title="Transferring..." />
      <span class="tab-name-text">{{ tab.name }}</span>
    </span>
    <input
      v-else
      ref="editInputRef"
      v-model="editName"
      class="tab-name-input"
      @keydown.enter="confirmEdit"
      @keydown.escape="cancelEdit"
      @blur="confirmEdit"
      @click.stop
    />
    <span v-if="tabShortcut && settingsStore.settings.showTabShortcutHints" class="tab-shortcut">{{ tabShortcut }}</span>
    <!-- OSC 9;4 progress indicator: a 2px bar along the tab's bottom edge.
         state 1 = normal (accent), 2 = error (red), 3 = indeterminate
         (animated), 4 = paused/warning (orange). -->
    <span
      v-if="activeProgress"
      class="tab-progress"
      :class="`tab-progress-${activeProgress.state}`"
      :style="activeProgress.state === 3 ? undefined : { width: `${Math.max(2, Math.min(100, activeProgress.value))}%` }"
    />
    <Radio
      v-if="showBroadcastIcon"
      class="tab-broadcast-icon"
      :size="'0.875rem'"
      :title="t('tab.unbroadcast')"
    />
    <button
      v-if="tabCloseRight && !showBroadcastIcon"
      class="tab-close tab-close-right"
      :class="{ 'tab-close-right-ghost': !hovered || tab.locked }"
      @click.stop="$emit('close', tab.id)"
    ><X /></button>
    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible">
      <!-- ⓪ 工作区操作 -->
      <MenuItem v-if="tab.type === 'workspace'" @click="onSaveWorkspace">
        {{ t('workspace.save') }}
      </MenuItem>
      <MenuItem v-if="tab.type === 'workspace'" :class="{ disabled: tab.locked }" @click="tab.locked ? null : onDissolveWorkspace()">
        {{ t('workspace.dissolve') }}
      </MenuItem>
      <MenuDivider v-if="tab.type === 'workspace'" />

      <!-- ① 标签类操作 -->
      <MenuItem v-if="canDuplicate" :shortcut="menuShortcut('duplicateSession')" @click="onDuplicate">
        {{ t('tab.duplicate') }}
      </MenuItem>
      <MenuItem v-if="canReconnect" @click="onReconnect">{{ t('tab.reconnect') }}</MenuItem>
      <MenuItem v-if="hasServerHost" @click="copyHostAddress">{{ t('tab.copyHostAddress') }}</MenuItem>
      <MenuItem v-if="tab.type === 'terminal'" :shortcut="menuShortcut('lockAI')" @click="toggleAiLock">
        {{ isAILocked ? t('terminal.aiLocked') : t('terminal.lockAI') }}
      </MenuItem>
      <MenuItem v-if="tab.type !== 'start' && tab.type !== 'settings'" @click="startEdit">{{ t('tab.rename') }}</MenuItem>
      <MenuItem v-if="hasLocatableConnection" @click="locateHost">{{ t('tab.locate') }}</MenuItem>
      <MenuItem v-if="tab.type !== 'start' && tab.type !== 'settings'" @click="toggleLock">
        {{ tab.locked ? t('tab.unlock') : t('tab.lock') }}
      </MenuItem>
      <MenuItem v-if="canBroadcast" @click="toggleBroadcastTarget">
        {{ isBroadcastTarget ? t('tab.unbroadcast') : t('tab.broadcast') }}
      </MenuItem>

      <!-- ② 会话文本操作 -->
      <MenuDivider />
      <MenuItem v-if="tab.type === 'terminal'" :shortcut="menuShortcut('terminalSearch')" @click="triggerSearch">
        {{ t('terminal.searchText') }}
      </MenuItem>
      <MenuItem v-if="tab.type === 'terminal'" @click="triggerExport">{{ t('terminal.export') }}</MenuItem>
      <MenuItem v-if="supportsOutputLog" @click="toggleOutputLog">
        {{ isOutputLogOn ? t('session.stopLog') : t('session.startLog') }}
      </MenuItem>
      <MenuItem v-if="supportsOutputLog && isOutputLogOn" @click="openLogDir">
        {{ t('session.openLogDir') }}
      </MenuItem>

      <!-- ③ 连接功能（ssh / rdp） -->
      <MenuDivider />
      <MenuItem v-if="tab.type === 'rdp'" @click="enterRdpFullScreen">{{ t('rdp.fullscreen') }}</MenuItem>
      <MenuItem v-if="isSsh" @click="openSftp">{{ t(fileMenuKey) }}</MenuItem>
      <MenuItem v-if="isSsh" @click="uploadFileRz">{{ t('terminal.uploadFileRz') }}</MenuItem>
      <MenuItem v-if="isSsh" @click="openMonitor">{{ t('sidebar.connectMonitor') }}</MenuItem>
      <MenuItem v-if="isSftpOverSsh" @click="openTerminal">{{ t('tab.openTerminal') }}</MenuItem>

      <!-- ④ 关闭标签操作 -->
      <MenuDivider />
      <MenuItem :class="{ disabled: tab.locked }" :shortcut="menuShortcut('closePanel')" @click="tab.locked ? null : closeTab()">
        {{ t('tab.close') }}
      </MenuItem>
      <MenuItem @click="closeOther">{{ t('tab.closeOther') }}</MenuItem>
      <MenuItem @click="closeRight">{{ t('tab.closeRight') }}</MenuItem>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useCompanionStore } from '../stores/companionStore'
import { formatKeyBinding, tabDigitShortcutPrefix, formatDigitShortcut } from '../composables/useKeyboardShortcuts'
import type { ShortcutAction } from '../types/settings'
import { useK8sStore } from '../stores/k8sStore'
import { useContainerStore } from '../stores/containerStore'
import { useI18n } from '../i18n'
import {
  EnableSessionOutputLog,
  DisableSessionOutputLog,
  GetSessionOutputLogInfo,
  OpenPathInExplorer,
  RDPSetFullScreen,
} from '../../bindings/easyaiot/terminal/app'
import { msg } from '../services/message'
import { ElMessageBox } from 'element-plus'
import { saveWorkspaceToConnections } from '../composables/savedWorkspace'
import type { TerminalTab, SettingsTab, SFTPTab, RDPTab, VNCTab, SPICETab, DBTab, MonitorTab, WorkspaceTab } from '../types/workspace'
import { connectFileMenuKey, fileTransferProto } from '../utils/fileTransferUtils'
import { connectionTypeIconOfKind } from '../utils/connectionTypes'
import { useDuplicateSession } from '../composables/useDuplicateSession'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import { Clipboard } from '@wailsio/runtime'
import { SquareTerminal, FolderUp, X, ArrowDownUp, Lock, Radio } from '@lucide/vue'

const props = defineProps<{
  tab: TerminalTab | SettingsTab | SFTPTab | RDPTab | VNCTab | SPICETab | DBTab | MonitorTab | WorkspaceTab
  shortcutIndex?: number
  isActive: boolean
  hasNotification?: boolean
  showClose?: boolean
  /** OSC 9;4 progress state (null/absent = no active progress). */
  progress?: { state: 0 | 1 | 2 | 3 | 4; value: number } | null
}>()

const emit = defineEmits<{
  activate: [id: string]
  close: [id: string]
  closeBatch: [ids: string[]]
  toggleAiLock: [panelId: string]
}>()

const tabStore = useTabStore()
const panelStore = usePanelStore()
const sessionStore = useSessionStore()
const k8sStore = useK8sStore()

// OSC 9;4 progress (state 0 = "no progress", rendered as nothing).
const activeProgress = computed(() => {
  const p = props.progress
  return p && p.state !== 0 ? p : null
})
const containerStore = useContainerStore()
const settingsStore = useSettingsStore()
const companionStore = useCompanionStore()
const { duplicateSession } = useDuplicateSession()
const { t } = useI18n()

const isMac = /Mac|iPhone|iPad/.test(navigator.userAgent)
const tabShortcut = computed(() => {
  if (!props.shortcutIndex || props.shortcutIndex > 9) return ''
  // Cmd+N on macOS / Ctrl+N elsewhere by default, or the user-configured
  // keyboard.tabSwitchModifier combo — always the real binding.
  const prefix = tabDigitShortcutPrefix(isMac, settingsStore.settings.keyboard.tabSwitchModifier)
  return formatDigitShortcut(prefix, props.shortcutIndex, isMac)
})

// Human-readable keybinding for a shortcut action ('' when unset), shown as a
// hint in the tab right-click context menu. Reactive via settingsStore, so the
// hint updates automatically when the user rebinds keys.
function menuShortcut(action: ShortcutAction): string {
  const b = settingsStore.settings.keyboard[action]
  if (!b) return ''
  return formatKeyBinding(b, isMac)
}

const hovered = ref(false)
const ctxMenuVisible = ref(false)
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)

// Whether the tab close (X) button sits on the right of the tab name,
// per the appearance setting ("tab close button position").
const tabCloseRight = computed(() => settingsStore.settings.tabCloseButton === 'right')

const editing = ref(false)
const editName = ref('')
const editInputRef = ref<HTMLInputElement>()

const tabIcon = computed(() => {
  const t = props.tab
  // The file browser tab's icon follows the panel's backing config (an SSH
  // connection's companion panel honors the SFTP/SCP protocol preference),
  // so it must be resolved before the plain tab-type lookup below.
  if (t.type === 'sftp') {
    const panel = panelStore.getPanel(t.panelId)
    const ct = panel?.config?.type
    if (ct === 'ssh') return connectionTypeIconOfKind(fileTransferProto(panel?.config))
    return connectionTypeIconOfKind(ct) || FolderUp
  }
  // Terminal tabs render the backing panel's session kind (ssh/local/k8s-exec/…).
  if (t.type === 'terminal') {
    const panel = panelStore.getPanel(t.panelId)
    return connectionTypeIconOfKind(panel?.type) || SquareTerminal
  }
  // Everything else (connection tabs + UI tab kinds) resolves from the registry.
  return connectionTypeIconOfKind(t.type)
})

const isAILocked = computed(() => {
  if (props.tab.type === 'workspace') {
    if (tabStore.aiLockedPanelIds.size === 0) return false
    return props.tab.panelIds.some(id => tabStore.isPanelAILocked(id))
  }
  if (props.tab.type !== 'terminal') return false
  return tabStore.isPanelAILocked(props.tab.panelId)
})

// Whether the tab can be a broadcast target / driver. ssh/local/wsl terminal
// tabs (broadcast routes those sessions) and workspace tabs. WSL is a local-run
// terminal, so it broadcasts like local.
const canBroadcast = computed(() => {
  if (props.tab.type === 'workspace') return true
  if (props.tab.type === 'terminal') {
    const p = panelStore.getPanel((props.tab as TerminalTab).panelId)
    return !!p && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')
  }
  return false
})

// Tab-level broadcast status — derived from broadcastPanelIds, so it stays in
// sync with each panel's broadcast button.
const isBroadcastTarget = computed(() =>
  tabStore.isTabBroadcastTarget(props.tab.id)
)

// The broadcast icon and the right close button share one far-right slot,
// so they are mutually exclusive: show the icon only while actually
// broadcasting, and while the right X would be visible (right-close setting +
// hover + not locked) show the X instead — the template v-if's out whichever
// one isn't shown so they never coexist. In the default (left-close) layout
// there is no right X, so the icon is always shown.
const showBroadcastIcon = computed(() =>
  canBroadcast.value &&
  isBroadcastTarget.value &&
  !(tabCloseRight.value && hovered.value && !props.tab.locked)
)


const hasActiveTransfers = computed(() => {
  if (props.tab.type === 'workspace') return false
  const keys = [props.tab.panelId]
  // Terminal tabs also surface their companion file panel's transfers.
  if (props.tab.type === 'terminal') {
    const companionKey = companionStore.sftpTransferKeyOf(props.tab.panelId)
    if (companionKey) keys.push(companionKey)
  }
  return keys.some(k =>
    panelStore.getTransferTasks(k).some(t => t.status === 'running' || t.status === 'paused'))
})

const isDisconnected = computed(() => {
  if (props.tab.type === 'start' || props.tab.type === 'settings') return false
  // k8s main tab has no session; its connect status comes from the k8s store
  // (grey while connecting / on error).
  if (props.tab.type === 'k8s') {
    const s = k8sStore.getConnStatus((props.tab as any).connectionId)
    return s === 'connecting' || s === 'error'
  }
  // container tab likewise has no panel session; its status lives in containerStore
  if (props.tab.type === 'container') {
    const s = containerStore.sessions[(props.tab as any).id]
    return !s || s.loading || !!s.error
  }
  const panelIds: string[] = props.tab.type === 'workspace' ? props.tab.panelIds : 'panelId' in props.tab ? [props.tab.panelId] : []
  if (panelIds.length === 0) return false
  return panelIds.every(pid => {
    const p = panelStore.getPanel(pid)
    if (!p?.sessionId) return true
    const s = sessionStore.getStatus(p.sessionId)
    return s === 'disconnected' || s === 'error'
  })
})

// Session output log state. Refreshed lazily when the right-click menu
// opens; also written after enable/disable so the REC badge stays in
// sync without an extra round-trip.
const isOutputLogOn = ref(false)
const outputLogPath = ref('')
const supportsOutputLog = computed(() => {
  if (props.tab.type !== 'terminal') return false
  const p = panelStore.getPanel((props.tab as TerminalTab).panelId)
  return !!p && ['ssh', 'telnet', 'serial', 'mosh', 'local'].includes(p.type)
})

// Duplicate is supported for tabs backed by a reproducible connection:
// terminals, file transfer, database (incl. mongodb/redis variants), and k8s.
const canDuplicate = computed(() => {
  const type = props.tab.type
  return type === 'terminal' || type === 'sftp' || type === 'database' || type === 'mongodb' || type === 'redis' || type === 'elasticsearch' || type === 'k8s'
})

// Reconnectable panels — terminal types that Panel.vue can re-initiate.
const TTY_RECONNECT_TYPES: readonly string[] = ['ssh', 'telnet', 'serial', 'mosh', 'local', 'tcp', 'k8s-exec', 'container-exec']

// Whether the tab has a right-click 「重连」(Reconnect). Terminal panels are
// re-initiated by Panel.vue via the 'panel:reconnect' event; desktop-protocol
// tabs (rdp/vnc/spice/x11) run their own reconnect inside their content component.
const canReconnect = computed(() => {
  const type = props.tab.type
  if (type === 'rdp' || type === 'vnc' || type === 'spice' || type === 'x11-desktop') return true
  if (type === 'database' || type === 'redis' || type === 'mongodb' || type === 'elasticsearch' || type === 'sftp' || type === 'monitor') {
    return 'panelId' in props.tab && !!panelStore.getPanel(props.tab.panelId)
  }
  if (type === 'k8s' || type === 'container') {
    return 'panelId' in props.tab
  }
  if (type === 'terminal' && 'panelId' in props.tab) {
    const p = panelStore.getPanel(props.tab.panelId)
    return !!p && TTY_RECONNECT_TYPES.includes(p.type)
  }
  return false
})

// SSH connection only — used to show the "连接功能" group of menu items.
const isSsh = computed(() => {
  if (props.tab.type !== 'terminal') return false
  const p = panelStore.getPanel((props.tab as TerminalTab).panelId)
  return p?.type === 'ssh'
})

// SSH-derived file tabs (SFTP/SCP from an SSH connection) — used to show the
// reverse action: open a terminal for the same host.
const isSftpOverSsh = computed(() => {
  if (props.tab.type !== 'sftp') return false
  const p = panelStore.getPanel((props.tab as SFTPTab).panelId)
  // SCP panels also have config.type === 'ssh'; include them as well.
  return p?.config?.type === 'ssh'
})

// Menu label for the file-transfer action follows the connection's protocol
// preference (Connect SFTP / Connect SCP).
const fileMenuKey = computed(() => {
  if (props.tab.type !== 'terminal') return 'sidebar.connectSftp'
  const p = panelStore.getPanel((props.tab as TerminalTab).panelId)
  return connectFileMenuKey(p?.config)
})

// Visibility of each menu group, used to place dividers strictly between
// Group-enable flags moved into MenuDivider's own sibling detection, so no
// longer needed here.

// True when the tab's panel is backed by a saved connection (has a config id),
// so the "定位到连接" item can locate it in the sidebar's connection list.
const hasLocatableConnection = computed(() => {
  if (!('panelId' in props.tab)) return false
  return !!panelStore.getPanel(props.tab.panelId)?.config?.id
})

// Connection host (IP or hostname) of the tab's panel. Empty for tab types
// without a remote endpoint (local, k8s, container, start, settings…).
const serverHost = computed(() => {
  if (!('panelId' in props.tab)) return ''
  return panelStore.getPanel(props.tab.panelId)?.config?.host || ''
})
const hasServerHost = computed(() => !!serverHost.value)

function onDragStart(e: DragEvent) {
  e.dataTransfer?.setData('application/tab-id', props.tab.id)
  e.dataTransfer?.setData('application/tab-type', props.tab.type)
  if (props.isActive) {
    e.dataTransfer?.setData('application/is-active-tab', '1')
  }
  e.dataTransfer!.effectAllowed = 'move'

  // Expose the dragged tab id for dragover handlers (dataTransfer.getData is
  // only readable during drop). TerminalTabContent uses it to detect the
  // active tab hovering its own content and only then switches to the
  // adjacent tab to offer the workspace-merge drop target — so a plain
  // tab-bar reorder never steals the selection.
  tabStore.setDraggingTabId(props.tab.id)
}

function onDragEnd() {
  tabStore.setDraggingTabId(null)
  // The drag ended without consuming the tab (tab-bar reorder, cancelled
  // drag, rejected drop): restore the selection the dragstart-adjacent
  // switch may have moved. A successful workspace merge removes the tab, so
  // there is nothing to restore (and this element no longer exists).
  if (tabStore.activeTabId !== props.tab.id && tabStore.tabs.some(t => t.id === props.tab.id)) {
    tabStore.setActiveTab(props.tab.id)
  }
}

function onContextMenu(e: MouseEvent) {
  e.preventDefault()
  e.stopPropagation()
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, props.tab)
  if (supportsOutputLog.value) {
    refreshOutputLogState()
  }
}

async function refreshOutputLogState() {
  const panel = panelStore.getPanel((props.tab as TerminalTab).panelId)
  if (!panel) {
    isOutputLogOn.value = false
    outputLogPath.value = ''
    return
  }
  try {
    const info = await GetSessionOutputLogInfo(panel.id)
    isOutputLogOn.value = !!info.enabled
    outputLogPath.value = info.path || ''
    panelStore.setOutputLog(panel.id, { enabled: isOutputLogOn.value, path: outputLogPath.value })
  } catch {
    isOutputLogOn.value = false
    outputLogPath.value = ''
  }
}

function closeContextMenu() {
  ctxMenuVisible.value = false
}

watch(ctxMenuVisible, (val) => {
  window.dispatchEvent(new CustomEvent(val ? 'rdp:overlay-push' : 'rdp:overlay-pop'))
})

function startEdit() {
  closeContextMenu()
  editName.value = props.tab.name
  editing.value = true
  nextTick(() => {
    editInputRef.value?.focus()
    editInputRef.value?.select()
  })
}

function confirmEdit() {
  if (!editing.value) return
  editing.value = false
  const newName = editName.value.trim()
  if (newName && newName !== props.tab.name) {
    tabStore.renameTab(props.tab.id, newName)
  }
}

function cancelEdit() {
  editing.value = false
}

function toggleLock() {
  tabStore.toggleTabLock(props.tab.id)
  closeContextMenu()
}

function toggleBroadcastTarget() {
  if (isBroadcastTarget.value) {
    tabStore.disableBroadcastForTab(props.tab.id)
  } else {
    tabStore.enableBroadcastForTab(props.tab.id)
  }
  closeContextMenu()
}

function toggleAiLock() {
  if (props.tab.type === 'terminal') {
    emit('toggleAiLock', props.tab.panelId)
  }
  closeContextMenu()
}

function closeTab() {
  emit('close', props.tab.id)
  closeContextMenu()
}

function closeOther() {
  const allTabs = tabStore.tabs
  const currentIdx = allTabs.findIndex(t => t.id === props.tab.id)
  const ids = allTabs.filter((t, i) => i !== currentIdx && !t.locked).map(t => t.id)
  if (ids.length) emit('closeBatch', ids)
  closeContextMenu()
}

function closeRight() {
  const allTabs = tabStore.tabs
  const currentIdx = allTabs.findIndex(t => t.id === props.tab.id)
  const ids = allTabs.slice(currentIdx + 1).filter(t => !t.locked).map(t => t.id)
  if (ids.length) emit('closeBatch', ids)
  closeContextMenu()
}

async function copyHostAddress() {
  const host = serverHost.value
  if (!host) return
  // Wails clipboard, falling back to the browser API when the runtime is
  // absent (plain dev in a browser) or the call fails.
  let ok = false
  try { ok = await Clipboard.SetText(host) } catch { ok = false }
  if (!ok) {
    try { await navigator.clipboard.writeText(host) } catch { /* no clipboard */ }
  }
  msg.success(t('tab.hostCopied', { host }))
  closeContextMenu()
}

function onDuplicate() {
  closeContextMenu()
  duplicateSession(props.tab)
}

// Dissolve: every member panel returns to the tab bar as a live terminal tab
// (sessions stay alive, broadcast cleared). NOT routed through closeTab —
// that would close the sessions.
async function onDissolveWorkspace() {
  closeContextMenu()
  const wsTab = props.tab as WorkspaceTab
  try {
    await ElMessageBox.confirm(
      t('workspace.dissolveConfirm', { name: wsTab.name, count: wsTab.panelIds.length }),
      t('workspace.dissolve'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
  } catch {
    return
  }
  const created = tabStore.dissolveWorkspace(wsTab.id)
  if (created.length > 0) msg.success(t('workspace.dissolvedToast', { count: created.length }))
}

// Save: create/overwrite the `type: "workspace"` connection record backing
// this tab (see composables/savedWorkspace.ts for the upsert semantics).
async function onSaveWorkspace() {
  closeContextMenu()
  await saveWorkspaceToConnections(props.tab as WorkspaceTab)
}

// Dispatch a 'panel:reconnect' event so the owning content (Panel.vue for
// terminals, the desktop tab-content components for rdp/vnc/spice/x11) can
// force-disconnect and re-initiate the connection.
function onReconnect() {
  closeContextMenu()
  const panelId = 'panelId' in props.tab ? props.tab.panelId : ''
  if (!panelId) return
  window.dispatchEvent(new CustomEvent('panel:reconnect', { detail: { panelId } }))
}

function openSftp() {
  const panel = panelStore.getPanel((props.tab as TerminalTab).panelId)
  if (panel) {
    window.dispatchEvent(new CustomEvent('app:connect-sftp', { detail: panel }))
  }
  closeContextMenu()
}

function uploadFileRz() {
  window.dispatchEvent(new CustomEvent('terminal:send-rz', { detail: { panelId: (props.tab as TerminalTab).panelId } }))
  closeContextMenu()
}

function openMonitor() {
  const panel = panelStore.getPanel((props.tab as TerminalTab).panelId)
  if (panel) {
    window.dispatchEvent(new CustomEvent('app:connect-monitor', { detail: panel }))
  }
  closeContextMenu()
}

function openTerminal() {
  const panel = panelStore.getPanel((props.tab as SFTPTab).panelId)
  if (panel) {
    window.dispatchEvent(new CustomEvent('app:connect-terminal', { detail: panel }))
  }
  closeContextMenu()
}

function locateHost() {
  const panel = panelStore.getPanel((props.tab as TerminalTab).panelId)
  if (panel?.config?.id) {
    window.dispatchEvent(new CustomEvent('app:locate-connection', { detail: { id: panel.config.id } }))
  }
  closeContextMenu()
}

async function enterRdpFullScreen() {
  closeContextMenu()
  const panel = panelStore.getPanel((props.tab as RDPTab).panelId)
  const sid = panel?.sessionId
  if (!sid) return
  window.dispatchEvent(new CustomEvent('rdp:fullscreen-enter'))
  try { await RDPSetFullScreen(sid, true) } catch (e) { console.error('RDP fullscreen error:', e) }
}

async function toggleOutputLog() {
  closeContextMenu()
  const panel = panelStore.getPanel((props.tab as TerminalTab).panelId)
  if (!panel) return
  try {
    if (isOutputLogOn.value) {
      await DisableSessionOutputLog(panel.id)
      isOutputLogOn.value = false
      const prev = outputLogPath.value
      outputLogPath.value = ''
      panelStore.setOutputLog(panel.id, { enabled: false, path: '' })
      msg.copyable(t('session.logStopped', { path: prev }), 'info')
      return
    }
    const path = await EnableSessionOutputLog(panel.id, '')
    if (!path) {
      msg.error(t('session.logFailed', { error: 'unknown' }))
      return
    }
    isOutputLogOn.value = true
    outputLogPath.value = path
    panelStore.setOutputLog(panel.id, { enabled: true, path })
    msg.copyable(t('session.logStarted', { path }), 'success')
  } catch (e: any) {
    msg.error(t('session.logFailed', { error: String(e?.message ?? e) }))
  }
}

async function openLogDir() {
  closeContextMenu()
  if (!outputLogPath.value) return
  try {
    await OpenPathInExplorer(outputLogPath.value)
  } catch (e: any) {
    msg.error(String(e?.message ?? e))
  }
}

function triggerSearch() {
  window.dispatchEvent(new CustomEvent('terminal:open-search', { detail: { panelId: (props.tab as TerminalTab).panelId } }))
  closeContextMenu()
}

function triggerExport() {
  window.dispatchEvent(new CustomEvent('terminal:export', { detail: { panelId: (props.tab as TerminalTab).panelId } }))
  closeContextMenu()
}

onMounted(async () => {
  if (supportsOutputLog.value) {
    await refreshOutputLogState()
  }
})
</script>

<style scoped>
.tab-item {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  height: 1.75rem;
  min-width: 9rem;
  padding: 0 0.75rem;
  margin: 0 1px;
  cursor: pointer;
  user-select: none;
  border-radius: var(--radius-sm);
  position: relative;
  color: var(--text-secondary);
  font-size: 0.75rem;
  transition: background 0.15s ease, color 0.15s ease;
  flex-shrink: 0;
  --wails-draggable: no-drag;
}
.tab-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.tab-item.active {
  background: var(--bg-hover);
  color: var(--text-primary);
  box-shadow: inset 0 0 0 1px var(--accent);
}
/* AI-locked tabs carry a warning-tinted background, not an edge marker, so the
   state reads at a glance (issue #909). The border is left alone: the accent
   ring stays the sole "which tab is selected" signal. */
.tab-item.ai-locked {
  background: var(--warning-tab);
  color: var(--text-primary);
}
.tab-item.ai-locked:hover {
  background: var(--warning-tab-hover);
}
.tab-item.active.ai-locked {
  background: var(--warning-tab-active);
  color: var(--text-primary);
  box-shadow: inset 0 0 0 1px var(--accent);
}
.tab-name {
  font-size: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  /* Keep a full IPv6 address visible; longer custom names still use ellipsis. */
  max-width: 18.75rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 500;
}
.tab-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tab-shortcut {
  flex-shrink: 0;
  margin-left: 0.25rem;
  color: var(--text-muted);
  font-size: 0.625rem;
  font-weight: 500;
  /* UI font so macOS modifier symbols (⌘⌥⇧) render with their native
     system-font shapes instead of a mono fallback. */
  font-family: var(--font-ui);
}
.tab-disconnected {
  opacity: 0.5;
}
.tab-icon-wrapper {
  position: relative;
  display: inline-flex;
  flex-shrink: 0;
  margin-right: 0.25rem;
}
.tab-type-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 0.875rem;
  height: 0.875rem;
  color: var(--text-muted);
}
/* Broadcast status icon occupies the exact same far-right slot as the right
   close button: with margin-left:auto it pushes to the edge, and the right X
   is v-if'd out of the DOM (see template) whenever the icon is shown, so the
   two are never siblings — the icon sits precisely where the X would. In the
   default (left-close) layout there is no right X, so the icon always takes
   the slot. Reserving real layout space (not absolute positioning) means it
   never overlaps the tab name. */
.tab-broadcast-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: auto;
  color: var(--accent);
}
.tab-notification-dot {
  position: absolute;
  top: -0.125rem;
  right: -0.25rem;
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 1px var(--bg-base);
}
/* OSC 9;4 progress bar along the tab's bottom edge (see template). */
.tab-progress {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 2px;
  min-width: 2px;
  background: var(--accent);
  border-radius: 2px;
  pointer-events: none;
  transition: width 0.2s ease;
}
.tab-progress-2 {
  background: #e5484d;
}
.tab-progress-4 {
  background: var(--warning-tab, #f5a623);
}
.tab-progress-3 {
  width: 40%;
  animation: tab-progress-indeterminate 1.4s linear infinite;
}
@keyframes tab-progress-indeterminate {
  from { left: -40%; }
  to { left: 100%; }
}
.tab-log-dot {
  position: absolute;
  right: -0.125rem;
  bottom: -0.125rem;
  width: 0.375rem;
  height: 0.375rem;
  background: #e5484d;
  border-radius: 50%;
  pointer-events: auto;
}
.tab-item.active .tab-type-icon {
  color: var(--accent);
}
.transfer-indicator {
  color: var(--accent);
  flex-shrink: 0;
  line-height: 1;
}
.tab-name-input {
  font-size: 0.75rem;
  font-family: inherit;
  color: var(--text-primary);
  background: var(--bg-base);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 0.125rem 0.375rem;
  width: 7.5rem;
  outline: none;
}
.tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 0.875rem;
  height: 0.875rem;
  margin-right: 0.25rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.12s ease;
}
.tab-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
/* Close button on the right side of the tab (appearance setting).
   margin-left:auto pushes it flush to the far right edge of the tab
   (inside the 0.75rem horizontal padding), instead of hugging the name.

   The button is always present in the layout when the right-side setting is on
   — ghosted (visibility:hidden) while not hovered OR the tab is locked — so its
   slot is always reserved; showing the X only toggles visibility instead of
   inserting/removing an element, which would otherwise re-truncate long names
   and cause jitter (including the instant the tab is locked). */
.tab-close.tab-close-right {
  margin-left: auto;
  margin-right: 0;
}
.tab-close-right-ghost {
  visibility: hidden;
  /* Hide instantly on mouse-leave: `.tab-close` carries transition:all, and
     visibility is a transitionable property, so a visible→hidden ghost would
     otherwise linger for the transition duration. */
  transition: visibility 0s;
}
</style>
