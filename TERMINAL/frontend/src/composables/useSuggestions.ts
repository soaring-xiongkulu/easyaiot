import { ref } from 'vue'
import { SaveTerminalHistory, LoadTerminalHistory } from '../../bindings/easyaiot/terminal/app'
import { useQuickCommandStore } from '../stores/quickCommandStore'
import { useI18n } from '../i18n'

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

export interface HistoryEntry {
  id: string
  command: string
}

export interface SuggestionItem {
  type: 'history' | 'quick-command'
  label: string
  value: string
  icon?: string
  description?: string
  matchIndices?: number[]
  commandMatchIndices?: number[]  // For quick-command items when match is on command text
  id?: string  // For history items only
}

export interface SuggestionsState {
  visible: boolean
  items: SuggestionItem[]
  selectedIndex: number
  loading: boolean
}

const MAX_HISTORY = 500
const MAX_COMMAND_LENGTH = 200

const historyCache = new Map<string, HistoryEntry>() // key = command
let historyLoaded = false
const historyEntries = ref<HistoryEntry[]>([])

function syncHistoryEntries() {
  // Reverse: newest first
  historyEntries.value = Array.from(historyCache.values()).reverse()
}

export function useSuggestions() {
  const { t } = useI18n()
  const state = ref<SuggestionsState>({
    visible: false,
    items: [],
    selectedIndex: -1,
    loading: false,
  })

  // If user presses Escape, suppress suggestions until next command (Enter)
  let suppressedUntilNextCommand = false

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let saveDebounceTimer: ReturnType<typeof setTimeout> | null = null

  async function loadHistory(): Promise<HistoryEntry[]> {
    if (historyLoaded) {
      syncHistoryEntries()
      return historyEntries.value
    }
    try {
      const entries = await LoadTerminalHistory()
      entries.forEach((entry: HistoryEntry) => historyCache.set(entry.command, entry))
      historyLoaded = true
      syncHistoryEntries()
      return historyEntries.value
    } catch {
      return []
    }
  }

  async function saveHistory(entries: HistoryEntry[]) {
    try {
      await SaveTerminalHistory(entries)
    } catch (e) {
      console.error('Failed to save terminal history:', e)
    }
  }

  function shouldSkipCommand(command: string): boolean {
    const trimmed = command.trim()
    if (!trimmed) return true
    if (trimmed.length > MAX_COMMAND_LENGTH) return true
    if (trimmed.length <= 1) return true
    // Shell comments (e.g. "# apt update")
    if (trimmed.startsWith('#')) return true
    // Session control commands
    if (/^(exit|logout|clear)$/i.test(trimmed)) return true
    // System control / dangerous commands
    if (/^\s*(reboot|shutdown|halt|poweroff)(\s+.*)?$/i.test(trimmed)) return true
    if (/^\s*init\s+(0|6)\b/i.test(trimmed)) return true
    // History viewing commands
    if (/^history(\s+.*)?$/i.test(trimmed)) return true
    // Commands with potential sensitive info (passwords, tokens, secrets, keys)
    if (/\b(password|passwd|token|api[_-]?key|secret|private[_-]?key)\s*[=:]\s*\S+/i.test(trimmed)) return true
    if (/\b(-p|--password)\s+\S+/i.test(trimmed)) return true
    if (/Authorization:\s*Bearer\s+\S+/i.test(trimmed)) return true
    return false
  }

  function addHistoryCommand(command: string) {
    if (shouldSkipCommand(command)) return
    if (historyCache.has(command)) {
      historyCache.delete(command)
    }
    historyCache.set(command, { id: generateUUID(), command })
    syncHistoryEntries()
    if (historyCache.size > MAX_HISTORY) {
      const firstKey = historyCache.keys().next().value
      if (firstKey !== undefined) {
        historyCache.delete(firstKey)
        syncHistoryEntries()
      }
    }
    // Debounce save to avoid blocking on every Enter (Go does JSON marshal + file write)
    if (saveDebounceTimer) {
      clearTimeout(saveDebounceTimer)
    }
    saveDebounceTimer = setTimeout(() => {
      saveDebounceTimer = null
      saveHistory(Array.from(historyCache.values()))
    }, 500)
  }

  function removeHistoryCommandById(id: string) {
    let commandToDelete: string | undefined
    for (const [cmd, entry] of historyCache) {
      if (entry.id === id) {
        commandToDelete = cmd
        break
      }
    }
    if (commandToDelete === undefined) return
    historyCache.delete(commandToDelete)
    syncHistoryEntries()
    // Also remove from current visible items if present
    state.value.items = state.value.items.filter(item => {
      if (item.type !== 'history') return true
      return historyCache.has(item.value)
    })
    // Adjust selectedIndex if needed
    if (state.value.selectedIndex >= state.value.items.length) {
      state.value.selectedIndex = state.value.items.length - 1
    }
    // Close popup if no history items left
    if (state.value.items.every(item => item.type !== 'history')) {
      state.value.visible = false
    }
    // Share the same debounce timer with addHistoryCommand to avoid race
    if (saveDebounceTimer) {
      clearTimeout(saveDebounceTimer)
    }
    saveDebounceTimer = setTimeout(() => {
      saveDebounceTimer = null
      saveHistory(Array.from(historyCache.values()))
    }, 500)
  }

  function removeHistoryCommandsById(ids: string[]) {
    const idSet = new Set(ids)
    for (const [cmd, entry] of historyCache) {
      if (idSet.has(entry.id)) {
        historyCache.delete(cmd)
      }
    }
    syncHistoryEntries()
    // Also remove from current visible items if present
    state.value.items = state.value.items.filter(item => {
      if (item.type !== 'history') return true
      return historyCache.has(item.value)
    })
    // Adjust selectedIndex if needed
    if (state.value.selectedIndex >= state.value.items.length) {
      state.value.selectedIndex = state.value.items.length - 1
    }
    // Close popup if no history items left
    if (state.value.items.every(item => item.type !== 'history')) {
      state.value.visible = false
    }
    // Share the same debounce timer with addHistoryCommand to avoid race
    if (saveDebounceTimer) {
      clearTimeout(saveDebounceTimer)
    }
    saveDebounceTimer = setTimeout(() => {
      saveDebounceTimer = null
      saveHistory(Array.from(historyCache.values()))
    }, 500)
  }

  function getFuzzyMatchIndices(command: string, prefix: string): number[] {
    const cmd = command.toLowerCase()
    const pre = prefix.toLowerCase()
    const indices: number[] = []
    let cmdIdx = 0
    let preIdx = 0
    while (cmdIdx < cmd.length && preIdx < pre.length) {
      if (cmd[cmdIdx] === pre[preIdx]) {
        indices.push(cmdIdx)
        preIdx++
      }
      cmdIdx++
    }
    return indices
  }

  function getHistorySuggestions(prefix: string): SuggestionItem[] {
    if (!prefix) return []
    const lowerPrefix = prefix.toLowerCase()
    const matches: SuggestionItem[] = []
    const entries = Array.from(historyCache.values()).reverse()

    // First pass: exact prefix matches (higher priority)
    for (const entry of entries) {
      const cmd = entry.command
      if (cmd.length > MAX_COMMAND_LENGTH) continue
      if (cmd.toLowerCase().startsWith(lowerPrefix)) {
        const indices: number[] = []
        for (let i = 0; i < lowerPrefix.length && i < cmd.length; i++) {
          indices.push(i)
        }
        matches.push({
          type: 'history',
          label: cmd,
          value: cmd,
          description: t('terminal.suggestionHistory'),
          matchIndices: indices,
          id: entry.id,
        })
      }
    }

    // Second pass: fuzzy matches (like Ctrl+R)
    for (const entry of entries) {
      const cmd = entry.command
      if (cmd.length > MAX_COMMAND_LENGTH) continue
      if (matches.some(m => m.value === cmd)) continue
      const indices = getFuzzyMatchIndices(cmd, lowerPrefix)
      if (indices.length === lowerPrefix.length) {
        matches.push({
          type: 'history',
          label: cmd,
          value: cmd,
          description: t('terminal.suggestionHistory'),
          matchIndices: indices,
          id: entry.id,
        })
      }
    }

    return matches.slice(0, 10)
  }

  function getQuickCommandSuggestions(prefix: string): SuggestionItem[] {
    if (!prefix) return []
    const lowerPrefix = prefix.toLowerCase()
    const matches: SuggestionItem[] = []
    // Read directly from store (lazy load if needed)
    const qcStore = useQuickCommandStore()
    if (!qcStore.loaded) {
      qcStore.load()
    }
    for (const cmd of qcStore.commands) {
      const label = cmd.name || cmd.command
      const lowerLabel = label.toLowerCase()
      const lowerCmd = cmd.command.toLowerCase()
      if (lowerLabel.includes(lowerPrefix) || lowerCmd.includes(lowerPrefix)) {
        // Compute label match indices
        const lblIdx = lowerLabel.indexOf(lowerPrefix)
        const labelIndices: number[] = []
        if (lblIdx >= 0) {
          for (let i = 0; i < lowerPrefix.length; i++) labelIndices.push(lblIdx + i)
        }
        // Compute command match indices
        const cmdIdx = lowerCmd.indexOf(lowerPrefix)
        const cmdIndices: number[] = []
        if (cmdIdx >= 0) {
          for (let i = 0; i < lowerPrefix.length; i++) cmdIndices.push(cmdIdx + i)
        }
        matches.push({
          type: 'quick-command',
          label,
          value: cmd.command,
          description: t('terminal.suggestionQuickCommand'),
          matchIndices: labelIndices.length > 0 ? labelIndices : undefined,
          commandMatchIndices: cmdIndices.length > 0 ? cmdIndices : undefined,
          id: cmd.id,
        })
      }
    }
    return matches.slice(0, 10)
  }

  function updateSuggestions(token: string) {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    if (!token || suppressedUntilNextCommand) {
      state.value.visible = false
      state.value.items = []
      return
    }
    debounceTimer = setTimeout(() => {
      if (!token) return
      const historyItems = getHistorySuggestions(token)
      const quickCommandItems = getQuickCommandSuggestions(token)
      const items: SuggestionItem[] = [...quickCommandItems, ...historyItems]
      state.value.items = items
      state.value.selectedIndex = -1
      state.value.visible = items.length > 0
    }, 150)
  }

  function selectNext() {
    if (state.value.items.length === 0) return
    // Cancel any pending suggestion update to prevent the debounced
    // timer from resetting selectedIndex after the user has navigated.
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (state.value.selectedIndex < 0) {
      state.value.selectedIndex = 0
    } else {
      state.value.selectedIndex = (state.value.selectedIndex + 1) % state.value.items.length
    }
  }

  function selectPrev() {
    if (state.value.items.length === 0) return
    // Cancel any pending suggestion update to prevent the debounced
    // timer from resetting selectedIndex after the user has navigated.
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (state.value.selectedIndex < 0) {
      state.value.selectedIndex = state.value.items.length - 1
    } else {
      state.value.selectedIndex = (state.value.selectedIndex - 1 + state.value.items.length) % state.value.items.length
    }
  }

  function getSelectedItem(): SuggestionItem | null {
    if (state.value.items.length === 0 || state.value.selectedIndex < 0) return null
    return state.value.items[state.value.selectedIndex]
  }

  function close() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    state.value.visible = false
    state.value.items = []
    state.value.selectedIndex = -1
  }

  function suppress() {
    suppressedUntilNextCommand = true
    close()
  }

  function resetSuppress() {
    suppressedUntilNextCommand = false
  }

  function isVisible(): boolean {
    return state.value.visible
  }

  return {
    state,
    historyEntries,
    loadHistory,
    addHistoryCommand,
    removeHistoryCommandById,
    removeHistoryCommandsById,
    updateSuggestions,
    selectNext,
    selectPrev,
    getSelectedItem,
    close,
    suppress,
    isVisible,
    resetSuppress,
  }
}
