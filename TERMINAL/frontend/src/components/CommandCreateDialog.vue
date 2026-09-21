<template>
  <el-dialog
    :model-value="true"
    :title="t('settings.commandsCreateTitle')"
    width="33.75rem"
    @close="$emit('close')"
  >
    <el-form label-position="right" label-width="4.5rem" size="small">
      <el-form-item :label="t('settings.commandsName')" required>
        <el-input v-model="form.name" :placeholder="t('settings.commandsNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="t('settings.commandsDescription')">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          :placeholder="t('settings.commandsDescriptionPlaceholder')"
        />
      </el-form-item>
      <el-form-item :label="t('settings.commandsArgumentHint')">
        <el-input
          v-model="form.argumentHint"
          :placeholder="t('settings.commandsArgumentHintPlaceholder')"
        />
      </el-form-item>
      <el-form-item :label="t('settings.commandsBody')" required>
        <el-input
          v-model="form.body"
          type="textarea"
          :rows="8"
          :placeholder="t('settings.commandsBodyPlaceholder')"
        />
      </el-form-item>
    </el-form>
    <p class="command-args-hint">{{ t('settings.commandsArgumentsHint') }}</p>
    <template #footer>
      <el-button @click="$emit('close')">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :disabled="!canCreate" @click="onCreate">
        {{ t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '../i18n'
import { useCommandStore } from '../stores/commandStore'

const { t } = useI18n()
const store = useCommandStore()

const COMMAND_TEMPLATE = `Analyze the following log output and produce a concise incident report.

$ARGUMENTS

Please:
- Summarize what happened, in order of importance.
- List every ERROR / WARN / FATAL line with its likely root cause.
- Point out repeated patterns, spikes, or timestamps that stand out.
- Suggest concrete next commands to run for confirmation (do not execute anything destructive).
`

const emit = defineEmits<{
  close: []
  created: []
}>()

const form = ref({ name: '', description: '', argumentHint: '', body: COMMAND_TEMPLATE })

const canCreate = computed(() => {
  return form.value.name.trim() && form.value.body.trim()
})

async function onCreate() {
  if (!canCreate.value) return
  try {
    await store.create(form.value.name.trim(), form.value.description.trim(), form.value.body.trim(), form.value.argumentHint.trim())
    emit('created')
  } catch (e: any) {
    ElMessage.error(e?.message || 'Create failed')
  }
}
</script>

<style scoped>
.command-args-hint {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  margin: 0;
  line-height: 1.5;
}
</style>
