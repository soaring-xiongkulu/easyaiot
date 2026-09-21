<template>
  <!-- Single unified menu row. Renders the .menu-item skin and lets the host
       add variant styles via props (iconic, mono...) plus any per-site class
       via attr fallthrough, so hosts never write the "menu-item" skin string.
       `shortcut` renders a muted trailing hint (keyboard shortcut / aux text);
       the `#trailing` slot hosts right-aligned content that fades in on row
       hover (e.g. a delete button) without the host hand-rolling the reveal. -->
  <div class="menu-item" :class="{ 'has-trailing': !!$slots.trailing, 'has-shortcut': !!shortcut, iconic }">
    <component
      v-if="icon"
      :is="icon"
      class="menu-leading-icon"
      :size="iconSize ?? 14"
    />
    <slot />
    <span v-if="shortcut" class="menu-shortcut">{{ shortcut }}</span>
    <span v-if="$slots.trailing" class="menu-trailing"><slot name="trailing" /></span>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
// inheritAttrs (default) forwards host class/:class/event listeners onto the
// single root <div>, merged with the static "menu-item" class above.
defineProps<{
  /** Leading lucide icon, rendered before the label (usually with `iconic`
   *  so it sits on the same flex line with the label and trailing content). The
   *  host passes the imported icon component; sizing/spacing live here. */
  icon?: Component
  /** Pixel size for the leading icon. Defaults to 14. */
  iconSize?: number
  /** Icon + label (and a trailing slot) laid out on one flex line. */
  iconic?: boolean
  /** Optional muted trailing hint (usually a keyboard shortcut). Shown only
   *  when non-empty; always right-aligned (.has-shortcut below). */
  shortcut?: string
}>()
</script>

<style scoped>
.menu-leading-icon {
  flex-shrink: 0;
  color: inherit;
}
/* Rows with a shortcut hint turn flex so the hint ("Ctrl+C" etc.) hugs the
   right edge instead of sitting after the label. Rows without one keep the
   plain block layout (the class is absent, so this no-ops). */
.menu-item.has-shortcut {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.menu-shortcut {
  flex-shrink: 0;
  margin-left: auto;
  font-size: 0.6875rem;
  /* UI font, not mono: on macOS the ⌘⌥⇧ glyphs only get their square,
     native-looking shapes from the system font (SF Pro); mono falls back to
     Menlo and renders them thin and text-like. Windows native menus also use
     the UI font for shortcut hints. */
  font-family: var(--font-ui);
  color: var(--text-muted, var(--text-disabled));
  opacity: 0.8;
}

/* Rows that use the #trailing slot: the trailing action overlays the row's
   right edge and fades in on hover, so it reserves no width and never pushes
   the label. The row stays flex so slot content can right-align/truncate.
   Only rows with trailing content are affected — plain rows stay block. */
.menu-item.has-trailing {
  position: relative;
  display: flex;
  align-items: center;
}
.menu-trailing {
  /* Positioned over the row's right edge, sized to its own content so the
     revealed block reads as the button itself, not a bar spanning the row. */
  position: absolute;
  top: 50%;
  right: 0.625rem;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  /* Uniform padding hugs the button content into a square; --bg-hover matches
     the hovered row so the block looks like a natural highlight, and being an
     opaque solid it occludes the row text passing beneath. */
  padding: 0.125rem;
  background: var(--bg-hover);
  border-radius: var(--radius-sm);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
}
.menu-item.has-trailing:hover .menu-trailing {
  opacity: 1;
  pointer-events: auto;
}
</style>