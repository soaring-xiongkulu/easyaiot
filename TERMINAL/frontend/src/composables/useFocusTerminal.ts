/**
 * Terminal-focus helpers shared across the app.
 *
 * xterm.js listens for keystrokes on an internal <textarea class="xterm-helper-textarea">.
 * To type into a terminal it must be the document's active element. Any UI action
 * that writes to a session — quick commands, history replay, paste — should
 * restore that focus so the user can immediately press Enter without an extra
 * click. And chrome-only mouse gestures (dragging the frameless window, clicking
 * the sidebar scrollbar) must not steal focus away from the terminal either.
 *
 * All lookups are DOM-based (via `[data-panel-id="..."]`) so we avoid the ref
 * plumbing that would be needed to reach BaseTerminal from unrelated components.
 */

import { useTabStore } from '../stores/tabStore'
import { useSettingsStore } from '../stores/settingsStore'
import { watch } from 'vue'

// Bounded backoff for focus recovery: 0/50/150/300ms (~500ms total, 4 polls
// instead of 11). Most xterm-helper-textarea appearances resolve inside one
// rAF; the trailing 300ms catches slow KeepAlive + drag re-mounts without
// the previous 1s of 10 Hz polling.
const FOCUS_RETRY_DELAYS = [0, 50, 150, 300]
const FOCUS_RETRY_MAX = FOCUS_RETRY_DELAYS.length

/**
 * Focus the terminal in the given panel. Retries with backoff because
 * xterm's internal textarea can be temporarily absent right after a
 * KeepAlive re-mount or during a session reconnect.
 */
export function focusPanelTerminal(panelId: string, attempt = 0) {
  if (attempt >= FOCUS_RETRY_MAX) return
  const el = document.querySelector(`[data-panel-id="${panelId}"] .xterm-helper-textarea`)
  if (el instanceof HTMLTextAreaElement) {
    el.focus()
  } else {
    const delay = FOCUS_RETRY_DELAYS[attempt]
    setTimeout(() => focusPanelTerminal(panelId, attempt + 1), delay)
  }
}

/** Focus the terminal in the currently active panel of the active tab. */
export function focusActivePanelTerminal() {
  const tabStore = useTabStore()
  const panelId = tabStore.getActivePanelId()
  if (panelId) focusPanelTerminal(panelId)
}

/**
 * Install a document-level guard that restores terminal focus after mouse
 * gestures that would otherwise steal it from xterm without the user meaning to
 * — dragging the frameless window by the header, or dragging the sidebar
 * scrollbar. Genuine clicks on interactive controls (buttons, inputs, links)
 * are left alone; they change focus intentionally.
 *
 * Runs on `window` in the capture phase so the check fires before any
 * component handlers, and only arms the mouseup restore when focus was on a
 * terminal at mousedown time.
 *
 * Returns a teardown function.
 */
export function installTerminalFocusRestore(): () => void {
  // Element Plus renders its select/dropdown trigger as a plain <div>
  // (.el-select__wrapper) and teleports the option list to <body> as
  // .el-popper — neither is a native control, so list them explicitly or the
  // focus guard steals focus back to the terminal and the dropdown never opens.
  // .msg-copyable is the log-path toast: leaving it alone keeps a text selection
  // alive so it can be copied instead of being cleared by a terminal refocus.
  const INTERACTIVE_SEL = 'input, textarea, select, button, a, [role="button"], [role="combobox"], [contenteditable="true"], .xterm-helper-textarea, .el-select__wrapper, .el-input__wrapper, .el-popper, .msg-copyable'

  // Walk ancestors looking for the --wails-draggable custom property so we
  // can tell a frameless-window drag region apart from ordinary chrome. Any
  // ancestor tagged `no-drag` short-circuits to false — same precedence Wails
  // itself uses when deciding whether to hand the mouse to the OS.
  //
  // getComputedStyle().getPropertyValue forces a style recalc, so cache each
  // visited element's verdict in a WeakMap. Drag regions are set in CSS at
  // page load and do not change at runtime; the cache is replaced wholesale
  // when theme/setting changes potentially alter resolved custom-property
  // values.
  let draggableCache: WeakMap<HTMLElement, boolean> = new WeakMap()
  const invalidateDraggableCache = () => {
    draggableCache = new WeakMap()
  }
  const isWailsDraggable = (el: HTMLElement | null): boolean => {
    let cur = el
    while (cur) {
      const cached = draggableCache.get(cur)
      if (cached !== undefined) return cached
      const val = getComputedStyle(cur).getPropertyValue('--wails-draggable').trim()
      if (val === 'drag') {
        draggableCache.set(cur, true)
        return true
      }
      if (val === 'no-drag') {
        draggableCache.set(cur, false)
        // explicit no-drag on this ancestor still allows a `drag` ancestor
        // further up to win — same precedence Wails uses internally
      }
      cur = cur.parentElement
    }
    return false
  }

  const onMouseDown = (e: MouseEvent) => {
    const active = document.activeElement
    const wasTerminal = active instanceof HTMLElement &&
      active.classList.contains('xterm-helper-textarea')
    if (!wasTerminal) return

    const target = e.target as HTMLElement | null
    // If the press lands on an interactive control the user is deliberately
    // moving focus — do not fight it.
    if (target && target.closest(INTERACTIVE_SEL)) return

    const capturedPanelId = active.closest('[data-panel-id]')?.getAttribute('data-panel-id') || null

    // Focusing xterm's helper textarea clears the document selection, so a
    // drag that selected text anywhere (AI messages, SFTP listings, query
    // results) must not be treated as accidental focus loss. xterm keeps its
    // own selection model outside the DOM, so this never sees a terminal's
    // own selection and can't disarm the guard for it.
    const hasTextSelection = () => {
      const sel = window.getSelection()
      return !!sel && !sel.isCollapsed && sel.toString().trim() !== ''
    }

    const restore = () => {
      if (hasTextSelection()) return
      const now = document.activeElement
      if (now instanceof HTMLElement && now.classList.contains('xterm-helper-textarea')) {
        return // browser kept us on the terminal, nothing to do
      }
      // Focus legitimately moved to an editable field (e.g. the tab-rename
      // input, opened from a menu item that isn't in INTERACTIVE_SEL) — don't
      // yank it back to the terminal, or renaming can never take focus.
      if (now instanceof HTMLElement &&
          (now.tagName === 'INPUT' || now.tagName === 'TEXTAREA' || now.isContentEditable)) {
        return
      }
      if (capturedPanelId) {
        focusPanelTerminal(capturedPanelId)
      } else {
        focusActivePanelTerminal()
      }
    }

    // Frameless-window drag: as soon as mousedown fires inside a
    // --wails-draggable: drag region, WebView2 hands the mouse to the OS and
    // no mouseup ever reaches the DOM. Fall back to a short-delay reclaim
    // instead of waiting on an event that will never arrive.
    if (isWailsDraggable(target)) {
      setTimeout(restore, 100)
      return
    }

    // Otherwise (sidebar scrollbar, empty regions) we can wait for the real
    // mouseup so we don't fight the browser's own focus bookkeeping mid-drag.
    const onUp = () => {
      window.removeEventListener('mouseup', onUp, true)
      // Defer so the browser has finished its own focus bookkeeping for the
      // gesture before we try to reclaim.
      setTimeout(restore, 0)
    }
    window.addEventListener('mouseup', onUp, true)
  }

  window.addEventListener('mousedown', onMouseDown, true)
  // --wails-draggable is set in CSS, but theme swaps can re-resolve custom
  // properties on existing elements. Drop the cache so the next click pays
  // the (now-cheap) one-time walk and re-caches.
  const settingsStore = useSettingsStore()
  const stopWatch = watch(
    () => settingsStore.settings.theme,
    () => invalidateDraggableCache()
  )
  return () => {
    window.removeEventListener('mousedown', onMouseDown, true)
    stopWatch()
  }
}
