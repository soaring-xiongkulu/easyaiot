<template>
  <div v-if="visible" class="terminal-gutter" :style="gutterStyle" aria-hidden="true">
    <div
      v-for="row in layout.lines"
      :key="row.key"
      class="terminal-gutter-row"
      :style="{ height: layout.rowHeight + 'px', lineHeight: layout.rowHeight + 'px' }"
    >
      <span
        v-if="showTimestamps"
        class="terminal-gutter-time"
        :style="{ width: layout.timeWidth + 'px' }"
      >{{ row.timestamp }}</span>
      <span
        v-if="showLineNumbers"
        class="terminal-gutter-num"
        :style="{ width: layout.numWidth + 'px' }"
      >{{ row.lineNumber }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import type { Terminal } from '@xterm/xterm'
import { getManagedTerminal } from '../services/terminalManager'
import { buildGutterLines, formatTimestampMs, TIMESTAMP_WIDTH_SAMPLE_MS, type GutterRow } from '../utils/terminalGutter'
import { useSettingsStore } from '../stores/settingsStore'

const props = defineProps<{
  sessionId: string | null | undefined
  showLineNumbers: boolean
  showTimestamps: boolean
  /** Current host element that holds the attached `.xterm`, or null. */
  getHost?: () => HTMLElement | null
}>()

const settingsStore = useSettingsStore()

interface GutterLayout {
  lines: GutterRow[]
  rowHeight: number
  topPadding: number
  fontFamily: string
  fontSize: number
  cellWidth: number
  background: string
  number: string
  timestamp: string
  border: string
  timeWidth: number
  numWidth: number
}

const layout = ref<GutterLayout>({
  lines: [],
  rowHeight: 18,
  topPadding: 0,
  fontFamily: 'inherit',
  fontSize: 12,
  cellWidth: 8,
  background: '',
  number: '',
  timestamp: '',
  border: '',
  timeWidth: 0,
  numWidth: 24,
})

const visible = computed(() => props.showLineNumbers || props.showTimestamps)

let terminal: Terminal | null = null
let currentViewportY = 0
let updateRaf = 0
let bindRaf = 0
let disposables: Array<{ dispose(): void }> = []
let onRefreshGutter: ((e: Event) => void) | null = null

function withAlpha(color: string | undefined, alpha: number): string {
  const hex = (color || '').match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)
  if (!hex) return ''
  const h = hex[1]
  let r = 0, g = 0, b = 0
  if (h.length === 3) {
    r = parseInt(h[0] + h[0], 16); g = parseInt(h[1] + h[1], 16); b = parseInt(h[2] + h[2], 16)
  } else {
    r = parseInt(h.slice(0, 2), 16); g = parseInt(h.slice(2, 4), 16); b = parseInt(h.slice(4, 6), 16)
  }
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function scheduleUpdate() {
  cancelAnimationFrame(updateRaf)
  updateRaf = requestAnimationFrame(() => compute())
}

function clearSubscriptions() {
  for (const d of disposables) { try { d.dispose() } catch { /* noop */ } }
  disposables = []
}

function bindTerminal() {
  const managed = props.sessionId ? getManagedTerminal(props.sessionId) : undefined
  terminal = managed?.terminal ?? null

  // The parent acquires the terminal in its own onMounted, which runs after a
  // child's, so the managed instance may not exist on first mount — retry.
  if (!terminal) {
    clearSubscriptions()
    if (props.sessionId) {
      cancelAnimationFrame(bindRaf)
      bindRaf = requestAnimationFrame(bindTerminal)
    }
    return
  }

  clearSubscriptions()
  const t = terminal
  currentViewportY = t.buffer.active.viewportY

  disposables = [
    t.onRender(() => { currentViewportY = t.buffer.active.viewportY; scheduleUpdate() }),
    t.onWriteParsed(() => { currentViewportY = t.buffer.active.viewportY; scheduleUpdate() }),
    t.onScroll((v) => { currentViewportY = v; scheduleUpdate() }),
    t.onResize(() => { currentViewportY = t.buffer.active.viewportY; scheduleUpdate() }),
  ]
  compute()
  setTimeout(compute, 0)
}

function compute() {
  const t = terminal
  const host = props.getHost?.()
  // Only render when this component's own host actually shows the terminal —
  // a cached (KeepAlive) or drag-detached instance must not paint numbers.
  if (!t || !t.element || !host || !host.contains(t.element)) {
    layout.value = { ...layout.value, lines: [] }
    return
  }

  const managed = t ? getManagedTerminal(props.sessionId || '') : undefined
  const buf = t.buffer.active
  // Use the font-canonical character dimensions, NOT the rendered cell size.
  // The cell size is derived from cols (hostWidth/cols), so sizing the gutter
  // from it feeds back: wider gutter → fewer cols → wider cell → … oscillation
  // (the terminal visibly shakes side to side when the gutter is on). The
  // canonical character size is constant for a given font/size, so the gutter
  // width is stable regardless of the host width it shrinks.
  let cellWidth = 0
  let cellHeight = 0
  try {
    const css = (t as any)._core?._renderService?.dimensions?.css
    const ch = css?.character
    const cell = css?.cell
    cellWidth = ch?.width || cell?.width || 0
    cellHeight = ch?.height || cell?.height || 0
  } catch { /* noop */ }
  if (!cellWidth || !cellHeight) return

  const screen = t.element.querySelector('.xterm-screen') as HTMLElement | null
  const topPadding = screen
    ? Math.max(0, screen.getBoundingClientRect().top - host.getBoundingClientRect().top)
    : 0

  const viewport = Math.max(0, Math.min(buf.baseY, currentViewportY))
  const alternate = buf.type === 'alternate'
  const lineOffset = alternate ? 0 : (managed?.lineOffset ?? 0)
  const theme = t.options.theme ?? {}
  const fg = theme?.foreground

  const tsFormat = settingsStore.settings.terminal.timestampFormat || 'HH:mm:ss'
  const registry = managed?.lineRegistry

  const result = buildGutterLines({
    rows: t.rows,
    viewportY: viewport,
    lineOffset,
    showTimestamps: props.showTimestamps,
    cursorAbsoluteY: buf.baseY + buf.cursorY,
    getLine: (n) => buf.getLine(n),
    getMeta: (abs) => {
      // Alternate screen lines are transient — fall back to per-screen
      // positional numbers, no timestamps.
      if (alternate) return { number: abs + 1 }
      return registry?.entries.get(abs)
    },
    maxNumberHint: registry && !alternate ? registry.nextNumber - 1 : 0,
    formatTimestamp: (ms) => formatTimestampMs(ms, tsFormat),
  })

  const maxDigits = String(Math.max(result.maxLineNumber, 1)).length
  const timeWidth = props.showTimestamps
    ? Math.ceil(cellWidth * formatTimestampMs(TIMESTAMP_WIDTH_SAMPLE_MS, tsFormat).length) + 2
    : 0
  const numWidth = props.showLineNumbers
    ? Math.max(Math.ceil(cellWidth * maxDigits) + 8, 24)
    : 0

  layout.value = {
    lines: result.lines,
    rowHeight: cellHeight,
    topPadding,
    fontFamily: String(t.options.fontFamily ?? 'inherit'),
    fontSize: Number(t.options.fontSize ?? 12),
    cellWidth,
    background: theme?.background || '',
    number: withAlpha(fg, 0.6),
    timestamp: withAlpha(fg, 0.85),
    border: withAlpha(fg, 0.16),
    timeWidth,
    numWidth,
  }
}

const gutterStyle = computed(() => {
  const l = layout.value
  const colGap = props.showLineNumbers && props.showTimestamps ? 12 : 0
  const width = (props.showTimestamps ? l.timeWidth : 0) +
    (props.showLineNumbers ? l.numWidth : 0) +
    colGap
  return {
    width: (width + (width > 0 ? 0 : 24)) + 'px',
    backgroundColor: l.background,
    color: l.timestamp,
    fontFamily: l.fontFamily,
    fontSize: l.fontSize + 'px',
    paddingTop: l.topPadding + 'px',
    '--tg-num': l.number,
    '--tg-border': l.border,
  }
})

watch(() => props.sessionId, bindTerminal)
watch(() => settingsStore.settings.terminal, () => scheduleUpdate(), { deep: true })

onMounted(() => {
  onRefreshGutter = () => scheduleUpdate()
  window.addEventListener('terminal:refresh-gutter', onRefreshGutter)
  bindTerminal()
})
onBeforeUnmount(() => {
  cancelAnimationFrame(updateRaf)
  cancelAnimationFrame(bindRaf)
  if (onRefreshGutter) window.removeEventListener('terminal:refresh-gutter', onRefreshGutter)
  clearSubscriptions()
})
</script>

<style scoped>
.terminal-gutter {
  box-sizing: content-box;
  flex: 0 0 auto;
  overflow: hidden;
  user-select: none;
  text-align: right;
  border-right: 1px solid var(--tg-border, transparent);
  pointer-events: none;
}
.terminal-gutter-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  box-sizing: border-box;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.terminal-gutter-time {
  display: inline-block;
  text-align: right;
  padding-right: 0.125rem;
}
.terminal-gutter-num {
  display: inline-block;
  text-align: right;
  padding-right: 0.5rem;
  color: var(--tg-num, currentColor);
}
</style>