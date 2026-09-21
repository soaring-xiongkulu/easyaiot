import { queuedSessionWrite } from '../services/sessionWriter'
import { getManagedTerminal } from '../services/terminalManager'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { Events } from '@wailsio/runtime'
import { watch } from 'vue'

// F-317: maintain a title→panelId index for O(1) lookups in
// resolveActiveSession. The original implementation spread panelStore.panels
// into an array and ran two .find passes per command call (O(n) per call).
// A vue watch on the reactive panels Map keeps the index in sync with
// add / remove / rename; we rebuild on every change because titles can
// duplicate and the index is tiny.
const panelTitleIndex: Map<string, string[]> = new Map()
let panelTitleIndexInit = false

function rebuildPanelTitleIndex(panels: Map<string, { id: string; title: string }>): void {
  panelTitleIndex.clear()
  for (const p of panels.values()) {
    const arr = panelTitleIndex.get(p.title)
    if (arr) arr.push(p.id)
    else panelTitleIndex.set(p.title, [p.id])
  }
}

function ensurePanelTitleIndex(): void {
  if (panelTitleIndexInit) return
  panelTitleIndexInit = true
  const panelStore = usePanelStore()
  rebuildPanelTitleIndex(panelStore.panels as Map<string, { id: string; title: string }>)
  // Watch the reactive Map: rebuild on size change (set/delete) and on any
  // title mutation (deep watch on the values). The index is tiny, so a full
  // rebuild is cheaper than a more granular diff.
  watch(
    () => panelStore.panels,
    () => rebuildPanelTitleIndex(panelStore.panels as Map<string, { id: string; title: string }>),
    { deep: true, flush: 'sync' }
  )
}

export interface ExecuteResult {
  output: string
  exitCode: number
  timedOut?: boolean
  cancelled?: boolean
}

export interface WatchResult {
  output: string
  timedOut: boolean
  cancelled?: boolean
}

// Split terminal output into display lines. Splits on newlines and, within a
// line, keeps only the text after the last carriage return so progress-bar
// style redraws (which overwrite the line with bare \r) collapse to their
// final state — the same way the text appears on screen.
function toDisplayLines(clean: string): string[] {
  // Normalize \r\n to \n, then handle bare \r (progress-bar redraws).
  // Bare \r (not at end of line) means the line was overwritten — keep only
  // the text after the last such \r.  Trailing \r (from \r\n that was already
  // normalized) is just stripped.
  const normalized = clean.replace(/\r\n/g, '\n')
  return normalized.split('\n').map((line) => {
    // If the only \r is at the very end, just strip it (it's a trailing \r).
    // Otherwise keep the text after the last \r (progress-bar style).
    const cr = line.lastIndexOf('\r')
    if (cr < 0) return line
    if (cr === line.length - 1) return line.slice(0, -1)
    return line.slice(cr + 1)
  })
}

// Short wait before reading the xterm screen buffer after completion is
// detected. xterm.js parses PTY writes asynchronously, so a chunk that is
// queued when the detector fires may not be reflected in the buffer yet.
const SCREEN_SETTLE_MS = 100

// Prompt + absolute buffer-row snapshot taken right before a command is sent.
// `startRow` is the row the command echo starts on, expressed as an absolute
// row (buffer row + accumulated scrollback-trim offset) so it stays valid
// even if rows scroll off the top of the buffer while the command runs.
export interface PromptSnapshot {
  promptLine: string
  startRow: number
}

// Read the current prompt line and the absolute row it sits on. Called right
// before a command is sent, when the cursor sits on the (freshly drawn)
// prompt with no input yet, so the cursor line's text is exactly the prompt
// string. ANSI sequences are stripped so the captured prompt matches the
// stripped output used in watchOutput. Returns promptLine '' and startRow -1
// when unavailable, which disables exact prompt detection and screen-buffer
// capture for that command (idle heuristic still applies).
function capturePromptSnapshot(sessionId: string): PromptSnapshot {
  const managed = getManagedTerminal(sessionId)
  const terminal = managed?.terminal
  if (!terminal) return { promptLine: '', startRow: -1 }
  const buffer = terminal.buffer.active
  const line = buffer.getLine(buffer.baseY + buffer.cursorY)
  const promptLine = line ? stripAnsi(line.translateToString(true)).trimEnd() : ''
  const startRow = (managed.lineOffset || 0) + buffer.baseY + buffer.cursorY
  return { promptLine, startRow }
}

// Read the visible command output from the xterm screen buffer, starting at
// the absolute row captured before the command ran, down to the last
// non-blank row. Unlike reconstructing text from the raw PTY stream, this
// reflects what the user actually sees: ConPTY redraws (cursor-left re-emits
// on old Windows Server builds, \r overwrites, erase sequences) have already
// been resolved by the terminal emulator.
//
// Returns null when no terminal/buffer is available so callers can fall back
// to raw-stream reconstruction.
function readScreenFromRow(sessionId: string, absStartRow: number): string | null {
  const managed = getManagedTerminal(sessionId)
  const terminal = managed?.terminal
  if (!terminal || absStartRow < 0) return null
  const buffer = terminal.buffer.active
  let first: number
  let last: number
  if (buffer.type === 'alternate') {
    // Full-screen program (vim, top, ...): the viewport is the whole picture
    // and absolute rows don't apply across the buffer switch.
    first = buffer.baseY
    last = buffer.length - 1
  } else {
    // Compensate for scrollback rows trimmed since the snapshot was taken.
    first = Math.max(0, absStartRow - (managed.lineOffset || 0))
    last = buffer.length - 1
    while (last >= first && isRowBlank(buffer, last)) last--
    if (last < first) return ''
  }
  const lines: string[] = []
  for (let i = first; i <= last; i++) {
    const line = buffer.getLine(i)
    if (line) lines.push(line.translateToString(true))
  }
  return lines.join('\n')
}

function isRowBlank(
  buffer: { getLine(n: number): { translateToString(trim?: boolean): string } | undefined },
  row: number
): boolean {
  const line = buffer.getLine(row)
  return !line || line.translateToString().trim() === ''
}

// Turn captured screen text into the output handed to the AI. On success the
// trailing blank rows and the final prompt line are dropped (completion was
// reported by the prompt reappearing — the prompt is terminal chrome, not
// command output); on timeout everything is kept.
function extractScreenOutput(screen: string, timedOut: boolean): string {
  const lines = screen.split('\n')
  if (!timedOut) {
    while (lines.length > 0 && lines[lines.length - 1].trimEnd() === '') lines.pop()
    if (lines.length > 0) lines.pop()
  }
  return lines.join('\n').trim()
}

// Watch session output and resolve when the command finishes.
//
// Completion is detected by the shell prompt reappearing: `promptLine` is the
// prompt captured immediately before the command was sent, and once that exact
// line shows up again at the bottom of the output the shell is back at the
// prompt and the command is done. No marker is injected into the shell, so the
// terminal shows nothing extra.
//
// As a fallback for dynamic prompts (timestamps, git branches, etc.) or ANSI
// mismatches, an idle heuristic is also used: if output stops for a short
// period and the last non-blank line looks like a prompt (ends with $, #, >,
// %, or :), the command is considered finished.
//
// When `promptLine` is empty and the heuristic cannot match, detection is
// skipped entirely and the call resolves on timeout.
//
// `shouldCancel` is polled periodically. When it returns true the watcher
// stops listening and resolves with cancelled=true. The terminal command is
// NOT interrupted; callers should discard the output and not pass it to the
// LLM.
export function watchOutput(
  sessionId: string,
  promptLine: string,
  timeoutMs: number,
  shouldCancel?: () => boolean,
  startRow: number = -1
): { promise: Promise<WatchResult>; cleanup: () => void } {
  const IDLE_MS = 800
  const CANCEL_POLL_MS = 150
  let timeoutId: ReturnType<typeof setTimeout>
  let idleTimeoutId: ReturnType<typeof setTimeout> | null = null
  let cancelPollId: ReturnType<typeof setTimeout> | null = null
  let settleId: ReturnType<typeof setTimeout> | null = null
  let unsubscribe: (() => void) | null = null
  let resolved = false
  let output = ''

  const cleanup = () => {
    clearTimeout(timeoutId)
    if (idleTimeoutId) {
      clearTimeout(idleTimeoutId)
      idleTimeoutId = null
    }
    if (cancelPollId) {
      clearTimeout(cancelPollId)
      cancelPollId = null
    }
    if (settleId) {
      clearTimeout(settleId)
      settleId = null
    }
    unsubscribe?.()
    resolved = true
  }

  function getLastDisplayLine(text: string): { line: string; index: number } | null {
    const lines = toDisplayLines(stripAnsi(text))
    let last = lines.length - 1
    while (last >= 0 && lines[last].trimEnd() === '') last--
    if (last < 0) return null
    return { line: lines[last].trimEnd(), index: last }
  }

  function looksLikePrompt(line: string): boolean {
    // Common prompt terminators: $, #, >, %, :
    // Avoid matching plain text lines that happen to end with these chars by
    // requiring a reasonably short line (prompts are rarely > 200 chars).
    return line.length <= 200 && /[\$#>%:]\s*$/.test(line)
  }

  const promise = new Promise<WatchResult>((resolve) => {
    const finish = (timedOut: boolean, cancelled = false) => {
      cleanup()
      if (cancelled) {
        resolve({ output: '', timedOut: false, cancelled: true })
        return
      }
      // Give xterm.js a moment to finish parsing writes that were queued when
      // the detector fired, then read what the screen actually shows instead
      // of reconstructing text from the raw stream — the raw stream carries
      // every intermediate ConPTY redraw frame (cursor-left re-emits on old
      // Windows Server builds, progress-bar \r overwrites, ...) that the
      // screen never displays. Falls back to the raw stream when no terminal
      // buffer is available.
      settleId = setTimeout(() => {
        settleId = null
        const screen = readScreenFromRow(sessionId, startRow)
        if (screen !== null) {
          resolve({ output: extractScreenOutput(screen, timedOut), timedOut })
          return
        }
        const lines = toDisplayLines(stripAnsi(output))
        if (!timedOut) {
          // The command finished when the shell prompt reappeared at the bottom.
          // That prompt line belongs to the terminal, not the command output —
          // completion is now reported explicitly by the caller's end-message
          // (see executeCommand in agent.ts), so drop the prompt (and any
          // trailing blanks) before returning the output to the AI.
          while (lines.length > 0 && lines[lines.length - 1].trimEnd() === '') lines.pop()
          if (lines.length > 0) lines.pop()
        }
        const normalized = lines.join('\n').trim()
        resolve({ output: normalized, timedOut })
      }, SCREEN_SETTLE_MS)
    }

    const checkIdle = () => {
      if (resolved || !promptLine) return
      const lastInfo = getLastDisplayLine(output)
      if (!lastInfo || lastInfo.index < 1) return
      if (looksLikePrompt(lastInfo.line)) {
        finish(false)
      }
    }

    const checkCancel = () => {
      if (resolved) return
      if (shouldCancel?.()) {
        finish(false, true)
        return
      }
      cancelPollId = setTimeout(checkCancel, CANCEL_POLL_MS)
    }

    unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data; 
      if (payload.id !== sessionId || resolved) return

      output += payload.data

      // Reset idle detection whenever new data arrives.
      if (idleTimeoutId) {
        clearTimeout(idleTimeoutId)
        idleTimeoutId = null
      }
      idleTimeoutId = setTimeout(checkIdle, IDLE_MS)

      const lastInfo = getLastDisplayLine(output)
      if (!lastInfo || lastInfo.index < 1) return

      // Exact prompt match (works when the prompt is static and ANSI-stripped).
      if (promptLine && lastInfo.line === promptLine) {
        finish(false)
        return
      }
     })

    if (shouldCancel) {
      cancelPollId = setTimeout(checkCancel, CANCEL_POLL_MS)
    }

    timeoutId = setTimeout(() => {
      finish(true)
    }, timeoutMs)
  })

  return { promise, cleanup }
}

export function truncateOutput(
  text: string,
  headLines: number,
  tailLines: number
): string {
  const lines = text.split('\n')
  const total = lines.length
  const threshold = headLines + tailLines
  if (total <= threshold) return text

  const head = lines.slice(0, headLines).join('\n')
  const tail = lines.slice(total - tailLines).join('\n')
  const omitted = total - headLines - tailLines
  return `${head}\n\n─────── [TRUNCATED: ${total} lines total, ${omitted} lines omitted] ────────\nAdjust head_lines / tail_lines to see more content.\n\n${tail}`
}

function resolveActiveSession(panelTitle?: string): { sessionId: string; shellPath?: string; remoteOS?: string } {
  const tabStore = useTabStore()
  const panelStore = usePanelStore()

  let panel

  if (panelTitle) {
    ensurePanelTitleIndex()
    // F-317: O(1) exact title match via the title→panelId index. The index
    // covers add/remove/rename via a vue watch; titles can duplicate, so we
    // verify the cached id still points at a panel with the requested title.
    let panelId: string | undefined
    const ids = panelTitleIndex.get(panelTitle)
    if (ids && ids.length > 0) {
      const candidate = panelStore.getPanel(ids[0])
      if (candidate && candidate.title === panelTitle) {
        panelId = ids[0]
      } else {
        // Stale entry (title just changed). Rebuild on demand.
        rebuildPanelTitleIndex(panelStore.panels as Map<string, { id: string; title: string }>)
        const refreshed = panelTitleIndex.get(panelTitle)
        if (refreshed && refreshed.length > 0) panelId = refreshed[0]
      }
    } else {
      // Title isn't in the index yet — rebuild and try once more.
      rebuildPanelTitleIndex(panelStore.panels as Map<string, { id: string; title: string }>)
      const refreshed = panelTitleIndex.get(panelTitle)
      if (refreshed && refreshed.length > 0) panelId = refreshed[0]
    }
    if (panelId) {
      panel = panelStore.getPanel(panelId)
    } else {
      // Suffix match for duplicate names: "title (id: xxx)". The id is
      // already known, so use getPanel for an O(1) by-id lookup.
      const suffixMatch = panelTitle.match(/^(.+)\s+\(id:\s*(.+)\)$/)
      if (suffixMatch) {
        panel = panelStore.getPanel(suffixMatch[2])
      }
    }
    if (!panel || !panel.sessionId) {
      throw new Error(`Panel "${panelTitle}" not found or has no active session`)
    }
  } else {
    // Default logic: first locked panel > active panel
    const lockedPanels = tabStore.getAILockedPanels()
    if (lockedPanels.length > 0) {
      panel = panelStore.getPanel(lockedPanels[0])
    }
    if (!panel) {
      const activeTab = tabStore.activeTab
      if (activeTab?.type === 'terminal' || activeTab?.type === 'settings') {
        panel = panelStore.getPanel(activeTab.panelId)
      } else if (activeTab?.type === 'workspace' && activeTab.activePanelId) {
        panel = panelStore.getPanel(activeTab.activePanelId)
      }
    }
    if (!panel || !panel.sessionId) {
      throw new Error('No active terminal session')
    }
  }

  const sessionId = panel.sessionId
  return {
    sessionId,
    shellPath: panel.config?.shellPath,
    remoteOS: useSessionStore().getRemoteOS(sessionId),
  }
}

function getShellNewline(shellPath?: string, remoteOS?: string): string {
  // Windows OpenSSH (cmd/PowerShell via ConPTY): the line terminator must be
  // CR — a lone LF is not accepted as Enter, so the command is echoed but never
  // executed. CR is what the Enter key actually emits in the terminal.
  if (remoteOS === 'windows-openssh') {
    return '\r'
  }
  const lowerShell = (shellPath || '').toLowerCase()
  if (lowerShell.includes('powershell') || lowerShell.includes('pwsh')) {
    return '\r'
  } else if (lowerShell.includes('cmd')) {
    return '\r\n'
  } else if (lowerShell.includes('bash') || lowerShell.includes('sh')) {
    return '\r\n'
  } else {
    return '\n'
  }
}

export async function executeCommand(
  command: string,
  timeoutMs: number = 60000,
  headLines: number = 50,
  tailLines: number = 300,
  shouldCancel?: () => boolean,
  panelTitle?: string
): Promise<ExecuteResult> {
  const { sessionId, shellPath, remoteOS } = resolveActiveSession(panelTitle)
  // Snapshot the prompt + its buffer row BEFORE the command is written, so
  // watchOutput knows where the command output starts on screen.
  const { promptLine, startRow } = capturePromptSnapshot(sessionId)
  const fullCommand = buildCommand(command, shellPath, remoteOS)
  const newline = getShellNewline(shellPath, remoteOS)

  await queuedSessionWrite(sessionId, fullCommand + newline)

  const { promise } = watchOutput(sessionId, promptLine, timeoutMs, shouldCancel, startRow)
  const result = await promise

  if (result.cancelled) {
    return {
      output: '',
      exitCode: -1,
      timedOut: false,
    }
  }

  if (result.timedOut) {
    const truncated = truncateOutput(result.output, headLines, tailLines)
    return {
      output: truncated,
      exitCode: -1,
      timedOut: true,
    }
  }

  return {
    output: truncateOutput(result.output, headLines, tailLines),
    exitCode: 0,
    timedOut: false,
  }
}

export interface StartResult {
  output: string
  started: boolean
}

export async function startCommand(command: string, panelTitle?: string): Promise<StartResult> {
  const { sessionId, shellPath, remoteOS } = resolveActiveSession(panelTitle)
  // Snapshot the prompt row BEFORE the command is written so the screen read
  // below starts where the command echo begins.
  const { startRow } = capturePromptSnapshot(sessionId)
  const newline = getShellNewline(shellPath, remoteOS)

  await queuedSessionWrite(sessionId, command + newline)

  // Collect output for 3 seconds, then return
  return new Promise((resolve) => {
    let output = ''
    const unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data;
      if (payload.id !== sessionId) return
      output += payload.data
     })

    setTimeout(() => {
      unsubscribe()
      // Prefer the screen buffer (redraw-resolved) over the raw stream; the
      // 3s window is far past the parse settle time, so read directly.
      const screen = readScreenFromRow(sessionId, startRow)
      resolve({
        output: (screen !== null ? screen : stripAnsi(output)).trim(),
        started: true,
      })
    }, 3000)
  })
}

export interface CaptureResult {
  output: string
}

export function captureTerminal(tailLines: number = 200, panelTitle?: string): CaptureResult {
  const { sessionId } = resolveActiveSession(panelTitle)

  const managed = getManagedTerminal(sessionId)
  if (!managed || !managed.terminal) {
    return { output: '' }
  }

  const terminal = managed.terminal
  const buffer = terminal.buffer.active
  const totalLines = buffer.length

  if (totalLines === 0) {
    return { output: '' }
  }

  // Find the last non-blank line — skip trailing empty space at the bottom of the terminal
  let lastContentLine = totalLines - 1
  while (lastContentLine >= 0) {
    const line = buffer.getLine(lastContentLine)
    if (line && line.translateToString().trim() !== '') break
    lastContentLine--
  }

  if (lastContentLine < 0) {
    return { output: '' }
  }

  // Capture up to tailLines lines, ending at the last non-blank line
  const startLine = Math.max(0, lastContentLine - tailLines + 1)
  const lines: string[] = []

  for (let i = startLine; i <= lastContentLine; i++) {
    const line = buffer.getLine(i)
    if (line) lines.push(line.translateToString())
  }

  return { output: lines.join('\n') }
}

export interface CollectResult {
  output: string
  timedOut: boolean
  completed: boolean
}

// Collect output passively — no command is sent. Detects completion by watching
// for the shell prompt to reappear (same idle heuristic as watchOutput), so the
// call returns as soon as the running command finishes instead of always waiting
// for the full timeout.
export async function collectOutput(
  timeoutMs: number = 30000,
  headLines: number = 100,
  tailLines: number = 300,
  shouldCancel?: () => boolean,
  panelTitle?: string
): Promise<CollectResult> {
  const { sessionId } = resolveActiveSession(panelTitle)
  const { promptLine, startRow } = capturePromptSnapshot(sessionId)

  const { promise } = watchOutput(sessionId, promptLine, timeoutMs, shouldCancel, startRow)
  const result = await promise

  if (result.cancelled) {
    return { output: '', timedOut: false, completed: false }
  }

  return {
    output: truncateOutput(result.output, headLines, tailLines),
    timedOut: result.timedOut,
    completed: !result.timedOut,
  }
}

interface SendKeyResult {
  output: string
}

export async function sendTerminalKey(
  input?: string,
  control?: 'ctrl_c' | 'ctrl_d' | 'enter',
  sendEnter: boolean = true,
  panelTitle?: string
): Promise<SendKeyResult> {
  const { sessionId, shellPath, remoteOS } = resolveActiveSession(panelTitle)

  // Snapshot the prompt row before writing so the ctrl_c / ctrl_d response
  // below can be read off the screen buffer.
  const { startRow } = capturePromptSnapshot(sessionId)

  let data: string
  if (control) {
    if (control === 'ctrl_c') {
      data = '\x03'
    } else if (control === 'ctrl_d') {
      data = '\x04'
    } else if (control === 'enter') {
      data = remoteOS === 'windows-openssh' ? '\r' : '\n'
    } else {
      data = ''
    }
  } else if (input !== undefined && input !== '') {
    data = input
  } else {
    throw new Error('Either input or control must be provided')
  }

  // Append shell-appropriate newline when send_enter is true and input was provided
  if (sendEnter && !control && input !== undefined && input !== '') {
    data += getShellNewline(shellPath, remoteOS)
  }

  await queuedSessionWrite(sessionId, data)

  // For ctrl_c / ctrl_d: passively capture shell response for a short time.
  // No marker injection — avoids corrupting interactive program input.
  if (control === 'ctrl_c' || control === 'ctrl_d') {
    return new Promise((resolve) => {
      let output = ''
      const unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data;
        if (payload.id !== sessionId) return
        output += payload.data
       })
      setTimeout(() => {
        unsubscribe()
        // Prefer the screen buffer (redraw-resolved) over the raw stream; the
        // 1s window is past the parse settle time, so read directly.
        const screen = readScreenFromRow(sessionId, startRow)
        resolve({ output: (screen !== null ? screen : stripAnsi(output)).trim() || '(input sent)' })
      }, 1000)
    })
  }

  return { output: '(input sent)' }
}

// Build the string sent to the shell. No completion marker is appended — the
// AI executor detects completion by watching for the shell prompt to reappear
// (see watchOutput). This keeps the terminal clean and, for POSIX shells,
// avoids corrupting multi-line input such as here-documents. A single leading
// space keeps the command out of shell history (HISTCONTROL=ignorespace).
function buildCommand(command: string, shellPath?: string, remoteOS?: string): string {
  const lower = (shellPath || '').toLowerCase()
  if (remoteOS === 'windows-openssh' || lower.includes('powershell') || lower.includes('pwsh') || lower.includes('cmd')) {
    return command
  }
  // bash / sh / zsh / fish
  return ` ${command}`
}

// Simple ANSI stripper for extracting readable text from terminal output
function stripAnsi(str: string): string {
  return str
    .replace(/\x1B\[[0-9;?]*[A-Za-z]/g, '')
    .replace(/\x1B\][\s\S]*?(?:\x07|\x1B\\)/g, '')
    .replace(/\x1B[()[\]#\^%@>=]/g, '')
    .replace(/\x1B[/!_]./g, '')
    .replace(/\x1B./g, '')
}
