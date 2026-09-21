// Filter terminal-generated responses that are known to interfere with remote
// applications when forwarded through the PTY input path. Device Attributes
// responses (CSI ... c) must pass through: fish queries them during startup to
// detect terminal capabilities and waits ten seconds when no reply arrives.
export function filterTerminalInput(input: string, inAlternateScreen: boolean): string {
  // OSC responses: ESC ] ... BEL or ESC ] ... ESC \
  let filtered = input.replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, '')
  // Cursor-position, device-status and window-size responses remain filtered.
  filtered = filtered.replace(/\x1b\[(?:[?>][\d;]*|[\d;]*)([Rnt])/g, '')
  if (inAlternateScreen) return filtered
  // Normal screen only: also strip focus in/out, which a shell does not want.
  return filtered.replace(/\x1b\[(?:[?>][\d;]*|[\d;]*)([IO])/g, '')
}
