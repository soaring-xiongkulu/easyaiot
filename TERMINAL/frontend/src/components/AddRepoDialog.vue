<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="t('addRepo.title')"
    width="32.5rem"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="6.25rem" class="add-repo-form">
      <el-form-item :label="t('addRepo.url')">
        <el-input
          v-model="repoUrl"
          :placeholder="t('addRepo.urlPlaceholder')"
        />
        <div class="form-hint warning">{{ t('addRepo.urlHint') }}</div>
      </el-form-item>

      <el-form-item :label="t('addRepo.username')">
        <el-input
          v-model="username"
          :placeholder="t('addRepo.usernamePlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="t('addRepo.token')">
        <el-input
          v-model="token"
          type="password"
          show-password
          :placeholder="t('addRepo.tokenPlaceholder')"
        />
        <div class="form-hint">{{ t('addRepo.tokenHint') }}</div>
      </el-form-item>

      <el-form-item :label="t('addRepo.masterPassword')">
        <el-input
          v-model="masterPassword"
          type="password"
          show-password
          :placeholder="t('addRepo.masterPasswordPlaceholder')"
        />
        <div class="form-hint">{{ t('addRepo.masterPasswordHint') }}</div>
      </el-form-item>
    </el-form>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button @click="handleClose">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ t('addRepo.saveAndConnect') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '../i18n'
import { useSyncStore } from '../stores/syncStore'
import { msg } from '../services/message'

const { t } = useI18n()
const syncStore = useSyncStore()

const visible = computed({
  get: () => syncStore.showAddRepo,
  set: (v) => { if (!v) syncStore.showAddRepo = false },
})

const repoUrl = ref('')
const username = ref('')
const token = ref('')
const masterPassword = ref('')
const submitting = ref(false)
const errorMsg = ref('')

function handleClose() {
  syncStore.showAddRepo = false
  resetForm()
}

function resetForm() {
  repoUrl.value = ''
  username.value = ''
  token.value = ''
  masterPassword.value = ''
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''

  if (!repoUrl.value.trim()) {
    errorMsg.value = t('addRepo.urlRequired')
    return
  }
  if (!username.value.trim()) {
    errorMsg.value = t('addRepo.usernameRequired')
    return
  }
  if (!token.value.trim()) {
    errorMsg.value = t('addRepo.tokenRequired')
    return
  }
  if (!masterPassword.value) {
    errorMsg.value = t('addRepo.masterPasswordRequired')
    return
  }

  submitting.value = true
  try {
    const result = await syncStore.configureRepo(
      repoUrl.value.trim(),
      username.value.trim(),
      token.value,
      masterPassword.value
    )
    if (result && result.direction === 3) {
      // Conflict: repo connected but data differs
      syncStore.showAddRepo = false
      resetForm()
      return
    }
    msg.success(t('addRepo.success'))
    syncStore.showAddRepo = false
    resetForm()
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.add-repo-form {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  line-height: 1.4;
}

.form-hint.warning {
  color: var(--el-color-warning-dark-2);
}

.form-error {
  color: var(--el-color-danger);
  font-size: 0.8125rem;
  margin-top: 0.5rem;
}
</style>
