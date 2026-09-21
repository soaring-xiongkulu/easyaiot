<template>
  <div class="commands-manager">
    <div class="commands-toolbar">
      <el-input
        v-model="searchQuery"
        size="small"
        :placeholder="t('settings.commandsSearch')"
        style="flex: 1"
        clearable
      >
        <template #prefix><el-icon :size="'0.875rem'"><Search /></el-icon></template>
      </el-input>
      <el-button size="small" @click="showCreate = true">
        <Plus :size="'0.875rem'" /> {{ t('settings.commandsCreate') }}
      </el-button>
    </div>

    <div v-if="filteredCommands.length === 0" class="commands-empty">
      {{ t('settings.commandsNoCommand') }}
    </div>

    <div
      v-for="cmd in filteredCommands"
      :key="cmd.name"
      class="command-card"
      @click="openEdit(cmd)"
    >
      <Terminal :size="'1.125rem'" class="command-card-icon" />
      <div class="command-card-info">
        <div class="command-card-title">
          <span class="command-card-name">{{ cmd.name }}</span>
        </div>
        <div class="command-card-desc">{{ cmd.description }}</div>
        <div v-if="cmd.path" class="command-card-path" @click.stop="openFolder(cmd)" :title="t('settings.commandsOpenFolder')">
          <FolderOpen :size="'0.75rem'" class="command-card-path-icon" />
          <span class="command-card-path-text">{{ cmd.path }}</span>
        </div>
      </div>
      <div class="command-card-actions" @click.stop>
        <el-switch
          :model-value="cmd.enabled"
          size="small"
          @change="store.toggleEnabled(cmd.name)"
        />
        <el-button
          link
          :title="cmd.locked ? t('settings.commandsLocked') : t('settings.commandsUnlocked')"
          @click="store.toggleLocked(cmd.name)"
        >
          <el-icon :size="'0.9375rem'"><Lock v-if="cmd.locked" /><LockOpen v-else /></el-icon>
        </el-button>
        <el-button link @click.stop="actionMenuRef?.toggle($event.currentTarget, cmd)">
          <el-icon :size="'0.9375rem'"><Settings2 /></el-icon>
        </el-button>
        <Menu ref="actionMenuRef" v-model:visible="actionMenuVisible">
          <template #default="{ current }">
            <MenuItem @click="onAction('edit', current)">{{ t('settings.commandsEdit') }}</MenuItem>
            <MenuDivider />
            <MenuItem class="danger" @click="onAction('delete', current)">{{ t('settings.commandsDelete') }}</MenuItem>
          </template>
        </Menu>
      </div>
    </div>

    <CommandCreateDialog
      v-if="showCreate"
      @close="showCreate = false"
      @created="onCreated"
    />

    <!-- 编辑弹窗（锁定则只读 + 提示解锁） -->
    <el-dialog
      v-model="showEdit"
      :title="editCommand ? '/' + editCommand.name : ''"
      width="37.5rem"
    >
      <div v-if="editCommand" class="command-edit">
        <el-alert
          v-if="editCommand.locked"
          :title="t('settings.commandsEditLocked')"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 0.75rem"
        />
        <el-form label-position="right" label-width="3.75rem" size="small">
          <el-form-item :label="t('settings.commandsDescription')">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="2"
              :disabled="editCommand.locked"
            />
          </el-form-item>
          <el-form-item :label="t('settings.commandsArgumentHint')">
            <el-input
              v-model="editForm.argumentHint"
              :placeholder="t('settings.commandsArgumentHintPlaceholder')"
              :disabled="editCommand.locked"
            />
          </el-form-item>
          <el-form-item :label="t('settings.commandsBody')">
            <el-input
              v-model="editForm.body"
              type="textarea"
              :rows="12"
              :disabled="editCommand.locked"
            />
          </el-form-item>
        </el-form>
        <p class="command-args-hint">{{ t('settings.commandsArgumentsHint') }}</p>
      </div>
      <template #footer>
        <el-button @click="showEdit = false">{{ t('common.cancel') }}</el-button>
        <el-button
          type="primary"
          :disabled="editCommand?.locked || !editForm.body.trim()"
          @click="onSaveEdit"
        >
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Lock, LockOpen, Settings2, Search, Terminal, FolderOpen } from '@lucide/vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { useCommandStore } from '../stores/commandStore'
import CommandCreateDialog from './CommandCreateDialog.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import type { CommandMeta } from '../types/command'

const { t } = useI18n()
const store = useCommandStore()

const showCreate = ref(false)
const searchQuery = ref('')

const actionMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const actionMenuVisible = ref(false)
function onAction(action: string, cmd?: unknown) {
  actionMenuVisible.value = false
  handleCmd(action, cmd as CommandMeta)
}

const showEdit = ref(false)
const editCommand = ref<CommandMeta | null>(null)
const editForm = ref({ description: '', argumentHint: '', body: '' })

const filteredCommands = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return store.commands
  return store.commands.filter(c => c.name.toLowerCase().includes(q) || c.description.toLowerCase().includes(q))
})

async function openEdit(cmd: CommandMeta) {
  editCommand.value = cmd
  editForm.value = { description: cmd.description, argumentHint: cmd.argumentHint || '', body: '' }
  showEdit.value = true
  try {
    editForm.value.body = await store.getBody(cmd.name)
  } catch (e) {
    editForm.value.body = ''
  }
}

async function onSaveEdit() {
  if (!editCommand.value) return
  try {
    await store.save(editCommand.value.name, editForm.value.description.trim(), editForm.value.body.trim(), editForm.value.argumentHint.trim())
    showEdit.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || 'Save failed')
  }
}

function handleCmd(action: string, cmd: CommandMeta) {
  if (action === 'delete') onDelete(cmd)
  else if (action === 'edit') openEdit(cmd)
}

function openFolder(cmd: CommandMeta) {
  store.openFolder(cmd.path)
}

async function onDelete(cmd: CommandMeta) {
  if (cmd.locked) {
    ElMessage.warning(t('settings.commandsDeleteLocked', { name: cmd.name }))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('settings.commandsDeleteConfirm', { name: cmd.name }),
      t('settings.commandsDelete')
    )
    await store.remove(cmd.name)
  } catch {
    // cancelled
  }
}

function onCreated() {
  showCreate.value = false
  store.reload()
}

onMounted(() => {
  store.load()
})
</script>

<style scoped>
.commands-manager {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}
.commands-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.commands-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
.command-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.command-card:hover {
  border-color: var(--el-color-primary);
}
.command-card-icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}
.command-card-info {
  flex: 1;
  min-width: 0;
}
.command-card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.command-card-name {
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--el-text-color-primary);
}
.command-card-desc {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-top: 0.125rem;
}
.command-card-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}
.command-card-path {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.25rem;
  font-size: 0.6875rem;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  width: fit-content;
  max-width: 100%;
}
.command-card-path:hover {
  color: var(--el-color-primary);
}
.command-card-path-icon {
  flex-shrink: 0;
}
.command-card-path-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: rtl;
  text-align: left;
}
.command-args-hint {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  margin: 0.25rem 0 0;
  line-height: 1.5;
}
</style>
