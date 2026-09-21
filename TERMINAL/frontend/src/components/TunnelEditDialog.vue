<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="editingId ? t('tunnels.editTunnel') : t('tunnels.addTunnel')"
    width="31.25rem"
    class="tunnel-dialog"
    @close="resetForm"
  >
    <!-- Tunnel mode: same look as the connection form's type selection -->
    <div class="mode-section">
      <div class="mode-grid">
        <button
          v-for="m in modes"
          :key="m.value"
          type="button"
          class="mode-btn"
          :class="{ active: form.mode === m.value }"
          @click="form.mode = m.value"
        >
          <component :is="m.icon" :size="'1.125rem'" />
          <span>{{ m.label }}</span>
        </button>
      </div>
      <div class="mode-desc">{{ t(`tunnels.hint.${form.mode}`) }}</div>
    </div>

    <el-form :model="form" label-width="5.625rem">
      <el-form-item :label="t('tunnels.name')" required>
        <el-input v-model="form.name" :placeholder="t('tunnels.namePlaceholder')" maxlength="50" />
      </el-form-item>

      <el-form-item :label="t('tunnels.sshConn')" required>
        <el-select v-model="form.sshConnId" :placeholder="t('tunnels.sshConnPlaceholder')" filterable class="full">
          <el-option
            v-for="c in sshConnections"
            :key="c.id"
            :label="`${c.name} (${c.user}@${c.host}:${c.port})`"
            :value="c.id"
          />
        </el-select>
      </el-form-item>

      <!-- Local -->
      <template v-if="form.mode === 'local'">
        <el-form-item :label="t('tunnels.listenLocal')" required>
          <div class="hostport">
            <el-input v-model="form.listenHost" placeholder="127.0.0.1" />
            <span class="colon">:</span>
            <el-input-number v-model="form.listenPort" :min="1" :max="65535" :controls="false" :placeholder="'13306'" />
          </div>
        </el-form-item>
        <el-form-item :label="t('tunnels.destination')" required>
          <div class="hostport">
            <el-input v-model="form.targetHost" placeholder="10.0.1.20" />
            <span class="colon">:</span>
            <el-input-number v-model="form.targetPort" :min="1" :max="65535" :controls="false" :placeholder="'3306'" />
          </div>
        </el-form-item>
      </template>

      <!-- Remote -->
      <template v-else-if="form.mode === 'remote'">
        <el-form-item :label="t('tunnels.listenRemote')" required>
          <div class="hostport">
            <el-input v-model="form.listenHost" placeholder="0.0.0.0" />
            <span class="colon">:</span>
            <el-input-number v-model="form.listenPort" :min="1" :max="65535" :controls="false" :placeholder="'8022'" />
          </div>
        </el-form-item>
        <el-form-item :label="t('tunnels.toLocal')" required>
          <div class="hostport">
            <el-input v-model="form.targetHost" placeholder="127.0.0.1" />
            <span class="colon">:</span>
            <el-input-number v-model="form.targetPort" :min="1" :max="65535" :controls="false" :placeholder="'22'" />
          </div>
        </el-form-item>
      </template>

      <!-- Dynamic -->
      <template v-else>
        <el-form-item :label="t('tunnels.listenLocal')" required>
          <div class="hostport">
            <el-input v-model="form.listenHost" placeholder="127.0.0.1" />
            <span class="colon">:</span>
            <el-input-number v-model="form.listenPort" :min="1" :max="65535" :controls="false" :placeholder="'1080'" />
          </div>
        </el-form-item>
      </template>

      <el-form-item :label="t('tunnels.autoStartLabel')">
        <el-switch v-model="form.autoStart" />
        <span class="inline-hint">{{ t('tunnels.autoStart') }}</span>
      </el-form-item>

      <!-- Equivalent ssh command, as a form row: mirrors the values above so
           users can verify what the fields map to -->
      <el-form-item :label="t('tunnels.sshExample')">
        <code class="se-cmd">{{ sshExample }}</code>
        <div v-if="needsGatewayHint" class="se-hint">{{ t('tunnels.sshExampleGatewayHint') }}</div>
      </el-form-item>
    </el-form>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button
        :loading="testing"
        :disabled="testing || editRunning"
        :title="editRunning ? t('tunnels.testDisabledRunning') : undefined"
        @click="handleTest"
      >{{ t('tunnels.test') }}</el-button>
      <el-button @click="visible = false">{{ t('tunnels.cancel') }}</el-button>
      <el-button type="primary" @click="handleSave">{{ t('tunnels.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ArrowRightToLine, ArrowLeftToLine, Waypoints } from '@lucide/vue'
import { useTunnelStore, type TunnelMode } from '../stores/tunnelStore'
import { useConnectionStore } from '../stores/connectionStore'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { useTunnelCredentials } from '../composables/useTunnelCredentials'
import { TestTunnel } from '../../bindings/easyaiot/terminal/app'

const { t } = useI18n()
const store = useTunnelStore()
const connectionStore = useConnectionStore()
const { resolveTunnelCredentials } = useTunnelCredentials()

const props = defineProps<{
  modelValue: boolean
  editingId?: string
  initialGroupId?: string
}>()

const emit = defineEmits<{ 'update:modelValue': [v: boolean] }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const sshConnections = computed(() =>
  connectionStore.connections
    .filter(c => c.type === 'ssh')
    .sort((a, b) => a.name.localeCompare(b.name))
)

const modes = computed(() => [
  { value: 'local' as TunnelMode, label: t('tunnels.mode.local'), icon: ArrowRightToLine },
  { value: 'remote' as TunnelMode, label: t('tunnels.mode.remote'), icon: ArrowLeftToLine },
  { value: 'dynamic' as TunnelMode, label: t('tunnels.mode.dynamic'), icon: Waypoints },
])

function blankForm() {
  return {
    name: '',
    sshConnId: '',
    mode: 'local' as TunnelMode,
    listenHost: '127.0.0.1',
    listenPort: undefined as number | undefined,
    targetHost: '',
    targetPort: undefined as number | undefined,
    autoStart: false,
    groupId: undefined as string | undefined,
  }
}

const form = reactive(blankForm())
const errorMsg = ref('')

watch(visible, (v) => {
  // Hide the native RDP window while the dialog is open so it isn't covered (issue #346)
  window.dispatchEvent(new CustomEvent(v ? 'rdp:overlay-push' : 'rdp:overlay-pop'))
  if (!v) return
  errorMsg.value = ''
  if (props.editingId) {
    const t0 = store.tunnels.find(x => x.id === props.editingId)
    if (t0) {
      Object.assign(form, blankForm(), {
        name: t0.name,
        sshConnId: t0.sshConnId,
        mode: t0.mode,
        listenHost: t0.listenHost || '127.0.0.1',
        listenPort: t0.listenPort,
        targetHost: t0.targetHost || '',
        targetPort: t0.targetPort,
        autoStart: !!t0.autoStart,
        groupId: t0.groupId,
      })
    }
  } else {
    Object.assign(form, blankForm(), { groupId: props.initialGroupId })
  }
})

// Editing a tunnel that is currently running: a test would grab the same
// ports the live tunnel already holds, so disable it.
const editRunning = computed(() => !!props.editingId && store.statusOf(props.editingId) === 'running')

const testing = ref(false)

// Shared by save and test: returns the validation message, or '' when valid.
function validate(): string {
  if (!form.sshConnId) return t('tunnels.errConn')
  if (!form.listenPort) return t('tunnels.errListenPort')
  if (form.mode !== 'dynamic' && (!form.targetHost.trim() || !form.targetPort)) return t('tunnels.errTarget')
  return ''
}

function formPayload() {
  return {
    id: props.editingId || '',
    name: form.name.trim(),
    mode: form.mode,
    sshConnId: form.sshConnId,
    listenHost: form.listenHost.trim() || '127.0.0.1',
    listenPort: form.listenPort,
    targetHost: form.mode === 'dynamic' ? undefined : form.targetHost.trim(),
    targetPort: form.mode === 'dynamic' ? undefined : form.targetPort,
    autoStart: form.autoStart,
    groupId: form.groupId,
  }
}

async function handleTest() {
  const invalid = validate()
  if (invalid) { errorMsg.value = invalid; return }
  // Exit connection without saved credentials: prompt for user/password and
  // pass them inline (backend fills only empty fields). Cancel aborts the test.
  const creds = await resolveTunnelCredentials(form.sshConnId)
  if (!creds) return
  testing.value = true
  try {
    const st = await TestTunnel(formPayload(), creds.user, creds.password)
    if (st.status === 'running') {
      msg.success(t('tunnels.testOk'))
    } else {
      msg.error(st.error || t('tunnels.testFailed'))
    }
  } catch (e: any) {
    msg.error(String(e) || t('tunnels.testFailed'))
  } finally {
    testing.value = false
  }
}

function handleSave() {
  if (!form.name.trim()) { errorMsg.value = t('tunnels.errName'); return }
  const invalid = validate()
  if (invalid) { errorMsg.value = invalid; return }
  const payload = formPayload()
  delete payload.id
  if (props.editingId) {
    store.updateTunnel(props.editingId, payload)
  } else {
    store.addTunnel(payload)
  }
  visible.value = false
}

function resetForm() {
  Object.assign(form, blankForm())
  errorMsg.value = ''
}

// Equivalent ssh command — same syntax OpenSSH accepts, so the user can
// cross-check the form against a command line they already know works.
const sshExample = computed(() => {
  const lh = (form.listenHost || '').trim() || '127.0.0.1'
  const lp = form.listenPort || '<port>'
  const th = (form.targetHost || '').trim() || '<targetHost>'
  const tp = form.targetPort || '<targetPort>'
  if (form.mode === 'local') return `ssh -L ${lh}:${lp}:${th}:${tp}`
  if (form.mode === 'remote') return `ssh -R ${lh}:${lp}:${th}:${tp}`
  return `ssh -D ${lh}:${lp}`
})

// A non-loopback remote bind only works when the server's sshd allows it.
const needsGatewayHint = computed(() => {
  const lh = (form.listenHost || '').trim() || '127.0.0.1'
  return form.mode === 'remote' && !['127.0.0.1', 'localhost', '::1'].includes(lh)
})
</script>

<style scoped>
.full { width: 100%; }
.tunnel-dialog :deep(.el-select) { width: 100%; }
.inline-hint { font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.625rem; }
.hostport { display: grid; grid-template-columns: 1fr auto 7.5rem; gap: 0.5rem; align-items: center; width: 100%; }
.hostport .colon { color: var(--text-muted); text-align: center; }
.hostport :deep(.el-input-number) { width: 100%; }
.form-error { color: var(--error); font-size: 0.75rem; margin-top: 0.125rem; }

/* Equivalent ssh command row (a form item like the fields above) */
.se-cmd {
  font-family: var(--font-mono, monospace); font-size: 0.75rem; color: var(--text-primary);
  word-break: break-all; user-select: all;
}
.se-hint { width: 100%; font-size: 0.6875rem; color: var(--warning, #e0a54b); line-height: 1.4; }

/* Mode buttons: identical look to the connection form's sub-type selection */
.mode-section {
  padding-bottom: 0.875rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}
.mode-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.375rem;
}
.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1875rem;
  width: 5rem;
  height: 3.5rem;
  padding: 0.25rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}
.mode-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.mode-btn.active {
  background: linear-gradient(135deg, var(--accent), var(--accent));
  color: var(--on-accent);
  border-color: var(--accent-glow);
  box-shadow: 0 0 0 1px var(--accent-glow), 0 0.125rem 0.5rem var(--accent-glow);
}
.mode-btn span {
  text-align: center;
  line-height: 1.2;
}
.mode-desc {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.5;
  text-align: center;
}

/* ── Dialog overrides ── */
:deep(.el-dialog__body) {
  padding: 1rem 1.25rem;
}
</style>
