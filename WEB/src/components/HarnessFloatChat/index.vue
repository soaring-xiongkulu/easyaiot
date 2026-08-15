<template>
  <Teleport to="body">
    <Transition name="harness-edge">
      <div
        v-if="hidden"
        class="harness-chat-edge"
        :title="`显示${appName}`"
        @mouseenter="peek = true"
        @mouseleave="peek = false"
        @click="showEntry"
      >
        <div class="harness-chat-edge__tab" :class="{ 'is-peek': peek }">
          <svg class="harness-chat-edge__icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
          </svg>
        </div>
      </div>
    </Transition>

    <Transition name="harness-panel">
      <div
        v-if="!hidden && panelOpen"
        class="harness-chat-panel"
        :class="{ 'is-expanded': expanded }"
        :style="panelStyle"
      >
        <header class="harness-chat-panel__header">
          <div class="harness-chat-panel__title">
            <span class="harness-chat-panel__dot" :class="{ 'is-online': health.online }" />
            <img v-if="logoUrl" class="harness-chat-panel__logo" :src="logoUrl" alt="" />
            <span>{{ appName }}</span>
            <span v-if="!health.online" class="harness-chat-panel__offline">未就绪</span>
          </div>
          <div class="harness-chat-panel__actions">
            <button type="button" title="刷新" @click="reloadFrame">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08a5.99 5.99 0 0 1-5.65 4c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
              </svg>
            </button>
            <button type="button" :title="expanded ? '缩小' : '放大'" @click="expanded = !expanded">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-if="expanded" d="M8 3v3H5v2h3v3h2V8h3V6h-3V3H8zm8 10v3h-3v2h3v3h2v-3h3v-2h-3v-3h-2z" />
                <path v-else d="M4 10V4h6V2H2v8h2zm10 0h2V4h-6V2h8v8h-2zM4 20v-6H2v8h8v-2H4zm16 0h-6v2h8v-8h-2v6z" />
              </svg>
            </button>
            <button type="button" title="管控台全屏页" @click="goFullPage">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
              </svg>
            </button>
            <button type="button" title="新窗口打开" @click="openExternal">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z" />
              </svg>
            </button>
            <button type="button" title="最小化" @click="closePanel">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M19 13H5v-2h14v2z" />
              </svg>
            </button>
          </div>
        </header>
        <div class="harness-chat-panel__body">
          <div v-if="!health.online" class="harness-chat-panel__offline-banner">
            <p>HARNESS 服务未就绪（:3080）</p>
            <code>bash HARNESS/install.sh start</code>
            <button type="button" @click="reloadFrame">重试连接</button>
          </div>
          <iframe
            v-show="health.online"
            :key="iframeKey"
            class="harness-chat-panel__frame"
            :src="portalUrl"
            :title="iframeTitle"
            allow="clipboard-read; clipboard-write"
          />
        </div>
      </div>
    </Transition>

    <Transition name="harness-fab">
      <div
        v-if="!hidden && !panelOpen"
        class="harness-chat-fab-wrap"
        @mouseenter="fabHover = true"
        @mouseleave="fabHover = false"
      >
        <Transition name="harness-label">
          <div v-if="fabHover" class="harness-chat-fab-label">{{ appName }}</div>
        </Transition>
        <button
          type="button"
          class="harness-chat-fab"
          :title="`打开${appName} · 右键更多`"
          @click="openPanel"
          @contextmenu.prevent="openMenu"
        >
          <span class="harness-chat-fab__ring" aria-hidden="true" />
          <span class="harness-chat-fab__core">
            <img v-if="logoUrl" class="harness-chat-fab__logo" :src="logoUrl" alt="" />
            <svg v-else class="harness-chat-fab__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z" />
            </svg>
          </span>
        </button>
      </div>
    </Transition>

    <Transition name="harness-menu">
      <div
        v-if="menu.visible"
        class="harness-chat-menu"
        :style="{ left: `${menu.x}px`, top: `${menu.y}px` }"
        @click.stop
      >
        <button type="button" @click="openPanel">打开聊天窗</button>
        <button type="button" @click="goFullPage">管控台内全屏</button>
        <button type="button" @click="openExternal">新窗口打开</button>
        <button type="button" @click="hideEntry">隐藏入口</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  HARNESS_PANEL_OPEN_EVENT,
  checkHarnessHealth,
  getHarnessAppName,
  getHarnessLogoUrl,
  getHarnessPortalUrl,
  isHarnessFloatHidden,
  isHarnessPanelOpen,
  openHarnessPortal,
  setHarnessFloatHidden,
  setHarnessPanelOpen,
  type HarnessHealth,
} from '@/utils/harness'
import { usePlatformBranding } from '@/hooks/web/usePlatformBranding'

defineOptions({ name: 'HarnessFloatChat' })

const router = useRouter()
const route = useRoute()
const { config: branding } = usePlatformBranding()
const portalUrl = getHarnessPortalUrl()
const appName = computed(() => getHarnessAppName())
const logoUrl = computed(() => getHarnessLogoUrl() || branding.value.platformLogo)
const iframeTitle = computed(() => appName.value)
const hidden = ref(false)
const panelOpen = ref(false)
const expanded = ref(false)
const peek = ref(false)
const fabHover = ref(false)
const iframeKey = ref(0)
const health = reactive<HarnessHealth>({ online: false })
const menu = reactive({ visible: false, x: 0, y: 0 })

const panelStyle = computed(() => {
  if (expanded.value) {
    return {
      width: 'min(960px, calc(100vw - 32px))',
      height: 'min(820px, calc(100vh - 48px))',
    }
  }
  return {
    width: 'min(420px, calc(100vw - 32px))',
    height: 'min(680px, calc(100vh - 120px))',
  }
})

watch(panelOpen, (open) => {
  setHarnessPanelOpen(open)
})

function closeMenu() {
  menu.visible = false
}

function openPanel() {
  closeMenu()
  // 仅允许 IDEA 门户组合入口，不再内嵌独立 HARNESS
  openHarnessPortal()
}

function closePanel() {
  panelOpen.value = false
}

function goFullPage() {
  closeMenu()
  panelOpen.value = false
  openHarnessPortal()
}

function openExternal() {
  closeMenu()
  openHarnessPortal()
}

function hideEntry() {
  closeMenu()
  hidden.value = true
  panelOpen.value = false
  setHarnessFloatHidden(true)
}

function showEntry() {
  hidden.value = false
  setHarnessFloatHidden(false)
  openPanel()
}

function openMenu(ev: MouseEvent) {
  menu.visible = true
  menu.x = ev.clientX
  menu.y = ev.clientY
}

function reloadFrame() {
  iframeKey.value += 1
  refreshHealth(true)
}

async function refreshHealth(forceReload = false) {
  const wasOnline = health.online
  const result = await checkHarnessHealth()
  health.online = result.online
  health.status = result.status
  health.latencyMs = result.latencyMs
  if (forceReload || (!wasOnline && result.online)) {
    iframeKey.value += 1
  }
}

function onDocClick() {
  closeMenu()
}

function onPanelOpenRequest() {
  if (hidden.value) {
    hidden.value = false
    setHarnessFloatHidden(false)
  }
  openPanel()
}

function onRouteOpenQuery() {
  if (route.query.harness === 'open') {
    onPanelOpenRequest()
    const { harness: _removed, ...rest } = route.query
    router.replace({ query: rest })
  }
}

onMounted(() => {
  hidden.value = isHarnessFloatHidden()
  panelOpen.value = !hidden.value && isHarnessPanelOpen()
  refreshHealth()
  onRouteOpenQuery()
  document.addEventListener('click', onDocClick)
  window.addEventListener(HARNESS_PANEL_OPEN_EVENT, onPanelOpenRequest)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener(HARNESS_PANEL_OPEN_EVENT, onPanelOpenRequest)
})
</script>

<style scoped>
.harness-chat-panel {
  --harness-ease: cubic-bezier(0.22, 1, 0.36, 1);
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1195;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow:
    0 24px 48px rgba(15, 23, 42, 0.18),
    0 8px 16px rgba(91, 33, 182, 0.08);
  transition: width 0.28s var(--harness-ease), height 0.28s var(--harness-ease);
}

.harness-chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px 10px 14px;
  background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 55%, #2563eb 100%);
  color: #fff;
  flex-shrink: 0;
  user-select: none;
}

.harness-chat-panel__logo {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  object-fit: contain;
}

.harness-chat-panel__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.harness-chat-panel__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.35);
}

.harness-chat-panel__dot.is-online {
  background: #34d399;
  box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.35);
}

.harness-chat-panel__offline {
  font-size: 11px;
  font-weight: 400;
  opacity: 0.85;
}

.harness-chat-panel__actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.harness-chat-panel__actions button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
  transition: background 0.2s ease;
}

.harness-chat-panel__actions button:hover {
  background: rgba(255, 255, 255, 0.22);
}

.harness-chat-panel__actions svg {
  width: 14px;
  height: 14px;
  fill: #fff;
}

.harness-chat-panel__body {
  flex: 1;
  min-height: 0;
  background: #f8fafc;
  position: relative;
}

.harness-chat-panel__offline-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  min-height: 280px;
  padding: 24px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
}

.harness-chat-panel__offline-banner p {
  margin: 0;
  color: #334155;
  font-weight: 500;
}

.harness-chat-panel__offline-banner code {
  display: block;
  padding: 10px 14px;
  border-radius: 8px;
  background: #1e293b;
  color: #e2e8f0;
  font-size: 12px;
}

.harness-chat-panel__offline-banner button {
  margin-top: 4px;
  padding: 6px 16px;
  border: 1px solid #c4b5fd;
  border-radius: 8px;
  background: #faf5ff;
  color: #5b21b6;
  font-size: 13px;
  cursor: pointer;
}

.harness-chat-panel__offline-banner button:hover {
  background: #f3e8ff;
}

.harness-chat-panel__frame {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 360px;
  border: none;
  background: #fff;
}

.harness-chat-fab-wrap {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 1190;
}

.harness-chat-fab-label {
  position: absolute;
  right: 68px;
  top: 50%;
  transform: translateY(-50%);
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.88);
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.2);
}

.harness-chat-fab {
  position: relative;
  width: 56px;
  height: 56px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
  transition: transform 0.24s cubic-bezier(0.22, 1, 0.36, 1);
}

.harness-chat-fab-wrap:hover .harness-chat-fab {
  transform: scale(1.06);
}

.harness-chat-fab__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #2563eb);
  opacity: 0.35;
  animation: harness-pulse 2.8s ease-in-out infinite;
}

.harness-chat-fab__core {
  position: absolute;
  inset: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(145deg, #6d28d9 0%, #4f46e5 55%, #2563eb 100%);
  box-shadow:
    0 8px 24px rgba(91, 33, 182, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.harness-chat-fab__logo {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  object-fit: contain;
}

.harness-chat-fab__icon {
  width: 26px;
  height: 26px;
  fill: #fff;
}

.harness-chat-edge {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1185;
  padding: 8px 0;
  cursor: pointer;
}

.harness-chat-edge__tab {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 56px;
  border-radius: 0 10px 10px 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-left: none;
  box-shadow: 4px 0 16px rgba(91, 33, 182, 0.08);
  transition: all 0.24s cubic-bezier(0.22, 1, 0.36, 1);
}

.harness-chat-edge__tab.is-peek {
  width: 28px;
  background: #faf5ff;
  border-color: #c4b5fd;
}

.harness-chat-edge__icon {
  width: 14px;
  height: 14px;
  fill: #7c3aed;
}

.harness-chat-menu {
  position: fixed;
  z-index: 1200;
  min-width: 160px;
  padding: 6px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.14);
}

.harness-chat-menu button {
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

.harness-chat-menu button:hover {
  background: #faf5ff;
  color: #5b21b6;
}

@keyframes harness-pulse {
  0%, 100% { transform: scale(1); opacity: 0.35; }
  50% { transform: scale(1.08); opacity: 0.2; }
}

.harness-panel-enter-active,
.harness-panel-leave-active {
  transition: all 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}

.harness-panel-enter-from,
.harness-panel-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}

.harness-fab-enter-active,
.harness-fab-leave-active {
  transition: all 0.24s ease;
}

.harness-fab-enter-from,
.harness-fab-leave-to {
  opacity: 0;
  transform: scale(0.7);
}

.harness-edge-enter-active,
.harness-edge-leave-active {
  transition: opacity 0.24s ease;
}

.harness-edge-enter-from,
.harness-edge-leave-to {
  opacity: 0;
}

.harness-label-enter-active,
.harness-label-leave-active {
  transition: all 0.2s ease;
}

.harness-label-enter-from,
.harness-label-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(8px);
}

.harness-menu-enter-active,
.harness-menu-leave-active {
  transition: all 0.18s ease;
}

.harness-menu-enter-from,
.harness-menu-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 480px) {
  .harness-chat-panel {
    right: 8px;
    bottom: 8px;
    width: calc(100vw - 16px) !important;
    height: calc(100vh - 80px) !important;
    border-radius: 12px;
  }

  .harness-chat-fab-wrap {
    right: 16px;
    bottom: 16px;
  }
}
</style>
