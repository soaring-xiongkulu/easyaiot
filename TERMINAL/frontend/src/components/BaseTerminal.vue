<template>
  <div
    class="base-terminal"
    :id="terminalDropId"
    data-file-drop-target
    @dragover.prevent="onDragOver"
    @dragenter.prevent="onDragEnter"
    @dragleave="onDragLeave"
    @drop="onDragDrop"
  >
    <div class="terminal-area" @contextmenu="onTerminalContextMenu">
      <TerminalGutter
        ref="gutterRef"
        :session-id="props.sessionId"
        :show-line-numbers="showLineNumbers"
        :show-timestamps="showTimestamps"
        :get-host="getTerminalHost"
      />
      <div ref="terminalRef" class="terminal-host"></div>
    </div>

    <div v-if="dragOver" class="drop-overlay">
      <span>{{ t('sftp.dropHere') }}</span>
    </div>

    <!-- Search bar -->
    <div v-show="searchVisible" class="terminal-search-bar">
      <button class="search-btn" :class="{ active: searchCaseSensitive }" :title="t('terminal.searchMatchCase')" @click="toggleSearchOption('caseSensitive')">
        <CaseSensitive :size="'0.875rem'" />
      </button>
      <button class="search-btn" :class="{ active: searchRegex }" :title="t('terminal.searchRegexp')" @click="toggleSearchOption('regex')">
        <Regex :size="'0.875rem'" />
      </button>
      <button class="search-btn" :class="{ active: searchWholeWord }" :title="t('terminal.searchWholeWord')" @click="toggleSearchOption('wholeWord')">
        <WholeWord :size="'0.875rem'" />
      </button>
      <input
        ref="searchInputRef"
        v-model="searchText"
        class="search-input"
        :placeholder="t('terminal.searchPlaceholder')"
        @input="onSearchInput"
        @keydown.enter.prevent="onSearchEnter"
        @keydown.escape="closeSearch"
        @blur="getSearchAddon()?.clearActiveDecoration()"
      />
      <span class="search-count" v-if="searchText">{{ searchResultIndex + 1 }}/{{ searchResultCount || 0 }}</span>
      <button class="search-btn" @click="onSearchPrev" :title="`${t('terminal.searchPrev')} (Enter)`">
        <ChevronUp :size="'0.875rem'" />
      </button>
      <button class="search-btn" @click="onSearchNext" :title="`${t('terminal.searchNext')} (Shift+Enter)`">
        <ChevronDown :size="'0.875rem'" />
      </button>
      <button class="search-btn" @click="closeSearch" :title="t('terminal.searchClose')">
        <X :size="'0.875rem'" />
      </button>
    </div>

    <!-- Terminal context menu -->
    <Menu ref="terminalMenuRef" v-model:visible="terminalMenuVisible">
      <!-- ① 剪贴板 -->
      <MenuItem :class="{ disabled: !menu.hasSelection.value }" :shortcut="menuShortcut('copy')" @click="menu.copySelection">
        {{ t('terminal.copy') }}
      </MenuItem>
      <MenuItem :class="{ disabled: !menu.hasSelection.value }" @click="menu.copyAndPaste">
        {{ t('terminal.copyAndPaste') }}
      </MenuItem>
      <MenuItem :shortcut="menuShortcut('paste')" @click="menu.pasteFromClipboard">
        {{ t('terminal.paste') }}
      </MenuItem>

      <!-- ② 会话文本操作 -->
      <MenuDivider />
      <MenuItem :shortcut="menuShortcut('terminalSearch')" @click="triggerSearch">
        {{ t('terminal.searchText') }}
      </MenuItem>
      <MenuItem @click="menu.closeMenu(); exportContent()">{{ t('terminal.export') }}</MenuItem>
      <MenuItem :shortcut="menuShortcut('toggleLineNumbers')" @click="toggleLineNumbers">
        {{ showLineNumbers ? t('settings.hideLineNumbers') : t('settings.showLineNumbers') }}
      </MenuItem>
      <MenuItem :shortcut="menuShortcut('toggleTimestamps')" @click="toggleTimestamps">
        {{ showTimestamps ? t('settings.hideTimestamps') : t('settings.showTimestamps') }}
      </MenuItem>
      <MenuItem v-if="supportsOutputLog" @click="toggleOutputLog">
        {{ isOutputLogOn ? t('session.stopLog') : t('session.startLog') }}
      </MenuItem>
      <MenuItem v-if="supportsOutputLog && isOutputLogOn" @click="openLogDir">
        {{ t('session.openLogDir') }}
      </MenuItem>

      <!-- ③ SSH 连接功能 -->
      <MenuDivider />
      <MenuItem v-if="isSsh" @click="openSftp">{{ t(connectFileMenuKey(panel?.config)) }}</MenuItem>
      <MenuItem v-if="isSsh" @click="uploadFileRz">{{ t('terminal.uploadFileRz') }}</MenuItem>
      <MenuItem v-if="isSsh" @click="openMonitor">{{ t('sidebar.connectMonitor') }}</MenuItem>
    </Menu>

    <!-- Gutter context menu — right-click on the line-number/time columns -->
    <Menu ref="gutterMenuRef" v-model:visible="gutterMenuVisible">
      <MenuItem :shortcut="menuShortcut('toggleLineNumbers')" @click="toggleLineNumbers">
        {{ showLineNumbers ? t('settings.hideLineNumbers') : t('settings.showLineNumbers') }}
      </MenuItem>
      <MenuItem :shortcut="menuShortcut('toggleTimestamps')" @click="toggleTimestamps">
        {{ showTimestamps ? t('settings.hideTimestamps') : t('settings.showTimestamps') }}
      </MenuItem>
    </Menu>

    <!-- Terminal suggestions popup -->
    <TerminalSuggestion
      :visible="suggestions.state.value.visible"
      :items="suggestions.state.value.items"
      :selected-index="suggestions.state.value.selectedIndex"
      :cursor-x="terminalInput?.cursorPixelPos.value.x ?? 0"
      :cursor-y="terminalInput?.cursorPixelPos.value.y ?? 0"
      @select="(idx: number) => applySuggestion(suggestions.state.value.items[idx])"
      @hover="(idx: number) => suggestions.state.value.selectedIndex = idx"
      @remove="(id: string) => suggestions.removeHistoryCommandById(id)"
    />

    <!-- Zmodem transfer panel -->
    <ZmodemTransfer :session-id="props.sessionId || ''" @cancel="onZmodemCancel" />

    <!-- Screen preview on scrollbar hover (issue #729) -->
    <TerminalScreenPreview :session-id="props.sessionId || ''" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, onActivated, onDeactivated, watch, nextTick } from 'vue'
import type { Terminal } from '@xterm/xterm'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'
import { SessionResize, SessionEndZmodem } from '../../bindings/easyaiot/terminal/app'
import { queuedSessionWrite } from '../services/sessionWriter'
import { WriteFileBase64, SaveFileDialog, FrontendLog, EnableSessionOutputLog, DisableSessionOutputLog, GetSessionOutputLogInfo, OpenPathInExplorer } from '../../bindings/easyaiot/terminal/app'
import { useNativeFileDrop } from '../composables/useFilePanel'
import { connectFileMenuKey } from '../utils/fileTransferUtils'
import { isMobilePlatform } from '../utils/platform'
import { applyMobileCtrl } from '../utils/mobileCtrlKey'
import { msg } from '../services/message'
import { useSettingsStore } from '../stores/settingsStore'
import { useLocalStateStore } from '../stores/localStateStore'
import { attachOverlayHighlighter, notifyOverlayHighlightThemeChanged } from '../composables/overlayHighlight'
import { onTerminalKey, formatKeyBinding } from '../composables/useKeyboardShortcuts'
import type { ShortcutAction } from '../types/settings'
import { useSessionStore } from '../stores/sessionStore'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useTerminalMenu } from '../composables/useTerminalMenu'
import { writeClipboard } from '../composables/useClipboardWrite'
import { filterTerminalInput } from '../utils/terminalInputFilter'
import { DcsReassembler } from '../utils/dcsReassembler'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import { useI18n } from '../i18n'
import {
  acquireTerminal,
  releaseTerminal,
  attachTerminal,
  detachTerminal,
  getManagedTerminal,
  transferTerminal,
  bumpOnDataGeneration,
} from '../services/terminalManager'
import { getXtermTheme } from '../composables/useTerminal'
import { resolveXtermBackground, applyTerminalBgVar, resolveTerminalThemeName } from '../composables/useTerminalTheme'
import { stripCursorBlink } from '../utils/cursor'
import { applyBackspaceKey } from '../utils/backspaceKey'
import { formatFontFamily } from '../utils/formatFontFamily'
import { normalizePastedText, pasteWithScroll } from '../utils/terminalPaste'
import {
  sanitizeTerminalOutput,
  sanitizeLiveTerminalOutput,
} from '../utils/terminalSanitize'
import { useTerminalInput } from '../composables/useTerminalInput'
import { useSuggestions } from '../composables/useSuggestions'
import TerminalSuggestion from './TerminalSuggestion.vue'
import TerminalGutter from './TerminalGutter.vue'
import { startZmodemService } from '../services/zmodemService'
import { recordWrite, stampCommandLine, currentAbsoluteLine } from '../services/terminalTimestamps'
import { useZmodemStore } from '../stores/zmodemStore'
import ZmodemTransfer from './ZmodemTransfer.vue'
import TerminalScreenPreview from './TerminalScreenPreview.vue'
import { Browser, Clipboard, Events } from '@wailsio/runtime'
import type { ISearchOptions } from '@xterm/addon-search'
import { CaseSensitive, ChevronUp, ChevronDown, Regex, WholeWord, X } from '@lucide/vue'

const props = defineProps<{
  mode: 'ssh' | 'sftp' | 'local'
  sessionId: string | null | undefined
  onSessionStatus?: (status: string) => void
  broadcastActive?: boolean
  workspaceId?: string
  panelId?: string
}>()

const isMac = /Mac|iPhone|iPad/.test(navigator.userAgent)

const settingsStore = useSettingsStore()

// Human-readable keybinding for a shortcut action ('' when unset), used to show
// the current shortcut hint in the terminal right-click context menu. Reactive
// via settingsStore, so hints update automatically when the user rebinds keys.
function menuShortcut(action: ShortcutAction): string {
  const b = settingsStore.settings.keyboard[action]
  if (!b) return ''
  return formatKeyBinding(b, isMac)
}
const sessionStore = useSessionStore()
const tabStore = useTabStore()
const panelStore = usePanelStore()
const zmodemStore = useZmodemStore()
const localStateStore = useLocalStateStore()
const { t } = useI18n()

// Prevent deactivated (KeepAlive-cached) components from processing
// terminal events. Only the active component should handle input/output.
const isActive = ref(true)

// Unique ref per BaseTerminal instance, so each instance independently
// contributes to the TerminalManager ref count. Without this, two instances
// rendering the same panel (e.g. KeepAlive'd tab + workspace panel) share
// the same panelId ref, and one release drops the count to zero.
const terminalInstanceRef = crypto.randomUUID?.() ||
  Math.random().toString(36).slice(2, 10) +
  Date.now().toString(36)

const terminalRef = ref<HTMLDivElement>()

// Whether the line-number gutter is enabled (from the persistent setting).
const showLineNumbers = computed(() => settingsStore.settings.terminal.showLineNumbers ?? false)
// Whether the timestamp column is enabled (from the persistent setting).
const showTimestamps = computed(() => settingsStore.settings.terminal.showTimestamps ?? false)

// Write terminal data and fold it into the logical-line registry for the
// gutter's number/time columns: lines that just received characters get the
// next sequential number and the arrival time; lines the cursor moved past
// get their timestamp fixed to the completion time. `before` is an absolute
// row index, so a trim inside the write doesn't skew the band.
function writeStamped(data: string) {
  const t = terminal
  const sid = props.sessionId
  if (!t || !sid) { t?.write(data); return }
  const ts = Date.now()
  const before = currentAbsoluteLine(sid)
  t.write(data, () => {
    recordWrite(sid, before, ts)
  })
}

// Pass the xterm host element to the gutter so it can verify the terminal it
// renders is attached to this very component (KeepAlive/drag can move it).
function getTerminalHost(): HTMLElement | null {
  return terminalRef.value ?? null
}

function toggleLineNumbers() {
  menu.closeMenu()
  gutterMenuVisible.value = false
  settingsStore.updateTerminal({ showLineNumbers: !showLineNumbers.value })
}

function toggleTimestamps() {
  menu.closeMenu()
  gutterMenuVisible.value = false
  settingsStore.updateTerminal({ showTimestamps: !showTimestamps.value })
}

const searchInputRef = ref<HTMLInputElement>()
const searchVisible = ref(false)

const dragOver = ref(false)
let dragEnterCount = 0

const suggestions = useSuggestions()
let terminalInput: ReturnType<typeof useTerminalInput> | null = null
let terminal: Terminal | null = null
let onDataDispose: { dispose(): void } | null = null
let keyHandlerDispose: { dispose(): void } | null = null
let resizeObserver: ResizeObserver | null = null
let intersectionObserver: IntersectionObserver | null = null
// Track how many sessionStore chunks have been written to the terminal
// so we can replay only missed data on KeepAlive reactivation.
let writtenChunks = 0
// Viewport position (top line in the buffer) captured on KeepAlive
// deactivation so reactivation can restore the user's scroll position
// instead of jumping to the bottom. baseY at deactivation is also kept so
// we can tell whether the user was scrolled to the bottom before
// deactivation — if they were, new output during the inactive period
// (replayed on activation) should pull the viewport down to the new
// bottom; otherwise the viewport stays where the user left it.
let savedViewportY: number | null = null
let savedBaseY: number | null = null
let unsubscribe: (() => void) | null = null
let statusUnsubscribe: (() => void) | null = null
let onDocumentMouseDown: ((e: MouseEvent) => void) | null = null
let onTerminalAuxClick: ((e: MouseEvent) => void) | null = null
let onOpenSearch: ((e: Event) => void) | null = null
let onExport: ((e: Event) => void) | null = null
let onSendRz: ((e: Event) => void) | null = null
let onTerminalCopy: ((e: Event) => void) | null = null
let onTerminalPaste: ((e: Event) => void) | null = null
let onVisibilityChange: (() => void) | null = null

// Reset xterm's internal IME composition state. Two variants:
// - resetIMEState:        only clears internal flags (safe during active typing)
// - resetIMEComposition:  also blurs textarea to end OS-level composition (for
//                         deactivation / visibility change when terminal is hidden)
//
// Accessing _core._compositionHelper is fragile but necessary — xterm exposes
// no public API for this. The guard ensures we only act when composition is
// actually active.
function resetIMEState(): boolean {
  if (!terminal) return false
  const core = (terminal as any)._core
  const ch = core?._compositionHelper
  if (!ch) return false
  if (!ch._isComposing && !ch._isSendingComposition) return false
  ch._isSendingComposition = false
  ch._isComposing = false
  ch._dataAlreadySent = ''
  const cv = core?._helperContainer?.querySelector?.('.composition-view')
  if (cv) cv.classList.remove('active')
  return true
}

function resetIMEComposition() {
  if (!resetIMEState()) return
  // Clear the textarea and end the OS-level composition via blur.
  if (terminal.textarea) {
    terminal.textarea.value = ''
    terminal.textarea.blur()
  }
}

let resizeTimer: ReturnType<typeof setTimeout> | null = null
// Trailing resize for size changes observed while a resize gate (window
// resize debounce / split drag / suppress window) was active. Separate from
// resizeTimer so it never cancels another handler's pending resize.
let deferredResizeTimer: ReturnType<typeof setTimeout> | null = null
let unsubNativeResizeEnd: (() => void) | null = null
let isResizing = false
let splitResizing = false
let suppressResizeUntil = 0
let retryOnEnter = false
let zmodemService: ReturnType<typeof startZmodemService> | null = null
let isZmodemStarting = false
let zmodemStartTimer: ReturnType<typeof setTimeout> | null = null
let zmodemDirection: 'upload' | 'download' | undefined = undefined
let zmodemCancellingUntil = 0
let zmodemRestoringOutput = false
let zmodemCompletionPending = false
const zmodemDeferredOutput: string[] = []
let exporting = false
// Reassembles DCS (sixel image) sequences split across session:data chunks
// so highlight's per-chunk segmenter never injects SGR codes into an open
// DCS body. Every chunk this component renders must pass through it exactly
// once, in order — including the KeepAlive gap replay below.
const dcsReassembler = new DcsReassembler()

function renderTerminalData(rawData: string, countChunk = true) {
  if (!terminal) return
  let data = stripCursorBlink(rawData, settingsStore.settings.terminal.cursorBlink ?? true).replace(/\x1b\[3J/g, '')
  if (data.includes('\x1b[2J') && terminal.buffer.active.type !== 'alternate') {
    const scrollClear = '\n'.repeat(terminal.rows) + '\x1b[H'
    data = data.replace(/\x1b\[H\x1b\[2J/g, scrollClear)
    data = data.replace(/\x1b\[2J/g, scrollClear)
  }
  data = sanitizeLiveTerminalOutput(data)
  if (props.mode === 'sftp') {
    const cleaned = data.replace(/\x1b\]633;S[^\x07]*\x07/g, '')
    if (cleaned) writeStamped(cleaned)
  } else {
    // Keyword highlighting is applied by the overlay renderer, which scans
    // the parsed buffer and lays decorations over matches — the data stream
    // is written verbatim.
    for (const seg of dcsReassembler.feed(data)) {
      if (seg.dcs) {
        // Complete DCS (sixel image, DECRQSS reply, …): write verbatim —
        // SGR codes injected inside a DCS body would corrupt it.
        writeStamped(seg.text)
        continue
      }
      if (props.mode === 'ssh' && terminalInput) {
        terminalInput.handleSessionData(seg.text)
        if (terminalInput.isInAlternateScreen()) suggestions.close()
      }
      writeStamped(seg.text)
    }
  }
  if (countChunk) writtenChunks++
}

function initZmodemService(sessionId: string) {
  if (!sessionId || props.mode !== 'ssh') return
  // Don't create a duplicate zmodem service if a transfer is already
  // active for this session. The existing service (in a deactivated
  // BaseTerminal) continues to handle the transfer.
  if (zmodemStore.getActiveTransfer(sessionId)) return
  zmodemService = startZmodemService({
    // Register abort so any BaseTerminal component can cancel the transfer
    onRegister: (abort) => zmodemStore.registerAbort(sessionId, abort),
    onUnregister: () => zmodemStore.unregisterAbort(sessionId),
    sessionId,
    direction: zmodemDirection,
    getDefaultDownloadDir: () => settingsStore.settings.terminal.zmodemDownloadDir,
    onTerminalRestoreState: restoring => {
      zmodemRestoringOutput = restoring
      if (!restoring) {
        for (const data of zmodemDeferredOutput.splice(0)) renderTerminalData(data)
        if (zmodemCompletionPending) {
          zmodemCompletionPending = false
          void disposeZmodemService(sessionId, true, false)
          initZmodemService(sessionId)
        }
      }
    },
    onWarning: warning => {
      terminal?.write(`\r\n\x1b[33mZmodem: ${warning}\x1b[0m\r\n`)
    },
    onComplete: (files, hint) => {
      if (files.length > 0) {
        terminal?.write(`\r\n\x1b[32mZmodem: ${files.length} file(s) transferred\x1b[0m\r\n`)
      }
      if (hint) {
        terminal?.write(`\r\n\x1b[33m${hint}\x1b[0m\r\n`)
      }
      if (files.length === 0 && !hint) {
        // 取消或未选择文件：打印提示
        terminal?.write(`\r\n\x1b[33mZmodem transfer cancelled\x1b[0m\r\n`)
        // 等吞数据保护过期后再发送一次回车，确保 sz 已退出、bash 恢复前台后触发提示符
        const cancelUntil = Math.max(zmodemCancellingUntil, zmodemStore.getCancelUntil(sessionId))
        const remaining = Math.max(0, cancelUntil - Date.now())
        setTimeout(() => {
          queuedSessionWrite(sessionId, '\n')
        }, remaining + 100)
      }
      zmodemStore.clearTransfers(sessionId)
      zmodemDirection = undefined
      if (zmodemRestoringOutput) {
        // Keep the binary listener alive until finishTransfer has drained any
        // prompt event queued concurrently with the backend mode handoff.
        zmodemCompletionPending = true
      } else {
        void disposeZmodemService(sessionId, true, false)
        initZmodemService(sessionId)
      }
    },
    onError: (err) => {
      zmodemCompletionPending = false
      terminal?.write(`\r\n\x1b[31mZmodem error: ${err}\x1b[0m\r\n`)
      zmodemStore.clearTransfers(sessionId)
      zmodemDirection = undefined
      void disposeZmodemService(sessionId, true, false)
      initZmodemService(sessionId)
    },
  })
}

async function disposeZmodemService(sessionId: string, resetDirection = true, endSession = true) {
  const service = zmodemService
  const serviceDisposed = service?.dispose()
  zmodemService = null
  isZmodemStarting = false
  zmodemCompletionPending = false
  if (resetDirection) {
    zmodemDirection = undefined
  }
  if (zmodemStartTimer) {
    clearTimeout(zmodemStartTimer)
    zmodemStartTimer = null
  }
  // A service that started binary mode also ends it, ordered after its pending
  // start. Only use the direct fallback when no service owns that lifecycle.
  if (!service && sessionId && endSession) {
    await SessionEndZmodem(sessionId).catch(() => {})
  }
  await serviceDisposed
}

// OS file drops (resource manager) are delivered by Wails via the native
// file-drop event (common:WindowFilesDropped) with real absolute paths,
// routed here by this component's data-file-drop-target id. The HTML5 drop
// handler below only clears overlay state — OS file drops never carry file
// content into the webview.
const terminalDropId = 'terminal-drop-' + (crypto.randomUUID?.() || Math.random().toString(36).slice(2))

const nativeDrop = useNativeFileDrop({
  elementId: terminalDropId,
  isActive: () => !!props.sessionId && !zmodemStore.getActiveTransfer(props.sessionId),
  upload: (paths) => onNativePathsDropped(paths),
})

function onDragOver(e: DragEvent) {
  if (!e.dataTransfer?.types.includes('Files')) return
  e.stopPropagation()
  e.dataTransfer.dropEffect = 'copy'
  dragOver.value = true
}

function onDragEnter(e: DragEvent) {
  if (!e.dataTransfer?.types.includes('Files')) return
  e.stopPropagation()
  dragEnterCount++
  dragOver.value = true
}

function onDragLeave() {
  dragEnterCount--
  if (dragEnterCount <= 0) {
    dragEnterCount = 0
    dragOver.value = false
  }
}

function onDragDrop(e: DragEvent) {
  dragOver.value = false
  dragEnterCount = 0
  // Internal panel/tab drags — let them bubble to workspace handlers
  if (e.dataTransfer?.types.includes('application/panel-id') ||
      e.dataTransfer?.types.includes('application/tab-id')) return
  // OS file drops are handled by the native file-drop event; prevent the
  // WebView from navigating and stop here.
  if (e.dataTransfer?.types.includes('Files')) e.preventDefault()
}

// Convert a Windows native path to the format expected by the active shell.
// - PowerShell / cmd: keep C:\foo\bar (native)
// - Git Bash / MSYS2 / Cygwin / MinGW: /c/foo/bar
// - WSL: /mnt/c/foo/bar
function toShellPath(nativePath: string, shellPath?: string): string {
  const isWinPath = /^[A-Za-z]:\\/.test(nativePath)
  if (!isWinPath) return nativePath.replace(/\\/g, '/')

  const lower = (shellPath || '').toLowerCase()
  let converted: string
  if (lower.includes('wsl')) {
    const drive = nativePath.charAt(0).toLowerCase()
    converted = '/mnt/' + drive + nativePath.slice(2).replace(/\\/g, '/')
  } else if (lower.includes('bash') || lower.includes('git') || lower.includes('msys') || lower.includes('cygwin') || lower.includes('mingw')) {
    const drive = nativePath.charAt(0).toLowerCase()
    converted = '/' + drive + nativePath.slice(2).replace(/\\/g, '/')
  } else {
    converted = nativePath
  }
  // Quote paths with spaces so the shell treats them as a single argument
  return converted.includes(' ') ? `"${converted}"` : converted
}

// Called with real absolute paths from the native OS file-drop event.
function onNativePathsDropped(paths: string[]) {
  if (!props.sessionId || paths.length === 0) return

  // Local terminal: paste file paths as input, adapting format to the shell
  if (props.mode === 'local') {
    const panel = panelStore.getPanel(props.panelId || '')
    const shellPath = panel?.config?.shellPath
    const text = paths.map(p => toShellPath(p, shellPath)).join(' ')
    queuedSessionWrite(props.sessionId, text)
    return
  }

  // Remote terminal: trigger zmodem upload
  zmodemStore.setPendingUploadFiles(props.sessionId, paths)
  queuedSessionWrite(props.sessionId, 'rz -be\n')
}

function onZmodemCancel() {
  const ts = Date.now() + 2000
  zmodemCancellingUntil = ts
  if (props.sessionId) {
    zmodemStore.setCancelUntil(props.sessionId, ts)
    zmodemStore.abortTransfer(props.sessionId)
  }
}

// Search state
const searchText = ref('')
const searchResultIndex = ref(0)
const searchResultCount = ref(0)
// Toggle states persist across search open/close within the session
const searchCaseSensitive = ref(false)
const searchRegex = ref(false)
const searchWholeWord = ref(false)

function sanitizeTerminalHistory(text: string): string {
  const cleaned = sanitizeTerminalOutput(text)
  // Forward debug info to backend log so we can inspect the raw garbage.
  if (cleaned !== text) {
    FrontendLog('sanitizeTerminalHistory', `raw last 400: ${JSON.stringify(text.slice(-400))}`)
    FrontendLog('sanitizeTerminalHistory', `cleaned last 400: ${JSON.stringify(cleaned.slice(-400))}`)
  }
  return cleaned
}

// SFTP line buffer
let inputBuffer = ''

function getTerminalOptions() {
  const ts = settingsStore.settings.terminal
  return {
    fontSize: ts.fontSize || 13,
    fontFamily: ts.fontFamily,
    fallbackFont: ts.fallbackFont || '',
    fontWeight: ts.fontWeight || 400,
    themeName: ts.theme || 'dark',
    scrollback: ts.maxHistoryLines || 2500,
  }
}

function getFitAddon() {
  return props.sessionId ? getManagedTerminal(props.sessionId)?.fitAddon : undefined
}

function getSearchAddon() {
  return props.sessionId ? getManagedTerminal(props.sessionId)?.searchAddon : undefined
}

function getSelection(): string {
  return terminal?.getSelection() || ''
}

async function applySuggestion(item: ReturnType<typeof suggestions.getSelectedItem>) {
  if (!item || !terminal || !terminalInput) return

  const sid = props.sessionId

  if (item.type === 'history' || item.type === 'quick-command') {
    // Replace entire line with Ctrl+U. Using backspaces only works when the
    // replacement is exactly the currentToken; for multi-token input (e.g.
    // "git che" → "git checkout") backspaces leave the earlier text behind.
    if (props.broadcastActive) {
      const targets = tabStore.getAllBroadcastPanelIds()
      for (const pid of targets) {
        const p = panelStore.getPanel(pid)
        if (p?.sessionId && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')) {
          queuedSessionWrite(p.sessionId, '\x15')
          queuedSessionWrite(p.sessionId, item.value)
        }
      }
    } else if (sid) {
      queuedSessionWrite(sid, '\x15')
      queuedSessionWrite(sid, item.value)
    }
    terminalInput.lineBuffer.value = item.value
    terminalInput.cursorIndex.value = item.value.length
    terminalInput.currentToken.value = ''
  }

  suggestions.close()
}

function resize() {
  if (props.mode === 'ssh' || props.mode === 'local') {
    const sid = props.sessionId
    if (!terminal || !sid) return
    const fitAddon = getFitAddon()
    if (!fitAddon) return
    const el = terminalRef.value
    if (!el) return

    const rect = el.getBoundingClientRect()
    // Skip resize when the component is hidden (e.g. during tab switching
    // with KeepAlive). A zero-size resize would corrupt xterm.js buffers.
    if (rect.width === 0 || rect.height === 0) return

    // Heal any stale scroll offset on the host: a focus()-driven auto-scroll
    // during a resize transition can leave it scrolled (content displaced
    // upward, blank space below). The host is never scrolled deliberately.
    if (el.scrollTop !== 0) {
      el.scrollTop = 0
    }

    // Always fit first to update CSS dimensions on the .xterm element.
    // Without this, stale inline pixel dimensions from a previous fit()
    // prevent the terminal from filling the container after window resize
    // (e.g. after duplicating a session tab).
    fitAddon.fit()
    if (terminal.cols <= 0 || terminal.rows <= 0) return

    // Trust fitAddon.fit() — its measure already accounts for the scrollbar
    // gutter; manual recomputation double-subtracts it.
    terminal.resize(terminal.cols, terminal.rows)
    // Full-viewport redraw — prevents canvas ghosting during rapid write bursts.
    terminal.refresh(0, terminal.rows - 1)
    SessionResize(sid, terminal.cols, terminal.rows).catch(() => {})
  } else {
    getFitAddon()?.fit()
  }
}

function write(data: string) {
  terminal?.write(data)
}

// Restore the scroll position captured on deactivation. Returns true when the
// position has landed (or there was nothing to restore) so callers can stop
// retrying.
//
// xterm v6 moved scrolling into the VS Code Scrollable widget: .xterm-viewport
// is no longer the scroll container and viewport._currentRowHeight is gone, so
// the old "write scrollTop by hand" fallback silently did nothing. The position
// now lives in the Scrollable and is derived from render dimensions — right
// after KeepAlive activation the container can still be 0×0, where cell height
// is unknown and any position we set clamps back to 0. So we bail while
// dimensions are invalid and re-apply after each resize() retry instead.
function restoreSavedScroll(): boolean {
  if (savedViewportY == null || savedBaseY == null) return true
  const buf = terminal?.buffer?.active
  const core = (terminal as any)?._core
  const cellHeight: number = core?._renderService?.dimensions?.css?.cell?.height ?? 0
  if (!buf || cellHeight <= 0) return false

  const wasAtBottom = savedViewportY >= savedBaseY - 1
  const target = wasAtBottom ? buf.baseY : Math.min(savedViewportY, buf.length - 1)
  // scrollToLine(line, true) on the internal viewport skips the smooth-scroll
  // animation and syncs ydisp in the same tick; the public scrollToLine() would
  // animate the jump on every tab switch.
  const vp = core?._viewport
  if (typeof vp?.scrollToLine === 'function') {
    vp.scrollToLine(target, true)
  } else {
    terminal?.scrollToLine(target)
  }
  if (buf.viewportY !== target) return false
  savedViewportY = null
  savedBaseY = null
  return true
}

function focus() {
  // Don't steal focus while the user is typing in an input (e.g. renaming a
  // tab); a stray session:status event would otherwise blur the rename box.
  const el = document.activeElement
  if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || (el as HTMLElement).isContentEditable)) {
    return
  }
  terminal?.focus()
}

function toBase64(str: string): string {
  const encoder = new TextEncoder()
  const bytes = encoder.encode(str)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

async function exportContent() {
  if (!terminal || exporting) return
  exporting = true
  try {
    let content = ''
    try {
      const buffer = terminal.buffer.active
      const totalLines = buffer.length
      const lines = new Array(totalLines)
      for (let i = 0; i < totalLines; i++) {
        const line = buffer.getLine(i)
        lines[i] = line ? line.translateToString() : ''
      }
      content = lines.join('\n')
    } catch (e) {
      console.error('Buffer read failed:', e)
      return
    }
    try {
      const filePath = await SaveFileDialog('terminal.txt')
      if (!filePath) return
      await WriteFileBase64(filePath, toBase64(content))
    } catch (e) {
      console.error('Export failed:', e)
    }
  } finally {
    exporting = false
  }
}

function setRetryOnEnter(value: boolean) {
  retryOnEnter = value
}

function onWindowResize() {
  const el = terminalRef.value
  if (!el) return
  if (!isResizing) {
    isResizing = true
    el.classList.add('resizing')
  }
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    isResizing = false
    el.classList.remove('resizing')
    resize()
  }, 400)
}

// Native window finished resizing (drag-to-restore / maximize / programmatic
// resize). Go emits this after WM_EXITSIZEMOVE / WM_SIZE settles, because the
// browser does not always fire a final window.resize at the settled size after
// a native drag — which would leave the canvas at a stale small row count with
// blank space below (issue #656). Bypass the isResizing gate so this cleanup
// fit always runs, then resolve for a clean re-fit at the true container size.
function onNativeResizeEnd() {
  if (resizeTimer) clearTimeout(resizeTimer)
  isResizing = false
  terminalRef.value?.classList.remove('resizing')
  resizeTimer = setTimeout(() => resize(), 100)
}

function onSplitResizeStart() {
  splitResizing = true
}

function onSplitResizeEnd() {
  splitResizing = false
  if (resizeTimer) {
    clearTimeout(resizeTimer)
    resizeTimer = null
  }
  suppressResizeUntil = Date.now() + 200
  nextTick(() => {
    setTimeout(() => {
      void terminalRef.value?.offsetWidth
      resize()
    }, 0)
  })
}

function writeTerminalInput(data: string, inAlternateScreen: boolean) {
  const sid = props.sessionId
  const filtered = filterTerminalInput(data, inAlternateScreen)
  // Don't send empty input - avoids extra blank line when pressing Enter with no command
  if (!sid || !filtered) return

  if (props.broadcastActive) {
    const targets = tabStore.getAllBroadcastPanelIds()
    if (targets.length > 0) {
      for (const pid of targets) {
        const p = panelStore.getPanel(pid)
        if (p?.sessionId && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl')) {
          const translated = applyBackspaceKey(
            filtered,
            p.config?.backspaceKey,
            p.config?.type,
          )
          queuedSessionWrite(p.sessionId, translated)
        }
      }
      return
    }
  }

  const panel = props.panelId ? panelStore.getPanel(props.panelId) : undefined
  const translated = applyBackspaceKey(
    filtered,
    panel?.config?.backspaceKey,
    panel?.config?.type,
  )
  queuedSessionWrite(sid, translated)
}

function handleTerminalKey(e: KeyboardEvent): boolean {
  // Check global shortcuts first (Ctrl+Shift+/Alt+ combos)
  if (e.type === 'keydown' && !onTerminalKey(e)) return false

  // A bare modifier key (Shift/Ctrl/Alt/Meta held alone) produces no input, yet
  // xterm's _keyDown still runs and, with scrollOnUserInput=true, fires
  // scrollToBottom() — yanking the viewport back to the bottom when the user
  // has scrolled up to read history (issue #538). Short-circuit bare modifiers
  // before they reach xterm's scroll logic; they shouldn't be PTY input anyway.
  if (e.type === 'keydown' && (e.key === 'Control' || e.key === 'Shift' || e.key === 'Alt' || e.key === 'Meta')) {
    return false
  }

  // macOS 26 WKWebView: xterm's modifier handling for Shift+Delete is
  // unreliable and may emit no sequence, so the key silently fails to delete
  // (issue #538). Inject the standard CSI delete sequence ESC[3~ directly for
  // all plain Delete presses. Ctrl/Meta/Cmd combos are left to xterm so future
  // Delete-chord shortcuts can still hook in.
  if (e.type === 'keydown' && e.key === 'Delete' && !e.ctrlKey && !e.metaKey && !e.altKey) {
    e.preventDefault()
    terminal?.input('\x1b[3~')
    return false
  }

  // Paste via Wails clipboard (xterm's DOM paste is unreliable in WKWebView).
  // macOS Cmd+V stays hardcoded — it is not one of the configurable shortcuts.
  // On Windows/Linux, Ctrl+Shift+V is handled by the configurable shortcut
  // system (see the terminal:paste event below). Plain Ctrl+V is never
  // intercepted, so it passes through to the terminal app (vim visual block,
  // bash literal-next…) on every platform.
  if (isMac && e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === 'v' || e.key === 'V') && e.type === 'keydown') {
    e.preventDefault()
    if (props.mode === 'ssh' || props.mode === 'local') {
      Clipboard.Text().then(text => {
        if (text) pasteToSession(text)
      }).catch(() => {})
    }
    return false
  }

  // macOS Cmd+C: copy selection when there is one. With no selection, don't
  // intercept — let it pass through (Ctrl+C interrupt uses ctrlKey, unaffected).
  if (isMac && e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === 'c' || e.key === 'C') && e.type === 'keydown') {
    const sel = terminal?.getSelection()
    if (sel) {
      e.preventDefault()
      writeClipboard(sel)
      return false
    }
    return true
  }

  // macOS-style cursor word/line jumping via Option/Cmd + arrow keys
  if (e.type === 'keydown' && (e.altKey || e.metaKey)) {
    if (e.key === 'ArrowLeft') {
      e.preventDefault()
      if (e.metaKey) {
        // Cmd+Left → beginning of line
        queuedSessionWrite(props.sessionId || '', '\x1b[H')
      } else if (e.altKey) {
        // Option+Left → backward word
        queuedSessionWrite(props.sessionId || '', '\x1bb')
      }
      return false
    }
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      if (e.metaKey) {
        // Cmd+Right → end of line
        queuedSessionWrite(props.sessionId || '', '\x1b[F')
      } else if (e.altKey) {
        // Option+Right → forward word
        queuedSessionWrite(props.sessionId || '', '\x1bf')
      }
      return false
    }
  }

  // Suggestion navigation (only on keydown, ignore keyup)
  if (suggestions.isVisible() && e.type === 'keydown') {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      suggestions.selectNext()
      return false
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      suggestions.selectPrev()
      return false
    }
    if (e.key === 'Tab') {
      const selected = suggestions.getSelectedItem()
      if (selected) {
        e.preventDefault()
        applySuggestion(selected)
        return false
      }
    }
    if (e.key === 'Enter') {
      // Only apply suggestion if user explicitly selected one with arrow keys
      const selected = suggestions.getSelectedItem()
      if (selected) {
        e.preventDefault()
        applySuggestion(selected)
        return false
      }
      // No selection: let xterm handle Enter normally (terminal command execution)
    }
    if (e.key === 'Escape') {
      suggestions.close()
      return false
    }
  }

  return true
}

let bindListeners: (() => void) | null = null

// ── Touch panning (mobile) ──
// xterm v6 scrolls via a VS Code-style custom scrollable element that only
// handles mouse wheel and scrollbar drags — touch drags do nothing, so on
// touch devices finger-panning can't scroll the buffer. Translate single-
// finger drags into scrollLines; in the alternate screen send arrow keys
// instead, matching desktop wheel behaviour.
const isMobileTouch = isMobilePlatform()
const touchPan = {
  active: false,
  moved: false,
  lastY: 0,
  lastT: 0,
  accum: 0,     // fractional line remainder so slow drags still accumulate
  velocity: 0,  // px/ms for release inertia
  raf: 0,
}
let panCellHeight = 16

function touchPanStop() {
  touchPan.active = false
  if (touchPan.raf) {
    cancelAnimationFrame(touchPan.raf)
    touchPan.raf = 0
  }
}

function touchPanBy(lines: number) {
  if (!terminal || lines === 0) return
  if (terminal.buffer.active.type === 'alternate') {
    const sid = props.sessionId
    if (!sid) return
    const seq = lines > 0 ? '\x1b[B' : '\x1b[A'
    for (let i = 0; i < Math.min(Math.abs(lines), 8); i++) queuedSessionWrite(sid, seq)
  } else {
    terminal.scrollLines(lines)
  }
}

function onTerminalTouchStart(e: TouchEvent) {
  if (e.touches.length !== 1) {
    touchPanStop()
    touchPan.moved = false
    return
  }
  touchPanStop()
  touchPan.active = true
  touchPan.moved = false
  touchPan.lastY = e.touches[0].clientY
  touchPan.lastT = performance.now()
  touchPan.velocity = 0
  touchPan.accum = 0
}

function onTerminalTouchMove(e: TouchEvent) {
  if (!touchPan.active || e.touches.length !== 1) return
  const y = e.touches[0].clientY
  const now = performance.now()
  const dy = touchPan.lastY - y // finger up => positive => scroll down
  if (!touchPan.moved && Math.abs(dy) < 2) return
  touchPan.moved = true
  e.preventDefault()
  const dt = Math.max(1, now - touchPan.lastT)
  touchPan.velocity = 0.8 * touchPan.velocity + 0.2 * (dy / dt)
  touchPan.lastY = y
  touchPan.lastT = now
  const host = terminalRef.value
  const rows = terminal?.rows || 1
  if (host && rows > 0 && host.clientHeight > 0) panCellHeight = host.clientHeight / rows
  touchPan.accum += dy / panCellHeight
  const lines = Math.trunc(touchPan.accum)
  if (lines !== 0) {
    touchPan.accum -= lines
    touchPanBy(lines)
  }
}

function onTerminalTouchEnd() {
  if (!touchPan.active) return
  touchPan.active = false
  if (!touchPan.moved) return
  // Release inertia: keep scrolling with exponential decay.
  let v = touchPan.velocity * 16 // px per frame
  const step = () => {
    if (Math.abs(v) < 1 || !terminal) {
      touchPan.raf = 0
      return
    }
    touchPan.accum += v / panCellHeight
    const lines = Math.trunc(touchPan.accum)
    if (lines !== 0) {
      touchPan.accum -= lines
      touchPanBy(lines)
    }
    v *= 0.94
    touchPan.raf = requestAnimationFrame(step)
  }
  touchPan.raf = requestAnimationFrame(step)
}

onMounted(() => {
  nativeDrop.bind()
  if (!terminalRef.value) return

  // Acquire shared terminal from manager (or create if first mount)
  const opts = getTerminalOptions()
  terminal = acquireTerminal(props.sessionId || '', terminalInstanceRef, opts, settingsStore.settings.customTerminalThemes)
  // Keyword highlighting scans the parsed buffer and overlays decorations;
  // the enable switch is re-read on every refresh, so toggling the setting
  // takes effect live. Applies to every terminal type.
  attachOverlayHighlighter(terminal)

  // Load WebLinksAddon per-component (has custom callbacks)
  let hoverEl: HTMLDivElement | null = null
  const webLinksAddon = new WebLinksAddon(
    (event, uri) => {
      if (event.ctrlKey || event.metaKey) {
        Browser.OpenURL(uri)
      }
    },
    {
      hover(event, _text, _location) {
        if (!hoverEl) {
          hoverEl = document.createElement('div')
          hoverEl.className = 'xterm-link-tooltip'
          terminal!.element!.appendChild(hoverEl)
        }
        const rect = terminal!.element!.getBoundingClientRect()
        hoverEl.textContent = 'Ctrl + Click to open'
        hoverEl.style.left = (event.clientX - rect.left + 12) + 'px'
        hoverEl.style.top = (event.clientY - rect.top - 28) + 'px'
        hoverEl.style.display = 'block'
      },
      leave() {
        if (hoverEl) {
          hoverEl.style.display = 'none'
        }
      }
    }
  )
  terminal.loadAddon(webLinksAddon)

  // Unicode 11 activeVersion is set in terminalManager.ts right after the
  // addon loads; no need to set it here again.

  // Set up search results listener from shared SearchAddon
  const managed = getManagedTerminal(props.sessionId || '')
  if (managed) {
    managed.searchAddon.onDidChangeResults((e) => {
      searchResultIndex.value = e.resultIndex
      searchResultCount.value = e.resultCount
    })
  }

  // Attach terminal DOM to this component's container
  attachTerminal(props.sessionId || '', terminalRef.value)

  // Touch panning: only wired on touch devices (see block above bindListeners)
  if (isMobileTouch && terminalRef.value) {
    const el = terminalRef.value
    el.addEventListener('touchstart', onTerminalTouchStart, { passive: true })
    el.addEventListener('touchmove', onTerminalTouchMove, { passive: false })
    el.addEventListener('touchend', onTerminalTouchEnd, { passive: true })
    el.addEventListener('touchcancel', () => { touchPanStop(); touchPan.moved = false }, { passive: true })
  }

  initZmodemService(props.sessionId || '')

  // Initialize terminal input handling for SSH
  if (props.mode === 'ssh') {
    terminalInput = useTerminalInput(terminal, {
      mode: props.mode,
      sessionId: props.sessionId,
      enableHistory: true,  // was: smartOn
      onHistoryExtract: (command: string) => {
        suggestions.addHistoryCommand(command)
      },
      onResetSuppress: () => {
        suggestions.resetSuppress()
      },
    })
    suggestions.loadHistory()
  }

  if (props.mode === 'ssh' || props.mode === 'local') {
    // Restore terminal content from session buffer on first mount only.
    // Subsequent mounts reuse the shared terminal whose buffer already
    // contains the correct content.
    const sid = props.sessionId
    const isNewTerminal = managed?.isNew
    if (sid && isNewTerminal) {
      const raw = sessionStore.getData(sid)
      const history = sanitizeTerminalHistory(raw)
      if (history) {
        // Highlighting is applied by the overlay renderer scanning the
        // buffer, so restored history is decorated the same way as
        // newly arriving lines after a tab switch.
        writeStamped(history)
      }
    }
    // Always sync writtenChunks to prevent onActivated from replaying
    // all session data when the terminal was reused (isNewTerminal=false).
    if (sid) {
      writtenChunks = sessionStore.getChunkCount(sid)
    }
    // Force initial resize with retries — needed because cell dimensions
    // may not be available immediately, and for reused terminals the cols/rows
    // may hold stale dimensions from the previous container.
    ;[50, 150, 300, 600, 1000, 2000].forEach(d => setTimeout(() => {
      if (!terminal) return
      getFitAddon()?.fit()
      const sessionId = props.sessionId
      if (sessionId && terminal.cols > 0 && terminal.rows > 0) {
        SessionResize(sessionId, terminal.cols, terminal.rows).catch(() => {})
      }
    }, d))
  }

  // Bind per-component listeners (onData, keyHandler).
  // Called from onMounted and onActivated; disposed in onDeactivated.
  bindListeners = () => {
    // Dispose previous listeners before re-registering
    onDataDispose?.dispose()
    onDataDispose = null
    keyHandlerDispose?.dispose()
    keyHandlerDispose = null

    // Bump the TERMINAL-SHARED generation counter so that ALL
    // components sharing this terminal can detect stale callbacks.
    // Per-component counter allowed KeepAlive-cached duplicate
    // components to both pass their independent guards.
    const sidNow = props.sessionId
    const gen = sidNow ? bumpOnDataGeneration(sidNow) : 0

    keyHandlerDispose = terminal.attachCustomKeyEventHandler(handleTerminalKey)

    // Input handling
    onDataDispose = terminal.onData((data) => {
      // ── Stale callback guard (terminal-shared) ──
      // Check against the MANAGED terminal's current generation.
      // If another component (e.g. KeepAlive-cached) has registered
      // a newer handler on the same shared terminal, bail out.
      const curGen = sidNow ? (getManagedTerminal(sidNow)?.onDataGeneration ?? gen) : gen
      if (gen !== curGen) {
        return
      }

      // Mobile sticky Ctrl: transform the next soft-keyboard character into
      // the corresponding Ctrl combo (e.g. 'c' → ^C) when Ctrl is armed.
      if (isMobileTouch && (props.mode === 'ssh' || props.mode === 'local')) {
        const transformed = applyMobileCtrl(data)
        if (transformed !== null) {
          writeTerminalInput(transformed, false)
          return
        }
      }

      if (props.mode === 'ssh' || props.mode === 'local') {
      if (retryOnEnter && (data === '\r' || data === '\n')) {
        retryOnEnter = false
        if (props.onSessionStatus) {
          props.onSessionStatus('retry')
        }
        return
      }

      // Detect rz/sz command to hint zmodem transfer direction.
      // Must happen BEFORE terminalInput.handleInput because handleInput
      // clears the line buffer on Enter.
      if ((data === '\r' || data === '\n') && terminalInput && !terminalInput.isInAlternateScreen()) {
        // Stamp the command line with the moment it was executed (timestamp
        // column). Must happen before handleInput clears the line buffer.
        if (props.sessionId) stampCommandLine(props.sessionId, Date.now())
        const line = terminalInput.lineBuffer.value.trim()
        if (/^(?:sudo\s+)?rz\b/.test(line)) {
          zmodemDirection = 'upload'
          // Recreate the zmodem service so on_detect sees the new direction.
          if (props.sessionId) {
            disposeZmodemService(props.sessionId, false).then(() => {
              initZmodemService(props.sessionId)
            })
          }
        } else if (/^(?:sudo\s+)?sz\b/.test(line)) {
          zmodemDirection = 'download'
          if (props.sessionId) {
            disposeZmodemService(props.sessionId, false).then(() => {
              initZmodemService(props.sessionId)
            })
          }
        }
      }

      // Handle suggestions input (skip in alternate screen apps like vim/k9s)
      if (terminalInput && !terminalInput.isInAlternateScreen() && (props.mode === 'ssh' || props.mode === 'local')) {
        terminalInput.handleInput(data)

        // When suggestions are visible, intercept certain keys synchronously
        if (suggestions.isVisible()) {
          if (data === '\t') {
            const selected = suggestions.getSelectedItem()
            if (selected) {
              applySuggestion(selected)
              return
            }
          }
          if (data === '\r' || data === '\n') {
            const selected = suggestions.getSelectedItem()
            if (selected) {
              applySuggestion(selected)
              return
            }
          }
          if (data === '\x1b') {
            suggestions.close()
            return
          }
        }

        // Defer suggestion update/close so SessionWrite is not blocked
        const wasVisible = suggestions.isVisible()
        setTimeout(() => {
          if (!terminalInput) return
          const smartOn = settingsStore.settings.terminal.smartCompletion ?? true
          if (!smartOn) {
            suggestions.close()
            return
          }
          // Don't show suggestions if line buffer was already cleared (e.g. Enter pressed)
          if (!terminalInput.lineBuffer.value) {
            suggestions.close()
            return
          }
          // Only show suggestions if they were already visible or if the
          // input is a printable character (not arrow keys / navigation).
          const isPrintable = data.length === 1 && data >= ' '
          if (!wasVisible && !isPrintable) return
          if (terminalInput.isAtLineEnd() && terminalInput.currentToken.value && !terminalInput.isPasswordMode()) {
            suggestions.updateSuggestions(terminalInput.currentToken.value)
          } else {
            suggestions.close()
          }
        }, 0)
      } else if (terminalInput?.isInAlternateScreen()) {
        suggestions.close()
      }

      const sid = props.sessionId
      const inAlt = terminalInput?.isInAlternateScreen() ?? false
      if (sid) {
        writeTerminalInput(data, inAlt)
      }
    } else {
      // SFTP line buffering
      for (let i = 0; i < data.length; i++) {
        const char = data[i]
        const code = data.charCodeAt(i)
        if (char === '\r' || char === '\n') {
          if (inputBuffer) {
            const sid = props.sessionId
            if (sid) {
              for (let j = 0; j < inputBuffer.length; j++) {
                terminal!.write('\b \b')
              }
              queuedSessionWrite(sid, inputBuffer)
            }
            inputBuffer = ''
          }
        } else if (code === 127 || char === '\b') {
          if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1)
            terminal!.write('\b \b')
          }
        } else if (code >= 32 && code <= 126) {
          inputBuffer += char
          terminal!.write(char)
        }
      }
    }
  })

  } // end bindListeners

  // Selection action: copy to clipboard via xterm's native selection event.
  // Use setTimeout to let xterm finish processing the selection (especially
  // for double-click word selection) before reading getSelection().
  let lastSelectionText = ''
  terminal.onSelectionChange(() => {
    if (settingsStore.settings.terminal.selectionAction !== 'copy') return
    setTimeout(() => {
      const text = terminal?.getSelection()
      if (text && text !== lastSelectionText) {
        lastSelectionText = text
        // Wails clipboard writer: navigator.clipboard silently fails in
        // WKWebView when the webview isn't first responder (#827).
        writeClipboard(text)
      }
    }, 0)
  })

  // Close suggestion popup when clicking outside
  onDocumentMouseDown = (event: MouseEvent) => {
    if (!suggestions.isVisible()) return
    const baseTerminalEl = terminalRef.value?.closest('.base-terminal')
    const popupEl = baseTerminalEl?.querySelector('.terminal-suggestion-popup')
    if (popupEl && !popupEl.contains(event.target as Node)) {
      suggestions.close()
    }
  }
  document.addEventListener('mousedown', onDocumentMouseDown)

  // Middle-click action: read setting. 'paste' pastes the clipboard, 'menu'
  // opens the context menu at the cursor, 'none' does nothing.
  onTerminalAuxClick = (event: MouseEvent) => {
    if (event.button !== 1) return
    if (!terminalRef.value?.contains(event.target as Node)) return
    const action = settingsStore.settings.terminal.middleClickAction
    if (action === 'menu') {
      // auxclick exposes the same clientX/clientY as a contextmenu event, so
      // reuse the menu opener to position the <Menu> at the cursor. openMenu
      // (not onContextMenu) is used so it opens regardless of the right-click
      // action setting and never falls through to paste.
      menu.openMenu(event)
      return
    }
    if (action !== 'paste') return
    event.preventDefault()
    event.stopPropagation()
    Clipboard.Text().then(text => {
      if (text && props.sessionId) {
        pasteToSession(text)
      }
    }).catch(() => {})
  }
  document.addEventListener('auxclick', onTerminalAuxClick)

  // Session data
  unsubscribe =Events.On('session:data', (ev) => { const payload: { id: string; data: string } = ev.data; 
    if (!isActive.value) {
      // Mark notification dot on the tab when inactive terminal receives output
      // Only process events for this instance's session (events are global)
      if (payload.id === props.sessionId && props.sessionId) {
        // Find the panel by sessionId (panels Map is keyed by panelId)
        let panelId: string | null = null
        for (const [id, p] of panelStore.panels) {
          if (p.sessionId === props.sessionId) {
            panelId = id
            break
          }
        }
        if (panelId) {
          const tab = tabStore.tabs.find(t =>
            (t.type === 'terminal' && t.panelId === panelId) ||
            (t.type === 'workspace' && t.panelIds.includes(panelId))
          )
          if (tab && tab.id !== tabStore.activeTabId) {
            tabStore.markTabNotification(tab.id)
          }
        }
      }
      return
    }
    if (payload.id !== props.sessionId || !terminal) return

    // 取消后 2 秒内吞掉所有数据，防止残余二进制乱码
    if (Date.now() < zmodemCancellingUntil) {
      return
    }

    // Keep output arriving after EndZmodem behind the restored prompt.
    if (zmodemRestoringOutput) {
      zmodemDeferredOutput.push(payload.data)
      return
    }

    // tab 切换后服务还没重建，但 store 里还有活跃传输（旧的 handleReceive 还在跑），先吞数据
    const hasStoreTransfer = zmodemStore.getActiveTransfer(props.sessionId || '')
    if (!zmodemService && hasStoreTransfer) {
      return
    }

    // Zmodem detection: scan for HEX header in normal terminal output.
    // Skip if the service was aborted (waiting for the next rz/sz command).
    const activeZmodem = zmodemService && zmodemStore.getActiveTransfer(props.sessionId || '')
    if (zmodemService && !activeZmodem && !zmodemService.isAborted?.()) {
      if (isZmodemStarting) {
        // Already detected header and waiting for SessionStartZmodem / on_detect.
        // Feed subsequent data to sentry so it can complete detection without
        // re-processing the header heuristic on every retry frame.
        zmodemService.consume(payload.data)
        return
      }
      // Real ZMODEM headers always contain the ZDLE control byte (0x18)
      // before the frame type: `**` (ZPAD ZPAD) `\x18` (ZDLE) `[ABC]` then
      // hex digits. Requiring the 0x18 avoids false positives on ordinary
      // terminal output — e.g. vim rendering a file whose content happens to
      // contain `**B<hex>` — which previously flipped the session into binary
      // ZMODEM mode and made the sentry write protocol bytes back to the
      // server, crashing the remote shell (issue #242).
      const ZMODEM_HEX_RE = /\*{2,}\x18[ABC][0-9a-fA-F]{10,}/
      if (ZMODEM_HEX_RE.test(payload.data)) {
        console.debug('[zmodem] header detected, entering transfer mode')
        isZmodemStarting = true
        if (zmodemStartTimer) clearTimeout(zmodemStartTimer)
        zmodemStartTimer = setTimeout(() => {
          isZmodemStarting = false
        }, 3000)
        const sid = props.sessionId
        if (sid) {
          // Consume immediately to avoid losing data during async handoff
          zmodemService.start(payload.data)
        }
        // Hide zmodem data from terminal
        return
      }
    }

    // If zmodem is active, skip writing data to terminal (data comes via session:binary)
    if (activeZmodem) {
      isZmodemStarting = false
      return
    }

    renderTerminalData(payload.data)
  })

  // SSH/Local: session status events
  if (props.mode === 'ssh' || props.mode === 'local') {
    retryOnEnter = false
    statusUnsubscribe = Events.On('session:status', (ev) => {
      const payload = ev.data as { id: string; status: string }
      if (!isActive.value) return
      if (payload.id !== props.sessionId) return
      if (payload.status === 'connected') {
        retryOnEnter = false
        if (props.onSessionStatus) {
          props.onSessionStatus(payload.status)
        }
        // Force send current terminal size to sync the backend PTY after reconnect.
        // The new session defaults to 80x24; without this, apps like vim/k9s use the wrong size.
        if (terminal && terminal.cols > 0 && terminal.rows > 0) {
          SessionResize(props.sessionId, terminal.cols, terminal.rows).catch(() => {})
        }
        resize()
      } else if (payload.status === 'error') {
        retryOnEnter = true
        if (props.onSessionStatus) {
          props.onSessionStatus(payload.status)
        }
        terminal?.write('\r\n\x1b[31mConnection failed. Press Enter to retry.\x1b[0m\r\n')
      } else if (payload.status === 'disconnected') {
        retryOnEnter = true
        if (props.onSessionStatus) {
          props.onSessionStatus(payload.status)
        }
        // Local shells exit for ordinary reasons (`exit`, or a child like
        // opencode's /exit tearing down the ConPT }), so say the shell ended
        // rather than implying a failure. Without this the pane just freezes
        // mid-output and looks hung — see the stray `+q4d73` case.
        //
        // Reset mouse tracking here too: an app that exited without
        // disabling it leaves selection broken, and the backend's
        // reset-on-Enter path needs a live session it no longer has.
        if (props.mode === 'local') {
          terminal?.write(
            '\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1004l\x1b[?1005l\x1b[?1006l\x1b[?1015l' +
            '\r\n\x1b[33mShell exited. Press Enter to restart.\x1b[0m\r\n'
          )
        }
      } else {
        // Focus terminal on connecting so user can type password immediately.
        focus()
        if (props.onSessionStatus) {
          props.onSessionStatus(payload.status)
        }
      }
    })
  }

  window.addEventListener('resize', onWindowResize)
  window.addEventListener('split:resize-start', onSplitResizeStart)
  window.addEventListener('split:resize-end', onSplitResizeEnd)
  // Native window finished resizing (drag-to-restore / maximize). Go emits this
  // after the WM_EXITSIZEMOVE / WM_SIZE loop settles; the browser doesn't always
  // fire a final window.resize at the settled size, so this is the reliable
  // trigger to re-fit the terminal (issue #656). Delivered as a Wails event.
  unsubNativeResizeEnd = Events.On('window:resize-end', () => onNativeResizeEnd())
  onOpenSearch = (e: Event) => {
    if (!isActive.value) return
    const detail = (e as CustomEvent).detail
    if (!props.panelId || detail?.panelId !== props.panelId) return
    openSearch()
  }
  window.addEventListener('terminal:open-search', onOpenSearch)

  onExport = (e: Event) => {
    if (!isActive.value) return
    const detail = (e as CustomEvent).detail
    if (!props.panelId || detail?.panelId !== props.panelId) return
    exportContent()
  }
  window.addEventListener('terminal:export', onExport)

  onSendRz = (e: Event) => {
    const detail = (e as CustomEvent).detail
    if (detail?.panelId && detail.panelId !== props.panelId) return
    if (props.sessionId) {
      queuedSessionWrite(props.sessionId, 'rz -be\n')
    }
  }
  window.addEventListener('terminal:send-rz', onSendRz)

  // Configurable copy/paste shortcuts (Ctrl+Shift+C/V on Windows/Linux).
  // The App-level shortcut handler dispatches these events to the active panel.
  onTerminalCopy = (e: Event) => {
    if (!isActive.value) return
    const detail = (e as CustomEvent).detail
    if (detail?.panelId && detail.panelId !== props.panelId) return
    const sel = terminal?.getSelection()
    if (sel) {
      writeClipboard(sel)
    }
  }
  window.addEventListener('terminal:copy', onTerminalCopy)

  onTerminalPaste = (e: Event) => {
    if (!isActive.value) return
    const detail = (e as CustomEvent).detail
    if (detail?.panelId && detail.panelId !== props.panelId) return
    if (props.mode === 'ssh' || props.mode === 'local') {
      Clipboard.Text().then(text => {
        if (text) pasteToSession(text)
      }).catch(() => {})
    }
  }
  window.addEventListener('terminal:paste', onTerminalPaste)

  bindListeners()

  // When the browser tab/page becomes hidden (user switches to another app
  // or another browser tab), reset IME composition state. This prevents the
  // OS IME from continuing to feed characters into the hidden textarea,
  // which causes input duplication when the user returns.
  onVisibilityChange = () => {
    if (document.hidden && isActive.value) {
      resetIMEComposition()
    }
  }
  document.addEventListener('visibilitychange', onVisibilityChange)

  resizeObserver = new ResizeObserver(() => {
    // A size change landing inside a resize gate must not be dropped: if it
    // were the last event (e.g. maximize/restore right after a split-drag),
    // the terminal would keep its old pixel size — blank space below — with
    // no further trigger. Park a trailing resize that runs once the gate
    // clears; harmless if another handler (window debounce, native resize
    // end) already fits at the settled size.
    if (isResizing || splitResizing || Date.now() < suppressResizeUntil) {
      if (deferredResizeTimer) clearTimeout(deferredResizeTimer)
      deferredResizeTimer = setTimeout(() => {
        deferredResizeTimer = null
        if (isResizing || splitResizing || Date.now() < suppressResizeUntil) return
        resize()
      }, Math.max(0, suppressResizeUntil - Date.now()) + 150)
      return
    }
    const el = terminalRef.value
    if (!el) return
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => resize(), 150)
  })
  resizeObserver.observe(terminalRef.value)

  if (props.mode === 'ssh') {
    intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          resize()
        }
      })
    })
    intersectionObserver.observe(terminalRef.value)
  }
})

onActivated(() => {
  // Component restored from KeepAlive cache.

  nativeDrop.bind()

  // Replay session data that arrived while deactivated BEFORE
  // setting isActive = true. The session:data handler gates on
  // isActive, so new data would race with the gap replay and
  // advance writtenChunks, making the gap undetectable.
  // Uses a monotonic sequence number (getChunkCount), not an array
  // index, so front-trimming of the sessionStore buffer during a
  // long background session doesn't invalidate the tracking position.
  if (props.sessionId) {
    const total = sessionStore.getChunkCount(props.sessionId)
    if (total > writtenChunks) {
      const tail = sessionStore.getDataFromChunk(props.sessionId, writtenChunks)
      // Route the gap replay through the DCS reassembler like the live
      // path — a sixel sequence may span the deactivation boundary.
      for (const seg of dcsReassembler.feed(tail)) {
        writeStamped(seg.text)
      }
      writtenChunks = total
    }
  }

  // Sync retryOnEnter from stored session status. The session:status
  // event is guarded by isActive (which was false during deactivation),
  // so if the session disconnected while we were cached, retryOnEnter
  // was never set and Enter would do nothing despite the reconnect
  // message being replayed above.
  if (props.sessionId) {
    const st = sessionStore.getStatus(props.sessionId)
    if (st === 'disconnected' || st === 'error') {
      retryOnEnter = true
    }
  }

  isActive.value = true
  // Re-attach terminal element — another component may have moved it while
  // we were cached (e.g. merge→drag-out→re-merge keeps panelId, KeepAlive
  // reuses the cached BaseTerminal, but the terminal is in holding).
  if (terminalRef.value && props.sessionId) {
    attachTerminal(props.sessionId, terminalRef.value)
    nextTick(() => getFitAddon()?.fit())
  }
  // Re-register onData/keyHandler listeners that were disposed in onDeactivated.
  bindListeners?.()
  // Restore the user's scroll position captured on deactivation. Try once now
  // (cheap when layout already settled), then again after each resize() retry —
  // restoreSavedScroll() bails while render dimensions are still invalid, which
  // is the normal state right after KeepAlive activation.
  //
  // Terminal dimensions may also be stale after a tab switch; resize() bails
  // when the rect is 0×0, so it is retried on the same schedule. Both are
  // self-clearing: restoreSavedScroll() nulls the saved position once it lands
  // and returns true immediately afterwards.
  restoreSavedScroll()
  resize()
  ;[0, 50, 150, 300, 600].forEach(d => setTimeout(() => {
    resize()
    restoreSavedScroll()
  }, d))
  // Re-initialize zmodem service only if it was disposed in onDeactivated.
  // If a transfer was active, the service is still running — skip recreate.
  // safe: no focus() call here, avoids WebView2 crash race with native dialogs.
  if (props.sessionId && props.mode === 'ssh' && !zmodemService) {
    initZmodemService(props.sessionId)
  }
  // Note: focus() is intentionally skipped here. Calling focus() during
  // activation can race with native dialogs (OpenDirectoryDialog etc.)
  // and trigger a WebView2 crash (edge.Chromium.Focus parameter error).
})

onDeactivated(() => {
  // Component deactivated by KeepAlive (e.g. terminal tab moved into workspace).
  // Mark inactive so session event handlers become no-ops.
  nativeDrop.unbind()
  isActive.value = false
  // Reset IME composition state so the OS IME doesn't continue feeding
  // characters into the textarea while the terminal is hidden. Without
  // this, the stale composition state causes input duplication when the
  // user switches back (issue: IME offscreen duplicate input).
  resetIMEComposition()
  // Capture viewport position before listeners are torn down so reactivation
  // can restore the user's scroll position. Reading from the public IBuffer
  // API avoids depending on internal _core field shape.
  const buf = terminal?.buffer?.active as { viewportY?: number; baseY?: number } | undefined
  if (buf && typeof buf.viewportY === 'number') {
    savedViewportY = buf.viewportY
  }
  if (buf && typeof buf.baseY === 'number') {
    savedBaseY = buf.baseY
  }
  // Dispose per-component listeners to prevent duplicate input when another
  // BaseTerminal mounts with the same shared terminal instance.
  onDataDispose?.dispose()
  onDataDispose = null
  keyHandlerDispose?.dispose()
  keyHandlerDispose = null

  // If a transfer is still active, keep the service running so the background
  // transfer continues. Otherwise dispose and restore backend state.
  const hasStoreTransfer = zmodemStore.getActiveTransfer(props.sessionId || '')
  if (hasStoreTransfer) {
    return
  }
  disposeZmodemService(props.sessionId || '')
})

// Watch sessionId changes to rebind session data
watch(() => props.sessionId, (newId, oldId) => {
  if (oldId && oldId !== newId) {
    if (terminalRef.value) detachTerminal(oldId, terminalRef.value)
    disposeZmodemService(oldId)
    // Transfer the terminal to the new sessionId so scrollback is
    // preserved across reconnects. releaseTerminal is intentionally
    // skipped — we want to keep the same terminal instance alive.
    if (newId) transferTerminal(oldId, newId)
  }
  // Reset write tracking when session changes so onActivated replay
  // starts from the correct offset for the new session.
  writtenChunks = 0
  // Reset saved scroll position — the new sessionId has a different buffer.
  savedViewportY = null
  savedBaseY = null
  if (newId && (props.mode === 'ssh' || props.mode === 'local')) {
    initZmodemService(newId)
    terminal = getManagedTerminal(newId)?.terminal ?? null
    if (terminalRef.value) {
      attachTerminal(newId, terminalRef.value)
    }
    // Re-create terminalInput with the new terminal reference.
    // Otherwise it would still hold the old (disposed) terminal and
    // cursor position tracking returns {0,0}, pinning the suggestion
    // popup to the top-left corner.
    if (props.mode === 'ssh') {
      terminalInput = useTerminalInput(terminal, {
        mode: props.mode,
        sessionId: newId,
        enableHistory: true,  // was: smartOn
        onHistoryExtract: (command: string) => {
          suggestions.addHistoryCommand(command)
        },
        onResetSuppress: () => {
          suggestions.resetSuppress()
        },
      })
      suggestions.loadHistory()
    }
    // Re-bind onData/keyHandler on the new terminal
    bindListeners?.()
    const delays = [200, 400, 600, 800, 1000, 1500, 2000]
    delays.forEach((delay) => {
      setTimeout(() => resize(), delay)
    })
  }
})

// ── Search ──
const searchDecoOptions = {
  matchBackground: '#515c6e',
  matchBorder: '#22d3ee',
  matchOverviewRuler: '#22d3ee',
  activeMatchBackground: '#22d3ee44',
  activeMatchBorder: '#22d3ee',
  activeMatchColorOverviewRuler: '#22d3ee',
}

function openSearch() {
  searchVisible.value = true
  nextTick(() => {
    searchInputRef.value?.focus()
    if (searchText.value) {
      searchInputRef.value?.select()
      onSearchInput()
    }
  })
}

function closeSearch() {
  searchVisible.value = false
  searchText.value = ''
  // Toggle states (case / regex / whole-word) persist across opens
  searchResultIndex.value = 0
  searchResultCount.value = 0
  getSearchAddon()?.clearDecorations()
}

function searchOpts(): ISearchOptions {
  return {
    caseSensitive: searchCaseSensitive.value,
    regex: searchRegex.value,
    wholeWord: searchWholeWord.value,
    decorations: searchDecoOptions,
  }
}

function invalidRegex() {
  // The addon constructs RegExp directly without try/catch (SearchEngine.ts:289),
  // so guard here; an invalid pattern must not throw.
  if (!searchRegex.value) return false
  try {
    new RegExp(searchText.value)
    return false
  } catch {
    return true
  }
}

function clearSearchMatches() {
  searchResultIndex.value = 0
  searchResultCount.value = 0
  getSearchAddon()?.clearDecorations()
}

function onSearchInput() {
  if (!searchText.value || invalidRegex()) {
    clearSearchMatches()
    return
  }
  // Anchor the match at the bottom of the buffer (closest to the prompt);
  // Enter continues upward, Shift+Enter downward.
  getSearchAddon()?.findPrevious(searchText.value, searchOpts())
}

function onSearchEnter(e: KeyboardEvent) {
  if (e.shiftKey) {
    onSearchNext()
  } else {
    onSearchPrev()
  }
}

function onSearchNext() {
  if (!searchText.value || invalidRegex()) return
  getSearchAddon()?.findNext(searchText.value, searchOpts())
}

function onSearchPrev() {
  if (!searchText.value || invalidRegex()) return
  getSearchAddon()?.findPrevious(searchText.value, searchOpts())
}

function toggleSearchOption(key: 'caseSensitive' | 'regex' | 'wholeWord') {
  if (key === 'caseSensitive') searchCaseSensitive.value = !searchCaseSensitive.value
  else if (key === 'regex') searchRegex.value = !searchRegex.value
  else searchWholeWord.value = !searchWholeWord.value
  // Re-anchor at the bottom with the new options
  onSearchInput()
}

function applyXtermTheme(themeName: string) {
  if (!terminal) return
  const theme = resolveXtermBackground(
    getXtermTheme(resolveTerminalThemeName(themeName, settingsStore.resolvedAppTheme), settingsStore.settings.customTerminalThemes),
    localStateStore.state.backgroundEnabled,
    localStateStore.state.backgroundImage
  )
  terminal.options.theme = theme
  applyTerminalBgVar(terminal, theme)
  // Highlight colors are resolved from the palette per refresh — force a
  // pass so recolored text switches to the new theme immediately.
  notifyOverlayHighlightThemeChanged(terminal)
}

// Watch terminal settings changes
watch(() => settingsStore.settings.terminal, (ts) => {
  if (!terminal) return
  if (ts.fontSize) terminal.options.fontSize = ts.fontSize
  if (ts.fontFamily) terminal.options.fontFamily = formatFontFamily(ts.fontFamily, ts.fallbackFont)
  if (ts.fontWeight) terminal.options.fontWeight = ts.fontWeight
  if (ts.maxHistoryLines) terminal.options.scrollback = ts.maxHistoryLines
  if (ts.theme) applyXtermTheme(ts.theme)
  if (typeof ts.cursorBlink === 'boolean') {
    terminal.options.cursorBlink = ts.cursorBlink
    // xterm keeps an internal blink state set by DECSET 12; if the
    // terminal previously received \x1b[?12h from a remote shell, just
    // flipping the option may not stop the running blink animation.
    // Force-reset by feeding the cursor a DECRST 12 sequence.
    if (!ts.cursorBlink) terminal.write('\x1b[?12l')
  }
  if (ts.wordSeparator) {
    // xterm reads wordSeparator on each selection via rawOptions; assigning
    // here is enough to change the next double-click selection without
    // recreating the terminal.
    terminal.options.wordSeparator = ts.wordSeparator
  }
  // Live minimum-contrast (F-039): xterm reads it on each render, so a plain
  // assignment re-evaluates the atlas without recreating the terminal.
  if (typeof ts.minimumContrast === 'number') {
    terminal.options.minimumContrastRatio = ts.minimumContrast
  }
  // Live cursorStyle is applied by xterm on the next cursor render.
  if (ts.cursorStyle) terminal.options.cursorStyle = ts.cursorStyle
  resize()
}, { deep: true })

// Watch for background image toggling to update terminal transparency
watch(
  () => localStateStore.state.backgroundEnabled,
  () => applyXtermTheme(settingsStore.settings.terminal.theme || 'dark')
)

// Re-apply when the app theme flips so FOLLOW_APP_THEME tracks it live.
watch(
  () => settingsStore.resolvedAppTheme,
  () => applyXtermTheme(settingsStore.settings.terminal.theme || 'dark')
)

// Detach terminal before Vue nulls template refs.
// In Vue 3, onUnmounted fires AFTER template refs are set to null,
// so detachTerminal would see terminalRef.value === null and skip.
// onBeforeUnmount fires while refs are still valid.
onBeforeUnmount(() => {
  if (props.sessionId && terminalRef.value) {
    detachTerminal(props.sessionId, terminalRef.value)
  }
})

onUnmounted(() => {
  nativeDrop.unbind()
  resizeObserver?.disconnect()
  intersectionObserver?.disconnect()
  touchPanStop()
  if (deferredResizeTimer) {
    clearTimeout(deferredResizeTimer)
    deferredResizeTimer = null
  }

  // Dispose per-component listeners BEFORE releasing terminal.
  // The terminal instance may outlive this component if another
  // component still holds a reference.
  onDataDispose?.dispose()
  onDataDispose = null
  keyHandlerDispose?.dispose()
  keyHandlerDispose = null

  // Release reference (delayed dispose: terminal survives 500ms)
  if (props.sessionId) {
    releaseTerminal(props.sessionId, terminalInstanceRef)
  }

  unsubscribe?.()
  statusUnsubscribe?.()
  if (onDocumentMouseDown) {
    document.removeEventListener('mousedown', onDocumentMouseDown)
    onDocumentMouseDown = null
  }
  if (onTerminalAuxClick) {
    document.removeEventListener('auxclick', onTerminalAuxClick)
    onTerminalAuxClick = null
  }
  window.removeEventListener('resize', onWindowResize)
  window.removeEventListener('split:resize-start', onSplitResizeStart)
  window.removeEventListener('split:resize-end', onSplitResizeEnd)
  unsubNativeResizeEnd?.()
  unsubNativeResizeEnd = null
  if (onOpenSearch) window.removeEventListener('terminal:open-search', onOpenSearch)
  if (onExport) window.removeEventListener('terminal:export', onExport)
  if (onSendRz) window.removeEventListener('terminal:send-rz', onSendRz)
  if (onTerminalCopy) window.removeEventListener('terminal:copy', onTerminalCopy)
  if (onTerminalPaste) window.removeEventListener('terminal:paste', onTerminalPaste)
  if (onVisibilityChange) document.removeEventListener('visibilitychange', onVisibilityChange)
  onVisibilityChange = null
  suggestions.close()
  if (!zmodemStore.getActiveTransfer(props.sessionId || '')) {
    disposeZmodemService(props.sessionId || '')
  }
})

// Paste handling
function pasteToTerminal(text: string) {
  if (props.mode === 'sftp' && terminal) {
    for (const char of text) {
      const code = char.charCodeAt(0)
      if (code >= 32 && code <= 126) {
        inputBuffer += char
        terminal.write(char)
      }
    }
  }
}

async function pasteToSession(text: string) {
  if (props.mode === 'ssh' || props.mode === 'local') {
    // Normalize line endings (CRLF -> LF, drop stray CR) so pasting into
    // editors like vim doesn't double newlines (Windows clipboard has \r\n).
    const normalized = normalizePastedText(text)

    // Broadcast mode: write to every target panel instead of only this
    // session (issue #597 — pasted command must sync like keyboard input).
    if (props.broadcastActive) {
      const targets = tabStore.getAllBroadcastPanelIds()
      if (targets.length > 0) {
        for (const pid of targets) {
          const p = panelStore.getPanel(pid)
          const managed = p?.sessionId ? getManagedTerminal(p.sessionId) : undefined
          if (p?.sessionId && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl') && managed) {
            // Bracket per target session — each has its own paste mode.
            // Scroll each target's viewport to the bottom too, so broadcast
            // paste behaves like keyboard input everywhere (issue 629).
            pasteWithScroll(
              {
                bracketedPasteMode: managed.terminal.modes.bracketedPasteMode,
                write: (payload) => queuedSessionWrite(p.sessionId, payload),
                scrollToBottom: () => managed.terminal.scrollToBottom(),
              },
              normalized,
            )
          }
        }
        return
      }
    }

    const sid = props.sessionId
    if (sid) {
      const managed = getManagedTerminal(sid)
      pasteWithScroll(
        {
          bracketedPasteMode: managed?.terminal.modes.bracketedPasteMode ?? false,
          write: (payload) => queuedSessionWrite(sid, payload),
          scrollToBottom: () => terminal?.scrollToBottom(),
        },
        normalized,
      )
    }
  }
}

// ── Terminal right-click menu context (mirrors the tab-level menu) ──
const panel = computed(() => (props.panelId ? panelStore.getPanel(props.panelId) : undefined))
const isSsh = computed(() => panel.value?.type === 'ssh')
const supportsOutputLog = computed(() =>
  !!panel.value && ['ssh', 'telnet', 'serial', 'mosh', 'local', 'wsl'].includes(panel.value.type),
)

const isOutputLogOn = ref(false)
const outputLogPath = ref('')

async function refreshOutputLogState() {
  const pid = props.panelId
  const p = panel.value
  if (!pid || !p) {
    isOutputLogOn.value = false
    outputLogPath.value = ''
    return
  }
  try {
    const info = await GetSessionOutputLogInfo(pid)
    isOutputLogOn.value = !!info.enabled
    outputLogPath.value = info.path || ''
    panelStore.setOutputLog(pid, { enabled: isOutputLogOn.value, path: outputLogPath.value })
  } catch {
    isOutputLogOn.value = false
    outputLogPath.value = ''
  }
}

function onTerminalContextMenu(e: MouseEvent) {
  // Right-click on the gutter (line-number/time columns) opens the gutter
  // toggle menu instead of the terminal menu. The gutter itself is
  // pointer-events: none, so the event surfaces on .terminal-area and is
  // routed here by hit-testing the click position against the gutter rect.
  if (showLineNumbers.value || showTimestamps.value) {
    const g = gutterRef.value?.$el as HTMLElement | null
    const r = g?.getBoundingClientRect()
    if (r && e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom) {
      e.preventDefault()
      gutterMenuRef.value?.openAt(e.clientX, e.clientY)
      return
    }
  }
  if (supportsOutputLog.value) {
    refreshOutputLogState()
  }
  menu.onContextMenu(e)
}

function triggerSearch() {
  menu.closeMenu()
  openSearch()
}

async function toggleOutputLog() {
  menu.closeMenu()
  const pid = props.panelId
  if (!pid) return
  try {
    if (isOutputLogOn.value) {
      await DisableSessionOutputLog(pid)
      isOutputLogOn.value = false
      const prev = outputLogPath.value
      outputLogPath.value = ''
      panelStore.setOutputLog(pid, { enabled: false, path: '' })
      msg.copyable(t('session.logStopped', { path: prev }), 'info')
      return
    }
    const path = await EnableSessionOutputLog(pid, '')
    if (!path) {
      msg.error(t('session.logFailed', { error: 'unknown' }))
      return
    }
    isOutputLogOn.value = true
    outputLogPath.value = path
    panelStore.setOutputLog(pid, { enabled: true, path })
    msg.copyable(t('session.logStarted', { path }), 'success')
  } catch (e: any) {
    msg.error(t('session.logFailed', { error: String(e?.message ?? e) }))
  }
}

async function openLogDir() {
  menu.closeMenu()
  if (!outputLogPath.value) return
  try {
    await OpenPathInExplorer(outputLogPath.value)
  } catch (e: any) {
    msg.error(String(e?.message ?? e))
  }
}

function openSftp() {
  menu.closeMenu()
  const p = panel.value
  if (p) {
    window.dispatchEvent(new CustomEvent('app:connect-sftp', { detail: p }))
  }
}

function uploadFileRz() {
  window.dispatchEvent(new CustomEvent('terminal:send-rz', { detail: { panelId: props.panelId } }))
  menu.closeMenu()
}

function openMonitor() {
  menu.closeMenu()
  const p = panel.value
  if (p) {
    window.dispatchEvent(new CustomEvent('app:connect-monitor', { detail: p }))
  }
}

const terminalMenuRef = ref<InstanceType<typeof Menu> | null>(null)
// Gutter context menu (right-click on the line-number/time columns) and the
// gutter component ref, for hit-testing where a right-click landed.
const gutterMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const gutterMenuVisible = ref(false)
const gutterRef = ref<{ $el: HTMLElement } | null>(null)
const menu = useTerminalMenu({
  getSelection,
  openAt: (x, y) => terminalMenuRef.value?.openAt(x, y),
  onPaste: async (text) => {
    if (props.mode === 'ssh' || props.mode === 'local') {
      await pasteToSession(text)
    } else {
      pasteToTerminal(text)
    }
    // Restore focus after paste so the cursor stays active in the terminal
    focus()
  },
})

// `menu.menuVisible` is a ref nested in a plain object, so the template would
// not auto-unwrap it — `v-model:visible="menu.menuVisible"` would hand the raw
// Ref (always truthy) to <Menu> and the menu could never hide. Route v-model
// through a top-level computed instead so get/set both hit the real boolean.
const terminalMenuVisible = computed({
  get: () => menu.menuVisible.value,
  set: (v: boolean) => { menu.menuVisible.value = v },
})

defineExpose({
  getSelection,
  resize,
  focus,
  write,
  setRetryOnEnter,
})
</script>

<style scoped>
.base-terminal {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}
.terminal-area {
  flex: 1;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}
.terminal-host {
  flex: 1;
  min-width: 0;
  min-height: 0;
  /* `clip` (not `hidden`): a hidden box is still programmatically scrollable,
   * so a focus()-driven auto-scroll during a resize transition could leave a
   * stale scrollTop here and shove the whole .xterm up, leaving blank space
   * below (it is never scrolled deliberately — xterm scrolls its own layers).
   * `clip` makes the box a non-scroll-container, so the offset cannot exist. */
  overflow: clip;
  position: relative;
}

/* Search bar */
.terminal-search-bar {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  /* 跟应用主题走（与 Zmodem 面板、终端建议弹窗等悬浮控件一致）；
     保留 88% 不透明度，让 blur 透出一点终端内容。 */
  background: color-mix(in srgb, var(--bg-surface) 88%, transparent);
  backdrop-filter: blur(0.5rem);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.25rem 0.375rem;
  z-index: 50;
}
.search-input {
  width: 10rem;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.125rem 0.25rem;
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-count {
  font-family: var(--font-mono);
  font-size: 0.6875rem;
  color: var(--text-muted);
  white-space: nowrap;
  min-width: 2rem;
  text-align: center;
}
.search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.375rem;
  height: 1.375rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.search-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.search-btn.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
.terminal-area :deep(.xterm) {
  width: 100%;
  height: 100%;
  display: block;
  box-sizing: border-box;
  /* 右侧不留：那 0.875rem 的滚动条轨道本身已把文本挡开（文本右缘与轨道间还有 0.125rem），
     右 padding 只会把整条滚动条往左推、在轨道外侧留一条空白。 */
  padding: 0.25rem 0 0.25rem 0.25rem;
}
/* 0.25rem padding 那圈用终端背景色，而不是应用主题色（--bg-base）。
   v5 时 xterm 把终端色内联在 .xterm-viewport 上，而它 absolute inset:0
   盖满 padding box，边缘因此自带终端色；v6 改成内联到 .xterm-scrollable-element，
   该元素止于 padding 内侧，边缘便露出 .xterm 自身的应用主题色 ——
   深色应用 + 浅色终端时就是一圈深色边框。--terminal-bg 由
   applyTerminalBgVar() 写在终端根元素上，取不到时回退旧行为。 */
.terminal-area :deep(.xterm),
.terminal-area :deep(.xterm-viewport) {
  background: var(--terminal-bg, var(--bg-base));
}
/* v6 起 .xterm-viewport 只是 overview ruler 的定位锚点，不再是滚动容器；
   留着 overflow-y: scroll 会多出一条空的原生轨道。终端滚动条样式见
   style.css 里的 .xterm-scrollable-element > .scrollbar 规则。 */
.terminal-area :deep(.xterm-viewport) {
  overflow: hidden;
}

.drop-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--scrim);
  pointer-events: none;
}
.drop-overlay span {
  font-size: 0.875rem;
  color: var(--text-primary);
  padding: 0.75rem 1.5rem;
  border: 0.125rem dashed var(--border-hover);
  border-radius: var(--radius-md);
}
</style>
