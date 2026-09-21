// Overlay keyword highlighter. Instead of rewriting the pty stream, it
// re-scans the xterm buffer after writes/scrolls and recolors matched cells
// through the CellColorOverrideStore API patched into our @xterm/xterm fork
// (setCellColorOverrides). Colors are applied to the original rendered text
// inside the DOM renderer — no overlay DOM of our own, no alignment concerns,
// no interaction with the data stream.
//
// The API takes absolute (ydisp-independent) buffer line indexes, which stay
// stable as content scrolls, so overrides set once keep tracking their line.
// Invalidations needed on our side: scrollback trims (sentinel marker),
// resize reflows, and alternate-buffer switches — each wipes the store.
//
// Performance machinery: visible-viewport-only scans (bottom-up so fresh
// output highlights first), an LRU over immutable scrollback lines, a
// per-refresh time budget with rAF continuation, and a write debounce with a
// max-wait escape so sustained output still gets highlighted. Matching is per
// physical line.
import type { Terminal as XTerm, IBufferCell, IBufferLine, ICellColorSpan, IDisposable } from '@xterm/xterm'
import { matchTextSpans, HIGHLIGHT_RULES, type HighlightCategory } from './highlightRules'
import { useSettingsStore } from '../stores/settingsStore'

// Category → xterm theme key, mirroring the legacy inject renderer's SGR
// choices (30-37/90-97 follow the theme palette; we read the palette here).
const CATEGORY_THEME_KEY: Record<HighlightCategory, string> = {
  url: 'blue',
  host: 'magenta',
  path: 'magenta',
  datetime: 'brightBlue',
  string: 'yellow',
  success: 'green',
  error: 'red',
  warning: 'yellow',
  info: 'cyan',
  brace: 'brightMagenta',
}

// xterm.js default palette values, used when the active theme doesn't
// define the expected key.
const FALLBACK_COLORS: Record<string, string> = {
  red: '#cd3131',
  green: '#0dbc79',
  yellow: '#e5e510',
  blue: '#2472c8',
  magenta: '#bc3fbc',
  cyan: '#11a8cd',
  brightBlue: '#2f9ded',
  brightMagenta: '#d33682',
}

/** Resolve the highlight color for every category from the terminal's
 * current theme palette. */
export function resolveHighlightColors(theme: unknown): Record<HighlightCategory, string> {
  const t = theme as Record<string, string | undefined> | undefined
  const colors = {} as Record<HighlightCategory, string>
  for (const category of Object.keys(CATEGORY_THEME_KEY) as HighlightCategory[]) {
    colors[category] = t?.[CATEGORY_THEME_KEY[category]] ?? FALLBACK_COLORS[CATEGORY_THEME_KEY[category]] ?? '#cccccc'
  }
  return colors
}

/** Per-column highlight color for one buffer line (undefined = no highlight).
 * Used by the scrollbar screen preview to match the terminal's highlighting. */
export function getLineHighlightColors(
  line: IBufferLine,
  cols: number,
  theme: unknown,
): Array<string | undefined> {
  const colors = resolveHighlightColors(theme)
  const perCol: Array<string | undefined> = new Array(cols)
  const lineText = line.translateToString(true, 0, cols)
  if (!lineText) return perCol
  const hasMultibyte = /[^\x00-\xFF]/.test(lineText)
  const cellMap = hasMultibyte
    ? buildStringToCellMap(line, lineText.length, cols)
    : null
  const { spans } = matchTextSpans(lineText, HIGHLIGHT_RULES)
  for (const span of spans) {
    const color = colors[span.category]
    const cellStartCol = cellMap ? (cellMap[span.start] ?? span.start) : span.start
    const cellEndCol = cellMap ? (cellMap[span.end] ?? span.end) : span.end
    for (let col = cellStartCol; col < cellEndCol; col++) perCol[col] = color
  }
  return perCol
}

interface HighlightSpan {
  cellStartCol: number
  cellWidth: number
  category: HighlightCategory
}

interface RefreshBudget {
  deadlineMs: number
  hitLimit: boolean
}

// Minimum spacing between synchronous (first-paint) scans. onWriteParsed
// runs in the write task, before the render frame's rAF — scanning there
// colors rows before their FIRST paint. Writes following within the same
// frame fall back to the trailing debounce and catch up on the next scan.
const SYNC_SCAN_MIN_INTERVAL_MS = 10
// Trailing catch-up only: batches writes that arrived inside the sync-scan
// gate window (e.g. output stopping right after a scan). One frame long —
// anything longer just delays those rows' color.
const DEBOUNCE_MS = 16
// Sustained output keeps resetting the trailing write debounce; after this
// long a refresh runs anyway so highlights keep up with a long stream
// instead of only appearing once the output ends.
const WRITE_MAX_WAIT_MS = 500
const SCROLL_IDLE_DEBOUNCE_MS = 120
const MAX_REFRESH_TIME_MS = 3
const MAX_CACHED_MATCH_LINES = 3000

  /** Map string indices from translateToString to cell columns. Needed only
   * for lines containing wide chars (CJK), where string index ≠ cell column. */
function buildStringToCellMap(
  line: IBufferLine,
  stringLength: number,
  maxCols: number,
  scratchCell?: IBufferCell,
  ): number[] {
  const map: number[] = []
  let col = 0
  let cellEndCol = 0
  // Mirror translateToString's traversal: advance by `width || 1` so wide-char
  // continuation cells (width 0) are skipped while NUL cells (also width 0,
  // emitted as a space) still contribute one entry.
  while (col < maxCols && map.length < stringLength) {
      const cell = scratchCell ? line.getCell(col, scratchCell) : line.getCell(col)
      if (!cell) break
      const chars = cell.getChars()
      const width = cell.getWidth()
      const stride = width || 1
      if (chars.length === 0) {
        map.push(col)
      } else {
        for (let i = 0; i < chars.length; i++) map.push(col)
      }
      cellEndCol = col + stride
      col += stride
  }
  map.push(cellEndCol) // sentinel: end position
  return map
  }

export class OverlayHighlighter {
  private term: XTerm
  /** Immutable (scrollback) absolute line index → resolved spans, including []. */
  private lineMatchCache = new Map<number, HighlightSpan[]>()
  private writeDebounceTimer: ReturnType<typeof setTimeout> | null = null
  private writePendingSince = 0
  private lastSyncScan = -Infinity
  private scrollDebounceTimer: ReturnType<typeof setTimeout> | null = null
  private continuationFrame: number | null = null
  private disposables: IDisposable[] = []
  private dead = false
  private lastViewportY = -1

  /** Marker anchored at buffer line 0; disposed by xterm when that line is
   * trimmed from scrollback, letting us detect cache-wide index shifts. */
  private sentinelMarker: unknown = null
  private sentinelDisposable: IDisposable | null = null
  private bufferTrimmed = false
  /** Active buffer kind at the last refresh; a switch means every override
   * and cached span is stale (full-screen app took over / released). */
  private lastBufferType: string | null = null

  constructor(term: XTerm) {
    this.term = term

    this.disposables.push(
      this.term.onWriteParsed(() => this.triggerWriteRefresh()),
      this.term.onResize(() => {
        this.invalidateAll()
        this.lastViewportY = -1
        this.triggerWriteRefresh()
      }),
      this.term.onRender(() => {
        const currentViewportY = this.term.buffer.active?.viewportY ?? 0
        if (currentViewportY !== this.lastViewportY) {
          this.lastViewportY = currentViewportY
          this.triggerScrollRefresh()
        }
      }),
    )
  }

  /** Kick off an initial pass. The enable decision itself is re-evaluated on
   * every refresh, so toggling the setting in the UI works live without
   * re-attaching. */
  public attach(): void {
    this.triggerWriteRefresh()
  }

  public dispose(): void {
    this.dead = true
    this.invalidateAll()
    for (const d of this.disposables) d.dispose()
    this.disposables = []
  }

  private isEnabled(): boolean {
    if (this.dead) return false
    return useSettingsStore().settings.terminal.highlightEnabled ?? true
  }

  /** Public mirror of isEnabled() for render-mirroring consumers. */
  public isActive(): boolean {
    return this.isEnabled()
  }

  private clearTimers(): void {
    if (this.writeDebounceTimer) {
      clearTimeout(this.writeDebounceTimer)
      this.writeDebounceTimer = null
    }
    if (this.scrollDebounceTimer) {
      clearTimeout(this.scrollDebounceTimer)
      this.scrollDebounceTimer = null
    }
    this.cancelContinuationRefresh()
  }

  private invalidateAll(): void {
    this.clearTimers()
    this.term.clearCellColorOverrides()
    this.lineMatchCache.clear()
    this.disposeSentinel()
    this.bufferTrimmed = false
  }

  private installSentinel(): void {
    this.disposeSentinel()
    const buffer = this.term.buffer.active
    if (!buffer || buffer.length === 0) return
    const cursorAbsoluteY = buffer.baseY + buffer.cursorY
    const marker = this.term.registerMarker(-cursorAbsoluteY)
    if (!marker || marker.line < 0) return
    this.sentinelMarker = marker
    this.sentinelDisposable = marker.onDispose(() => {
      this.bufferTrimmed = true
      this.sentinelMarker = null
      this.sentinelDisposable = null
    })
  }

  private disposeSentinel(): void {
    this.sentinelDisposable?.dispose()
    ;(this.sentinelMarker as { dispose(): void } | null)?.dispose()
    this.sentinelMarker = null
    this.sentinelDisposable = null
  }

  private canRefresh(): boolean {
    if (!this.isEnabled() || this.dead) return false
    try {
      // Touch the buffer so a disposed terminal flips us off here rather
      // than throwing inside the scan.
      void this.term.buffer.active.type
      return true
    } catch {
      this.dead = true
      return false
    }
  }

  private triggerWriteRefresh(): void {
    if (!this.canRefresh()) return
    if (this.scrollDebounceTimer !== null) return
    const now = performance.now()
    // Scan synchronously when the last scan isn't brand new: this runs before
    // the render frame, so new rows are painted colored from the start —
    // no white flash. Rapid follow-up writes within the same frame batch
    // through the trailing debounce instead.
    if (now - this.lastSyncScan >= SYNC_SCAN_MIN_INTERVAL_MS) {
      this.lastSyncScan = now
      this.writePendingSince = now
      this.refreshViewport()
      return
    }
    if (this.writeDebounceTimer) {
      clearTimeout(this.writeDebounceTimer)
    } else {
      this.writePendingSince = now
    }
    if (now - this.writePendingSince >= WRITE_MAX_WAIT_MS) {
      this.writeDebounceTimer = null
      this.refreshViewport()
      return
    }
    this.writeDebounceTimer = setTimeout(() => {
      this.writeDebounceTimer = null
      this.refreshViewport()
    }, DEBOUNCE_MS)
  }

  /** Trailing debounce: scrolling preempts pending highlight work. */
  private triggerScrollRefresh(): void {
    if (!this.canRefresh()) return
    if (this.writeDebounceTimer !== null) {
      clearTimeout(this.writeDebounceTimer)
      this.writeDebounceTimer = null
    }
    this.cancelContinuationRefresh()
    if (this.scrollDebounceTimer !== null) clearTimeout(this.scrollDebounceTimer)
    this.scrollDebounceTimer = setTimeout(() => {
      this.scrollDebounceTimer = null
      this.refreshViewport()
    }, SCROLL_IDLE_DEBOUNCE_MS)
  }

  /** A refresh hit its time budget mid-viewport — continue on the next frame
   * so the rest of the viewport completes without waiting for another
   * terminal event. */
  private triggerContinuationRefresh(): void {
    if (!this.canRefresh()) return
    if (this.continuationFrame !== null || this.scrollDebounceTimer !== null) return
    this.continuationFrame = requestAnimationFrame(() => {
      this.continuationFrame = null
      this.refreshViewport()
    })
  }

  /** Re-apply overrides after a theme switch: colors are resolved per
   * refresh from the terminal's palette, so a forced pass over the viewport
   * rewrites them with the new theme's colors (and wiping the store drops
   * the stale colors baked into off-viewport rows). */
  public forceRefresh(): void {
    if (!this.canRefresh()) return
    this.term.clearCellColorOverrides()
    this.lineMatchCache.clear()
    this.lastViewportY = -1
    this.refreshViewport()
  }

  private cancelContinuationRefresh(): void {
    if (this.continuationFrame !== null) {
      cancelAnimationFrame(this.continuationFrame)
      this.continuationFrame = null
    }
  }

  private getCachedSpans(lineY: number): HighlightSpan[] | undefined {
    const spans = this.lineMatchCache.get(lineY)
    if (spans === undefined) return undefined
    // LRU touch
    this.lineMatchCache.delete(lineY)
    this.lineMatchCache.set(lineY, spans)
    return spans
  }

  private setCachedSpans(lineY: number, spans: HighlightSpan[]): void {
    this.lineMatchCache.delete(lineY)
    this.lineMatchCache.set(lineY, spans)
    while (this.lineMatchCache.size > MAX_CACHED_MATCH_LINES) {
      const oldest = this.lineMatchCache.keys().next().value
      if (oldest === undefined) break
      this.lineMatchCache.delete(oldest)
    }
  }


  private isBudgetExhausted(budget: RefreshBudget): boolean {
    if (budget.hitLimit) return true
    if (performance.now() > budget.deadlineMs) {
      budget.hitLimit = true
      return true
    }
    return false
  }

  private scanPhysicalLine(
    line: IBufferLine,
    cols: number,
    scratchCell: IBufferCell,
    budget: RefreshBudget,
  ): { spans: HighlightSpan[]; complete: boolean } {
    const lineText = line.translateToString(true, 0, cols)
    if (!lineText) return { spans: [], complete: true }

    const hasMultibyte = /[^\x00-\xFF]/.test(lineText)
    const cellMap = hasMultibyte
      ? buildStringToCellMap(line, lineText.length, cols, scratchCell)
      : null

    const result = matchTextSpans(lineText, HIGHLIGHT_RULES, {
      shouldStop: () => this.isBudgetExhausted(budget),
    })

    // String index → cell column: the renderer's override consumer walks
    // spans with a monotonic pointer, so they must be in column order
    // (matchTextSpans already sorts by string position and the map is
    // monotonic).
    const spans: HighlightSpan[] = []
    for (const span of result.spans) {
      const cellStartCol = cellMap ? (cellMap[span.start] ?? span.start) : span.start
      const cellEndCol = cellMap ? (cellMap[span.end] ?? span.end) : span.end
      const cellWidth = cellEndCol - cellStartCol
      if (cellWidth <= 0) continue
      spans.push({ cellStartCol, cellWidth, category: span.category })
    }
    return { spans, complete: result.complete }
  }

  private refreshViewport(): void {
    if (!this.canRefresh()) return
    try {
      this.refreshViewportInner()
    } catch {
      // Terminal disposed mid-refresh; stop all future work.
      this.dead = true
      this.clearTimers()
    }
  }

  private refreshViewportInner(): void {
    const buffer = this.term.buffer.active
    const bufferType = buffer.type

    // Entering or leaving a full-screen app invalidates everything at once:
    // absolute indices refer to a different buffer and the match cache
    // describes the other screen.
    if (bufferType !== this.lastBufferType) {
      this.term.clearCellColorOverrides()
      this.lineMatchCache.clear()
      this.disposeSentinel()
      this.bufferTrimmed = false
      this.lastBufferType = bufferType
    }

    if (this.bufferTrimmed) {
      // Scrollback was trimmed: all absolute indices shifted.
      this.invalidateAll()
    }
    // Sentinel only makes sense on the normal buffer: the alternate buffer
    // has no scrollback trimming, and a marker created there dies on switch.
    if (!this.sentinelMarker && bufferType === 'normal') this.installSentinel()

    const viewportY = buffer.viewportY
    const rows = this.term.rows
    const cols = this.term.cols
    const totalLines = buffer.length
    const screenStartY = buffer.baseY
    const budget: RefreshBudget = {
      deadlineMs: performance.now() + MAX_REFRESH_TIME_MS,
      hitLimit: false,
    }
    const colors = resolveHighlightColors(this.term.options.theme)

    // Visible viewport only, bottom-up: newly output lines sit at the bottom
    // of the screen, so a truncated pass decorates them first.
    const scanStart = viewportY
    const scanEnd = Math.min(totalLines - 1, viewportY + rows - 1)
    const scratchCell = buffer.getNullCell()

    for (let lineY = scanEnd; lineY >= scanStart; lineY--) {
      if (this.isBudgetExhausted(budget)) break
      const line = buffer.getLine(lineY)
      if (!line) continue

      let spans: HighlightSpan[]
      if (lineY < screenStartY) {
        const cached = this.getCachedSpans(lineY)
        if (cached !== undefined) {
          spans = cached
        } else {
          const result = this.scanPhysicalLine(line, cols, scratchCell, budget)
          spans = result.spans
          if (result.complete) this.setCachedSpans(lineY, spans)
        }
      } else {
        // On-screen lines can still change via escape sequences — never cache.
        spans = this.scanPhysicalLine(line, cols, scratchCell, budget).spans
      }

      // Always sync the line's overrides: empty spans clear stale entries
      // (e.g. a vim redraw removed the match). The store no-ops when nothing
      // changed. Overrides for lines above the viewport are kept so
      // scrolling back re-renders them immediately without a rescan.
      this.term.setCellColorOverrides(
        lineY,
        spans.length > 0
          ? spans.map((s): ICellColorSpan => ({
              col: s.cellStartCol,
              width: s.cellWidth,
              color: colors[s.category],
            }))
          : null,
      )
    }

    if (budget.hitLimit) {
      this.triggerContinuationRefresh()
    }
  }
}

const attached = new WeakMap<XTerm, OverlayHighlighter>()

/** Attach an overlay highlighter to a terminal (idempotent per terminal).
 * Applies to every terminal type; the "文本高亮" setting is the only gate. */
export function attachOverlayHighlighter(term: XTerm): void {
  if (attached.has(term)) return
  const highlighter = new OverlayHighlighter(term)
  attached.set(term, highlighter)
  highlighter.attach()
}

/** Call after the terminal's theme was swapped: re-applies highlight colors
 * from the new palette immediately (no need to wait for output/scroll). */
export function notifyOverlayHighlightThemeChanged(term: XTerm): void {
  attached.get(term)?.forceRefresh()
}

/** Whether keyword highlighting is actively applied to this terminal right
 * now (attached and enabled in settings). Consumers that mirror the
 * terminal's rendering — like the scrollbar screen preview — use this to
 * stay in sync. */
export function isOverlayHighlightActive(term: XTerm): boolean {
  return attached.get(term)?.isActive() ?? false
}
