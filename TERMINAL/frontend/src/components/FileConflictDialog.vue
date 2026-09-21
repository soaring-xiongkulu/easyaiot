<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="t('sftp.dialog.conflictTitle')"
    width="28.125rem"
    :close-on-click-modal="false"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
  >
    <p>{{ t('sftp.dialog.conflictPrompt') }}</p>
    <ul class="conflict-list">
      <li v-for="f in files" :key="f">{{ f }}</li>
    </ul>
    <template #footer>
      <el-button @click="emit('resolve', 'cancel')">{{ t('sftp.dialog.cancel') }}</el-button>
      <el-button @click="emit('resolve', 'overwrite')">{{ t('sftp.dialog.conflictOverwrite') }}</el-button>
      <el-button type="primary" @click="emit('resolve', 'rename')">{{ t('sftp.dialog.conflictRename') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n'

const { t } = useI18n()

defineProps<{
  visible?: boolean
  files?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'resolve', action: 'overwrite' | 'rename' | 'cancel'): void
}>()
</script>

<style scoped>
.conflict-list {
  max-height: 11.25rem;
  overflow-y: auto;
  margin: 0.5rem 0 0.25rem;
  padding-left: 1.25rem;
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  color: var(--text-secondary);
}
</style>