import { computed } from 'vue'
import { useSettingsStore } from '../stores/settingsStore'
import { TERMINAL_THEMES } from '../types/settings'
import type { TerminalThemeEntry } from '../types/settings'

const DARK_THEMES = TERMINAL_THEMES.filter(t => t.type === 'dark')
const LIGHT_THEMES = TERMINAL_THEMES.filter(t => t.type === 'light')

/** Grouped terminal theme options for the theme <el-select>: built-in themes
 * split into Dark/Light, SSH client defaults, plus a Custom group for
 * user-defined themes (only shown when at least one exists). Shared by
 * Sidebar.vue's personalization panel and SettingsTab.vue. */
export function useTerminalThemeOptions() {
  const settingsStore = useSettingsStore()

  const customThemeEntries = computed<TerminalThemeEntry[]>(() =>
    settingsStore.settings.customTerminalThemes.map(t => ({
      label: t.name,
      value: t.id,
      type: t.type
    }))
  )

  const terminalThemeGroups = computed(() => {
    const groups = [
      { label: 'Dark', options: DARK_THEMES },
      { label: 'Light', options: LIGHT_THEMES },
    ]
    if (customThemeEntries.value.length > 0) {
      groups.push({ label: 'Custom', options: customThemeEntries.value })
    }
    return groups
  })

  function isCustomTheme(id: string): boolean {
    return settingsStore.settings.customTerminalThemes.some(t => t.id === id)
  }

  return { terminalThemeGroups, customThemeEntries, isCustomTheme }
}
