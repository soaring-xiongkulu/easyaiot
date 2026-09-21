<template>
  <el-dialog append-to-body
    :model-value="visible"
    @update:model-value="(v: boolean) => !v && onCancel()"
    :title="t('encrypt.title')"
    width="30rem"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
  >
    <p v-if="existingSecrets > 0" class="encrypt-hint">{{ t('encrypt.existing', { n: existingSecrets }) }}</p>
    <el-form label-width="7.5rem" class="encrypt-form" @submit.prevent="onConfirm">
      <el-form-item :label="t('config.encryption')">
        <el-select v-model="mode" popper-class="mode-select-popper" style="width: 100%">
          <el-option :label="t('encrypt.keychain')" value="keychain">
            <div class="mode-option">
              <div class="mode-option-title">{{ t('encrypt.keychain') }}</div>
              <div class="mode-option-desc">{{ t('config.switchKeychainHint') }}</div>
            </div>
          </el-option>
          <el-option :label="t('encrypt.masterPassword')" value="master-password">
            <div class="mode-option">
              <div class="mode-option-title">{{ t('encrypt.masterPassword') }}</div>
              <div class="mode-option-desc">{{ t('config.switchMasterHint') }}</div>
            </div>
          </el-option>
        </el-select>
      </el-form-item>
      <template v-if="mode === 'master-password'">
        <el-form-item :label="t('encrypt.password')">
          <el-input v-model="pw" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('encrypt.confirm')">
          <el-input v-model="pw2" type="password" show-password />
        </el-form-item>
      </template>
    </el-form>
    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>
    <template #footer>
      <el-button type="primary" :loading="submitting" @click="onConfirm">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from '../i18n'
import { useCredentialStore } from '../stores/credentialStore'
import { isMobilePlatform } from '../utils/platform'

const props = defineProps<{ visible: boolean; existingSecrets: number }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'done'): void }>()

const { t } = useI18n()
const cred = useCredentialStore()
const mode = ref<'keychain' | 'master-password'>('keychain')
const pw = ref('')
const pw2 = ref('')
const submitting = ref(false)
const errorMsg = ref('')

// Mobile (android/ios) only supports the system keychain — skip the picker and
// set it up directly. Covers every path that opens this dialog: first run,
// keychain-lost recovery and manual reset. On failure the dialog stays open
// showing the error.
const isMobile = isMobilePlatform()

async function autoKeychainSetup() {
  submitting.value = true
  try {
    await cred.setup('keychain')
    emit('done')
    emit('update:visible', false)
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}

// Reset on every open so a previously-entered password isn't shown again.
watch(() => props.visible, (v) => {
  if (v) {
    mode.value = 'keychain'
    pw.value = ''
    pw2.value = ''
    errorMsg.value = ''
    if (isMobile) void autoKeychainSetup()
  }
})

async function onConfirm() {
  errorMsg.value = ''
  if (mode.value === 'master-password') {
    if (!pw.value) { errorMsg.value = t('encrypt.passwordRequired'); return }
    if (pw.value !== pw2.value) { errorMsg.value = t('encrypt.mismatch'); return }
  }
  submitting.value = true
  try {
    await cred.setup(mode.value, pw.value)
    emit('done')
    emit('update:visible', false)
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}
function onCancel() { emit('update:visible', false) }
</script>

<style scoped>
.encrypt-form { display: flex; flex-direction: column; gap: 0.25rem; }
.encrypt-hint { margin: 0 0 0.75rem; color: var(--text-secondary); font-size: 0.8125rem; }
.form-error { color: var(--el-color-danger); font-size: 0.8125rem; margin-top: 0.5rem; }
</style>
