package session

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// ansiStripper removes ANSI escape sequences from a byte stream chunk
// by chunk. Because emitData is invoked with arbitrary chunk boundaries,
// an escape sequence may be split across two calls. State is tracked in
// the pending slice.
//
// Sequences handled:
//   - CSI: ESC '[' ... final byte (0x40-0x7E)
//   - OSC: ESC ']' ... (BEL 0x07 or ESC '\')
//   - SCS: ESC '(' / ')' / '*' / '+' / '-' / '.' / '/' + designator
//   - SS2/SS3: ESC 'N' single-char / ESC 'O' single-char
//   - Single-char ESC: ESC + one letter
//   - BEL (0x07) outside OSC context is dropped
//
// Bytes preserved: printable ASCII (0x20-0x7E), UTF-8 continuation bytes
// (0x80-0xFF, passed through verbatim — UTF-8 multi-byte characters are
// never split by ANSI logic), and control bytes \r \n \t \b.
type ansiStripper struct {
	// pending holds bytes from an incomplete escape sequence carried over
	// from the previous Strip call. When Strip is called again, pending
	// is prepended to the new input before parsing resumes.
	pending []byte
}

// Strip returns in with ANSI escape sequences removed, EXCEPT the small set
// of in-line cursor/erase CSI sequences that lineProcessor interprets to
// reconstruct readline-edited lines (see isPreservedCSI). Those are passed
// through verbatim. Incomplete sequences at the tail are held until the next
// call, so lineProcessor always receives complete escape sequences.
func (s *ansiStripper) Strip(in []byte) []byte {
	if len(in) == 0 && len(s.pending) == 0 {
		return nil
	}
	data := in
	if len(s.pending) > 0 {
		data = append(s.pending, in...)
		s.pending = nil
	}
	out := make([]byte, 0, len(data))
	i := 0
	for i < len(data) {
		b := data[i]
		if b == 0x1b { // ESC
			end, complete := scanEscape(data, i)
			if !complete {
				// Incomplete tail: save for next chunk.
				s.pending = append(s.pending[:0], data[i:]...)
				return out
			}
			if isPreservedCSI(data[i:end]) {
				out = append(out, data[i:end]...)
			}
			i = end
			continue
		}
		if b == 0x07 { // stray BEL, drop
			i++
			continue
		}
		out = append(out, b)
		i++
	}
	return out
}

// isPreservedCSI reports whether seq (a complete escape sequence starting at
// ESC) is one of the cursor-movement / erase CSIs that lineProcessor knows
// how to apply to its single-line buffer. Everything else (colors, OSC,
// private modes like ESC[?25l, cursor up/down) is dropped by Strip.
func isPreservedCSI(seq []byte) bool {
	if len(seq) < 3 || seq[1] != '[' {
		return false
	}
	if seq[2] == '?' { // private mode (e.g. ?25l show/hide cursor)
		return false
	}
	switch seq[len(seq)-1] {
	case 'C', 'D', 'G', '`', 'K', 'P', '@':
		return true
	}
	return false
}

// scanEscape parses one escape sequence starting at data[start] (which
// must be ESC 0x1b). Returns the index just past the sequence and true
// if a complete sequence was consumed; otherwise returns start and false.
func scanEscape(data []byte, start int) (int, bool) {
	if start+1 >= len(data) {
		return start, false // just ESC, need more
	}
	kind := data[start+1]
	switch kind {
	case '[': // CSI: ESC [ params final(0x40-0x7E)
		for j := start + 2; j < len(data); j++ {
			c := data[j]
			if c >= 0x40 && c <= 0x7e {
				return j + 1, true
			}
		}
		return start, false
	case ']': // OSC: ESC ] ... BEL or ESC \
		for j := start + 2; j < len(data); j++ {
			if data[j] == 0x07 {
				return j + 1, true
			}
			if data[j] == 0x1b && j+1 < len(data) && data[j+1] == '\\' {
				return j + 2, true
			}
		}
		return start, false
	case 'N', 'O': // SS2/SS3: ESC N x / ESC O x — one char follows
		if start+2 >= len(data) {
			return start, false
		}
		return start + 3, true
	case '(', ')', '*', '+', '-', '.', '/': // SCS: designate a character set
		// The byte after the introducer is the character-set designator.
		// fish commonly emits ESC ( B and ESC ) B; consuming only ESC and
		// the introducer would leak the final B into printable session logs.
		if start+2 >= len(data) {
			return start, false
		}
		return start + 3, true
	default:
		// Single-char ESC + letter: consume 2 bytes.
		return start + 2, true
	}
}

// lineProcessor turns a raw byte stream (already ANSI-stripped, with
// cursor/erase CSI sequences preserved) into a sequence of complete
// logical lines suitable for a human-readable log file. It models a
// one-row terminal: a cursor moves through a byte buffer, printable bytes
// overwrite (or extend) at the cursor, \b moves the cursor left, \r sends
// the cursor to column 0, \n flushes the whole row, and preserved CSI
// sequences (ESC [ ... C/D/G/`/K/P/@) perform cursor movement, erase, or
// delete/insert on the buffer.
//
// This is what SecureCRT / Xshell / PuTTY do in "Printable text" mode:
// the log ends up containing the text the user actually saw on screen,
// not every backspace-shuffle or CR-repaint intermediate.
//
// Rules:
//   - Printable byte → write at cursor, advance cursor (extending the
//     buffer when the cursor was already at the end).
//   - \b (0x08) → cursor moves left by one (bounded at 0). The buffer
//     is unchanged; the next write overwrites in place. This matches
//     the shell BS-space-BS erase pattern once you follow through.
//   - \r (0x0D) → cursor jumps to column 0 without clearing. This is
//     the key semantic: \r\n now correctly flushes the accumulated
//     line, and progress-bar-style repainting still yields the final
//     state because later writes overwrite the earlier ones in place.
//   - \n (0x0A) → append \n and flush the whole buffer; buffer + cursor
//     reset.
//   - \t (0x09) → treated as a printable byte and preserved.
//   - CSI C (CUF) → cursor right n columns.
//   - CSI D (CUB) → cursor left n columns.
//   - CSI G / ` (CHA) → cursor to column n (1-indexed).
//   - CSI K (EL) → erase in line: 0=to end, 1=from start, 2=entire.
//   - CSI P (DCH) → delete n chars at cursor.
//   - CSI @ (ICH) → insert n blanks at cursor.
//   - After flushTimeout of inactivity, the next Feed call flushes the
//     partial line (without appending \n) so long-running commands
//     without newline output — top, less, monitoring shells — still
//     make it into the file eventually. The buffer is preserved so the
//     next line's start doesn't get lost mid-write.
type lineProcessor struct {
	line         []byte
	pos          int
	emitted      int // high-water mark: bytes of line already written to output
	lastActivity time.Time
	flushTimeout time.Duration
}

// Feed consumes in and returns whatever complete-line output is ready
// to append to the log file. Multi-byte UTF-8 sequences are opaque:
// backspace moves one byte at a time, so an inflight multi-byte
// character hit by \b could leak a partial rune. In practice, servers
// echo one grapheme per keystroke, so \b almost always lands on ASCII.
func (p *lineProcessor) Feed(in []byte) []byte {
	if p.flushTimeout == 0 {
		p.flushTimeout = 500 * time.Millisecond
	}
	if len(in) == 0 {
		return nil
	}
	now := time.Now()
	var out []byte
	// If we have been idle long enough and there is un-emitted content in
	// the buffer, flush only the new tail (bytes past the high-water mark)
	// so timestamps in the log roughly track the wall clock. The partial
	// line stays in the buffer — this is a flush, not a discard. Emitting
	// only line[emitted:] avoids re-writing bytes already logged, which is
	// what caused slow char-by-char echo (e.g. switch CLIs) to duplicate a
	// growing line prefix on every keystroke.
	if !p.lastActivity.IsZero() && len(p.line) > p.emitted && now.Sub(p.lastActivity) >= p.flushTimeout {
		out = append(out, p.line[p.emitted:]...)
		p.emitted = len(p.line)
	}

	i := 0
	for i < len(in) {
		b := in[i]
		if b == 0x1b && i+2 < len(in) && in[i+1] == '[' {
			// Complete CSI sequence, guaranteed by ansiStripper.
			// Find the final byte (0x40-0x7E).
			end := i + 2
			for end < len(in) {
				c := in[end]
				end++
				if c >= 0x40 && c <= 0x7E {
					break
				}
			}
			p.applyCSI(in[i+2 : end]) // params + final byte
			i = end
			continue
		}
		// Non-CSI byte: standard line-processor logic.
		switch b {
		case '\n':
			out = append(out, p.line[p.emitted:]...)
			out = append(out, '\n')
			p.line = p.line[:0]
			p.pos = 0
			p.emitted = 0
		case '\r':
			p.pos = 0
		case '\b':
			if p.pos > 0 {
				p.pos--
			}
		default:
			if p.pos < len(p.line) {
				p.line[p.pos] = b
			} else {
				p.line = append(p.line, b)
			}
			p.pos++
			// A write at or before the high-water mark rewrote already-emitted
			// bytes (\r or \b repaint); pull the mark back so the change is
			// re-flushed rather than silently lost.
			if p.pos <= p.emitted {
				p.emitted = p.pos - 1
			}
		}
		i++
	}
	p.lastActivity = now
	return out
}

// applyCSI applies a cursor/erase CSI command to the line buffer. csi is the
// parameter + final byte portion of the sequence (without "ESC [").
// Supported commands: C (CUF), D (CUB), G/` (CHA), K (EL), P (DCH), @ (ICH).
func (p *lineProcessor) applyCSI(csi []byte) {
	if len(csi) == 0 {
		return
	}
	cmd := csi[len(csi)-1]
	params := csi[:len(csi)-1]

	switch cmd {
	case 'C': // CUF — cursor right
		n := parseCSIParam(params, 0, 1)
		p.pos += n
		if p.pos > len(p.line) {
			p.pos = len(p.line)
		}
	case 'D': // CUB — cursor left
		n := parseCSIParam(params, 0, 1)
		if n > p.pos {
			p.pos = 0
		} else {
			p.pos -= n
		}
	case 'G', '`': // CHA — cursor to column n (1-indexed)
		n := parseCSIParam(params, 0, 1)
		if n < 1 {
			n = 1
		}
		col := n - 1
		if col > len(p.line) {
			col = len(p.line)
		}
		p.pos = col
	case 'K': // EL — erase in line (default param 0)
		switch parseCSIParam(params, 0, 0) {
		case 0: // erase to end of line
			p.line = p.line[:p.pos]
		case 1: // erase from beginning to cursor
			suffix := make([]byte, len(p.line)-p.pos)
			copy(suffix, p.line[p.pos:])
			p.line = suffix
			p.pos = 0
			p.emitted = 0
			return
		case 2: // erase entire line
			p.line = p.line[:0]
			p.pos = 0
			p.emitted = 0
			return
		}
	case 'P': // DCH — delete n characters at cursor
		n := parseCSIParam(params, 0, 1)
		if p.pos >= len(p.line) {
			return
		}
		if n > len(p.line)-p.pos {
			p.line = p.line[:p.pos]
		} else {
			copy(p.line[p.pos:], p.line[p.pos+n:])
			p.line = p.line[:len(p.line)-n]
		}
	case '@': // ICH — insert n blank characters at cursor
		n := parseCSIParam(params, 0, 1)
		if p.pos >= len(p.line) {
			return
		}
		ins := make([]byte, n)
		p.line = append(p.line[:p.pos], append(ins, p.line[p.pos:]...)...)
		// Bytes that were past the insert point shifted right by n. If any of
		// those were already emitted, bump the high-water mark so they aren't
		// double-flushed on the next sweep.
		if p.emitted > p.pos {
			p.emitted += n
		}
	}
	// If the buffer was shortened past the emitted mark, pull it back so
	// we don't silently lose bytes that were already flushed.
	if p.emitted > len(p.line) {
		p.emitted = len(p.line)
	}
}

// maxCSIParam caps parsed CSI numeric parameters so a hostile or buggy
// remote can't feed values that overflow int arithmetic and drive p.pos
// negative downstream. Real terminals never exceed a few thousand.
const maxCSIParam = 4096

// parseCSIParam extracts the idx-th semicolon-separated numeric parameter
// from params. Returns defaultVal if the parameter is missing or empty.
func parseCSIParam(params []byte, idx, defaultVal int) int {
	start := 0
	for i := 0; i < idx; i++ {
		semi := -1
		for j := start; j < len(params); j++ {
			if params[j] == ';' {
				semi = j
				break
			}
		}
		if semi == -1 {
			return defaultVal
		}
		start = semi + 1
	}
	if start >= len(params) {
		return defaultVal
	}
	end := start
	for end < len(params) && params[end] != ';' {
		end++
	}
	if start == end {
		return defaultVal
	}
	n := 0
	for _, b := range params[start:end] {
		if b < '0' || b > '9' {
			break
		}
		n = n*10 + int(b-'0')
		if n > maxCSIParam {
			return maxCSIParam
		}
	}
	return n
}

// FlushPartial returns the not-yet-emitted tail of the current line
// (without appending \n) and empties the buffer. Called on Disable so the
// last-written line is not lost when the session ends without a trailing
// newline. Bytes already flushed on a timeout are not repeated.
func (p *lineProcessor) FlushPartial() []byte {
	if len(p.line) <= p.emitted {
		p.line = p.line[:0]
		p.pos = 0
		p.emitted = 0
		p.lastActivity = time.Time{}
		return nil
	}
	out := make([]byte, len(p.line)-p.emitted)
	copy(out, p.line[p.emitted:])
	p.line = p.line[:0]
	p.pos = 0
	p.emitted = 0
	p.lastActivity = time.Time{}
	return out
}

// Reset clears buffer and idle state — used when a logger is repurposed.
func (p *lineProcessor) Reset() {
	p.line = p.line[:0]
	p.pos = 0
	p.emitted = 0
	p.lastActivity = time.Time{}
}

// OutputLogger owns a single .log file for one session's lifetime.
// The zero value is a disabled logger; Enable installs a file, Disable
// closes it. All methods are safe for concurrent use.
type OutputLogger struct {
	mu        sync.Mutex
	file      *os.File
	bw        *bufio.Writer
	path      string
	stripper  ansiStripper
	lines     lineProcessor
	flushCh   chan struct{}
	flushDone chan struct{}
	// buffered controls whether writes go through bufio + periodic flush.
	// SetBuffered(false) opts back into the legacy Sync-per-write path,
	// useful for callers that need durable-per-write semantics (and for
	// tests that want deterministic post-Disable fs visibility).
	buffered    bool
	bufferedSet bool
}

// logBufferSize is the in-memory buffer size for the log writer. 64 KiB
// matches the typical filesystem block cluster and avoids per-write
// syscalls on the hot path (see SESSION-07).
const logBufferSize = 64 * 1024

// logFlushInterval is how often the periodic goroutine flushes the
// buffered writer to the underlying file. The OS coalesces the actual
// disk write; we only need to forward buffered bytes out of user-space.
const logFlushInterval = 1 * time.Second

const bannerHeader = "=== Terminal session log ==="

// Enable opens the log file and writes the header banner. Returns the
// final path. If dir is empty, defaultSessionLogDir() is used.
// filenameTemplate supports %S (session), %H (host), %M (month), %D (day),
// %h (hour), and %m (minute). An empty template uses the default.
// On a name collision, "_2"/"_3"/... is appended before the extension.
// Any previous file is closed first.
func (l *OutputLogger) Enable(dir, filenameTemplate, name, host, protocol string) (string, error) {
	if dir == "" {
		dir = defaultSessionLogDir()
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", fmt.Errorf("mkdir log dir %s: %w", dir, err)
	}
	now := time.Now()
	filename := formatLogFilename(filenameTemplate, name, host, now)
	ext := filepath.Ext(filename)
	base := strings.TrimSuffix(filename, ext)
	if ext == "" {
		ext = ".log"
	}

	var file *os.File
	var final string
	for suffix := 1; suffix <= 100; suffix++ {
		var candidate string
		if suffix == 1 {
			candidate = filepath.Join(dir, base+ext)
		} else {
			candidate = filepath.Join(dir, fmt.Sprintf("%s_%d%s", base, suffix, ext))
		}
		f, err := os.OpenFile(candidate, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o644)
		if err == nil {
			file = f
			final = candidate
			break
		}
		if !os.IsExist(err) {
			return "", fmt.Errorf("open log %s: %w", candidate, err)
		}
	}
	if file == nil {
		return "", fmt.Errorf("could not allocate log filename in %s", dir)
	}

	l.mu.Lock()
	defer l.mu.Unlock()
	if l.file != nil {
		_, _ = fmt.Fprintf(l.file, "\n=== Ended: %s ===\n", now.Format("2006-01-02 15:04:05 -0700"))
		_ = l.file.Sync()
		_ = l.file.Close()
	}
	l.file = file
	l.path = final
	l.stripper = ansiStripper{}
	l.lines.Reset()

	// Default to buffered mode unless SetBuffered(false) was called
	// before Enable (the zero value is false; we treat Enable as opting in).
	if !l.bufferedSet {
		l.buffered = true
	}
	if l.buffered {
		l.bw = bufio.NewWriterSize(file, logBufferSize)
		l.flushCh = make(chan struct{})
		l.flushDone = make(chan struct{})
		go l.flushLoop(l.flushCh, l.flushDone)
	}

	fmt.Fprintf(file, "%s\nName: %s\nProtocol: %s\nStarted: %s\n\n",
		bannerHeader, name, protocol, now.Format("2006-01-02 15:04:05 -0700"))
	if l.bw != nil {
		_ = l.bw.Flush()
		_ = file.Sync()
	} else {
		_ = file.Sync()
	}
	return final, nil
}

// Disable writes the footer banner and closes the file. Idempotent.
func (l *OutputLogger) Disable() {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.file == nil {
		return
	}
	// Flush any buffered partial line so an unterminated last command
	// still appears in the log.
	if partial := l.lines.FlushPartial(); len(partial) > 0 {
		if l.bw != nil {
			_, _ = l.bw.Write(partial)
		} else {
			_, _ = l.file.Write(partial)
		}
	}
	if l.bw != nil {
		fmt.Fprintf(l.bw, "\n=== Ended: %s ===\n", time.Now().Format("2006-01-02 15:04:05 -0700"))
		_ = l.bw.Flush()
	} else {
		fmt.Fprintf(l.file, "\n=== Ended: %s ===\n", time.Now().Format("2006-01-02 15:04:05 -0700"))
		_ = l.file.Sync()
	}
	// Stop the periodic flush goroutine.
	if l.flushCh != nil {
		close(l.flushCh)
		l.flushCh = nil
	}
	if l.flushDone != nil {
		// Wait outside the lock — the goroutine may need to take it.
		done := l.flushDone
		l.flushDone = nil
		l.mu.Unlock()
		<-done
		l.mu.Lock()
	}
	_ = l.file.Sync()
	_ = l.file.Close()
	l.file = nil
	l.bw = nil
	l.path = ""
}

// Enabled reports whether a log file is currently open.
func (l *OutputLogger) Enabled() bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.file != nil
}

// Path returns the current log path, or "" if disabled.
func (l *OutputLogger) Path() string {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.path
}

// WriteOutput strips ANSI, runs the byte stream through the line
// processor, and appends any complete lines to the log. No-op if
// disabled or if there is nothing to write. Errors from writing are
// swallowed — a session must not fail because a log file cannot be
// written.
func (l *OutputLogger) WriteOutput(data []byte) {
	if len(data) == 0 {
		return
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.file == nil {
		return
	}
	stripped := l.stripper.Strip(data)
	if len(stripped) == 0 {
		return
	}
	toWrite := l.lines.Feed(stripped)
	if len(toWrite) == 0 {
		return
	}
	if l.bw != nil {
		// Buffered mode: hand bytes to bufio.Writer; the periodic flush
		// goroutine (or Disable) forwards them to the file. No Sync per write.
		_, _ = l.bw.Write(toWrite)
	} else {
		if _, err := l.file.Write(toWrite); err == nil {
			_ = l.file.Sync()
		}
	}
}

// SetBuffered toggles the bufio + periodic-flush path. When buffered is
// true (the default after Enable), writes go through a 64 KiB buffer and
// a 1 s ticker flushes to the OS — the OS coalesces actual disk writes.
// When false, every WriteOutput call durably syncs to disk (legacy
// behavior, useful for tests that need deterministic fs visibility).
// Has no effect after Enable; must be called before Enable, or after
// Disable when the logger is idled.
func (l *OutputLogger) SetBuffered(buffered bool) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.file != nil {
		return // can't change mode while a file is open
	}
	l.buffered = buffered
	l.bufferedSet = true
}

// flushLoop is the periodic flush goroutine. It exits when stopCh is
// closed (by Disable) and signals done so the closer can wait. Both
// channels are captured locally so the loop reads stable pointers —
// Disable can write to l.flushCh / l.flushDone while this goroutine is
// parked on the select without triggering a data race.
func (l *OutputLogger) flushLoop(stopCh, done chan struct{}) {
	defer close(done)
	ticker := time.NewTicker(logFlushInterval)
	defer ticker.Stop()
	for {
		select {
		case <-stopCh:
			return
		case <-ticker.C:
			l.mu.Lock()
			if l.bw != nil {
				_ = l.bw.Flush()
			}
			l.mu.Unlock()
		}
	}
}
