import { describe, it, expect } from 'vitest'
import {
  sanitizeTerminalOutput,
  sanitizeLiveTerminalOutput,
} from './terminalSanitize'

describe('sanitizeTerminalOutput()', () => {
  it('returns empty / falsy input unchanged', () => {
    expect(sanitizeTerminalOutput('')).toBe('')
  })

  it('passes plain ASCII through untouched', () => {
    expect(sanitizeTerminalOutput('hello world\n')).toBe('hello world\n')
  })

  it('drops U+FFFD replacement chars between box-drawing borders', () => {
    // Input: 2 box-drawing chars + 2 replacement chars + 2 box-drawing chars.
    // After strip: just the 4 box-drawing chars survive.
    const dirty = '──��──\n'
    expect(sanitizeTerminalOutput(dirty)).toBe('────\n')
  })

  it('drops standalone U+FFFD chars', () => {
    expect(sanitizeTerminalOutput('a��b��c')).toBe('abc')
  })

  it('preserves every box-drawing char in the U+2500-257F range', () => {
    const all = '─│┌┐└┘├┤┬┴┼━┃┏┓┗┛┣┫┳┻╋┳┓'
    expect(sanitizeTerminalOutput(all)).toBe(all)
  })

  it('preserves block elements U+2580-259F', () => {
    const all = '▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟'
    expect(sanitizeTerminalOutput(all)).toBe(all)
  })

  it('preserves arrows U+2190-21FF', () => {
    const sample = '←↑→↓⇐⇑⇒⇓⇔↔↕↖↗'
    expect(sanitizeTerminalOutput(sample)).toBe(sample)
  })

  it('preserves math operators U+2200-22FF', () => {
    const sample = '∀∂∃∅∇∈∉∋∏∑−∓∔∕∖∗∘∙√∛∜∝'
    expect(sanitizeTerminalOutput(sample)).toBe(sample)
  })

  it('preserves braille patterns U+2800-28FF (spinners survive)', () => {
    const spinner = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    expect(sanitizeTerminalOutput(spinner)).toBe(spinner)
  })

  it('preserves CJK (中文 / 日本語 / 한국어)', () => {
    const cjk = '中文测试 日本語テスト 한국어 테스트'
    expect(sanitizeTerminalOutput(cjk)).toBe(cjk)
  })

  it('preserves Hangul syllables in U+AC00-D7AF range', () => {
    expect(sanitizeTerminalOutput('가나다라마바사아자차카')).toBe(
      '가나다라마바사아자차카'
    )
  })

  it('drops ASCII control chars except \\n \\r \\t ESC', () => {
    // \x07 BEL, \x0b VT, \x7f DEL should be stripped.
    expect(sanitizeTerminalOutput('a\x07b\x0bc\x7fd')).toBe('abcd')
    // Newlines / CR / TAB must survive.
    expect(sanitizeTerminalOutput('a\nb\tc\rd')).toBe('a\nb\tc\rd')
    // ESC must survive (SGR / cursor movement).
    expect(sanitizeTerminalOutput('\x1b[31mred\x1b[0m')).toBe(
      '\x1b[31mred\x1b[0m'
    )
  })

  it('strips ZModem ZDLE (0x18) and backspace (0x08) runs', () => {
    expect(sanitizeTerminalOutput('a\x18\x18\x18b\x08\x08c')).toBe('abc')
  })

  it('strips ZModem HEX header fragments', () => {
    expect(
      sanitizeTerminalOutput('**B00000000000000aabb\nhello')
    ).toBe('\nhello')
  })

  it('strips a binary-garbage char in the U+E000 private-use area', () => {
    // U+E000 is in the BMP private-use area, never legitimate terminal output.
    expect(sanitizeTerminalOutput('ab')).toBe('ab')
  })

  it('keeps an astral-plane symbol such as an emoji', () => {
    // U+1F600 GRINNING FACE is \p{S}, the same category as the ● ⏺ ✓ glyphs
    // Claude Code draws with — they cannot be separated, and emoji in command
    // output is legitimate anyway.
    expect(sanitizeTerminalOutput('a😀b')).toBe('a😀b')
  })

  it('keeps the Claude Code glyph set through a history restore', () => {
    const glyphs = '● ⏺ ⏵ ⌘ ⌥ ⌫ ↵ ⏎ ✓ ✗ ■ □ ▶ ◆ ★'
    expect(sanitizeTerminalOutput(glyphs)).toBe(glyphs)
  })

  it('collapses 3+ consecutive newlines down to 2', () => {
    expect(sanitizeTerminalOutput('a\n\n\n\nb')).toBe('a\n\nb')
  })

  it('preserves exactly 2 consecutive newlines', () => {
    expect(sanitizeTerminalOutput('a\n\nb')).toBe('a\n\nb')
  })

  it('handles a realistic Claude Code table fragment end-to-end', () => {
    // 4 box-drawing chars + replacement chars + BEL + 2 box-drawing chars +
    // 4 blank lines + a row.
    const input = '──��──\x07──\n\n\n\n│ a │ b │\n'
    const expected = '──────\n\n│ a │ b │\n'
    expect(sanitizeTerminalOutput(input)).toBe(expected)
  })
})

describe('sanitizeLiveTerminalOutput()', () => {
  it('does NOT collapse 3+ newlines (hot path skips that step)', () => {
    expect(sanitizeLiveTerminalOutput('a\n\n\n\nb')).toBe('a\n\n\n\nb')
  })

  it('still strips U+FFFD', () => {
    expect(sanitizeLiveTerminalOutput('─��─')).toBe('──')
  })

  it('still preserves box-drawing and braille', () => {
    const input = '─│┌┐\n⠋⠙⠹'
    expect(sanitizeLiveTerminalOutput(input)).toBe(input)
  })

  // Regression guard: the live path used to run the same control-character
  // filter as the history path, which broke interactive line editing. A
  // shell steers the cursor with these bytes; dropping them left the cursor
  // to the right of where the shell believed it was, so typing "12" rendered
  // as "112" and backspace erased the glyph but left its column as a space.
  it('preserves BS so a shell line editor can move the cursor back', () => {
    expect(sanitizeLiveTerminalOutput('\x08 \x08')).toBe('\x08 \x08')
  })

  it('preserves a PSReadLine redraw sequence verbatim', () => {
    const redraw = '\x1b[?25l\x08\x1b[K12\x1b[?25h'
    expect(sanitizeLiveTerminalOutput(redraw)).toBe(redraw)
  })

  it('preserves the C0 control characters a PTY relies on', () => {
    // BEL, BS, TAB, LF, CR, ESC — all meaningful to xterm's parser.
    const controls = '\x07\x08\x09\x0a\x0d\x1b'
    expect(sanitizeLiveTerminalOutput(controls)).toBe(controls)
  })
})