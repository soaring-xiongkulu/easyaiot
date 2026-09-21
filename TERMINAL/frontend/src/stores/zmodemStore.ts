import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type TransferDirection = 'upload' | 'download'
export type TransferStatus = 'pending' | 'transferring' | 'completed' | 'cancelled' | 'error'

export interface TransferInfo {
  id: string
  sessionId: string
  filename: string
  size: number
  transferred: number
  direction: TransferDirection
  status: TransferStatus
  speed: number
  savePath?: string
  error?: string
}

export const useZmodemStore = defineStore('zmodem', () => {
  const transfers = ref<Map<string, TransferInfo[]>>(new Map())

  // Store abort functions so any BaseTerminal instance can cancel an
  // active transfer, even if the zmodem service lives in a different
  // (KeepAlive-cached) component instance.
  const abortFns = new Map<string, () => void>()

  function registerAbort(sessionId: string, abort: () => void) {
    abortFns.set(sessionId, abort)
  }

  function unregisterAbort(sessionId: string) {
    abortFns.delete(sessionId)
  }

  // Shared cancellation timestamp so any component can set the 2s swallow
  // window, and the onComplete callback (which may run in a different
  // component instance) can compute the correct delay before sending \n.
  const cancelUntil = new Map<string, number>()

  function setCancelUntil(sessionId: string, ts: number) {
    cancelUntil.set(sessionId, ts)
  }

  function getCancelUntil(sessionId: string): number {
    return cancelUntil.get(sessionId) || 0
  }

  // Pending upload file paths (set by drag-and-drop, consumed by zmodem on_detect)
  const pendingUploads = new Map<string, string[]>()

  function setPendingUploadFiles(sessionId: string, paths: string[]) {
    pendingUploads.set(sessionId, paths)
  }

  function getPendingUploadFiles(sessionId: string): string[] | undefined {
    const paths = pendingUploads.get(sessionId)
    pendingUploads.delete(sessionId)
    return paths
  }

  function abortTransfer(sessionId: string) {
    abortFns.get(sessionId)?.()
    abortFns.delete(sessionId)
  }

  const getTransfers = computed(() => {
    return (sessionId: string): TransferInfo[] => {
      return transfers.value.get(sessionId) || []
    }
  })

  const getActiveTransfer = computed(() => {
    return (sessionId: string): TransferInfo | undefined => {
      const list = transfers.value.get(sessionId) || []
      return list.find(t => t.status === 'transferring' || t.status === 'pending')
    }
  })

  function addTransfer(sessionId: string, info: TransferInfo) {
    const list = transfers.value.get(sessionId) || []
    list.push(info)
    transfers.value.set(sessionId, list)
  }

  function updateTransfer(sessionId: string, transferId: string, updates: Partial<TransferInfo>) {
    const list = transfers.value.get(sessionId) || []
    const idx = list.findIndex(t => t.id === transferId)
    if (idx >= 0) {
      list[idx] = { ...list[idx], ...updates }
      transfers.value.set(sessionId, [...list])
    }
  }

  function clearTransfers(sessionId: string) {
    transfers.value.delete(sessionId)
  }

  function removeCompleted(sessionId: string) {
    const list = transfers.value.get(sessionId) || []
    const active = list.filter(t => t.status !== 'completed')
    if (active.length === 0) {
      transfers.value.delete(sessionId)
    } else {
      transfers.value.set(sessionId, active)
    }
  }

  return {
    transfers,
    getTransfers,
    getActiveTransfer,
    addTransfer,
    updateTransfer,
    clearTransfers,
    removeCompleted,
    registerAbort,
    unregisterAbort,
    abortTransfer,
    setCancelUntil,
    getCancelUntil,
    setPendingUploadFiles,
    getPendingUploadFiles,
  }
})
