import { describe, it, expect, vi } from 'vitest'
import { normalizePastedText, bracketPaste, pasteWithScroll } from './terminalPaste'
import type { PasteTarget } from './terminalPaste'

function mkTarget(overrides: Partial<PasteTarget> = {}): PasteTarget & { scrollToBottom: ReturnType<typeof vi.fn> } {
  return {
    bracketedPasteMode: false,
    write: vi.fn(),
    scrollToBottom: vi.fn(),
    ...overrides,
  }
}

describe('normalizePastedText', () => {
  it('converts CRLF to LF and strips stray CR', () => {
    expect(normalizePastedText('a\r\nb\r\nc')).toBe('a\nb\nc')
    expect(normalizePastedText('a\rb')).toBe('ab')
  })

  it('leaves plain text untouched', () => {
    expect(normalizePastedText('ls -la')).toBe('ls -la')
  })
})

describe('bracketPaste', () => {
  it('wraps when bracketed-paste mode is on', () => {
    expect(bracketPaste('vim', true)).toBe('\x1b[200~vim\x1b[201~')
  })

  it('passes through when bracketed-paste mode is off', () => {
    expect(bracketPaste('vim', false)).toBe('vim')
  })
})

describe('pasteWithScroll', () => {
  it('writes the normalized, wrapped payload to the session', () => {
    const t = mkTarget({ bracketedPasteMode: true })
    pasteWithScroll(t, 'a\r\nb')
    expect(t.write).toHaveBeenCalledWith('\x1b[200~a\nb\x1b[201~')
  })

  // The regression under test (issue 629): pasting while scrolled up must
  // yank the viewport back to the bottom, mirroring how Enter/arrow keys
  // auto-scroll via xterm's scrollOnUserInput.
  it('scrolls the viewport to the bottom after writing pasted text', () => {
    const t = mkTarget()
    pasteWithScroll(t, 'printf "big log\\n"')
    expect(t.scrollToBottom).toHaveBeenCalled()
  })
})