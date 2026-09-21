import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@fontsource-variable/jetbrains-mono'
import { ElDialog } from 'element-plus'
import App from './App.vue'
import './style.css'
import { Window } from '@wailsio/runtime'
import { useSettingsStore } from './stores/settingsStore'
import { setLocale } from './i18n'

Window.SetTitle('终端')

// Set ElDialog draggable by default
if (ElDialog.props) {
  ElDialog.props.draggable = { type: Boolean, default: true }
}

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)

const settingsStore = useSettingsStore()
// Sync locale from navigator before mount (default 'system' → resolves from
// navigator.language, zero IPC) so the first paint is already in the user's
// language; init() re-resolves with the persisted preference once loaded.
setLocale('system')
// Fire settings init without awaiting: top-level await here used to block the
// module's completion, which delayed the page load event, which delayed Wails'
// window Show() — seconds of dock-icon-but-no-window on slow first paint. All
// settings consumers are reactive (computed/watch/template), so values apply
// themselves once init lands. applyTheme() on the loaded defaults runs before
// mount anyway (init() calls it synchronously after its awaits settle).
settingsStore.init()

app.mount('#app')

// Global IME guard: swallow keydown/keyup events consumed by an IME
// composition (e.g. Enter confirming a candidate word) before any
// element-level handler mistakes them for app shortcuts. xterm terminals are
// exempt — they manage their own IME pipeline.
//
// keydown: isComposing is the standard signal; keyCode 229 is the phantom code
// WKWebView reports for composition keystrokes where isComposing is unreliable.
//
// keyup: the commit key's keyup arrives AFTER compositionend, so isComposing
// is already false there. Track state via composition events instead: while
// composing, keyups are blocked; on compositionend exactly one keyup (the
// commit key's) is blocked. A real (non-IME) keydown disarms the pending
// swallow, so a mouse-click commit (no keyup) cannot swallow the user's next
// keystroke.
{
  const inTerminal = (t: EventTarget | null) =>
    !!(t as Element | null)?.closest?.('.xterm')
  let inComposition = false
  let swallowNextKeyup = false

  document.addEventListener('keydown', (e) => {
    if (inTerminal(e.target)) return
    // keyCode is deprecated, but 229 is kept deliberately: WKWebView (macOS)
    // reports composition keystrokes as the phantom keyCode 229, and `key`
    // ("Process") is not reliably set there.
    if (e.isComposing || e.key === 'Process' || e.keyCode === 229) {
      e.stopPropagation()
      return
    }
    // A real keystroke invalidates a pending swallow.
    swallowNextKeyup = false
  }, true)

  document.addEventListener('compositionstart', () => {
    inComposition = true
    swallowNextKeyup = false
  }, true)

  document.addEventListener('compositionend', () => {
    inComposition = false
    swallowNextKeyup = true
  }, true)

  document.addEventListener('keyup', (e) => {
    if (inTerminal(e.target)) return
    if (inComposition || swallowNextKeyup) {
      swallowNextKeyup = false
      e.stopPropagation()
    }
  }, true)
}

// Global context menu closer: broadcast to all menu components via window event
document.addEventListener('contextmenu', () => {
  window.dispatchEvent(new CustomEvent('global:close-context-menus'))
}, true)

interface EditableSelectionSnapshot {
  target: HTMLElement
  start?: number | null
  end?: number | null
  range?: Range
}

const isEditableTarget = (target: EventTarget | null): target is HTMLElement => {
  if (!(target instanceof HTMLElement)) return false
  return target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
}

let rightClickSelection: EditableSelectionSnapshot | null = null

function captureEditableSelection(target: HTMLElement): EditableSelectionSnapshot {
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
    const input = target as HTMLInputElement | HTMLTextAreaElement
    return { target, start: input.selectionStart, end: input.selectionEnd }
  }
  const selection = window.getSelection()
  if (selection && selection.rangeCount > 0) {
    const range = selection.getRangeAt(0)
    if (target.contains(range.commonAncestorContainer)) {
      return { target, range: range.cloneRange() }
    }
  }
  return { target }
}

function restoreEditableSelection(snapshot: EditableSelectionSnapshot) {
  const { target } = snapshot
  target.focus()
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
    const input = target as HTMLInputElement | HTMLTextAreaElement
    if (typeof snapshot.start === 'number' && typeof snapshot.end === 'number') {
      input.setSelectionRange(snapshot.start, snapshot.end)
    }
    return
  }
  if (snapshot.range) {
    const selection = window.getSelection()
    selection?.removeAllRanges()
    selection?.addRange(snapshot.range.cloneRange())
  }
}

document.addEventListener('mousedown', (e) => {
  if (e.button !== 2 || !isEditableTarget(e.target)) {
    if (e.button === 0) rightClickSelection = null
    return
  }
  const target = e.target
  rightClickSelection = captureEditableSelection(target)
  e.preventDefault()
}, true)

document.addEventListener('select', (e) => {
  const target = e.target
  if (rightClickSelection?.target === target &&
      (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) {
    const sel = target as HTMLInputElement | HTMLTextAreaElement
    if (typeof rightClickSelection.start === 'number' &&
        typeof rightClickSelection.end === 'number' &&
        (sel.selectionStart !== rightClickSelection.start ||
         sel.selectionEnd !== rightClickSelection.end)) {
      restoreEditableSelection(rightClickSelection)
    }
  }
}, true)

document.addEventListener('contextmenu', (e) => {
  const target = e.target as HTMLElement
  // Read-only log-path toast: offer copy/select-all on its plain text.
  const copyable = target.closest('.msg-copyable') as HTMLElement | null
  if (copyable) {
    e.preventDefault()
    const content = (copyable.querySelector('.el-message__content') as HTMLElement) || copyable
    window.dispatchEvent(new CustomEvent('input:contextmenu', {
      detail: { x: e.clientX, y: e.clientY, target: content, readonly: true }
    }))
    return
  }
  const tag = target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || target.isContentEditable) {
    e.preventDefault()
    if (rightClickSelection?.target === target) {
      restoreEditableSelection(rightClickSelection)
    }
    rightClickSelection = null
    window.dispatchEvent(new CustomEvent('input:contextmenu', {
      detail: { x: e.clientX, y: e.clientY, target }
    }))
    return
  }
  e.preventDefault()
})
