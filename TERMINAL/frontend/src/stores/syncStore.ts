import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useI18n } from '../i18n'
import {
  SyncGetConfig,
  SyncSaveConfig,
  SyncNow,
  SyncResolveConflict,
  SyncTestConnection,
  SyncConfigureRepo,
  SyncChangePassword,
  SyncDeleteRepo,
} from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import { SyncConfig } from '../../bindings/easyaiot/terminal/backend/sync/models'
import { backendErrorText } from '../utils/backendError'
// Module-level un-subscribers for sync:conflict / sync:completed listeners.
// Tracked at module scope so re-imports under HMR can detach the previous
// listener before re-subscribing (FE-03).
let unsubSyncConflict: (() => void) | null = null
let unsubSyncCompleted: (() => void) | null = null

export interface SyncConfig {
  repoUrl: string
  branch: string
  username: string
  autoSync: boolean
  lastSyncAt: string
  lastSyncStatus: string
  lastSyncError: string
}

export interface SyncResult {
  direction: number // 0=none, 1=push, 2=pull, 3=conflict
  message: string
  conflict?: SyncConflict
}

export interface SyncConflict {
  localTime: string
  remoteTime: string
}

export const useSyncStore = defineStore('sync', () => {
  const { t } = useI18n()
  const config = ref<SyncConfig>({
    repoUrl: '',
    branch: 'main',
    username: '',
    autoSync: false,
    lastSyncAt: '',
    lastSyncStatus: '',
    lastSyncError: '',
  })
  const syncing = ref(false)
  const testingConnection = ref(false)
  const conflict = ref<SyncConflict | null>(null)
  const lastResult = ref('')

  // Dialog visibility
  const showAddRepo = ref(false)
  const showEditRepo = ref(false)
  const showChangePassword = ref(false)
  const showDeleteRepo = ref(false)

  async function loadConfig() {
    try {
      const cfg = await SyncGetConfig()
      config.value = {
        repoUrl: cfg.repoUrl || '',
        branch: cfg.branch || 'main',
        username: cfg.username || '',
        autoSync: cfg.autoSync || false,
        lastSyncAt: cfg.lastSyncAt || '',
        lastSyncStatus: cfg.lastSyncStatus || '',
        lastSyncError: cfg.lastSyncError || '',
      }
    } catch (e) {
      console.error('Load sync config failed:', e)
    }
  }

  async function saveConfig(token: string = '') {
    try {
      const cfg = new SyncConfig()
      cfg.repoUrl = config.value.repoUrl
      cfg.branch = config.value.branch
      cfg.username = config.value.username
      cfg.autoSync = config.value.autoSync
      cfg.lastSyncAt = config.value.lastSyncAt
      cfg.lastSyncStatus = config.value.lastSyncStatus
      cfg.lastSyncError = config.value.lastSyncError
      await SyncSaveConfig(cfg, token)
      await loadConfig()
    } catch (e) {
      console.error('Save sync config failed:', e)
      throw e
    }
  }

  async function doSync(): Promise<SyncResult | null> {
    syncing.value = true
    try {
      const result = await SyncNow()
      const direction = result.direction ?? (result as any).Direction ?? 0
      if (direction === 3) {
        conflict.value = result.conflict
          ? { localTime: result.conflict.localTime ?? (result.conflict as any).LocalTime ?? '',
              remoteTime: result.conflict.remoteTime ?? (result.conflict as any).RemoteTime ?? '' }
          : (result as any).Conflict
            ? { localTime: (result as any).Conflict.LocalTime ?? '', remoteTime: (result as any).Conflict.RemoteTime ?? '' }
            : null
      } else {
        conflict.value = null
      }
      lastResult.value = result.message ?? (result as any).Message ?? ''
      await loadConfig()
      return {
        direction,
        message: result.message ?? (result as any).Message ?? '',
        conflict: conflict.value ?? undefined,
      }
    } catch (e: any) {
      lastResult.value = backendErrorText(e)
      await loadConfig()
      return null
    } finally {
      syncing.value = false
    }
  }

  async function resolveConflict(useLocal: boolean): Promise<SyncResult | null> {
    syncing.value = true
    try {
      const result = await SyncResolveConflict(useLocal)
      conflict.value = null
      lastResult.value = result.message ?? (result as any).Message ?? ''
      await loadConfig()
      return {
        direction: result.direction ?? (result as any).Direction ?? 0,
        message: result.message ?? (result as any).Message ?? '',
      }
    } catch (e: any) {
      lastResult.value = backendErrorText(e)
      return null
    } finally {
      syncing.value = false
    }
  }

  async function testConnection(): Promise<string | null> {
    testingConnection.value = true
    try {
      await SyncTestConnection()
      return null
    } catch (e: any) {
      return backendErrorText(e)
    } finally {
      testingConnection.value = false
    }
  }

  async function configureRepo(repoUrl: string, username: string, token: string, masterPassword: string): Promise<SyncResult | null> {
    syncing.value = true
    try {
      const result = await SyncConfigureRepo(repoUrl, username, token, masterPassword)
      await loadConfig()
      const direction = result.direction ?? (result as any).Direction ?? 0
      if (direction === 3) {
        conflict.value = result.conflict
          ? { localTime: result.conflict.localTime ?? (result.conflict as any).LocalTime ?? '',
              remoteTime: result.conflict.remoteTime ?? (result.conflict as any).RemoteTime ?? '' }
          : (result as any).Conflict
            ? { localTime: (result as any).Conflict.LocalTime ?? '', remoteTime: (result as any).Conflict.RemoteTime ?? '' }
            : { localTime: '', remoteTime: '' }
      }
      return {
        direction,
        message: result.message ?? (result as any).Message ?? '',
      }
    } catch (e: any) {
      throw e
    } finally {
      syncing.value = false
    }
  }

  async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
    try {
      await SyncChangePassword(oldPassword, newPassword)
    } catch (e: any) {
      throw e
    }
  }

  async function deleteRepo(): Promise<void> {
    try {
      await SyncDeleteRepo()
      await loadConfig()
    } catch (e: any) {
      throw e
    }
  }

  function formatSyncTime(): string {
    if (!config.value.lastSyncAt) return t('sync.neverSynced')
    try {
      const d = new Date(config.value.lastSyncAt)
      return d.toLocaleString()
    } catch {
      return config.value.lastSyncAt
    }
  }

  // Listen for conflict events from auto-sync
  unsubSyncConflict?.()
  unsubSyncConflict =Events.On('sync:conflict', (ev) => { const data: SyncConflict = ev.data; 
    conflict.value = {
      localTime: data.localTime ?? (data as any).LocalTime ?? '',
      remoteTime: data.remoteTime ?? (data as any).RemoteTime ?? '',
    }
   })

  // Reload config when auto-sync completes
  unsubSyncCompleted?.()
  unsubSyncCompleted =Events.On('sync:completed', () => {
    loadConfig()
  })

  function dispose() {
    unsubSyncConflict?.()
    unsubSyncConflict = null
    unsubSyncCompleted?.()
    unsubSyncCompleted = null
  }

  return {
    config,
    syncing,
    testingConnection,
    conflict,
    lastResult,
    showAddRepo,
    showEditRepo,
    showChangePassword,
    showDeleteRepo,
    loadConfig,
    saveConfig,
    doSync,
    resolveConflict,
    testConnection,
    configureRepo,
    changePassword,
    deleteRepo,
    formatSyncTime,
    dispose
  }
})
