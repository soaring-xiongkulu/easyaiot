<template>
  <div
    ref="popupRef"
    v-show="visible"
    class="terminal-suggestion-popup"
    :style="popupStyle"
  >
    <!-- Scrollable history list -->
    <div class="history-list" ref="historyListRef">
      <div
        v-for="{ item, index } in historyItemsWithIndex"
        :key="item.id"
        :ref="(el) => setItemRef(el as HTMLElement, index)"
        class="suggestion-item"
        :class="{ selected: index === selectedIndex }"
        @click="onSelect(index)"
        @mouseenter="onHover(index)"
      >
        <span class="suggestion-desc">
          <el-icon v-if="item.type === 'quick-command'"><Zap :size="'0.75rem'" /></el-icon>
          <el-icon v-else-if="item.type === 'history'"><Clock :size="'0.75rem'" /></el-icon>
        </span>
        <span v-if="item.type === 'quick-command' && item.label !== item.value" class="suggestion-label">
          <span class="qc-name">
            <template v-for="(char, charIdx) in item.label" :key="charIdx">
              <span :class="{ 'match-char': item.matchIndices?.includes(charIdx) }">{{ char }}</span>
            </template>
          </span>
          <span class="qc-cmd">
            <template v-for="(char, charIdx) in item.value" :key="charIdx">
              <span :class="{ 'match-char': item.commandMatchIndices?.includes(charIdx) }">{{ char }}</span>
            </template>
          </span>
        </span>
        <span v-else class="suggestion-label">
          <template v-for="(char, charIdx) in item.label" :key="charIdx">
            <span :class="{ 'match-char': item.matchIndices?.includes(charIdx) }">{{ char }}</span>
          </template>
        </span>
        <button class="delete-btn" :class="{ visible: item.type === 'history' }" @click.stop="onRemove(item.id)"><Trash2 :size="'0.75rem'" /></button>
      </div>
    </div>
    <!-- AI section (fixed at bottom) -->
    <div
      v-if="aiItemWithIndex"
      class="suggestion-item ai-fixed"
      :class="{
        selected: aiItemWithIndex.index === selectedIndex,
        'ai-result': aiItemWithIndex.item.type === 'ai-result',
        'ai-preview': aiItemWithIndex.item.type === 'ai-preview'
      }"
      @click="onSelect(aiItemWithIndex.index)"
      @mouseenter="onHover(aiItemWithIndex.index)"
    >
      <span class="suggestion-desc">
        <el-icon><Sparkles :size="'0.75rem'" /></el-icon>
      </span>
      <span class="suggestion-label">{{ aiItemWithIndex.item.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Trash2, Clock, Zap, Sparkles } from '@lucide/vue'
import type { SuggestionItem } from '../composables/useSuggestions'

const props = defineProps<{
  visible: boolean
  items: SuggestionItem[]
  selectedIndex: number
  cursorX: number
  cursorY: number
}>()

const emit = defineEmits<{
  select: [index: number]
  hover: [index: number]
  remove: [id: string]
}>()

const popupRef = ref<HTMLDivElement | null>(null)
const adjustedY = ref(0)
const screenPos = ref({ x: 0, y: 0 })
const mouseMoved = ref(false)

watch(() => props.visible, (v) => {
  if (v) mouseMoved.value = false
})

function onGlobalMouseMove() {
  mouseMoved.value = true
}

onMounted(() => {
  document.addEventListener('mousemove', onGlobalMouseMove)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onGlobalMouseMove)
})

const popupStyle = computed(() => ({
  position: 'fixed' as const,
  left: `${screenPos.value.x}px`,
  top: `${screenPos.value.y}px`,
}))

const itemRefs = ref<Record<number, HTMLElement>>({})
const historyListRef = ref<HTMLDivElement | null>(null)

function adjustPosition() {
  if (!props.visible) {
    adjustedY.value = 0
    screenPos.value = { x: 0, y: 0 }
    return
  }
  nextTick(() => {
    const popupEl = popupRef.value
    const terminalEl = popupEl?.closest('.base-terminal') as HTMLElement | null
    if (!popupEl || !terminalEl) return
    const popupRect = popupEl.getBoundingClientRect()
    const terminalRect = terminalEl.getBoundingClientRect()
    const cursorScreenX = terminalRect.left + props.cursorX
    const cursorScreenY = terminalRect.top + props.cursorY

    // Space below cursor line (within terminal area)
    const spaceBelow = terminalRect.bottom - cursorScreenY - 8
    // Space above cursor line
    const spaceAbove = cursorScreenY - terminalRect.top - 8

    // cursorY = (buffer.y + 1) * cellHeight (bottom edge of cursor line)
    const cellHeight = 17
    if (spaceBelow >= popupRect.height + 4) {
      // Enough room below — show below cursor line with 4px gap
      adjustedY.value = 4
    } else if (spaceAbove >= popupRect.height + 4) {
      // Not enough below — show above cursor line.
      // Popup bottom must be above cursor top (cursorY - cellHeight).
      // adjustedY = cursorTop - gap - popupHeight - cursorY
      //            = (cursorY - cellHeight) - 4 - popupHeight - cursorY
      //            = -(cellHeight + 4 + popupHeight)
      adjustedY.value = -(cellHeight + 4 + popupRect.height)
    } else {
      // Neither direction has full room — show below and push up to fit
      adjustedY.value = -(popupRect.height - spaceBelow + 4)
    }

    // Update fixed-position screen coordinates
    screenPos.value = {
      x: cursorScreenX,
      y: cursorScreenY + adjustedY.value,
    }
  })
}

watch(() => props.visible, (visible) => {
  if (visible) adjustPosition()
  else {
    adjustedY.value = 0
    screenPos.value = { x: 0, y: 0 }
  }
})

watch(() => props.items, () => {
  if (props.visible) adjustPosition()
}, { deep: true })

const historyItemsWithIndex = computed(() => {
  const result: { item: SuggestionItem; index: number }[] = []
  props.items.forEach((item, index) => {
    if (item.type !== 'ai-preview' && item.type !== 'ai-result') {
      result.push({ item, index })
    }
  })
  return result
})

const aiItemWithIndex = computed(() => {
  const index = props.items.findIndex(item => item.type === 'ai-preview' || item.type === 'ai-result')
  if (index >= 0) {
    return { item: props.items[index], index }
  }
  return null
})

function setItemRef(el: HTMLElement | null, index: number) {
  if (el) {
    itemRefs.value[index] = el
  }
}

// Reset scroll position to top when items change (new input triggers refresh)
watch(() => props.items, () => {
  nextTick(() => {
    if (historyListRef.value) {
      historyListRef.value.scrollTop = 0
    }
  })
}, { deep: true })

// Scroll selected history item into view when navigating with arrow keys.
// AI items are fixed at the bottom and should not scroll.
watch(() => props.selectedIndex, (newIndex) => {
  nextTick(() => {
    const item = props.items[newIndex]
    if (!item || item.type === 'ai-preview' || item.type === 'ai-result') return
    const el = itemRefs.value[newIndex]
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
})

function onSelect(index: number) {
  emit('select', index)
}

function onHover(index: number) {
  if (!mouseMoved.value) return
  emit('hover', index)
}

function onRemove(id: string) {
  emit('remove', id)
}
</script>

<style scoped>
.terminal-suggestion-popup {
  position: fixed;
  z-index: 100;
  min-width: 12.5rem;
  max-width: 25rem;
  max-height: 12.5rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(0.5rem);
}

.history-list {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  padding: 0.25rem 0 0 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  transition: background 0.1s ease;
}

.suggestion-item:hover,
.suggestion-item.selected {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.suggestion-item.ai-result {
  border-left: 0.1875rem solid var(--success);
}

.suggestion-item.ai-preview {
  color: var(--accent);
}

.ai-fixed {
  flex-shrink: 0;
  border-top: 1px solid var(--border-subtle);
  padding-top: 0.5rem;
  background: var(--bg-surface);
}

.suggestion-icon {
  font-size: 0.75rem;
  opacity: 0.7;
}

.suggestion-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.suggestion-label .qc-name {
  display: block;
  font-size: 0.8125rem;
  color: var(--text-primary);
  line-height: 1.3;
}

.suggestion-label .qc-cmd {
  display: block;
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.match-char {
  color: var(--accent);
  font-weight: 600;
}

.suggestion-desc {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
}

.delete-btn {
  display: flex;
  width: 1rem;
  height: 1rem;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1;
  border-radius: 0.125rem;
  padding: 0;
  margin-left: 0.125rem;
  flex-shrink: 0;
  visibility: hidden;
  opacity: 0;
  transition: opacity 0.12s ease, visibility 0.12s ease;
}

.suggestion-item:hover .delete-btn.visible {
  visibility: visible;
  opacity: 1;
}

.delete-btn:hover {
  background: var(--error-subtle);
  color: var(--error);
}

.history-list::-webkit-scrollbar {
  width: 0.375rem;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

.history-list::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 0.1875rem;
}
</style>
