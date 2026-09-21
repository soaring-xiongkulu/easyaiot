// Keyword highlight rule set + matcher shared by the overlay terminal
// highlighter (overlayHighlight.ts). Rules are plain regexes over rendered
// buffer text; a match maps to a HighlightCategory, which the renderer turns
// into a theme color via the xterm fork's cell color override API.
//
// Group 1, when present, is a consumed left word guard that is NOT part of
// the highlighted span (matchTextSpans trims it) — unless the rule sets
// noLeadTrim (e.g. the brace rule's group is a run anchor that IS part of
// the span). Right guards are zero-width lookaheads. No lookbehind anywhere
// — unsupported by the JavaScriptCore in macOS ≤12.3 WebView, where this
// module fails to parse.
export type HighlightCategory =
  | 'url' | 'host' | 'path' | 'datetime' | 'string'
  | 'success' | 'error' | 'warning' | 'info' | 'brace'

export interface HighlightRule {
  category: HighlightCategory
  noLeadTrim?: boolean
  regexes: RegExp[]
}

export const HIGHLIGHT_RULES: HighlightRule[] = [
  { category: 'url',     regexes: [
    /https?:\/\/[A-Za-z0-9_.&?=%~#{}()@+-]+(?::?[A-Za-z0-9_./&?=%~#{}()@+-]+)?/gi,
  ]},
  { category: 'host',    regexes: [
    // IPv4 (first octet 1-254) and IPv6 (full and ::-compressed forms)
    /(^|[^0-9a-z_&-])(localhost|(?:1[0-9][0-9]|2[0-4][0-9]|25[0-4]|[1-9][0-9]|[1-9])\.\d+\.\d+\.\d+|null|none)(?![0-9a-z_-])/gi,
    /(^|[^0-9a-z_&-])((?:[a-f0-9]{1,4}:){7}[a-f0-9]{1,4}|(?:[a-f0-9]{1,4}:){1,7}:|(?:[a-f0-9]{1,4}:){1,6}:[a-f0-9]{1,4}|(?:[a-f0-9]{1,4}:){1,5}(?::[a-f0-9]{1,4}){1,2}|(?:[a-f0-9]{1,4}:){1,4}(?::[a-f0-9]{1,4}){1,3}|(?:[a-f0-9]{1,4}:){1,3}(?::[a-f0-9]{1,4}){1,4}|(?:[a-f0-9]{1,4}:){1,2}(?::[a-f0-9]{1,4}){1,5}|[a-f0-9]{1,4}:(?::[a-f0-9]{1,4}){1,6}|:(?::[a-f0-9]{1,4}){1,7})(?![0-9a-f:])/gi,
  ]},
  { category: 'error',   regexes: [
    // "<adjective> <noun>" phrases: bad address, invalid argument, …
    /(^|[^a-z_&-])((?:bad|wrong|incorrect|improper|invalid|unsupported)(?: file| memory)? (?:descriptor|alloc(?:ation)?|addr(?:ess)?|owner(?:ship)?|arg(?:ument)?|param(?:eter)?|setting|length|filename))(?![a-z_-])/gi,
    // denied, failed, segfault, no X found, …
    /(^|[^a-z_&-])((?:operation |connection |authentication |access |permission )?(?:denied|disallowed|not allowed|refused|problem|failed|failure|not permitted)|not properly|improperly|no [a-z]+(?: [a-z]+)? found|invalid|unsupported|not supported|seg(?:mentation )?fault|corrupt(?:ion|ed)?|overflow|underrun|not ok|unimplemented|unsuccessfull?|not implemented|permerrors?|errors?|crash(?:ed)?|core dump|\(ee\)|\(ni\))(?![a-z_-])/gi,
    // falsy output values ("=> no", "status: false")
    /([=>"':.,;({\[] *)(?:false|no|ko)(?=[\]=>"':.,;)} ]|$)/gi,
  ]},
  { category: 'success', regexes: [
    /(^|[^a-z_&-])(accepted|allowed|enabled|connected|successfully|successful|succeeded|success)(?![a-z_-])/gi,
  ]},
  { category: 'warning', regexes: [
    /(^|[^a-z_&-])(\[-w[a-z-]+\]|caught signal [0-9]+|cannot|not responding|(?:connection (?:to (?:remote host|[a-z0-9.]+) )?)?(?:closed|terminated|stopped)|exited|no more [a-z]+ available|unexpected|(?:command |binary |file )?not found|o{2,}ps|out of (?:space|memory)|low (?:memory|disk)|unknown|disabled|disconnect(?:ed|ion)?|deprecated|refused|warnings?|\(ww\)|\(\?\?\)|could not|unable to)(?![a-z_-])/gi,
  ]},
  { category: 'info',    regexes: [
    /(^|[^a-z_&-])(last (?:failed )?login:|launching|checking|loading|creating|building|important|booting|starting|informational|informations?|info|notice|note|\(ii\)|\(\!\!\))(?![a-z_-])/gi,
  ]},
  // Character class includes `+`, `~`, `@` so paths like
  // `/usr/local/gcc-11.5.0/bin/g++` are recognised whole.
  { category: 'path',    regexes: [/(^|\s)(?:\/|~\/)[\w.+~@/-]+(?=[\s:;"')\]}]|$)/g] },
  { category: 'datetime', regexes: [
    /\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:[.,]\d+)?Z?\b/g,
    /\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4}\b/g,
    /\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b/g,
    /\b\d{2}:\d{2}:\d{2}\b/g,
  ]},
  { category: 'string',  regexes: [/"(?:[^"\\]|\\.){2,}"|'(?:[^'\\]|\\.){2,}'/g] },
  // Consecutive identical symbols (`****`, `=====`, `>>>`) match once as a
  // whole run — the capture group is a backreference anchor, not a guard,
  // hence noLeadTrim.
  { category: 'brace',   noLeadTrim: true, regexes: [/([{}()\[\]|*=<>])\1*/g] },
]

export interface TextSpan {
  /** String index of the first character (inclusive). */
  start: number
  /** String index just past the last character (exclusive). */
  end: number
  category: HighlightCategory
}

export interface MatchTextOptions {
  /** Hard cap of accepted spans. */
  maxMatches?: number
  /** Pollable stop (e.g. a time budget). When it fires, `complete: false`
   * and the spans accepted so far are returned. */
  shouldStop?: () => boolean
}

export interface MatchTextResult {
  spans: TextSpan[]
  /** False when a cap or the stop probe ended the scan early. */
  complete: boolean
}

/** Run every rule regex over one line of plain text and collect the
 * non-overlapping highlight spans (first rule wins on overlap). Spans come
 * back sorted by position. The rule regexes carry `g` flags and are shared
 * across callers — safe because each call resets and exhausts lastIndex
 * synchronously. */
export function matchTextSpans(
  text: string,
  rules: HighlightRule[] = HIGHLIGHT_RULES,
  opts: MatchTextOptions = {},
): MatchTextResult {
  const maxMatches = opts.maxMatches ?? 40
  const shouldStop = opts.shouldStop
  const spans: TextSpan[] = []
  if (!text) return { spans, complete: true }
  const stopEarly = (): false => {
    spans.sort((a, b) => a.start - b.start)
    return false
  }
  // Occupied string positions prevent multi-rule overlap (first rule wins).
  const occupied = new Uint8Array(text.length)

  for (const { category, noLeadTrim, regexes } of rules) {
    if (spans.length >= maxMatches) break
    if (shouldStop?.()) return { spans, complete: stopEarly() }
    for (const regex of regexes) {
      if (spans.length >= maxMatches) break
      if (shouldStop?.()) return { spans, complete: stopEarly() }
      regex.lastIndex = 0
      let match: RegExpExecArray | null
      while ((match = regex.exec(text)) !== null) {
        if (spans.length >= maxMatches) break
        if (shouldStop?.()) return { spans, complete: stopEarly() }
        if (match[0].length === 0) {
          regex.lastIndex++
          continue
        }
        // Trim the consumed left word guard (group 1) — unless the rule
        // marks its group as part of the span (run anchor).
        const lead = noLeadTrim ? 0 : (match[1] ? match[1].length : 0)
        const start = match.index + lead
        const end = match.index + match[0].length
        if (end <= start) continue

        let isOverlapping = false
        for (let k = start; k < end; k++) {
          if (occupied[k]) {
            isOverlapping = true
            break
          }
        }
        if (isOverlapping) continue

        spans.push({ start, end, category })
        for (let k = start; k < end; k++) occupied[k] = 1
      }
    }
  }
  spans.sort((a, b) => a.start - b.start)
  // If the cap fired, the text wasn't fully scanned — report incomplete so
  // callers don't cache the truncated result as final.
  return { spans, complete: spans.length < maxMatches }
}
