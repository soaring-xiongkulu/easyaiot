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
