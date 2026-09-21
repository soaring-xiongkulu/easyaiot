// Regression tests for FE-P0-3: runtime input validation at the tool dispatch
// boundary. The LLM is untrusted; `tu.input.command as string` would yield
// "[object Object]" for `command: {}` and the malformed payload would flow
// straight into `executeCommand` / `startCommand` / `sendTerminalKey` / etc.
// The validator helpers below must reject wrong-typed / missing-required
// fields and quietly accept extra fields.

import { describe, expect, it, vi } from 'vitest'

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

import {
  InputValidationError,
  validateObject,
  validateRequiredString,
} from '../utils/runtimeTypeCheck'

// Re-import the validators indirectly via the dispatch tests below. Here we
// test the raw helpers + the same shape-checks the agent dispatch applies.

function tryValidate<T>(fn: () => T): T {
  return fn()
}

describe('InputValidationError', () => {
  it('is an Error subclass with a name', () => {
    const e = new InputValidationError('boom')
    expect(e).toBeInstanceOf(Error)
    expect(e.name).toBe('InputValidationError')
    expect(e.message).toBe('boom')
  })
})

describe('validateObject', () => {
  it('rejects null', () => {
    expect(() => validateObject(null, 'input')).toThrow(InputValidationError)
  })
  it('rejects arrays', () => {
    expect(() => validateObject([], 'input')).toThrow(InputValidationError)
    expect(() => validateObject([1, 2], 'input')).toThrow(InputValidationError)
  })
  it('rejects primitives', () => {
    expect(() => validateObject('hi', 'input')).toThrow(InputValidationError)
    expect(() => validateObject(42, 'input')).toThrow(InputValidationError)
    expect(() => validateObject(true, 'input')).toThrow(InputValidationError)
  })
  it('accepts plain objects and returns them as Record<string, unknown>', () => {
    const obj = { command: 'ls', risk: 'read' }
    expect(validateObject(obj, 'input')).toEqual(obj)
  })
})

describe('validateRequiredString', () => {
  it('rejects non-strings', () => {
    expect(() => validateRequiredString(42, 'command')).toThrow(InputValidationError)
    expect(() => validateRequiredString({}, 'command')).toThrow(InputValidationError)
    expect(() => validateRequiredString([], 'command')).toThrow(InputValidationError)
    expect(() => validateRequiredString(null, 'command')).toThrow(InputValidationError)
    expect(() => validateRequiredString(undefined, 'command')).toThrow(InputValidationError)
  })
  it('rejects empty string', () => {
    expect(() => validateRequiredString('', 'command')).toThrow(/non-empty/)
  })
  it('returns the string when valid', () => {
    expect(tryValidate(() => validateRequiredString('ls', 'command'))).toBe('ls')
  })
})

describe('execute_command input shape (FE-P0-3 wrong-shape bug)', () => {
  // Mirrors the agent dispatch: validate input as object, then command as
  // required string. The OLD code was `tu.input.command as string` which
  // produces "[object Object]" when command is an object.
  function validate(input: unknown): { command: string; risk: string } {
    const obj = validateObject(input, 'execute_command input')
    return {
      command: validateRequiredString(obj.command, 'command'),
      risk: typeof obj.risk === 'string' ? obj.risk : 'dangerous',
    }
  }

  it('rejects object instead of string for command', () => {
    // Reproduces: `command: { cmd: "rm -rf /" }` would have stringified to
    // "[object Object]" and executed verbatim. Now it throws.
    expect(() => validate({ command: { cmd: 'rm -rf /' }, risk: 'dangerous' }))
      .toThrow(InputValidationError)
  })

  it('rejects missing required command field', () => {
    expect(() => validate({ risk: 'read' })).toThrow(/command/)
  })

  it('rejects empty command', () => {
    expect(() => validate({ command: '', risk: 'read' })).toThrow(/non-empty/)
  })

  it('rejects non-object input', () => {
    expect(() => validate('ls')).toThrow(InputValidationError)
    expect(() => validate(null)).toThrow(InputValidationError)
    expect(() => validate([])).toThrow(InputValidationError)
  })

  it('accepts valid input with extra fields (extras ignored)', () => {
    const out = validate({
      command: 'ls -la',
      risk: 'read',
      timeout: 60,
      head_lines: 50,
      tail_lines: 300,
      panel: 'main',
      unexpected_extra: { foo: 'bar' },
    })
    expect(out.command).toBe('ls -la')
    expect(out.risk).toBe('read')
  })
})

describe('send_terminal_key input shape', () => {
  // Mirrors the dispatch validator.
  function validate(input: unknown): { control?: 'ctrl_c' | 'ctrl_d' | 'enter' } {
    const obj = validateObject(input, 'send_terminal_key input')
    const control = obj.control
    if (control === undefined) return { control: undefined }
    if (control === 'ctrl_c' || control === 'ctrl_d' || control === 'enter') {
      return { control }
    }
    throw new InputValidationError(`control must be one of ctrl_c, ctrl_d, enter`)
  }

  it('rejects non-string control that would have been cast', () => {
    expect(() => validate({ control: { key: 'enter' } })).toThrow(InputValidationError)
  })

  it('rejects unknown control string', () => {
    expect(() => validate({ control: 'delete' })).toThrow(InputValidationError)
    expect(() => validate({ control: 'CTRL_C' })).toThrow(InputValidationError)
  })

  it('accepts ctrl_c / ctrl_d / enter', () => {
    expect(validate({ control: 'ctrl_c' }).control).toBe('ctrl_c')
    expect(validate({ control: 'ctrl_d' }).control).toBe('ctrl_d')
    expect(validate({ control: 'enter' }).control).toBe('enter')
  })
})