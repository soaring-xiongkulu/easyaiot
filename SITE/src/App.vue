<script setup lang="ts">
import { RouterView } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import SiteFooter from './components/SiteFooter.vue'
</script>

<template>
  <div class="site-shell">
    <SiteHeader />
    <main class="site-main">
      <RouterView />
    </main>
    <SiteFooter />
  </div>
</template>
