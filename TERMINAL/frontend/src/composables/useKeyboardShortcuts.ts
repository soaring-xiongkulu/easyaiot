import type { KeyboardSettings, KeyBinding, ShortcutAction } from '../types/settings'

type ActionHandlers = Record<ShortcutAction, () => void>

// Symbols for special key names in the macOS display style (⌃⌥2, ⇧↩ …).
const MAC_KEY_SYMBOLS: Record<string, string> = {
  tab: '⇥',
  enter: '↩',
  escape: '⎋',
  space: '␣',
  backspace: '⌫',
  delete: '⌦',
  arrowleft: '←',
  arrowright: '→',
  arrowup: '↑',
  arrowdown: '↓',
}

// Proper display labels for multi-character key names on Windows/Linux
// (bindings store the lowercase e.key form, e.g. 'arrowleft').
const KEY_LABELS: Record<string, string> = {
  enter: 'Enter',
  tab: 'Tab',
  escape: 'Escape',
  space: 'Space',
  backspace: 'Backspace',
  delete: 'Delete',
  insert: 'Insert',
  home: 'Home',
  end: 'End',
  pageup: 'PageUp',
  pagedown: 'PageDown',
  arrowleft: 'ArrowLeft',
  arrowright: 'ArrowRight',
  arrowup: 'ArrowUp',
  arrowdown: 'ArrowDown',
}

// macOS-style key label: symbols for special keys, uppercase for single
// characters, the raw name for anything else.
function macKeyLabel(key: string): string {
  const k = key.toLowerCase()
  if (MAC_KEY_SYMBOLS[k]) return MAC_KEY_SYMBOLS[k]
  // The spacebar's e.key is a literal space; show the symbol, not a blank.
  if (k === ' ') return MAC_KEY_SYMBOLS.space
  return k.length === 1 ? k.toUpperCase() : k
}

// Windows/Linux key label: mapped names when known, capitalized for single
// characters (Ctrl+M) and first-letter-capitalized for anything else.
function keyLabel(key: string): string {
  const k = key.toLowerCase()
  if (KEY_LABELS[k]) return KEY_LABELS[k]
  // The spacebar's e.key is a literal space; show the name, not a blank.
  if (k === ' ') return KEY_LABELS.space
  if (/^f([1-9]|1[0-9]|2[0-4])$/.test(k)) return k.toUpperCase()
  return k.length === 1 ? k.toUpperCase() : k.charAt(0).toUpperCase() + k.slice(1)
}

/**
 * Render a KeyBinding as a human-readable combo. Shared by the settings UI
 * and the terminal context-menu shortcut hints so both show the same format:
 * mac symbols concatenated without separators on macOS (⌃⇧M), words joined
 * with '+' elsewhere (Ctrl+Shift+M). An empty `key` (modifier-only bindings
 * of the digit settings rows) renders just the modifiers.
 */
export function formatKeyBinding(b: KeyBinding, isMac: boolean): string {
  if (!b) return ''
  if (isMac) {
    let s = ''
    // ctrl combos fire on Cmd on macOS (the physical Ctrl works too), so
    // display the natural Cmd symbol.
    if (b.ctrl) s += '⌘'
    if (b.alt) s += '⌥'
    if (b.shift) s += '⇧'
    return s + macKeyLabel(b.key)
  }
  const parts: string[] = []
  if (b.ctrl) parts.push('Ctrl')
  if (b.shift) parts.push('Shift')
  if (b.alt) parts.push('Alt')
  parts.push(keyLabel(b.key))
  return parts.join('+')
}

function bindingKey(b: KeyBinding): string {
  if (!b.key) return ''
  let k = ''
  if (b.ctrl) k += 'ctrl+'
  if (b.shift) k += 'shift+'
  if (b.alt) k += 'alt+'
  k += b.key.toLowerCase()
  return k
}

function normalize(e: KeyboardEvent): string {
  const parts: string[] = []
  if (e.ctrlKey) parts.push('ctrl')
  if (e.metaKey) parts.push('meta')
  if (e.shiftKey) parts.push('shift')
  if (e.altKey) parts.push('alt')
  parts.push(e.key.toLowerCase())
  return parts.join('+')
}

// Module-level state: key combo → action handler
const shortcutMap = new Map<string, () => void>()
// Terminal-scoped shortcuts: only fire while a terminal session is focused
// (handled by onTerminalKey), never from the global capture listener, so they
// don't hijack copy/paste while the user is typing in another input.
const terminalShortcutMap = new Map<string, () => void>()
// Reverse lookup: action → key combo (for display / dedup)
const actionKeyMap = new Map<ShortcutAction, string>()

// Actions that should only take effect while a terminal session is focused.
const TERMINAL_SCOPED_ACTIONS: ShortcutAction[] = ['copy', 'paste']

export function loadKeybindings(
  bindings: KeyboardSettings,
  handlers: ActionHandlers,
) {
  shortcutMap.clear()
  terminalShortcutMap.clear()
  actionKeyMap.clear()
  for (const [action, b] of Object.entries(bindings) as [ShortcutAction, KeyBinding][]) {
    const key = bindingKey(b)
    if (!key) continue
    const handler = handlers[action]
    if (handler) {
      const target = TERMINAL_SCOPED_ACTIONS.includes(action) ? terminalShortcutMap : shortcutMap
      target.set(key, handler)
      // macOS: ctrl combos also answer to Cmd.
      if (b.ctrl) {
        target.set(key.replace(/^ctrl\+/, 'meta+'), handler)
      }
      actionKeyMap.set(action, key)
    }
  }
}

export function getActionKey(action: ShortcutAction): string {
  return actionKeyMap.get(action) || ''
}

// True while the settings page is capturing a key rebind. Runtime handlers
// (the global listener is already uninstalled, but e.g. App.vue's platform
// digit handler is a separate capture listener) must stand down, otherwise
// recording e.g. Ctrl+1 would switch tabs mid-capture.
let rebinding = false
export function setRebinding(v: boolean): void {
  rebinding = v
}
export function isRebinding(): boolean {
  return rebinding
}

function fire(e: KeyboardEvent, normalized: string, map: Map<string, () => void>): boolean {
  const handler = map.get(normalized)
  if (!handler) return false
  e.preventDefault()
  e.stopPropagation()
  handler()
  return true
}

export function onGlobalKeydown(e: KeyboardEvent) {
  fire(e, normalize(e), shortcutMap)
}

export function onTerminalKey(e: KeyboardEvent): boolean {
  const normalized = normalize(e)
  if (fire(e, normalized, shortcutMap)) return false
  if (fire(e, normalized, terminalShortcutMap)) return false
  return true
}

// ── Configurable digit tab/panel switching ──
//
// Digit shortcuts live in onPlatformSystemShortcut (App.vue): by default
// Ctrl/Cmd+1…9 switches tabs and Alt/Option+1…9 switches workspace panels.
// The optional keyboard.tabSwitchModifier / keyboard.panelSwitchModifier
// settings move either combo to any modifier the user prefers. The helpers
// below are the pure decision logic, shared by the runtime handler and the
// tab/panel shortcut badges so the UI can never show a combo that doesn't
// work. When both settings resolve to the same combo, tab switching wins and
// the panel shortcuts are suppressed.

function hasAnyFlag(mod: KeyBinding | undefined): boolean {
  return !!mod && !!(mod.ctrl || mod.shift || mod.alt)
}

function comboSigOf(ctrl: boolean, shift: boolean, alt: boolean): string {
  const parts: string[] = []
  if (ctrl) parts.push('ctrl')
  if (shift) parts.push('shift')
  if (alt) parts.push('alt')
  return parts.join('+')
}

// On macOS Cmd is treated as Ctrl for the digit shortcuts, mirroring the
// per-action ctrl→Cmd registration, so a configured Ctrl combo answers to
// both keys.
function eventSigOf(e: KeyboardEvent, isMac: boolean): string {
  return comboSigOf(isMac ? (e.ctrlKey || e.metaKey) : e.ctrlKey, e.shiftKey, e.altKey)
}

/**
 * Effective modifier combo as a signature string. `mod` undefined falls back
 * to the fixed platform default; a binding with no modifier set disables the
 * family (null); otherwise the exact configured combo.
 */
function effectiveComboSig(mod: KeyBinding | undefined, fallback: string): string | null {
  if (mod === undefined) return fallback
  if (!hasAnyFlag(mod)) return null
  return comboSigOf(!!mod.ctrl, !!mod.shift, !!mod.alt)
}

// True when the tab-switch combo claims the same combo as the panel digit
// shortcuts, i.e. the panels must be suppressed (runtime handler skips them,
// badges hide the hint). The default tab combo is Ctrl/Cmd (unified on mac),
// so a Ctrl-only panel modifier collides on every platform.
export function panelDigitShortcutsSuppressed(
  tabMod?: KeyBinding,
  panelMod?: KeyBinding,
): boolean {
  const tabSig = effectiveComboSig(tabMod, 'ctrl')
  if (tabSig === null) return false
  const panelSig = effectiveComboSig(panelMod, 'alt')
  return panelSig !== null && tabSig === panelSig
}

/**
 * Resolve which target a digit keydown addresses, or null when it belongs to
 * nobody. `tabMod` / `panelMod` are the configured tabSwitchModifier /
 * panelSwitchModifier: undefined falls back to the fixed platform bindings
 * (Ctrl/Cmd tabs, Alt/Option panels); a binding with no modifier set disables
 * that family entirely; a configured combo moves it there. Tab switching wins
 * when both resolve to the same combo.
 */
export function matchDigitShortcut(
  e: KeyboardEvent,
  isMac: boolean,
  tabMod?: KeyBinding,
  panelMod?: KeyBinding,
): 'tab' | 'panel' | null {
  const sig = eventSigOf(e, isMac)
  const tabSig = effectiveComboSig(tabMod, 'ctrl')
  if (tabSig !== null && sig === tabSig) return 'tab'
  const panelSig = effectiveComboSig(panelMod, 'alt')
  if (panelSig !== null && sig === panelSig) return 'panel'
  return null
}

// Modifier text for the digit shortcut badges, same style as
// formatKeyBinding: mac symbols on macOS (ctrl shown as ⌘ — the Cmd mirror),
// words elsewhere.
function modifierText(mod: KeyBinding, isMac: boolean): string {
  if (isMac) {
    let s = ''
    if (mod.ctrl) s += '⌘'
    if (mod.alt) s += '⌥'
    if (mod.shift) s += '⇧'
    return s
  }
  const parts: string[] = []
  if (mod.ctrl) parts.push('Ctrl')
  if (mod.shift) parts.push('Shift')
  if (mod.alt) parts.push('Alt')
  return parts.join('+')
}

// Platform-default modifier flags per digit family: tabs switch with
// Ctrl/Cmd (unified on mac), panels with Alt/Option.
export const TAB_DEFAULT_FLAGS: KeyBinding = { ctrl: true, shift: false, alt: false, key: '' }
export const PANEL_DEFAULT_FLAGS: KeyBinding = { ctrl: false, shift: false, alt: true, key: '' }

export function digitModifierFlagsEqual(a: KeyBinding, b: KeyBinding): boolean {
  return !!a.ctrl === !!b.ctrl && !!a.shift === !!b.shift && !!a.alt === !!b.alt
}

// True when assigning `binding` to one digit family would collide with the
// other family's effective combo: an unset family falls back to its platform
// default (`otherDefault` — ctrl for tabs, alt for panels), a configured
// family uses its own flags, and a disabled (all-flags-off) family never
// collides.
export function digitModifierCollides(other: KeyBinding | undefined, otherDefault: KeyBinding, binding: KeyBinding): boolean {
  if (other && !hasAnyFlag(other)) return false
  const effective = other ?? otherDefault
  return digitModifierFlagsEqual(effective, binding)
}

/**
 * Badge prefix for the tab digit shortcut (the digit is appended by callers
 * via formatDigitShortcut): platform symbols for the default binding, plain
 * modifier text for a configured one. '' when digit tab switching is
 * disabled.
 */
export function tabDigitShortcutPrefix(isMac: boolean, tabMod?: KeyBinding): string {
  if (tabMod === undefined) return isMac ? '⌘' : 'Ctrl'
  if (!hasAnyFlag(tabMod)) return ''
  return modifierText(tabMod, isMac)
}

/**
 * Badge prefix for the panel digit shortcut, mirroring tabDigitShortcutPrefix
 * with the panel default (Alt/Option).
 */
export function panelDigitShortcutPrefix(isMac: boolean, panelMod?: KeyBinding): string {
  if (panelMod === undefined) return isMac ? '⌥' : 'Alt'
  if (!hasAnyFlag(panelMod)) return ''
  return modifierText(panelMod, isMac)
}

/**
 * Render a digit shortcut badge: word prefixes get a separating plus
 * ('Ctrl+1'), macOS symbol prefixes stay compact ('⌘1'). '' when the family
 * is disabled (empty prefix).
 */
export function formatDigitShortcut(prefix: string, index: number, isMac: boolean): string {
  if (!prefix) return ''
  return isMac ? `${prefix}${index}` : `${prefix}+${index}`
}

let registered = false

export function installGlobalListener() {
  if (registered) return
  registered = true
  window.addEventListener('keydown', onGlobalKeydown, true)
}

export function uninstallGlobalListener() {
  registered = false
  window.removeEventListener('keydown', onGlobalKeydown, true)
}
