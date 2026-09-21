/**
 * Format one or two terminal font families into a CSS `font-family` value with
 * a guaranteed trailing `monospace` generic as the final fallback.
 *
 * A family name containing a space (e.g. "JetBrains Mono Variable",
 * "DejaVu Sans Mono") must be wrapped in quotes so the browser treats it as a
 * single family; without quotes "JetBrains Mono Variable" is parsed as three
 * families (JetBrains, Mono, Variable) the browser can't find, and xterm.js
 * canvas width measurement diverges from actual rendering — causing
 * double-width characters and layout corruption.
 *
 * The primary family holds Latin/general glyphs; the optional `second` fills
 * in glyphs the primary lacks — most useful as a CJK font so Chinese renders
 * with the chosen face instead of the OS's generic (e.g. SimSun) fallback.
 * The resulting stack is `"primary", "second", monospace`.
 */
export function formatFontFamily(first?: string, second?: string): string {
  // A passed-in stack may already end in `monospace`; avoid a doubled tail by
  // stripping it here and re-adding exactly one at the end.
  const stripTrailingMonospace = (v: string): string =>
    v.replace(/\s*,\s*monospace\s*$/i, '')

  const parts: string[] = []
  for (const name of [first, second]) {
    const v = (name || '').trim()
    if (!v) continue
    const cleaned = stripTrailingMonospace(v)
    // Skip a generic that is (or resolves to) `monospace` — it's appended once
    // at the end, so mentioning it here would only produce `monospace, monospace`.
    if (cleaned.toLowerCase() === 'monospace') continue
    // Already a multi-family stack (has commas) → keep as-is. A single spaced
    // family → quote it. Single unspaced family → leave bare.
    parts.push(
      cleaned.includes(',') ? cleaned : /\s/.test(cleaned) ? `"${cleaned}"` : cleaned
    )
  }
  parts.push('monospace')
  return parts.join(', ')
}

/**
 * Coerce a stored `fontFamily` value into a valid bare family name that matches
 * a picker option. The picker stores single family names, but older versions
 * persisted a full CSS stack (e.g. `"JetBrains Mono Variable", Menlo, ...,
 * monospace`); such a value wouldn't match any option and would render as a
 * raw string in the select. If the stored value is already a known bare name we
 * keep it; otherwise we pull the first family out of a legacy stack and use it
 * when it's a real installed font, falling back to the bundled default.
 */
export function normalizeFontFamilyValue(value: string, knownNames: Set<string>): string {
  const DEFAULT = 'JetBrains Mono Variable'
  const v = (value || '').trim()
  if (!v) return DEFAULT
  if (knownNames.has(v)) return v

  // Legacy CSS stack (has commas) — keep its first family if that's a real font.
  const first = v.split(',')[0]?.trim().replace(/^["']|["']$/g, '') || ''
  if (first && knownNames.has(first)) return first
  return first && !/^["'\s]/.test(first) ? first : DEFAULT
}