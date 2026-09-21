import { describe, it, expect, vi } from 'vitest'

vi.mock('@xterm/xterm', () => ({
  Terminal: class {},
}))
vi.mock('@xterm/addon-fit', () => ({
  FitAddon: class {
    fit() {}
  },
}))
vi.mock('@xterm/addon-unicode11', () => ({
  Unicode11Addon: class {},
}))
vi.mock('@xterm/addon-search', () => ({
  SearchAddon: class {},
}))
vi.mock('@xterm/addon-clipboard', () => ({
  ClipboardAddon: class {},
  Base64: class {},
}))
vi.mock('@xterm/addon-progress', () => ({
  ProgressAddon: class {
    // IEvent: called as a function, returns a disposable.
    onChange = () => ({ dispose() {} })
  },
}))
vi.mock('../composables/useTerminal', () => ({
  getXtermTheme: () => ({}),
}))
vi.mock('../stores/settingsStore', () => ({
  useSettingsStore: () => ({
    settings: { terminal: { fontFamily: 'monospace', fontSize: 14, scrollback: 1000 } },
  }),
}))
vi.mock('../stores/localStateStore', () => ({
  useLocalStateStore: () => ({
    state: { sessionLogStates: {} },
    setSessionLogState: () => {},
  }),
}))

import { getTerminalSize, waitForTerminalSize } from './terminalManager'

describe('terminalManager sizing helpers', () => {
  it('getTerminalSize returns 0,0 for an unknown session id', () => {
    const size = getTerminalSize('does-not-exist')
    expect(size).toEqual({ cols: 0, rows: 0 })
  })

  it('waitForTerminalSize resolves to 0,0 after the timeout when no terminal mounts', async () => {
    const start = Date.now()
    const size = await waitForTerminalSize('still-missing', 120)
    const elapsed = Date.now() - start
    expect(size).toEqual({ cols: 0, rows: 0 })
    expect(elapsed).toBeGreaterThanOrEqual(100)
  })
})
