<template>
  <div
    class="companion-sidebar file-sidebar"
  >
    <div v-if="!sessionId" class="companion-empty">
      <span v-if="connecting">{{ t('companion.connecting') }}</span>
      <span v-else-if="connectError">{{ connectError }}</span>
      <span v-else>{{ t('companion.needSsh') }}</span>
    </div>

    <template v-else>
      <div
        class="file-body"
        :class="{ 'drag-active': dragOver }"
        :id="FILE_DROP_ID"
        data-file-drop-target
        @dragenter.prevent="onDragEnter"
        @dragleave.prevent="onDragLeave"
        @dragover.prevent="onDragOver"
        @drop.prevent="onDropUpload"
      >
        <div v-if="dragOver" class="drop-overlay">
          <span>{{ t('sftp.dropHere') }}</span>
        </div>

        <FileList
          mode="remote"
          breadcrumb-mode="remote"
          :show-send-to-other="false"
          :breadcrumb-path="cwd"
          :breadcrumb-saved-paths="settingsStore.sftpBookmarks.remotePaths"
          :files="files"
          :loading="loading"
          :paste-loading="pasteLoading"
          :cut-item-names="cutItemNames"
          :clipboard-count="clipboardCount"
          :clipboard-mode="clipboard?.mode"
          @navigate="onNavigate"
          :can-back="canBack"
          :can-forward="canForward"
          @back="onBack"
          @forward="onForward"
          @up="onUp"
          @refresh="onRefresh"
          @upload="onUpload"
          @download-to="onDownloadTo"
          @rename="onRename"
          @delete="onDelete"
          @mkdir="onMkdir"
          @symlink="onSymlink"
          :supports-symlink="true"
          show-copy-path-to-terminal
          @chmod="onChmod"
          @send-to-other="onDownloadTo"
          @edit="onEditFile"
          @edit-external="onEditExternal"
          @open-with-system="onOpenWithSystem"
          @new-file="onNewFile"
          @copy-to-clipboard="onCopyToClipboard"
          @cut-to-clipboard="onCutToClipboard"
          @paste="onPaste"
          @clear-clipboard="onClearClipboard"
          @cancel-paste="onCancelPaste"
          @open="onEditFile"
          @cancel-load="onCancelLoad"
          @save-bookmark="onSaveBookmark"
          @remove-bookmark="onRemoveBookmark"
          @copy-path-to-terminal="onCopyPathToTerminal"
        />
      </div>

      <!-- Transfer history / progress panel (pinned at the sidebar bottom).
           Defaults to collapsed; a new transfer expands it (see the watcher). -->
      <TransferPanel
        v-model:height="transferHeight"
        :collapsed="sidebarTransferCollapsed"
        @update:collapsed="(v: boolean) => sidebarTransferCollapsed = v"
        resizable
        :tasks="transferTasks"
        @cancel="onCancelTransfer"
        @pause="onPauseTransfer"
        @resume="onResumeTransfer"
        @retry="onRetryTransfer"
        @clearCompleted="clearFinishedTransfers"
      >
        <template #actions>
          <button
            class="filter-icon-btn"
            :class="{ active: followActive }"
            :disabled="!followSupported"
            :title="t('sftp.followPathHint')"
            @click="toggleFollow"
          ><el-icon><FolderSync :size="'0.875rem'" /></el-icon></button>
        </template>
        <template #actions-end>
          <button
            class="filter-icon-btn"
            :disabled="!sessionId"
            :title="t('companion.openSftpTab')"
            @click="openStandaloneSftp"
          ><el-icon><ExternalLink :size="'0.875rem'" /></el-icon></button>
        </template>
      </TransferPanel>
    </template>

    <!-- Change permission dialog (shared with the full SFTP tab) -->
    <FileChmodDialog
      v-model:visible="chmodVisible"
      :name="chmodItem?.name"
      :owner="chmodItem?.owner"
      :group="chmodItem?.group"
      :mode="chmodItem?.mode"
      @confirm="onChmodConfirm"
    />

    <!-- Generic dialog (rename / new dir / new file / new link / delete) -->
    <FileGenericDialog
      v-model:visible="genDlg.visible"
      :title="genDlg.title"
      :type="genDlg.type"
      :input-value="genDlg.inputValue"
      :placeholder="genDlg.placeholder"
      :input2-value="genDlg.inputValue2"
      :input2-placeholder="genDlg.input2Placeholder"
      :message="genDlg.message"
      @update:inputValue="(v: string) => genDlg.inputValue = v"
      @update:input2Value="(v: string) => genDlg.inputValue2 = v"
      @confirm="onGenericConfirm"
      @cancel="onGenericCancel"
    />

    <!-- Overwrite/rename conflict dialog -->
    <FileConflictDialog
      v-model:visible="conflictVisible"
      :files="conflictFiles"
      @resolve="onConflictResolve"
    />

    <!-- Remote file editor (shared CodeMirror dialog) -->
    <FileEditorDialog
      ref="fileEditorRef"
      v-model:visible="editorVisible"
      :session-id="sessionId"
      mode="remote"
      @saved="onRefresh"
    />
  </div>
</template>

<script setup lang="ts">
import { ExternalLink, FolderSync } from '@lucide/vue'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { useCompanionStore } from '../stores/companionStore'
import { usePanelStore } from '../stores/panelStore'
import { useSettingsStore } from '../stores/settingsStore'
import {
  SftpListRemote, SftpChangeRemoteDir, SftpOpenExternalEditor, SftpOpenWithSystem, ListSessions,
  SessionInjectCwdHook, SessionIsCwdHookInstalled,
} from '../../bindings/easyaiot/terminal/app'
import {
  useFilePanel, useConflictDialog, useFileDialogs, useFileListing, useChmodDialog,
  useEditorBridge, useDragOver, useNativeFileDrop, remoteFileOps, resolveRemoteTarget, joinPath,
} from '../composables/useFilePanel'
import { bindExtEditUploadedToast } from '../composables/useFilePanel'
import FileList from './FileList.vue'
import type { FileItem } from './FileList.vue'
import TransferPanel from './TransferPanel.vue'
import FileChmodDialog from './FileChmodDialog.vue'
import FileEditorDialog from './FileEditorDialog.vue'
import FileGenericDialog from './FileGenericDialog.vue'
import FileConflictDialog from './FileConflictDialog.vue'
import { Events } from '@wailsio/runtime'
import { watchNewTransferTasks } from '../composables/useTransferTasks'
import { registerTransferRoute } from '../services/transferTaskCenter'
import { queuedSessionWrite } from '../services/sessionWriter'

const { t } = useI18n()
bindExtEditUploadedToast()
const companionStore = useCompanionStore()
const panelStore = usePanelStore()
const settingsStore = useSettingsStore()

const connecting = ref(false)
const connectError = ref('')
// Transfer panel: default height (px), adjustable by dragging its top edge.
const transferHeight = ref(130)
// The transfer panel starts COLLAPSED (only its button bar shows) and a new
// transfer expands it — the user can always re-collapse via the bar's toggle.
const sidebarTransferCollapsed = ref(true)
// Set on unmount so late transfer-done callbacks (routes outlive the
// sidebar's v-if) don't refresh an unmounted component.
let sidebarDisposed = false

let refreshTimer: ReturnType<typeof setTimeout> | null = null
let refreshDebounce: ReturnType<typeof setTimeout> | null = null
// Unique id on this component's drop zone. Wails v3 forwards the id of the
// element the file was dropped on via common:WindowFilesDropped, so keep only
// the drops that actually landed on this sidebar (SFTP panes are also targets).
const FILE_DROP_ID = 'file-sidebar-drop'

const sessionId = computed(() => companionStore.currentSftpSessionId)
const transferKey = computed(() => companionStore.transferKey || 'companion-sftp')
const transferTasks = computed(() => panelStore.getTransferTasks(transferKey.value))
// Auto-expand the collapsed panel whenever a NEW transfer task appears.
watchNewTransferTasks(() => transferTasks.value, () => { sidebarTransferCollapsed.value = false })
const LIST_TIMEOUT_MS = 20000

function scheduleRefreshRetry() {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => {
    if (sessionId.value && companionStore.filesVisible && files.value.length === 0) {
      onRefresh()
    }
  }, 800)
}

/** Coalesce bursty refresh (transfer complete + delete + mkdir). */
function scheduleRefresh(delay = 250) {
  if (refreshDebounce) clearTimeout(refreshDebounce)
  refreshDebounce = setTimeout(() => {
    refreshDebounce = null
    onRefresh()
  }, delay)
}

async function ensureConnected() {
  const pid = companionStore.activeFilesPanelId
  if (!pid || !companionStore.filesVisible) return
  connecting.value = true
  connectError.value = ''
  try {
    await companionStore.ensureSftp(pid)
  } catch (e: any) {
    connectError.value = e?.toString?.() || t('companion.listFailed')
  } finally {
    connecting.value = false
  }
}

// Listing / navigation engine (refresh coalescing + retry glue stays here).
const listing = useFileListing({
  sid: () => sessionId.value ?? undefined,
  list: SftpListRemote,
  changeDir: SftpChangeRemoteDir,
  resolveTarget: resolveRemoteTarget,
  listTimeoutMs: LIST_TIMEOUT_MS,
  onListSuccess: () => { connectError.value = '' },
  onListError: (err) => {
    if (/not connected/i.test(err)) { scheduleRefreshRetry(); return true }
    if (/timeout/i.test(err)) { msg.warning(t('companion.refreshTimeout')); return true }
    return false
  },
})
const { cwd, files, loading, onRefresh, onNavigate, onCancelLoad,
  canBack, canForward, onBack, onForward, onUp } = listing

// Shared dialog + conflict plumbing and the per-panel file actions live in
// the useFilePanel composable (same implementation as the SFTP tab's panes).
const conflicts = useConflictDialog()
const { conflictVisible, conflictFiles, onConflictResolve } = conflicts
const fileDialogs = useFileDialogs()
const { dlg: genDlg, onGenericConfirm, onGenericCancel } = fileDialogs

// Drag-hover + native (OS) file-drop routing. The Wails native drop owns the
// upload when bound; HTML5 drop handling backs off while it is active.
const { dragOver, onDragEnter, onDragLeave, onDragOver, clearDragState } = useDragOver()
const nativeDrop = useNativeFileDrop({
  elementId: FILE_DROP_ID,
  isActive: () => !!companionStore.filesVisible && !!sessionId.value,
  upload: (paths) => { clearDragState(); uploadPaths(paths) },
})
const bindFileDrop = nativeDrop.bind
const unbindFileDrop = nativeDrop.unbind

function onDropUpload(e: DragEvent) {
  e.preventDefault()
  clearDragState()
  // OS file drops are owned by the Wails native file-drop event
  // (common:WindowFilesDropped, routed by element id) and uploaded by
  // absolute path. Nothing to do on the HTML5 side.
}

// Open the current companion's file view as a standalone tab. SSH panels open
// an SFTP tab (mirroring the SSH tab's context-menu action); WSL panels open a
// wsl-file tab over the distro.
function openStandaloneSftp() {
  const pid = companionStore.activeFilesPanelId
  const panel = pid ? panelStore.getPanel(pid) : null
  if (!panel) return
  const ev = companionStore.isWslPanel(pid) ? 'app:connect-wsl-file' : 'app:connect-sftp'
  window.dispatchEvent(new CustomEvent(ev, { detail: panel }))
}

// ── "Follow terminal path" (per-panel toggle) ──
// When enabled for the active SSH/WSL panel, the sidebar navigates whenever the
// panel's terminal shell reports a cwd change (terminal:cwd, emitted by the
// backend on OSC 7 / shell integration). The flag is per panel id and
// ephemeral; rapid cd chains are debounced (trailing) so only the last path
// navigates.
const followActive = computed(() => {
  const pid = companionStore.activeFilesPanelId
  return !!pid && companionStore.followPathByPanel[pid] === true
})
// Following requires an SSH or WSL terminal panel (the only panels that emit
// terminal:cwd with POSIX paths).
const followSupported = computed(() => !!companionStore.activeFilesPanelId)

async function toggleFollow() {
  const pid = companionStore.activeFilesPanelId
  if (!pid) return
  const wasOn = companionStore.followPathByPanel[pid] === true
  // Enabling follow without startup shell integration (the user turned the
  // connection's「目录跟随启动注入」off): confirm once, then type the OSC-7
  // hook into the running shell so cwd reporting starts at the next prompt.
  // SSH only: WSL panels already inject the hook unconditionally at startup.
  if (!wasOn) {
    const panel = panelStore.getPanel(pid)
    if (panel?.config?.type === 'ssh' && panel.sessionId && panel.config?.shellIntegration === false) {
      let installed = false
      try {
        installed = await SessionIsCwdHookInstalled(panel.sessionId)
      } catch {
        installed = false
      }
      if (!installed) {
        // Already-injected sessions never prompt (checked above); cancelling
        // leaves follow off.
        const r = await fileDialogs.openGeneric({
          type: 'message',
          title: t('sftp.followInjectTitle'),
          message: t('sftp.followInjectConfirm'),
        })
        if (!r.ok) return
      }
    }
  }
  companionStore.toggleFollowPath(pid)
  if (wasOn) return
  const panel = panelStore.getPanel(pid)
  if (panel?.config?.type !== 'ssh') return
  if (!panel.sessionId) return
  if (panel.config?.shellIntegration !== false) return // startup injection active
  try {
    const injected = await SessionInjectCwdHook(panel.sessionId)
    // injected=false means the hook was already installed on this session —
    // no toast, to avoid rewarding a mere re-toggle.
    if (injected) msg.success(t('sftp.followInjectOk'))
  } catch {
    // Follow itself is harmless without the hook; keep it enabled.
    msg.warning(t('sftp.followInjectFailed'))
  }
}

let followTimer: ReturnType<typeof setTimeout> | null = null
function scheduleFollowNavigate(path: string) {
  if (followTimer) clearTimeout(followTimer)
  followTimer = setTimeout(() => {
    followTimer = null
    // Re-check: the sidebar may have navigated elsewhere during the debounce.
    if (path === cwd.value) return
    onNavigate(path)
  }, 300)
}

let unsubCwd: (() => void) | null = null

function onTerminalCwd(ev: { data?: unknown }) {
  const p = ev?.data as { sessionId?: string; cwd?: string } | undefined
  if (!p?.sessionId || !p.cwd) return
  // Only the active SSH/WSL panel's own terminal session drives navigation.
  const pid = companionStore.activeFilesPanelId
  if (!pid || companionStore.followPathByPanel[pid] !== true) return
  const panel = panelStore.getPanel(pid)
  if (!panel || panel.sessionId !== p.sessionId) return
  if (!p.cwd.startsWith('/')) return // Windows local terminals are out of scope
  scheduleFollowNavigate(p.cwd)
}

// "Copy path to terminal" (FileList context menu): the clipboard write already
// happened in FileList. Additionally, type the path at the prompt of the
// terminal panel that owns this sidebar — the SSH (or WSL) panel tracked by the
// companion store, whose panel session IS the terminal. Without one, no-op.
function onCopyPathToTerminal(text: string) {
  const pid = companionStore.activeFilesPanelId
  const sid = pid ? panelStore.getPanel(pid)?.sessionId : null
  if (!sid) return
  // Path only — no trailing newline, so the user can complete the command.
  queuedSessionWrite(sid, text)
}

// ── Change-permission dialog (shared FileChmodDialog) ──
const chmod = useChmodDialog({
  target: (item) => {
    const sid = sessionId.value
    return sid ? { sid, path: joinPath(cwd.value, item.name) } : null
  },
  refresh: scheduleRefresh,
})
const { chmodVisible, chmodItem, onChmod, onChmodConfirm } = chmod

// ── Editor dialog bridge (shared FileEditorDialog) ──
const editor = useEditorBridge({ saved: () => onRefresh() })
const { editorVisible, fileEditorRef } = editor

// ── Shared panel logic (clipboard, dialogs, file ops) — mirrors the SFTP tab ──
// The "new link" entry is always shown: companion panels are SSH (SFTP/SCP) or
// WSL, both of which can create symbolic links.
const {
  clipboard, cutItemNames, clipboardCount, pasteLoading,
  onCopyToClipboard, onCutToClipboard, onClearClipboard, onCancelPaste, onPaste,
  onRename, onDelete, onMkdir, onNewFile, onSymlink,
  onUpload, onDownloadTo,
  onEditFile, onEditExternal, onOpenWithSystem,
  onCancelTransfer, onPauseTransfer, onResumeTransfer, onRetryTransfer, clearFinishedTransfers,
  onSaveBookmark, onRemoveBookmark,
  uploadPaths,
} = useFilePanel({
  sid: () => sessionId.value ?? undefined,
  cwd,
  files,
  refresh: scheduleRefresh,
  ops: remoteFileOps,
  conflicts,
  dialogs: fileDialogs,
  bookmarkMode: 'remote',
  transferTasks: () => transferTasks.value,
  openEditor: (path, title) => editor.openEditor(path, title, 'remote'),
  openExternal: (sid, path, cmd) => SftpOpenExternalEditor(sid, path, cmd),
  openWithSystem: (sid, path) => SftpOpenWithSystem(sid, path),
})

let unsubStatus: (() => void) | null = null
let unsubData: (() => void) | null = null
let unsubExtEdit: (() => void) | null = null

// On disconnect/error nothing will ever complete the in-flight transfers, so
// mark them (and their running files) failed here — otherwise they would sit
// as "running" forever. Failed tasks become retryable in the transfer panel.
function markTransferTasksDisconnected() {
  for (const t of transferTasks.value) {
    if (t.status === 'running' || t.status === 'paused') {
      t.status = 'error'
      t.files.forEach(f => { if (f.status === 'running') f.status = 'failed' })
    }
  }
}

function bindListeners() {
  unsubStatus?.()
  unsubData?.()
  unsubExtEdit?.()
  unsubStatus =Events.On('session:status', (ev) => { const payload: { id: string; status: string } = ev.data;
    if (payload.id !== sessionId.value) return
    if (payload.status === 'connected') {
      onRefresh()
      // Reconnect: re-install the runtime cwd hook if follow was enabled and
      // startup shell integration is not active. SSH panels only (WSL injects
      // at startup); skip connections with post-login automation so the hook
      // command cannot interleave with that automation's keystrokes. Best
      // effort, never blocks the refresh above.
      const pid = companionStore.activeFilesPanelId
      const panel = pid ? panelStore.getPanel(pid) : null
      if (pid && panel?.sessionId === payload.id &&
          panel.config?.type === 'ssh' &&
          companionStore.followPathByPanel[pid] === true &&
          panel.config?.shellIntegration !== false &&
          !panel.config?.postLoginScript &&
          !(panel.config?.postLoginExpectSteps?.length)) {
        SessionInjectCwdHook(panel.sessionId).catch(() => {})
      }
    } else if (payload.status === 'error') {
      markTransferTasksDisconnected()
      connectError.value = t('sftp.connectError')
    } else if (payload.status === 'disconnected') {
      markTransferTasksDisconnected()
    }
   })
  unsubData =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data;
    if (payload.id !== sessionId.value) return
    const connMatch = payload.data.match(/\[Connection failed: ([^\]]+)\]/)
    if (connMatch) {
      connectError.value = connMatch[1]
      msg.error(connMatch[1])
      return
    }
  })

  // External-editor status events (started / uploaded / closed): refresh the
  // listing when edits land back on the remote, like the SFTP tab does.
  unsubExtEdit = Events.On('sftp:extedit', (ev) => {
    const payload = ev?.data as { sessionId?: string; path?: string; status?: string }
    if (payload?.sessionId !== sessionId.value) return
    if (payload.status === 'uploaded') {
      onRefresh()
    }
  })

  // Transfer events are routed app-level by transferTaskCenter keyed by
  // session id. Registering here on every session change keeps one route
  // per (session, list key); earlier routes stay registered so transfers
  // keep updating their list while another terminal is active or the
  // sidebar view is hidden. Routes are dropped when the panel is disposed
  // (companionStore.disposeForPanel).
  const sid = sessionId.value
  const key = companionStore.transferKey
  const pid = companionStore.activeFilesPanelId
  if (sid && key) {
    registerTransferRoute(sid, key, (status) => {
      if (sidebarDisposed || status !== 'done') return
      // Routes outlive panel switches; only refresh when this route's own
      // panel is the one the sidebar is currently showing.
      if (companionStore.activeFilesPanelId !== pid) return
      scheduleRefresh(400)
    })
  }
}

/** Restore this panel's cached listing; returns true if a non-empty cache existed. */
function restoreCache(): boolean {
  const pid = companionStore.activeFilesPanelId
  const sid = sessionId.value
  const cached = pid ? companionStore.getFileViewCache(pid) : null
  if (!cached || !cached.files.length) return false
  // Defer the (possibly huge) reactive assignment to a macrotask (setTimeout
  // 0) so the tab switch paints first. `requestAnimationFrame` is not enough
  // here: rAF callbacks run before the next frame's paint, so the restore
  // would still jank the switch frame itself. setTimeout runs post-paint —
  // the browser paints the switched tab between tasks, then the sidebar pays
  // the reactivity + sort cost. Guarded: if the user switched panels before
  // the callback fires, the stale restore is dropped.
  setTimeout(() => {
    if (companionStore.activeFilesPanelId !== pid || sessionId.value !== sid) return
    cwd.value = cached.cwd
    files.value = cached.files as FileItem[]
  }, 0)
  return true
}

watch(sessionId, async (sid) => {
  // Re-entering an already-visited tab: restore its cached listing instead of
  // re-fetching it, so switching back shows the previous content instantly.
  if (restoreCache()) {
    if (sid) bindListeners()
    return
  }
  files.value = []
  cwd.value = ''
  if (!sid) return
  bindListeners()
  try {
    const sessions = await ListSessions()
    const sess = sessions.find(s => s.id === sid)
    if (sess?.status === 'connected') await onRefresh()
    else scheduleRefreshRetry()
  } catch {
    scheduleRefreshRetry()
  }
})

// Persist the current listing per files panel so a later switch-back can restore it.
watch([files, cwd], () => {
  const pid = companionStore.activeFilesPanelId
  if (!pid) return
  companionStore.setFileViewCache(pid, { cwd: cwd.value, files: files.value })
})

watch(() => companionStore.filesVisible, (v) => {
  if (v) {
    ensureConnected()
    bindFileDrop()
  } else {
    unbindFileDrop()
  }
})

watch(() => companionStore.activeFilesPanelId, () => {
  if (companionStore.filesVisible) ensureConnected()
})

onMounted(() => {
  bindListeners()
  // Terminal cwd reports (OSC 7 / shell integration) for path following.
  unsubCwd = Events.On('terminal:cwd', onTerminalCwd)
  // Re-mounting after the view was hidden (e.g. switching files<->monitor):
  // restore this panel's cached listing since the session didn't change.
  restoreCache()
  if (companionStore.filesVisible) {
    ensureConnected()
    bindFileDrop()
  }
})

onUnmounted(() => {
  sidebarDisposed = true
  unsubStatus?.()
  unsubData?.()
  unsubExtEdit?.()
  unsubCwd?.()
  unbindFileDrop()
  if (refreshTimer) clearTimeout(refreshTimer)
  if (followTimer) clearTimeout(followTimer)
})
</script>

<style scoped>
.companion-sidebar {
  background: transparent;
  display: flex;
  flex-direction: column;
  position: relative;
  flex: 1 1 0;
  width: 100%;
  height: auto;
  min-height: 0;
  overflow: hidden;
}
.companion-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.companion-actions {
  display: flex;
  gap: 0.125rem;
  align-items: center;
}
.filter-icon-btn {
  width: 1.625rem;
  height: 1.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
}
.filter-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.filter-icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.filter-icon-btn.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
.transfer-badge {
  position: absolute;
  top: -0.125rem;
  right: -0.125rem;
  min-width: 0.875rem;
  height: 0.875rem;
  padding: 0 0.1875rem;
  border-radius: 62.4375rem;
  background: var(--accent, #22d3ee);
  color: #0b1220;
  font-size: 0.625rem;
  font-weight: 700;
  line-height: 0.875rem;
  text-align: center;
}
.companion-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 1rem;
  text-align: center;
}
.file-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  position: relative;
}
.file-body.drag-active {
  outline: 1px solid var(--accent, #22d3ee);
  outline-offset: -1px;
}
.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--scrim, rgba(0, 0, 0, 0.45));
  pointer-events: none;
}
.drop-overlay span {
  font-size: 0.875rem;
  color: var(--text-primary);
  padding: 0.75rem 1.5rem;
  border: 0.125rem dashed var(--border-hover, var(--accent, #22d3ee));
  border-radius: 0.5rem;
  background: var(--bg-elevated, rgba(0, 0, 0, 0.35));
}
.transfer-panel {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface, var(--bg-elevated));
  min-height: 0;
}
.transfer-panel-resize {
  height: 0.3125rem;
  flex-shrink: 0;
  cursor: ns-resize;
  background: transparent;
}
.transfer-panel-resize:hover {
  background: var(--bg-hover);
}
.transfer-panel-head {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0.375rem 0.5rem 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.transfer-panel-actions {
  display: flex;
  align-items: center;
  gap: 0.125rem;
}
.transfer-empty {
  padding: 1rem 0.75rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
}
.transfer-panel :deep(.transfer-progress-bar) {
  border-top: none;
  max-height: none;
  flex: 1;
  overflow-y: auto;
  padding: 0.25rem 0.5rem 0.5rem;
}
.file-footer {
  flex-shrink: 0;
  padding: 0.25rem 0.625rem;
  font-size: 0.6875rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
}
.footer-transfer {
  color: var(--accent, #22d3ee);
  cursor: pointer;
}
.footer-transfer:hover {
  text-decoration: underline;
}
.companion-editor-meta {
  margin-bottom: 0.5rem;
}
.lang-badge {
  display: inline-block;
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  border-radius: 62.4375rem;
  background: var(--bg-hover, rgba(255,255,255,0.08));
  color: var(--text-secondary);
}
.companion-editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
}
.companion-editor-opts {
  display: flex;
  gap: 0.5rem;
}
</style>
