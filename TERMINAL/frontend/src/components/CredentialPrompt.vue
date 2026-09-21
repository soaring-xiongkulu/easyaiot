<template>
  <el-dialog append-to-body
    :model-value="visible"
    @update:model-value="(v: boolean) => !v && onCancel()"
    :title="title"
    width="25rem"
    :close-on-click-modal="false"
    @opened="onDialogOpened"
  >
    <p v-if="subtitle" class="credential-subtitle">{{ subtitle }}</p>
    <div class="credential-fields">
      <div v-if="fields.includes('user')" class="credential-field">
        <label class="credential-label">{{ t('conn.user') }}</label>
        <el-input
          ref="userInputRef"
          v-model="inputUser"
          :placeholder="t('conn.user')"
          @keyup.enter="onConnect"
        />
      </div>
      <div v-if="fields.includes('password')" class="credential-field">
        <label class="credential-label">{{ t('conn.password') }}</label>
        <el-input
          ref="passwordInputRef"
          v-model="inputPassword"
          type="password"
          show-password
          :placeholder="t('conn.password')"
          @keyup.enter="onConnect"
        />
      </div>
    </div>
    <template #footer>
      <el-button @click="onCancel">{{ t('common.cancel') }}</el-button>
      <el-button @click="onSaveAndConnect">{{ t('conn.saveConnect') }}</el-button>
      <el-button type="primary" @click="onConnect">{{ t('credential.connect') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from '../i18n'
import type { InputInstance } from 'element-plus'

export interface CredentialResult {
  action: 'connect' | 'save_and_connect'
  user: string
  password: string
}

const props = defineProps<{
  visible: boolean
  title: string
  subtitle?: string
  fields: ('user' | 'password')[]
  initialUser?: string
  initialPassword?: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'resolve', result: CredentialResult | null): void
}>()

const { t } = useI18n()

const inputUser = ref('')
const inputPassword = ref('')
const userInputRef = ref<InputInstance | null>(null)
const passwordInputRef = ref<InputInstance | null>(null)

watch(() => props.visible, (v) => {
  if (v) {
    inputUser.value = props.initialUser || ''
    inputPassword.value = props.initialPassword || ''
  }
})

function onDialogOpened() {
  // Focus the first empty field, or username if both are filled
  if (props.fields.includes('password') && !inputPassword.value) {
    passwordInputRef.value?.focus()
  } else if (props.fields.includes('user') && !inputUser.value) {
    userInputRef.value?.focus()
  } else if (props.fields.includes('user')) {
    userInputRef.value?.focus()
  } else if (props.fields.includes('password')) {
    passwordInputRef.value?.focus()
  }
}

function onCancel() {
  emit('resolve', null)
}

function onSaveAndConnect() {
  emit('resolve', {
    action: 'save_and_connect',
    user: inputUser.value,
    password: inputPassword.value
  })
}

function onConnect() {
  emit('resolve', {
    action: 'connect',
    user: inputUser.value,
    password: inputPassword.value
  })
}
</script>

<style scoped>
.credential-subtitle {
  margin: 0 0 0.75rem 0;
  color: var(--el-text-color-secondary);
  font-size: 0.8125rem;
}
.credential-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.credential-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.credential-label {
  font-size: 0.8125rem;
  color: var(--el-text-color-regular);
}
</style>
