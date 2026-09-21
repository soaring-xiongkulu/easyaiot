// Scale a design-px value by the live root font size so JS-driven geometry
// (Element Plus table column widths are parsed with parseInt, so they cannot
// take rem strings) stays in sync with the rem-based CSS on every platform.
// The design baseline is 1rem = 16px; on macOS the root is scaled up.
export function uiPx(designPx: number): number {
  const root = parseFloat(getComputedStyle(document.documentElement).fontSize)
  if (!Number.isFinite(root) || root <= 0) return designPx
  return Math.round(designPx * (root / 16))
}
