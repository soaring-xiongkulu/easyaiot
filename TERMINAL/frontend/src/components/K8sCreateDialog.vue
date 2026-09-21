<template>
  <el-dialog
    append-to-body
    v-model="visible"
    :title="title"
    width="80%"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <SyntaxEditor v-model="content" lang="yaml" />
    <div v-if="error" class="yaml-error">{{ error }}</div>
    <template #footer>
      <el-button @click="visible = false">{{ t('common.cancel') || '取消' }}</el-button>
      <el-button type="primary" :loading="saving" @click="onConfirm">{{ t('common.save') || '保存' }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElDialog, ElButton } from 'element-plus'
import { useI18n } from '../i18n'
import SyntaxEditor from './SyntaxEditor.vue'

const props = defineProps<{ modelValue: boolean; title: string; template: string; saving?: boolean; error?: string }>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'confirm', yaml: string): void
}>()

const { t } = useI18n()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})
const content = ref(props.template)

watch(() => props.modelValue, (v) => { if (v) content.value = props.template })

function onConfirm() {
  emit('confirm', content.value)
}
</script>

<style scoped>
.yaml-error { color: var(--el-color-danger, #f56); padding: 0.5rem 0.125rem 0; font-size: 0.75rem; }
</style>
