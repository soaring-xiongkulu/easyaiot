import { Clipboard } from '@wailsio/runtime'

// Write to the OS clipboard. Wails' ClipboardSetText resolves false (it does
// not reject) on focus loss / AppKit glitches, so a false return has to fall
// through to the browser API rather than being treated as done. The browser
// API alone is unreliable in WKWebView — navigator.clipboard.writeText
// silently fails when the webview isn't first responder, which is exactly
// when selection-event-driven copies fire (#827). browserWriter is also the
// standalone path when Wails is absent (dev outside the runtime).
type ClipboardWriter = (text: string) => Promise<boolean>
const browserWriter: ClipboardWriter = async (text) => {
  try { await navigator.clipboard.writeText(text); return true } catch { return false }
}
const wailsWriter: ClipboardWriter = async (text) => {
  let ok = false
  try {
    ok = await Clipboard.SetText(text)
  } catch {
    ok = false
  }
  return ok || browserWriter(text)
}

export const writeClipboard: ClipboardWriter = typeof Clipboard.SetText === 'function'
  ? wailsWriter
  : browserWriter
