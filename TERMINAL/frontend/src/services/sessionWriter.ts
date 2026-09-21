import { SessionWrite } from '../../bindings/easyaiot/terminal/app'

// Wails v3 dispatches every JS binding call in its own goroutine
// (pkg/application/application.go: `event := <-windowMessageBuffer;
// go a.handleWindowMessage(event)`), so two SessionWrite calls issued in
// quick succession can reach the PTY out of order — under fast typing,
// characters appear swapped. Serialize per session on the JS side: at most
// one write in flight, the next batch is only sent after the previous one
// settles. Concatenation plus single-flight makes PTY delivery order exactly
// match call order, and merges keystroke-sized writes into fewer IPC calls.

// Wrapping the binding in an object allows tests to swap it without fighting
// vitest's ESM module namespace immutability.
export const writeFn: { current: typeof SessionWrite } = { current: SessionWrite }

interface WriteQueue {
  buf: string
  inFlight: boolean
}

const queues = new Map<string, WriteQueue>()

export function queuedSessionWrite(sessionId: string, data: string): void {
  if (!sessionId || !data) return
  let q = queues.get(sessionId)
  if (!q) {
    q = { buf: '', inFlight: false }
    queues.set(sessionId, q)
  }
  q.buf += data
  if (q.inFlight) return
  q.inFlight = true
  const drain = (): void => {
    if (q!.buf === '') {
      q!.inFlight = false
      if (queues.get(sessionId) === q) queues.delete(sessionId)
      return
    }
    const batch = q!.buf
    q!.buf = ''
    Promise.resolve()
      .then(() => writeFn.current(sessionId, batch))
      .catch(() => {})
      .then(drain)
  }
  drain()
}
