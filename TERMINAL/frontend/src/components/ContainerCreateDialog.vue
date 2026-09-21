<template>
  <el-dialog
    append-to-body
    v-model="visible"
    :title="t('container.create')"
    width="35rem"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form label-width="6.875rem" size="small">
      <el-form-item :label="t('container.createDialog.image')" required :error="imageError">
        <el-input v-model="form.image" placeholder="nginx:latest" @input="imageError = ''" />
      </el-form-item>
      <el-form-item :label="t('container.createDialog.name')">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('container.createDialog.ports')">
        <div class="rows">
          <div v-for="(p, i) in form.ports" :key="i" class="row">
            <el-input
              v-model="p.hostPort"
              placeholder="8080"
              class="port-input"
              :class="{ 'row-error': portErrors[i] }"
              @input="portErrors[i] = false"
            />
            <span class="row-sep">:</span>
            <el-input
              v-model="p.containerPort"
              placeholder="80"
              class="port-input"
              :class="{ 'row-error': portErrors[i] }"
              @input="portErrors[i] = false"
            />
            <el-select v-model="p.protocol" class="proto-select">
              <el-option label="tcp" value="tcp" />
              <el-option label="udp" value="udp" />
            </el-select>
            <el-button link size="small" :icon="Trash2" @click="removePort(i)" />
          </div>
          <el-button link size="small" :icon="Plus" @click="addPort">{{ t('container.createDialog.addRow') }}</el-button>
        </div>
      </el-form-item>
      <el-form-item :label="t('container.createDialog.volumes')">
        <div class="rows">
          <div v-for="(_, i) in form.volumes" :key="i" class="row">
            <el-input v-model="form.volumes[i]" placeholder="/host/path:/container/path" />
            <el-button link size="small" :icon="Trash2" @click="form.volumes.splice(i, 1)" />
          </div>
          <el-button link size="small" :icon="Plus" @click="form.volumes.push('')">{{ t('container.createDialog.addRow') }}</el-button>
        </div>
      </el-form-item>
      <el-form-item :label="t('container.createDialog.env')">
        <div class="rows">
          <div v-for="(_, i) in form.env" :key="i" class="row">
            <el-input v-model="form.env[i]" placeholder="KEY=VALUE" />
            <el-button link size="small" :icon="Trash2" @click="form.env.splice(i, 1)" />
          </div>
          <el-button link size="small" :icon="Plus" @click="form.env.push('')">{{ t('container.createDialog.addRow') }}</el-button>
        </div>
      </el-form-item>
      <el-form-item :label="t('container.createDialog.restart')">
        <el-select v-model="form.restart" class="restart-select">
          <el-option v-for="r in restartOptions" :key="r" :label="r" :value="r" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('container.createDialog.command')">
        <el-input v-model="form.command" placeholder="sleep 3600" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="creating" @click="onSubmit">{{ t('container.createDialog.create') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Trash2 } from '@lucide/vue'
import { useI18n } from '../i18n'
import { useContainerStore } from '../stores/containerStore'
import type { ContainerCreateOptions } from '../types/container'

const props = defineProps<{ modelValue: boolean; tabId: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void; (e: 'created'): void }>()

const { t } = useI18n()
const store = useContainerStore()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

interface PortRow { hostPort: string; containerPort: string; protocol: string }

const restartOptions = ['no', 'always', 'unless-stopped', 'on-failure']

const form = reactive({
  image: '',
  name: '',
  ports: [] as PortRow[],
  volumes: [] as string[],
  env: [] as string[],
  restart: 'no',
  command: '',
})
const creating = ref(false)
const imageError = ref('')
const portErrors = ref<boolean[]>([])

watch(() => props.modelValue, (v) => { if (v) resetForm() })

function resetForm() {
  form.image = ''
  form.name = ''
  form.ports = []
  form.volumes = []
  form.env = []
  form.restart = 'no'
  form.command = ''
  imageError.value = ''
  portErrors.value = []
}

function addPort() {
  form.ports.push({ hostPort: '', containerPort: '', protocol: 'tcp' })
  portErrors.value.push(false)
}
function removePort(i: number) {
  form.ports.splice(i, 1)
  portErrors.value.splice(i, 1)
}

function portRowInvalid(p: PortRow): boolean {
  const h = p.hostPort.trim()
  const c = p.containerPort.trim()
  if (!h && !c) return false
  return !/^\d+$/.test(h) || !/^\d+$/.test(c)
}

function buildOptions(): ContainerCreateOptions {
  return {
    image: form.image.trim(),
    name: form.name.trim(),
    ports: form.ports.filter(p => p.hostPort.trim() && p.containerPort.trim())
      .map(p => ({ hostPort: p.hostPort.trim(), containerPort: p.containerPort.trim(), protocol: p.protocol || 'tcp' })),
    volumes: form.volumes.map(v => v.trim()).filter(Boolean),
    env: form.env.map(e => e.trim()).filter(Boolean),
    restart: form.restart,
    command: form.command.trim() ? form.command.trim().split(/\s+/) : [],
  }
}

async function onSubmit() {
  if (!form.image.trim()) {
    imageError.value = t('container.createDialog.imageRequired')
    ElMessage.error(t('container.createDialog.imageRequired'))
    return
  }
  portErrors.value = form.ports.map(portRowInvalid)
  if (portErrors.value.some(Boolean)) {
    ElMessage.error(t('container.createDialog.portInvalid'))
    return
  }
  creating.value = true
  try {
    await store.createContainer(props.tabId, buildOptions())
    ElMessage.success(t('container.createDialog.created'))
    emit('created')
    visible.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || String(e))
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.rows {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  width: 100%;
}

.row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.row-sep {
  color: var(--text-muted);
  flex-shrink: 0;
}

.port-input {
  width: 6.875rem;
}

.proto-select {
  width: 5.625rem;
}

.restart-select {
  width: 11.25rem;
}

.row-error :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-color-danger) inset;
}
</style>
