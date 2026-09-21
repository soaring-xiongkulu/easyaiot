import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const handlers: Record<string, (ev: any) => void> = {}
vi.mock('@wailsio/runtime', () => ({
  Events: {
    On: vi.fn((name: string, cb: (ev: any) => void) => {
      handlers[name] = cb
      return () => { delete handlers[name] }
    }),
  },
}))

// panelStore imports Wails app bindings, which pull in @wailsio/runtime
// exports beyond Events (Create/Models...) that the mock above omits. Mock the
// bindings module outright (same pattern as utils/quickConnect.test.ts).
vi.mock('../../bindings/easyaiot/terminal/app', () => ({
  DisableSessionOutputLog: vi.fn(),
  RegisterSessionForPanel: vi.fn(),
  UnregisterSession: vi.fn(),
}))

import { registerTransferRoute, unregisterTransferRoute } from './transferTaskCenter'
import { usePanelStore } from '../stores/panelStore'

function fireTransfer(payload: any) {
  handlers['sftp:transfer']({ data: payload })
}

// The router is a module singleton (routes + listener persist across tests,
// mirroring app lifetime). Each test uses unique session ids / list keys so
// registrations never cross-talk.
beforeEach(() => {
  setActivePinia(createPinia())
})

describe('transferTaskCenter routing', () => {
  it('creates, updates and completes a task in the registered list', () => {
    const onDone = vi.fn()
    registerTransferRoute('sid-1', 'key-1', onDone)
    const tasks = usePanelStore().getTransferTasks('key-1')

    fireTransfer({ sessionId: 'sid-1', type: 'sftp:transfer', taskId: 'dl-1', event: 'start', tfType: 'download', name: 'dir', total: 100 })
    expect(tasks).toHaveLength(1)
    expect(tasks[0]).toMatchObject({ id: 'dl-1', name: 'dir', status: 'running', total: 100 })

    fireTransfer({ sessionId: 'sid-1', type: 'sftp:transfer', taskId: 'dl-1', event: 'progress', progress: 50, total: 100 })
    expect(tasks[0].percentage).toBe(50)

    fireTransfer({ sessionId: 'sid-1', type: 'sftp:transfer', taskId: 'dl-1', event: 'complete', status: 'done' })
    expect(tasks[0].status).toBe('done')
    expect(onDone).toHaveBeenCalledWith('done', 'download')
  })

  it('keeps updating an earlier session route after other routes register (switch-terminal regression)', () => {
    // Session A starts a transfer, the user switches to terminal B (route for
    // B registers afterwards), then A's progress/complete arrive. A's list
    // must still receive them — this is the event flow the old per-component
    // filtered listener dropped.
    const onDoneA = vi.fn()
    registerTransferRoute('sid-a', 'key-a', onDoneA)
    const tasksA = usePanelStore().getTransferTasks('key-a')

    fireTransfer({ sessionId: 'sid-a', type: 'sftp:transfer', taskId: 'up-1', event: 'start', tfType: 'upload', name: 'big.bin', total: 200 })

    registerTransferRoute('sid-b', 'key-b')
    const tasksB = usePanelStore().getTransferTasks('key-b')

    fireTransfer({ sessionId: 'sid-a', type: 'sftp:transfer', taskId: 'up-1', event: 'progress', progress: 200, total: 200 })
    fireTransfer({ sessionId: 'sid-a', type: 'sftp:transfer', taskId: 'up-1', event: 'complete', status: 'error' })

    expect(tasksA[0].percentage).toBe(100)
    expect(tasksA[0].status).toBe('error')
    expect(onDoneA).toHaveBeenCalledWith('error', 'upload')
    expect(tasksB).toHaveLength(0)
  })

  it('fans out to every list key registered for the same session', () => {
    registerTransferRoute('sid-x', 'key-x1')
    registerTransferRoute('sid-x', 'key-x2')
    const t1 = usePanelStore().getTransferTasks('key-x1')
    const t2 = usePanelStore().getTransferTasks('key-x2')

    fireTransfer({ sessionId: 'sid-x', type: 'sftp:transfer', taskId: 'dl-2', event: 'start', tfType: 'download', name: 'f.bin', total: 10 })
    expect(t1).toHaveLength(1)
    expect(t2).toHaveLength(1)
  })

  it('replaces the done callback when the same route re-registers', () => {
    const first = vi.fn()
    const second = vi.fn()
    registerTransferRoute('sid-r', 'key-r', first)
    registerTransferRoute('sid-r', 'key-r', second)
    usePanelStore().getTransferTasks('key-r')

    fireTransfer({ sessionId: 'sid-r', type: 'sftp:transfer', taskId: 'up-2', event: 'start', tfType: 'upload', name: 'a.bin', total: 1 })
    fireTransfer({ sessionId: 'sid-r', type: 'sftp:transfer', taskId: 'up-2', event: 'complete', status: 'done' })

    expect(first).not.toHaveBeenCalled()
    expect(second).toHaveBeenCalledTimes(1)
  })

  it('ignores non-transfer payloads, unknown sessions and missing fields', () => {
    registerTransferRoute('sid-i', 'key-i')
    const tasks = usePanelStore().getTransferTasks('key-i')

    fireTransfer({ sessionId: 'sid-i', type: 'terminal:noise', event: 'start' })
    fireTransfer({ sessionId: 'sid-other', type: 'sftp:transfer', taskId: 'x', event: 'start', tfType: 'download', name: 'x', total: 1 })
    fireTransfer(undefined)
    fireTransfer({ data: null })
    expect(tasks).toHaveLength(0)
  })

  it('caps a list at 80 tasks, dropping the oldest', () => {
    registerTransferRoute('sid-cap', 'key-cap')
    const tasks = usePanelStore().getTransferTasks('key-cap')
    for (let i = 0; i < 81; i++) {
      fireTransfer({ sessionId: 'sid-cap', type: 'sftp:transfer', taskId: `t-${i}`, event: 'start', tfType: 'upload', name: `f${i}`, total: 1 })
    }
    expect(tasks).toHaveLength(80)
    expect(tasks[0].id).toBe('t-1')
    expect(tasks[79].id).toBe('t-80')
  })
})

describe('transferTaskCenter event details', () => {
  it('tracks per-file completion for directory transfers', () => {
    registerTransferRoute('sid-f1', 'key-f1')
    const tasks = usePanelStore().getTransferTasks('key-f1')

    fireTransfer({ sessionId: 'sid-f1', type: 'sftp:transfer', taskId: 'dl-9', event: 'start', tfType: 'download', name: 'bigdir', total: 300, fileCount: 3 })
    fireTransfer({ sessionId: 'sid-f1', type: 'sftp:transfer', taskId: 'dl-9', event: 'file-start', file: 'a.txt', name: 'a.txt' })
    expect(tasks[0].currentFile).toBe('a.txt')
    expect(tasks[0].files).toContainEqual({ path: 'a.txt', status: 'running' })
    fireTransfer({ sessionId: 'sid-f1', type: 'sftp:transfer', taskId: 'dl-9', event: 'file-done', file: 'a.txt', completedFiles: 1, fileCount: 3 })
    expect(tasks[0].files[0]).toEqual({ path: 'a.txt', status: 'done' })
    expect(tasks[0].completedFiles).toBe(1)
    fireTransfer({ sessionId: 'sid-f1', type: 'sftp:transfer', taskId: 'dl-9', event: 'file-failed', file: 'b.txt', error: 'permission denied' })
    expect(tasks[0].files.find(f => f.path === 'b.txt')!.status).toBe('failed')
    expect(tasks[0].failedFiles).toContainEqual({ path: 'b.txt', error: 'permission denied' })
  })

  it('learns fileCount from file/complete events so failed dir transfers retry recursively', () => {
    registerTransferRoute('sid-f2', 'key-f2')
    const tasks = usePanelStore().getTransferTasks('key-f2')

    fireTransfer({ sessionId: 'sid-f2', type: 'sftp:transfer', taskId: 'dl-3', event: 'start', tfType: 'download', name: 'dir' })
    expect(tasks[0].fileCount).toBe(0)
    fireTransfer({ sessionId: 'sid-f2', type: 'sftp:transfer', taskId: 'dl-3', event: 'file-start', file: 'a.txt', name: 'a.txt', fileCount: 3 })
    expect(tasks[0].fileCount).toBe(3)
    fireTransfer({ sessionId: 'sid-f2', type: 'sftp:transfer', taskId: 'dl-3', event: 'file-failed', file: 'a.txt', error: 'boom', fileCount: 3 })
    fireTransfer({ sessionId: 'sid-f2', type: 'sftp:transfer', taskId: 'dl-3', event: 'complete', status: 'error', fileCount: 3, completedFiles: 0 })
    expect(tasks[0].status).toBe('error')
    expect(tasks[0].fileCount).toBe(3)
  })

  it('maps paused/resumed onto task status without firing the done callback', () => {
    const onDone = vi.fn()
    registerTransferRoute('sid-f3', 'key-f3', onDone)
    const tasks = usePanelStore().getTransferTasks('key-f3')

    fireTransfer({ sessionId: 'sid-f3', type: 'sftp:transfer', taskId: 'dl-7', event: 'start', tfType: 'upload', name: 'big.bin', total: 100 })
    fireTransfer({ sessionId: 'sid-f3', type: 'sftp:transfer', taskId: 'dl-7', event: 'paused' })
    expect(tasks[0].status).toBe('paused')
    fireTransfer({ sessionId: 'sid-f3', type: 'sftp:transfer', taskId: 'dl-7', event: 'resumed' })
    expect(tasks[0].status).toBe('running')
    expect(onDone).not.toHaveBeenCalled()
  })

  it('stores the full source/target paths from the start payload', () => {
    registerTransferRoute('sid-f4', 'key-f4')
    const tasks = usePanelStore().getTransferTasks('key-f4')

    fireTransfer({
      sessionId: 'sid-f4', type: 'sftp:transfer', taskId: 'up-1', event: 'start',
      tfType: 'upload', name: 'big.bin', total: 10,
      localPath: 'C:/data/big.bin', remotePath: '/srv/big.bin',
    })
    expect(tasks[0].localPath).toBe('C:/data/big.bin')
    expect(tasks[0].remotePath).toBe('/srv/big.bin')
  })

  it('unregisterTransferRoute stops delivery and is a no-op for unknown sessions', () => {
    registerTransferRoute('sid-u1', 'key-u1')
    const tasks = usePanelStore().getTransferTasks('key-u1')
    fireTransfer({ sessionId: 'sid-u1', type: 'sftp:transfer', taskId: 'dl-u', event: 'start', tfType: 'download', name: 'f', total: 1 })
    expect(tasks).toHaveLength(1)

    unregisterTransferRoute('sid-u1')
    fireTransfer({ sessionId: 'sid-u1', type: 'sftp:transfer', taskId: 'dl-u2', event: 'start', tfType: 'download', name: 'f2', total: 1 })
    expect(tasks).toHaveLength(1) // no new task after unregistration

    expect(() => unregisterTransferRoute('sid-unknown')).not.toThrow()
    expect(() => unregisterTransferRoute('')).not.toThrow()
  })
})
