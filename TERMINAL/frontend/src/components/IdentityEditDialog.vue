<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="identity ? t('settings.editIdentity') : t('settings.addIdentity')"
    width="30rem"
    @update:model-value="v => emit('update:visible', v)"
  >
    <el-form label-width="5.625rem">
      <el-form-item :label="t('conn.name')">
        <el-input v-model="form.name" :placeholder="t('conn.namePlaceholder')" />
      </el-form-item>
      <el-form-item :label="t('conn.authType')">
        <el-radio-group v-model="form.authType">
          <el-radio-button value="password">{{ t('conn.password') }}</el-radio-button>
          <el-radio-button value="key">{{ t('conn.keyPath') }}</el-radio-button>
          <el-radio-button value="keyText">{{ t('conn.keyText') }}</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="t('conn.user')">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item v-if="form.authType === 'password'" :label="t('conn.password')">
        <el-input v-model="passwordInput" type="password" show-password />
      </el-form-item>
      <template v-else-if="form.authType === 'key'">
        <el-form-item :label="t('conn.keyPath')">
          <el-input v-model="form.keyPath" :placeholder="t('conn.keyPathPlaceholder')">
            <template #append>
              <el-tooltip :content="t('conn.selectKeyFile')" placement="top">
                <el-button :aria-label="t('conn.selectKeyFile')" @click="selectKeyFile">
                  <el-icon><FolderOpen :size="'1rem'" /></el-icon>
                </el-button>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item :label="t('conn.keyPassphrase')">
          <el-input v-model="passphraseInput" type="password" show-password :placeholder="t('conn.keyPassphrasePlaceholder')" />
        </el-form-item>
      </template>
      <template v-else>
        <el-form-item :label="t('conn.keyContent')">
          <template v-if="!keyContentRevealed">
            <el-button size="small" @click="keyContentRevealed = true">
              <el-icon><Eye :size="'0.875rem'" /></el-icon>
              <span style="margin-left: 0.25rem">{{ t('conn.keyTextReveal') }}</span>
            </el-button>
          </template>
          <template v-else>
            <el-input
              v-model="form.keyContent"
              type="textarea"
              :rows="7"
              class="key-text-area mono"
              :placeholder="t('conn.keyContentPlaceholder')"
              spellcheck="false"
            />
            <div class="key-content-actions">
              <el-button size="small" @click="keyContentRevealed = false">
                <el-icon><EyeOff :size="'0.875rem'" /></el-icon>
                <span style="margin-left: 0.25rem">{{ t('conn.keyTextHide') }}</span>
              </el-button>
              <el-button size="small" @click="importKeyText">
                <el-icon><FolderOpen :size="'0.875rem'" /></el-icon>
                <span style="margin-left: 0.25rem">{{ t('conn.importFromFile') }}</span>
              </el-button>
            </div>
          </template>
        </el-form-item>
        <el-form-item :label="t('conn.keyPassphrase')">
          <el-input v-model="passphraseInput" type="password" show-password :placeholder="t('conn.keyPassphrasePlaceholder')" />
        </el-form-item>
      </template>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="save">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useI18n } from '../i18n'
import { ElMessage } from 'element-plus'
import { OpenFileDialog, OpenPrivateKeyFile } from '../../bindings/easyaiot/terminal/app'
import { backendErrorText } from '../utils/backendError'
import { FolderOpen, Eye, EyeOff } from '@lucide/vue'
import { useIdentityStore } from '../stores/identityStore'
import type { Identity } from '../types/identity'

const props = defineProps<{ visible: boolean; identity: Identity | null }>()
// `saved` carries the persisted entity so callers (e.g. the connection form's
// "+" button) can select the just-created item. Settings' handler ignores it.
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'saved', entity: Identity): void }>()
const { t } = useI18n()
const store = useIdentityStore()

function newId(): string {
  // crypto.randomUUID() may be unavailable in the Wails/webview runtime, so
  // fall back to the same timestamp+random scheme used for connection IDs.
  return `id-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

const form = reactive<Identity>({ id: '', name: '', username: '', authType: 'password', password: '', keyPath: '', keyContent: '' })

// The persisted Identity carries a single `password` field that doubles as the
// login password (authType "password") and the private-key passphrase
// (authType "key"). Binding both inputs to it made them move together, so each
// mode gets its own local state and only the active one is written on save.
const passwordInput = ref('')
const passphraseInput = ref('')
// keyContentRevealed gates the keyText paste area: hidden behind a single "show"
// button by default so the PEM is never on screen until the user asks to see it.
const keyContentRevealed = ref(false)

watch(() => props.visible, (v) => {
  if (v) {
    // Always re-hide the keyText paste area when opening, so a prior reveal in
    // another identity can't leak into this edit.
    keyContentRevealed.value = false
    Object.assign(form, props.identity ?? { id: newId(), name: '', username: '', authType: 'password', password: '', keyPath: '', keyContent: '' })
    // Hydrate only the field matching the stored authType; the other mode
    // starts empty rather than echoing an unrelated secret.
    passwordInput.value = form.authType === 'password' ? (form.password ?? '') : ''
    passphraseInput.value = (form.authType === 'key' || form.authType === 'keyText') ? (form.password ?? '') : ''
  }
})

async function selectKeyFile() {
  try {
    const p = await OpenFileDialog('~/.ssh')
    if (p) form.keyPath = p
  } catch (e) { console.error('select key file:', e) }
}

async function importKeyText() {
  try {
    const content = await OpenPrivateKeyFile()
    if (content) {
      form.keyContent = content
      keyContentRevealed.value = true
    }
  } catch (e: any) {
    ElMessage.error(backendErrorText(e))
  }
}

// importKeyText picks a private-key file on disk and pastes its content into the
// keyText textarea (backend reads + validates the PEM).
async function save() {
  if (!form.name.trim()) { ElMessage.warning(t('settings.identityNameRequired')); return }
  const entity: Identity = {
    ...form,
    password: (form.authType === 'key' || form.authType === 'keyText') ? passphraseInput.value : passwordInput.value,
  }
  // 只保留当前认证方式对应的密钥字段，避免切换后残留路径/密钥文本。
  if (form.authType !== 'key') entity.keyPath = undefined
  if (form.authType !== 'keyText') entity.keyContent = undefined
  if (props.identity) await store.update(entity)
  else await store.add(entity)
  ElMessage.success(t('settings.saved'))
  emit('saved', entity)
  emit('update:visible', false)
}
</script>

<style scoped>
.key-text-area :deep(textarea) {
  font-family: var(--font-mono, ui-monospace, "JetBrains Mono", monospace);
}
.key-content-actions {
  margin-top: 0.375rem;
}
.key-content-actions .el-button + .el-button {
  margin-left: 0.5rem;
}
</style>

