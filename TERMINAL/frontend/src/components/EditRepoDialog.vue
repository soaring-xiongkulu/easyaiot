<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="t('editRepo.title')"
    width="32.5rem"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="7.5rem" class="edit-repo-form">
      <el-form-item :label="t('editRepo.url')">
        <div class="locked-field">
          <span class="locked-value">{{ syncStore.config.repoUrl }}</span>
          <el-icon class="lock-icon"><Lock :size="'0.875rem'" /></el-icon>
        </div>
        <div class="form-hint">{{ t('editRepo.urlLocked') }}</div>
      </el-form-item>

      <el-form-item :label="t('editRepo.username')">
        <el-input
          v-model="username"
          :placeholder="t('editRepo.usernamePlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="t('editRepo.token')">
        <el-input
          v-model="token"
          type="password"
          show-password
          :placeholder="t('editRepo.tokenPlaceholder')"
        />
        <div class="form-hint">{{ t('editRepo.tokenHint') }}</div>
      </el-form-item>

      <el-form-item :label="t('editRepo.currentPassword')">
        <el-input
          v-model="currentPassword"
          type="password"
          show-password
          :placeholder="t('editRepo.currentPasswordPlaceholder')"
        />
        <div class="form-hint">{{ t('editRepo.currentPasswordHint') }}</div>
      </el-form-item>
    </el-form>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button @click="handleClose">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Lock } from '@lucide/vue'
import { useI18n } from '../i18n'
import { useSyncStore } from '../stores/syncStore'
import { SyncVerifyPassword } from '../../bindings/easyaiot/terminal/app'
import { backendErrorText } from '../utils/backendError'
import { msg } from '../services/message'

const { t } = useI18n()
const syncStore = useSyncStore()

const visible = computed({
  get: () => syncStore.showEditRepo,
  set: (v) => { if (!v) syncStore.showEditRepo = false },
})

const username = ref('')
const token = ref('')
const currentPassword = ref('')
const submitting = ref(false)
const errorMsg = ref('')

watch(visible, (v) => {
  if (v) {
    username.value = syncStore.config.username
    token.value = ''
    currentPassword.value = ''
    errorMsg.value = ''
  }
})

function handleClose() {
  syncStore.showEditRepo = false
  resetForm()
}

function resetForm() {
  username.value = syncStore.config.username
  token.value = ''
  currentPassword.value = ''
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''

  if (!username.value.trim()) {
    errorMsg.value = t('editRepo.usernameRequired')
    return
  }

  submitting.value = true
  try {
    await SyncVerifyPassword(currentPassword.value, username.value.trim(), token.value)
    syncStore.config.username = username.value.trim()
    await syncStore.saveConfig(token.value)
    const syncResult = await syncStore.doSync()
    if (syncResult) {
      if (syncResult.direction === 3) {
        // Conflict — SyncConflictDialog will open via event
      } else {
        msg.success(syncResult.message || t('editRepo.success'))
      }
    } else {
      msg.error(syncStore.lastResult || t('settings.syncFailed'))
    }
    syncStore.showEditRepo = false
    resetForm()
  } catch (e: any) {
    const msg = backendErrorText(e)
    errorMsg.value = msg === 'WRONG_SYNC_PASSWORD' ? t('editRepo.wrongPassword') : msg
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.edit-repo-form {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.locked-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--el-fill-color-light);
  border-radius: 0.25rem;
  font-size: 0.8125rem;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  word-break: break-all;
}

.locked-value {
  flex: 1;
  min-width: 0;
}

.lock-icon {
  flex-shrink: 0;
  color: var(--text-muted);
}

.form-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  line-height: 1.4;
}

.form-error {
  color: var(--el-color-danger);
  font-size: 0.8125rem;
  margin-top: 0.5rem;
}
</style>
