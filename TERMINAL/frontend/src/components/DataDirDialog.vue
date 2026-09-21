<template>
  <el-dialog append-to-body
    :model-value="visible"
    @update:model-value="(v: boolean) => !v && onCancel()"
    :title="firstRun ? t('dataDir.title') : t('config.changeDir')"
    width="32.5rem"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="!firstRun"
  >
    <el-form label-width="6.25rem" class="datadir-form">
      <el-form-item :label="t('config.dataDir')">
        <el-select v-model="kind" style="width: 100%">
          <el-option :label="t('dataDir.default')" value="default" />
          <el-option :label="t('dataDir.portable')" value="portable" />
          <el-option :label="t('dataDir.custom')" value="custom" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="kind === 'custom'" :label="t('dataDir.customPath')">
        <div class="datadir-custom">
          <el-input v-model="customDir" :placeholder="t('dataDir.customPlaceholder')" />
          <el-button size="small" @click="pickDir">{{ t('dataDir.browse') }}</el-button>
        </div>
      </el-form-item>
      <el-form-item v-if="!firstRun" :label="t('dataDir.migrate')">
        <el-switch v-model="migrate" />
      </el-form-item>
    </el-form>
    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>
    <template #footer>
      <el-button v-if="!firstRun" @click="onCancel">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="submitting" @click="onConfirm">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from '../i18n'
import { useCredentialStore } from '../stores/credentialStore'
import { OpenDirectoryDialog } from '../../bindings/easyaiot/terminal/app'

const props = defineProps<{ visible: boolean; firstRun: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'done', restart: boolean): void }>()

const { t } = useI18n()
const cred = useCredentialStore()
const kind = ref<'default' | 'portable' | 'custom'>('default')
const customDir = ref('')
const migrate = ref(true)
const submitting = ref(false)
const errorMsg = ref('')

// Preselect the current data-dir type when the dialog opens, so the radio
// reflects where config actually lives rather than always "default".
watch(() => props.visible, (v) => {
  if (!v) return
  kind.value = cred.dataDirInfo.type
  customDir.value = cred.dataDirInfo.type === 'custom' ? cred.dataDirInfo.dataDir : ''
  errorMsg.value = ''
})

async function pickDir() {
  const p = await OpenDirectoryDialog()
  if (p) customDir.value = p
}
async function onConfirm() {
  errorMsg.value = ''
  submitting.value = true
  try {
    await cred.selectDataDir(kind.value, customDir.value, migrate.value)
    emit('done', false)
    emit('update:visible', false)
  } catch (e: any) {
    if (String(e?.message || e).includes('restart required')) {
      emit('done', true)
      emit('update:visible', false)
    } else {
      errorMsg.value = e?.message || String(e)
    }
  } finally {
    submitting.value = false
  }
}
function onCancel() {
  emit('update:visible', false)
}
</script>

<style scoped>
.datadir-form { display: flex; flex-direction: column; gap: 0.25rem; }
.datadir-custom { display: flex; gap: 0.5rem; }
.form-error { color: var(--el-color-danger); font-size: 0.8125rem; margin-top: 0.5rem; }
</style>
