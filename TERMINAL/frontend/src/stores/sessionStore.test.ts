import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// EventsOn is called at module load; stub it so importing the store is safe.
// The session:data handler is captured so cancel-window tests can drive the
// module-level listener directly.
const { runtimeState } = vi.hoisted(() => ({
  runtimeState: {
    dataHandler: null as null | ((ev: any) => void),
  },
}))
vi.mock('@wailsio/runtime', () => ({
  Events: {
    On: vi.fn((name: string, handler: (ev: any) => void) => {
      if (name === 'session:data') runtimeState.dataHandler = handler
      return () => { if (name === 'session:data') runtimeState.dataHandler = null }
    }),
    Off: vi.fn(),
  },
}))

import { useSessionStore } from './sessionStore'
import { useZmodemStore } from './zmodemStore'

const MAX_CHUNKS = 2000
const TRIM_TO = 1000

describe('sessionStore replay tracking', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('getChunkCount is a monotonic sequence, not the buffer length', () => {
    const store = useSessionStore()
    const id = 'seq-monotonic'
    store.initSession(id)

    // Push more than MAX_CHUNKS so the buffer trims from the front.
    const total = MAX_CHUNKS + 500
    for (let i = 0; i < total; i++) store.appendData(id, `c${i}\n`)

    // seq counts everything ever appended, even though data was trimmed.
    expect(store.getChunkCount(id)).toBe(total)
  })

  it('replays the gap correctly after the buffer is trimmed', () => {
    const store = useSessionStore()
    const id = 'seq-gap'
    store.initSession(id)

    // Simulate: component recorded its position, then went to background
    // while a long compile flooded the session past the trim threshold.
    for (let i = 0; i < 500; i++) store.appendData(id, `pre${i}\n`)
    const writtenChunks = store.getChunkCount(id) // = 500

    // Flood well past MAX_CHUNKS so the first 500 chunks are trimmed away.
    const flood = MAX_CHUNKS + 800
    for (let i = 0; i < flood; i++) store.appendData(id, `post${i}\n`)

    // Old behavior (array index): getChunkCount would have been <= writtenChunks
    // after trimming, so `total > writtenChunks` was false and NOTHING replayed.
    const total = store.getChunkCount(id)
    expect(total).toBeGreaterThan(writtenChunks)

    // The gap replay must return recent output, including the very last chunk,
    // so the terminal never freezes mid-stream.
    const tail = store.getDataFromChunk(id, writtenChunks)
    expect(tail.length).toBeGreaterThan(0)
    expect(tail.endsWith(`post${flood - 1}\n`)).toBe(true)
  })

  it('getDataFromChunk returns best-effort tail when position was trimmed away', () => {
    const store = useSessionStore()
    const id = 'seq-trimmed-pos'
    store.initSession(id)

    for (let i = 0; i < MAX_CHUNKS + 1000; i++) store.appendData(id, `x${i}\n`)

    // Ask from sequence 0 (long since trimmed). Should not throw or return '',
    // but the buffered remainder — bounded by TRIM_TO..MAX_CHUNKS chunks.
    const tail = store.getDataFromChunk(id, 0)
    expect(tail.length).toBeGreaterThan(0)
    expect(tail.endsWith(`x${MAX_CHUNKS + 1000 - 1}\n`)).toBe(true)
    const lines = tail.trimEnd().split('\n')
    expect(lines.length).toBeLessThanOrEqual(MAX_CHUNKS)
    expect(lines.length).toBeGreaterThanOrEqual(TRIM_TO - 1)
  })

  it('getDataFromChunk returns empty once fully consumed', () => {
    const store = useSessionStore()
    const id = 'seq-consumed'
    store.initSession(id)
    for (let i = 0; i < 10; i++) store.appendData(id, `y${i}\n`)
    const total = store.getChunkCount(id)
    expect(store.getDataFromChunk(id, total)).toBe('')
  })

  // F-019 behavior-parity: the 256 KB byte cap must keep the most recent
  // output intact even after it has evicted earlier chunks. Regressing this
  // would re-introduce #288 (background-tab output truncation): when the
  // background tab becomes active again, the tail must include the latest
  // chunk so the user sees the prompt they were waiting for.
  it('256KB byte cap keeps the most recent chunks intact', () => {
    const store = useSessionStore()
    const id = 'byte-cap'
    store.initSession(id)

    // Push chunks totaling well over the 256 KB cap. 4 KB each × 200 = 800 KB.
    const chunkSize = 4 * 1024
    const total = 200
    for (let i = 0; i < total; i++) {
      // Make each chunk distinguishable by its leading line.
      const header = `chunk-${i.toString().padStart(4, '0')}-${'x'.repeat(chunkSize - 16)}\n`
      store.appendData(id, header)
    }
    expect(store.getChunkCount(id)).toBe(total)

    // The store reports a bounded number of buffered chunks; the buffer
    // must be < total (proves eviction ran) and the joined buffer must be
    // under the cap.
    const tail = store.getDataFromChunk(id, 0)
    expect(tail.length).toBeGreaterThan(0)
    expect(tail.length).toBeLessThanOrEqual(256 * 1024)

    // The most recent chunk must always survive. Reading from the very
    // last sequence position returns just that one chunk.
    const last = store.getDataFromChunk(id, total - 1)
    expect(last.startsWith(`chunk-${(total - 1).toString().padStart(4, '0')}`)).toBe(true)
  })

  // F-019 + F-026 + F-027 collectively fix #288: a background tab receives
  // a long flood of output, the front of the buffer is evicted, and when the
  // tab is reactivated the replay must still reach the most recent output.
  it('replay after byte-cap eviction still includes the latest output (issue #288)', () => {
    const store = useSessionStore()
    const id = 'replay-after-cap'
    store.initSession(id)

    // First wave — a few chunks so the component has a replay cursor.
    for (let i = 0; i < 50; i++) store.appendData(id, `pre-${i}\n`)
    const cursor = store.getChunkCount(id)

    // Second wave — floods past the byte cap.
    for (let i = 0; i < 200; i++) store.appendData(id, `post-${i}-${'y'.repeat(1024)}\n`)

    // Reactivation must replay the gap. The gap here covers everything from
    // `cursor` onward; the most recent chunk is the last `post-199-...` line.
    const replayed = store.getDataFromChunk(id, cursor)
    expect(replayed.length).toBeGreaterThan(0)
    expect(replayed.includes(`post-199-`)).toBe(true)
  })
})

describe('sessionStore zmodem cancel window', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function emitData(id: string, data: string) {
    runtimeState.dataHandler?.({ data: { id, data } })
  }

  it('stores chunks outside the cancel window', () => {
    const sessions = useSessionStore()
    const zmodem = useZmodemStore()
    zmodem.setCancelUntil('s-outside', Date.now() - 1)

    emitData('s-outside', 'hello')
    const total = sessions.getChunkCount('s-outside')
    expect(total).toBe(1)
    expect(sessions.getDataFromChunk('s-outside', 0)).toBe('hello')
  })

  it('drops chunks arriving inside the zmodem cancel window', () => {
    const sessions = useSessionStore()
    const zmodem = useZmodemStore()
    // Residual binary garbage from an aborted sz transfer lands within the
    // 2s cancel window; it must never enter the replay buffer, or tab-switch
    // gap replay writes it straight into xterm.
    zmodem.setCancelUntil('s-window', Date.now() + 2000)

    emitData('s-window', '\x18\x18garbage')
    emitData('s-window', '\x18more')

    expect(sessions.getChunkCount('s-window')).toBe(0)
    expect(sessions.getDataFromChunk('s-window', 0)).toBe('')
  })

  it('stores chunks again once the cancel window expires', () => {
    const sessions = useSessionStore()
    const zmodem = useZmodemStore()
    zmodem.setCancelUntil('s-expire', Date.now() + 2000)

    emitData('s-expire', '\x18garbage')
    expect(sessions.getChunkCount('s-expire')).toBe(0)

    zmodem.setCancelUntil('s-expire', Date.now() - 1)
    emitData('s-expire', 'prompt')
    expect(sessions.getChunkCount('s-expire')).toBe(1)
    expect(sessions.getDataFromChunk('s-expire', 0)).toBe('prompt')
  })
})
