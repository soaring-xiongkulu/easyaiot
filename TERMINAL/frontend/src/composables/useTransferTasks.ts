import { watch } from 'vue'
import type { TransferTaskUI } from '../stores/panelStore'

/**
 * Shared helpers for the file-transfer task UI. Event bookkeeping itself
 * lives in services/transferTaskCenter.ts (app-level routing into
 * panelStore); this module keeps the view-side utilities: auto-expand
 * watching, retry skip-list building and finished-count helpers.
 *
 * watchNewTransferTasks fires onNew() when the task list gains at least one
 * task id not seen before (used to auto-expand a collapsed transfer panel).
 * The getter must READ the task ids — watching the array by reference never
 * fires when tasks are pushed into it, which is how the sidebar's auto-expand
 * broke once.
 */
export function watchNewTransferTasks(getTasks: () => TransferTaskUI[], onNew: () => void) {
  const seen = new Set<string>()
  watch(() => getTasks().map(t => t.id).join('|'), () => {
    let hasNew = false
    for (const task of getTasks()) {
      if (!seen.has(task.id)) {
        seen.add(task.id)
        hasNew = true
      }
    }
    if (hasNew) onNew()
  })
}

/**
 * Keep a finished-transfers counter for cheap UI state (e.g. enabling the
 * "clear completed" button) without recomputing by hand everywhere.
 */
export function countFinishedTasks(tasks: TransferTaskUI[]): number {
  return tasks.filter(t => t.status === 'done' || t.status === 'error' || t.status === 'cancelled').length
}

/**
 * Relative paths of files already completed — the retry skip list. Passed to
 * SftpRetryTransfer so the backend only re-transfers what failed or never ran.
 */
export function buildSkipList(task: TransferTaskUI): string[] {
  return task.files.filter(f => f.status === 'done').map(f => f.path)
}
