<template>
  <div class="rdp-tab-content">
    <!-- Connecting state -->
    <div v-if="status === 'connecting'" class="rdp-overlay">
      <el-icon class="is-loading" :size="'2rem'"><Loader /></el-icon>
      <p>{{ t('rdp.connecting', { host: config?.host || '...' }) }}</p>
    </div>

    <!-- Error state -->
    <div v-else-if="status === 'error'" class="rdp-overlay">
      <p class="rdp-error-text">{{ t('rdp.error') }}</p>
      <p v-if="errorMessage" class="rdp-error-detail">{{ errorMessage }}</p>
      <el-button type="primary" @click="reconnect">{{ t('rdp.retry') }}</el-button>
    </div>

    <!-- Disconnected state -->
    <div v-else-if="status === 'disconnected'" class="rdp-overlay">
      <p>{{ t('rdp.disconnected') }}</p>
      <el-button type="primary" @click="reconnect">{{ t('rdp.reconnect') }}</el-button>
    </div>

    <!-- Connected: placeholder div overlaid by native RDP popup window -->
    <div
      v-show="status === 'connected'"
      class="rdp-area"
    />

    <!-- Status bar -->
    <div v-if="status === 'connected'" class="rdp-statusbar">
      <span class="rdp-status-dot" />
      <span>{{ t('rdp.connected') }}</span>
      <span class="rdp-status-sep">|</span>
      <span>{{ config?.host }}:{{ config?.port || 3389 }}</span>
      <span class="rdp-status-sep">|</span>
      <span>{{ t('rdp.resolution') }}: {{ statusResolution }}</span>
      <span class="rdp-status-spacer" />
      <button class="rdp-fullscreen-btn" @click="enterFullScreen">{{ t('rdp.fullscreen') }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Loader } from '@lucide/vue'
import { useI18n } from '../i18n'
import type { ConnectionConfig } from '../types/session'
import { CreateSession, CloseSession, RDPHide, RDPSetFullScreen } from '../../bindings/easyaiot/terminal/app'
import { backendErrorText, backendErrorTextOf } from '../utils/backendError'
import { Events } from '@wailsio/runtime'
import { usePanelStore } from '../stores/panelStore'

const { t } = useI18n()
const panelStore = usePanelStore()

const props = defineProps<{
  panelId: string
  config: ConnectionConfig | null
  sessionId: string | null
}>()

const status = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting')
const currentSessionId = ref<string | null>(props.sessionId)
const errorMessage = ref<string>('')
const statusResolution = computed(() => {
  if (props.config?.rdpFixedWidth === -1 || props.config?.rdpFixedHeight === -1) {
    return t('rdp.fullscreen')
  }
  if (props.config?.rdpFixedWidth && props.config?.rdpFixedHeight) {
    return `${props.config.rdpFixedWidth}×${props.config.rdpFixedHeight}`
  }
  return '800×600'
})

const CONNECT_TIMEOUT = 30_000 // 30 seconds

// --- Connection ---

let connectTimer: ReturnType<typeof setTimeout> | null = null

function clearConnectTimer() {
  if (connectTimer !== null) {
    clearTimeout(connectTimer)
    connectTimer = null
  }
}

async function connect() {
  if (!props.config) return
  status.value = 'connecting'
  errorMessage.value = ''

  // Start timeout timer
  clearConnectTimer()
  connectTimer = setTimeout(() => {
    if (status.value === 'connecting') {
      errorMessage.value = t('rdp.timeout')
      status.value = 'error'
      if (currentSessionId.value) {
        try { CloseSession(currentSessionId.value) } catch (_) {}
      }
    }
  }, CONNECT_TIMEOUT)

  try {
    const info = await CreateSession('rdp', props.config)
    currentSessionId.value = info.id
    panelStore.bindSession(props.panelId, info.id)
  } catch (e) {
    console.error('RDP connect error:', e)
    errorMessage.value = backendErrorText(e)
    status.value = 'error'
    clearConnectTimer()
  }
}

async function reconnect() {
  clearConnectTimer()
  if (currentSessionId.value) {
    try { await CloseSession(currentSessionId.value) } catch (_) {}
    currentSessionId.value = null
  }
  await connect()
}

// Enter the ActiveX control's built-in full screen. The control renders its
// own connection bar with a restore button to exit.
async function enterFullScreen() {
  if (!currentSessionId.value) return
  window.dispatchEvent(new CustomEvent('rdp:fullscreen-enter'))
  try { await RDPSetFullScreen(currentSessionId.value, true) } catch (e) { console.error('RDP fullscreen error:', e) }
}

// --- Events (lifecycle-scoped to avoid listener accumulation) ---

let unsubStatus: (() => void) | null = null
let unsubData: (() => void) | null = null

onMounted(() => {
  if (props.sessionId) {
    currentSessionId.value = props.sessionId
  }
  if (currentSessionId.value) {
    status.value = 'connected'
  } else {
    status.value = 'connecting'
  }

  unsubStatus =Events.On('session:status', (ev) => { const data: any = ev.data; 
    if (data.id !== currentSessionId.value) return
    switch (data.status) {
      case 'connected':
        clearConnectTimer()
        status.value = 'connected'
        errorMessage.value = ''
        window.dispatchEvent(new CustomEvent('rdp:sync-position'))
        break
      case 'disconnected':
        clearConnectTimer()
        if (status.value !== 'error') status.value = 'disconnected'
        if (currentSessionId.value) RDPHide(currentSessionId.value)
        break
      case 'error':
        clearConnectTimer()
        status.value = 'error'
        errorMessage.value = backendErrorTextOf(data.errorMessage || '')
        if (currentSessionId.value) RDPHide(currentSessionId.value)
        break
    }
   })

  unsubData =Events.On('session:data', (ev) => { const data: any = ev.data; 
    if (data.id === currentSessionId.value && data.data?.includes('[Connection failed')) {
      status.value = 'error'
    }
   })

  // Tab right-click 「重连」(Reconnect) menu → forced reconnect of this panel.
  window.addEventListener('panel:reconnect', onReconnectEvent)
})

function onReconnectEvent(e: Event) {
  const panelId = (e as CustomEvent)?.detail?.panelId
  if (panelId && panelId === props.panelId) reconnect()
}

onUnmounted(() => {
  unsubStatus?.()
  unsubData?.()
  window.removeEventListener('panel:reconnect', onReconnectEvent)
  clearConnectTimer()
})

watch(() => props.sessionId, (newId) => {
  if (newId && !currentSessionId.value) {
    currentSessionId.value = newId
  }
})
</script>

<style scoped>
.rdp-tab-content {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--bg-primary);
  position: relative;
}
.rdp-area {
  flex: 1;
}
.rdp-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-muted);
  z-index: 10;
}
.rdp-error-text { color: var(--error); }
.rdp-error-detail { color: var(--text-muted); font-size: 0.8125rem; max-width: 30rem; text-align: center; word-break: break-word; }
.rdp-statusbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: var(--bg-elevated);
  color: var(--text-muted);
  font-size: 0.75rem;
  flex-shrink: 0;
}
.rdp-status-dot {
  width: 0.5rem; height: 0.5rem;
  border-radius: 50%;
  background: var(--success);
}
.rdp-status-sep { color: var(--text-disabled); }
.rdp-status-spacer { flex: 1; }
.rdp-fullscreen-btn {
  border: 1px solid var(--border-default);
  background: transparent;
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 1px 0.625rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.rdp-fullscreen-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
</style>
