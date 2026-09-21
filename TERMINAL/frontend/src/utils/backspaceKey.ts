// Translate xterm.js's default backspace byte (ASCII DEL, 0x7F) into the byte
// sequence the remote end expects. xterm.js always emits 0x7F for the physical
// Backspace key, which works on most modern Linux/macOS PTYs but is silently
// dropped on Huawei/H3C/Cisco network gear and some serial consoles. Those
// devices expect 0x08 (ASCII BS) or ESC[3~ (VT220 Delete).
//
// Only applies to terminal-stream connection types. Non-terminal protocols
// (SFTP, FTP, database, RDP…) never pass through xterm's onData, but the
// defensive type check makes the function safe to call from any code path.
//
// `mode === undefined` falls back to 'del' (0x7F, xterm.js's native byte) so
// terminal-stream types behave as before commit 3d9c5a1 changed it. Sending
// 0x08 unconditionally broke two scenarios: Linux shells whose tty line
// discipline ERASE is 0x7F echo literal ^H for bash `read` prompts (issue
// #638), and Windows local PowerShell/CMD sessions through ConPTY, where the
// translated byte maps to a Ctrl+Backspace key event that deletes a whole
// word. Huawei/H3C/Cisco users (issue #456) can still pick "bs" per
// connection via the dropdown.
const TERMINAL_STREAM_TYPES = new Set([
  'ssh',
  'telnet',
  'serial',
  'mosh',
  'local',
  'k8s',
  'container',
])

// Types without a backspaceKey dropdown in ConnectionForm. Any stored 'bs'
// value on these came from the v1.7 form default (saved silently, never user
// chosen), so it is ignored and the default applies — otherwise existing
// local/k8s/container connections keep sending 0x08 and stay broken.
const NO_UI_TYPES = new Set(['local', 'k8s', 'container'])

export type BackspaceKeyMode = 'del' | 'bs' | 'vt220'

export function applyBackspaceKey(
  data: string,
  mode: BackspaceKeyMode | undefined,
  connType: string | undefined,
): string {
  if (!connType || !TERMINAL_STREAM_TYPES.has(connType)) return data
  // Undefined → keep xterm.js's native 0x7F (see file header).
  const effective: BackspaceKeyMode = NO_UI_TYPES.has(connType) ? 'del' : mode ?? 'del'
  if (effective === 'del') return data
  if (!data.includes('\x7f')) return data
  const replacement = effective === 'bs' ? '\x08' : '\x1b[3~'
  return data.split('\x7f').join(replacement)
}
