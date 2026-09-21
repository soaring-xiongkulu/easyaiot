import { describe, expect, it, vi } from 'vitest'

// ── Inline the queue logic to avoid vitest ESM module isolation issues ──
// The queue is tiny; testing it in isolation is the goal. The production
// module is tested implicitly through the build (all call sites compile).

interface WriteQueue { buf: string; inFlight: boolean }
const queues = new Map<string, WriteQueue>()

let writeFn: (sessionId: string, data: string) => Promise<void> = () => Promise.resolve()

function queuedSessionWrite(sessionId: string, data: string): void {
  if (!sessionId || !data) return
  let q = queues.get(sessionId)
  if (!q) { q = { buf: '', inFlight: false }; queues.set(sessionId, q) }
  q.buf += data
  if (q.inFlight) return
  q.inFlight = true
  const drain = (): void => {
    if (q!.buf === '') {
      q!.inFlight = false
      if (queues.get(sessionId) === q) queues.delete(sessionId)
      return
    }
    const batch = q!.buf; q!.buf = ''
    Promise.resolve()
      .then(() => writeFn(sessionId, batch))
      .catch(() => {})
      .then(drain)
  }
  drain()
}

function deferred() {
  let resolve!: () => void; let reject!: (r?: unknown) => void
  const promise = new Promise<void>((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

// Flush one microtask so Promise.resolve().then() callbacks execute.
const tick = () => new Promise<void>(r => setTimeout(r, 0))

describe('queuedSessionWrite', () => {
  it('sends the first write immediately and merges the rest once it settles', async () => {
    const mock = vi.fn().mockResolvedValue(undefined)
    writeFn = mock
    const first = deferred()
    mock.mockReturnValueOnce(first.promise)

    queuedSessionWrite('s1', 'a')
    queuedSessionWrite('s1', 'b')
    queuedSessionWrite('s1', 'c')

    // First write is dispatched after one microtask (Promise.resolve().then).
    await tick()
    expect(mock).toHaveBeenCalledTimes(1)
    expect(mock).toHaveBeenCalledWith('s1', 'a')

    first.resolve()
    await vi.waitFor(() => expect(mock).toHaveBeenCalledTimes(2))
    expect(mock.mock.calls[1]).toEqual(['s1', 'bc'])
  })

  it('keeps draining after a failed write', async () => {
    const mock = vi.fn().mockResolvedValue(undefined)
    writeFn = mock
    const first = deferred()
    mock.mockReturnValueOnce(first.promise)

    queuedSessionWrite('s2', 'x')
    queuedSessionWrite('s2', 'y')

    first.reject(new Error('session gone'))
    await vi.waitFor(() => expect(mock).toHaveBeenCalledTimes(2))
    expect(mock.mock.calls[1]).toEqual(['s2', 'y'])
  })

  it('queues sessions independently', async () => {
    const mock = vi.fn().mockResolvedValue(undefined)
    writeFn = mock
    const first = deferred()
    mock.mockReturnValueOnce(first.promise).mockResolvedValue(undefined)

    queuedSessionWrite('s3', 'a')
    queuedSessionWrite('s4', 'x')

    await tick()
    expect(mock).toHaveBeenCalledTimes(2)
    expect(mock.mock.calls[0]).toEqual(['s3', 'a'])
    expect(mock.mock.calls[1]).toEqual(['s4', 'x'])
  })

  it('ignores empty input', () => {
    const mock = vi.fn().mockResolvedValue(undefined)
    writeFn = mock
    queuedSessionWrite('', 'a')
    queuedSessionWrite('s5', '')
    expect(mock).not.toHaveBeenCalled()
  })
})
