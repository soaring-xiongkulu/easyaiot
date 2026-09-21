import { ref } from 'vue'

// Shared sticky-Ctrl state between the app-level MobileKeyBar (button) and
// BaseTerminal's onData path (transform). One-shot: disarms after consuming
// one input, whether or not it was convertible.

export const mobileCtrlArmed = ref(false)

// applyMobileCtrl is called from BaseTerminal's onData with soft-keyboard
// input. If Ctrl is armed, the next single-character input that maps to a
// control character is converted (e.g. 'c' → \x03 = Ctrl+C); anything else
// passes through unchanged. Returns the (possibly transformed) data when it
// was consumed, or null when Ctrl isn't armed so the caller proceeds normally.
export function applyMobileCtrl(data: string): string | null {
  if (!mobileCtrlArmed.value) return null
  mobileCtrlArmed.value = false
  if (data.length === 1) {
    const c = data.charCodeAt(0)
    // a-z / A-Z / @[\]^_ → & 0x1f (standard Ctrl mapping)
    if ((c >= 0x41 && c <= 0x5a) || (c >= 0x61 && c <= 0x7a) || (c >= 0x40 && c <= 0x5f)) {
      return String.fromCharCode(c & 0x1f)
    }
  }
  return data
}
