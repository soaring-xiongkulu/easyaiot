<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="title"
    width="25rem"
    :close-on-click-modal="false"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
    @closed="emit('closed')"
  >
    <template v-if="type === 'message'">
      <p>{{ message }}</p>
    </template>
    <template v-else>
      <el-input
        :model-value="inputValue"
        :placeholder="placeholder"
        :disabled="loading"
        @update:model-value="(v: string) => emit('update:inputValue', v)"
        @keyup.enter="emit('confirm')"
      />
      <el-input
        v-if="input2Placeholder"
        :model-value="input2Value"
        :placeholder="input2Placeholder"
        :disabled="loading"
        class="generic-dialog-input2"
        @update:model-value="(v: string) => emit('update:input2Value', v)"
        @keyup.enter="emit('confirm')"
      />
      <p v-if="error" class="generic-dialog-error">{{ error }}</p>
    </template>
    <template #footer>
      <el-button :disabled="loading" @click="emit('cancel')">{{ t('sftp.dialog.cancel') }}</el-button>
      <el-button type="primary" :loading="loading" @click="emit('confirm')">{{ t('sftp.dialog.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { useI18n } from '../i18n'

const { t } = useI18n()

defineProps<{
  visible?: boolean
  title?: string
  type?: 'input' | 'message'
  inputValue?: string
  placeholder?: string
  /** Optional second input row, rendered only when set (e.g. link target). */
  input2Value?: string
  input2Placeholder?: string
  message?: string
  error?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'update:inputValue', v: string): void
  (e: 'update:input2Value', v: string): void
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'closed'): void
}>()
</script>

<style scoped>
.generic-dialog-input2 {
  margin-top: 0.5rem;
}
.generic-dialog-error {
  color: var(--el-color-danger);
  margin-top: 0.5rem;
}
</style>