// Reassemble DCS (Device Control String) sequences — `ESC P … ESC \` — that
// arrive split across `session:data` chunks.
//
// xterm.js itself assembles split escape sequences across writes, but it
// never sees a coherent chunk when the sixel payload is split: the highlight
// pass (useHighlight) segments per chunk, and a payload half it does not
// recognize as part of `ESC P` is treated as plain text — brace/pipe
// characters inside the sixel body (`{ } |` are valid sixel data bytes) get
// SGR color codes injected *inside* the DCS sequence, corrupting the image.
//
// This scanner holds bytes of an open DCS until its terminator arrives, and
// hands back the complete sequence as a marked segment so the caller can
// bypass highlighting for it. Everything outside DCS bodies passes through
// untouched, chunk-boundary-agnostic.

export interface DataSegment {
  text: string
  /** true: a complete (or explicitly aborted) DCS sequence — must bypass highlight */
  dcs: boolean
}

// A DCS is aborted by CAN (0x18) or SUB (0x1A) per the VT spec.
const ABORT_RE = /[\x18\x1a]/

export class DcsReassembler {
  private buf = ''
  private inDcs = false

  /** Feed one chunk; returns the segments that are safe to write now. */
  feed(chunk: string): DataSegment[] {
    return this.feedInner(chunk).filter(s => s.text !== '')
  }

  private feedInner(chunk: string): DataSegment[] {
    const out: DataSegment[] = []
    if (!this.inDcs) {
      this.buf += chunk
      const start = this.buf.indexOf('\x1bP')
      if (start === -1) {
        // A trailing lone ESC may be the first half of an `ESC P`
        // introducer (or of an ST) — hold it back, emit the rest.
        if (this.buf.endsWith('\x1b')) {
          out.push({ text: this.buf.slice(0, -1), dcs: false })
          this.buf = '\x1b'
        } else {
          out.push({ text: this.buf, dcs: false })
          this.buf = ''
        }
        return out
      }
      out.push({ text: this.buf.slice(0, start), dcs: false })
      this.buf = this.buf.slice(start)
      this.inDcs = true
    } else {
      this.buf += chunk
    }

    // this.buf now starts with `ESC P`; scan for the terminator from past
    // the introducer so an `ESC` inside the params is handled too.
    for (;;) {
      ABORT_RE.lastIndex = 0
      const esc = this.buf.indexOf('\x1b', 2)
      const abort = ABORT_RE.exec(this.buf.slice(2))
      const abortAt = abort ? abort.index + 2 : -1
      const at = esc === -1 ? abortAt : abortAt === -1 ? esc : Math.min(esc, abortAt)
      if (at === -1) return out
      const next = this.buf[at + 1]
      if (next === undefined) return out // trailing ESC: ambiguous, keep buffering
      if (next === '\\') {
        out.push({ text: this.buf.slice(0, at + 2), dcs: true })
        this.buf = this.buf.slice(at + 2)
        this.inDcs = false
        return out.concat(this.resume())
      }
      // ESC + anything else (or CAN/SUB): the DCS never terminated
      // properly. Flush what we buffered (marked, so highlight still stays
      // off the binary body) and hand the remainder back to normal scanning.
      out.push({ text: this.buf.slice(0, at), dcs: true })
      this.buf = this.buf.slice(at)
      this.inDcs = false
      return out.concat(this.resume())
    }
  }

  // Resume idle scanning over whatever is left in buf after a DCS ended.
  private resume(): DataSegment[] {
    if (!this.buf) return []
    return this.feedInner('')
  }

  /** Drop any pending state (e.g. session reset). */
  reset(): void {
    this.buf = ''
    this.inDcs = false
  }
}
