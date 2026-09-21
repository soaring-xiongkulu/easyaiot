<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="t('sync.conflictTitle')"
    width="30rem"
    :close-on-click-modal="false"
    @close="handleCancel"
  >
    <div class="conflict-body">
      <p>{{ t('sync.conflictDesc') }}</p>
      <div class="conflict-times">
        <div class="conflict-time">
          <span class="time-label">{{ t('sync.conflictLocal') }}</span>
          <span>{{ formatTime(syncStore.conflict?.localTime) }}</span>
        </div>
        <div class="conflict-time">
          <span class="time-label">{{ t('sync.conflictRemote') }}</span>
          <span>{{ formatTime(syncStore.conflict?.remoteTime) }}</span>
        </div>
      </div>

      <el-radio-group v-model="choice" class="conflict-choice">
        <el-radio value="local">{{ t('sync.conflictUseLocal') }}</el-radio>
        <el-radio value="remote">{{ t('sync.conflictUseRemote') }}</el-radio>
      </el-radio-group>
    </div>

    <template #footer>
      <el-button @click="handleCancel">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="syncing" @click="handleConfirm">
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
const choice = ref<'local' | 'remote'>('local')
const syncing = ref(false)

const visible = computed({
  get: () => syncStore.conflict !== null,
  set: (v) => { if (!v) syncStore.conflict = null },
})

function formatTime(timeStr?: string): string {
  if (!timeStr) return '-'
  try {
    const d = new Date(timeStr)
    return d.toLocaleString()
  } catch {
    return timeStr
  }
}

async function handleConfirm() {
  syncing.value = true
  try {
    const result = await syncStore.resolveConflict(choice.value === 'local')
    if (result) {
      msg.success(result.message || t('settings.syncSuccess'))
    } else {
      msg.error(syncStore.lastResult || t('settings.syncFailed'))
    }
  } finally {
    syncing.value = false
  }
}

function handleCancel() {
  syncStore.conflict = null
}
</script>

<style scoped>
.conflict-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.conflict-times {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--el-fill-color-light);
  border-radius: 0.375rem;
  font-size: 0.8125rem;
}

.conflict-time {
  display: flex;
  gap: 0.5rem;
}

.time-label {
  font-weight: 500;
  min-width: 6.25rem;
}

.conflict-choice {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}
</style>
