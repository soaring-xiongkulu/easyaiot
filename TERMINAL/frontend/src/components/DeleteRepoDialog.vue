<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="t('deleteRepo.title')"
    width="27.5rem"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="delete-body">
      <p>{{ t('deleteRepo.confirm') }}</p>
      <ul class="delete-desc">
        <li>{{ t('deleteRepo.desc1') }}</li>
        <li>{{ t('deleteRepo.desc2') }}</li>
      </ul>
    </div>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button @click="handleClose">{{ t('common.cancel') }}</el-button>
      <el-button type="danger" :loading="submitting" @click="handleSubmit">
        {{ t('deleteRepo.confirmDelete') }}
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
  get: () => syncStore.showDeleteRepo,
  set: (v) => { if (!v) syncStore.showDeleteRepo = false },
})

const submitting = ref(false)
const errorMsg = ref('')

function handleClose() {
  syncStore.showDeleteRepo = false
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''
  submitting.value = true
  try {
    await syncStore.deleteRepo()
    msg.success(t('deleteRepo.success'))
    syncStore.showDeleteRepo = false
  } catch (e: any) {
    errorMsg.value = e?.message || String(e)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.delete-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.delete-body p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.delete-desc {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.8;
}

.form-error {
  color: var(--el-color-danger);
  font-size: 0.8125rem;
  margin-top: 0.75rem;
}
</style>
