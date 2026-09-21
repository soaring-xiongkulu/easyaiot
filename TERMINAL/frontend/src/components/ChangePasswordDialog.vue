<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="t('changePassword.title')"
    width="30rem"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form label-width="7.5rem" class="change-password-form">
      <el-form-item :label="t('changePassword.current')">
        <el-input
          v-model="currentPassword"
          type="password"
          show-password
          :placeholder="t('changePassword.currentPlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="t('changePassword.new')">
        <el-input
          v-model="newPassword"
          type="password"
          show-password
          :placeholder="t('changePassword.newPlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="t('changePassword.confirmNew')">
        <el-input
          v-model="confirmPassword"
          type="password"
          show-password
          :placeholder="t('changePassword.confirmNewPlaceholder')"
        />
      </el-form-item>
    </el-form>

    <div class="password-warning">
      <span>{{ t('changePassword.warning') }}</span>
    </div>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button @click="handleClose">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ t('common.confirm') }}
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
  get: () => syncStore.showChangePassword,
  set: (v) => { if (!v) syncStore.showChangePassword = false },
})

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const submitting = ref(false)
const errorMsg = ref('')

function handleClose() {
  syncStore.showChangePassword = false
  resetForm()
}

function resetForm() {
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''

  if (!currentPassword.value) {
    errorMsg.value = t('changePassword.currentRequired')
    return
  }
  if (!newPassword.value) {
    errorMsg.value = t('changePassword.newRequired')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = t('changePassword.mismatch')
    return
  }

  submitting.value = true
  try {
    await syncStore.changePassword(currentPassword.value, newPassword.value)
    msg.success(t('changePassword.success'))
    syncStore.showChangePassword = false
    resetForm()
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.change-password-form {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.password-warning {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
  line-height: 1.4;
}

.form-error {
  color: var(--el-color-danger);
  font-size: 0.8125rem;
  margin-top: 0.5rem;
}
</style>
