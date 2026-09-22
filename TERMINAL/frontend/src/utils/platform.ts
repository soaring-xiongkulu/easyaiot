// Platform detection shared by components that adapt desktop-only UI
// (window controls, local terminal, keyboard hints) for mobile.
export type UiPlatform = 'windows' | 'darwin' | 'linux' | 'android' | 'ios'

// Detect synchronously so the layout is correct on first render, even if the
// Wails System.Environment() call is slow or fails.
export function detectPlatformSync(): UiPlatform {
  const ua = navigator.userAgent
  if (/Android/.test(ua)) return 'android'
  if (/iPhone|iPad/.test(ua)) return 'ios'
  if (/Mac/.test(ua)) return 'darwin'
  if (/Linux/.test(ua)) return 'linux'
  return 'windows'
}

// Mobile platforms have no OS window, no hardware keyboard and no local
// shell, so desktop-only affordances are hidden there.
export function isMobilePlatform(p: UiPlatform = detectPlatformSync()): boolean {
  return p === 'android' || p === 'ios'
}

// Server/web deployment (wails3 `-tags server`): the UI is served to a plain
// browser over HTTP — no OS window, no system keychain (D-Bus secret service
// is absent in the container), no native dialogs.
//
// Detection: the desktop asset server injects its runtime (which populates
// `window._wails.flags`) into <head> before the app bundle executes; the
// server build injects only the custom.js event bridge, which never creates
// flags. So "flags missing" IS the server-mode signal, and flags.server is
// the explicit belt-and-braces form for future wails versions.
export function isWebDeployment(): boolean {
  try {
    const flags = (window as any)._wails?.flags
    return !flags || flags.server === true
  } catch {
    return false
  }
}
