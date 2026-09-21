import { ref, computed } from 'vue'
import type { Terminal } from '@xterm/xterm'

export interface CursorPosition {
  x: number
  y: number
}

export interface UseTerminalInputOptions {
  mode: 'ssh' | 'sftp' | 'local'
  sessionId: string | null | undefined
  onHistoryExtract?: (command: string) => void
  onResetSuppress?: () => void
  enableHistory?: boolean
}

export function useTerminalInput(terminal: Terminal | null, options: UseTerminalInputOptions) {
  // Char-array source of truth — mid-string inserts cost O(n) splice instead
  // of two string copies + concat per keystroke. lineBuffer mirrors as string.
  const lineChars = ref<string[]>([])
  const lineBuffer = computed<string>({
    get: () => lineChars.value.join(''),
    set: (val) => { lineChars.value = Array.from(val) }
  })
  const cursorIndex = ref(0)
  const currentToken = ref('')
  const cursorPixelPos = ref<CursorPosition>({ x: 0, y: 0 })

  let inAlternateScreen = false
  let isPasswordPrompt = false
  let cursorPosRAF: number | null = null

  function stripAnsi(str: string): string {
    return str
      // OSC sequences: ESC ] ... BEL or ESC ] ... ESC \
      .replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, '')
      // CSI sequences: ESC [ params final-byte
      .replace(/\x1b\[[0-?]*[ -/]*[@-~]/g, '')
      // Single-char FE escapes: ESC @ to ESC _, ESC ` to ESC ~
      .replace(/\x1b[@-Z\-_]/g, '')
      // Character set designation: ESC ( B, ESC ) B, etc.
      .replace(/\x1b[()[\]{}][0-9A-Za-z]/g, '')
  }

  const MAX_COMMAND_LENGTH = 200

  function getCurrentCommandFromTerminal(): string | null {
    if (!terminal) return null
    try {
      const buffer = (terminal as any).buffer?.active
      if (!buffer) return null
      // Prompt endings: $ # > ] plus common zsh/oh-my-zsh/powerline glyphs
      const PROMPT_RE = /(.+?[$#>\]❯➜→»λ])(?:\s+|$)(.*)/
      const rows = (terminal as any).rows || 24
      // Scan visible area from bottom to top — always finds the latest
      // prompt regardless of cursor position. (Cursor-based scanning was
      // tried in e4d31b7 but proved unreliable for prompt detection.)
      const bottomY = (buffer.baseY ?? 0) + rows - 1
      for (let dy = 0; dy < rows; dy++) {
        const y = bottomY - dy
        if (y < 0) break
        const line = buffer.getLine(y)
        if (!line) continue
        const rawText = line.translateToString().trim()
        if (!rawText) continue
        const cleanText = stripAnsi(rawText)
        const match = cleanText.match(PROMPT_RE)
        if (!match) continue
        const command = match[2].trim()
        if (!command || command.includes('__AI_DONE_')) continue
        // A long command that overflows the panel width wraps onto the rows
        // below the prompt. Walk down while each row is marked as a wrapped
        // continuation (isWrapped) and append it so the full command is
        // captured instead of being truncated at the wrap point (issue 639).
        let full = command
        for (let cy = y + 1; cy < bottomY; cy++) {
          const cont = buffer.getLine(cy)
          if (!cont || typeof cont.isWrapped !== 'function' || !cont.isWrapped()) break
          full += stripAnsi(cont.translateToString().trim())
        }
        if (full.length > MAX_COMMAND_LENGTH) continue
        return full
      }
    } catch {
      // Ignore errors
    }
    return null
  }

  function updateToken() {
    const buf = lineChars.value
    const idx = cursorIndex.value
    let beforeCursor = ''
    for (let i = 0; i < idx && i < buf.length; i++) beforeCursor += buf[i]
    // Use the entire command before cursor for suggestion matching,
    // so "git status" matches history entries like "git status --short".
    currentToken.value = beforeCursor.trim()
  }

  let lastTerminalCursorX = -1

  function updateCursorPosition() {
    if (!terminal) {
      cursorPixelPos.value = { x: 0, y: 0 }
      return
    }
    try {
      const core = (terminal as any)._core
      if (!core) return
      const buffer = core.buffer
      const renderer = core._renderService
      if (!buffer || !renderer) return
      const cursorX = buffer.x
      const cursorY = buffer.y
      const dims = renderer.dimensions
      if (dims && dims.css && dims.css.cell) {
        const cellWidth = dims.css.cell.width || 9
        const cellHeight = dims.css.cell.height || 17
        const x = cursorX * cellWidth
        const belowY = (cursorY + 1) * cellHeight
        cursorPixelPos.value = { x, y: belowY }
      }
      // Echo off (password mode): local buffer grew but terminal cursor didn't.
      if (lineChars.value.length > 0 && cursorX === lastTerminalCursorX && cursorX >= 0) {
        isPasswordPrompt = true
      } else if (cursorX !== lastTerminalCursorX) {
        isPasswordPrompt = false
      }
      lastTerminalCursorX = cursorX
    } catch {
      const el = terminal.element
      if (el) {
        const rect = el.getBoundingClientRect()
        cursorPixelPos.value = { x: 0, y: rect.height }
      }
    }
  }

  function isAtLineEnd(): boolean {
    return cursorIndex.value >= lineChars.value.length
  }

  function handleInput(data: string) {
    if (options.mode !== 'ssh') return
    if (inAlternateScreen) return
    for (let i = 0; i < data.length; i++) {
      const char = data[i]
      const code = data.charCodeAt(i)
      if (char === '\r' || char === '\n') {
        // Save command to history before clearing.
        // Always prefer terminal buffer (has server echo + tab completion),
        // only fall back to local lineBuffer if terminal buffer is unreadable.
        if (options.enableHistory !== false && !isPasswordPrompt) {
          const command = getCurrentCommandFromTerminal()
          if (command && options.onHistoryExtract) {
            options.onHistoryExtract(command)
          }
        }
        if (isPasswordPrompt) {
          isPasswordPrompt = false
        }
        lineChars.value = []
        cursorIndex.value = 0
        // Reset suggestion suppress on new command
        if (options.onResetSuppress) {
          options.onResetSuppress()
        }
      } else if (code === 127 || char === '\b') {
        if (cursorIndex.value > 0) {
          lineChars.value.splice(cursorIndex.value - 1, 1)
          cursorIndex.value--
        }
      } else if (code === 1) {
        // Ctrl+A — beginning of line
        cursorIndex.value = 0
      } else if (code === 5) {
        // Ctrl+E — end of line
        cursorIndex.value = lineChars.value.length
      } else if (code === 11) {
        // Ctrl+K — delete from cursor to end of line
        lineChars.value.length = cursorIndex.value
      } else if (code === 21) {
        // Ctrl+U — delete from beginning to cursor
        lineChars.value.splice(0, cursorIndex.value)
        cursorIndex.value = 0
      } else if (code === 27) {
        i++
        if (data[i] === '[') {
          i++
          let param = ''
          while (i < data.length && ((data[i] >= '0' && data[i] <= '9') || data[i] === ';')) {
            param += data[i]
            i++
          }
          const finalChar = data[i]
          if (finalChar === 'D') {
            // Left arrow
            if (cursorIndex.value > 0) cursorIndex.value--
          } else if (finalChar === 'C') {
            // Right arrow
            if (cursorIndex.value < lineChars.value.length) cursorIndex.value++
          } else if (finalChar === 'H' && param === '') {
            // Home
            cursorIndex.value = 0
          } else if (finalChar === 'F' && param === '') {
            // End
            cursorIndex.value = lineChars.value.length
          } else if (finalChar === '~') {
            if (param === '1' || param === '7') {
              // Home (alternate)
              cursorIndex.value = 0
            } else if (param === '4' || param === '8') {
              // End (alternate)
              cursorIndex.value = lineChars.value.length
            } else if (param === '3') {
              // Delete
              if (cursorIndex.value < lineChars.value.length) {
                lineChars.value.splice(cursorIndex.value, 1)
              }
            }
          }
        }
      } else if (code >= 32) {
        // Support all printable characters including CJK
        lineChars.value.splice(cursorIndex.value, 0, char)
        cursorIndex.value++
      }
    }
    updateToken()
    // Coalesce cursor position update to next paint frame via rAF. The
    // suggestion popup only needs roughly correct placement, so per-keystroke
    // updates are wasteful under typing bursts — rAF naturally coalesces
    // multiple keystrokes within one frame into a single update.
    if (cursorPosRAF !== null) {
      cancelAnimationFrame(cursorPosRAF)
    }
    cursorPosRAF = requestAnimationFrame(() => {
      cursorPosRAF = null
      updateCursorPosition()
    })
  }

  function handleSessionData(data: string) {
    if (options.mode !== 'ssh') return

    // Detect alternate screen buffer enter/exit (vim, k9s, less, etc.)
    if (data.includes('\x1b[?1049h') || data.includes('\x1b[?47h')) {
      inAlternateScreen = true
      return
    }
    if (data.includes('\x1b[?1049l') || data.includes('\x1b[?47l')) {
      inAlternateScreen = false
    }
  }

  function clearBuffer() {
    lineChars.value = []
    cursorIndex.value = 0
    currentToken.value = ''
  }

  function isInAlternateScreen(): boolean {
    return inAlternateScreen
  }

  function isPasswordMode(): boolean {
    return isPasswordPrompt
  }

  return {
    lineBuffer,
    cursorIndex,
    currentToken,
    cursorPixelPos,
    isAtLineEnd,
    handleInput,
    handleSessionData,
    clearBuffer,
    isInAlternateScreen,
    isPasswordMode,
  }
}
