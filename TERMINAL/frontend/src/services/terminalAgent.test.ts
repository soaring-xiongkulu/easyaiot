import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Use vi.hoisted to allow factory references to variables defined at top level
const { mockSessionWrite } = vi.hoisted(() => {
  const mockSessionWrite = vi.fn().mockResolvedValue(undefined)
  return { mockSessionWrite }
})

// ---- mock wailsjs modules ----
import { Events } from '@wailsio/runtime'
vi.mock('@wailsio/runtime', () => ({
  Events: { On: vi.fn(() => () => {}), Off: vi.fn() },
}))

vi.mock('../../bindings/easyaiot/terminal/app', () => ({
  SessionWrite: mockSessionWrite,
}))

vi.mock('../services/sessionWriter', () => ({
  queuedSessionWrite: (...args: any[]) => mockSessionWrite(...args),
}))

// ---- mock terminal manager (prompt-line capture + screen-buffer reads) ----
// The fake terminal exposes a scripted screen buffer: `fakeScreen` models the
// buffer rows xterm.js would hold after parsing the PTY stream. Tests set it
// to the *final* screen state while feeding raw (possibly redraw-heavy) data
// through the session:data events.
const PROMPT = '[root@node140 ~]#'

let fakeScreen: string[] = [PROMPT + ' ']
let fakeBufferType: 'normal' | 'alternate' = 'normal'

function setFakeScreen(lines: string[], type: 'normal' | 'alternate' = 'normal') {
  fakeScreen = lines
  fakeBufferType = type
}

function makeFakeTerminal() {
  const screen = fakeScreen
  const type = fakeBufferType
  return {
    rows: screen.length,
    buffer: {
      active: {
        type,
        baseY: 0,
        cursorY: 0,
        length: screen.length,
        getLine: (n: number) => {
          if (n < 0 || n >= screen.length) return undefined
          return {
            translateToString: (trim?: boolean) =>
              trim ? screen[n].replace(/\s+$/, '') : screen[n],
          }
        },
      },
    },
  }
}

const mockGetManagedTerminal = vi.fn(() => ({
  terminal: makeFakeTerminal(),
  lineOffset: 0,
}))
vi.mock('../services/terminalManager', () => ({
  getManagedTerminal: (...args: any[]) => mockGetManagedTerminal(...(args as [])),
}))

// ---- mock pinia stores ----
const mockPanel = {
  sessionId: 'test-session-id',
  config: { shellPath: '/bin/bash' },
}
const mockGetPanel = vi.fn().mockReturnValue(mockPanel)
const mockGetAILockedPanel = vi.fn().mockReturnValue(null)
const mockGetAILockedPanels = vi.fn().mockReturnValue([])

const mockActiveTab: { type: string; panelId: string } = {
  type: 'terminal',
  panelId: 'panel-1',
}
const mockTabStore = {
  getAILockedPanel: mockGetAILockedPanel,
  getAILockedPanels: mockGetAILockedPanels,
  activeTab: mockActiveTab,
}
const mockPanelStore = {
  getPanel: mockGetPanel,
}

vi.mock('../stores/tabStore', () => ({
  useTabStore: vi.fn(() => mockTabStore),
}))
vi.mock('../stores/panelStore', () => ({
  usePanelStore: vi.fn(() => mockPanelStore),
}))
const mockGetRemoteOS = vi.fn().mockReturnValue(undefined)
const mockSessionStore = {
  getRemoteOS: mockGetRemoteOS,
}
vi.mock('../stores/sessionStore', () => ({
  useSessionStore: vi.fn(() => mockSessionStore),
}))

// ---- import after mocks ----
import { watchOutput, executeCommand, truncateOutput, startCommand, sendTerminalKey } from './terminalAgent'
import type { ExecuteResult, WatchResult } from './terminalAgent'
// ---- helpers ----
const MOCK_TIMESTAMP = 1700000000000

function fakeData(sessionId: string, data: string) {
  return { id: sessionId, data }
}

function withMockedTime() {
  const originalNow = Date.now
  const originalRandom = Math.random
  Date.now = vi.fn(() => MOCK_TIMESTAMP)
  Math.random = vi.fn(() => 0)
  return () => {
    Date.now = originalNow
    Math.random = originalRandom
  }
}

describe('truncateOutput', () => {
  it('returns full text when lines <= threshold', () => {
    const text = 'line1\nline2\nline3'
    const result = truncateOutput(text, 2, 2)
    expect(result).toBe(text)
  })

  it('truncates middle when lines > threshold', () => {
    const lines = Array.from({ length: 20 }, (_, i) => `line${i + 1}`)
    const text = lines.join('\n')
    const result = truncateOutput(text, 2, 3)

    expect(result).toContain('line1')
    expect(result).toContain('line2')
    expect(result).not.toContain('line3')
    expect(result).not.toContain('line17')
    expect(result).toContain('line18')
    expect(result).toContain('line19')
    expect(result).toContain('line20')
    expect(result).toContain('TRUNCATED')
    expect(result).toContain('omitted')
  })

  it('handles edge case: headLines=0', () => {
    const lines = Array.from({ length: 10 }, (_, i) => `line${i + 1}`)
    const text = lines.join('\n')
    const result = truncateOutput(text, 0, 2)

    expect(result).toContain('omitted')
    expect(result).toContain('line9')
    expect(result).toContain('line10')
  })

  it('handles edge case: tailLines=0', () => {
    const lines = Array.from({ length: 10 }, (_, i) => `line${i + 1}`)
    const text = lines.join('\n')
    const result = truncateOutput(text, 3, 0)

    expect(result).toContain('line1')
    expect(result).toContain('line3')
    expect(result).toContain('omitted')
  })

  it('handles single line input', () => {
    const result = truncateOutput('single', 1, 1)
    expect(result).toBe('single')
  })

  it('handles empty string', () => {
    const result = truncateOutput('', 1, 1)
    expect(result).toBe('')
  })
})

describe('ExecuteResult interface', () => {
  it('has optional timedOut field', () => {
    const result: ExecuteResult = {
      output: 'test',
      exitCode: 0,
      timedOut: false,
    }
    expect(result.timedOut).toBe(false)

    const result2: ExecuteResult = {
      output: 'test',
      exitCode: -1,
      timedOut: true,
    }
    expect(result2.timedOut).toBe(true)

    const result3: ExecuteResult = {
      output: 'test',
      exitCode: 0,
    }
    expect(result3.timedOut).toBeUndefined()
  })
})

describe('watchOutput', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setFakeScreen([PROMPT + ' '])
  })

  it('returns promise and cleanup', () => {
    const result = watchOutput('session-1', PROMPT, 1000)
    expect(result.promise).toBeInstanceOf(Promise)
    expect(typeof result.cleanup).toBe('function')
  })

  it('resolves when the prompt line reappears after the command', async () => {
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', PROMPT, 5000, undefined, 0)

    // Final screen state after the command: echoed command, output, new prompt.
    setFakeScreen([`${PROMPT} echo hi`, 'hi', `${PROMPT} `])

    // Echoed command line, then output, then the prompt returns.
    capturedCallback!({ data: fakeData('s1', `${PROMPT} echo hi\nhi\n${PROMPT} `) })

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(false)
    expect(result.output).toContain('hi')
    // The reappeared prompt line is stripped: output ends at the last output
    // line, not with a trailing prompt.
    expect(result.output).not.toMatch(/\[root@node140 ~\]#\s*$/)
  })

  it('captures the final screen state, not raw ConPTY redraw frames (issue 624)', async () => {
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', PROMPT, 5000, undefined, 0)

    // What the user actually sees on screen after the command completes.
    setFakeScreen([
      `${PROMPT} reg query X`,
      'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server',
      `${PROMPT} `,
    ])

    // Windows Server 2016 ConPTY redraws a wrapping line by moving the cursor
    // left (ESC[nD) and re-emitting progressively shorter tails — the raw
    // stream is full of intermediate redraw frames the screen never shows.
    const redrawFragments = [
      'Server\\WinStation\\SYSTEM\\CurrentControlSet\\Control\\Terminal',
      'Server\\WinStationSYSTEM\\CurrentControlSet\\Control\\Terminal',
      'Server\\WinStationYSTEM\\CurrentControlSet\\Control\\Terminal',
      'Server\\WinStationM\\CurrentControlSet\\Control\\Terminal',
      'Server\\WinStationtControlSet\\Control\\Terminal',
    ].join('\r\n')
    capturedCallback!({
      data: fakeData(
        's1',
        `${PROMPT} reg query X\r\n${redrawFragments}\r\nHKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\r\n${PROMPT} `
      ),
    })

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(false)
    expect(result.output).toBe(
      `${PROMPT} reg query X\nHKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server`
    )
    // None of the redraw fragments may leak into the AI-visible output.
    expect(result.output).not.toContain('WinStation')
  })

  it('resolves via idle heuristic when prompt differs (e.g. dynamic prompt)', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', PROMPT, 5000)

    setFakeScreen([`${PROMPT} echo hi`, 'hi', '[user@host ~]$ '])
    capturedCallback!({ data: fakeData('s1', `${PROMPT} echo hi\nhi\n[user@host ~]$ `) })
    vi.advanceTimersByTime(800)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(false)
    expect(result.output).toContain('hi')
    vi.useRealTimers()
  })

  it('does not resolve on the initial prompt alone', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', PROMPT, 1000)

    // Only the prompt so far (no echoed command line before it) → keep waiting.
    capturedCallback!({ data: fakeData('s1', `${PROMPT} `) })
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(true)
    vi.useRealTimers()
  })

  it('never resolves early when promptLine is empty (timeout only)', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', '', 1000)

    // Even output that looks like a prompt must not trigger detection.
    setFakeScreen([`${PROMPT} echo hi`, 'hi', `${PROMPT} `])
    capturedCallback!({ data: fakeData('s1', `${PROMPT} echo hi\nhi\n${PROMPT} `) })
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(true)
    expect(result.output).toContain('hi')
    vi.useRealTimers()
  })

  it('times out after timeoutMs', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const { promise } = watchOutput('s1', PROMPT, 1000)

    setFakeScreen(['partial output'])
    capturedCallback!({ data: fakeData('s1', 'partial output') })
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: WatchResult = await promise
    expect(result.timedOut).toBe(true)
    expect(result.output).toContain('partial output')
    vi.useRealTimers()
  })

  it('ignores events from different sessions', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    setFakeScreen([''])
    const { promise } = watchOutput('s1', PROMPT, 1000)

    capturedCallback!({ data: fakeData('s2', 'wrong session data') })
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: WatchResult = await promise
    expect(result.output).toBe('')
    vi.useRealTimers()
  })

  it('cleanup prevents resolution', async () => {
    vi.useFakeTimers()
    vi.mocked(Events.On).mockImplementation((_eventName, _callback) => {
      return () => { }
    })

    const { promise, cleanup } = watchOutput('s1', PROMPT, 1000)
    cleanup()

    // Should not resolve/resolve with undefined after cleanup
    let resolved = false
    promise.then(() => { resolved = true }).catch(() => { resolved = true })
    vi.advanceTimersByTime(2000)
    // After cleanup, the promise should not settle via the normal path
    // (it's prevented by the resolved flag)
    expect(resolved).toBe(false)
    vi.useRealTimers()
  })
})

describe('executeCommand', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(Events.On).mockReturnValue(() => {})
    vi.mocked(mockSessionWrite).mockClear()
    vi.mocked(mockGetPanel).mockReturnValue(mockPanel)
    vi.mocked(mockGetAILockedPanel).mockReturnValue(null)
    vi.mocked(mockGetAILockedPanels).mockReturnValue([])
    vi.mocked(mockGetRemoteOS).mockReturnValue(undefined)
    mockActiveTab.type = 'terminal'
    mockActiveTab.panelId = 'panel-1'
    setFakeScreen([PROMPT + ' '])
  })

  // A failing assertion inside a fake-timer test must not leak fake timers
  // into the next test (settle timers would never fire and it would hang).
  afterEach(() => {
    vi.useRealTimers()
  })

  it('throws when no active session', async () => {
    vi.mocked(mockGetPanel).mockReturnValue(null)
    mockActiveTab.type = 'settings' // not terminal, not workspace

    await expect(executeCommand('ls')).rejects.toThrow('No active terminal session')
  })

  it('sends the command with no injected marker', async () => {
    const restore = withMockedTime()

    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => {}
    })

    const cmdPromise = executeCommand('echo hello')

    // Should have written to session — command only, no marker echo appended.
    expect(mockSessionWrite).toHaveBeenCalledOnce()
    const writtenArg = mockSessionWrite.mock.calls[0][1]
    expect(writtenArg).toContain('echo hello')
    expect(writtenArg).not.toContain('__AI_DONE_')
    expect(writtenArg).not.toContain('echo "')

    // Wait for async EventsOn to fire (inside Promise constructor = microtask)
    await Promise.resolve()
    expect(capturedCallback).not.toBeNull()

    // Prompt reappears after the echoed command + output → completion.
    setFakeScreen([`${PROMPT} echo hello`, 'hello', `${PROMPT} `])
    capturedCallback!({ data: fakeData('test-session-id', `${PROMPT} echo hello\nhello\n${PROMPT} `) })

    const result = await cmdPromise
    expect(result.exitCode).toBe(0)
    expect(result.timedOut).toBe(false)
    expect(typeof result.output).toBe('string')

    restore()
  }, 10000)

  it('sends CR newline (not LF) and no leading space for Windows OpenSSH', async () => {
    vi.mocked(mockGetRemoteOS).mockReturnValue('windows-openssh')
    const restore = withMockedTime()

    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => {}
    })

    const cmdPromise = executeCommand('dir')

    expect(mockSessionWrite).toHaveBeenCalledOnce()
    const writtenArg = mockSessionWrite.mock.calls[0][1] as string
    expect(writtenArg).toBe('dir\r') // CR terminator, no leading space

    await Promise.resolve()
    capturedCallback!({ data: fakeData('test-session-id', `${PROMPT} dir\r\n${PROMPT} `) })
    await cmdPromise

    restore()
  }, 10000)

  it('returns timedOut=true on timeout', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const cmdPromise = executeCommand('long-command', 1000, 2, 2)

    // Wait for async EventsOn to capture the callback
    await Promise.resolve()
    expect(capturedCallback).not.toBeNull()

    // Command still running at timeout: screen holds the output lines so far
    // (no trailing prompt row yet). Five lines so head=2/tail=2 keeps
    // line1+line2 and line4+line5.
    setFakeScreen(['line1', 'line2', 'line3', 'line4', 'line5'])
    capturedCallback!({ data: fakeData('test-session-id', 'some output line1\nline2\nline3\nline4\nline5') })
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result: ExecuteResult = await cmdPromise
    expect(result.exitCode).toBe(-1)
    expect(result.timedOut).toBe(true)
    expect(result.output).toContain('TRUNCATED')
    expect(result.output).toContain('line1')
    expect(result.output).toContain('line2')
    expect(result.output).toContain('line4')
    expect(result.output).toContain('line5')
    expect(result.output).not.toContain('line3') // truncated middle
    vi.useRealTimers()
  })

  it('truncates long output on success path', async () => {
    const restore = withMockedTime()

    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const lines = Array.from({ length: 10 }, (_, i) => `line${i + 1}`)
    const output = lines.join('\n')

    // headLines=3 so the head keeps the echoed command line + line1 + line2.
    const cmdPromise = executeCommand('some-cmd', 5000, 3, 3)

    // Wait for async EventsOn to capture the callback
    await Promise.resolve()
    expect(capturedCallback).not.toBeNull()

    // Echoed command + long output + returning prompt on the final screen.
    setFakeScreen([`${PROMPT} some-cmd`, ...lines, `${PROMPT} `])
    // Echoed command + long output + returning prompt triggers completion.
    capturedCallback!({ data: fakeData('test-session-id', `${PROMPT} some-cmd\n` + output + `\n${PROMPT} `) })

    const result: ExecuteResult = await cmdPromise
    expect(result.exitCode).toBe(0)
    expect(result.timedOut).toBe(false)
    expect(result.output).toContain('TRUNCATED')
    // headLines=3 keeps the echoed command line + line1 + line2. The trailing
    // prompt that reappeared on completion is stripped before truncation, so
    // tailLines=3 now keeps line8 + line9 + line10 (line8 was previously
    // omitted because the returning prompt occupied one tail slot).
    expect(result.output).toContain('line1')
    expect(result.output).toContain('line2')
    expect(result.output).toContain('line8')
    expect(result.output).toContain('line9')
    expect(result.output).toContain('line10')
    // The reappeared prompt must not leak into the returned output.
    expect(result.output).not.toMatch(/\n\[root@node140 ~\]#\s*$/)

    restore()
  })
})

describe('startCommand', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(Events.On).mockReturnValue(() => {})
    setFakeScreen([PROMPT + ' '])
  })

  it('returns the screen content collected during the window', async () => {
    vi.useFakeTimers()

    const p = startCommand('tail -f app.log')

    // startCommand awaits SessionWrite before subscribing/scheduling — flush.
    await Promise.resolve()

    // Output streams in during the 3s collect window and lands on screen.
    setFakeScreen([`${PROMPT} tail -f app.log`, 'log line A', 'log line B'])
    vi.advanceTimersByTime(3000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result = await p
    expect(result.started).toBe(true)
    expect(result.output).toContain('log line A')
    expect(result.output).toContain('log line B')
    vi.useRealTimers()
  })

  it('returns the final screen state even when the stream carries redraw frames', async () => {
    vi.useFakeTimers()
    let capturedCallback: ((payload: { id: string; data: string }) => void) | null = null
    vi.mocked(Events.On).mockImplementation((_eventName, callback) => {
      capturedCallback = callback
      return () => { }
    })

    const p = startCommand('cmd-with-redraws')
    await Promise.resolve() // flush the SessionWrite await inside startCommand

    setFakeScreen([`${PROMPT} cmd-with-redraws`, 'final state only'])
    capturedCallback!({
      data: fakeData('test-session-id', 'frame1\rframe2\rframe3\r\nfinal state only'),
    })
    vi.advanceTimersByTime(3000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result = await p
    expect(result.output).toBe(`${PROMPT} cmd-with-redraws\nfinal state only`)
    expect(result.output).not.toContain('frame1')
    vi.useRealTimers()
  })
})

describe('sendTerminalKey', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(Events.On).mockReturnValue(() => {})
    setFakeScreen([PROMPT + ' '])
  })

  it('captures the screen response after ctrl_c', async () => {
    vi.useFakeTimers()

    const p = sendTerminalKey(undefined, 'ctrl_c', true)
    await Promise.resolve() // flush the SessionWrite await inside sendTerminalKey

    // The interrupted program stops and the shell prompt returns.
    setFakeScreen([`${PROMPT} ^C`, `${PROMPT} `])
    vi.advanceTimersByTime(1000)
    vi.advanceTimersByTime(100) // screen-read settle delay

    const result = await p
    expect(result.output).toContain('^C')
    vi.useRealTimers()
  })
})
