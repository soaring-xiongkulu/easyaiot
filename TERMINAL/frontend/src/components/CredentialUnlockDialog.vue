<template>
  <el-dialog append-to-body
    :model-value="visible"
    @update:model-value="(v: boolean) => !v && onCancel()"
    :title="t('unlock.title')"
    width="25rem"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <el-input v-model="pw" type="password" show-password :placeholder="t('unlock.password')" @keyup.enter="onUnlock" />
    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>
    <template #footer>
      <el-button type="primary" :loading="submitting" @click="onUnlock">{{ t('unlock.confirm') }}</el-button>
      <el-button @click="onReset">{{ t('unlock.reset') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '../i18n'
import { useCredentialStore } from '../stores/credentialStore'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'done'): void; (e: 'reset'): void }>()

const { t } = useI18n()
const cred = useCredentialStore()
const pw = ref('')
const submitting = ref(false)
const errorMsg = ref('')

async function onUnlock() {
  errorMsg.value = ''
  submitting.value = true
  try {
    await cred.unlock(pw.value)
    emit('done')
    emit('update:visible', false)
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}
function onReset() { emit('reset') }
function onCancel() { emit('update:visible', false) }
</script>

<style scoped>
.form-error { color: var(--el-color-danger); font-size: 0.8125rem; margin-top: 0.5rem; }
</style>
