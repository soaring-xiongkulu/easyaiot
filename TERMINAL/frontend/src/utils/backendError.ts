import { t } from '../i18n'

// Backend coded errors arrive as "terminalerr:<code>[|<arg>...]" (see
// backend/utils/apperr.go). Wrapper layers may prepend context before the
// marker, so search anywhere in the message. The code maps to an i18n key
// backendErrors.<code> with args interpolated at {0}, {1}, ...
const MARKER = 'terminalerr:'

// Render a caught JS error (Wails bindings reject with Error) as localized text.
export function backendErrorText(e: unknown): string {
  const raw = e instanceof Error ? e.message : String(e)
  return backendErrorTextOf(raw)
}

// Render a raw error string (e.g. session:status payload errorMessage) the same way.
export function backendErrorTextOf(raw: string): string {
  const idx = raw.indexOf(MARKER)
  if (idx === -1) return raw
  const payload = raw.slice(idx + MARKER.length)
  const parts = payload.split('|')
  const code = parts[0]
  const params: Record<string, string> = {}
  parts.slice(1).forEach((arg, i) => {
    params[String(i)] = arg
  })
  const key = `backendErrors.${code}`
  const localized = t(key, params)
  if (localized === key) {
    // Unknown code or missing translation — drop the marker, keep raw remainder.
    return raw.slice(0, idx) + payload
  }
  // Keep any wrapper context preceding the marker.
  return raw.slice(0, idx) + localized
}
