<template>
  <Teleport to="body">
    <div
      v-show="visible"
      ref="menuEl"
      class="conn-context-menu"
      :class="[{ 'mirror-left': mirrorLeft, overflow: overflow }, rootClass]"
      :style="menuStyle"
      @mouseover="onInnerMouseOver"
      @mouseleave="submenu.active = ''"
      @contextmenu.stop
    >
      <slot :current="current" />
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, provide, watch, nextTick } from 'vue'

// Single unified menu. Covers every showed-panel style of menu the app uses:
//   - flat button trigger    → toggle(anchorEl, data) / open(anchorEl, data)
//   - right-click / pointer  → openAt(x, y, data)
//   - nested submenus        → render .submenu-wrap rows in the slot; the active
//                               flyout key is the `submenu` slot prop ({ active }).
// The .conn-context-menu skin lives once in style.css, reused by everything.

// ── Global single-open coordinator (module scope, shared across ALL <Menu>s) ──
// Only the most recently opened menu stays open: opening one closes whatever was
// open before, and ONE shared document listener dismisses the active menu on
// outside-click / Escape. Defined here once so hosts never reimplement it.
// Note: per/future migration this also broadcasts so non-Menu popovers close.
interface ActiveMenu { el: () => HTMLElement | null; close: () => void }
let active: ActiveMenu | null = null
let docBound = false

// ── RDP overlay coordination ──
// The RDP ActiveX native window sits above the webview layer and occludes
// HTML-rendered menus. Every Menu instance hides the RDP window when it opens
// and restores it when it closes. A reference counter handles overlapping
// transitions (one menu closing as another opens): the push fires on the first
// open, the pop only on the last close.
let menuOpenCount = 0

// Close the active menu whenever any surface broadcasts the legacy
// global:close-context-menus event (opening a dialog, RDP overlay push,
// keyboard nav, etc.). Centralized here so no host re-subscribes to force-close
// menus — single-open + this event is the whole close story.
window.addEventListener('global:close-context-menus', () => { active?.close() })

function activate(m: ActiveMenu) {
  // Right-click menus close each other because main.ts dispatches the global
  // close signal on every `contextmenu` (capture) before the new menu opens.
  // Broadcast the same signal here when taking over a *different* menu so a
  // button-triggered open closes everything too — this is the close-other path
  // that's actually proven to fire. Dispatch BEFORE switching `active` so the
  // signal closes the previous menu, not this one.
  //
  // Re-activating the SAME menu (open()/openAt() emit `update:visible` true and
  // the visible-prop watcher ALSO calls activate) must NOT push/ref-count again,
  // otherwise menuOpenCount never returns to 0 and the pop that restores the RDP
  // window never fires — the RDP stays on top and occludes every later menu.
  if (active === m) {
    // Already the active menu: ensure the shared dismiss listeners are bound,
    // then bail — this is the watcher's duplicate call.
    if (!docBound) {
      document.addEventListener('click', onDocClick)
      document.addEventListener('keydown', onDocKeydown)
      docBound = true
    }
    return
  }
  window.dispatchEvent(new Event('global:close-context-menus'))
  active?.close()
  active = m
  if (!docBound) {
    document.addEventListener('click', onDocClick)
    document.addEventListener('keydown', onDocKeydown)
    docBound = true
  }
  // Hide the native RDP window so menus aren't occluded (first open only).
  if (menuOpenCount === 0) {
    window.dispatchEvent(new CustomEvent('rdp:overlay-push'))
  }
  menuOpenCount++
}
function deactivate(m: ActiveMenu) {
  if (active === m) active = null
  menuOpenCount = Math.max(0, menuOpenCount - 1)
  // Restore the RDP window only after the last menu closes.
  if (menuOpenCount === 0) {
    window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
  }
}

// Bubble-phase outside-click close. Trigger buttons use @click.stop so their own
// click only runs toggle(); anything that bubbles past the open menu closes it.
function onDocClick(e: MouseEvent) {
  if (!active) return
  const el = active.el()
  if (el && !el.contains(e.target as Node)) active.close()
}
function onDocKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') active?.close()
}

const props = defineProps<{
  visible: boolean
  align?: 'start' | 'end'
  /** Extra class(es) merged onto the teleported root; lets hosts keep
   *  per-menu skin modifiers. */
  rootClass?: string
}>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
}>()

const menuEl = ref<HTMLElement | null>(null)
const menuStyle = ref({ top: '-9999px', left: '-9999px' })
// Submenu fly direction is computed per-position from the window edges (which
// side has more room), not from the static align. See position().
const mirrorLeft = ref(false)
// True when the menu is taller than the viewport: scroll inside the container
// instead of letting the window clip the bottom. Only set in that state —
// overflow != visible would clip the absolutely positioned submenu flyouts
// even when nothing actually overflows, so menus that fit must stay untouched.
const overflow = ref(false)
const current = ref<unknown>()
// Writable submenu state shared with descendant <MenuSubmenu> rows via provide;
// MenuSubmenu sets `active` on hover and reads it to show/hide its flyout.
const submenu = reactive({ active: '' as string })
provide('menuSubmenu', submenu)

const closeFn = () => emit('update:visible', false)
const menuController: ActiveMenu = { el: () => menuEl.value, close: closeFn }

function position(x: number, y: number) {
  const m = menuEl.value
  if (!m) return
  const mr = m.getBoundingClientRect()
  overflow.value = mr.height > window.innerHeight - 8
  menuStyle.value = {
    left: Math.max(4, Math.min(x, window.innerWidth - mr.width - 4)) + 'px',
    top: Math.max(4, Math.min(y, window.innerHeight - mr.height - 4)) + 'px',
  }
  // Seed the submenu fly side with the menu's own width as a stand-in for the
  // projected flyout width; refiners the exact fit once a flyout actually opens
  // (see the submenu.active watcher below). The rule: fly RIGHT by default, and
  // only mirror LEFT when the right side cannot fit the flyout but the left can.
  // In overflow mode always fly LEFT over the parent menu: a rightward flyout
  // would be clipped by the scroll container's overflow-x.
  const placed = m.getBoundingClientRect()
  mirrorLeft.value = overflow.value || shouldMirror(placed, placed.width)
}

// Decide whether a flyout must open leftward instead of the default rightward:
// fit on the right first; fall back to the left only if the right doesn't have
// room but the left does. Never mirrors just because one side has "more" room.
function shouldMirror(placed: DOMRect, flyoutWidth: number): boolean {
  const edge = 4
  const fitsRight = placed.right + flyoutWidth <= window.innerWidth - edge
  const fitsLeft = placed.left - flyoutWidth >= edge
  return !fitsRight && fitsLeft
}

// Flat menu anchored below a trigger button.
function open(anchorEl: HTMLElement, data?: unknown) {
  current.value = data
  emit('update:visible', true)
  // Close any other open menu synchronously at open-time (not deferred to the
  // async visible-prop watcher) so a button-triggered open behaves exactly like
  // a right-click one and always drops the previously-open menu.
  activate(menuController)
  nextTick(() => {
    const m = menuEl.value
    if (!anchorEl || !m) return
    const br = anchorEl.getBoundingClientRect()
    const mr = m.getBoundingClientRect()
    const gap = 4
    // Open below the trigger: `start` left-aligns the menu to the button's left
    // edge, `end` right-aligns it to the button's right edge (x = right - width).
    // Using the button's right as the menu's LEFT edge (the old code) shifted the
    // whole menu off to the button's corner instead of directly under it.
    const x = props.align === 'end' ? br.right - mr.width : br.left
    // Open downward below the trigger; flip upward when it would run past the
    // bottom edge of the window so the menu never gets clipped at the edge.
    let y = br.bottom + gap
    if (y + mr.height > window.innerHeight - gap) {
      y = Math.max(gap, br.top - mr.height - gap)
    }
    position(x, y)
  })
}

// Right-click menu positioned at a pointer/X-Y coordinate.
function openAt(x: number, y: number, data?: unknown) {
  current.value = data
  emit('update:visible', true)
  // See open(): close others synchronously instead of waiting on the watcher.
  activate(menuController)
  nextTick(() => position(x, y))
}

function toggle(anchorEl: HTMLElement, data?: unknown) {
  if (props.visible) {
    emit('update:visible', false)
  } else {
    open(anchorEl, data)
  }
}

defineExpose({ open, openAt, toggle, close: closeFn })

// Hovering anywhere outside a submenu-wrap or its open flyout collapses it.
function onInnerMouseOver(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (!t.closest('.submenu-wrap') && !t.closest('.menu-submenu')) {
    submenu.active = ''
  }
}

// When a flyout actually opens, refine the fly side with its real width instead
// of the parent-width estimate used in position().
watch(() => submenu.active, (key) => {
  if (!key) return
  nextTick(() => {
    const m = menuEl.value
    const fly = m?.querySelector('.menu-submenu') as HTMLElement | null
    if (!m || !fly) return
    const fw = fly.getBoundingClientRect().width
    if (fw) mirrorLeft.value = overflow.value || shouldMirror(m.getBoundingClientRect(), fw)
  })
})

watch(() => props.visible, (v) => {
  if (v) {
    activate(menuController)
  } else {
    deactivate(menuController)
    current.value = undefined
    submenu.active = ''
  }
})
</script>

<!-- Non-scoped so the rules still reach the building-block rows
     (.menu-item / .menu-divider / .menu-submenu) rendered by child components
     (MenuItem / MenuDivider / MenuSubmenu) nested inside the menu's slot. -->
<style>
/* ── Unified context-menu styling (single source of truth) ─────────────
   Every right-click / popover / dropdown menu in the app should reuse these
   classes instead of defining its own look. All containers share the same
   surface skin (background, border, radius, shadow, padding, frosted-glass
   blur) and the same row styling (.menu-item / .menu-divider), so font size,
   text colors, hover, danger, active and radius stay consistent everywhere.

   Which container class to use:
   - .conn-context-menu          → a top-level menu (this component's root),
     teleported to <body> and positioned with screen coordinates (fixed).
   - .menu-submenu               → a nested flyout / submenu. It reuses the
     same surface and row styling as the parent, but is positioned relative
     to an open, hoverable anchor — drop it on any flyout and the look is
     identical without writing extra CSS.

   Modifiers / building blocks (all defined once here):
   - .conn-context-menu.anchored → absolute, anchored to a relatively
     positioned parent (e.g. an inline "⋯" button) instead of fixed.
   - .conn-context-menu.mirror-  → the container is shifted left via
       left                        translateX(-100%); the flyout side is decided
                                   per-position against the window edges.
   - .menu-item.active           → selected / highlighted row (accent).
   - .menu-item.iconic           → row with a leading icon; keeps icon+label
                                   and a trailing slot aligned on one line.
   - .menu-item.submenu-wrap     → row that hosts a nested .menu-submenu
                                   (gets position:relative so the flyout can
                                   anchor to it).
   - .menu-item.mono             → monospaced path / label row (SFTP drives,
                                   bookmarks).
   - .menu-divider               → separator line between groups.
     (.menu-shortcut / trailing overlay live scoped inside MenuItem.vue.) */
.conn-context-menu {
  position: fixed;
  z-index: 99999;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  /* Auto-width: the menu hugs its widest row, so no per-menu min-width tuning
     is needed. min-width only guarantees a floor for single-word menus. */
  width: max-content;
  min-width: 8.75rem;
  padding: 0.25rem;
  backdrop-filter: blur(0.5rem);
}
.conn-context-menu.anchored {
  position: absolute;
  top: 100%;
  right: 0;
}
/* Flyout flip is per-flyout: each .menu-submenu anchors absolutely to its own
   .submenu-wrap row, so flipping its side must never move the parent menu.
   (A prior version translated the whole container with translateX(-100%), which
   made hovering a submenu-wrapped row jump the entire top-level menu sideways —
   e.g. the AppHeader settings menu hopping left. Removed: only the flyout's
   left/right flips.) */
.conn-context-menu.mirror-left {
  /* intentionally empty — kept for the descendant selector below */
}
/* Too tall for the window: scroll inside the container instead of being cut
   off by the window edge. Toggled only when the measured height exceeds the
   viewport (see position()), because overflow != visible would clip the
   absolutely positioned submenu flyouts even when nothing overflows. */
.conn-context-menu.overflow {
  max-height: calc(100vh - 0.5rem);
  overflow-y: auto;
  overflow-x: hidden;
}
.conn-context-menu .menu-item {
  padding: 0.4375rem 0.875rem;
  font-size: 0.75rem;
  font-family: var(--font-ui);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  border-radius: var(--radius-sm);
  transition: all 0.1s ease;
}
.conn-context-menu .menu-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.conn-context-menu .menu-item.disabled {
  color: var(--text-disabled);
  cursor: default;
  pointer-events: none;
}
.conn-context-menu .menu-item.danger {
  color: var(--error);
}
.conn-context-menu .menu-item.danger:hover {
  background: var(--error-subtle);
  color: var(--error);
}
/* Selected / highlighted row — accent + semibold (same look as the settings
   submenus). */
.conn-context-menu .menu-item.active {
  color: var(--accent);
  font-weight: 500;
}
.conn-context-menu .menu-item.iconic {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}
.conn-context-menu .menu-item.mono {
  font-family: var(--font-mono);
}
.conn-context-menu .menu-item.submenu-wrap {
  position: relative;
}
.conn-context-menu .menu-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 0.25rem 0.375rem;
}
/* Trailing chevron on a submenu-wrap row (settings + type-filter menus).
   margin-left:auto pushes it to the right edge of the flex .iconic row. */
.conn-context-menu .menu-icon-trailing {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 0.8125rem;
  color: var(--text-tertiary);
}
/* Nested flyout / submenu surface — inherits the same surface skin. Position
   it relative to a .menu-item.submenu-wrap; the skin and rows reuse everything
   above. Flyout direction is decided per-position by Menu.vue against the
   window edges (`mirror-left` flips it leftward when the right side can't fit
   it). Hosts just write `menu-submenu` and never pick a side. Each overlaps 0.1875rem
   onto its parent row so the parent→flyout mouse path never crosses a dead gap
   (which would close the flyout). */
.conn-context-menu .menu-submenu {
  position: absolute;
  z-index: 10001;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 8.75rem;
  padding: 0.25rem;
  backdrop-filter: blur(0.5rem);
  /* default: fly right of the parent row */
  left: calc(100% - 0.1875rem);
  top: -0.25rem;
  /* A long flyout (e.g. the language list) scrolls instead of running past
     the window bottom. Safe here: flyouts contain plain rows only, no
     absolutely positioned descendants to clip. */
  max-height: calc(100vh - 0.5rem);
  overflow-y: auto;
}
/* mirror-left container → submenus fly left */
.conn-context-menu.mirror-left .menu-submenu {
  left: auto;
  right: calc(100% - 0.1875rem);
  top: -0.25rem;
}
.conn-context-menu .menu-submenu .menu-item {
  padding: 0.4375rem 0.75rem;
  font-size: 0.75rem;
  font-family: var(--font-ui);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  border-radius: var(--radius-sm);
  transition: all 0.1s ease;
}
.conn-context-menu .menu-submenu .menu-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.conn-context-menu .menu-submenu .menu-item.active {
  color: var(--accent);
  font-weight: 500;
}
</style>