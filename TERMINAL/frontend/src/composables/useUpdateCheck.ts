import { reactive, ref, watch, h } from 'vue'
import { ElMessage } from 'element-plus'
import { msg } from '../services/message'
import { CheckForUpdate, GetAppInfo, DownloadUpdate, ApplyUpdate } from '../../bindings/easyaiot/terminal/app'
import { useI18n, locale } from '../i18n'
import { useSettingsStore } from '../stores/settingsStore'
import { isMobilePlatform } from '../utils/platform'
import { Events } from '@wailsio/runtime'
import type { UpdateInfo } from '../types/settings'

const CHECK_TIMEOUT = 15000

const updateInfo = ref<UpdateInfo | null>(null)
const checking = ref(false)
const autoCheck = ref(true)
// Update source preference: "auto" resolves from the UI language, or is
// pinned to "github" / "gitee" by the user (settings.updateSource).
const source = ref<'auto' | 'github' | 'gitee'>('auto')

// --- update install flow state ---------------------------------------------
type UpdatePhase = 'idle' | 'downloading' | 'verifying' | 'applying' | 'restarting' | 'error'
const updateDialogVisible = ref(false)
const updatePhase = ref<UpdatePhase>('idle')
const downloadProgress = ref({ received: 0, total: -1, percent: 0 })
const updateError = ref('')

let unsubProgress: (() => void) | null = null

// bindProgressEvents subscribes to backend update:progress events once and
// drives the dialog state machine.
function bindProgressEvents() {
  if (unsubProgress) return
  unsubProgress = Events.On('update:progress', (ev) => {
    const p: any = ev.data
    if (!p) return
    switch (p.phase) {
      case 'downloading':
        updatePhase.value = 'downloading'
        downloadProgress.value = {
          received: Number(p.received ?? 0),
          total: Number(p.total ?? -1),
          percent: Math.max(0, Math.min(100, Math.round(p.percent ?? 0))),
        }
        break
      case 'verifying':
        updatePhase.value = 'verifying'
        break
      case 'applying':
        updatePhase.value = 'applying'
        break
      case 'error':
        updatePhase.value = 'error'
        updateError.value = p.message || ''
        break
    }
  })
}

// startUpdate downloads the staged update and applies it. On success the
// backend relaunches the app (or quits for the installer channel), so the
// last state the user sees is "restarting".
async function startUpdate() {
  const info = updateInfo.value
  if (!info || info.assets.length === 0) {
    updateError.value = 'no assets'
    updatePhase.value = 'error'
    return
  }
  updateError.value = ''
  updatePhase.value = 'downloading'
  bindProgressEvents()
  try {
    await DownloadUpdate(info.assets as any)
    updatePhase.value = 'applying'
    await ApplyUpdate()
    updatePhase.value = 'restarting'
  } catch (e) {
    updatePhase.value = 'error'
    updateError.value = String(e)
  }
}

function openUpdateDialog() {
  updatePhase.value = 'idle'
  updateError.value = ''
  updateDialogVisible.value = true
}

function closeUpdateDialog() {
  if (updatePhase.value === 'applying' || updatePhase.value === 'restarting') {
    return
  }
  updateDialogVisible.value = false
  updatePhase.value = 'idle'
}

function showUpdateNotification(info: UpdateInfo) {
  const { t } = useI18n()
  const canInstall = info.assets.length > 0
  const linkStyle = { color: 'inherit', textDecoration: 'underline', cursor: 'pointer' }
  ElMessage({
    message: h('div', null, [
      h('span', null, `${t('settings.foundNewVersion')}: ${info.latest}`),
      canInstall ? h('span', null, ' · ') : null,
      canInstall ? h('a', {
        href: '#',
        style: linkStyle,
        onClick: (e: Event) => {
          e.preventDefault()
          openUpdateDialog()
        },
      }, t('settings.updateInstall')) : null,
    ]),
    type: 'success',
    duration: 0,
    showClose: true,
    offset: 50,
  })
}

let timer: ReturnType<typeof setInterval> | null = null
let initialCheckTimer: ReturnType<typeof setTimeout> | null = null
let settingsWatchStop: (() => void) | null = null

function resolveSource(): 'github' | 'gitee' {
  if (source.value === 'github' || source.value === 'gitee') {
    return source.value
  }
  return locale.value === 'zh-CN' ? 'gitee' : 'github'
}

// setSource persists the preference and immediately re-checks with the new
// source so the user sees feedback right away.
function setSource(v: 'auto' | 'github' | 'gitee') {
  source.value = v
  try {
    const settings = useSettingsStore()
    settings.settings.updateSource = v
    settings.save()
  } catch { /* store may not be ready yet */ }
  checkForUpdate()
}

function startTimer() {
  if (timer !== null) {
    clearInterval(timer)
  }
  timer = setInterval(() => {
    checkForUpdate()
  }, 24 * 60 * 60 * 1000)
}

function stopTimer() {
  if (initialCheckTimer !== null) {
    clearTimeout(initialCheckTimer)
    initialCheckTimer = null
  }
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

async function checkForUpdate(showStatus = false): Promise<UpdateInfo | null> {
  checking.value = true
  const updateSource = resolveSource()
  try {
    const info = await Promise.race([
      CheckForUpdate(updateSource),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), CHECK_TIMEOUT)
      ),
    ])
    updateInfo.value = info
    if (info.hasUpdate) {
      showUpdateNotification(info)
    } else if (showStatus) {
      const { t } = useI18n()
      msg.success(t('settings.upToDate'))
    }
    return info
  } catch {
    if (showStatus) {
      const { t } = useI18n()
      msg.error(t('settings.checkUpdateFailed'))
    }
    return null
  } finally {
    checking.value = false
  }
}

// Persist changes made through the UI. Store-driven updates already contain
// the same value and must not be written back.
watch(autoCheck, (enabled) => {
  const settings = useSettingsStore()
  if (settings.settings.autoCheckUpdate === enabled) return
  settings.settings.autoCheckUpdate = enabled
  settings.save()
})

function initAutoCheck() {
  checking.value = false
  stopTimer()
  settingsWatchStop?.()
  settingsWatchStop = null

  // Fetch current version immediately so About page shows it
  GetAppInfo().then(info => {
    if (!updateInfo.value) {
      updateInfo.value = { hasUpdate: false, current: info.version, latest: '', releaseUrl: '', changelog: '', assets: [] }
    }
  }).catch(() => {})
  // Mobile updates by installing a new APK; the in-app update check would
  // only fetch desktop assets. Skip auto-check scheduling entirely.
  if (isMobilePlatform()) return
  // Wait for persisted settings before scheduling network requests. Reading
  // the temporary default here would ignore a stored `false`.
  const settings = useSettingsStore()
  let initialized = false
  settingsWatchStop = watch(
    [() => settings.loaded, () => settings.settings.autoCheckUpdate],
    ([loaded, persisted]) => {
      if (!loaded) return
      const enabled = persisted ?? true
      autoCheck.value = enabled
      const s = settings.settings.updateSource
      source.value = (s === 'github' || s === 'gitee' || s === 'auto') ? s : 'auto'
      if (enabled) {
        if (!initialized) {
          initialCheckTimer = setTimeout(() => {
            initialCheckTimer = null
            checkForUpdate()
          }, 5000)
        }
        startTimer()
      } else {
        stopTimer()
      }
      initialized = true
    },
    { immediate: true },
  )
}

const state = reactive({
  updateInfo,
  checking,
  autoCheck,
  source,
  checkForUpdate,
  setSource,
  initAutoCheck,
  dispose,
  // update dialog flow
  updateDialogVisible,
  updatePhase,
  downloadProgress,
  updateError,
  startUpdate,
  openUpdateDialog,
  closeUpdateDialog,
})

function dispose() {
  stopTimer()
  settingsWatchStop?.()
  settingsWatchStop = null
  if (unsubProgress) {
    unsubProgress()
    unsubProgress = null
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', dispose)
}

export function useUpdateCheck() {
  return state
}
