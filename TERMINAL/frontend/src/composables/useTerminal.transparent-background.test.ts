import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// resolveXtermBackground reads getComputedStyle().getPropertyValue('--bg-base')
// from the document root. Stub the document surface so we can drive what
// '--bg-base' resolves to.
const getPropertyValue = vi.fn()
const getComputedStyle = vi.fn(() => ({ getPropertyValue })) as unknown as typeof window.getComputedStyle

beforeEach(() => {
  vi.stubGlobal('document', { documentElement: {} })
  vi.stubGlobal('getComputedStyle', getComputedStyle)
  getPropertyValue.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

import { resolveXtermBackground } from './useTerminalTheme'
import type { ITheme } from '@xterm/xterm'

const baseTheme: ITheme = { background: '#101418', foreground: '#e4e4e7' }

describe('resolveXtermBackground', () => {
  it('leaves theme.background alone when background image is disabled', () => {
    const out = resolveXtermBackground(baseTheme, false, 'foo.png')
    expect(out.background).toBe('#101418')
    expect(getComputedStyle).not.toHaveBeenCalled()
  })

  it('leaves theme.background alone when no background image is set', () => {
    const out = resolveXtermBackground(baseTheme, true, null)
    expect(out.background).toBe('#101418')
    expect(getComputedStyle).not.toHaveBeenCalled()

    const out2 = resolveXtermBackground(baseTheme, true, undefined)
    expect(out2.background).toBe('#101418')
  })

  it('uses real RGB from --bg-base instead of transparent when background image is enabled', () => {
    getPropertyValue.mockReturnValue(' #fafafa ')
    const out = resolveXtermBackground(baseTheme, true, 'bg.png')
    expect(out.background).toBe('#fafafa')
    expect(out.background).not.toBe('rgba(0,0,0,0)')
    expect(out.foreground).toBe('#e4e4e7') // other fields untouched
  })

  it('falls back to base theme when --bg-base is unset', () => {
    getPropertyValue.mockReturnValue('')
    const out = resolveXtermBackground(baseTheme, true, 'bg.png')
    expect(out.background).toBe('#101418')
  })

  it('does not mutate the input theme object', () => {
    getPropertyValue.mockReturnValue('#fafafa')
    const input = { ...baseTheme }
    const out = resolveXtermBackground(input, true, 'bg.png')
    expect(input.background).toBe('#101418')
    expect(out).not.toBe(input)
  })
})
