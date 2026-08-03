<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const root = ref<HTMLElement | null>(null)
const visible = ref(false)
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry?.isIntersecting) {
        visible.value = true
        observer?.disconnect()
      }
    },
    { threshold: 0.16, rootMargin: '0px 0px -40px 0px' },
  )
  if (root.value) observer.observe(root.value)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<template>
  <div ref="root" class="reveal" :class="{ 'is-visible': visible }">
    <slot />
  </div>
</template>
