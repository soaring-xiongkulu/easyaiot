<template>
  <!-- Mobile soft keyboards lack Esc/Tab/arrows/Ctrl combos. This bar sits at
       the bottom of the app (directly above the soft keyboard, because
       MainActivity pads the app root by the IME inset) while a terminal input
       has focus. Keys go straight to the session via queuedSessionWrite;
       sticky Ctrl combines with the next soft-keyboard character via
       applyMobileCtrl in BaseTerminal's onData path. -->
  <div class="mobile-key-bar">
    <div class="key-bar-scroll">
      <!-- pointerdown + preventDefault: sending on click would let the tap
           move focus off the terminal textarea, which closes the soft
           keyboard and unmounts this bar before the click ever fires. -->
      <button
        v-for="key in KEYS"
        :key="key.label"
        class="key-btn"
        :class="{ sticky: key.sticky && mobileCtrlArmed }"
        @pointerdown.prevent="onKey(key)"
      >{{ key.label }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { queuedSessionWrite } from '../services/sessionWriter'
import { mobileCtrlArmed } from '../utils/mobileCtrlKey'

interface BarKey {
  label: string
  seq: string
  /** CSI final byte for modifier sequences (arrows) */
  csi?: string
  /** sticky toggle button (Ctrl) */
  sticky?: boolean
}

// Keys kept to the essentials — everything else is reachable from the soft
// keyboard (punctuation lives on its symbol page).
const KEYS: BarKey[] = [
  { label: 'Esc', seq: '\x1b' },
  { label: 'Tab', seq: '\t' },
  { label: 'Ctrl', sticky: true, seq: '' },
  { label: '↑', seq: '\x1b[A', csi: 'A' },
  { label: '↓', seq: '\x1b[B', csi: 'B' },
  { label: '←', seq: '\x1b[D', csi: 'D' },
  { label: '→', seq: '\x1b[C', csi: 'C' },
  { label: '/', seq: '/' },
  { label: ':', seq: ':' },
]

function onKey(key: BarKey) {
  if (key.sticky) {
    mobileCtrlArmed.value = !mobileCtrlArmed.value
  } else {
    // Ctrl+arrow jumps words in most shells — 1;5C / 1;5D etc.
    const seq = mobileCtrlArmed.value
      ? `\x1b[1;5${key.csi}`
      : key.seq
    mobileCtrlArmed.value = false
    queuedSessionWrite(props.sessionId, seq)
  }
  // Defensive: keep focus on the terminal so the soft keyboard stays up even
  // if the browser still moved focus despite pointerdown preventDefault.
  const ta = document.querySelector('.xterm-helper-textarea') as HTMLElement | null
  ta?.focus()
}

const props = defineProps<{ sessionId: string }>()
</script>

<style scoped>
.mobile-key-bar {
  flex-shrink: 0;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border-subtle);
  /* keep the bar above the webview's own touch gestures */
  touch-action: manipulation;
}

.key-bar-scroll {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem 0.375rem;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
}
.key-bar-scroll::-webkit-scrollbar {
  display: none;
}

.key-btn {
  flex-shrink: 0;
  min-width: 2.125rem;
  height: 2rem;
  padding: 0 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  cursor: pointer;
  user-select: none;
  /* don't let the bar's horizontal scroll steal the tap */
  touch-action: none;
}

.key-btn:active {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.key-btn.sticky {
  font-family: var(--font-ui);
  font-weight: 600;
  color: var(--accent);
  border-color: var(--accent);
}
</style>
