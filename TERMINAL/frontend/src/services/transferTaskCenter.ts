import { Events } from '@wailsio/runtime'
import { usePanelStore } from '../stores/panelStore'
import type { TransferTaskUI } from '../stores/panelStore'

export type TransferDoneCallback = (status: string, type: string) => void

// App-level routing of backend `sftp:transfer` events into the per-panel task
// lists held by panelStore. Routes are keyed (session id → list key) and
// outlive view switches ON PURPOSE: a transfer keeps running while the user
// switches to another terminal or hides the file sidebar, and its
// progress/complete events must still land in the owning panel's list. A
// component-local listener filtered by the currently active session dropped
// those events, which froze the transfer panel (stuck progress, cancel hitting
// "task not found", failed tasks never becoming clearable). Routes live until
// their panel/session is disposed via unregisterTransferRoute.
const routes = new Map<string, Map<string, TransferDoneCallback | undefined>>()
let listening = false

function ensureListener() {
  if (listening) return
  listening = true
  Events.On('sftp:transfer', (ev) => {
    const msg = ev?.data as (Record<string, any> & { type?: string; sessionId?: string }) | undefined
    if (!msg || msg.type !== 'sftp:transfer' || !msg.sessionId) return
    dispatchTransferEvent(msg)
  })
}

/** Registers (or replaces) the route delivering `sessionId` events to `listKey`. */
export function registerTransferRoute(sessionId: string, listKey: string, onDone?: TransferDoneCallback) {
  if (!sessionId || !listKey) return
  ensureListener()
  let perKey = routes.get(sessionId)
  if (!perKey) {
    perKey = new Map()
    routes.set(sessionId, perKey)
  }
  perKey.set(listKey, onDone)
}

/** Drops every route registered for `sessionId` (panel/session closed).
 * Events for an unregistered session are ignored. */
export function unregisterTransferRoute(sessionId: string) {
  if (!sessionId) return
  routes.delete(sessionId)
}

/** Delivers one backend event to every list key registered for its session. */
function dispatchTransferEvent(msg: Record<string, any>) {
  const perKey = routes.get(msg.sessionId)
  if (!perKey) return
  const store = usePanelStore()
  for (const [listKey, onDone] of perKey) {
    applyTransferEvent(store.getTransferTasks(listKey), msg, onDone)
  }
}

function applyTransferEvent(tasks: TransferTaskUI[], msg: Record<string, any>, onDone?: TransferDoneCallback) {
  if (msg.event === 'start') {
    const existing = tasks.find(t => t.id === msg.taskId)
    if (existing) {
      existing.status = 'running'
      existing.speed = ''
      existing.eta = ''
      existing.lastBytes = 0
      existing.lastTime = Date.now()
    } else {
      tasks.push({
        id: msg.taskId,
        type: msg.tfType,
        name: msg.name,
        localPath: msg.localPath || '',
        remotePath: msg.remotePath || '',
        percentage: 0,
        speed: '',
        eta: '',
        status: 'running',
        lastBytes: 0,
        lastTime: Date.now(),
        total: msg.total || 0,
        fileCount: msg.fileCount || 0,
        completedFiles: 0,
        currentFile: '',
        files: [],
        failedFiles: [],
      })
      while (tasks.length > 80) tasks.shift()
    }
  } else if (msg.event === 'progress') {
    const existing = tasks.find(t => t.id === msg.taskId)
    if (existing) {
      existing.total = msg.total || existing.total
      existing.percentage = existing.total > 0 ? Math.round((msg.progress / existing.total) * 100) : 0
      const now = Date.now()
      const elapsed = (now - existing.lastTime) / 1000
      if (elapsed >= 0.5) {
        const bytesSince = msg.progress - existing.lastBytes
        const bytesPerSec = bytesSince / elapsed
        existing.speed = formatSpeed(bytesPerSec)
        if (bytesPerSec > 0 && existing.total > 0) {
          existing.eta = formatETA((existing.total - msg.progress) / bytesPerSec)
        }
        existing.lastBytes = msg.progress
        existing.lastTime = now
      }
    }
  } else if (msg.event === 'file-start') {
    const t = tasks.find(t => t.id === msg.taskId)
    if (t) {
      t.currentFile = msg.name || msg.file
      t.files.push({ path: msg.file, status: 'running' })
      t.fileCount = msg.fileCount || t.fileCount
    }
  } else if (msg.event === 'file-done') {
    const t = tasks.find(t => t.id === msg.taskId)
    if (t) {
      const f = t.files.find((f: any) => f.path === msg.file)
      if (f) f.status = 'done'
      else t.files.push({ path: msg.file, status: 'done' })
      t.completedFiles = msg.completedFiles ?? t.completedFiles
      t.fileCount = msg.fileCount || t.fileCount
    }
  } else if (msg.event === 'file-failed') {
    const t = tasks.find(t => t.id === msg.taskId)
    if (t) {
      const f = t.files.find((f: any) => f.path === msg.file)
      if (f) f.status = 'failed'
      else t.files.push({ path: msg.file, status: 'failed' })
      t.failedFiles.push({ path: msg.file, error: msg.error })
      t.fileCount = msg.fileCount || t.fileCount
    }
  } else if (msg.event === 'paused') {
    const t = tasks.find(t => t.id === msg.taskId)
    if (t) t.status = 'paused'
  } else if (msg.event === 'resumed') {
    const t = tasks.find(t => t.id === msg.taskId)
    if (t) {
      t.status = 'running'
      // Reset the speed baseline so the pause duration doesn't skew the
      // next speed/eta sample.
      t.lastTime = Date.now()
    }
  } else if (msg.event === 'complete') {
    const existing = tasks.find(t => t.id === msg.taskId)
    if (existing) {
      const st = msg.status as string
      existing.status = st === 'done' ? 'done' : st === 'cancelled' ? 'cancelled' : st === 'paused' ? 'paused' : 'error'
      existing.percentage = existing.status === 'done' ? 100 : existing.percentage
      if (msg.fileCount) {
        existing.fileCount = msg.fileCount
        existing.completedFiles = msg.completedFiles ?? existing.completedFiles
      }
      if (msg.failedFiles) existing.failedFiles = msg.failedFiles
      onDone?.(existing.status, existing.type)
      // Finished tasks stay listed until the user clears them.
    }
  }
}

function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec < 1024) return Math.round(bytesPerSec) + ' B/s'
  if (bytesPerSec < 1024 * 1024) return (bytesPerSec / 1024).toFixed(1) + ' KB/s'
  return (bytesPerSec / (1024 * 1024)).toFixed(1) + ' MB/s'
}

function formatETA(seconds: number): string {
  if (seconds < 1) return ''
  if (seconds < 60) return Math.round(seconds) + 's'
  const m = Math.floor(seconds / 60)
  if (m < 60) return m + 'm'
  const h = Math.floor(m / 60)
  return h + 'h' + (m % 60 ? (m % 60) + 'm' : '')
}
