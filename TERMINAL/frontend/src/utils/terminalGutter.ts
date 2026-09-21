/**
 * Pure line-number/timestamp computation for the terminal gutter.
 *
 * Kept free of DOM/xterm so the numbering rules can be unit-tested without a
 * terminal instance. The gutter component adapts xterm's buffer to this model.
 *
 * Numbers and timestamps are NOT derived from buffer positions — they come
 * from the logical-line registry (services/terminalTimestamps), where each
 * line got a fixed sequential number and birth time when it first received
 * characters. Wrapped continuation rows carry neither; resize reflows never
 * renumber anything.
 */

/** Default timestamp format, e.g. "12:34:56". */
export const DEFAULT_TIMESTAMP_FORMAT = 'HH:mm:ss'

export interface GutterRow {
  /** Stable identity for the DOM row (lineOffset + absolute buffer row). */
  key: number
  /** The number to display; empty for rows that carry no number. */
  lineNumber: string
  /** Timestamp to display for the row's logical line; empty when none. */
  timestamp: string
}

export interface GutterLineSource {
  isWrapped: boolean
}

/** Per-logical-line data the gutter reads from the registry. */
export interface GutterMeta {
  number: number
  ts?: number
}

export interface BuildGutterLinesOptions {
  /** Number of visible rows on the terminal screen (terminal.rows). */
  rows: number
  /** Index of the top visible buffer row (terminal.buffer.active.viewportY). */
  viewportY: number
  /** Absolute-row offset accumulated from scrollback trimming
   * (0 in the alternate screen). */
  lineOffset: number
  /** Absolute index of the cursor row (baseY + cursorY); rows below it
   * have not been rendered yet and carry no number. */
  cursorAbsoluteY: number
  /** Fetch the wrapping flag for a given absolute buffer row. */
  getLine: (bufferLine: number) => GutterLineSource | null | undefined
  /** Look up a logical line's meta by its absolute start row. */
  getMeta?: (absoluteStartIndex: number) => GutterMeta | undefined
  /** When true and a getTimestamp-style meta is present, populate the column. */
  showTimestamps?: boolean
  /** Largest line number handed out so far — keeps the column width stable
   * even when the viewport shows only low numbers. */
  maxNumberHint?: number
  /** Convert a birth timestamp to display text. Defaults to [HH:mm:ss]. */
  formatTimestamp?: (ms: number) => string
}

export interface GutterBuildResult {
  lines: GutterRow[]
  /** Largest number on screen, used to size the column (>= 1). */
  maxLineNumber: number
}

/**
 * Format a birth timestamp per a tokenized template. Supported tokens:
 * YYYY/YY (year), MM/DD (month/day), HH/mm/ss (hour/minute/second); everything
 * else (e.g. ":") passes through unchanged.
 */
export function formatTimestampMs(ms: number, format: string = DEFAULT_TIMESTAMP_FORMAT): string {
  const d = new Date(ms)
  const pad = (n: number) => String(n).padStart(2, '0')
  const tokens: Record<string, string> = {
    YYYY: String(d.getFullYear()),
    YY: String(d.getFullYear()).slice(-2),
    MM: pad(d.getMonth() + 1),
    DD: pad(d.getDate()),
    HH: pad(d.getHours()),
    mm: pad(d.getMinutes()),
    ss: pad(d.getSeconds()),
  }
  return format.replace(/YYYY|YY|MM|DD|HH|mm|ss/g, (t) => tokens[t])
}

/** Sample timestamp whose rendered length bounds a format's column width. */
export const TIMESTAMP_WIDTH_SAMPLE_MS = new Date(2099, 11, 28, 23, 59, 59).getTime()

/**
 * Resolve the meta of a visible row's logical line. Walks back through the
 * wrapped group: the meta lives on the first (non-wrapped) row, so wrapped
 * continuation rows inherit their group's number and timestamp.
 */
export function resolveRowMeta(
  bufferLine: number,
  lineOffset: number,
  getLine: (bufferLine: number) => GutterLineSource | null | undefined,
  getMeta: (absoluteStartIndex: number) => GutterMeta | undefined,
): GutterMeta | undefined {
  let y = bufferLine
  for (;;) {
    const meta = getMeta(lineOffset + y)
    if (meta) return meta
    const line = getLine(y)
    if (!line?.isWrapped) return undefined
    y -= 1
  }
}

export function buildGutterLines(opts: BuildGutterLinesOptions): GutterBuildResult {
  const lines: GutterRow[] = []
  let maxLineNumber = Math.max(opts.maxNumberHint ?? 0, 1)
  const fmt = opts.formatTimestamp ?? formatTimestampMs

  for (let i = 0; i < opts.rows; i += 1) {
    const bufferLine = opts.viewportY + i
    const isWrapped = opts.getLine(bufferLine)?.isWrapped ?? false
    const isRendered = bufferLine <= opts.cursorAbsoluteY

    // Wrapped continuation rows and rows the cursor hasn't reached yet get no
    // number — the former belong to the line above, the latter haven't been
    // written (nor registered) yet.
    const showNumber = isRendered && !isWrapped
    const key = opts.lineOffset + bufferLine

    let lineNumber = ''
    let timestamp = ''
    if (showNumber && opts.getMeta) {
      const meta = resolveRowMeta(bufferLine, opts.lineOffset, opts.getLine, opts.getMeta)
      if (meta) {
        lineNumber = String(meta.number)
        maxLineNumber = Math.max(maxLineNumber, meta.number)
        if (opts.showTimestamps && meta.ts) timestamp = fmt(meta.ts)
      }
    }

    lines.push({ key, lineNumber, timestamp })
  }

  return { lines, maxLineNumber }
}
