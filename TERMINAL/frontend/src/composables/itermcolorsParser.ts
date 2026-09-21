/**
 * Minimal parser/serializer for iTerm2's .itermcolors format — an Apple
 * Property List (XML plist) with a flat <dict> of 16 ANSI colors plus
 * background/foreground/cursor/selection, each itself a <dict> of
 * Red/Green/Blue Component floats (0-1).
 *
 * This is a purpose-built subset, not a general plist parser: iTerm2 export
 * files are internally consistent enough that scanning for
 * "<key>Field Name</key> ... Red/Green/Blue Component ..." blocks with
 * regex is reliable and avoids pulling in a full XML/plist dependency.
 */
import type { TerminalThemeColors } from '../types/settings'

// Maps our TerminalThemeColors field names to iTerm2's plist key names.
const FIELD_TO_ITERM_KEY: Record<keyof TerminalThemeColors, string> = {
  background: 'Background Color',
  foreground: 'Foreground Color',
  cursor: 'Cursor Color',
  selection: 'Selection Color',
  black: 'Ansi 0 Color',
  red: 'Ansi 1 Color',
  green: 'Ansi 2 Color',
  yellow: 'Ansi 3 Color',
  blue: 'Ansi 4 Color',
  magenta: 'Ansi 5 Color',
  cyan: 'Ansi 6 Color',
  white: 'Ansi 7 Color',
  brightBlack: 'Ansi 8 Color',
  brightRed: 'Ansi 9 Color',
  brightGreen: 'Ansi 10 Color',
  brightYellow: 'Ansi 11 Color',
  brightBlue: 'Ansi 12 Color',
  brightMagenta: 'Ansi 13 Color',
  brightCyan: 'Ansi 14 Color',
  brightWhite: 'Ansi 15 Color'
}

function clamp01(n: number): number {
  return Math.min(1, Math.max(0, n))
}

function hexToUnit(hex: string): [number, number, number] {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(hex.trim())
  if (!m) return [0, 0, 0]
  return [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255]
}

function unitToHex(r: number, g: number, b: number): string {
  const toByte = (n: number) => Math.round(clamp01(n) * 255).toString(16).padStart(2, '0')
  return `#${toByte(r)}${toByte(g)}${toByte(b)}`
}

// Extracts a `<key>Field</key><dict>...Component floats...</dict>` block's
// Red/Green/Blue Component values for one plist key name.
function extractComponentColor(xml: string, itermKey: string): string | null {
  const keyEscaped = itermKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const blockRe = new RegExp(`<key>${keyEscaped}</key>\\s*<dict>([\\s\\S]*?)</dict>`, 'i')
  const block = blockRe.exec(xml)
  if (!block) return null
  const body = block[1]
  const comp = (name: string): number | null => {
    const re = new RegExp(`<key>${name}\\s*Component</key>\\s*<real>([\\d.eE+-]+)</real>`, 'i')
    const m = re.exec(body)
    return m ? parseFloat(m[1]) : null
  }
  const r = comp('Red')
  const g = comp('Green')
  const b = comp('Blue')
  if (r === null || g === null || b === null) return null
  return unitToHex(r, g, b)
}

/** Parses an .itermcolors XML string into TerminalThemeColors. Any field
 * missing from the file falls back to the corresponding value in
 * `fallback` (typically the theme currently being edited), so a partial
 * iTerm2 export doesn't blank out unrelated fields. */
export function parseItermColors(xml: string, fallback: TerminalThemeColors): TerminalThemeColors {
  const result = { ...fallback }
  for (const field of Object.keys(FIELD_TO_ITERM_KEY) as (keyof TerminalThemeColors)[]) {
    const hex = extractComponentColor(xml, FIELD_TO_ITERM_KEY[field])
    if (hex) result[field] = hex
  }
  return result
}

/** Serializes TerminalThemeColors into an .itermcolors-compatible XML plist
 * string, so a theme created here can be opened directly in iTerm2 (or
 * re-imported elsewhere). */
export function buildItermColors(colors: TerminalThemeColors): string {
  const entries = (Object.keys(FIELD_TO_ITERM_KEY) as (keyof TerminalThemeColors)[])
    .map(field => {
      const [r, g, b] = hexToUnit(colors[field])
      return [
        `\t<key>${FIELD_TO_ITERM_KEY[field]}</key>`,
        '\t<dict>',
        '\t\t<key>Color Space</key>',
        '\t\t<string>sRGB</string>',
        '\t\t<key>Red Component</key>',
        `\t\t<real>${r.toFixed(6)}</real>`,
        '\t\t<key>Green Component</key>',
        `\t\t<real>${g.toFixed(6)}</real>`,
        '\t\t<key>Blue Component</key>',
        `\t\t<real>${b.toFixed(6)}</real>`,
        '\t\t<key>Alpha Component</key>',
        '\t\t<real>1</real>',
        '\t</dict>'
      ].join('\n')
    })
    .join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
${entries}
</dict>
</plist>
`
}
