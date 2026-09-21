// JS bridge to WailsJSBridge's keep-alive foreground service methods
// (Android only — the `wails` object is injected by MainActivity via
// addJavascriptInterface and only exposes these on Android builds).
export function startAndroidKeepAlive(title: string, text: string): void {
  const w = window as unknown as { wails?: { startForegroundService?: (json: string) => void } }
  if (typeof w.wails?.startForegroundService === 'function') {
    w.wails.startForegroundService(JSON.stringify({ title, text }))
  }
}

export function stopAndroidKeepAlive(): void {
  const w = window as unknown as { wails?: { stopForegroundService?: () => void } }
  if (typeof w.wails?.stopForegroundService === 'function') {
    w.wails.stopForegroundService()
  }
}
