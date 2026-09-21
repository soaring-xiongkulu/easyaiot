package database

import "strings"

// ScriptStatement is one executable statement extracted from a SQL script,
// together with the 1-based line number where it starts (for error reporting).
type ScriptStatement struct {
	SQL  string
	Line int
}

// SplitScript splits a SQL script into individual statements. It understands
// string literals ('…', "…", `…`), line comments (-- and #), block comments
// (/* … */), and the MySQL DELIMITER command used to define routines. The
// DELIMITER line itself is consumed and not emitted as a statement.
func SplitScript(script string) []ScriptStatement {
	var stmts []ScriptStatement

	var b strings.Builder
	stmtStartLine := 1
	line := 1
	i := 0
	n := len(script)
	delimiter := ";"
	flushed := true // true means no statement content since last flush

	emit := func() {
		s := strings.TrimSpace(b.String())
		if s != "" {
			stmts = append(stmts, ScriptStatement{SQL: s, Line: stmtStartLine})
		}
		b.Reset()
		flushed = true
	}

	for i < n {
		c := script[i]

		// newline tracking for line numbers
		if c == '\n' {
			line++
			// Detect DELIMITER command at line start (only when not mid-statement).
			if flushed {
				if d, consumed, ok := matchDelimiterCmd(script, i+1); ok {
					delimiter = d
					i += consumed
					// skip rest of that line
					for i < n && script[i] != '\n' {
						i++
					}
					// leave line counting to next loop; b is empty
					continue
				}
			}
			b.WriteByte(c)
			i++
			continue
		}

		// whitespace
		if c == ' ' || c == '\t' || c == '\r' {
			b.WriteByte(c)
			i++
			continue
		}

		// block comment /* ... */ : skip entirely
		if c == '/' && i+1 < n && script[i+1] == '*' {
			i += 2
			for i < n {
				if script[i] == '*' && i+1 < n && script[i+1] == '/' {
					i += 2
					break
				}
				if script[i] == '\n' {
					line++
				}
				i++
			}
			continue
		}

		// line comment -- or # : skip to end of line (comments are not statement content)
		if c == '-' && i+1 < n && script[i+1] == '-' {
			for i < n && script[i] != '\n' {
				i++
			}
			continue
		}
		if c == '#' {
			for i < n && script[i] != '\n' {
				i++
			}
			continue
		}

		// string literals
		if c == '\'' || c == '"' || c == '`' {
			if flushed {
				stmtStartLine = line
			}
			quote := c
			b.WriteByte(c)
			i++
			for i < n {
				ch := script[i]
				if ch == '\\' && quote != '`' {
					b.WriteByte(ch)
					if i+1 < n {
						b.WriteByte(script[i+1])
						if script[i+1] == '\n' {
							line++
						}
						i += 2
						continue
					}
					i++
					continue
				}
				if ch == quote {
					// doubled quote = escaped quote
					if i+1 < n && script[i+1] == quote {
						b.WriteByte(ch)
						b.WriteByte(ch)
						i += 2
						continue
					}
					b.WriteByte(ch)
					i++
					break
				}
				if ch == '\n' {
					line++
				}
				b.WriteByte(ch)
				i++
			}
			flushed = false
			continue
		}

		// delimiter match (custom or ';')
		if strings.HasPrefix(script[i:], delimiter) {
			emit()
			i += len(delimiter)
			continue
		}

		if flushed {
			stmtStartLine = line
			flushed = false
		}
		b.WriteByte(c)
		i++
	}

	emit()
	return stmts
}

// matchDelimiterCmd checks whether the text starting at pos begins (after
// optional whitespace) with "DELIMITER <new-delimiter>", and returns the
// new delimiter + number of bytes consumed (including the keyword). Returns
// ok=false if it does not match.
func matchDelimiterCmd(script string, pos int) (string, int, bool) {
	i := pos
	for i < len(script) && (script[i] == ' ' || script[i] == '\t') {
		i++
	}
	kw := "DELIMITER"
	if i+len(kw) > len(script) || !strings.EqualFold(script[i:i+len(kw)], kw) {
		return "", 0, false
	}
	// must be followed by whitespace
	j := i + len(kw)
	if j >= len(script) || (script[j] != ' ' && script[j] != '\t') {
		return "", 0, false
	}
	for j < len(script) && (script[j] == ' ' || script[j] == '\t') {
		j++
	}
	start := j
	for j < len(script) && script[j] != ' ' && script[j] != '\t' && script[j] != '\n' && script[j] != '\r' {
		j++
	}
	if j == start {
		return "", 0, false
	}
	return script[start:j], j - pos, true
}
