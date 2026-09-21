import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { Unicode11Addon } from '@xterm/addon-unicode11'
import { SearchAddon } from '@xterm/addon-search'
import { ImageAddon } from '@xterm/addon-image'
import { ClipboardAddon, Base64 } from '@xterm/addon-clipboard'
import { ProgressAddon, type IProgressState } from '@xterm/addon-progress'
import { getXtermTheme } from '../composables/useTerminal'
import { resolveXtermBackground, applyTerminalBgVar, resolveTerminalThemeName } from '../composables/useTerminalTheme'
import { useSettingsStore } from '../stores/settingsStore'
import { useLocalStateStore } from '../stores/localStateStore'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import type { CustomTerminalTheme } from '../types/settings'
import { formatFontFamily } from '../utils/formatFontFamily'
import { installImeCompatibilityPatch } from '../utils/xtermImeCompatibility'
import {
  bufferRowSource,
  createLineRegistry,
  realignRegistry,
  type LineRegistryState,
} from './terminalTimestamps'

export interface TerminalOptions {
  fontSize?: number
  fontFamily?: string
  // Secondary family (e.g. CJK) appended behind fontFamily at render time.
  fallbackFont?: string
  // Weight for regular terminal text (variable-font weights for JetBrains).
  fontWeight?: number
  themeName?: string
  scrollback?: number
}

export interface ManagedTerminal {
  terminal: Terminal
  fitAddon: FitAddon
  searchAddon: SearchAddon
  unicodeAddon: Unicode11Addon
  progressAddon: ProgressAddon
  container: HTMLElement | null
  refs: Set<string>
  options: TerminalOptions
  disposeTimer: ReturnType<typeof setTimeout> | null
  /** Whether this terminal was newly created (not reused via timer cancellation). */
  isNew: boolean
  /** Shared generation counter across all components using this terminal.
   * Bumped each time any component registers an onData handler. Callbacks
   * capture a snapshot and bail out if it no longer matches, preventing
   * double input when multiple KeepAlive-cached components share the same
   * terminal instance. */
  onDataGeneration: number
  /** Logical-line registry (sequential number + birth/completion time per
   * shell line), keyed by absolute row index (lineOffset-compensated). Backs
   * the gutter's line-number and time columns. Kept on the shared terminal so
   * it survives KeepAlive and drag-across-panes. */
  lineRegistry: LineRegistryState
  /** Absolute-row offset accumulated from scrollback trimming, so both the
   * line-number and timestamp columns stay continuous as old lines drop off
   * the top of the buffer. */
  lineOffset: number
  /** Subscription to the normal-buffer line-collection onTrim event. */
  trimDispose: { dispose(): void } | null
  /** Subscription to terminal.onResize — reflows the buffer, so the registry
   * must be re-keyed to the rows lines now start at. */
  resizeDispose: { dispose(): void } | null
  /** Subscription to ProgressAddon.onChange — routes OSC 9;4 progress
   * state into the tab store for the tab-bar indicator. */
  progressDispose: { dispose(): void } | null
  /** IME compatibility patch installed on this terminal (macOS only). */
  imeDispose: { dispose(): void } | null
}

const terminals = new Map<string, ManagedTerminal>()

// Route a progress state from a session's terminal to the tab that displays
// it (session → panel → tab, same resolution the notification dots use).
function setTabProgressForSession(sessionId: string, state: IProgressState | null): void {
  const panelStore = usePanelStore()
  const tabStore = useTabStore()
  for (const [panelId, panel] of panelStore.panels) {
    if (panel.sessionId !== sessionId) continue
    const tab = tabStore.tabs.find(t =>
      (t.type === 'terminal' && t.panelId === panelId) ||
      (t.type === 'workspace' && t.panelIds.includes(panelId))
    )
    if (tab) tabStore.setTabProgress(tab.id, state)
    return
  }
}

// F-027: scrollback limit applied while the terminal sits in the hidden
// holding container (between detach and re-attach). Restored on re-attach
// so users keep their full scrollback when they revisit the tab.
const INACTIVE_SCROLLBACK = 500

// Hidden holding containers to keep terminal elements alive when no
// component is actively displaying them. detachTerminal moves elements
// here; attachTerminal picks them up regardless of where they are.
const holding = new Map<string, HTMLDivElement>()
function getHolding(sessionId: string): HTMLDivElement {
  let el = holding.get(sessionId)
  if (!el) {
    el = document.createElement('div')
    el.style.display = 'none'
    holding.set(sessionId, el)
  }
  return el
}

export function acquireTerminal(
  sessionId: string,
  ref: string,
  options: TerminalOptions,
  customThemes?: CustomTerminalTheme[]
): Terminal {
  let managed = terminals.get(sessionId)

  if (managed) {
    // Cancel any pending disposal — terminal is still needed
    if (managed.disposeTimer) {
      clearTimeout(managed.disposeTimer)
      managed.disposeTimer = null
    }
    managed.isNew = false
  } else {
    const cursorBlink = useSettingsStore().settings.terminal.cursorBlink ?? true
    const wordSeparator = useSettingsStore().settings.terminal.wordSeparator
      || '\\ :;~`!@#$%^&*()=+|[]{}\'",<>?'
    const ls = useLocalStateStore()
    const theme = resolveXtermBackground(
      getXtermTheme(resolveTerminalThemeName(options.themeName, useSettingsStore().resolvedAppTheme), customThemes),
      ls.state.backgroundEnabled,
      ls.state.backgroundImage
    )
    // F-036: italic SGR-3 is handled natively by xterm.js — its DOM
    // renderer emits <span class="xterm-italic">…</span> and applies
    // `font-style: italic` via xterm.css. No @xterm/addon-italic package
    // is published on npm (verified: npm view @xterm/addon-italic → 404),
    // and xterm.js already routes the italic attribute through the
    // browser's CSS font-matching — so the JetBrains Mono Variable /
    // Consolas / Courier New chain in fontFamily already renders italic
    // faces when the system has them.
    //
    // F-037: DEC mode 2026 (synchronized output) bracketing used by
    // Claude Code's thinking-block redraws was not honored by xterm.js
    // v5.5 — the parser core had no handler for SET/RESET 2026. The v6
    // upgrade (PR #437) is what addresses the thinking-block flicker.
    //
    // F-038: bracketed-paste (`\e[?2004h`) and mouse-reporting modes
    // (1000/1006/1015) are handled by the xterm.js parser core itself
    // and surfaced via `terminal.modes`. This is a verification gap,
    // not a production bug — a smoke test asserting
    // terminal.modes.bracketedPasteMode after writing the sequence
    // would catch a regression on future upgrades.
    const terminal = new Terminal({
      fontSize: options.fontSize ?? 13,
      fontFamily: formatFontFamily(options.fontFamily ?? 'JetBrains Mono Variable', options.fallbackFont),
      fontWeight: options.fontWeight ?? 400,
      theme,
      cursorBlink,
      cursorStyle: useSettingsStore().settings.terminal.cursorStyle ?? 'block',
      rightClickSelectsWord: false,
      scrollback: options.scrollback ?? 2500,
      allowProposedApi: true,
      allowTransparency: true,
      // Boost text/background contrast (F-039): xterm auto-brightens or
      // darkens the foreground toward black/white until the configured
      // minimumContrast ratio (1 = off) is met — only for cells below it,
      // normal text is untouched. Fixes ls's colored blocks for 777 dirs
      // (e.g. ow=34;42 blue-on-green is ~1.3:1, illegible) staying readable.
      minimumContrastRatio: useSettingsStore().settings.terminal.minimumContrast ?? 4.5,
      wordSeparator,
    })

    // ctrl+wheel is font zoom (App.vue). xterm v6 reports wheel events to the
    // app regardless of defaultPrevented, so vim would scroll on zoom too.
    terminal.attachCustomWheelEventHandler(ev => !ev.ctrlKey)

    const fitAddon = new FitAddon()
    const searchAddon = new SearchAddon()
    const unicodeAddon = new Unicode11Addon()
    // Terminal image support (sixel + iTerm2 OSC 1337). The addon parses the
    // sequences itself and draws them on its own canvas layer, so it works
    // with the default DOM renderer. DCS sixel sequences are reassembled
    // chunk-wise in BaseTerminal's render path (dcsReassembler) BEFORE they
    // reach xterm, so the parser only ever sees complete sequences.
    const imageAddon = new ImageAddon()
    // OSC 52 clipboard: remote programs (vim "+ register, tmux, ssh through
    // chains) can WRITE to the local clipboard. Reads are deliberately
    // answered with an empty report instead of a rejection — the addon does
    // not catch provider promise rejections (verified in its source), so a
    // rejected read would surface as an unhandled rejection, and refusing to
    // read also keeps remote processes from exfiltrating local clipboard
    // contents. Writes swallow failures (window unfocused etc.) for the
    // same unhandled-rejection reason.
    const clipboardAddon = new ClipboardAddon(new Base64(), {
      readText: () => '',
      writeText: (_selection, text) => {
        navigator.clipboard.writeText(text).catch(() => { /* non-critical */ })
      },
    })
    // ConEmu-style OSC 9;4 progress, surfaced as a tab-bar indicator.
    const progressAddon = new ProgressAddon()

    terminal.loadAddon(fitAddon)
    terminal.loadAddon(searchAddon)
    terminal.loadAddon(unicodeAddon)
    terminal.loadAddon(imageAddon)
    terminal.loadAddon(clipboardAddon)
    terminal.loadAddon(progressAddon)
    // F-035: charSizeCompat / ITheme.codeBlockBackground do not exist in
    // xterm.js v5.5. The Unicode 11 activeVersion below is the available
    // WC-width alignment — the backend PTY uses the same Unicode 11
    // tables so column counts match. The v6 upgrade (PR #437) is what
    // unlocks extended-theme support.
    //
    // Activate Unicode 11 widths (default v6 miscounts CJK cells). Must come
    // AFTER loadAddon — the unicode property is provided by the addon.
    terminal.unicode.activeVersion = '11'

    // IME compatibility (macOS) is installed in attachTerminal, after
    // terminal.open() — the patch needs textarea/_compositionHelper, which
    // xterm only creates there.
    managed = {
      terminal,
      fitAddon,
      searchAddon,
      unicodeAddon,
      progressAddon,
      container: null,
      refs: new Set(),
      options,
      disposeTimer: null,
      isNew: true,
      onDataGeneration: 0,
      lineRegistry: createLineRegistry(),
      lineOffset: 0,
      trimDispose: null,
      resizeDispose: null,
      progressDispose: null,
      imeDispose: null,
    }

    // Track scrollback trimming so line-numbers / timestamps stay continuous
    // as old lines drop off the top of the buffer. Internal API — guarded.
    // Doesn't survive terminal re-creation, but a fresh terminal restarts at 0.
    // Snapshot `managed` into a const so the onTrim closure doesn't re-widen it.
    const m = managed
    try {
      const core = (terminal as any)._core
      const lines = core?._bufferService?.buffers?.normal?.lines
      if (typeof lines?.onTrim === 'function') {
        m.trimDispose = lines.onTrim((amount: number) => {
          // NOTE: deliberately no entry pruning here. "key < lineOffset ⇒
          // off-buffer" only holds for append+trim growth; a resize reflow
          // also fires trims while INSERTING physical rows for wrapped lines,
          // so surviving content's absolute coordinates shift and live
          // entries would be deleted (tail lines lose their number/time).
          // Off-buffer entries are bounded by the size cap in the registry
          // and dropped wholesale by realignRegistry on the next resize.
          m.lineOffset += amount
        })
      }
    } catch { /* noop */ }

    // A resize reflows the (normal) buffer: physical rows move but logical
    // lines keep their identity. Re-key the registry so each entry points at
    // the row its line now starts at. Uses the normal buffer explicitly so a
    // resize while an alternate-screen app is up still realigns.
    m.resizeDispose = terminal.onResize(() => {
      const buf = terminal.buffer.normal
      realignRegistry(m.lineRegistry, {
        lineOffset: m.lineOffset,
        cursorAbs: m.lineOffset + buf.baseY + buf.cursorY,
        source: bufferRowSource(buf),
      })
    })

    // OSC 9;4 progress → tab-bar indicator. One subscription per terminal
    // (at creation) so KeepAlive re-mounts never stack listeners; state 0
    // clears the indicator.
    m.progressDispose = progressAddon.onChange(state => {
      setTabProgressForSession(sessionId, state.state === 0 ? null : state)
    })

    terminals.set(sessionId, m)
  }

  managed.refs.add(ref)
  return managed.terminal
}

export function releaseTerminal(sessionId: string, ref: string): void {
  const managed = terminals.get(sessionId)
  if (!managed) return

  managed.refs.delete(ref)

  if (managed.refs.size === 0) {
    // Delay disposal to survive drag-and-drop lifecycle race.
    // If acquireTerminal is called within 500ms, the timer is cancelled.
    managed.disposeTimer = setTimeout(() => {
      managed.trimDispose?.dispose()
      managed.trimDispose = null
      managed.resizeDispose?.dispose()
      managed.resizeDispose = null
      managed.progressDispose?.dispose()
      managed.progressDispose = null
      setTabProgressForSession(sessionId, null)
      managed.imeDispose?.dispose()
      managed.imeDispose = null
      managed.terminal.dispose()
      terminals.delete(sessionId)
    }, 500)
  }
}

export function disposeTerminal(sessionId: string): void {
  const managed = terminals.get(sessionId)
  if (!managed) return
  if (managed.disposeTimer) {
    clearTimeout(managed.disposeTimer)
  }
  managed.trimDispose?.dispose()
  managed.trimDispose = null
  managed.resizeDispose?.dispose()
  managed.resizeDispose = null
  managed.progressDispose?.dispose()
  managed.progressDispose = null
  setTabProgressForSession(sessionId, null)
  managed.imeDispose?.dispose()
  managed.imeDispose = null
  managed.terminal.dispose()
  terminals.delete(sessionId)
}

// Transfer a terminal from oldSessionId to newSessionId so the
// terminal buffer is preserved across session reconnects.
export function transferTerminal(oldSessionId: string, newSessionId: string): boolean {
  const managed = terminals.get(oldSessionId)
  if (!managed) return false
  terminals.delete(oldSessionId)
  terminals.set(newSessionId, managed)
  // Re-target the progress subscription: its closure captured oldSessionId,
  // and events for the old id would resolve to no panel and strand a stale
  // indicator on the previous tab.
  managed.progressDispose?.dispose()
  managed.progressDispose = managed.progressAddon.onChange(state => {
    setTabProgressForSession(newSessionId, state.state === 0 ? null : state)
  })
  setTabProgressForSession(oldSessionId, null)
  return true
}

export function attachTerminal(sessionId: string, container: HTMLElement): void {
  const managed = terminals.get(sessionId)
  if (!managed) return
  if (managed.container === container) return

  managed.container = container

  // F-027: restore the user-configured scrollback that detachTerminal
  // shrank while the terminal sat in the holding container. Without this
  // re-attach, users would see only the last 500 lines after every
  // drag-out / re-merge cycle even though the full history is still
  // replayable from sessionStore on a fresh mount.
  if (managed.options.scrollback != null &&
      managed.terminal.options.scrollback != managed.options.scrollback) {
    managed.terminal.options.scrollback = managed.options.scrollback
  }

  if (!managed.terminal.element) {
    managed.terminal.open(container)
  } else {
    container.appendChild(managed.terminal.element)
  }

  // IME compatibility (macOS): deliver single-char input directly when an
  // IME marks keystrokes with the phantom keyCode 229, instead of relying on
  // xterm's racy deferred textarea diff that drops chars under fast typing.
  // Must run after open() — that is where xterm creates the textarea and the
  // composition helper the patch hooks into; installing at construction time
  // silently no-ops.
  if (!managed.imeDispose) {
    managed.imeDispose = installImeCompatibilityPatch(managed.terminal)
  }

  // terminal.element only exists after open(), so the padding-ring color is
  // published here rather than at construction time.
  applyTerminalBgVar(managed.terminal, managed.terminal.options.theme ?? {})

  // Wait for the font to actually paint before measuring cell width — if
  // we measure while JetBrains Mono Variable (or whatever the user picked)
  // is still loading, fitAddon reads a fallback width and reports wrong
  // cols. document.fonts.ready resolves once every face in the page is
  // loaded; that's the signal Claude Code (and any TUI app) needs to see
  // a consistent terminal size from the first byte.
  const fontReady = (typeof document !== 'undefined' && document.fonts && document.fonts.ready)
    ? document.fonts.ready
    : Promise.resolve()
  fontReady.finally(() => {
    // Two rAFs: one for the .xterm element to receive its size, one for
    // the canvas to render with the now-loaded font.
    requestAnimationFrame(() => requestAnimationFrame(() => managed.fitAddon.fit()))
  })
}

export function detachTerminal(sessionId: string, container: HTMLElement): void {
  const managed = terminals.get(sessionId)
  if (!managed) return
  // F-027: shrink xterm's pixel buffer while in the hidden holding
  // container. detach → attach within the disposeTimer window still
  // restores the original scrollback so users see their full history on
  // re-attach. Without this the canvas + row objects for the trimmed
  // rows stay pinned in the holding container's offscreen DOM and
  // accumulate over the session.
  if (managed.terminal.options.scrollback != null &&
      managed.terminal.options.scrollback > INACTIVE_SCROLLBACK) {
    managed.terminal.options.scrollback = INACTIVE_SCROLLBACK
  }
  // Move element to a holding container so it survives component destruction.
  // The next attachTerminal picks it up from there.
  if (managed.terminal.element?.parentElement === container) {
    getHolding(sessionId).appendChild(managed.terminal.element)
  }
  if (managed.container === container) {
    managed.container = null
  }
}

export function getTerminal(sessionId: string): Terminal | undefined {
  return terminals.get(sessionId)?.terminal
}

export function getManagedTerminal(sessionId: string): ManagedTerminal | undefined {
  return terminals.get(sessionId)
}

/** Return the xterm-measured cols/rows for an existing session, or
 * {0,0} if the session has no terminal yet. Callers use this to learn
 * the actual size to send to the backend as InitialCols/Rows BEFORE
 * CreateSession so the remote PTY starts at the right dimensions. */
export function getTerminalSize(sessionId: string): { cols: number; rows: number } {
  const m = terminals.get(sessionId)
  if (!m) return { cols: 0, rows: 0 }
  return { cols: m.terminal.cols, rows: m.terminal.rows }
}

/** Poll for the terminal to report a non-zero size, up to timeoutMs.
 * Returns the latest size (possibly {0,0}) if the timeout elapses —
 * callers should fall back to defaults rather than treat it as an error. */
export async function waitForTerminalSize(
  sessionId: string,
  timeoutMs = 1500
): Promise<{ cols: number; rows: number }> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const s = getTerminalSize(sessionId)
    if (s.cols > 0 && s.rows > 0) return s
    await new Promise(r => setTimeout(r, 30))
  }
  return getTerminalSize(sessionId)
}

/** Bump the shared onData generation counter for the given terminal.
 * Returns the NEW generation value. Callers should capture this value
 * in their onData callback and bail out if the terminal's current
 * generation no longer matches. */
export function bumpOnDataGeneration(sessionId: string): number {
  const managed = terminals.get(sessionId)
  if (!managed) return 0
  const next = ++managed.onDataGeneration
  return next
}
