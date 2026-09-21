<template>
  <el-dialog append-to-body
    v-model="visible"
    :title="editingId ? t('quickCommands.editCommand') : t('quickCommands.addCommand')"
    width="38.75rem"
    :close-on-click-modal="false"
    @close="resetForm"
  >
    <el-form label-width="3.75rem">
      <el-form-item :label="t('quickCommands.name')">
        <el-input
          v-model="formName"
          :placeholder="t('quickCommands.namePlaceholder')"
          maxlength="50"
        />
      </el-form-item>
      <el-form-item :label="t('quickCommands.remark')">
        <el-input
          v-model="formRemark"
          type="textarea"
          :rows="2"
          :placeholder="t('quickCommands.remarkPlaceholder')"
        />
      </el-form-item>
      <el-form-item :label="t('quickCommands.group')">
        <el-select v-model="formGroupId" :placeholder="t('quickCommands.noGroup')" clearable @change="onGroupSelect">
          <el-option
            v-for="g in store.groups"
            :key="g.id"
            :label="g.name"
            :value="g.id"
          />
          <el-option :label="t('conn.noGroup')" value="" />
          <el-option :label="t('conn.newGroup')" value="__new__" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('quickCommands.command')">
        <el-input
          v-model="formCommand"
          type="textarea"
          :rows="10"
          :placeholder="t('quickCommands.commandPlaceholder')"
          class="command-textarea"
        />
      </el-form-item>
    </el-form>

    <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

    <template #footer>
      <el-button @click="visible = false">{{ t('quickCommands.cancel') }}</el-button>
      <el-button type="primary" :disabled="!formCommand.trim()" @click="handleSave">
        {{ t('quickCommands.save') }}
      </el-button>
    </template>
  </el-dialog>

  <!-- New group dialog -->
  <el-dialog append-to-body v-model="showNewGroupDialog" :title="t('conn.newGroupTitle')" width="22.5rem" :close-on-click-modal="false">
    <el-form @submit.prevent="confirmNewGroup">
      <el-form-item :label="t('conn.groupName')">
        <el-input v-model="newGroupName" :placeholder="t('conn.groupNamePlaceholder')" @keyup.enter="confirmNewGroup" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showNewGroupDialog = false">{{ t('conn.cancel') }}</el-button>
      <el-button type="primary" :disabled="!newGroupName.trim()" @click="confirmNewGroup">{{ t('conn.save') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuickCommandStore } from '../stores/quickCommandStore'
import { useI18n } from '../i18n'

const { t } = useI18n()
const store = useQuickCommandStore()

const props = defineProps<{
  modelValue: boolean
  editingId?: string
  initialName?: string
  initialCommand?: string
  initialGroupId?: string
  initialRemark?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const formName = ref('')
const formRemark = ref('')
const formCommand = ref('')
const formGroupId = ref<string | undefined>(undefined)
const errorMsg = ref('')

watch(visible, (v) => {
  if (v) {
    formName.value = props.initialName || ''
    formRemark.value = props.initialRemark || ''
    formCommand.value = props.initialCommand || ''
    formGroupId.value = props.initialGroupId || undefined
    errorMsg.value = ''
  }
})

function handleSave() {
  const cmd = formCommand.value.trim()
  if (!cmd) {
    errorMsg.value = t('quickCommands.commandRequired')
    return
  }
  const remark = formRemark.value.trim()
  if (props.editingId) {
    store.updateCommand(props.editingId, formName.value || undefined, cmd, formGroupId.value || undefined, remark)
  } else {
    store.addCommand(formName.value || undefined, cmd, formGroupId.value || undefined, remark)
  }
  visible.value = false
  resetForm()
}

const showNewGroupDialog = ref(false)
const newGroupName = ref('')

function onGroupSelect(value: string) {
  if (value === '__new__') {
    formGroupId.value = undefined
    showNewGroupDialog.value = true
  }
}

function confirmNewGroup() {
  const name = newGroupName.value.trim()
  if (!name) return
  const group = store.addGroup(name)
  formGroupId.value = group.id
  showNewGroupDialog.value = false
  newGroupName.value = ''
}

function resetForm() {
  formName.value = ''
  formRemark.value = ''
  formCommand.value = ''
  formGroupId.value = undefined
  errorMsg.value = ''
}
</script>

<style scoped>
.command-textarea :deep(textarea) {
  font-family: var(--font-mono, 'Consolas', 'Courier New', monospace);
}
.form-error {
  color: var(--error);
  font-size: 0.75rem;
  margin-top: -0.5rem;
  margin-bottom: 0.5rem;
}
</style>
