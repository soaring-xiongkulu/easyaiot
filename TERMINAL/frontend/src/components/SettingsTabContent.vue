<template>
  <div class="settings-tab-content">
    <SettingsTab />
  </div>
</template>

<script setup lang="ts">
import SettingsTab from './SettingsTab.vue'
</script>

<style scoped>
.settings-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: auto;
  background: var(--bg-base);
}
</style>
