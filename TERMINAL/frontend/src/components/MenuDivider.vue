<template>
  <!-- Single unified menu separator. Renders the .menu-divider skin so hosts
       never write the class string themselves. Auto-hides unless there is a
       menu row on BOTH sides — a divider needs two non-empty groups to separate
       — so hosts don't have to gate it with v-if when a group is empty. -->
  <div v-show="visible" ref="dividerEl" class="menu-divider" />
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'

const dividerEl = ref<HTMLElement | null>(null)
const visible = ref(true)
let observer: MutationObserver | null = null

function isItem(n: Element | null): boolean {
  return !!n && n.classList.contains('menu-item')
}
function isDivider(n: Element | null): boolean {
  return !!n && n.classList.contains('menu-divider')
}
// Nearest menu row scanning backward/forward, jumping over comment placeholders
// (v-if'd-away rows) and, crucially, over OTHER dividers — so when several
// consecutive groups are empty the stacked dividers don't each cancel each other
// out and hide even though there is content on both ends.
function nearestItem(d: Element | null, step: (n: Element) => Element | null): Element | null {
  let n = d
  while (n) {
    if (isItem(n)) return n
    n = step(n)
  }
  return null
}

function update() {
  const el = dividerEl.value
  if (!el) return
  const above = nearestItem(el.previousElementSibling, (n) => n.previousElementSibling)
  const below = nearestItem(el.nextElementSibling, (n) => n.nextElementSibling)
  // Collapse a run of consecutive dividers to its topmost one: only show if this
  // divider is NOT preceded directly by another divider AND there is a real menu
  // row somewhere above and below it. A leading/trailing separator (nothing on
  // one side) stays hidden.
  const isFirstOfRun = !isDivider(el.previousElementSibling)
  visible.value = isFirstOfRun && !!above && !!below
}

onMounted(() => {
  // Defer so sibling v-if rows have settled before the first read.
  nextTick(update)
  const parent = dividerEl.value?.parentElement
  if (!parent) return
  observer = new MutationObserver(update)
  observer.observe(parent, { childList: true, subtree: false })
})

onBeforeUnmount(() => observer?.disconnect())
</script>