<template>
  <el-dialog append-to-body :model-value="visible" :title="t('conn.deleteGroupTitle')" width="28.125rem" @update:model-value="(v: boolean) => emit('update:visible', v)">
    <p>{{ promptText }}</p>
    <template #footer>
      <el-button @click="emit('update:visible', false)">{{ t('conn.deleteGroupCancel') }}</el-button>
      <el-button type="warning" @click="onConfirm('move-out')">{{ t('conn.deleteGroupMoveUp') }}</el-button>
      <el-button type="danger" @click="onConfirm('delete-connections')">{{ t('conn.deleteGroupDeleteAll') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// Shared "delete group" dialog: choose whether the group's connections are
// moved out or deleted along with it. Child-group handling is the parent's
// concern (the confirm callback carries the connection action).
import { computed } from 'vue'
import { useI18n } from '../i18n'
import { useConnectionStore } from '../stores/connectionStore'
import type { ConnectionGroup } from '../types/session'

const props = defineProps<{
  visible: boolean
  group: ConnectionGroup | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', action: 'move-out' | 'delete-connections'): void
}>()

const { t } = useI18n()
const connectionStore = useConnectionStore()

const promptText = computed(() => {
  const g = props.group
  if (!g) return ''
  const connCount = connectionStore.connections.filter(c => c.groupId === g.id).length
  const childCount = connectionStore.groups.filter(cg => cg.parentId === g.id).length
  return t('conn.deleteGroupPrompt', { name: g.name, connCount, childCount })
})

function onConfirm(action: 'move-out' | 'delete-connections') {
  emit('update:visible', false)
  emit('confirm', action)
}
</script>
