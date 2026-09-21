import { describe, it, expect, vi, beforeEach } from 'vitest'

// vitest runs in node by default and the project has no jsdom dep;
// stub the surface useTerminalMenu touches (window/document/MouseEvent).
if (typeof globalThis.window === 'undefined') {
  const g = globalThis as any
  g.window = {
    dispatchEvent: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    innerWidth: 1024,
    innerHeight: 768,
  }
  g.document = {
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }
}
class FakeMouseEvent {
  ctrlKey = false
  metaKey = false
  clientX = 0
  clientY = 0
  preventDefault() { /* noop */ }
  stopPropagation() { /* noop */ }
}
;(globalThis as any).MouseEvent = FakeMouseEvent

async function flushAsync() {
  for (let i = 0; i < 5; i++) await Promise.resolve()
}

const { mockClipboardSetText, mockSettingsStore } = vi.hoisted(() => ({
  mockClipboardSetText: vi.fn(),
  mockSettingsStore: {
    settings: { terminal: { rightClickAction: 'menu' } },
  },
}))

vi.mock('@wailsio/runtime', () => ({
  Clipboard: {
    Text: vi.fn().mockResolvedValue(''),
    SetText: (...args: unknown[]) => mockClipboardSetText(...args),
  },
}))

vi.mock('../stores/settingsStore', () => ({
  useSettingsStore: () => mockSettingsStore,
}))

import { useTerminalMenu } from './useTerminalMenu'
import { Clipboard } from '@wailsio/runtime'

function buildMenu(getSelection: () => string) {
  return useTerminalMenu({ getSelection, onPaste: vi.fn() })
}

function stubNavigatorWrite(writeText: ReturnType<typeof vi.fn>) {
  Object.defineProperty(globalThis.navigator, 'clipboard', {
    configurable: true,
    value: { writeText },
  })
}

describe('useTerminalMenu.writeClipboard', () => {
  let writeText: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockClipboardSetText.mockReset()
    mockSettingsStore.settings.terminal.rightClickAction = 'menu'
    writeText = vi.fn().mockResolvedValue(undefined)
    stubNavigatorWrite(writeText)
  })

  it('falls back to navigator.clipboard.writeText when Wails resolves false', async () => {
    mockClipboardSetText.mockResolvedValue(false)
    const m = buildMenu(() => 'hello')
    m.copySelection()
    await flushAsync()
    expect(mockClipboardSetText).toHaveBeenCalledWith('hello')
    expect(writeText).toHaveBeenCalledWith('hello')
  })

  it('does NOT call navigator.clipboard when Wails resolves true', async () => {
    mockClipboardSetText.mockResolvedValue(true)
    const m = buildMenu(() => 'hello')
    m.copySelection()
    await flushAsync()
    expect(mockClipboardSetText).toHaveBeenCalledWith('hello')
    expect(writeText).not.toHaveBeenCalled()
  })

  it('falls back to navigator.clipboard when Wails throws', async () => {
    mockClipboardSetText.mockRejectedValue(new Error('boom'))
    const m = buildMenu(() => 'hello')
    m.copySelection()
    await flushAsync()
    expect(mockClipboardSetText).toHaveBeenCalledWith('hello')
    expect(writeText).toHaveBeenCalledWith('hello')
  })

  it('opens menu on contextmenu when rightClickAction is "menu"', () => {
    const m = buildMenu(() => '')
    m.onContextMenu(new FakeMouseEvent() as any)
    expect(m.menuVisible.value).toBe(true)
  })

  it('dispatches to paste instead of showing menu when rightClickAction is "paste"', () => {
    mockSettingsStore.settings.terminal.rightClickAction = 'paste'
    const m = buildMenu(() => '')
    m.onContextMenu(new FakeMouseEvent() as any)
    expect(m.menuVisible.value).toBe(false)
  })

  // Regression: the Wails Clipboard import was dropped from useTerminalMenu,
  // so the bare `Clipboard` reference resolved to the DOM global (the Clipboard
  // API interface) and Clipboard.Text() threw inside the swallowed try/catch —
  // right-click paste did nothing while every test still stayed green. The
  // paste dispatch must actually reach onPaste through the Wails runtime.
  it('pastes clipboard text via onPaste when rightClickAction is "paste"', async () => {
    mockSettingsStore.settings.terminal.rightClickAction = 'paste'
    const paste = vi.fn()
    const m = useTerminalMenu({ getSelection: () => '', onPaste: paste })
    vi.mocked(Clipboard.Text).mockResolvedValueOnce('clipboard-content')
    m.onContextMenu(new FakeMouseEvent() as any)
    await flushAsync()
    expect(Clipboard.Text).toHaveBeenCalled()
    expect(paste).toHaveBeenCalledWith('clipboard-content')
    expect(m.menuVisible.value).toBe(false)
  })

  // Ctrl/Cmd + right-click is the escape hatch when right-click is bound to
  // paste: either modifier forces the context menu open.
  it.each([
    ['Ctrl', (e: FakeMouseEvent) => { e.ctrlKey = true }],
    ['Cmd/Meta', (e: FakeMouseEvent) => { e.metaKey = true }],
  ])('opens the menu on %s + right-click even when rightClickAction is "paste"', (_label, setModifier) => {
    mockSettingsStore.settings.terminal.rightClickAction = 'paste'
    const m = buildMenu(() => 'selected-text')
    const ev = new FakeMouseEvent()
    setModifier(ev)
    m.onContextMenu(ev as any)
    expect(m.menuVisible.value).toBe(true)
    expect(m.hasSelection.value).toBe(true)
  })

  it('openMenu opens the menu regardless of rightClickAction (middle-click "menu" path)', () => {
    // The middle-click "show menu" action must never fall through to paste,
    // even when right-click itself is bound to paste.
    mockSettingsStore.settings.terminal.rightClickAction = 'paste'
    const paste = vi.fn()
    const m = useTerminalMenu({ getSelection: () => '', onPaste: paste })
    m.openMenu(new FakeMouseEvent() as any)
    expect(m.menuVisible.value).toBe(true)
    expect(paste).not.toHaveBeenCalled()
  })
})

describe('useTerminalMenu.copySelection re-reads selection at click time', () => {
  let writeText: ReturnType<typeof vi.fn>
  beforeEach(() => {
    mockClipboardSetText.mockReset()
    mockSettingsStore.settings.terminal.rightClickAction = 'menu'
    writeText = vi.fn().mockResolvedValue(undefined)
    stubNavigatorWrite(writeText)
  })

  // WKWebView race: right-click mousedown can clear xterm selection between
  // contextmenu (where hasSelection is sampled) and the menu click. The
  // getSelection() snapshot at click time must be the source of truth.
  it('copies the fresh getSelection() value, ignoring stale hasSelection', async () => {
    let selection = 'initial-selection'
    const getSelection = vi.fn(() => selection)
    const m = useTerminalMenu({ getSelection, onPaste: vi.fn() })
    m.onContextMenu(new FakeMouseEvent() as any)
    expect(m.hasSelection.value).toBe(true)

    selection = ''
    getSelection.mockImplementation(() => selection)
    mockClipboardSetText.mockResolvedValue(true)
    m.copySelection()
    await flushAsync()

    expect(mockClipboardSetText).not.toHaveBeenCalled()
    expect(writeText).not.toHaveBeenCalled()
  })

  it('copies the fresh selection even when hasSelection was false at contextmenu', async () => {
    let selection = ''
    const getSelection = vi.fn(() => selection)
    const m = useTerminalMenu({ getSelection, onPaste: vi.fn() })
    m.onContextMenu(new FakeMouseEvent() as any)
    expect(m.hasSelection.value).toBe(false)

    selection = 'late-selection'
    getSelection.mockImplementation(() => selection)
    mockClipboardSetText.mockResolvedValue(true)
    m.copySelection()
    await flushAsync()

    expect(mockClipboardSetText).toHaveBeenCalledWith('late-selection')
    expect(writeText).not.toHaveBeenCalled()
  })
})
