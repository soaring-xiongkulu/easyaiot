import { describe, it, expect, vi } from 'vitest'

// The merged module pulls in the terminal manager and the settings store;
// mock both so these registry tests stay hermetic (no xterm / pinia needed).
vi.mock('./terminalManager', () => ({
  getManagedTerminal: () => undefined,
}))
vi.mock('../stores/settingsStore', () => ({
  useSettingsStore: () => ({ settings: { terminal: { showTimestamps: false } } }),
}))

import {
  bufferRowSource,
  createLineRegistry,
  recordWrittenLines,
  realignRegistry,
  type LineRegistryRowSource,
  type RegistryBufferLike,
} from './terminalTimestamps'

/** Fake buffer: wrapped flags + per-row text ('' = blank). */
function fakeBuffer(wrapped: boolean[], text: string[]) {
  return {
    getLine(y: number) {
      if (y < 0 || y >= wrapped.length) return undefined
      return {
        isWrapped: wrapped[y],
        translateToString: () => text[y] ?? '',
      }
    },
  }
}

function source(wrapped: boolean[], text: string[]): LineRegistryRowSource {
  return bufferRowSource(fakeBuffer(wrapped, text) as unknown as RegistryBufferLike)
}

/** Run one write from cursor `before` (buffer row) to `after`. */
function write(
  state: ReturnType<typeof createLineRegistry>,
  src: LineRegistryRowSource,
  before: number,
  after: number,
  ts: number,
  lineOffset = 0,
) {
  recordWrittenLines(state, {
    lineOffset,
    beforeAbs: lineOffset + before,
    afterAbs: lineOffset + after,
    source: src,
    now: ts,
  })
}

function numbers(state: ReturnType<typeof createLineRegistry>): Array<[number, number]> {
  return [...state.entries.entries()]
    .map(([k, v]) => [k, v.number] as [number, number])
    .sort((a, b) => a[0] - b[0])
}

function times(state: ReturnType<typeof createLineRegistry>): Array<[number, number]> {
  return [...state.entries.entries()]
    .map(([k, v]) => [k, v.ts] as [number, number])
    .sort((a, b) => a[0] - b[0])
}

describe('recordWrittenLines()', () => {
  it('registers content rows with sequential numbers', () => {
    const state = createLineRegistry()
    const src = source([false, false, false], ['a', 'b', 'c'])
    write(state, src, 0, 2, 1000)
    expect(numbers(state)).toEqual([[0, 1], [1, 2], [2, 3]])
    expect(state.nextNumber).toBe(4)
  })

  it('does not register the empty row the cursor lands on after a newline', () => {
    const state = createLineRegistry()
    const src = source([false, false, false], ['a', '', ''])
    write(state, src, 0, 2, 1000)
    expect(numbers(state)).toEqual([[0, 1]])
  })

  it('registers a line only once (first write wins for the number and start ts)', () => {
    const state = createLineRegistry()
    const src = source([false], ['hello'])
    write(state, src, 0, 0, 1000)
    write(state, src, 0, 0, 2000)
    expect(numbers(state)).toEqual([[0, 1]])
    expect(times(state)).toEqual([[0, 1000]])
  })

  it('overwrites ts with the completion time once the cursor moves past', () => {
    const state = createLineRegistry()
    const src = source([false, false], ['hello', ''])
    write(state, src, 0, 0, 1000) // "hel" typed
    write(state, src, 0, 1, 2000) // newline: line 0 complete
    expect(times(state)).toEqual([[0, 2000]])
  })

  it('keeps the start ts while a progress bar redraws in place with \\r', () => {
    const state = createLineRegistry()
    const src = source([false], ['30%'])
    write(state, src, 0, 0, 1000)
    // \r redraw: cursor stays on the row, line not complete.
    write(state, src, 0, 0, 2000)
    expect(times(state)).toEqual([[0, 1000]])
    // The final newline completes it.
    write(state, src, 0, 1, 3000)
    expect(times(state)).toEqual([[0, 3000]])
  })

  it('handles a wrapped group: continuation rows get no number, completion stamps the start', () => {
    const state = createLineRegistry()
    // Rows 0-1 belong to one logical line; row 2 is the next line.
    const src = source([false, true, false], ['aaa', 'bbb', 'next'])
    write(state, src, 0, 2, 1000)
    expect(numbers(state)).toEqual([[0, 1], [2, 2]])
    // Newline moves cursor to row 3: the second line completes; the first
    // group already completed in the first write, so its ts is untouched.
    write(state, src, 2, 3, 2000)
    expect(times(state)).toEqual([[0, 1000], [2, 2000]])
  })

  it('registers lines arriving in the same write as one band, all with that write ts', () => {
    const state = createLineRegistry()
    const src = source([false, false, false, false], ['l1', 'l2', 'l3', ''])
    write(state, src, 0, 3, 1000)
    expect(numbers(state)).toEqual([[0, 1], [1, 2], [2, 3]])
    expect(times(state)).toEqual([[0, 1000], [1, 1000], [2, 1000]])
  })

  it('also registers content rows written above the band (cursor-addressed redraws)', () => {
    const state = createLineRegistry()
    // Rows 0-4 already registered; rows 5-8 blank. Cursor sits at row 9 while
    // a redraw paints content on row 7 without the cursor moving there.
    const wrapped = new Array(10).fill(false)
    const text = new Array(10).fill('x').map((c, i) => (i === 9 || i < 5 ? c : ''))
    let src = source(wrapped, text)
    write(state, src, 0, 9, 1000)
    // Now the redraw: row 7 gains content, cursor stays at row 9.
    text[7] = 'progress'
    src = source(wrapped, text)
    write(state, src, 9, 9, 2000)
    // Row 7 joins late, so it takes the next number after row 9's — late
    // registration, but registered.
    expect(numbers(state)).toEqual([[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [7, 7], [9, 6]])
    expect(times(state)).toEqual([[0, 1000], [1, 1000], [2, 1000], [3, 1000], [4, 1000], [7, 2000], [9, 1000]])
  })

  it('caps the map size by dropping the oldest numbers', () => {
    const state = createLineRegistry()
    for (let i = 0; i < 5001; i += 1) {
      state.entries.set(i, { number: i + 1, ts: 1000 })
    }
    state.nextNumber = 5002
    const src = source(new Array(5002).fill(false), new Array(5001).fill('x').concat(['new']))
    write(state, src, 5001, 5001, 2000)
    expect(state.entries.size).toBe(3000)
    // Oldest numbers dropped, the brand-new line survives.
    expect(state.entries.get(5001)?.number).toBe(5002)
    expect(state.entries.get(0)).toBeUndefined()
  })
})

describe('realignRegistry()', () => {
  it('re-keys entries to the rows lines start at after a reflow, preserving values', () => {
    const state = createLineRegistry()
    // Before: three logical lines at rows 0,1,2.
    let wrapped = [false, false, false]
    let text = ['a', 'b', 'c']
    let src = source(wrapped, text)
    write(state, src, 0, 3, 1000)

    // Reflow: shrinking cols wraps each line onto two rows → starts at 0,2,4.
    wrapped = [false, true, false, true, false]
    text = ['a', 'b', 'b', 'c', 'c', '']
    src = source(wrapped, text)
    realignRegistry(state, { lineOffset: 0, cursorAbs: 4, source: src })

    expect(numbers(state)).toEqual([[0, 1], [2, 2], [4, 3]])
    expect(times(state)).toEqual([[0, 1000], [2, 1000], [4, 1000]])
  })

  it('drops entries whose lines no longer exist in the buffer', () => {
    const state = createLineRegistry()
    const src = source([false, false, false], ['a', 'b', 'c'])
    write(state, src, 0, 3, 1000)
    // After the reflow only the last two lines remain (e.g. older content
    // scrolled off): starts at rows 0 and 1.
    const after = source([false, false], ['b', 'c'])
    realignRegistry(state, { lineOffset: 0, cursorAbs: 1, source: after })
    expect(numbers(state)).toEqual([[0, 2], [1, 3]])
  })

  it('offsets keys by lineOffset (trim-compensated absolute rows)', () => {
    const state = createLineRegistry()
    const src = source([false, false], ['a', 'b'])
    write(state, src, 0, 2, 1000, 5)
    const after = source([false, false], ['a', 'b'])
    realignRegistry(state, { lineOffset: 5, cursorAbs: 5 + 1, source: after })
    expect(numbers(state)).toEqual([[5, 1], [6, 2]])
  })

  it('anchors matching at the bottom: when entries run short, the OLDEST lines go without', () => {
    const state = createLineRegistry()
    // Only two entries survived (numbers 4,5 — the newest lines), but the
    // buffer holds four content lines after the reflow.
    state.entries.set(0, { number: 4, ts: 1000 })
    state.entries.set(1, { number: 5, ts: 1000 })
    state.nextNumber = 6
    const after = source([false, false, false, false], ['a', 'b', 'c', 'd'])
    realignRegistry(state, { lineOffset: 0, cursorAbs: 3, source: after })
    // Bottom lines keep the newest numbers; the top of the buffer goes blank.
    expect(numbers(state)).toEqual([[2, 4], [3, 5]])
  })
})

describe('bufferRowSource()', () => {
  it('treats whitespace-only rows as empty', () => {
    const src = source([false, false], ['   ', 'x'])
    expect(src.hasContent(0)).toBe(false)
    expect(src.hasContent(1)).toBe(true)
  })

  it('is tolerant of rows past the end of the buffer', () => {
    const src = source([false], ['a'])
    expect(src.isWrapped(99)).toBe(false)
    expect(src.hasContent(99)).toBe(false)
  })
})
