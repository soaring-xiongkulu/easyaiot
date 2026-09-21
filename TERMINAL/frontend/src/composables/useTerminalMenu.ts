import { ref } from 'vue'
import type { Ref } from 'vue'
import { Clipboard } from '@wailsio/runtime'
import { useSettingsStore } from '../stores/settingsStore'
import { writeClipboard } from './useClipboardWrite'
export interface UseTerminalMenuOptions {
  getSelection: () => string
  onPaste: (text: string) => Promise<void> | void
  onAskAI?: (text: string) => void
  /** Position + open the actual menu. The host wires this to its <Menu>
   *  instance (openAt), so the composable stays decoupled from the component
   *  and its viewport clamping lives in Menu. */
  openAt?: (x: number, y: number) => void
}

export interface UseTerminalMenuReturn {
  menuVisible: Ref<boolean>
  hasSelection: Ref<boolean>
  onContextMenu: (e: MouseEvent) => void
  openMenu: (e: MouseEvent) => void
  closeMenu: () => void
  copySelection: () => void
  copyAndPaste: () => Promise<void>
  pasteFromClipboard: () => Promise<void>
  askAI: () => void
}

export function useTerminalMenu(options: UseTerminalMenuOptions): UseTerminalMenuReturn {
  const settingsStore = useSettingsStore()

  const menuVisible = ref(false)
  const hasSelection = ref(false)

  function closeMenu() {
    menuVisible.value = false
  }

  function onContextMenu(e: MouseEvent) {
    const rightClickAction = settingsStore.settings.terminal.rightClickAction
    // Ctrl/Cmd + right-click always opens the menu, even when right-click is
    // bound to paste — it's the escape hatch to reach copy/search/export etc.
    // Either modifier is accepted so the intent reads the same on macOS (Cmd)
    // and Windows/Linux (Ctrl).
    const forceMenu = e.ctrlKey || e.metaKey
    if (rightClickAction === 'paste' && !forceMenu) {
      e.preventDefault()
      e.stopPropagation()
      pasteFromClipboard()
      return
    }
    openMenu(e)
  }

  // Unconditionally open the context menu at the cursor. Shared by right-click
  // and the middle-click "show menu" action; unlike onContextMenu it ignores
  // rightClickAction entirely so a middle-click menu never falls through to paste.
  function openMenu(e: MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    hasSelection.value = !!options.getSelection()
    // menuVisible drives the host <Menu>.v-model; openAt positions it (and
    // flips it on). In isolation (tests) openAt is absent so we set it here.
    menuVisible.value = true
    options.openAt?.(e.clientX, e.clientY)
  }

  function copySelection() {
    // Trust getSelection() at click time; the contextmenu-captured ref can
    // be stale in WKWebView (right-click mousedown clears the xterm selection).
    const text = options.getSelection()
    if (text) {
      writeClipboard(text)
    }
    closeMenu()
  }

  async function copyAndPaste() {
    const text = options.getSelection()
    if (text) {
      await writeClipboard(text)
      await options.onPaste(text)
    }
    closeMenu()
  }

  function askAI() {
    const text = options.getSelection()
    if (text && options.onAskAI) {
      options.onAskAI(text)
    }
    closeMenu()
  }

  async function pasteFromClipboard() {
    try {
      // Wails clipboard, not navigator.clipboard.readText() — the latter pops
      // a system "Paste" confirmation on macOS WKWebView.
      const text = await Clipboard.Text()
      if (text) {
        await options.onPaste(text)
      }
    } catch {
      // clipboard read failed
    }
    closeMenu()
  }

  return {
    menuVisible,
    hasSelection,
    onContextMenu,
    openMenu,
    closeMenu,
    copySelection,
    copyAndPaste,
    pasteFromClipboard,
    askAI,
  }
}