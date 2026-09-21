import { describe, it, expect } from 'vitest'
import { normalizeKeyBindings, DEFAULT_KEYBOARD } from './settings'
import type { KeyBinding } from './settings'

describe('normalizeKeyBindings — legacy meta bindings', () => {
  it('converts a meta-only binding to ctrl (ctrl covers Cmd on mac)', () => {
    const legacy = {
      openQuickCommands: { ctrl: false, meta: true, shift: false, alt: false, key: 'k' },
    }
    const normalized = normalizeKeyBindings(legacy as any)
    expect(normalized.openQuickCommands).toEqual({ ctrl: true, shift: false, alt: false, key: 'k' })
    expect('meta' in (normalized.openQuickCommands as KeyBinding)).toBe(false)
  })

  it('keeps ctrl and drops meta when a binding has both', () => {
    const legacy = {
      terminalSearch: { ctrl: true, meta: true, shift: true, alt: false, key: 'f' },
    }
    const normalized = normalizeKeyBindings(legacy as any)
    expect(normalized.terminalSearch).toEqual({ ctrl: true, shift: true, alt: false, key: 'f' })
  })

  it('migrates the digit modifier entries too and leaves clean bindings alone', () => {
    const legacy = {
      copy: { ctrl: true, shift: true, alt: false, key: 'c' },
      tabSwitchModifier: { ctrl: false, meta: false, shift: false, alt: true, key: '' },
      panelSwitchModifier: { ctrl: false, meta: true, shift: false, alt: false, key: '' },
    }
    const normalized = normalizeKeyBindings(legacy as any)
    expect(normalized.copy).toEqual(legacy.copy)
    expect(normalized.tabSwitchModifier).toEqual(legacy.tabSwitchModifier)
    expect(normalized.panelSwitchModifier).toEqual({ ctrl: true, shift: false, alt: false, key: '' })
  })

  it('fills in platform defaults for untouched actions', () => {
    const normalized = normalizeKeyBindings({})
    expect(normalized.openQuickCommands).toEqual(DEFAULT_KEYBOARD.openQuickCommands)
    expect(normalized.copy).toEqual(DEFAULT_KEYBOARD.copy)
  })
})
