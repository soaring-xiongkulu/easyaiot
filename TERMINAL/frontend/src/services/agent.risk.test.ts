// Regression tests for FE-P0-2: getRisk must default to 'dangerous' for
// missing / wrong-typed / unknown risk values rather than 'write', so a
// model that omits or typos the field cannot bypass the user's
// read-only / confirm_write confirmation mode.

import { describe, expect, it, vi } from 'vitest'

// agent.ts transitively pulls in terminalAgent.ts → terminalManager.ts → xterm
// addons that expect a browser `self` global. Stub the wails runtime + the
// terminal manager so the module graph is small enough to load in vitest.
vi.mock('@wailsio/runtime', () => ({
  Events: { On: vi.fn(() => () => {}), Off: vi.fn() },
}))

vi.mock('../../bindings/easyaiot/terminal/app', () => ({
  ChatCompletion: vi.fn(),
  GetSkillFile: vi.fn(),
  ListSkillFiles: vi.fn(),
  SessionWrite: vi.fn(),
}))

vi.mock('./terminalManager', () => ({
  getManagedTerminal: vi.fn(),
}))

import { getRisk, VALID_RISK } from './agent'

describe('getRisk (FE-P0-2 default-closed)', () => {
  it('returns the risk exactly when valid (read)', () => {
    expect(getRisk({ name: 'execute_command', input: { risk: 'read' } })).toBe('read')
  })

  it('returns the risk exactly when valid (write)', () => {
    expect(getRisk({ name: 'start_command', input: { risk: 'write' } })).toBe('write')
  })

  it('returns the risk exactly when valid (dangerous)', () => {
    expect(getRisk({ name: 'execute_command', input: { risk: 'dangerous' } })).toBe('dangerous')
  })

  it('defaults to dangerous when risk field is missing', () => {
    expect(getRisk({ name: 'execute_command', input: {} })).toBe('dangerous')
    expect(getRisk({ name: 'start_command', input: {} })).toBe('dangerous')
  })

  it('defaults to dangerous when risk is an unknown string', () => {
    expect(getRisk({ name: 'execute_command', input: { risk: 'low' } })).toBe('dangerous')
    expect(getRisk({ name: 'start_command', input: { risk: 'risky' } })).toBe('dangerous')
    // Case-sensitive — "READ" is not the same literal as "read".
    expect(getRisk({ name: 'execute_command', input: { risk: 'READ' } })).toBe('dangerous')
  })

  it('defaults to dangerous when risk is null, an empty array, or wrong-typed', () => {
    expect(getRisk({ name: 'execute_command', input: { risk: null } })).toBe('dangerous')
    expect(getRisk({ name: 'execute_command', input: { risk: [] } })).toBe('dangerous')
    expect(getRisk({ name: 'execute_command', input: { risk: '' } })).toBe('dangerous')
    expect(getRisk({ name: 'execute_command', input: { risk: 42 } })).toBe('dangerous')
    expect(getRisk({ name: 'execute_command', input: { risk: { foo: 'bar' } } })).toBe('dangerous')
  })

  it('VALID_RISK exposes exactly the three literal risk levels', () => {
    expect([...VALID_RISK].sort()).toEqual(['dangerous', 'read', 'write'])
  })
})