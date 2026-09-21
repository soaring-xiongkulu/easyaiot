import { describe, it, expect, beforeAll } from 'vitest'
import { useTerminalInput } from './useTerminalInput'

// handleInput schedules cursor-position reads through requestAnimationFrame
// (PR #434 rAF coalescing). The default vitest environment is node, which
// has no rAF — run the callback synchronously so assertions see the result.
beforeAll(() => {
  const g = globalThis as any
  if (typeof g.requestAnimationFrame !== 'function') {
    g.requestAnimationFrame = (cb: FrameRequestCallback) => {
      cb(0)
      return 0
    }
    g.cancelAnimationFrame = () => {}
  }
})

function mkTerminal(opts: {
  cursorY?: number; lines: string[]; rows?: number; wrapped?: number[]
} = { lines: [] }) {
  const { cursorY = 0, lines, rows = 24 } = opts
  const wrapped = new Set(opts.wrapped ?? [])
  return {
    rows,
    buffer: {
      active: {
        y: cursorY,
        baseY: 0,
        getLine: (y: number) => lines[y] === undefined ? undefined : {
          translateToString: () => lines[y],
          isWrapped: () => wrapped.has(y),
        },
      },
    },
  } as any
}

describe('useTerminalInput', () => {
  describe('lineBuffer (char-array backed)', () => {
    it('get/set round-trip and preserve CJK chars', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.lineBuffer.value = 'hello'
      expect(t.lineBuffer.value).toBe('hello')
      t.lineBuffer.value = 'hi 你好'
      expect(t.lineBuffer.value).toBe('hi 你好')
    })

    it('handleInput inserts at cursor in the middle without losing existing chars', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.lineBuffer.value = 'hllo'
      t.cursorIndex.value = 1
      t.handleInput('e')
      expect(t.lineBuffer.value).toBe('hello')
      expect(t.cursorIndex.value).toBe(2)
    })

    it('handleInput appends when cursor is at end', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abc')
      expect(t.lineBuffer.value).toBe('abc')
      expect(t.cursorIndex.value).toBe(3)
      expect(t.isAtLineEnd()).toBe(true)
    })

    it('handleInput backspace removes char before cursor and shifts left', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abc')
      t.cursorIndex.value = 3
      t.handleInput('\b')
      expect(t.lineBuffer.value).toBe('ab')
      expect(t.cursorIndex.value).toBe(2)
    })

    it('handleInput backspace at cursor 0 is a no-op', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abc')
      t.cursorIndex.value = 0
      t.handleInput('\b')
      expect(t.lineBuffer.value).toBe('abc')
      expect(t.cursorIndex.value).toBe(0)
    })

    it('Ctrl+A / Ctrl+E move cursor to start / end', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abcde')
      t.cursorIndex.value = 2
      t.handleInput('\x01')
      expect(t.cursorIndex.value).toBe(0)
      t.handleInput('\x05')
      expect(t.cursorIndex.value).toBe(5)
    })

    it('Ctrl+K deletes from cursor to end of line', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abcdef')
      t.cursorIndex.value = 2
      t.handleInput('\x0b')
      expect(t.lineBuffer.value).toBe('ab')
      expect(t.cursorIndex.value).toBe(2)
    })

    it('Ctrl+U deletes from beginning to cursor', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('abcdef')
      t.cursorIndex.value = 4
      t.handleInput('\x15')
      expect(t.lineBuffer.value).toBe('ef')
      expect(t.cursorIndex.value).toBe(0)
    })

    it('Enter clears the local buffer', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('ls')
      t.handleInput('\r')
      expect(t.lineBuffer.value).toBe('')
      expect(t.cursorIndex.value).toBe(0)
    })

    it('isAtLineEnd reflects the char-array, not a stale string copy', () => {
      const t = useTerminalInput(null, { mode: 'ssh', sessionId: null })
      t.handleInput('ab')
      expect(t.isAtLineEnd()).toBe(true)
      t.cursorIndex.value = 1
      expect(t.isAtLineEnd()).toBe(false)
    })
  })

  describe('getCurrentCommandFromTerminal (cursor-row first scan)', () => {
    function makeInput(terminal: any, onExtract?: (cmd: string) => void) {
      return useTerminalInput(terminal, {
        mode: 'ssh',
        sessionId: 's1',
        enableHistory: onExtract !== undefined,
        onHistoryExtract: onExtract,
      })
    }

    it('extracts the command from the cursor row when present', () => {
      const extracted: string[] = []
      const t = makeInput(mkTerminal({
        cursorY: 3,
        lines: [
          'user@host:~$ git status',
          'On branch main',
          'nothing to commit, working tree clean',
          'user@host:~$ ls',
        ],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('ls')
      t.handleInput('\r')
      expect(extracted).toEqual(['ls'])
    })

    it('walks up from cursor row when the cursor row has no prompt', () => {
      const extracted: string[] = []
      const t = makeInput(mkTerminal({
        cursorY: 5,
        lines: [
          'user@host:~$ git status',
          'On branch main',
          'Changes to be committed:',
          '  modified: foo.ts',
          '  modified: bar.ts',
          'still working...',
        ],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('\r')
      expect(extracted).toEqual(['git status'])
    })

    it('stops walking once a prompt is found (does not scan the full visible area)', () => {
      const extracted: string[] = []
      // The prompt sits two rows above the cursor, buried between non-prompt
      // lines. The scanner must stop at the first prompt it finds, not keep
      // walking through the rest of the viewport.
      const t = makeInput(mkTerminal({
        cursorY: 10,
        lines: [
          'filler 1',
          '[root@node ~]# git log --oneline -5',
          'filler 2', 'filler 3', 'filler 4', 'filler 5',
          'filler 6', 'filler 7', 'filler 8',
          'filler 9 (just a blank echo)',
          '', // cursor row
        ],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('\r')
      expect(extracted).toEqual(['git log --oneline -5'])
    })

    it('returns null when no prompt is visible', () => {
      const extracted: string[] = []
      const t = makeInput(mkTerminal({
        cursorY: 0,
        rows: 5,
        lines: ['no prompt here', 'just some text', 'no prompt here either'],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('\r')
      expect(extracted).toEqual([])
    })

    it('joins wrapped continuation rows into the full command', () => {
      const extracted: string[] = []
      // A long command that overflows the panel width wraps onto following
      // rows (marked isWrapped). The history must reconstruct the whole
      // command, not just the first row's tail after the prompt.
      const t = makeInput(mkTerminal({
        cursorY: 5,
        lines: [
          'user@host:~$ echo aaaa',
          'bbbbbbbbbbbbbbbbbb',
          'cccccccccccccccccccc',
          'dddddddddddddddddd',
          'eeeeeeeeeeeeeeeeeeee',
        ],
        wrapped: [1, 2, 3, 4],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('\r')
      expect(extracted).toEqual([
        'echo aaaabbbbbbbbbbbbbbbbbbccccccccccccccccccccdddddddddddddddddd' +
        'eeeeeeeeeeeeeeeeeeee',
      ])
    })

    it('stops joining wrapped rows once a non-wrapped row is reached', () => {
      const extracted: string[] = []
      const t = makeInput(mkTerminal({
        cursorY: 4,
        lines: [
          'user@host:~$ cat foo',
          'bar',
          'zz',
        ],
        // row 1 is the wrap of the prompt command; row 2 is a fresh command
        // (not wrapped) and must NOT be appended.
        wrapped: [1],
      }), (cmd) => extracted.push(cmd))
      t.handleInput('\r')
      expect(extracted).toEqual(['cat foobar'])
    })
  })
})
