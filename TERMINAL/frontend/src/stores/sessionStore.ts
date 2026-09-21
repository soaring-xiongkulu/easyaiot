import { defineStore } from 'pinia'
import { reactive } from 'vue'
import { Events } from '@wailsio/runtime'
import type { SessionStatus } from '../types/session'
import { useZmodemStore } from './zmodemStore'

interface SessionData {
  id: string
  status: SessionStatus
  // Detected remote OS (e.g. "windows-openssh") reported by the backend on
  // connect. Empty when unknown or not applicable.
  remoteOS?: string
  data: string[]
  // Monotonically increasing count of chunks ever appended to this session.
  // Unlike data.length, it is NOT reset when `data` is trimmed from the front,
  // so it is a stable sequence number for tracking replay position across
  // trims. See getDataFromChunk.
  seq: number
  // Sum of `data[i].length` (string code units). Used to enforce a byte-size
  // cap so total resident memory per session stays bounded under real-world
  // chunk sizes (F-019 P0).
  bytes: number
}

// Chunk-count cap (legacy protection against pathological tiny-chunk floods).
// Once `data.length > MAX_CHUNKS`, drop from the front down to TRIM_TO.
// Trimming removes from the front, which is why consumers must track position
// by `seq` (a stable sequence number), not by array index.
const MAX_CHUNKS = 2000
const TRIM_TO = 1000

// Byte-size cap (F-019 P0). Real chunks are typically 4 KB–16 KB; an 8-tab
// session at the old 2000-chunk ceiling held ~64 MB resident in Pinia state.
// Cap each session to MAX_BYTES (~256 KB, ≈ 4× viewport) and, when exceeded,
// trim from the front down to MAX_BYTES_TO before appending so we don't
// thrash on every subsequent chunk.
const MAX_BYTES = 256 * 1024
const MAX_BYTES_TO = 192 * 1024

function pushChunk(s: SessionData, chunk: string) {
  s.data.push(chunk)
  s.bytes += chunk.length
  s.seq++
  if (s.data.length > MAX_CHUNKS) {
    const drop = s.data.length - TRIM_TO
    for (let i = 0; i < drop; i++) s.bytes -= s.data[i].length
    s.data.splice(0, drop)
  }
  if (s.bytes > MAX_BYTES) {
    let dropIdx = 0
    let dropped = 0
    const target = s.bytes - MAX_BYTES_TO
    while (dropIdx < s.data.length && dropped < target) {
      dropped += s.data[dropIdx].length
      dropIdx++
    }
    if (dropIdx > 0) {
      s.data.splice(0, dropIdx)
      s.bytes -= dropped
    }
  }
}

// Module-level reactive state (shared across all store instances)
const sessionState = reactive<{
  sessions: Map<string, SessionData>
}>({
  sessions: new Map()
})

// Module-level un-subscribers for session:status / session:data listeners.
// Tracked at module scope so HMR re-imports can detach the previous listener
// before re-subscribing (FE-03).
let unsubSessionStatus: (() => void) | null = null
let unsubSessionData: (() => void) | null = null

// Register event listeners once at module level
unsubSessionStatus =Events.On('session:status', (ev) => { const payload: { id: string; status: SessionStatus; remoteOS?: string } = ev.data; 
  let s = sessionState.sessions.get(payload.id)
  if (!s) {
    s = { id: payload.id, status: 'connecting', data: [], seq: 0, bytes: 0 }
    sessionState.sessions.set(payload.id, s)
  }
  s.status = payload.status
  if (payload.remoteOS !== undefined) {
    s.remoteOS = payload.remoteOS
  }
 })

unsubSessionData =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data;
  // Chunks arriving inside a zmodem cancel window are residual binary
  // garbage from the aborted transfer (the backend has already left binary
  // mode, so the bytes take the text path). They are swallowed from live
  // rendering too; storing them here would replay them straight into xterm
  // on tab-switch gap replay, which bypasses the zmodem gates.
  try {
    if (Date.now() < useZmodemStore().getCancelUntil(payload.id)) return
  } catch (_) {
    // Pinia not installed yet (event before app init) — store normally.
  }
  let s = sessionState.sessions.get(payload.id)
  if (!s) {
    s = { id: payload.id, status: 'connecting', data: [], seq: 0, bytes: 0 }
    sessionState.sessions.set(payload.id, s)
  }
  pushChunk(s, payload.data)
 })

// Detach both session:* listeners. Called from App.vue's onUnmounted.
export function disposeSessionStore() {
  unsubSessionStatus?.()
  unsubSessionStatus = null
  unsubSessionData?.()
  unsubSessionData = null
}

export const useSessionStore = defineStore('session', () => {
  function initSession(id: string) {
    const existing = sessionState.sessions.get(id)
    if (existing) {
      if (existing.status !== 'connected') {
        existing.status = 'connecting'
      }
    } else {
      sessionState.sessions.set(id, { id, status: 'connecting', data: [], seq: 0, bytes: 0 })
    }
  }

  function updateStatus(id: string, status: SessionStatus) {
    const s = sessionState.sessions.get(id)
    if (s) {
      s.status = status
    }
  }

  function getStatus(id: string): SessionStatus {
    const s = sessionState.sessions.get(id)
    return s ? s.status : 'disconnected'
  }

  function getRemoteOS(id: string): string | undefined {
    const s = sessionState.sessions.get(id)
    return s ? s.remoteOS : undefined
  }

  function appendData(id: string, chunk: string) {
    const s = sessionState.sessions.get(id)
    if (s) {
      pushChunk(s, chunk)
    }
  }

  function getData(id: string): string {
    const s = sessionState.sessions.get(id)
    if (!s) return ''
    const raw = s.data.join('')
    // When the buffer is trimmed (2000→1000 chunks), the joined string may
    // start mid-escape-sequence (e.g. DA2, OSC color queries). Those broken
    // fragments lack the \x1b prefix and xterm.js renders them as garbled text.
    // Find the first \n or \x1b to locate a safe restart boundary.
    const nl = raw.indexOf('\n')
    const esc = raw.indexOf('\x1b')
    if (esc >= 0 && esc < 4096 && (nl < 0 || esc < nl)) {
      return raw.slice(esc)
    }
    if (nl > 0 && nl < 4096) {
      return raw.slice(nl + 1)
    }
    return raw
  }

  // Total number of chunks ever received for this session. This is a stable,
  // monotonically increasing sequence number — pass it to getDataFromChunk to
  // resume from a remembered position even after the buffer has been trimmed.
  function getChunkCount(id: string): number {
    const s = sessionState.sessions.get(id)
    return s ? s.seq : 0
  }

  // Return all chunks with sequence number >= startSeq, joined. `startSeq` is a
  // value previously returned by getChunkCount. If the requested position has
  // already been trimmed away, returns everything still buffered (best effort,
  // so the most recent output — including the final prompt — is never dropped).
  function getDataFromChunk(id: string, startSeq: number): string {
    const s = sessionState.sessions.get(id)
    if (!s) return ''
    // Number of chunks already dropped from the front of `data`.
    const base = s.seq - s.data.length
    let idx = startSeq - base
    if (idx >= s.data.length) return ''
    if (idx < 0) idx = 0
    return s.data.slice(idx).join('')
  }

  // Drop the buffered output for `id` (F-019 cleanup-on-close). Calling before
  // the map delete lets GC reclaim the string chunks promptly instead of
  // waiting for the next reactive write to fire.
  function clearData(id: string) {
    const s = sessionState.sessions.get(id)
    if (s) {
      s.data.length = 0
      s.bytes = 0
    }
  }

  function removeSession(id: string) {
    const s = sessionState.sessions.get(id)
    if (s) {
      s.data.length = 0
      s.bytes = 0
    }
    sessionState.sessions.delete(id)
  }

  return {
    sessions: sessionState.sessions,
    initSession,
    updateStatus,
    getStatus,
    getRemoteOS,
    appendData,
    getData,
    getChunkCount,
    getDataFromChunk,
    clearData,
    removeSession
  }
})
