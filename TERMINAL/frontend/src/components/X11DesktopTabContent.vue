<template>
  <div class="x11-desktop-tab-content">
    <!-- Connecting state -->
    <div v-if="status === 'connecting'" class="x11-overlay">
      <el-icon class="is-loading" :size="'2rem'"><Loader /></el-icon>
      <p>{{ t('x11.tab.connecting') }}</p>
    </div>

    <!-- Connected state -->
    <div v-else-if="status === 'connected'" class="x11-info">
      <div class="x11-rows">
        <div class="x11-row">
          <span class="x11-row-label">{{ t('conn.host') }}</span>
          <span>{{ hostDisplay }}</span>
        </div>
        <div class="x11-row">
          <span class="x11-row-label">{{ t('x11.tab.desktopEnv') }}</span>
          <span>{{ desktopEnvDisplay }}</span>
        </div>
        <div class="x11-row">
          <span class="x11-row-label">X Server</span>
          <span>{{ localXServerName }}</span>
        </div>
      </div>
      <p class="x11-hint">{{ t('x11.tab.localXHint') }}</p>
      <div class="x11-actions">
        <el-button type="primary" @click="disconnect">{{ t('x11.tab.disconnect') }}</el-button>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="status === 'error'" class="x11-overlay">
      <p class="x11-error-text">{{ t('x11.tab.error') }}</p>
      <p v-if="lastError" class="x11-error-detail">{{ lastError }}</p>
      <el-button type="primary" @click="reconnect">{{ t('x11.tab.retry') }}</el-button>
    </div>

    <!-- Disconnected state -->
    <div v-else class="x11-overlay">
      <p>{{ t('x11.tab.disconnected') }}</p>
      <el-button type="primary" @click="reconnect">{{ t('x11.tab.reconnect') }}</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Loader } from '@lucide/vue'
import { useI18n } from '../i18n'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import type { ConnectionConfig } from '../types/session'
import { Events } from '@wailsio/runtime'
import { CreateSession, CloseSession, GetPlatform, X11DesktopConnect } from '../../bindings/easyaiot/terminal/app'
import { backendErrorText, backendErrorTextOf } from '../utils/backendError'
const { t } = useI18n()
const panelStore = usePanelStore()
const sessionStore = useSessionStore()
const props = defineProps<{
  panelId: string
  config: ConnectionConfig | null
  sessionId: string | null
}>()

const status = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting')
const lastError = ref<string>('')
const currentSessionId = ref<string | null>(props.sessionId)
const platform = ref<string>('')

const localXServerName = computed(() => {
  const p = platform.value
  if (p === 'darwin') return 'XQuartz'
  if (p === 'linux') return 'Xorg'
  if (p === 'windows') return 'VcXsrv'
  return t('x11.tab.localXServerUnknown')
})

const hostDisplay = computed(() => {
  if (!props.config) return ''
  const host = props.config.host || ''
  const port = props.config.port
  return port ? `${host}:${port}` : host
})

const desktopEnvDisplay = computed(() => {
  if (!props.config) return ''
  const de = props.config.x11DesktopDesktopType
  if (!de) return ''
  if (de === 'custom') {
    return props.config.x11DesktopCustomCmd || t('conn.x11DesktopDECustom')
  }
  return de.charAt(0).toUpperCase() + de.slice(1)
})

let unsubStatus: (() => void) | null = null

async function start() {
  if (!props.config) return
  status.value = 'connecting'
  lastError.value = ''
  try {
    platform.value = await GetPlatform()
  } catch (e) {
    console.warn('X11 desktop: GetPlatform failed', e)
  }
  try {
    const info = await CreateSession('x11-desktop', { ...props.config })
    currentSessionId.value = info.id
    panelStore.bindSession(props.panelId, info.id)
    sessionStore.initSession(info.id)
    await X11DesktopConnect(props.config.id, info.id)
    status.value = 'connected'
  } catch (e: any) {
    console.error('X11 desktop connect error:', e)
    lastError.value = backendErrorText(e)
    status.value = 'error'
  }
}

async function disconnect() {
  if (currentSessionId.value) {
    try { await CloseSession(currentSessionId.value) } catch (_) {}
    panelStore.bindSession(props.panelId, '')
    currentSessionId.value = null
  }
}

async function reconnect() {
  if (currentSessionId.value) {
    try { await CloseSession(currentSessionId.value) } catch (_) {}
    panelStore.bindSession(props.panelId, '')
    currentSessionId.value = null
  }
  await start()
}

function onReconnectEvent(e: Event) {
  const panelId = (e as CustomEvent)?.detail?.panelId
  if (panelId && panelId === props.panelId) reconnect()
}

onMounted(() => {
  if (props.sessionId) {
    currentSessionId.value = props.sessionId
    status.value = 'connecting'
  }
  start()

  unsubStatus =Events.On('session:status', (ev) => { const data: any = ev.data; 
    if (data.id !== currentSessionId.value) return
    switch (data.status) {
      case 'connected':
        status.value = 'connected'
        lastError.value = ''
        break
      case 'disconnected':
        if (status.value !== 'error') status.value = 'disconnected'
        break
      case 'error':
        if (!lastError.value) lastError.value = backendErrorTextOf(data.errorMessage || '')
        status.value = 'error'
        break
    }
   })

  // Tab right-click 「重连」(Reconnect) menu → forced reconnect of this panel.
  window.addEventListener('panel:reconnect', onReconnectEvent)
})

onBeforeUnmount(() => {
  unsubStatus?.()
  window.removeEventListener('panel:reconnect', onReconnectEvent)
  if (currentSessionId.value) {
    try { CloseSession(currentSessionId.value) } catch (_) {}
    panelStore.bindSession(props.panelId, '')
    currentSessionId.value = null
  }
})
</script>

<style scoped>
.x11-desktop-tab-content {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-base);
  display: flex;
  flex-direction: column;
}
.x11-overlay {
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
.x11-info {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1.5rem;
  z-index: 10;
}
.x11-rows {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 35rem;
  width: 100%;
  background: var(--bg-elevated);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md, 0.375rem);
  padding: 1rem 1.25rem;
  color: var(--text-primary);
}
.x11-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
}
.x11-row-label {
  color: var(--text-muted);
  min-width: 7.5rem;
}
.x11-cmd {
  font-family: var(--font-mono, monospace);
  background: var(--bg-base);
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius-sm, 0.25rem);
  color: var(--text-primary);
  word-break: break-all;
}
.x11-hint {
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1.5;
  margin-top: 0.5rem;
}
.x11-actions {
  display: flex;
  gap: 0.5rem;
}
.x11-status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--success);
  flex-shrink: 0;
}
.x11-error-text { color: var(--error); }
.x11-error-detail {
  color: var(--text-muted);
  font-size: 0.75rem;
  max-width: 80%;
  text-align: center;
  word-break: break-word;
}
</style>
