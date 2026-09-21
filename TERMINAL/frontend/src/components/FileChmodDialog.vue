<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="t('sftp.changePermission')"
    width="25rem"
    :close-on-click-modal="false"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
    @closed="onClosed"
  >
    <div class="chmod-file-info">
      <span class="chmod-filename">{{ name }}</span>
      <span v-if="owner || group" class="chmod-ownergroup">{{ owner || '-' }}:{{ group || '-' }}</span>
    </div>
    <el-form class="chmod-form" label-width="5rem">
      <el-form-item label="Owner">
        <el-checkbox v-model="ownerR">Read</el-checkbox>
        <el-checkbox v-model="ownerW">Write</el-checkbox>
        <el-checkbox v-model="ownerX">Execute</el-checkbox>
      </el-form-item>
      <el-form-item label="Group">
        <el-checkbox v-model="groupR">Read</el-checkbox>
        <el-checkbox v-model="groupW">Write</el-checkbox>
        <el-checkbox v-model="groupX">Execute</el-checkbox>
      </el-form-item>
      <el-form-item label="Other">
        <el-checkbox v-model="otherR">Read</el-checkbox>
        <el-checkbox v-model="otherW">Write</el-checkbox>
        <el-checkbox v-model="otherX">Execute</el-checkbox>
      </el-form-item>
      <el-form-item :label="t('sftp.dialog.chmodOctal')">
        <el-input v-model="octalInput" class="chmod-octal-input" maxlength="3" placeholder="644" @input="onOctalInput" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close(false)">{{ t('sftp.dialog.cancel') }}</el-button>
      <el-button type="primary" @click="close(true)">{{ t('sftp.dialog.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from '../i18n'

const { t } = useI18n()

const props = defineProps<{
  visible?: boolean
  name?: string
  owner?: string
  group?: string
  mode?: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', octal: string): void
  (e: 'cancel'): void
}>()

const ownerR = ref(false)
const ownerW = ref(false)
const ownerX = ref(false)
const groupR = ref(false)
const groupW = ref(false)
const groupX = ref(false)
const otherR = ref(false)
const otherW = ref(false)
const otherX = ref(false)

const chmodOctal = computed(() => {
  const o = (ownerR.value ? 4 : 0) + (ownerW.value ? 2 : 0) + (ownerX.value ? 1 : 0)
  const g = (groupR.value ? 4 : 0) + (groupW.value ? 2 : 0) + (groupX.value ? 1 : 0)
  const t = (otherR.value ? 4 : 0) + (otherW.value ? 2 : 0) + (otherX.value ? 1 : 0)
  return String(o) + String(g) + String(t)
})

const octalInput = ref('000')

// Keep the editable octal field in sync with the checkbox grid both ways.
watch(chmodOctal, (v) => { octalInput.value = v })

function applyOctal(digits: string) {
  const nums = digits.split('').map(Number)
  ownerR.value = !!(nums[0] & 4); ownerW.value = !!(nums[0] & 2); ownerX.value = !!(nums[0] & 1)
  groupR.value = !!(nums[1] & 4); groupW.value = !!(nums[1] & 2); groupX.value = !!(nums[1] & 1)
  otherR.value = !!(nums[2] & 4); otherW.value = !!(nums[2] & 2); otherX.value = !!(nums[2] & 1)
}

function onOctalInput() {
  octalInput.value = octalInput.value.replace(/[^0-7]/g, '').slice(0, 3)
  if (octalInput.value.length === 3) applyOctal(octalInput.value)
}

function parseMode(mode: string) {
  // mode example: "drwxr-xr-x" or "-rw-r--r--" — strip leading file type char
  const m = mode.length >= 10 ? mode.slice(1) : mode
  ownerR.value = m[0] === 'r'
  ownerW.value = m[1] === 'w'
  ownerX.value = m[2] === 'x' || m[2] === 's'
  groupR.value = m[3] === 'r'
  groupW.value = m[4] === 'w'
  groupX.value = m[5] === 'x' || m[5] === 's'
  otherR.value = m[6] === 'r'
  otherW.value = m[7] === 'w'
  otherX.value = m[8] === 'x' || m[8] === 't'
  octalInput.value = chmodOctal.value
}

// (Re)parse the mode whenever the dialog opens with new data.
watch(() => props.visible, (v) => { if (v) parseMode(props.mode || '') })

function onClosed() {
  /* state re-parses on next open */
}

function close(ok: boolean) {
  emit('update:visible', false)
  if (ok) emit('confirm', chmodOctal.value)
  else emit('cancel')
}
</script>

<style scoped>
.chmod-file-info {
  text-align: center;
  margin-bottom: 1rem;
}
.chmod-filename {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono, monospace);
}
.chmod-ownergroup {
  display: block;
  font-size: 0.6875rem;
  color: var(--text-disabled);
  margin-top: 0.125rem;
}
.chmod-form {
  margin-top: 0.25rem;
}
.chmod-form .el-form-item {
  margin-bottom: 0.75rem;
}
.chmod-octal-input {
  width: 7.5rem;
}
</style>