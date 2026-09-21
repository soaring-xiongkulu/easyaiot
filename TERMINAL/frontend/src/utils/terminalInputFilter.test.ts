import { describe, expect, it } from 'vitest'
import { filterTerminalInput } from './terminalInputFilter'

describe('filterTerminalInput()', () => {
  it('preserves primary and secondary Device Attributes responses', () => {
    expect(filterTerminalInput('\x1b[?1;2c', false)).toBe('\x1b[?1;2c')
    expect(filterTerminalInput('\x1b[>0;276;0c', false)).toBe('\x1b[>0;276;0c')
  })

  it('continues to strip cursor, status and window responses', () => {
    expect(filterTerminalInput('a\x1b[2;2Rb\x1b[0nc\x1b[8;24;80td', false)).toBe('abcd')
  })

  it('strips focus responses only outside the alternate screen', () => {
    expect(filterTerminalInput('a\x1b[Ib\x1b[Oc', false)).toBe('abc')
    expect(filterTerminalInput('a\x1b[Ib\x1b[Oc', true)).toBe('a\x1b[Ib\x1b[Oc')
  })

  it('preserves ordinary keyboard input around filtered responses', () => {
    expect(filterTerminalInput('hello\x1b[2;2R world', false)).toBe('hello world')
  })
})
