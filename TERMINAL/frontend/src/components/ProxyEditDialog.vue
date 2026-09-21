<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="proxy ? t('settings.editProxy') : t('settings.addProxy')"
    width="30rem"
    @update:model-value="v => emit('update:visible', v)"
  >
    <el-form label-width="5.625rem">
      <el-form-item :label="t('conn.name')">
        <el-input v-model="form.name" :placeholder="t('conn.namePlaceholder')" />
      </el-form-item>
      <el-form-item :label="t('conn.proxyType')">
        <el-radio-group v-model="form.kind">
          <el-radio-button value="socks5">SOCKS5</el-radio-button>
          <el-radio-button value="http">HTTP</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="t('conn.host')">
        <el-input v-model="form.host" placeholder="127.0.0.1" />
      </el-form-item>
      <el-form-item :label="t('conn.port')">
        <el-input-number v-model="form.port" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item :label="t('conn.user')">
        <el-input v-model="form.user" />
      </el-form-item>
      <el-form-item :label="t('conn.password')">
        <el-input v-model="form.pass" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:visible', false)">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="save">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { useI18n } from '../i18n'
import { ElMessage } from 'element-plus'
import { useProxyStore } from '../stores/proxyStore'
import type { Proxy } from '../types/proxy'

const props = defineProps<{ visible: boolean; proxy: Proxy | null }>()
// `saved` carries the persisted entity so callers (e.g. the connection form's
// "+" button) can select the just-created item. Settings' handler ignores it.
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'saved', entity: Proxy): void }>()
const { t } = useI18n()
const store = useProxyStore()

function newId(): string {
  return `px-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

const form = reactive<Proxy>({ id: '', name: '', kind: 'socks5', host: '', port: 1080, user: '', pass: '' })

watch(() => props.visible, (v) => {
  if (v) {
    Object.assign(form, props.proxy ?? { id: newId(), name: '', kind: 'socks5', host: '', port: 1080, user: '', pass: '' })
  }
})

async function save() {
  if (!form.name.trim()) { ElMessage.warning(t('settings.proxyNameRequired')); return }
  if (!form.host.trim()) { ElMessage.warning(t('settings.proxyHostRequired')); return }
  const entity = { ...form }
  if (props.proxy) await store.update(entity)
  else await store.add(entity)
  ElMessage.success(t('settings.saved'))
  emit('saved', entity)
  emit('update:visible', false)
}
</script>
