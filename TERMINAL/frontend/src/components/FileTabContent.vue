<template>
  <div class="sftp-tab-content">
    <div class="panes-area">
      <div
        v-show="showLocalPane"
        class="local-pane"
        @dragover.prevent="onDragOver"
        @dragenter.prevent="onDragEnter('local')"
        @dragleave="onDragLeave('local')"
        @drop.capture="onDropLocal"
      >
        <div v-if="dragOverLocal" class="drop-overlay">
          <span>{{ t('sftp.dropHere') }}</span>
        </div>
        <FileList
          mode="local"
          breadcrumb-mode="local"
          :breadcrumb-path="localCwd"
          :breadcrumb-drives="localDrives"
          :breadcrumb-saved-paths="settingsStore.sftpBookmarks.localPaths"
          :files="localFiles"
          :loading="loadingLocal"
          :paste-loading="pasteLoadingLocal"
          :cut-item-names="localCutItemNames"
          :clipboard-count="localClipboardCount"
          :clipboard-mode="localClipboard?.mode"
          :can-back="localCanBack"
          :can-forward="localCanForward"
          @back="onLocalBack"
          @forward="onLocalForward"
          @up="onLocalUp"
          @navigate="onLocalNavigate"
          @send-to-other="onSendToRemote"
          @rename="onLocalRename"
          @delete="onLocalDelete"
          @refresh="onRefreshLocal"
          @mkdir="onLocalMkdir"
          @edit="onLocalEditFile"
          @edit-external="onLocalEditExternal"
          @open-with-system="onLocalOpenWithSystem"
          @new-file="onLocalNewFile"
          @copy-to-clipboard="onLocalCopyToClipboard"
          @cut-to-clipboard="onLocalCutToClipboard"
          @paste="onLocalPaste"
          @cancel-paste="onLocalCancelPaste"
          @clear-clipboard="onLocalClearClipboard"
          @open="onLocalEditFile"
          @cancel-load="onCancelLoadLocal"
          @save-bookmark="onLocalSaveBookmark"
          @remove-bookmark="onLocalRemoveBookmark"
          toolbar-layout="flat"
        />
      </div>
      <div
        class="remote-pane"
        :id="remoteDropId"
        data-file-drop-target
        @dragover.prevent="onDragOver"
        @dragenter.prevent="onDragEnter('remote')"
        @dragleave="onDragLeave('remote')"
        @drop.capture="onDropRemote"
      >
        <div v-if="dragOverRemote" class="drop-overlay">
          <span>{{ t('sftp.dropHere') }}</span>
        </div>
        <FileList
          mode="remote"
          breadcrumb-mode="remote"
          :breadcrumb-path="cwd"
          :protocol="remoteProtocol"
          :dir-file-counts="s3FileCounts"
          :local-pane-toggle="isS3Panel"
          :local-pane-visible="showLocalPane"
          @toggle-local-pane="onToggleLocalPane"
          :breadcrumb-saved-paths="settingsStore.sftpBookmarks.remotePaths"
          :files="remoteFiles"
          :loading="loadingRemote"
          :paste-loading="pasteLoadingRemote"
          :cut-item-names="cutItemNames"
          :clipboard-count="clipboardCount"
          :clipboard-mode="clipboard?.mode"
          :can-back="remoteCanBack"
          :can-forward="remoteCanForward"
          @back="onRemoteBack"
          @forward="onRemoteForward"
          @up="onRemoteUp"
          @navigate="onRemoteNavigate"
          @send-to-other="onSendToLocal"
          @rename="onRename"
          @delete="onDelete"
          @refresh="onRefreshRemote"
          @mkdir="onMkdir"
          @create-bucket="onCreateBucket"
          @delete-bucket="onDeleteBucket"
          @symlink="onSymlink"
          :supports-symlink="remoteSupportsSymlink"
          @chmod="(item: FileItem) => onChmod(item, 'remote')"
          @upload="onUpload"
          @download-to="onDownloadTo"
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
          @cancel-load="onCancelLoadRemote"
          @save-bookmark="onSaveBookmark"
          @remove-bookmark="onRemoveBookmark"
          toolbar-layout="flat"
        />
      </div>
    </div>
    <!-- The panel bar is always visible; collapsing hides only the task list
         (the persisted flag now tracks "list expanded", default collapsed). -->
    <TransferPanel
      v-model:height="transferHeight"
      :collapsed="!settingsStore.sftpTransferPanelVisible"
      @update:collapsed="(v: boolean) => settingsStore.sftpTransferPanelVisible = !v"
      resizable
      :tasks="transferTasks"
      @cancel="onCancelTransfer"
      @pause="onPauseTransfer"
      @resume="onResumeTransfer"
      @retry="onRetryTransfer"
      @clearCompleted="clearFinishedTransfers"
    />

    <!-- Custom Dialog (shared) -->
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

    <!-- Change permission dialog (shared with the file sidebar) -->
    <FileChmodDialog
      v-model:visible="chmodVisible"
      :name="chmodItem?.name"
      :owner="chmodItem?.owner"
      :group="chmodItem?.group"
      :mode="chmodItem?.mode"
      @confirm="onChmodConfirm"
    />

    <!-- Editor Dialog (shared CodeMirror editor) -->
    <FileEditorDialog
      ref="fileEditorRef"
      v-model:visible="editorVisible"
      :session-id="panel?.sessionId"
      :mode="editorMode"
      @saved="onEditorSaved"
    />

    <!-- Conflict Dialog (shared) -->
    <FileConflictDialog
      v-model:visible="conflictVisible"
      :files="conflictFiles"
      @resolve="onConflictResolve"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, watch } from 'vue'

import { msg } from '../services/message'
import { usePanelStore } from '../stores/panelStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useLocalStateStore } from '../stores/localStateStore'
import { useI18n } from '../i18n'
import {
  SftpListRemote, SftpListLocal, SftpListLocalDrives,
  SftpChangeRemoteDir, SftpChangeLocalDir,
  SftpOpenExternalEditor, OpenExternalEditorLocal, ListSessions,
  SftpOpenWithSystem, OpenWithSystemLocal,
  S3CreateBucket, S3DeleteBucket, S3EntryCount,
} from '../../bindings/easyaiot/terminal/app'

import FileList from './FileList.vue'
import TransferPanel from './TransferPanel.vue'
import FileChmodDialog from './FileChmodDialog.vue'
import FileEditorDialog from './FileEditorDialog.vue'
import FileGenericDialog from './FileGenericDialog.vue'
import FileConflictDialog from './FileConflictDialog.vue'
import type { FileItem } from './FileList.vue'
import {
  useFilePanel, useConflictDialog, useFileDialogs, useFileListing, useChmodDialog,
  useEditorBridge, useNativeFileDrop, remoteFileOps, localFileOps, createSendToOther,
  resolveRemoteTarget, resolveLocalTarget, joinPath,
} from '../composables/useFilePanel'
import { reconnectFileTransferPanel, isPanelReconnecting } from '../composables/usePanelReconnect'
import { isConnectionLostError, supportsRemoteSymlink } from '../utils/fileTransferUtils'
import { bindExtEditUploadedToast } from '../composables/useFilePanel'
import { Events } from '@wailsio/runtime'
import { watchNewTransferTasks } from '../composables/useTransferTasks'
import { registerTransferRoute, unregisterTransferRoute } from '../services/transferTaskCenter'

const props = defineProps<{
  panelId: string
}>()

const panelStore = usePanelStore()
const settingsStore = useSettingsStore()
const localStateStore = useLocalStateStore()
const transferTasks = panelStore.getTransferTasks(props.panelId)
const transferHeight = ref(130)
const { t } = useI18n()
bindExtEditUploadedToast()
const panel = computed(() => panelStore.getPanel(props.panelId))
// "New link" exists only for backends with link semantics (SFTP/SCP/WSL).
const remoteSupportsSymlink = computed(() => supportsRemoteSymlink(panel.value?.config ?? undefined))
// Drives the remote pane's protocol-aware UI: for S3 the FileList hides POSIX
// columns and exposes bucket create/delete at the bucket list.
const remoteProtocol = computed(() => panel.value?.config?.type ?? '')
const isS3Panel = computed(() => remoteProtocol.value === 's3')
// S3 browsing rarely needs the local directory, so the local pane starts
// collapsed (persisted preference); other protocols keep it always visible.
const showLocalPane = computed(() => !isS3Panel.value || !!localStateStore.state.s3ShowLocalPane)
function onToggleLocalPane() {
  localStateStore.update({ s3ShowLocalPane: !showLocalPane.value })
}

const localDrives = ref<string[]>([])
const dragOverLocal = ref(false)
const dragOverRemote = ref(false)
const dragSource = ref<'local' | 'remote' | null>(null)
let dragEnterLocalCount = 0
let dragEnterRemoteCount = 0

// Unique id on this tab's remote-pane drop zone. Wails v3 forwards the id of the
// element a file was dropped on via common:WindowFilesDropped, and the file
// sidebar also acts as a drop target, so only keep drops that landed here.
const remoteDropId = (crypto.randomUUID?.() ||
  `sftp-remote-drop-${Date.now()}-${Math.random().toString(36).slice(2)}`)

// Editor dialog (shared FileEditorDialog with CodeMirror)
const editor = useEditorBridge({
  saved: () => (editorMode.value === 'local' ? onRefreshLocal('') : onRefreshRemote('')),
})
const { editorVisible, editorMode, fileEditorRef, onEditorSaved } = editor

// Change-permission dialog state (rendered by the shared FileChmodDialog).
const chmod = useChmodDialog({
  target: (item, ctx) => {
    const sid = panel.value?.sessionId
    if (!sid) return null
    const pane = (ctx as 'local' | 'remote' | undefined) ?? 'remote'
    const baseDir = pane === 'local' ? localCwd.value : cwd.value
    return { sid, path: joinPath(baseDir, item.name) }
  },
  refresh: () => onRefreshRemote(''),
})
const { chmodVisible, chmodItem, onChmod, onChmodConfirm } = chmod

// ── Shared per-panel logic (clipboard, dialogs, file ops) — one instance per pane ──
const conflicts = useConflictDialog()
const { conflictVisible, conflictFiles, onConflictResolve } = conflicts
const fileDialogs = useFileDialogs()
const { dlg: genDlg, onGenericConfirm, onGenericCancel } = fileDialogs

// ── Listing / navigation engine — one instance per pane ──
const remoteListing = useFileListing({
  sid: () => panel.value?.sessionId ?? undefined,
  list: SftpListRemote,
  changeDir: SftpChangeRemoteDir,
  resolveTarget: resolveRemoteTarget,
  onListError: onRemoteListError,
})
const localListing = useFileListing({
  sid: () => panel.value?.sessionId ?? undefined,
  list: SftpListLocal,
  changeDir: SftpChangeLocalDir,
  resolveTarget: resolveLocalTarget,
  // No initialDir: an empty dir lets the backend answer with its own localCwd,
  // which starts at the home directory. Passing '/' here used to override that
  // and open the pane at the filesystem root, several clicks from ~ (#947).
  afterList: async (dir) => {
    const sid = panel.value?.sessionId
    if (!sid || !/^[A-Za-z]:\\$/.test(dir)) return
    try {
      const drives = await SftpListLocalDrives(sid)
      localDrives.value = drives.map(d => d.name)
    } catch {}
  },
})
const {
  cwd, files: remoteFiles, loading: loadingRemote,
  onRefresh: onRefreshRemote, onNavigate: onRemoteNavigate, onCancelLoad: onCancelLoadRemote,
  canBack: remoteCanBack, canForward: remoteCanForward,
  onBack: onRemoteBack, onForward: onRemoteForward, onUp: onRemoteUp,
} = remoteListing

// ── S3 "files" column ────────────────────────────────────────────────────────
// Directory rows get their direct-entry count from the backend asynchronously
// (one delimited listing per row, cached server-side), so the listing itself
// stays fast. The generation counter discards results from a stale view after
// navigating away or refreshing.
const s3FileCounts = ref<Record<string, number | null>>({})
let s3CountGen = 0
watch([remoteFiles, cwd], ([files, dir]) => {
  if (!isS3Panel.value) return
  const gen = ++s3CountGen
  const sid = panel.value?.sessionId
  s3FileCounts.value = {}
  if (!sid || !files) return
  for (const f of files) {
    if (!f.isDir || f.name === '..') continue
    S3EntryCount(sid, joinPath(dir, f.name)).then((n: number) => {
      if (gen !== s3CountGen) return
      s3FileCounts.value = { ...s3FileCounts.value, [f.name]: n }
    }).catch(() => {
      if (gen !== s3CountGen) return
      s3FileCounts.value = { ...s3FileCounts.value, [f.name]: null }
    })
  }
})
const {
  cwd: localCwd, files: localFiles, loading: loadingLocal,
  onRefresh: onRefreshLocal, onNavigate: onLocalNavigate, onCancelLoad: onCancelLoadLocal,
  canBack: localCanBack, canForward: localCanForward,
  onBack: onLocalBack, onForward: onLocalForward, onUp: onLocalUp,
} = localListing

// Auto-reconnect when a remote listing/navigation hits a dead session (used to
// toast "connection lost" on every refresh with no way back except closing the
// tab). A disconnect is detected either from the error wording or from the
// session's own status; then the shared panel-reconnect flow (same one the tab
// right-click 「重连」 uses) brings up a fresh session and the listing reloads
// once. Returns true so the generic error toast is suppressed whenever we took
// over — including when the reconnect itself failed (it reports its own error).
async function onRemoteListError(err: string): Promise<boolean> {
  const panel = panelStore.getPanel(props.panelId)
  if (!panel?.config) return false
  let connected = false
  try {
    const sessions = await ListSessions()
    connected = sessions.find(s => s.id === panel.sessionId)?.status === 'connected'
  } catch { /* status unknown — treat as disconnected */ }
  if (connected && !isConnectionLostError(err)) return false
  if (!isPanelReconnecting(props.panelId)) {
    msg.warning(t('sftp.reconnecting'))
  }
  try {
    const newId = await reconnectFileTransferPanel(props.panelId)
    if (newId) onRefreshRemote()
    else msg.error(t('tab.reconnectFailed'))
  } catch (e: any) {
    msg.error(`${t('tab.reconnectFailed')}: ${e?.message || String(e)}`)
  }
  return true
}

const remotePanel = useFilePanel({
  sid: () => panel.value?.sessionId,
  cwd: remoteListing.cwd,
  files: remoteListing.files,
  refresh: () => onRefreshRemote(),
  ops: remoteFileOps,
  conflicts,
  dialogs: fileDialogs,
  transferTasks: () => transferTasks,
  openEditor: (path, title) => fileEditorRef.value?.open(path, title, 'remote') ?? Promise.resolve(),
  openExternal: (sid, path, cmd) => SftpOpenExternalEditor(sid, path, cmd),
  openWithSystem: (sid, path) => SftpOpenWithSystem(sid, path),
  bookmarkMode: 'remote',
  // Upload/download pickers open at the local pane's directory, so the two
  // halves of the tab stay in step.
  localCwd: () => localListing.cwd.value,
})
const localPanel = useFilePanel({
  sid: () => panel.value?.sessionId,
  cwd: localListing.cwd,
  files: localListing.files,
  refresh: () => onRefreshLocal(),
  ops: localFileOps,
  conflicts,
  dialogs: fileDialogs,
  transferTasks: () => transferTasks,
  openEditor: (path, title) => fileEditorRef.value?.open(path, title, 'local') ?? Promise.resolve(),
  openExternal: (_sid, path, cmd) => OpenExternalEditorLocal(path, cmd),
  openWithSystem: (_sid, path) => OpenWithSystemLocal(path),
  bookmarkMode: 'local',
})
const {
  clipboard, cutItemNames, clipboardCount, pasteLoading: pasteLoadingRemote,
  onCopyToClipboard, onCutToClipboard, onClearClipboard, onCancelPaste, onPaste,
  onRename, onDelete, onMkdir, onNewFile, onSymlink,
  onUpload, onDownloadTo,
  onEditFile, onEditExternal, onOpenWithSystem,
  onCancelTransfer, onPauseTransfer, onResumeTransfer, onRetryTransfer, clearFinishedTransfers,
  onSaveBookmark, onRemoveBookmark,
  uploadPaths,
} = remotePanel
const {
  clipboard: localClipboard, cutItemNames: localCutItemNames,
  clipboardCount: localClipboardCount, pasteLoading: pasteLoadingLocal,
  onCopyToClipboard: onLocalCopyToClipboard, onCutToClipboard: onLocalCutToClipboard,
  onClearClipboard: onLocalClearClipboard, onCancelPaste: onLocalCancelPaste,
  onPaste: onLocalPaste, onRename: onLocalRename, onDelete: onLocalDelete,
  onMkdir: onLocalMkdir, onNewFile: onLocalNewFile,
  onEditFile: onLocalEditFile, onEditExternal: onLocalEditExternal, onOpenWithSystem: onLocalOpenWithSystem,
  onSaveBookmark: onLocalSaveBookmark, onRemoveBookmark: onLocalRemoveBookmark,
} = localPanel

// ── S3 bucket management ─────────────────────────────────────────────────────
// At the bucket list ("/") the pane's create/delete actions are bucket-level:
// FileList swaps "new folder" for CreateBucket and bucket-row delete for
// DeleteBucket, and only emits these when protocol is 's3'.
async function onCreateBucket() {
  const sid = panel.value?.sessionId
  if (!sid) return
  const r = await fileDialogs.openGeneric({
    title: t('s3.createBucket'),
    placeholder: t('s3.bucketNamePlaceholder'),
  })
  if (!r.ok) return
  const name = r.value?.trim()
  if (!name) return
  try {
    await S3CreateBucket(sid, name)
    msg.success(t('s3.createBucketOk', { name }))
    onRefreshRemote('')
  } catch (e: any) {
    msg.error(`${t('s3.createBucket')}: ${e?.message || String(e)}`)
  }
}

async function onDeleteBucket(items: FileItem[]) {
  const sid = panel.value?.sessionId
  if (!sid || !items.length) return
  const names = items.map(i => i.name).filter(n => n && n !== '..')
  if (!names.length) return
  const r = await fileDialogs.openGeneric({
    type: 'message',
    title: t('s3.deleteBucket'),
    message: t('s3.deleteBucketConfirm', { names: names.join(', ') }),
  })
  if (!r.ok) return
  const failed: string[] = []
  for (const name of names) {
    try {
      await S3DeleteBucket(sid, name)
    } catch {
      failed.push(name)
    }
  }
  if (failed.length) msg.error(`${t('s3.deleteBucketFailed', { count: failed.length })}: ${failed.join(', ')}`)
  else msg.success(t('s3.deleteBucketOk'))
  onRefreshRemote('')
}

let unsubscribe: (() => void) | null = null
let unsubscribeStatus: (() => void) | null = null
let unsubscribeExt: (() => void) | null = null
let initialNavDone = false

// On disconnect/error nothing will ever complete the in-flight transfers, so
// mark them (and their running files) failed here — otherwise they would sit
// as "running" forever. Failed tasks become retryable in the transfer panel.
function markTransferTasksDisconnected() {
  for (const t of transferTasks) {
    if (t.status === 'running' || t.status === 'paused') {
      t.status = 'error'
      t.files.forEach(f => { if (f.status === 'running') f.status = 'failed' })
    }
  }
}

onMounted(async () => {
  unsubscribeStatus =Events.On('session:status', (ev) => { const payload: { id: string; status: string } = ev.data;
    if (payload.id === panel.value?.sessionId) {
      if (payload.status === 'connected') {
        onRefreshLocal()
        onRefreshRemote().then(() => doInitialAutoNav())
      } else if (payload.status === 'error') {
        markTransferTasksDisconnected()
        msg.error(t('sftp.connectError'))
      } else if (payload.status === 'disconnected') {
        markTransferTasksDisconnected()
      }
    }
   })

  unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data;
    if (payload.id !== panel.value?.sessionId) return
    // Connection failed messages from backend (SFTP/FTP async connect errors)
    const connMatch = payload.data.match(/\[Connection failed: ([^\]]+)\]/)
    if (connMatch) {
      msg.error(connMatch[1])
      return
    }
  })

  // External-editor status events from the backend (started / uploaded / closed)
  unsubscribeExt = Events.On('sftp:extedit', (ev) => {
    const payload = ev?.data as { sessionId?: string; path?: string; status?: string }
    if (!payload?.sessionId || payload.sessionId !== panel.value?.sessionId) return
    if (payload.status === 'uploaded') {
      onRefreshRemote()
    }
  })

  // Proactively check if session is already connected (race: event may have fired
  // before the listener registered). The initial load is resumed from the
  // sessionId watch when the panel binds its session id (S3 connects so fast that
  // 'connected' can fire before that binding).
  await probeConnectAndLoad()
})

watch(() => panel.value?.sessionId, async (newId, oldId) => {
  if (newId && !oldId) {
    fetchLocalDrives()
    await probeConnectAndLoad()
  }
}, { immediate: true })

// Transfer panel visibility: hidden by default; a NEW task id auto-pops it
// (a manual collapse only hides the panel until the next task starts). The
// persisted flag remembers the last visibility across restarts but never
// suppresses the auto-pop.
watchNewTransferTasks(
  () => transferTasks,
  () => { settingsStore.sftpTransferPanelVisible = true },
)

// Transfer events are routed app-level by transferTaskCenter keyed by
// session id, so this tab's list stays current while another tab is
// active. Re-connects re-route through this watch (the panel's session
// id changes); the done-refresh is suppressed once the tab is gone.
let transferRoutingDisposed = false
// Captured non-reactively so unmount cleanup works even after the panel is
// removed from panelStore (KeepAlive can defer onUnmounted until long after
// closeTab, when panel.value is already undefined).
let boundSessionId: string | null = null
watch(() => panel.value?.sessionId, (sid, oldSid) => {
  if (oldSid && oldSid !== sid) unregisterTransferRoute(oldSid)
  if (!sid) return
  registerTransferRoute(sid, props.panelId, (status, type) => {
    if (transferRoutingDisposed || status !== 'done') return
    if (type === 'download') onRefreshLocal()
    else onRefreshRemote()
  })
  boundSessionId = sid
}, { immediate: true })

// A fast-connecting session (e.g. S3) can emit session:status 'connected' before
// this panel binds its sessionId, so the connected-event handler and a mount-time
// probe that runs while sid is still undefined both miss it. Once we know the id,
// check whether the session is already up and, if so, run the initial load.
let probeRan = false
async function probeConnectAndLoad() {
  if (probeRan || initialNavDone) return
  const sid = panel.value?.sessionId
  if (!sid) return
  try {
    const sessions = await ListSessions()
    const sess = sessions.find(s => s.id === sid)
    if (sess && sess.status === 'connected') {
      probeRan = true
      onRefreshLocal()
      onRefreshRemote().then(() => doInitialAutoNav())
    }
  } catch { /* ignore */ }
}

onUnmounted(() => {
  transferRoutingDisposed = true
  const sid = boundSessionId
  if (sid) unregisterTransferRoute(sid)
  panelStore.removeTransferTasks(props.panelId)
  unsubscribe?.()
  unsubscribeStatus?.()
  unsubscribeExt?.()
  nativeDrop.unbind()
})

// With KeepAlive, only the active instance should listen for global document
// drag/drop events to avoid cached instances picking up drops from other tabs.
onActivated(() => {
  document.addEventListener('dragstart', onDragStart)
  document.addEventListener('dragend', clearDragState)
  // OS file drops (resource manager) are delivered by Wails via this event, routed
  // to the drop zone whose id matches, then uploaded by absolute local path.
  nativeDrop.bind()
})

onDeactivated(() => {
  document.removeEventListener('dragstart', onDragStart)
  document.removeEventListener('dragend', clearDragState)
  nativeDrop.unbind()
})

async function fetchLocalDrives() {
  const sid = panel.value?.sessionId
  if (!sid) return
  try {
    const drives = await SftpListLocalDrives(sid)
    localDrives.value = drives.map(d => d.name)
  } catch {}
}

// Auto-navigate into the configured share/bucket on initial load.
async function doInitialAutoNav() {
  if (initialNavDone) return
  initialNavDone = true
  const cfg = panel.value?.config
  if (!cfg) return
  let target = ''
  if (cfg.type === 'smb' && cfg.smbShare) {
    target = '/' + cfg.smbShare
  } else if (cfg.type === 's3' && cfg.s3Bucket) {
    target = '/' + cfg.s3Bucket
  }
  if (target) {
    await onRemoteNavigate(target)
  }
}

// Send-to-other (context menu) and cross-pane drag-drop share one transfer
// implementation per direction (see createSendToOther): the source pane
// provides the files, the target pane receives them.
const onSendToRemote = createSendToOther({
  sid: () => panel.value?.sessionId ?? undefined,
  direction: 'toRemote',
  sourceCwd: localListing.cwd,
  targetCwd: remoteListing.cwd,
  targetFiles: remoteListing.files,
  conflicts,
  ops: remoteFileOps,
})
const onSendToLocal = createSendToOther({
  sid: () => panel.value?.sessionId ?? undefined,
  direction: 'toLocal',
  sourceCwd: remoteListing.cwd,
  targetCwd: localListing.cwd,
  targetFiles: localListing.files,
  conflicts,
  ops: localFileOps,
})

// OS file drops (resource manager / desktop) arrive via Wails v3's native pipe.
// Wails forwards the absolute local paths, which we upload directly from disk
// via SftpPut — memory-bounded and recursive for folders — instead of reading
// the file content into the webview and base64-ing it (which crashed on very
// large files; issue #699).
const nativeDrop = useNativeFileDrop({
  elementId: remoteDropId,
  isActive: () => !!panel.value?.sessionId,
  upload: (paths) => uploadPaths(paths),
})

function onDragOver(e: DragEvent) {
  if (dragSource.value === null) {
    e.dataTransfer!.dropEffect = 'copy'
  } else {
    e.dataTransfer!.dropEffect = 'move'
  }
}

function onDragStart(e: DragEvent) {
  const target = e.target as HTMLElement | null
  if (target?.closest('.local-pane')) {
    dragSource.value = 'local'
  } else if (target?.closest('.remote-pane')) {
    dragSource.value = 'remote'
  }
}

function onDragEnter(mode: 'local' | 'remote') {
  // Internal drag: skip overlay on source pane
  if (dragSource.value !== null && dragSource.value === mode) return
  // External drag (from desktop): only show overlay on remote pane
  if (dragSource.value === null && mode === 'local') return
  if (mode === 'local') {
    dragEnterLocalCount++
    dragOverLocal.value = true
  } else {
    dragEnterRemoteCount++
    dragOverRemote.value = true
  }
}

function onDragLeave(mode: 'local' | 'remote') {
  if (mode === 'local') {
    dragEnterLocalCount--
    if (dragEnterLocalCount <= 0) {
      dragEnterLocalCount = 0
      dragOverLocal.value = false
    }
  } else {
    dragEnterRemoteCount--
    if (dragEnterRemoteCount <= 0) {
      dragEnterRemoteCount = 0
      dragOverRemote.value = false
    }
  }
}

function clearDragState() {
  dragOverLocal.value = false
  dragOverRemote.value = false
  dragEnterLocalCount = 0
  dragEnterRemoteCount = 0
  dragSource.value = null
}

async function onDropLocal(e: DragEvent) {
  e.preventDefault()
  clearDragState()
  const data = e.dataTransfer?.getData('application/sftp-file')
  if (!data) return
  try {
    const parsed = JSON.parse(data)
    const items: FileItem[] = parsed.items ? parsed.items : (parsed.name ? [{ name: parsed.name, isDir: !!parsed.isDir }] : [])
    if (items.length === 0 || parsed.mode !== 'remote') return
    await onSendToLocal(items)
  } catch (e) { console.error('onDropLocal:', e) }
}

async function onDropRemote(e: DragEvent) {
  e.preventDefault()
  clearDragState()

  // OS file drops (resource manager) are handled natively via
  // common:WindowFilesDropped (onNativeFileDrop) so we upload by absolute path;
  // skip the HTML5 content path that base64-escapes whole files into memory.
  const dt = e.dataTransfer
  const hasFileItems = !!(dt && dt.items && [...dt.items].some(it => it.kind === 'file'))
  const hasRawFiles = !!(dt && dt.files && dt.files.length > 0)
  if (hasFileItems || hasRawFiles) return

  // Internal SFTP file drag
  const data = e.dataTransfer?.getData('application/sftp-file')
  if (!data) return
  try {
    const parsed = JSON.parse(data)
    const items: FileItem[] = parsed.items ? parsed.items : (parsed.name ? [{ name: parsed.name, isDir: !!parsed.isDir }] : [])
    if (items.length === 0 || parsed.mode !== 'local') return
    await onSendToRemote(items)
  } catch (e) { console.error('onDropRemote:', e) }
}
</script>

<style scoped>
.sftp-tab-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.panes-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.local-pane, .remote-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--border-subtle);
  position: relative;
}
.remote-pane {
  border-right: none;
}
.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--scrim);
  pointer-events: none;
}
.drop-overlay span {
  font-size: 0.875rem;
  color: var(--text-primary);
  padding: 0.75rem 1.5rem;
  border: 0.125rem dashed var(--border-hover);
  border-radius: var(--radius-md);
}

</style>
