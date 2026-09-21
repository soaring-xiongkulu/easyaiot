import { defineStore } from 'pinia'
import { ref } from 'vue'
import { LoadLocalState, SaveLocalState } from '../../bindings/easyaiot/terminal/app'

// Shape of the backend's LocalState store (bindings are untyped JS, so the
// type is declared here and must stay in sync with backend/store).
interface LocalState {
  sidebarVisible: boolean
  aiSidebarVisible: boolean
  collapsedGroupIds: string[]
  collapsedQuickCommandGroupIds: string[]
  windowX: number
  windowY: number
  windowWidth: number
  windowHeight: number
  windowMaximised: boolean
  backgroundEnabled: boolean
  backgroundImage: string
  backgroundOpacity: number
  backgroundBlur: number
  backgroundFit: string
  systemTitleBar: boolean
  externalEditor: string
  // SFTP file-list columns the user hid via the header context menu. Columns
  // absent from the list stay visible.
  sftpHiddenColumns: string[]
}

const DEFAULT: LocalState = {
  sidebarVisible: true,
  aiSidebarVisible: true,
  collapsedGroupIds: [],
  collapsedQuickCommandGroupIds: [],
  windowX: 0,
  windowY: 0,
  windowWidth: 0,
  windowHeight: 0,
  windowMaximised: false,
  backgroundEnabled: false,
  backgroundImage: '',
  backgroundOpacity: 60,
  backgroundBlur: 3,
  backgroundFit: 'cover',
  systemTitleBar: false,
  externalEditor: '',
  sftpHiddenColumns: [],
} as LocalState

export const useLocalStateStore = defineStore('localState', () => {
  const state = ref<LocalState>({ ...DEFAULT })
  const loaded = ref(false)
  let initPromise: Promise<void> | null = null

  async function init() {
    if (loaded.value) return
    if (!initPromise) {
      initPromise = (async () => {
        try {
          const s = await LoadLocalState()
          state.value = { ...DEFAULT, ...s } as LocalState
        } catch {
          // keep defaults
        } finally {
          loaded.value = true
        }
      })()
    }
    return initPromise
  }

  async function update(patch: Partial<LocalState>) {
    state.value = { ...state.value, ...patch } as LocalState
    try {
      await SaveLocalState(state.value as LocalState)
    } catch {
      // ignore save errors
    }
  }

  return { state, loaded, init, update }
})
