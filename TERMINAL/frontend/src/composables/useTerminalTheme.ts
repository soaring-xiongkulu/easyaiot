import type { ITheme, Terminal } from '@xterm/xterm'
import { FOLLOW_APP_THEME } from '../types/settings'

/**
 * Resolve the concrete built-in terminal theme name to render.
 *
 * When the user picks an explicit palette it is returned unchanged; only the
 * special FOLLOW_APP_THEME value is derived from the app theme. `appTheme` here
 * is expected to be already resolved to a concrete light/dark choice.
 */
export function resolveTerminalThemeName(
  terminalTheme: string | undefined,
  appTheme: 'dark' | 'light'
): string {
  if (terminalTheme !== FOLLOW_APP_THEME) return terminalTheme || 'terminal-dark'
  return appTheme === 'light' ? 'terminal-light' : 'terminal-dark'
}

/**
 * Resolve the real background color for an xterm theme.
 *
 * When the user enables a custom background image, Terminal previously set
 * `theme.background = 'rgba(0,0,0,0)'` so the canvas would show the image
 * through. xterm.js however parses that string and stores `rgb:0/0/0` as the
 * background — which means OSC 11 (background query) responses also report
 * pure black. TUI applications that probe the background to decide light/dark
 * (Claude Code, lazygit, etc.) then wrongly pick dark-mode colors.
 *
 * Fix: resolve `--bg-base` (the same CSS variable the application chrome
 * uses) to its actual computed color and hand that hex/rgb string to xterm.
 * With `allowTransparency: true` the canvas can still composite the
 * background image underneath.
 */
export function resolveXtermBackground(
  baseTheme: ITheme,
  backgroundEnabled: boolean,
  backgroundImage: string | null | undefined
): ITheme {
  if (!backgroundEnabled || !backgroundImage) return baseTheme

  const resolved = getComputedStyle(document.documentElement)
    .getPropertyValue('--bg-base')
    .trim()

  if (!resolved) return baseTheme

  return { ...baseTheme, background: resolved }
}

/**
 * Relative luminance (0 = black, 1 = white) of a CSS color string, or null when
 * the format isn't one we can read. Handles #rgb / #rrggbb / rgb() / rgba().
 */
function luminance(color: string): number | null {
  const c = color.trim().toLowerCase()
  let r: number, g: number, b: number
  const hex = c.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/)
  if (hex) {
    const h = hex[1]
    if (h.length === 3) {
      r = parseInt(h[0] + h[0], 16); g = parseInt(h[1] + h[1], 16); b = parseInt(h[2] + h[2], 16)
    } else {
      r = parseInt(h.slice(0, 2), 16); g = parseInt(h.slice(2, 4), 16); b = parseInt(h.slice(4, 6), 16)
    }
  } else {
    const m = c.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/)
    if (!m) return null
    r = parseFloat(m[1]); g = parseFloat(m[2]); b = parseFloat(m[3])
  }
  // Rec. 601 luma is plenty for a light/dark decision.
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255
}

/**
 * Publish the terminal's background color as `--terminal-bg`, plus matching
 * scrollbar slider colors, on the terminal root element.
 *
 * `--terminal-bg` paints the 4px padding ring around `.xterm`. Up to xterm v5
 * the ring inherited the terminal color for free: xterm wrote the background
 * inline on `.xterm-viewport`, which is `position: absolute; inset: 0` and
 * therefore covered the padding box too. v6 writes it on
 * `.xterm-scrollable-element` instead, an in-flow `position: relative` element
 * that stops at the padding edge — so the ring fell through to whatever
 * `.xterm` itself is painted with (`--bg-base`, the *app* theme). On a dark app
 * theme with a light terminal theme that reads as a dark frame around the text.
 *
 * The slider colors exist for the same reason. The scrollbar track sits inside
 * the padding, so giving it an app-theme color would show the ring as three
 * stripes down its top/bottom/right. The track is therefore transparent and the
 * slider alone has to carry the contrast — which means keying it off the
 * *terminal* background's luminance rather than the app theme, so a light
 * terminal gets a dark slider and vice versa.
 *
 * CSS can't see the xterm theme, so the values are handed over here; the
 * stylesheet falls back to the app-theme variables when they're absent.
 */
export function applyTerminalBgVar(terminal: Terminal | null | undefined, theme: ITheme): void {
  const el = terminal?.element
  if (!el) return
  const bg = theme.background
  if (!bg) {
    el.style.removeProperty('--terminal-bg')
    el.style.removeProperty('--terminal-scrollbar-thumb')
    el.style.removeProperty('--terminal-scrollbar-thumb-hover')
    return
  }
  el.style.setProperty('--terminal-bg', bg)

  const lum = luminance(bg)
  if (lum == null) {
    el.style.removeProperty('--terminal-scrollbar-thumb')
    el.style.removeProperty('--terminal-scrollbar-thumb-hover')
    return
  }
  // Same opacities as the app-wide scrollbar (0.18 / 0.30 idle / hover).
  const ink = lum > 0.5 ? '0, 0, 0' : '255, 255, 255'
  el.style.setProperty('--terminal-scrollbar-thumb', `rgba(${ink}, 0.18)`)
  el.style.setProperty('--terminal-scrollbar-thumb-hover', `rgba(${ink}, 0.35)`)
}
