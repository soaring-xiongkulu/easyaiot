<template>
  <Teleport to="body">
    <Transition name="idea-edge">
      <div
        v-if="hidden"
        class="idea-float-edge"
        title="显示 AI 助手入口"
        @mouseenter="peek = true"
        @mouseleave="onEdgeLeave"
        @click="showBall"
      >
        <div class="idea-float-edge__tab" :class="{ 'is-peek': peek }">
          <svg class="idea-float-edge__icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 8V4H8" />
            <rect width="16" height="12" x="4" y="8" rx="2" />
            <path d="M2 14h2" />
            <path d="M20 14h2" />
            <path d="M9 13v2" />
            <path d="M15 13v2" />
          </svg>
        </div>
      </div>
    </Transition>

    <Transition name="idea-ball" appear>
      <div
        v-if="!hidden"
        ref="ballRef"
        class="idea-float-wrap"
        :class="{
          'is-dragging': dragging,
          'is-hover': hovering && !dragging,
          'is-settling': settling,
          'is-idle': !dragging && !hovering && !settling,
        }"
        :style="ballStyle"
        @mouseenter="hovering = true"
        @mouseleave="hovering = false"
      >
        <Transition name="idea-label">
          <div v-if="hovering && !dragging" class="idea-float-label">{{ appName }}</div>
        </Transition>
        <button
          type="button"
          class="idea-float-ball"
          :title="`按住左键拖动；单击打开${appName}；右键隐藏`"
          @click="onBallClick"
          @contextmenu.prevent="onContextMenu"
          @mousedown="onDragStart"
          @touchstart.passive="onTouchStart"
        >
          <span class="idea-float-ball__ring" aria-hidden="true" />
          <span class="idea-float-ball__core">
            <span class="idea-float-ball__shine" aria-hidden="true" />
            <svg class="idea-float-ball__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 8V4H8" />
              <rect width="16" height="12" x="4" y="8" rx="2" />
              <path d="M2 14h2" />
              <path d="M20 14h2" />
              <path d="M9 13v2" />
              <path d="M15 13v2" />
            </svg>
          </span>
        </button>
      </div>
    </Transition>

    <Transition name="idea-menu">
      <div
        v-if="menu.visible"
        class="idea-float-menu"
        :style="{ left: `${menu.x}px`, top: `${menu.y}px` }"
        @click.stop
      >
        <button type="button" @click="openIdea">打开{{ appName }}</button>
        <button type="button" @click="hideBall">隐藏入口</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { getHarnessAppName, openHarnessPortal } from '@/utils/harness'

defineOptions({ name: 'IdeaFloatBall' })

const appName = getHarnessAppName()

/** v2：默认展示悬浮球；旧 hidden=1 偏好不再沿用 */
const HIDE_KEY = 'easyaiot.idea.float.hidden.v2'
const POS_KEY = 'easyaiot.idea.float.pos.v5'

const BALL = 68
const RIGHT_INSET = 128
const CENTER_Y_RATIO = 0.46
const MARGIN = 24
const DRAG_THRESHOLD = 6

const hidden = ref(false)
const peek = ref(false)
const hovering = ref(false)
const dragging = ref(false)
const settling = ref(false)
const ballRef = ref<HTMLElement | null>(null)
const pos = reactive({ x: 0, y: 0 })
const menu = reactive({ visible: false, x: 0, y: 0 })

let dragMoved = false
let dragStartX = 0
let dragStartY = 0
let dragOffsetX = 0
let dragOffsetY = 0
let settleTimer: ReturnType<typeof setTimeout> | null = null

const ballStyle = computed(() => ({
  left: `${pos.x}px`,
  top: `${pos.y}px`,
}))

function defaultPos() {
  return {
    x: Math.max(MARGIN, window.innerWidth - BALL - RIGHT_INSET),
    y: Math.max(MARGIN, Math.round(window.innerHeight * CENTER_Y_RATIO - BALL / 2)),
  }
}

function clampPos(x: number, y: number) {
  const maxX = Math.max(MARGIN, window.innerWidth - BALL - MARGIN)
  const maxY = Math.max(MARGIN, window.innerHeight - BALL - MARGIN)
  return {
    x: Math.min(Math.max(MARGIN, x), maxX),
    y: Math.min(Math.max(MARGIN, y), maxY),
  }
}

function loadHidden() {
  try {
    hidden.value = localStorage.getItem(HIDE_KEY) === '1'
  } catch {
    hidden.value = false
  }
}

function loadPos() {
  try {
    const raw = localStorage.getItem(POS_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as { x?: number; y?: number }
      if (typeof parsed.x === 'number' && typeof parsed.y === 'number') {
        Object.assign(pos, clampPos(parsed.x, parsed.y))
        return
      }
    }
  } catch {
    // ignore
  }
  Object.assign(pos, defaultPos())
}

function persistPos() {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify({ x: pos.x, y: pos.y }))
  } catch {
    // ignore
  }
}

function persistHidden(value: boolean) {
  hidden.value = value
  try {
    localStorage.setItem(HIDE_KEY, value ? '1' : '0')
  } catch {
    // ignore
  }
}

function openIdea() {
  menu.visible = false
  // 统一跳转 IDEA 门户组合入口（默认 :9300?harness=1）
  openHarnessPortal()
}

function hideBall() {
  menu.visible = false
  persistHidden(true)
  peek.value = false
}

function showBall() {
  persistHidden(false)
  peek.value = false
}

function onBallClick() {
  if (dragMoved) {
    dragMoved = false
    return
  }
  openIdea()
}

function onContextMenu(e: MouseEvent) {
  menu.x = Math.min(e.clientX, window.innerWidth - 160)
  menu.y = Math.min(e.clientY, window.innerHeight - 96)
  menu.visible = true
}

function onEdgeLeave() {
  window.setTimeout(() => {
    if (hidden.value) {
      peek.value = false
    }
  }, 180)
}

function markDragIfNeeded(clientX: number, clientY: number) {
  if (dragMoved) {
    return
  }
  const dx = clientX - dragStartX
  const dy = clientY - dragStartY
  if (Math.hypot(dx, dy) >= DRAG_THRESHOLD) {
    dragMoved = true
  }
}

function onDragStart(e: MouseEvent) {
  if (e.button !== 0) {
    return
  }
  dragMoved = false
  dragging.value = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragOffsetX = e.clientX - pos.x
  dragOffsetY = e.clientY - pos.y
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

function onTouchStart(e: TouchEvent) {
  const t = e.touches[0]
  if (!t) {
    return
  }
  dragMoved = false
  dragging.value = true
  dragStartX = t.clientX
  dragStartY = t.clientY
  dragOffsetX = t.clientX - pos.x
  dragOffsetY = t.clientY - pos.y
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', onDragEnd)
}

function onDragMove(e: MouseEvent) {
  markDragIfNeeded(e.clientX, e.clientY)
  if (!dragMoved) {
    return
  }
  Object.assign(pos, clampPos(e.clientX - dragOffsetX, e.clientY - dragOffsetY))
}

function onTouchMove(e: TouchEvent) {
  const t = e.touches[0]
  if (!t) {
    return
  }
  markDragIfNeeded(t.clientX, t.clientY)
  if (!dragMoved) {
    return
  }
  e.preventDefault()
  Object.assign(pos, clampPos(t.clientX - dragOffsetX, t.clientY - dragOffsetY))
}

function playSettle() {
  settling.value = true
  if (settleTimer) {
    clearTimeout(settleTimer)
  }
  settleTimer = setTimeout(() => {
    settling.value = false
    settleTimer = null
  }, 360)
}

function onDragEnd() {
  dragging.value = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onDragEnd)
  if (dragMoved) {
    persistPos()
    playSettle()
  }
}

function onResize() {
  Object.assign(pos, clampPos(pos.x, pos.y))
  persistPos()
}

function onDocClick() {
  menu.visible = false
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    menu.visible = false
  }
}

onMounted(() => {
  loadHidden()
  loadPos()
  window.addEventListener('resize', onResize)
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
  if (settleTimer) {
    clearTimeout(settleTimer)
  }
  onDragEnd()
})
</script>

<style scoped>
/* 缓动曲线：自然、不拖沓 */
:root {
  --idea-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --idea-ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

/* 悬浮球进出场 */
.idea-ball-enter-active {
  transition:
    opacity 0.42s var(--idea-ease-out),
    transform 0.42s var(--idea-ease-out);
}
.idea-ball-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}
.idea-ball-enter-from,
.idea-ball-leave-to {
  opacity: 0;
  transform: scale(0.78) translateX(14px);
}

/* 贴边唤出条 */
.idea-edge-enter-active {
  transition:
    opacity 0.32s var(--idea-ease-out),
    transform 0.32s var(--idea-ease-out);
}
.idea-edge-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.idea-edge-enter-from,
.idea-edge-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(12px);
}

.idea-edge-enter-to,
.idea-edge-leave-from {
  transform: translateY(-50%) translateX(0);
}

/* 右键菜单 */
.idea-menu-enter-active {
  transition:
    opacity 0.22s var(--idea-ease-out),
    transform 0.22s var(--idea-ease-out);
}
.idea-menu-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}
.idea-menu-enter-from,
.idea-menu-leave-to {
  opacity: 0;
  transform: scale(0.94) translateY(-4px);
}

.idea-float-wrap {
  position: fixed;
  z-index: 1100;
  width: 68px;
  height: 68px;
  touch-action: none;
  transition:
    transform 0.32s var(--idea-ease),
    filter 0.32s var(--idea-ease);
}

.idea-float-wrap.is-idle {
  animation: idea-float-breathe 4.2s ease-in-out infinite;
}

@keyframes idea-float-breathe {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.idea-float-wrap.is-hover {
  animation: none;
  transform: translateY(-3px) scale(1.02);
}

.idea-float-wrap.is-dragging {
  animation: none;
  transition: none;
  transform: scale(1.04);
}

.idea-float-wrap.is-settling {
  animation: none;
  transition: transform 0.36s cubic-bezier(0.34, 1.25, 0.64, 1);
  transform: scale(1);
}

/* 悬停标签 */
.idea-label-enter-active {
  transition:
    opacity 0.24s var(--idea-ease-out),
    transform 0.24s var(--idea-ease-out);
}
.idea-label-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.idea-label-enter-from,
.idea-label-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(8px);
}

.idea-label-enter-to,
.idea-label-leave-from {
  opacity: 1;
  transform: translateY(-50%) translateX(0);
}

.idea-float-label {
  position: absolute;
  right: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%);
  padding: 7px 12px;
  border-radius: 18px;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  white-space: nowrap;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
  pointer-events: none;
}

.idea-float-ball {
  position: relative;
  width: 68px;
  height: 68px;
  padding: 0;
  border: none;
  border-radius: 50%;
  cursor: grab;
  background: transparent;
  filter: drop-shadow(0 5px 14px rgba(37, 99, 235, 0.16));
  transition: filter 0.32s var(--idea-ease);
}

.idea-float-wrap.is-hover .idea-float-ball {
  filter: drop-shadow(0 8px 20px rgba(37, 99, 235, 0.22));
}

.idea-float-wrap.is-dragging .idea-float-ball {
  cursor: grabbing;
  filter: drop-shadow(0 10px 24px rgba(37, 99, 235, 0.26));
}

.idea-float-ball__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background:
    conic-gradient(
      from 210deg,
      rgba(96, 165, 250, 0.5) 0deg 50deg,
      rgba(148, 163, 184, 0.2) 50deg 360deg
    );
  mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 calc(100% - 2px));
  pointer-events: none;
  transition: opacity 0.32s var(--idea-ease);
}

.idea-float-wrap.is-hover .idea-float-ball__ring {
  opacity: 1;
}

.idea-float-ball__core {
  position: absolute;
  inset: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background:
    radial-gradient(circle at 35% 30%, #ffffff 0%, #f5f9ff 42%, #e8f0fe 100%);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow:
    inset 0 2px 5px rgba(255, 255, 255, 0.9),
    inset 0 -4px 10px rgba(37, 99, 235, 0.08),
    0 3px 10px rgba(37, 99, 235, 0.1);
  transition:
    box-shadow 0.32s var(--idea-ease),
    transform 0.32s var(--idea-ease);
}

.idea-float-ball__shine {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(
    145deg,
    rgba(255, 255, 255, 0.75) 0%,
    rgba(255, 255, 255, 0.2) 38%,
    transparent 55%
  );
  pointer-events: none;
  transition: opacity 0.32s var(--idea-ease);
}

.idea-float-wrap.is-hover .idea-float-ball__core {
  transform: scale(1.04);
  box-shadow:
    inset 0 2px 6px rgba(255, 255, 255, 0.95),
    inset 0 -5px 12px rgba(37, 99, 235, 0.1),
    0 6px 16px rgba(37, 99, 235, 0.15);
}

.idea-float-wrap.is-dragging .idea-float-ball__core {
  transform: scale(0.98);
  box-shadow:
    inset 0 2px 6px rgba(255, 255, 255, 0.95),
    0 8px 22px rgba(37, 99, 235, 0.2);
}

.idea-float-ball__icon {
  position: relative;
  z-index: 1;
  width: 26px;
  height: 26px;
  fill: none;
  stroke: #2563eb;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.32s var(--idea-ease);
}

.idea-float-wrap.is-hover .idea-float-ball__icon {
  transform: scale(1.06);
}

.idea-float-edge {
  position: fixed;
  top: 46%;
  right: 0;
  z-index: 1099;
  width: 22px;
  height: 72px;
  transform: translateY(-50%);
  cursor: pointer;
}

.idea-float-edge__tab {
  position: absolute;
  right: 0;
  top: 0;
  width: 16px;
  height: 48px;
  border-radius: 10px 0 0 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%);
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-right: none;
  box-shadow: -2px 0 12px rgba(37, 99, 235, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    width 0.28s var(--idea-ease),
    box-shadow 0.28s var(--idea-ease),
    transform 0.28s var(--idea-ease);
}

.idea-float-edge__tab.is-peek {
  width: 24px;
  transform: translateX(-2px);
  box-shadow: -4px 0 16px rgba(37, 99, 235, 0.12);
}

.idea-float-edge__icon {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: #64748b;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: stroke 0.24s var(--idea-ease), transform 0.24s var(--idea-ease);
}

.idea-float-edge__tab.is-peek .idea-float-edge__icon {
  stroke: #2563eb;
  transform: scale(1.08);
}

@media (prefers-reduced-motion: reduce) {
  .idea-float-wrap.is-idle {
    animation: none;
  }

  .idea-ball-enter-active,
  .idea-ball-leave-active,
  .idea-edge-enter-active,
  .idea-edge-leave-active,
  .idea-menu-enter-active,
  .idea-menu-leave-active,
  .idea-label-enter-active,
  .idea-label-leave-active {
    transition-duration: 0.01ms !important;
  }
}

.idea-float-menu {
  position: fixed;
  z-index: 1200;
  min-width: 148px;
  padding: 6px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.14);
}

.idea-float-menu button {
  display: block;
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #111827;
}

.idea-float-menu button:hover {
  background: #f3f4f6;
}
</style>
