import { describe, it, expect, vi } from 'vitest'
import {
  loadKeybindings, onGlobalKeydown, matchDigitShortcut, panelDigitShortcutsSuppressed,
  tabDigitShortcutPrefix, panelDigitShortcutPrefix, formatDigitShortcut, formatKeyBinding,
  digitModifierCollides, isRebinding, setRebinding,
} from './useKeyboardShortcuts'
import { DEFAULT_KEYBOARD } from '../types/settings'
import type { KeyboardSettings } from '../types/settings'

function fakeKey(partial: Partial<{ ctrlKey: boolean; metaKey: boolean; shiftKey: boolean; altKey: boolean; key: string; isComposing: boolean; keyCode: number }>): KeyboardEvent {
  return {
    ctrlKey: false, metaKey: false, shiftKey: false, altKey: false, key: '',
    isComposing: false, keyCode: 0,
    preventDefault() {}, stopPropagation() {},
    ...partial,
  } as any
}

describe('useKeyboardShortcuts — font zoom bindings', () => {
  it('fires the handler on Ctrl+= (zoom in)', () => {
    const zoomFontIn = vi.fn()
    loadKeybindings(
      { zoomFontIn: { ctrl: true, shift: false, alt: false, key: '=' } } as Particle<KeyboardSettings>,
      { zoomFontIn } as any,
    )
    onGlobalKeydown(fakeKey({ ctrlKey: true, key: '=' }))
    expect(zoomFontIn).toHaveBeenCalledTimes(1)
  })

  it('mirrors Ctrl+= to Meta+= (issue #614 ⌘ zoom)', () => {
    const zoomFontIn = vi.fn()
    loadKeybindings(
      { zoomFontIn: { ctrl: true, shift: false, alt: false, key: '=' } } as Particle<KeyboardSettings>,
      { zoomFontIn } as any,
    )
    onGlobalKeydown(fakeKey({ metaKey: true, key: '=' }))
    expect(zoomFontIn).toHaveBeenCalledTimes(1)
  })

  it('fires the handler on Ctrl+- (zoom out) but not on the raw "=" key alone', () => {
    const zoomFontOut = vi.fn()
    loadKeybindings(
      { zoomFontOut: { ctrl: true, shift: false, alt: false, key: '-' } } as Particle<KeyboardSettings>,
      { zoomFontOut } as any,
    )
    onGlobalKeydown(fakeKey({ ctrlKey: true, key: '-' }))
    expect(zoomFontOut).toHaveBeenCalledTimes(1)
    onGlobalKeydown(fakeKey({ key: '=' }))
    expect(zoomFontOut).toHaveBeenCalledTimes(1) // no modifier → unharmed
  })

  it('does not fire when the active modifiers do not match the binding', () => {
    const zoomFontIn = vi.fn()
    loadKeybindings(
      { zoomFontIn: { ctrl: true, shift: false, alt: false, key: '=' } } as Particle<KeyboardSettings>,
      { zoomFontIn } as any,
    )
    onGlobalKeydown(fakeKey({ ctrlKey: true, shiftKey: true, key: '=' }))
    expect(zoomFontIn).not.toHaveBeenCalled()
  })
})

type Particle<T> = Partial<{ [K in keyof T]?: T[K] }>

describe('useKeyboardShortcuts — quick commands', () => {
  it('fires the quick-command handler on Ctrl+Shift+M and mirrors it to Cmd on mac', () => {
    const openQuickCommands = vi.fn()
    loadKeybindings(
      DEFAULT_KEYBOARD,
      { openQuickCommands } as any,
    )

    onGlobalKeydown(fakeKey({ ctrlKey: true, shiftKey: true, key: 'm' }))
    expect(openQuickCommands).toHaveBeenCalledTimes(1)
    onGlobalKeydown(fakeKey({ metaKey: true, shiftKey: true, key: 'm' }))
    expect(openQuickCommands).toHaveBeenCalledTimes(2)
    onGlobalKeydown(fakeKey({ key: 'm' }))
    expect(openQuickCommands).toHaveBeenCalledTimes(2) // bare key → unharmed
  })
})

describe('useKeyboardShortcuts — maximize panel', () => {
  it('fires the maximize handler on Ctrl+Shift+Enter (default) and mirrors it to Cmd on mac', () => {
    const maximizePanel = vi.fn()
    loadKeybindings(
      DEFAULT_KEYBOARD,
      { maximizePanel } as any,
    )

    onGlobalKeydown(fakeKey({ ctrlKey: true, shiftKey: true, key: 'Enter' }))
    expect(maximizePanel).toHaveBeenCalledTimes(1)
    onGlobalKeydown(fakeKey({ metaKey: true, shiftKey: true, key: 'Enter' }))
    expect(maximizePanel).toHaveBeenCalledTimes(2)
    onGlobalKeydown(fakeKey({ key: 'Enter' }))
    expect(maximizePanel).toHaveBeenCalledTimes(2) // bare Enter → unharmed
  })
})

describe('rebinding flag', () => {
  it('toggles so runtime handlers can stand down while capturing keys', () => {
    expect(isRebinding()).toBe(false)
    setRebinding(true)
    expect(isRebinding()).toBe(true)
    setRebinding(false)
    expect(isRebinding()).toBe(false)
  })
})

describe('matchDigitShortcut — configurable tab-switch modifier', () => {
  const alt = { ctrl: false, shift: false, alt: true, key: '' }
  const ctrlAlt = { ctrl: true, shift: false, alt: true, key: '' }
  const none = { ctrl: false, shift: false, alt: false, key: '' }

  it('keeps the fixed platform bindings when unset', () => {
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '1' }), false, undefined)).toBe('tab')
    expect(matchDigitShortcut(fakeKey({ metaKey: true, key: '1' }), true, undefined)).toBe('tab')
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), false, undefined)).toBe('panel')
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), true, undefined)).toBe('panel')
  })

  it('moves tab switching to the configured modifier (Alt)', () => {
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '3' }), false, alt)).toBe('tab')
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '3' }), false, alt)).toBe(null)
  })

  it('suppresses workspace panels only for the plain Alt combo', () => {
    expect(panelDigitShortcutsSuppressed(alt)).toBe(true)
    expect(panelDigitShortcutsSuppressed(undefined)).toBe(false)
    expect(panelDigitShortcutsSuppressed(none)).toBe(false)
    // Ctrl+Alt+digits for tabs leaves plain Alt+digits to the panels.
    expect(panelDigitShortcutsSuppressed(ctrlAlt)).toBe(false)
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), false, ctrlAlt)).toBe('panel')
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, altKey: true, key: '2' }), false, ctrlAlt)).toBe('tab')
  })

  it('a cleared modifier disables digit tab switching entirely', () => {
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '1' }), false, none)).toBe(null)
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '1' }), false, none)).toBe('panel')
  })

  it('requires the modifiers to match exactly', () => {
    expect(matchDigitShortcut(fakeKey({ altKey: true, shiftKey: true, key: '1' }), false, alt)).toBe(null)
    expect(matchDigitShortcut(fakeKey({ altKey: true, ctrlKey: true, key: '1' }), false, alt)).toBe(null)
  })

  it('badges follow the configured modifier and hide suppressed panels', () => {
    expect(tabDigitShortcutPrefix(false, undefined)).toBe('Ctrl')
    expect(tabDigitShortcutPrefix(true, undefined)).toBe('⌘')
    expect(tabDigitShortcutPrefix(false, alt)).toBe('Alt')
    expect(tabDigitShortcutPrefix(true, alt)).toBe('⌥')
    expect(tabDigitShortcutPrefix(false, ctrlAlt)).toBe('Ctrl+Alt')
    expect(tabDigitShortcutPrefix(false, none)).toBe('')
  })
})

describe('matchDigitShortcut — configurable panel-switch modifier', () => {
  const ctrl = { ctrl: true, shift: false, alt: false, key: '' }
  const ctrlShift = { ctrl: true, shift: true, alt: false, key: '' }
  const none = { ctrl: false, shift: false, alt: false, key: '' }

  it('keeps the fixed Alt/Option binding when unset', () => {
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), false, undefined, undefined)).toBe('panel')
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), true, undefined, undefined)).toBe('panel')
  })

  it('moves panel switching to the configured modifier', () => {
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, shiftKey: true, key: '4' }), false, undefined, ctrlShift)).toBe('panel')
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '4' }), false, undefined, ctrlShift)).toBe(null)
  })

  it('the tab-switch modifier wins when both target the same combo', () => {
    // The default tab combo is Ctrl/Cmd, so a Ctrl-only panel modifier collides.
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '5' }), false, undefined, ctrl)).toBe('tab')
    // Clearing the tab modifier hands Ctrl+digits to the panels.
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '5' }), false, none, ctrl)).toBe('panel')
  })

  it('a cleared panel modifier disables panel digit switching entirely', () => {
    expect(matchDigitShortcut(fakeKey({ altKey: true, key: '2' }), false, undefined, none)).toBe(null)
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '2' }), false, undefined, none)).toBe('tab')
  })

  it('treats Ctrl and Cmd as the same modifier on macOS', () => {
    // Default: Cmd+1 and Ctrl+1 both switch tabs on mac.
    expect(matchDigitShortcut(fakeKey({ metaKey: true, key: '1' }), true, undefined, undefined)).toBe('tab')
    expect(matchDigitShortcut(fakeKey({ ctrlKey: true, key: '1' }), true, undefined, undefined)).toBe('tab')
    // A configured Ctrl combo also answers to Cmd on mac.
    expect(matchDigitShortcut(fakeKey({ metaKey: true, shiftKey: true, key: '4' }), true, undefined, ctrlShift)).toBe('panel')
    // …and a Ctrl-only panel modifier collides with the mac default tabs too.
    expect(matchDigitShortcut(fakeKey({ metaKey: true, key: '5' }), true, undefined, ctrl)).toBe('tab')
  })
})

describe('panelDigitShortcutsSuppressed — panel modifier collisions', () => {
  const ctrl = { ctrl: true, shift: false, alt: false, key: '' }
  const ctrlShift = { ctrl: true, shift: true, alt: false, key: '' }

  it('is true when the panel modifier equals the effective tab combo', () => {
    // The default tab combo is Ctrl/Cmd (unified on mac), so a Ctrl-only
    // panel modifier collides on every platform.
    expect(panelDigitShortcutsSuppressed(undefined, ctrl)).toBe(true)
  })

  it('is false for distinct combos and the default Alt binding', () => {
    expect(panelDigitShortcutsSuppressed(undefined, undefined)).toBe(false)
    expect(panelDigitShortcutsSuppressed(undefined, ctrlShift)).toBe(false)
  })
})

describe('digitModifierCollides — mutual exclusion of the two digit families', () => {
  const ctrl = { ctrl: true, shift: false, alt: false, key: '' }
  const ctrlShift = { ctrl: true, shift: true, alt: false, key: '' }
  const alt = { ctrl: false, shift: false, alt: true, key: '' }
  const none = { ctrl: false, shift: false, alt: false, key: '' }
  // Platform defaults: tabs = Ctrl/Cmd, panels = Alt/Option.
  const tabDefault = { ctrl: true, shift: false, alt: false, key: '' }
  const panelDefault = { ctrl: false, shift: false, alt: true, key: '' }

  it('an unset other family counts as its own platform default', () => {
    // Setting panels to Ctrl collides with the tabs' Ctrl/Cmd default…
    expect(digitModifierCollides(undefined, tabDefault, ctrl)).toBe(true)
    // …but setting tabs to Ctrl does NOT collide with the panels' Alt default.
    expect(digitModifierCollides(undefined, panelDefault, ctrl)).toBe(false)
    // Setting tabs to Alt collides with the panels' Alt default…
    expect(digitModifierCollides(undefined, panelDefault, alt)).toBe(true)
    // …while setting panels to Alt does not collide with the tabs' default.
    expect(digitModifierCollides(undefined, tabDefault, alt)).toBe(false)
  })

  it('a configured other family collides only on equal flags', () => {
    expect(digitModifierCollides(alt, tabDefault, alt)).toBe(true)
    expect(digitModifierCollides(ctrlShift, panelDefault, ctrl)).toBe(false)
  })

  it('a disabled (cleared) other family never collides', () => {
    expect(digitModifierCollides(none, tabDefault, ctrl)).toBe(false)
  })
})

describe('digit shortcut badges', () => {
  const ctrl = { ctrl: true, shift: false, alt: false, key: '' }
  const none = { ctrl: false, shift: false, alt: false, key: '' }

  it('panel badge follows the configured modifier', () => {
    expect(panelDigitShortcutPrefix(false, undefined)).toBe('Alt')
    expect(panelDigitShortcutPrefix(true, undefined)).toBe('⌥')
    expect(panelDigitShortcutPrefix(false, ctrl)).toBe('Ctrl')
    expect(panelDigitShortcutPrefix(true, ctrl)).toBe('⌘')
    expect(panelDigitShortcutPrefix(false, none)).toBe('')
  })

  it('renders word prefixes with a separating plus, mac symbols without', () => {
    expect(formatDigitShortcut('Ctrl', 1, false)).toBe('Ctrl+1')
    expect(formatDigitShortcut('Ctrl+Alt', 3, false)).toBe('Ctrl+Alt+3')
    expect(formatDigitShortcut('⌘', 1, true)).toBe('⌘1')
    expect(formatDigitShortcut('⌃⌥', 2, true)).toBe('⌃⌥2')
    expect(formatDigitShortcut('', 1, false)).toBe('')
  })

  it('defaults openQuickCommands to Ctrl+Shift+M', () => {
    expect(DEFAULT_KEYBOARD.openQuickCommands).toEqual({ ctrl: true, shift: true, alt: false, key: 'm' })
  })
})

describe('formatKeyBinding — macOS symbol display', () => {
  it('renders mac symbols for modifiers and keys on macOS, ctrl shown as ⌘ (the Cmd mirror)', () => {
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: 'm' }, true)).toBe('⌘⇧M')
    expect(formatKeyBinding({ ctrl: true, shift: false, alt: true, key: 'arrowleft' }, true)).toBe('⌘⌥←')
    expect(formatKeyBinding({ ctrl: false, shift: false, alt: true, key: '2' }, true)).toBe('⌥2')
    expect(formatKeyBinding({ ctrl: true, shift: false, alt: false, key: ',' }, true)).toBe('⌘,')
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: 'enter' }, true)).toBe('⌘⇧↩')
  })

  it('capitalizes key names on Windows/Linux', () => {
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: 'm' }, false)).toBe('Ctrl+Shift+M')
    expect(formatKeyBinding({ ctrl: false, shift: false, alt: true, key: 'arrowleft' }, false)).toBe('Alt+ArrowLeft')
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: 'enter' }, false)).toBe('Ctrl+Shift+Enter')
    expect(formatKeyBinding({ ctrl: true, shift: false, alt: false, key: 'space' }, false)).toBe('Ctrl+Space')
    expect(formatKeyBinding({ ctrl: true, shift: false, alt: false, key: 'tab' }, false)).toBe('Ctrl+Tab')
  })

  it('displays the literal space character (e.key of the spacebar) as Space', () => {
    // The rebind capture stores the raw e.key, which for the spacebar is ' '.
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: ' ' }, false)).toBe('Ctrl+Shift+Space')
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: ' ' }, true)).toBe('⌘⇧␣')
  })

  it('handles a modifier-only binding (empty key) for the digit settings rows', () => {
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: '' }, true)).toBe('⌘⇧')
    expect(formatKeyBinding({ ctrl: true, shift: true, alt: false, key: '' }, false)).toBe('Ctrl+Shift+')
  })
})
