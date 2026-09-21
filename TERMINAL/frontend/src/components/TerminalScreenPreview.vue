<template>
  <div
    v-show="visible"
    class="terminal-screen-preview"
    :style="popupStyle"
  >
    <div
      v-for="(row, i) in lines"
      :key="i"
      class="preview-line"
      :style="{ height: cellHeightPx, lineHeight: cellHeightPx }"
    >
      <span
        v-if="showTimestamps"
        class="preview-col-time"
        :style="{ width: timeColWidth, color: timeColor, borderRight: dividerOnTime ? dividerCss : undefined }"
      >{{ row.timestamp }}&nbsp;</span>
      <span
        v-if="showLineNumbers"
        class="preview-col-num"
        :style="{ width: numColWidth, color: numColor, marginRight: numColGap, borderRight: dividerOnNum ? dividerCss : undefined }"
      >{{ row.lineNumber }}</span>
      <span class="preview-content">
        <template v-if="row.runs.length">
          <span
            v-for="(run, j) in row.runs"
            :key="j"
            :style="runStyle(run)"
          >{{ run.text }}</span>
        </template>
        <span v-else class="preview-blank">&nbsp;</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
// Issue #729 — screen preview (屏幕回看): hovering the terminal scrollbar for
// a moment pops up a small read-only preview of the scrollback at that
// position (WindTerm/Termora-style). Clicking the preview scrolls the
// terminal there. Pure display: never touches the pty stream or terminal
// state, so TUI apps (vim, htop) are unaffected.
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import type { Terminal } from '@xterm/xterm'
import { getManagedTerminal } from '../services/terminalManager'
import { getLineHighlightColors, isOverlayHighlightActive } from '../composables/overlayHighlight'
import { useSettingsStore } from '../stores/settingsStore'
import { formatTimestampMs, resolveRowMeta } from '../utils/terminalGutter'
import {
  buildPalette,
  lineToRuns,
  computePreviewStart,
  computePreviewWindowStart,
  computeTrackClickRatio,
  computeSliderHeight,
  pickVerticalTrackIndex,
  type PreviewPalette,
  type PreviewStyleRun,
} from '../services/screenPreview'

const props = defineProps<{ sessionId: string }>()

const PREVIEW_ROWS = 10
const HOVER_DELAY = 250

const settingsStore = useSettingsStore()
const showLineNumbers = computed(() => settingsStore.settings.terminal.showLineNumbers ?? false)
const showTimestamps = computed(() => settingsStore.settings.terminal.showTimestamps ?? false)

const visible = ref(false)
const lines = ref<Array<{ runs: PreviewStyleRun[]; lineNumber: string; timestamp: string }>>([])
const startRow = ref(0)
const pos = ref({ left: 0, top: 0 })
const size = ref({ width: 0, height: 0 })
const cellHeightPx = ref('1.5em')
const bgColor = ref('#1e1e1e')
// Terminal's resolved default foreground. Cells without an explicit color
// have no inline style — the popup container must carry the terminal's
// foreground, or they inherit the app UI's text color instead.
const fgColor = ref('#cccccc')
const fontCss = ref({ fontSize: '13px', fontFamily: 'monospace' })
const numColWidth = ref('')
const timeColWidth = ref('')
// Gutter-mirroring colors: same alphas the main gutter uses (time 0.85,
// number 0.6, divider 0.16 of the terminal foreground) so the preview's
// columns read exactly like the terminal's.
const timeColor = ref('')
const numColor = ref('')
const dividerColor = ref('')
const numColGap = ref('')
const dividerCss = computed(() => `1px solid ${dividerColor.value}`)
// The divider sits after the LAST gutter column (number, when numbers are
// shown; otherwise the time column).
const dividerOnNum = computed(() => showLineNumbers.value)
const dividerOnTime = computed(() => showTimestamps.value && !showLineNumbers.value)

const popupStyle = computed(() => ({
  left: `${pos.value.left}px`,
  top: `${pos.value.top}px`,
  width: `${size.value.width}px`,
  height: `${size.value.height}px`,
  // Mix the terminal background toward a light blue so the popup reads as a
  // distinct overlay instead of blending with the terminal; rendered
  // translucent + CSS backdrop blur (see .terminal-screen-preview) for a
  // frosted-glass look. tintBlue() falls back to opaque black for
  // non-hex backgrounds (transparent in background-image mode), so the
  // popup is never invisible.
  background: withAlpha(tintBlue(bgColor.value, 0.3), 0.85),
  color: fgColor.value,
  fontSize: fontCss.value.fontSize,
  fontFamily: fontCss.value.fontFamily,
}))

function runStyle(run: PreviewStyleRun) {
  return {
    color: run.fg,
    background: run.bg,
    fontWeight: run.bold ? 600 : undefined,
    fontStyle: run.italic ? 'italic' : undefined,
    textDecoration: run.underline ? 'underline' : undefined,
    opacity: run.dim ? 0.6 : undefined,
  }
}

function getTerminal(): Terminal | null {
  return getManagedTerminal(props.sessionId)?.terminal ?? null
}

/**
 * Palette for the preview popup. xterm resolves `options.theme` against its
 * built-in defaults — a theme may override only a few keys, so the popup must
 * read the RESOLVED colors from the theme service (what the terminal actually
 * paints), not the raw option; reading the raw option left the preview stuck
 * on fixed fallback colors after switching terminal themes.
 */
function buildLivePalette(t: Terminal): PreviewPalette {
  try {
    const colors = (t as any)._core?._themeService?.colors
    if (Array.isArray(colors?.ansi) && colors.ansi.length >= 16) {
      return {
        defaultFg: colors.foreground?.css ?? '#ffffff',
        defaultBg: colors.background?.css ?? '#000000',
        ansi16: colors.ansi.slice(0, 16).map((c: { css: string }) => c.css),
      }
    }
  } catch { /* internal API — fall through */ }
  return buildPalette(t.options.theme)
}

/** Add alpha to a hex color (e.g. popup background); non-hex passes through. */
function withAlpha(color: string, alpha: number): string {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(color.trim())
  if (!m) return color
  let hex = m[1]
  if (hex.length === 3) {
    hex = hex.split('').map((ch) => ch + ch).join('')
  }
  const n = parseInt(hex, 16)
  return `rgba(${(n >> 16) & 0xff}, ${(n >> 8) & 0xff}, ${n & 0xff}, ${alpha})`
}

/**
 * Blend a hex color toward a light-blue tint: the preview popup must not read
 * as part of the terminal background, so shift it toward a pale blue.
 * Non-hex colors pass through unchanged.
 */
function tintBlue(color: string, ratio: number): string {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(color.trim())
  // Non-hex input used to pass through unchanged. In background-image mode
  // the terminal's theme background is 'transparent', which rendered the
  // popup fully invisible; treat it as opaque black instead — it tints to
  // the same dark blue as a black-background terminal.
  let hex = m ? m[1] : '000000'
  if (hex.length === 3) {
    hex = hex.split('').map((ch) => ch + ch).join('')
  }
  const n = parseInt(hex, 16)
  const r = (n >> 16) & 0xff, g = (n >> 8) & 0xff, b = n & 0xff
  const mix = (c: number, t: number) => Math.round(c + (t - c) * ratio)
  return (
    '#' +
    [mix(r, 0xa0), mix(g, 0xc8), mix(b, 0xe8)]
      .map((v) => v.toString(16).padStart(2, '0'))
      .join('')
  )
}

/**
 * Locate xterm's scrollbar element. xterm v6 renders a VS Code-style overlay
 * scrollbar (`.xterm-scrollable-element > .scrollbar`) that is a *sibling* of
 * `.xterm-viewport` — hovering it never produces events on the viewport, so
 * hover detection must hit-test against this element instead.
 */
function findScrollbar(t: Terminal): HTMLElement | null {
  const el = t.element
  if (!el) return null
  const nodes = el.querySelectorAll<HTMLElement>('.xterm-scrollable-element > .scrollbar')
  const rects = Array.from(nodes).map((n) => n.getBoundingClientRect())
  const idx = pickVerticalTrackIndex(rects)
  return idx >= 0 ? nodes[idx] : null
}

let host: HTMLElement | null = null
let hoverTimer: number | undefined
/** Click-equivalent scroll fraction (slider-centered mapping). */
let lastRatio = 0
/** The pointer's own vertical fraction within the track ≙ viewport row. */
let lastPointerFraction = 0
/** Viewport top line the track click will land on. */
let jumpTopLine = 0
let lastClientY = 0
/** True between pointerdown and pointerup on the track (preview visible). */
let trackDragging = false

function clearTimers() {
  if (hoverTimer !== undefined) {
    clearTimeout(hoverTimer)
    hoverTimer = undefined
  }
}

function bind() {
  unbind()
  const t = getTerminal()
  const el = t?.element
  if (!el) return
  host = el
  el.addEventListener('mousemove', onMouseMove)
  el.addEventListener('mouseleave', onMouseLeave)
  el.addEventListener('pointerdown', onPointerDownCapture, true)
}

function unbind() {
  host?.removeEventListener('mousemove', onMouseMove)
  host?.removeEventListener('mouseleave', onMouseLeave)
  host?.removeEventListener('pointerdown', onPointerDownCapture, true)
  host = null
  clearTimers()
  visible.value = false
}

function cellHeight(t: Terminal): number {
  try {
    const h = (t as any)._core?._renderService?.dimensions?.css?.cell?.height
    if (h > 0) return h
  } catch { /* internal API — fall through */ }
  return (t.options.fontSize ?? 13) * 1.5
}

function charWidth(t: Terminal): number {
  try {
    const w = (t as any)._core?._renderService?.dimensions?.css?.character?.width
    if (w > 0) return w
  } catch { /* internal API — fall through */ }
  return (t.options.fontSize ?? 13) * 0.6
}

/**
 * The scrollbar track under the pointer, or null when not hovering it.
 * Geometry-based on purpose: mouse events over xterm v6's overlay scrollbar
 * target the underlying `xterm-screen` (the scrollbar never becomes the event
 * target), so only coordinate containment against the scrollbar's rect works.
 * A small tolerance on the left edge makes the narrow (14px) strip easier to
 * hit. Hovering the thumb (slider) returns null — the thumb marks the content
 * that is already on screen, so there is nothing to preview there.
 *
 * Returns the track rect plus the slider's real height: the preview maps the
 * hover point to buffer rows with the same slider-centered formula xterm uses
 * for track clicks (see computeTrackClickRatio), so the slider height is part
 * of the math. Falls back to ScrollbarState's own max(20, …) formula when the
 * slider element can't be measured.
 */
function scrollbarRect(
  t: Terminal,
  e: MouseEvent,
): { track: DOMRect; sliderHeight: number } | null {
  const sb = findScrollbar(t)
  if (!sb) return null
  const r = sb.getBoundingClientRect()
  const TOLERANCE = 6
  if (
    e.clientX < r.left - TOLERANCE ||
    e.clientX > r.right + 2 ||
    e.clientY < r.top ||
    e.clientY > r.bottom
  ) {
    return null
  }
  const slider = sb.querySelector('.slider') as HTMLElement | null
  if (slider) {
    const s = slider.getBoundingClientRect()
    const PAD = 4
    if (e.clientY >= s.top - PAD && e.clientY <= s.bottom + PAD) return null
    return { track: r, sliderHeight: s.height }
  }
  const total = t.buffer.active.length
  return {
    track: r,
    sliderHeight: computeSliderHeight(r.height, r.height, total * cellHeight(t)),
  }
}

function onMouseMove(e: MouseEvent) {
  const t = getTerminal()
  if (!t || !host) return hide()

  const hit = scrollbarRect(t, e)
  if (!hit) return hide()
  const rect = hit.track
  // Alt-screen apps (vim, htop) have no scrollback to preview.
  if (t.buffer.active.type === 'alternate') return hide()
  const total = t.buffer.active.length
  if (total <= t.rows) return hide()

  // Same mapping xterm applies to a track click at this point, so the
  // previewed lines are exactly what the user would see after clicking.
  lastRatio = computeTrackClickRatio(e.clientY - rect.top, rect.height, hit.sliderHeight)
  lastPointerFraction = Math.min(1, Math.max(0, (e.clientY - rect.top) / rect.height))
  lastClientY = e.clientY
  clearTimers()
  if (visible.value) {
    show(t, rect)
    // Pointer held down on the track: keep jumping while it drags.
    if (trackDragging) scrollToPreviewTop(t)
  } else {
    hoverTimer = window.setTimeout(() => {
      hoverTimer = undefined
      const t2 = getTerminal()
      if (t2?.element) show(t2, rect)
    }, HOVER_DELAY)
  }
}

function show(t: Terminal, sbRect: DOMRect) {
  const total = t.buffer.active.length
  // Model the outcome of clicking the track at the hover point. The popup
  // hangs above the pointer and previews the block that reappears below it:
  // after the click, the line under the pointer is the viewport's top line
  // plus the pointer's row within the viewport (the pointer stays put on
  // screen while content scrolls underneath it).
  const clickTop = computePreviewStart(lastRatio, total, t.rows, PREVIEW_ROWS)
  const start = computePreviewWindowStart(clickTop, t.rows, lastPointerFraction, total, PREVIEW_ROWS)
  startRow.value = start
  jumpTopLine = clickTop

  const palette = buildLivePalette(t)
  const buf = t.buffer.active
  const managed = getManagedTerminal(props.sessionId)
  const lineOffset = managed?.lineOffset ?? 0

  const withNumbers = showLineNumbers.value
  const withTimestamps = showTimestamps.value && managed
  // Mirror the terminal's gating exactly (attached + enabled).
  const highlightOn = isOverlayHighlightActive(t)
  const tsFormat = settingsStore.settings.terminal.timestampFormat || 'HH:mm:ss'
  const alternate = buf.type === 'alternate'
  const registry = managed?.lineRegistry
  const getMeta = (abs: number) =>
    alternate ? { number: abs + 1 } : registry?.entries.get(abs)

  const rendered: Array<{ runs: PreviewStyleRun[]; lineNumber: string; timestamp: string }> = []
  for (let i = 0; i < PREVIEW_ROWS; i++) {
    const bufferLine = start + i
    const line = buf.getLine(bufferLine)
    const isWrapped = line?.isWrapped ?? false
    // Keyword highlight colors, matching what the terminal itself renders
    // (same rules + palette source as overlayHighlight).
    const hlColors = line && highlightOn
      ? getLineHighlightColors(line, t.cols, t.options.theme)
      : undefined
    const runs = line ? lineToRuns(line, t.cols, palette, hlColors ? (col) => hlColors[col] : undefined) : []
    // Mirror the gutter's semantics: numbers/timestamps come from the logical
    // line registry; wrapped continuation rows belong to the line above, so
    // they carry no number/timestamp of their own.
    const numbered = withNumbers && !isWrapped
    const stamped = withTimestamps && !isWrapped
    const meta = (numbered || stamped) && managed
      ? resolveRowMeta(bufferLine, lineOffset, (y) => buf.getLine(y), getMeta)
      : undefined
    rendered.push({
      runs,
      lineNumber: numbered && meta ? String(meta.number) : '',
      timestamp: stamped && meta?.ts ? formatTimestampMs(meta.ts, tsFormat) : '',
    })
  }
  lines.value = rendered
  // Resolved (not raw-option) colors — same source the cells were styled from.
  bgColor.value = palette.defaultBg
  fgColor.value = palette.defaultFg
  // Mirror the gutter's column palette (TerminalGutter.vue): same alphas of
  // the terminal foreground for time, number and the divider line.
  timeColor.value = withAlpha(palette.defaultFg, 0.85)
  numColor.value = withAlpha(palette.defaultFg, 0.6)
  dividerColor.value = withAlpha(palette.defaultFg, 0.16)
  fontCss.value = {
    fontSize: `${t.options.fontSize ?? 13}px`,
    fontFamily: typeof t.options.fontFamily === 'string' ? t.options.fontFamily : 'monospace',
  }
  // Column width from the largest line number handed out (registry counter);
  // falls back to the buffer extent when there is no registry data (alt screen).
  const maxNumberHint = registry && !alternate ? registry.nextNumber - 1 : total
  const maxDigits = String(Math.max(maxNumberHint, 1)).length
  // Column widths mirror the gutter's formulas (TerminalGutter.vue): time =
  // ceil(cellWidth × format length) + 2px padding; number = max(ceil(cellWidth
  // × digits) + 8px padding, 24); 12px gap between the two columns; the
  // character width comes from the terminal's measured cell — the CSS `ch`
  // unit measures the '0' glyph and drifts from the real cell size.
  const cw = charWidth(t)
  const timeW = withTimestamps ? Math.ceil(cw * tsFormat.length) + 2 : 0
  const numW = withNumbers ? Math.max(Math.ceil(cw * maxDigits) + 8, 24) : 0
  const gap = withTimestamps && withNumbers ? 12 : 0
  timeColWidth.value = withTimestamps ? `${timeW}px` : ''
  numColWidth.value = withNumbers ? `${numW}px` : ''
  numColGap.value = gap ? `${gap}px` : ''
  // The number/timestamp columns live INSIDE the popup, so the popup must be
  // wider than the terminal by exactly those columns (+1px divider) —
  // otherwise the content area shrinks and the right-hand side of each line
  // gets clipped. The left gutter area of the terminal provides this room.
  const colsExtra = timeW + gap + numW + 1

  const lh = cellHeight(t)
  cellHeightPx.value = `${lh}px`
  // Anchor measurements to the terminal's own container — never to the popup
  // itself: while the popup is hidden (v-show display:none) its offsetParent
  // is null, which used to misplace the very first appearance to (0,0).
  const base = (host?.closest('.base-terminal') as HTMLElement | null)?.getBoundingClientRect()
  if (!base) return
  const termRect = t.element?.getBoundingClientRect()
  if (!termRect) return

  // box-sizing: content-box — `width` IS the content area, so text lines up
  // with the terminal regardless of padding. CHROME (padding 4px ×2, no side
  // borders) only matters for the outer footprint when positioning/clamping.
  const POPUP_H_CHROME = 8
  // Base the content width on the actual rendered text area (.xterm-screen),
  // NOT the `.xterm` root: the root's width also spans the scrollbar strip,
  // which left a blank margin at the right edge of every preview line.
  const screenEl = t.element?.querySelector('.xterm-screen') as HTMLElement | null
  const contentWidth = screenEl?.getBoundingClientRect().width ?? t.cols * cw
  // Overlay the terminal window exactly: flush with its left edge and ending
  // at the scrollbar. (The previous right-anchored layout left a visible gap
  // on the left whenever the popup's content was narrower than the window.)
  // Text is left-aligned, so lines start exactly where the terminal's do;
  // the columns make the previewed text line up with the real columns.
  const areaRect = (host?.closest('.terminal-area') as HTMLElement | null)?.getBoundingClientRect()
  const width = areaRect
    ? Math.max(contentWidth + colsExtra, sbRect.left - areaRect.left - POPUP_H_CHROME)
    : contentWidth + colsExtra
  const left = areaRect
    ? Math.max(0, areaRect.left - base.left)
    : Math.max(4, sbRect.left - width - POPUP_H_CHROME - 6 - base.left)
  const height = PREVIEW_ROWS * lh
  size.value = { width, height }
  // Center the popup vertically on the pointer, to the LEFT of the scrollbar:
  // its middle row is the line that lands under the pointer after the click
  // (see computePreviewWindowStart).
  pos.value = {
    left,
    top: Math.min(
      Math.max(4, lastClientY - height / 2 - base.top),
      Math.max(4, base.height - height - 8),
    ),
  }
  visible.value = true
}

function onMouseLeave() {
  clearTimers()
  hide()
}

function hide() {
  clearTimers()
  visible.value = false
}

/**
 * Take over track clicks while the preview popup is up: jump so the previewed
 * content lands at the pointer, exactly as shown. xterm's own track handling
 * (slider-centering on stale buffer indices) is suppressed for this click.
 * Without the popup, native xterm behavior is untouched; dragging the thumb
 * is unaffected (pointerdown on the slider never reaches here — the popup
 * hides when the pointer moves onto the slider).
 */
function onPointerDownCapture(e: MouseEvent) {
  trackDragging = false
  if (!visible.value || e.button !== 0) return
  const t = getTerminal()
  if (!t) return
  const hit = scrollbarRect(t, e)
  if (!hit) return
  e.preventDefault()
  e.stopPropagation()
  trackDragging = true
  window.addEventListener(
    'pointerup',
    () => {
      trackDragging = false
    },
    { once: true },
  )
  lastRatio = computeTrackClickRatio(e.clientY - hit.track.top, hit.track.height, hit.sliderHeight)
  lastPointerFraction = Math.min(1, Math.max(0, (e.clientY - hit.track.top) / hit.track.height))
  lastClientY = e.clientY
  show(t, hit.track)
  scrollToPreviewTop(t)
}

/** Instant, animation-free jump to the previewed viewport top. */
function scrollToPreviewTop(t: Terminal) {
  const vp = (t as any)?._core?._viewport
  if (typeof vp?.scrollToLine === 'function') {
    vp.scrollToLine(jumpTopLine, true)
  } else {
    t.scrollToLine(jumpTopLine)
  }
}

watch(
  () => props.sessionId,
  () => nextTick(bind),
  { immediate: false },
)

onMounted(() => nextTick(bind))
onBeforeUnmount(unbind)
</script>

<style scoped>
.terminal-screen-preview {
  position: absolute;
  z-index: 30;
  overflow: hidden;
  /* No left/right borders: the popup sits flush against the scrollbar, so
     side borders read as an extra divider next to it. Only top/bottom edges
     are drawn to keep the block visually bounded. */
  border: none;
  border-top: 1px solid var(--el-border-color, rgba(255, 255, 255, 0.2));
  border-bottom: 1px solid var(--el-border-color, rgba(255, 255, 255, 0.2));
  box-shadow: 0 0.25rem 1rem rgba(0, 0, 0, 0.35);
  padding: 0.125rem 0.25rem;
  box-sizing: content-box;
  /* Frosted glass: translucent background (inline, theme-tinted) + backdrop
     blur so the content beneath the popup shows through, blurred. Keep this
     the ONLY backdrop-filter declaration in the rule: pairing it with the
     -webkit- alias makes the CSS minifier merge the two into the prefixed
     form, which WebView2 (Chromium) does not honor — that silently removed
     the blur in production builds. */
  backdrop-filter: blur(0.5rem);
  /* Display-only: never intercepts the mouse, so hovering/clicking near it
     keeps working and the preview keeps refreshing underneath. */
  pointer-events: none;
}

.preview-line {
  display: flex;
  white-space: pre;
  overflow: hidden;
  /* Same tabular figures as the gutter so digits line up column-wide. */
  font-variant-numeric: tabular-nums;
}

.preview-col-time {
  flex: none;
  text-align: right;
  padding-right: 0.125rem;
}

.preview-col-num {
  flex: none;
  text-align: right;
  padding-right: 0.5rem;
}

.preview-content {
  flex: 1 1 auto;
  overflow: hidden;
}

.preview-blank {
  display: inline-block;
}
</style>
