import { ref, reactive, computed } from 'vue'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import {
  SftpCopy, SftpMove, SftpRename, SftpRemove, SftpMakeDir, SftpPutContent,
  SftpPut, SftpGet, SftpChmod, SftpSymlink,
  SftpLocalCopy, SftpLocalMove, SftpLocalRename, SftpLocalRemove, SftpLocalMkdir, SftpLocalPutContent,
  SftpCancelTransfer, SftpPauseTransfer, SftpResumeTransfer,
  SftpRetryTransfer, SftpDismissTransfer, SftpListLocal,
  OpenMultipleFilesDialog, OpenDirectoryDialog,
} from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import { useLocalStateStore } from '../stores/localStateStore'
import { useSettingsStore } from '../stores/settingsStore'
import { t as i18nT } from '../i18n'
import { buildSkipList } from './useTransferTasks'
import type { TransferTaskUI } from '../stores/panelStore'

// --- Global external-edit toast ---------------------------------------------
// The "uploaded" event is broadcast app-wide while the file sidebar AND the
// SFTP tab listeners may both be mounted for the same session; toasting per
// component duplicates the message. One app-level listener owns the toast,
// the per-component listeners only refresh their listing.
let extEditToastBound = false
export function bindExtEditUploadedToast() {
  if (extEditToastBound) return
  extEditToastBound = true
  Events.On('sftp:extedit', (ev) => {
    const payload = ev?.data as { path?: string; status?: string }
    if (payload?.status === 'uploaded') {
      msg.success(i18nT('sftp.editExternalUploaded', { path: payload.path || '' }))
    }
  })
}
import type { FileItem } from '../components/FileList.vue'

/** Max file size accepted by the in-app / external editor flows. */
export const EDIT_FILE_MAX_SIZE = 1024 * 1024

const REMOVE_TIMEOUT_MS = 60000

// --- Shared path helpers ---------------------------------------------------

export function joinPath(base: string, name: string): string {
  if (base.endsWith('/') || base.endsWith('\\')) return base + name
  return base + '/' + name
}

export function autoRename(targetName: string, existingNames: string[]): string {
  if (!existingNames.includes(targetName)) return targetName
  const dotIdx = targetName.lastIndexOf('.')
  const base = dotIdx > 0 ? targetName.slice(0, dotIdx) : targetName
  const ext = dotIdx > 0 ? targetName.slice(dotIdx) : ''
  let n = 1
  let candidate: string
  do {
    candidate = `${base} (${n})${ext}`
    n++
  } while (existingNames.includes(candidate))
  return candidate
}

export function isPathInside(child: string, parent: string): boolean {
  const c = child.endsWith('/') ? child : child + '/'
  const p = parent.endsWith('/') ? parent : parent + '/'
  return c.startsWith(p)
}

export function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`${label} timeout`)), ms)
    promise.then(
      (v) => { clearTimeout(timer); resolve(v) },
      (e) => { clearTimeout(timer); reject(e) },
    )
  })
}

// --- Conflict dialog (shared instance per host component) ------------------

export function useConflictDialog() {
  const conflictVisible = ref(false)
  const conflictFiles = ref<string[]>([])
  let conflictResolve: ((a: 'overwrite' | 'rename' | 'cancel') => void) | null = null

  function showConflictDialog(conflicts: string[]): Promise<'overwrite' | 'rename' | 'cancel'> {
    return new Promise((resolve) => {
      conflictFiles.value = conflicts
      conflictResolve = resolve
      conflictVisible.value = true
    })
  }

  function onConflictResolve(action: 'overwrite' | 'rename' | 'cancel') {
    conflictVisible.value = false
    if (conflictResolve) { conflictResolve(action); conflictResolve = null }
  }

  /** Prompt only when fileNames clash with existingNames. */
  async function resolveConflicts(
    fileNames: string[],
    existingNames: string[],
  ): Promise<'overwrite' | 'rename' | 'cancel'> {
    const conflicts = fileNames.filter(n => existingNames.includes(n))
    if (!conflicts.length) return 'overwrite'
    return showConflictDialog(conflicts)
  }

  return { conflictVisible, conflictFiles, showConflictDialog, onConflictResolve, resolveConflicts }
}

export type ConflictDialog = ReturnType<typeof useConflictDialog>

// --- Generic input/message dialog (shared instance per host component) -----

export function useFileDialogs() {
  const dlg = reactive<{
    visible: boolean
    type: 'input' | 'message'
    title: string
    inputValue: string
    placeholder: string
    // Optional second input row (e.g. the target path of "new link"); the
    // second el-input is rendered only when input2Placeholder is non-empty.
    inputValue2: string
    input2Placeholder: string
    message: string
    resolve: ((r: { ok: boolean; value?: string; value2?: string }) => void) | null
  }>({ visible: false, type: 'input', title: '', inputValue: '', placeholder: '', inputValue2: '', input2Placeholder: '', message: '', resolve: null })

  function openGeneric(opts: {
    type?: 'input' | 'message'
    title: string
    inputValue?: string
    placeholder?: string
    inputValue2?: string
    input2Placeholder?: string
    message?: string
  }): Promise<{ ok: boolean; value?: string; value2?: string }> {
    return new Promise((resolve) => {
      dlg.type = opts.type || 'input'
      dlg.title = opts.title
      dlg.inputValue = opts.inputValue || ''
      dlg.placeholder = opts.placeholder || ''
      dlg.inputValue2 = opts.inputValue2 || ''
      dlg.input2Placeholder = opts.input2Placeholder || ''
      dlg.message = opts.message || ''
      dlg.resolve = resolve
      dlg.visible = true
    })
  }

  function onGenericConfirm() {
    const value = dlg.inputValue
    const value2 = dlg.inputValue2
    const resolve = dlg.resolve
    dlg.visible = false
    dlg.resolve = null
    resolve?.({ ok: true, value, value2 })
  }

  function onGenericCancel() {
    const resolve = dlg.resolve
    dlg.visible = false
    dlg.resolve = null
    resolve?.({ ok: false })
  }

  return { dlg, openGeneric, onGenericConfirm, onGenericCancel }
}

export type FileDialogs = ReturnType<typeof useFileDialogs>

// --- Per-panel file operations ---------------------------------------------

/** Backend operations for one panel. Remote panels use the Sftp* bindings,
 *  the SFTP tab's local pane uses the SftpLocal* ones. */
export interface FilePanelOps {
  copy: (sid: string, src: string, dst: string) => Promise<unknown>
  move: (sid: string, src: string, dst: string) => Promise<unknown>
  rename: (sid: string, src: string, dst: string) => Promise<unknown>
  remove: (sid: string, path: string, isDir: boolean) => Promise<unknown>
  makeDir: (sid: string, path: string) => Promise<unknown>
  /** Remote panels only: create a symbolic link. Local panes never set it. */
  symlink?: (sid: string, target: string, linkPath: string) => Promise<unknown>
  putContent: (sid: string, path: string, content: string) => Promise<unknown>
  put: (sid: string, localPath: string, targetPath: string, recursive: boolean) => Promise<unknown>
  get: (sid: string, remotePath: string, localPath: string, isDir: boolean) => Promise<unknown>
  chmod: (sid: string, path: string, octal: string) => Promise<unknown>
}

export const remoteFileOps: FilePanelOps = {
  copy: SftpCopy,
  move: SftpMove,
  rename: SftpRename,
  remove: SftpRemove,
  makeDir: SftpMakeDir,
  symlink: SftpSymlink,
  putContent: (sid, path, content) => SftpPutContent(sid, path, content, 'utf-8'),
  put: SftpPut,
  get: SftpGet,
  chmod: SftpChmod,
}

export const localFileOps: FilePanelOps = {
  copy: SftpLocalCopy,
  move: SftpLocalMove,
  rename: SftpLocalRename,
  remove: SftpLocalRemove,
  makeDir: SftpLocalMkdir,
  putContent: SftpLocalPutContent,
  // The local pane never uses upload/download buttons; placeholders keep the
  // interface satisfied.
  put: SftpPut,
  get: SftpGet,
  chmod: SftpChmod,
}

// --- Unified "send to the other pane" ---------------------------------------

/** Creates the shared "send these items to the other pane" handler used by
 *  both the context-menu action and the cross-pane drag-drop. Filters '..',
 *  prompts once per batch for name conflicts, auto-renames on 'rename' (with
 *  a growing existing-names list), then fires each transfer without awaiting
 *  it — completion refreshes go through the transferEvents onDone hook.
 *
 *  Role of the cwds: the source pane provides the files (its cwd builds the
 *  remote/source path with the item's original name), the target pane
 *  receives them (its cwd builds the destination path with the resolved
 *  name). 'toRemote' uploads local → remote, 'toLocal' downloads remote →
 *  local. */
export function createSendToOther(opts: {
  sid: () => string | undefined
  direction: 'toRemote' | 'toLocal'
  sourceCwd: { value: string }
  targetCwd: { value: string }
  targetFiles: { value: FileItem[] }
  conflicts: ConflictDialog
  ops: FilePanelOps
}): (items: FileItem[]) => Promise<void> {
  return async (items: FileItem[]) => {
    const id = opts.sid()
    if (!id) return

    const fileNames = items.filter(i => i.name !== '..').map(i => i.name)
    const action = await opts.conflicts.resolveConflicts(
      fileNames,
      opts.targetFiles.value.map(f => f.name),
    )
    if (action === 'cancel') return

    const existingNames = opts.targetFiles.value.map(f => f.name)
    for (const item of items) {
      if (item.name === '..') continue
      let resolvedName = item.name
      if (action === 'rename' && existingNames.includes(item.name)) {
        resolvedName = autoRename(item.name, existingNames)
      }
      existingNames.push(resolvedName)
      if (opts.direction === 'toRemote') {
        opts.ops.put(
          id,
          joinPath(opts.sourceCwd.value, item.name),
          opts.targetCwd.value + '/' + resolvedName,
          item.isDir,
        )
      } else {
        opts.ops.get(
          id,
          joinPath(opts.sourceCwd.value, item.name),
          joinPath(opts.targetCwd.value, resolvedName).replace(/\\/g, '/'),
          item.isDir,
        )
      }
    }
  }
}

// --- The panel composable ---------------------------------------------------

export interface FilePanelOptions {
  /** Backend session id used by every file operation. */
  sid: () => string | undefined
  /** Current directory and current listing of THIS panel. */
  cwd: { value: string }
  files: { value: FileItem[] }
  /** Post-operation refresh; optional delay in ms (delete uses ~300). */
  refresh: (delay?: number) => void
  ops: FilePanelOps
  conflicts: ConflictDialog
  dialogs: FileDialogs
  /** Transfer tasks of the owning view (for cancel-on-delete + clear). */
  transferTasks: () => TransferTaskUI[]
  /** Open the shared code editor on a path (mode is the host's choice). */
  openEditor?: (path: string, title: string) => Promise<void>
  /** Launch the external editor; remote panels upload on save, local edits in place. */
  openExternal?: (sid: string, path: string, editorCmd: string) => Promise<unknown>
  /** Open via the OS "open with" flow (system picker on Windows, default handler elsewhere). */
  openWithSystem?: (sid: string, path: string) => Promise<unknown>
  /** Which bookmark list this panel's paths belong to. */
  bookmarkMode: 'local' | 'remote'
  /** Local directory the upload/download pickers should open at. Defaults to
   *  the home directory when omitted or when the path no longer exists. */
  localCwd?: () => string | undefined
}

export function useFilePanel(opts: FilePanelOptions) {
  const { t } = useI18n()
  const { sid, cwd, files, refresh, ops, conflicts, dialogs, transferTasks } = opts
  const { openGeneric } = dialogs
  const localStateStore = useLocalStateStore()
  const settingsStore = useSettingsStore()

  // --- Remote clipboard (copy / cut / paste) ---

  interface Clipboard {
    items: string[]
    sourceDir: string
    mode: 'copy' | 'cut'
  }
  const clipboard = ref<Clipboard | null>(null)
  const cutItemNames = computed(() =>
    clipboard.value?.mode === 'cut' ? clipboard.value.items : []
  )
  const clipboardCount = computed(() => clipboard.value?.items.length ?? 0)
  const pasteLoading = ref(false)
  let pasteCancelled = false

  function onCopyToClipboard(items: FileItem[]) {
    clipboard.value = { items: items.map(i => i.name), sourceDir: cwd.value, mode: 'copy' }
    msg.success(t('sftp.copy'))
  }

  function onCutToClipboard(items: FileItem[]) {
    clipboard.value = { items: items.map(i => i.name), sourceDir: cwd.value, mode: 'cut' }
    msg.success(t('sftp.cut'))
  }

  function onClearClipboard() {
    clipboard.value = null
  }

  function onCancelPaste() {
    pasteCancelled = true
    pasteLoading.value = false
  }

  async function onPaste() {
    const id = sid()
    if (!id || !clipboard.value) return
    const { items, sourceDir, mode } = clipboard.value
    pasteCancelled = false
    pasteLoading.value = true
    const targetDir = cwd.value

    // Cut to same directory: error immediately, no conflict dialog
    if (mode === 'cut' && sourceDir === targetDir) {
      msg.warning(t('sftp.paste.cutSameDir'))
      pasteLoading.value = false
      return
    }

    const existingNames = files.value.map(f => f.name)
    const clashes = items.filter(name => existingNames.includes(name))
    let resolveAction: 'overwrite' | 'rename' | 'cancel' = 'rename'
    if (clashes.length > 0) {
      resolveAction = await conflicts.showConflictDialog(clashes)
      if (resolveAction === 'cancel') { pasteLoading.value = false; return }
    }

    let success = 0
    const failed: string[] = []

    for (const name of items) {
      if (pasteCancelled) break
      const source = joinPath(sourceDir, name)
      const target = joinPath(targetDir, name)
      if (source !== target && isPathInside(target, source)) {
        msg.warning(t('sftp.paste.circularWarning'))
        continue
      }
      // Copy into the same directory always auto-renames; cut is blocked above.
      const forceRename = source === target && mode === 'copy'
      let resolvedName = name
      if (forceRename || (resolveAction === 'rename' && existingNames.includes(name))) {
        resolvedName = autoRename(name, existingNames)
      }
      const resolvedTarget = joinPath(targetDir, resolvedName)
      existingNames.push(resolvedName)
      try {
        if (mode === 'copy') {
          await ops.copy(id, source, resolvedTarget)
        } else {
          await ops.move(id, source, resolvedTarget)
        }
        success++
      } catch (e: any) {
        failed.push(name + ': ' + (e?.toString() || 'unknown'))
      }
    }

    pasteLoading.value = false

    if (pasteCancelled) {
      // keep clipboard so user can retry
    } else if (failed.length > 0) {
      msg.error(`Copied/Moved ${success}/${items.length}, ${failed.length} failed`)
    } else {
      msg.success(t('sftp.paste'))
    }

    if (!pasteCancelled) clipboard.value = null
    refresh()
  }

  // --- Rename / delete / mkdir / new file (promise-based generic dialog) ---

  async function onRename(item: FileItem) {
    const id = sid()
    if (!id) return
    const r = await openGeneric({
      title: t('sftp.dialog.renameTitle'),
      inputValue: item.name,
      placeholder: t('sftp.dialog.renamePrompt', { name: item.name }),
    })
    if (!r.ok || !r.value || r.value === item.name) return
    try {
      await ops.rename(id, joinPath(cwd.value, item.name), joinPath(cwd.value, r.value))
      refresh()
    } catch (e) { console.error('rename:', e) }
  }

  async function onDelete(items: FileItem[]) {
    const id = sid()
    if (!id) return
    const targets = items.filter(i => i.name !== '..')
    if (!targets.length) return
    const hasDir = targets.some(i => i.isDir)
    const hasFile = targets.some(i => !i.isDir)
    let confirmMsg: string
    if (hasDir && hasFile) {
      confirmMsg = t('sftp.dialog.deleteConfirmMixed', { count: targets.length })
    } else if (hasDir) {
      confirmMsg = t('sftp.dialog.deleteConfirmDir', { count: targets.length })
    } else {
      confirmMsg = t('sftp.dialog.deleteConfirmFile', { count: targets.length })
    }
    const r = await openGeneric({ type: 'message', title: t('sftp.dialog.deleteTitle'), message: confirmMsg })
    if (!r.ok) return

    const names = new Set(targets.map(i => i.name))
    // Stop any in-flight upload/download of these files first — otherwise
    // remove can block forever while the transfer holds the handle.
    for (const task of [...transferTasks()]) {
      if ((task.status === 'running' || task.status === 'paused') && names.has(task.name)) {
        try { await SftpCancelTransfer(id, task.id) } catch { /* ignore */ }
        task.status = 'cancelled'
      }
    }

    // Optimistic UI — remove from list immediately so delete never "looks stuck"
    files.value = files.value.filter(f => !names.has(f.name))

    for (const item of targets) {
      try {
        await withTimeout(
          Promise.resolve(ops.remove(id, joinPath(cwd.value, item.name), item.isDir)),
          REMOVE_TIMEOUT_MS,
          'remove',
        )
      } catch (e: any) {
        const err = e?.toString?.() || String(e)
        // File may already be gone — ignore not-found; otherwise put back & report
        if (!/no such file|not found|no such file or directory|timeout/i.test(err)) {
          msg.error(err)
          if (!files.value.some(f => f.name === item.name)) {
            files.value = [...files.value, item]
          }
        } else if (/timeout/i.test(err)) {
          // Likely deleted on server but reply stalled — keep optimistic removal
          msg.warning(t('companion.deleteTimeout'))
        }
      }
    }
    refresh(300)
  }

  async function onMkdir() {
    const id = sid()
    if (!id) return
    const r = await openGeneric({ title: t('sftp.dialog.mkdirTitle'), placeholder: t('sftp.dialog.mkdirPrompt') })
    if (!r.ok || !r.value) return
    try {
      await ops.makeDir(id, joinPath(cwd.value, r.value))
      refresh()
    } catch (e) { console.error('mkdir:', e) }
  }

  async function onNewFile() {
    const id = sid()
    if (!id) return
    const r = await openGeneric({ title: t('sftp.newFile'), inputValue: 'newfile.txt' })
    if (!r.ok || !r.value) return
    const name = r.value.trim()
    if (!name) { msg.warning(t('sftp.dialog.newFileEmpty')); return }
    if (name.includes('/') || name.includes('\\')) { msg.warning(t('sftp.dialog.newFileInvalid')); return }
    const finalName = autoRename(name, files.value.map(f => f.name))
    try {
      await ops.putContent(id, joinPath(cwd.value, finalName), '')
      msg.success(t('sftp.dialog.confirm'))
      refresh()
    } catch (e: any) {
      msg.error(e?.toString() || 'Failed to create file')
    }
  }

  // Creates a symbolic link pointing at the entered target. The target is
  // stored verbatim, so relative targets resolve against the link's own
  // directory (per symlink semantics). Panels of protocols without link
  // semantics hide the menu entry and never get here.
  async function onSymlink() {
    const id = sid()
    if (!id) return
    const r = await openGeneric({
      title: t('sftp.dialog.symlinkTitle'),
      placeholder: t('sftp.dialog.symlinkName'),
      input2Placeholder: t('sftp.dialog.symlinkTarget'),
    })
    if (!r.ok || !r.value) return
    const name = r.value.trim()
    const target = (r.value2 || '').trim()
    if (!name) { msg.warning(t('sftp.dialog.newFileEmpty')); return }
    if (name.includes('/') || name.includes('\\')) { msg.warning(t('sftp.dialog.newFileInvalid')); return }
    if (!target) { msg.warning(t('sftp.dialog.symlinkTargetEmpty')); return }
    try {
      await ops.symlink?.(id, target, joinPath(cwd.value, name))
      msg.success(t('sftp.dialog.confirm'))
      refresh()
    } catch (e: any) {
      msg.error(e?.toString() || 'Failed to create link')
    }
  }

  // --- Upload / download ----------------------------------------------------

  async function onUpload() {
    const id = sid()
    if (!id) return
    try {
      const localPaths = await OpenMultipleFilesDialog(opts.localCwd?.() || '')
      if (!localPaths?.length) return
      const names = localPaths.map(fp => fp.replace(/\\/g, '/').split('/').pop() || 'upload')
      const action = await conflicts.resolveConflicts(names, files.value.map(f => f.name))
      if (action === 'cancel') return
      const existing = files.value.map(f => f.name)
      for (let i = 0; i < localPaths.length; i++) {
        let name = names[i]
        if (action === 'rename' && existing.includes(name)) {
          name = autoRename(name, existing)
        }
        existing.push(name)
        // false = single file; backend auto-upgrades to recursive for directories
        ops.put(id, localPaths[i], joinPath(cwd.value, name), false)
      }
    } catch (e) {
      console.error('upload:', e)
    }
  }

  async function onDownloadTo(items: FileItem[]) {
    const id = sid()
    if (!id) return
    try {
      const dir = await OpenDirectoryDialog(opts.localCwd?.() || '')
      if (!dir) return

      const fileNames = items.filter(i => i.name !== '..').map(i => i.name)
      // Conflict check against the selected directory (may differ from cwd).
      let targetNames: string[] = []
      try {
        const result = await SftpListLocal(id, dir)
        targetNames = result.files.map(f => f.name)
      } catch { /* if listing fails, proceed without conflict prompting */ }
      const clashes = fileNames.filter(n => targetNames.includes(n))
      let action: 'overwrite' | 'rename' | 'cancel' = 'overwrite'
      if (clashes.length > 0) {
        action = await conflicts.showConflictDialog(clashes)
        if (action === 'cancel') return
      }
      const existingNames = [...targetNames]
      for (const item of items) {
        if (item.name === '..') continue
        let resolvedName = item.name
        if (action === 'rename' && existingNames.includes(item.name)) {
          resolvedName = autoRename(item.name, existingNames)
        }
        existingNames.push(resolvedName)
        const remotePath = joinPath(cwd.value, item.name)
        const localPath = (dir + '/' + resolvedName).replace(/\\/g, '/')
        ops.get(id, remotePath, localPath, item.isDir)
      }
    } catch (e) {
      console.error('downloadTo:', e)
    }
  }

  // --- Editors ---------------------------------------------------------------

  async function onEditFile(item: FileItem) {
    if (item.isDir) return
    if (item.size > EDIT_FILE_MAX_SIZE) {
      msg.warning(t('sftp.edit.fileTooLarge'))
      return
    }
    const id = sid()
    if (!id) return
    const path = joinPath(cwd.value, item.name)
    await opts.openEditor?.(path, t('sftp.dialog.editTitle', { path }))
  }

  async function onEditExternal(item: FileItem) {
    if (item.isDir) return
    if (item.size > EDIT_FILE_MAX_SIZE) {
      msg.warning(t('sftp.edit.fileTooLarge'))
      return
    }
    const id = sid()
    if (!id) return
    const editorCmd = localStateStore.state.externalEditor?.trim()
    if (!editorCmd) {
      msg.warning(t('sftp.editExternalNotConfigured'))
      return
    }
    const path = joinPath(cwd.value, item.name)
    try {
      await opts.openExternal?.(id, path, editorCmd)
      msg.info(t('sftp.editExternalStart', { path }))
    } catch (e: any) {
      msg.error(e?.toString() || 'Failed to open external editor')
    }
  }

  // Opens via the OS "open with" flow (Windows pops the association picker).
  // No editor binding required: like onEditExternal this shares the extedit
  // pipeline, so saves made in the picked application auto-upload to remote.
  async function onOpenWithSystem(item: FileItem) {
    if (item.isDir) return
    if (item.size > EDIT_FILE_MAX_SIZE) {
      msg.warning(t('sftp.edit.fileTooLarge'))
      return
    }
    const id = sid()
    if (!id) return
    const path = joinPath(cwd.value, item.name)
    try {
      await opts.openWithSystem?.(id, path)
      msg.info(t('sftp.openWithSystemStart', { path }))
    } catch (e: any) {
      msg.error(e?.toString() || 'Failed to open with system')
    }
  }

  // --- Transfer panel actions -------------------------------------------------

  async function onCancelTransfer(taskId: string) {
    const id = sid()
    if (!id) return
    try { await SftpCancelTransfer(id, taskId) } catch (e) { console.error('cancel transfer:', e) }
  }

  async function onPauseTransfer(taskId: string) {
    const id = sid()
    if (!id) return
    try { await SftpPauseTransfer(id, taskId) } catch (e) { console.error('pause transfer:', e) }
  }

  async function onResumeTransfer(taskId: string) {
    const id = sid()
    if (!id) return
    try { await SftpResumeTransfer(id, taskId) } catch (e) { console.error('resume transfer:', e) }
  }

  // Re-runs a failed transfer. The task stores the original full paths from the
  // backend's start payload; completed files (per the per-file tracker) are
  // skipped on the backend via the skip list.
  async function onRetryTransfer(task: TransferTaskUI) {
    const id = sid()
    if (!id) return
    const spec = {
      type: task.type,
      localPath: task.localPath,
      remotePath: task.remotePath,
      // Directory tasks carry per-file state; single files retry as-is.
      recursive: task.fileCount > 0,
    }
    try {
      await SftpRetryTransfer(id, spec, buildSkipList(task))
    } catch (e) {
      console.error('retry transfer:', e)
    }
  }

  /** Drops a retained (failed) task from the backend's transfer registry. */
  function onDismissTask(taskId: string) {
    const id = sid()
    if (!id) return
    SftpDismissTransfer(id, taskId).catch(() => {})
  }

  function clearFinishedTransfers() {
    const tasks = transferTasks()
    for (let i = tasks.length - 1; i >= 0; i--) {
      const st = tasks[i].status
      if (st === 'done' || st === 'error' || st === 'cancelled') {
        // The backend only retains failed tasks; tell it to drop each one
        // before the UI forgets the task id.
        if (st === 'error') onDismissTask(tasks[i].id)
        tasks.splice(i, 1)
      }
    }
  }

  // --- Drag-drop upload (native OS paths) -----------------------------------

  /** Upload absolute local paths (native drop / file dialog) into cwd. */
  async function uploadPaths(localPaths: string[]) {
    const id = sid()
    if (!id || !localPaths.length) return
    const names = localPaths.map(fp => fp.replace(/\\/g, '/').replace(/\/$/, '').split('/').pop() || 'upload')
    const action = await conflicts.resolveConflicts(names, files.value.map(f => f.name))
    if (action === 'cancel') return
    const existing = files.value.map(f => f.name)
    for (let i = 0; i < localPaths.length; i++) {
      let name = names[i]
      if (action === 'rename' && existing.includes(name)) {
        name = autoRename(name, existing)
      }
      existing.push(name)
      // false = single file; backend auto-upgrades to recursive for directories
      ops.put(id, localPaths[i], joinPath(cwd.value, name), false)
    }
  }

  // --- Bookmarks ---

  function onSaveBookmark(path: string) {
    settingsStore.addSftpBookmark(opts.bookmarkMode, path)
  }

  function onRemoveBookmark(path: string) {
    settingsStore.removeSftpBookmark(opts.bookmarkMode, path)
  }

  return {
    // clipboard
    clipboard, cutItemNames, clipboardCount, pasteLoading,
    onCopyToClipboard, onCutToClipboard, onClearClipboard, onCancelPaste, onPaste,
    // file actions
    onRename, onDelete, onMkdir, onNewFile, onSymlink,
    onUpload, onDownloadTo,
    onEditFile, onEditExternal, onOpenWithSystem,
    // transfer panel
    onCancelTransfer, onPauseTransfer, onResumeTransfer,
    onRetryTransfer, onDismissTask, clearFinishedTransfers,
    // bookmarks
    onSaveBookmark, onRemoveBookmark,
    // drag-drop upload
    uploadPaths,
  }
}

// --- Listing / navigation engine --------------------------------------------

export interface ListingResult { files: FileItem[]; dir: string }

/** Resolves '..' and relative names against a POSIX-style cwd (remote panels). */
export function resolveRemoteTarget(cwd: string, path: string): string {
  if (path === '..') return '/' + cwd.split('/').filter(Boolean).slice(0, -1).join('/')
  if (!path.startsWith('/')) return joinPath(cwd, path)
  return path
}

/** Resolves '..' and relative names against a Windows-aware local cwd. */
export function resolveLocalTarget(cwd: string, path: string): string {
  if (path === '..') {
    const parts = cwd.replace(/\\/g, '/').split('/').filter(Boolean)
    parts.pop()
    if (parts.length === 0) return cwd
    if (/^[A-Za-z]:$/.test(parts[0])) return parts[0] + '\\' + parts.slice(1).join('\\')
    return '/' + parts.join('/')
  }
  if (!path.startsWith('/') && !/^[A-Za-z]:/.test(path)) return joinPath(cwd, path)
  return path
}

export function useFileListing(opts: {
  sid: () => string | undefined
  list: (sid: string, dir: string) => Promise<ListingResult>
  changeDir: (sid: string, dir: string) => Promise<ListingResult>
  resolveTarget: (cwd: string, path: string) => string
  initialDir?: string
  listTimeoutMs?: number
  /** Called after a successful list (e.g. drive-letter refresh). */
  afterList?: (dir: string) => Promise<void> | void
  /** Return true when the error was fully handled (no generic toast). May be
   *  async (e.g. an auto-reconnect that decides after a status check). */
  onListError?: (err: string) => boolean | void | Promise<boolean | void>
  onListSuccess?: () => void
}) {
  const cwd = ref(opts.initialDir ?? '')
  const files = ref<FileItem[]>([])
  const loading = ref(false)
  let version = 0

  // --- Navigation history (per-pane) ---
  // Stack of absolute directories plus the current position. Every successful
  // navigation/refresh whose directory differs from the current position
  // truncates everything after it and appends (no consecutive duplicates);
  // back/forward only move the index, so they never duplicate entries.
  const dirStack = ref<string[]>([])
  const dirIndex = ref(-1)
  const canBack = computed(() => dirIndex.value > 0)
  const canForward = computed(() =>
    dirIndex.value >= 0 && dirIndex.value < dirStack.value.length - 1)

  function recordHistory(dir: string) {
    if (dirStack.value[dirIndex.value] === dir) return
    dirStack.value = [...dirStack.value.slice(0, dirIndex.value + 1), dir]
    dirIndex.value = dirStack.value.length - 1
  }

  /** Shared load core of onRefresh/onNavigate. `dir` is the list/change target,
   *  `cwdFallback` keeps the old cwd when the backend returns no directory, and
   *  `push` records the result in the history stack. Returns true only when
   *  this call's own result was applied (not superseded, no failure). */
  async function loadDir(
    kind: 'list' | 'change',
    dir: string,
    cwdFallback: string,
    push: boolean,
  ): Promise<boolean> {
    const id = opts.sid()
    if (!id) return false
    const v = ++version
    loading.value = true
    try {
      const run = kind === 'list' ? opts.list(id, dir || '') : opts.changeDir(id, dir)
      const result = kind === 'list' && opts.listTimeoutMs
        ? await withTimeout(run, opts.listTimeoutMs, 'list')
        : await run
      if (v !== version) return false
      files.value = result.files || []
      cwd.value = result.dir || cwdFallback
      if (push) recordHistory(result.dir || cwdFallback)
      if (kind === 'list') opts.onListSuccess?.()
      await opts.afterList?.(result.dir)
      return true
    } catch (e: any) {
      if (v !== version) return false
      const err = e?.toString?.() || String(e)
      if (await opts.onListError?.(err)) return false
      msg.error(err)
      return false
    } finally {
      if (v === version) loading.value = false
    }
  }

  async function onRefresh(dir = cwd.value) {
    await loadDir('list', dir, cwd.value, true)
  }

  async function onNavigate(path: string) {
    const target = opts.resolveTarget(cwd.value, path)
    await loadDir('change', target, target, true)
  }

  /** Moves through the history stack and lists the stored absolute directory
   *  via the same change-dir binding a normal navigation uses — without
   *  pushing history, so back-then-forward never duplicates entries. The index
   *  only advances when the load succeeds, so failures leave history intact. */
  async function goHistory(delta: number) {
    const idx = dirIndex.value + delta
    if (idx < 0 || idx >= dirStack.value.length) return
    const dir = dirStack.value[idx]
    if (await loadDir('change', dir, dir, false)) {
      dirIndex.value = idx
    }
  }

  const onBack = () => goHistory(-1)
  const onForward = () => goHistory(1)
  const onUp = () => onNavigate('..')

  function onCancelLoad() {
    version++
    loading.value = false
  }

  return {
    cwd, files, loading, onRefresh, onNavigate, onCancelLoad,
    canBack, canForward, onBack, onForward, onUp,
  }
}

// --- Change-permission dialog ------------------------------------------------

export function useChmodDialog(opts: {
  /** Resolve the operation target when the user confirms; ctx is whatever the
   *  host passed to onChmod (e.g. the pane name). */
  target: (item: FileItem, ctx?: unknown) => { sid: string; path: string } | null
  chmod?: (sid: string, path: string, octal: string) => Promise<unknown>
  refresh: () => void
}) {
  const chmodVisible = ref(false)
  const chmodItem = ref<FileItem | null>(null)
  let chmodCtx: unknown

  function onChmod(item: FileItem, ctx?: unknown) {
    chmodCtx = ctx
    chmodItem.value = item
    chmodVisible.value = true
  }

  async function onChmodConfirm(octal: string) {
    const item = chmodItem.value
    const target = item ? opts.target(item, chmodCtx) : null
    if (!target) return
    chmodItem.value = null
    try {
      await (opts.chmod ?? SftpChmod)(target.sid, target.path, octal)
      opts.refresh()
    } catch (e) { console.error('chmod:', e) }
  }

  return { chmodVisible, chmodItem, onChmod, onChmodConfirm }
}

// --- Editor dialog bridge ------------------------------------------------------

export function useEditorBridge(opts: { saved: () => void }) {
  const editorVisible = ref(false)
  const editorMode = ref<'local' | 'remote'>('remote')
  const fileEditorRef = ref<{ open: (path: string, title: string, mode?: 'local' | 'remote') => Promise<void> } | null>(null)

  async function openEditor(path: string, title: string, mode: 'local' | 'remote' = 'remote') {
    editorMode.value = mode
    await fileEditorRef.value?.open(path, title, mode)
  }

  function onEditorSaved() {
    opts.saved()
  }

  return { editorVisible, editorMode, fileEditorRef, openEditor, onEditorSaved }
}

// --- Drag-hover state ----------------------------------------------------------

export function useDragOver(opts?: { dropEffect?: (e: DragEvent) => string }) {
  const dragOver = ref(false)
  let enterCount = 0

  function onDragEnter(e: DragEvent) {
    if (!e.dataTransfer?.types?.includes('Files')) return
    enterCount++
    dragOver.value = true
  }

  function onDragLeave() {
    if (--enterCount <= 0) {
      enterCount = 0
      dragOver.value = false
    }
  }

  function onDragOver(e: DragEvent) {
    if (e.dataTransfer) e.dataTransfer.dropEffect = (opts?.dropEffect?.(e) ?? 'copy') as DataTransfer['dropEffect']
  }

  function clearDragState() {
    dragOver.value = false
    enterCount = 0
  }

  return { dragOver, onDragEnter, onDragLeave, onDragOver, clearDragState }
}

// --- Native (OS) file-drop binding ----------------------------------------------

export function useNativeFileDrop(opts: {
  /** Wails forwards the drop zone element id; only matching drops are kept. */
  elementId?: string
  isActive: () => boolean
  upload: (paths: string[]) => void
}) {
  let bound = false
  let unsub: (() => void) | null = null

  function bind() {
    if (bound) return
    try {
      unsub = Events.On('common:WindowFilesDropped', (ev) => {
        const d = ev.data as { elementId?: string; filenames: string[] }
        if (!opts.isActive() || !d?.filenames?.length) return
        if (d.elementId && opts.elementId && d.elementId !== opts.elementId) return
        opts.upload(d.filenames)
      })
      bound = true
    } catch {
      // runtime may be unavailable in browser preview
    }
  }

  function unbind() {
    if (!bound) return
    try { unsub?.(); unsub = null } catch { /* ignore */ }
    bound = false
  }

  return { bind, unbind }
}
