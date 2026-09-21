// Package utils holds small cross-cutting helpers shared by backend packages.
//
// apperr: user-facing errors that carry a stable machine code so the frontend
// can render localized text via i18n instead of relying on Go-side message
// strings. The wire format is
//
//	terminalerr:<code>[|<arg0>[|<arg1>...]]
//
// The frontend helper (src/utils/backendError.ts) locates the marker anywhere
// in the message (wrapper layers may prepend context), strips it, looks up
// backendErrors.<code> in the active locale and interpolates the args into
// {0}, {1}, ... Unknown codes or a missing translation fall back to the raw
// remainder, so uncoded errors and diagnostics keep working unchanged.
package utils

import (
	"errors"
	"strings"
)

// apperrPrefix marks an error as carrying a frontend-localizable code.
const apperrPrefix = "terminalerr:"

// UserErr returns a coded, user-facing error. Args are interpolated into the
// localized template at {0}, {1}, ...
func UserErr(code string, args ...string) error {
	var b strings.Builder
	b.WriteString(apperrPrefix)
	b.WriteString(code)
	for _, a := range args {
		b.WriteByte('|')
		b.WriteString(a)
	}
	return errors.New(b.String())
}
