package session

import (
	"os"
	"path/filepath"
	"strings"
	"time"
)

const DefaultSessionLogFilenameTemplate = "%S_%H_%M%D_%h%m.log"

// windowsReservedNames are file names that Windows treats as devices,
// regardless of extension. Comparison is case-insensitive.
var windowsReservedNames = map[string]struct{}{
	"CON": {}, "PRN": {}, "AUX": {}, "NUL": {},
	"COM1": {}, "COM2": {}, "COM3": {}, "COM4": {}, "COM5": {},
	"COM6": {}, "COM7": {}, "COM8": {}, "COM9": {},
	"LPT1": {}, "LPT2": {}, "LPT3": {}, "LPT4": {}, "LPT5": {},
	"LPT6": {}, "LPT7": {}, "LPT8": {}, "LPT9": {},
}

// sanitizeLogName produces a filesystem-safe base name from a
// user-supplied connection name. Returns "" if the result would be
// empty; the caller should fall back to a session-id based default.
//
// Rules (spec §5.6):
//  1. Replace ':' with '-' and other [/\*?"<>|] or control bytes with '_'
//  2. Trim leading/trailing whitespace
//  3. Collapse runs of '_' to a single '_'
//  4. If the result (uppercase) matches a Windows reserved device
//     name, wrap it as _NAME_
//  5. Truncate to 100 chars
func sanitizeLogName(name string) string {
	var b strings.Builder
	b.Grow(len(name))
	for _, r := range name {
		switch {
		case r == ':':
			b.WriteByte('-')
		case r == '/' || r == '\\' || r == '*' || r == '?' ||
			r == '"' || r == '<' || r == '>' || r == '|':
			b.WriteByte('_')
		case r < 0x20:
			b.WriteByte('_')
		default:
			b.WriteRune(r)
		}
	}
	s := strings.TrimSpace(b.String())
	// Collapse consecutive underscores.
	var out strings.Builder
	out.Grow(len(s))
	prevUnderscore := false
	for _, r := range s {
		if r == '_' {
			if !prevUnderscore {
				out.WriteByte('_')
			}
			prevUnderscore = true
		} else {
			out.WriteRune(r)
			prevUnderscore = false
		}
	}
	s = out.String()
	// Windows reserved names.
	stem, ext := s, ""
	if dot := strings.IndexByte(s, '.'); dot >= 0 {
		stem, ext = s[:dot], s[dot:]
	}
	if _, ok := windowsReservedNames[strings.ToUpper(stem)]; ok {
		s = "_" + stem + "_" + ext
	}
	// Truncate.
	if len(s) > 100 {
		s = s[:100]
	}
	return s
}

// formatLogFilename expands the supported session-log filename tokens. If the
// session name and host are identical, %H and one adjacent separator are
// removed so the same value is not repeated in the resulting filename.
func formatLogFilename(template, sessionName, host string, now time.Time) string {
	if template == "" {
		template = DefaultSessionLogFilenameTemplate
	}
	if host == "" || sessionName == host {
		template = removeAllTokensWithSeparator(template, "%H")
		host = ""
	}
	if sessionName == "" {
		template = removeAllTokensWithSeparator(template, "%S")
	}
	extTemplate := filepath.Ext(template)
	stemTemplate := strings.TrimSuffix(template, extTemplate)
	replacer := strings.NewReplacer(
		"%S", sessionName,
		"%H", host,
		"%M", now.Format("01"),
		"%D", now.Format("02"),
		"%h", now.Format("15"),
		"%m", now.Format("04"),
	)
	stem := sanitizeLogName(replacer.Replace(stemTemplate))
	if stem == "" {
		stem = "session"
	}
	ext := sanitizeLogName(replacer.Replace(extTemplate))
	if ext == "" || ext == "." {
		ext = ".log"
	}
	return stem + ext
}

func removeAllTokensWithSeparator(template, token string) string {
	for {
		i := strings.Index(template, token)
		if i < 0 {
			return template
		}
		const separators = "_- ."
		if i > 0 && strings.ContainsRune(separators, rune(template[i-1])) {
			template = template[:i-1] + template[i+len(token):]
			continue
		}
		end := i + len(token)
		if end < len(template) && strings.ContainsRune(separators, rune(template[end])) {
			end++
		}
		template = template[:i] + template[end:]
	}
}

// defaultSessionLogDir is the fallback log root: <home>/Documents/Terminal/logs.
// Callers must MkdirAll before use. Returns a temp-dir path if the
// user's home cannot be determined.
func defaultSessionLogDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(os.TempDir(), "Terminal", "logs")
	}
	return filepath.Join(home, "Documents", "Terminal", "logs")
}

// DefaultSessionLogDir exposes the OS-default log directory for the
// App layer (settings UI displays it as the placeholder path).
func DefaultSessionLogDir() string { return defaultSessionLogDir() }
