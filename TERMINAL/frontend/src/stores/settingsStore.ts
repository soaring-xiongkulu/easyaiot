import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { AppSettings, AIModelConfig, CustomTerminalTheme } from '../types/settings'
import { DEFAULT_SETTINGS, normalizeKeyBindings } from '../types/settings'
import { SaveSettings, LoadSettings, GetAvailableShells, SetDefaultSessionLogDir } from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import { setLocale } from '../i18n'
import { useAIConfigStore } from './aiConfigStore'

// Module-level un-subscriber for the cross-window store:settings:changed listener.
// Tracked at module scope so re-imports under HMR can detach the previous
// listener before re-subscribing (FE-03).
let unsubSettingsChanged: (() => void) | null = null
let unsubAiChanged: (() => void) | null = null

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({ ...DEFAULT_SETTINGS })
  const loaded = ref(false)
  const availableShells = ref<string[]>([])

  const theme = computed(() => settings.value.theme)
  const language = computed(() => settings.value.language)
  const terminal = computed(() => settings.value.terminal)
  const ai = computed(() => settings.value.ai)

  // Tracks the OS color-scheme preference so `resolvedAppTheme` stays reactive
  // to live system changes while the app theme is set to 'system'.
  const systemPrefersDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
  // The app theme collapsed to a concrete light/dark choice (never 'system').
  // Used by the terminal to resolve FOLLOW_APP_THEME.
  const resolvedAppTheme = computed<'dark' | 'light'>(() => {
    if (settings.value.theme === 'light') return 'light'
    if (settings.value.theme === 'system') return systemPrefersDark.value ? 'dark' : 'light'
    // 'dark' and 'deep-blue' are both dark.
    return 'dark'
  })

  const activeModel = computed(() =>
    settings.value.ai.models.find(m => m.id === settings.value.ai.activeModelId) || settings.value.ai.models[0]
  )

  // Current active category in the settings page (persisted across tab switches)
  const activeCategory = ref('basic')
  // For navigating to a specific settings category from other components
  const openCategory = ref<string | null>(null)

  // Tracks the last ai.json payload pushed from this store so unrelated
  // settings saves don't rewrite the AI config file needlessly.
  let lastSavedAiJson = ''

  // Overlay the syncable AI slice (ai.json) onto the settings blob and
  // validate the device-local activeModelId against the synced catalog.
  function recomposeAi() {
    const aiCfg = useAIConfigStore()
    const models = aiCfg.models.length ? aiCfg.models : settings.value.ai.models
    settings.value.ai = {
      maxTurns: aiCfg.maxTurns,
      models,
      activeModelId: models.some(m => m.id === settings.value.ai.activeModelId)
        ? settings.value.ai.activeModelId
        : (models[0]?.id ?? DEFAULT_SETTINGS.ai.activeModelId)
    }
  }

  function syncAiConfigFromSettings() {
    const aiJson = JSON.stringify({ maxTurns: settings.value.ai.maxTurns, models: settings.value.ai.models })
    if (aiJson === lastSavedAiJson) return
    lastSavedAiJson = aiJson
    const aiCfg = useAIConfigStore()
    aiCfg.maxTurns = settings.value.ai.maxTurns
    aiCfg.models = settings.value.ai.models
    aiCfg.save()
  }

  // Apply the UI font baseline to the rem root and cache it for the
  // pre-paint script in index.html (avoids a wrong-size flash on reload).
  function applyUiFontSize() {
    const px = (settings.value.uiFontSize / 12) * 16
    document.documentElement.style.fontSize = px + 'px'
    try {
      localStorage.setItem('uiFontSize', String(settings.value.uiFontSize))
    } catch {
      // private mode etc. — the loaded value still applies this session
    }
  }

  function applyTheme() {
    let theme = settings.value.theme
    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.dataset.theme = prefersDark ? 'dark' : 'light'
    } else {
      document.documentElement.dataset.theme = theme
    }
  }

  async function init() {
    try {
      const loadedSettings = await LoadSettings()
      if (loadedSettings) {
        settings.value = mergeSettings(loadedSettings)
      }
    } catch {
      // use defaults
    } finally {
      loaded.value = true
    }
    await useAIConfigStore().load()
    recomposeAi()
    lastSavedAiJson = JSON.stringify({ maxTurns: settings.value.ai.maxTurns, models: settings.value.ai.models })
    applyUiFontSize()
    try {
      availableShells.value = await GetAvailableShells()
    } catch {
      availableShells.value = []
    }
    // Push the persisted log directory override to the backend so
    // logs enabled before the user opens the settings tab already
    // respect it. Fire-and-forget; the backend has a safe empty fallback.
    SetDefaultSessionLogDir(settings.value.terminal.sessionLogDir || '').catch(() => {})
    applyTheme()
    setLocale(settings.value.language)
  }

  // Reload settings after the credential store is unlocked (e.g. after a
  // data-dir migration in master-password mode). Model apiKeys can only be
  // decrypted once the store is unlocked; re-running LoadSettings re-fetches
  // them instead of leaving the initial load's empty fallback in place.
  async function reload() {
    try {
      const loadedSettings = await LoadSettings()
      if (loadedSettings) {
        settings.value = mergeSettings(loadedSettings)
        loaded.value = true
      }
    } catch {
      // use defaults
    }
    await useAIConfigStore().load()
    recomposeAi()
    applyUiFontSize()
    applyTheme()
    setLocale(settings.value.language)
  }

  async function save() {
    try {
      await SaveSettings(settings.value)
      // Mirror the syncable AI slice into ai.json (skipped when unchanged).
      syncAiConfigFromSettings()
      // Keep the backend override in sync on every save. Cheap and
      // avoids the need for a dedicated watcher on this single field.
      SetDefaultSessionLogDir(settings.value.terminal.sessionLogDir || '').catch(() => {})
    } catch {
      // ignore save errors
    }
  }

  function updateTheme(value: AppSettings['theme']) {
    settings.value.theme = value
    save()
  }

  function addCustomTheme(theme: CustomTerminalTheme) {
    settings.value.customTerminalThemes.push(theme)
    save()
  }

  function updateCustomTheme(id: string, updates: Partial<CustomTerminalTheme>) {
    const idx = settings.value.customTerminalThemes.findIndex(t => t.id === id)
    if (idx >= 0) {
      settings.value.customTerminalThemes[idx] = { ...settings.value.customTerminalThemes[idx], ...updates }
      save()
    }
  }

  function removeCustomTheme(id: string) {
    const idx = settings.value.customTerminalThemes.findIndex(t => t.id === id)
    if (idx >= 0) {
      settings.value.customTerminalThemes.splice(idx, 1)
      save()
    }
  }

  function updateLanguage(value: AppSettings['language']) {
    settings.value.language = value
    setLocale(value)
    save()
  }

  function updateTerminal(updates: Partial<AppSettings['terminal']>) {
    settings.value.terminal = { ...settings.value.terminal, ...updates }
    save()
  }

  function addModel(model: AIModelConfig) {
    settings.value.ai.models.push(model)
    save()
  }

  function updateModel(id: string, updates: Partial<AIModelConfig>) {
    const idx = settings.value.ai.models.findIndex(m => m.id === id)
    if (idx >= 0) {
      settings.value.ai.models[idx] = { ...settings.value.ai.models[idx], ...updates }
      save()
    }
  }

  function removeModel(id: string) {
    const idx = settings.value.ai.models.findIndex(m => m.id === id)
    if (idx >= 0) {
      settings.value.ai.models.splice(idx, 1)
      if (settings.value.ai.activeModelId === id && settings.value.ai.models.length > 0) {
        settings.value.ai.activeModelId = settings.value.ai.models[0].id
      }
      save()
    }
  }

  function setActiveModel(id: string) {
    settings.value.ai.activeModelId = id
    save()
  }

  const sftpBookmarks = computed(() => settings.value.sftpBookmarks)

  // Writable computed so components can toggle visibility directly; every
  // write is persisted with the settings blob. The transfer panel auto-pops
  // on new tasks regardless of this flag — it only remembers the last
  // visibility across restarts.
  const sftpTransferPanelVisible = computed<boolean>({
    get: () => settings.value.sftpTransferPanelVisible,
    set: (v: boolean) => {
      settings.value.sftpTransferPanelVisible = v
      save()
    }
  })

  function addSftpBookmark(mode: 'local' | 'remote', path: string) {
    const key = mode === 'local' ? 'localPaths' : 'remotePaths'
    const paths = settings.value.sftpBookmarks[key]
    if (!paths.includes(path)) {
      if (paths.length >= 50) {
        paths.shift()
      }
      paths.push(path)
      save()
    }
  }

  function removeSftpBookmark(mode: 'local' | 'remote', path: string) {
    const key = mode === 'local' ? 'localPaths' : 'remotePaths'
    const paths = settings.value.sftpBookmarks[key]
    const idx = paths.indexOf(path)
    if (idx >= 0) {
      paths.splice(idx, 1)
      save()
    }
  }

  // Auto-save when AI models change
  watch(() => settings.value.ai, save, { deep: true })

  // Apply theme when it changes
  watch(() => settings.value.theme, applyTheme)

  // Apply the UI font baseline as soon as it changes (no restart needed)
  watch(() => settings.value.uiFontSize, applyUiFontSize)

  // Listen for system color scheme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    systemPrefersDark.value = e.matches
    if (settings.value.theme === 'system') {
      applyTheme()
    }
  })

  // Listen for settings changes from sync
  unsubSettingsChanged?.()
  unsubSettingsChanged =Events.On('store:settings:changed', (ev) => { const data: AppSettings = ev.data; 
    if (data) {
      settings.value = mergeSettings(data)
      loaded.value = true
      applyUiFontSize()
      applyTheme()
    }
  })

  // AI config changed via a sync pull — refresh the local composition.
  unsubAiChanged?.()
  unsubAiChanged = Events.On('store:ai:changed', (ev) => {
    const data = ev.data as { maxTurns?: number; models?: AIModelConfig[] } | null
    if (data) {
      const aiCfg = useAIConfigStore()
      aiCfg.maxTurns = data.maxTurns ?? DEFAULT_SETTINGS.ai.maxTurns
      aiCfg.models = data.models?.length ? data.models : aiCfg.models
      recomposeAi()
      lastSavedAiJson = JSON.stringify({ maxTurns: settings.value.ai.maxTurns, models: settings.value.ai.models })
    }
  })

  function dispose() {
    unsubSettingsChanged?.()
    unsubSettingsChanged = null
    unsubAiChanged?.()
    unsubAiChanged = null
  }

  return {
    settings,
    loaded,
    availableShells,
    theme,
    resolvedAppTheme,
    language,
    terminal,
    ai,
    activeModel,
    activeCategory,
    openCategory,
    init,
    reload,
    save,
    applyTheme,
    updateTheme,
    updateLanguage,
    updateTerminal,
    addModel,
    updateModel,
    removeModel,
    setActiveModel,
    sftpBookmarks,
    sftpTransferPanelVisible,
    addSftpBookmark,
    removeSftpBookmark,
    addCustomTheme,
    updateCustomTheme,
    removeCustomTheme,
    dispose
  }
})

function mergeSettings(loaded: AppSettings): AppSettings {
  return {
    theme: loaded.theme || DEFAULT_SETTINGS.theme,
    language: loaded.language || DEFAULT_SETTINGS.language,
    uiFontSize: loaded.uiFontSize ?? DEFAULT_SETTINGS.uiFontSize,
    terminal: {
      ...DEFAULT_SETTINGS.terminal,
      ...loaded.terminal,
      theme: (loaded.terminal?.theme as string) === 'dark' || (loaded.terminal?.theme as string) === 'light'
        ? DEFAULT_SETTINGS.terminal.theme
        : loaded.terminal?.theme || DEFAULT_SETTINGS.terminal.theme
    },
    ai: {
      maxTurns: loaded.ai?.maxTurns ?? DEFAULT_SETTINGS.ai.maxTurns,
      models: loaded.ai?.models?.length ? loaded.ai.models : DEFAULT_SETTINGS.ai.models,
      activeModelId: loaded.ai?.activeModelId || DEFAULT_SETTINGS.ai.activeModelId
    },
    keyboard: normalizeKeyBindings(loaded.keyboard || {}),
    closeTabPrompt: loaded.closeTabPrompt ?? DEFAULT_SETTINGS.closeTabPrompt,
    closeAppPrompt: loaded.closeAppPrompt ?? DEFAULT_SETTINGS.closeAppPrompt,
    sftpBookmarks: {
      localPaths: loaded.sftpBookmarks?.localPaths || [],
      remotePaths: loaded.sftpBookmarks?.remotePaths || []
    },
    sftpTransferPanelVisible: loaded.sftpTransferPanelVisible ?? DEFAULT_SETTINGS.sftpTransferPanelVisible,
    customTerminalThemes: loaded.customTerminalThemes || [],
    defaultLocalShell: loaded.defaultLocalShell ?? DEFAULT_SETTINGS.defaultLocalShell,
    tabCloseButton: loaded.tabCloseButton || DEFAULT_SETTINGS.tabCloseButton,
    showTabShortcutHints: loaded.showTabShortcutHints ?? DEFAULT_SETTINGS.showTabShortcutHints,
    hostListMenuStyle: loaded.hostListMenuStyle || DEFAULT_SETTINGS.hostListMenuStyle,
    // Per-key merge so a settings.json written before a view existed (or
    // with a key dropped) still gets the default for that view.
    sidebarTabs: {
      ...DEFAULT_SETTINGS.sidebarTabs,
      ...(loaded.sidebarTabs || {})
    }
  }
}
