<template>
  <el-dialog append-to-body
    :model-value="visible"
    @update:model-value="(v: boolean) => !v && onCancel()"
    :title="t('keychainLost.title')"
    width="27.5rem"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <p class="keychain-lost-desc">{{ t('keychainLost.desc') }}</p>
    <template #footer>
      <el-button type="primary" @click="onConfirm">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'done'): void }>()
const { t } = useI18n()

function onConfirm() {
  emit('done')
  emit('update:visible', false)
}
function onCancel() { emit('update:visible', false) }
</script>

<style scoped>
.keychain-lost-desc { margin: 0 0 0.75rem; color: var(--text-secondary); font-size: 0.8125rem; line-height: 1.5; }
</style>
