<template>
  <MenuItem iconic class="submenu-wrap" @mouseenter="submenu.active = name">
    {{ label }}
    <el-icon class="menu-icon-trailing"><ChevronRight :size="'0.8125rem'" /></el-icon>
    <div v-show="submenu.active === name" class="menu-submenu" @mouseleave="submenu.active = ''">
      <slot />
    </div>
  </MenuItem>
</template>

<script lang="ts">
// Module-scoped counter: `<script setup>` re-runs its body per component
// instance, so a counter declared there would always reset to 0. Keeping it in
// a plain `<script>` block gives every instance a distinct, stable key.
let submenuSeq = 0
</script>

<script setup lang="ts">
import { inject } from 'vue'
import { ChevronRight } from '@lucide/vue'
import MenuItem from './MenuItem.vue'

// Hover-driven nested flyout row. The `active` state lives on the host <Menu>
// (single flyout open at a time); this row sets `active` on hover, and the
// flyout shows only when this instance's auto-generated key matches. Hides the
// .submenu-wrap / arrow / .menu-submenu / mouseenter-leave boilerplate that
// hosts used to hand-write.
defineProps<{
  label: string
}>()

// Stable per instance; globally unique is safe because the single-open
// coordinator shows only one <Menu> at a time.
const name = `submenu-${submenuSeq++}`

// `submenu.active` reactive object provided by the enclosing <Menu>.
const submenu = inject<{ active: string }>('menuSubmenu')!
</script>