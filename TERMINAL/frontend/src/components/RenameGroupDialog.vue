<template>
  <el-dialog append-to-body :model-value="visible" :title="t('conn.renameGroup')" width="22.5rem" @update:model-value="(v: boolean) => emit('update:visible', v)">
    <el-form @submit.prevent="onConfirm">
      <el-form-item :label="t('conn.groupName')">
        <el-input
          ref="nameInputRef"
          v-model="name"
          :placeholder="t('conn.groupNamePlaceholder')"
          @keyup.enter="onConfirm"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">{{ t('conn.cancel') }}</el-button>
      <el-button type="primary" @click="onConfirm">{{ t('conn.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// Shared "rename group" dialog.
import { ref, watch, nextTick } from 'vue'
import { useI18n } from '../i18n'

const props = defineProps<{
  visible: boolean
  name: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', name: string): void
}>()

const { t } = useI18n()

const name = ref('')
const nameInputRef = ref()

watch(() => props.visible, (open) => {
  if (!open) return
  name.value = props.name
  nextTick(() => nameInputRef.value?.focus())
})

function onConfirm() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  emit('update:visible', false)
  emit('confirm', trimmed)
}
</script>
