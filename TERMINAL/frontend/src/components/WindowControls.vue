<template>
  <!-- macOS: traffic-light style (close/minimise/zoom as coloured dots) -->
  <div v-if="variant === 'mac'" class="window-controls mac">
      <button class="wc-btn mac close" @click="$emit('close')" :aria-label="t('window.close')" :title="t('window.close')">
        <svg viewBox="0 0 8 8"><path d="M1.2 1.2l5.6 5.6M6.8 1.2L1.2 6.8" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>
      </button>
      <button class="wc-btn mac minimise" @click="$emit('minimise')" :aria-label="t('window.minimize')" :title="t('window.minimize')">
        <svg viewBox="0 0 8 8"><path d="M1.2 4h5.6" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/></svg>
      </button>
      <button class="wc-btn mac maximise" @click="$emit('maximise')" :aria-label="t('window.maximize')" :title="t('window.maximize')">
        <svg v-if="isMaximised" viewBox="0 0 8 8">
          <!-- restore: two small triangles pointing inward -->
          <path d="M4.9 0.9L7.1 3.1 4.9 3.1zM3.1 7.1L0.9 4.9 3.1 4.9z" fill="currentColor"/>
        </svg>
        <svg v-else viewBox="0 0 8 8">
          <!-- zoom: two triangles pointing outward -->
          <path d="M3.1 0.9L0.9 3.1 3.1 3.1zM4.9 7.1L7.1 4.9 4.9 4.9z" fill="currentColor"/>
        </svg>
      </button>
  </div>

  <!-- Windows/Linux: match header-btn style -->
  <div v-else class="window-controls">
      <button class="wc-btn win minimise" @click="$emit('minimise')" :aria-label="t('window.minimize')">
        <svg viewBox="0 0 12 12" width="0.875rem" height="0.875rem"><path d="M1 5.5h10v1H1z"/></svg>
      </button>
      <button class="wc-btn win maximise" @click="$emit('maximise')" :aria-label="t('window.maximize')">
        <svg v-if="isMaximised" viewBox="0 0 12 12" width="0.875rem" height="0.875rem">
          <defs>
            <mask :id="restoreMaskId">
              <rect width="0.75rem" height="0.75rem" fill="white"/>
              <rect x="1" y="3.5" width="6.5" height="6.5" fill="black"/>
            </mask>
          </defs>
          <!-- 后方大矩形（右上），被前方遮挡重叠区域 -->
          <rect x="3.5" y="1" width="6.5" height="6.5" fill="none" stroke="currentColor" stroke-width="1" :mask="`url(#${restoreMaskId})`"/>
          <!-- 前方小矩形（左下），完整显示 -->
          <rect x="1" y="3.5" width="6.5" height="6.5" fill="none" stroke="currentColor" stroke-width="1"/>
        </svg>
        <svg v-else viewBox="0 0 12 12" width="0.875rem" height="0.875rem"><rect x="1.5" y="1.5" width="0.5625rem" height="0.5625rem" fill="none" stroke="currentColor" stroke-width="1"/></svg>
      </button>
      <button class="wc-btn win close" @click="$emit('close')" :aria-label="t('window.close')">
        <svg viewBox="0 0 12 12" width="0.875rem" height="0.875rem"><path d="M2 2l8 8M10 2L2 10" stroke="currentColor" stroke-width="1.2"/></svg>
      </button>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n'

const { t } = useI18n()

withDefaults(defineProps<{
  isMaximised: boolean
  /** 'mac' renders traffic-light dots, 'win' the header-btn-matching icons */
  variant?: 'win' | 'mac'
}>(), {
  variant: 'win'
})

defineEmits(['minimise', 'maximise', 'close'])

const restoreMaskId = `rm-${Math.random().toString(36).slice(2, 9)}`
</script>

<style scoped>
.window-controls {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  --wails-draggable: no-drag;
}

/* ── macOS traffic lights ── */
.window-controls.mac {
  gap: 0.5rem;
  /* nudge right of the header padding so the dots sit clear of the
     window's rounded corners, matching the native macOS inset */
  margin-left: 0.375rem;
}

.wc-btn.mac {
  width: 0.75rem;
  height: 0.75rem;
  padding: 0;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 0.5px rgba(0, 0, 0, 0.15);
}

.wc-btn.mac.close { background: #ff5f57; }
.wc-btn.mac.minimise { background: #febc2e; }
.wc-btn.mac.maximise { background: #28c840; }

/* Glyphs appear when hovering anywhere over the group (macOS behaviour) */
.wc-btn.mac svg {
  width: 0.5rem;
  height: 0.5rem;
  color: rgba(0, 0, 0, 0.55);
  opacity: 0;
  transition: opacity 0.1s ease;
}

.window-controls.mac:hover .wc-btn.mac svg {
  opacity: 1;
}

/* ── Windows/Linux buttons — match header-btn style ── */
.wc-btn.win {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.3125rem 0.5rem;
  height: 1.75rem;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  background: transparent;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.wc-btn.win:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.wc-btn.win.close:hover {
  background: #e81123;
  color: var(--on-accent);
}

.wc-btn.win.close:active {
  background: #f1707a;
}

.wc-btn.win svg {
  fill: currentColor;
}
</style>
