<template>
  <div class="skills-manager">
    <div class="skills-toolbar">
      <el-input
        v-model="searchQuery"
        size="small"
        :placeholder="t('settings.skillsSearch')"
        style="flex: 1"
        clearable
      >
        <template #prefix><el-icon :size="'0.875rem'"><Search /></el-icon></template>
      </el-input>
      <el-button size="small" @click="showCreate = true">
        <Plus :size="'0.875rem'" /> {{ t('settings.skillsCreate') }}
      </el-button>
    </div>

    <div v-if="filteredSkills.length === 0" class="skills-empty">
      {{ t('settings.skillsNoSkill') }}
    </div>

    <div
      v-for="skill in filteredSkills"
      :key="skill.name"
      class="skill-card"
      @click="openEdit(skill)"
    >
      <BookOpen :size="'1.125rem'" class="skill-card-icon" />
      <div class="skill-card-info">
        <div class="skill-card-title">
          <span class="skill-card-name">{{ skill.name }}</span>
        </div>
        <div class="skill-card-desc">{{ skill.description }}</div>
        <div v-if="skill.path" class="skill-card-path" @click.stop="openFolder(skill)" :title="t('settings.skillsOpenFolder')">
          <FolderOpen :size="'0.75rem'" class="skill-card-path-icon" />
          <span class="skill-card-path-text">{{ skill.path }}</span>
        </div>
      </div>
      <div class="skill-card-actions" @click.stop>
        <el-switch
          :model-value="skill.enabled"
          size="small"
          @change="store.toggleEnabled(skill.name)"
        />
        <el-button
          link
          :title="skill.locked ? t('settings.skillsLocked') : t('settings.skillsUnlocked')"
          @click="store.toggleLocked(skill.name)"
        >
          <el-icon :size="'0.9375rem'"><Lock v-if="skill.locked" /><LockOpen v-else /></el-icon>
        </el-button>
        <el-button link @click.stop="actionMenuRef?.toggle($event.currentTarget, skill)">
          <el-icon :size="'0.9375rem'"><Settings2 /></el-icon>
        </el-button>
        <Menu ref="actionMenuRef" v-model:visible="actionMenuVisible">
          <template #default="{ current }">
            <MenuItem @click="onAction('edit', current)">{{ t('settings.skillsEdit') }}</MenuItem>
            <MenuDivider />
            <MenuItem class="danger" @click="onAction('delete', current)">{{ t('settings.skillsDelete') }}</MenuItem>
          </template>
        </Menu>
      </div>
    </div>

    <SkillCreateDialog
      v-if="showCreate"
      @close="showCreate = false"
      @created="onCreated"
    />

    <!-- 编辑弹窗（锁定则只读 + 提示解锁） -->
    <el-dialog
      v-model="showEdit"
      :title="editSkill?.name"
      width="37.5rem"
    >
      <div v-if="editSkill" class="skill-edit">
        <el-alert
          v-if="editSkill.locked"
          :title="t('settings.skillsEditLocked')"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 0.75rem"
        />
        <el-form label-position="right" label-width="3.75rem" size="small">
          <el-form-item :label="t('settings.skillsDescription')">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="2"
              :disabled="editSkill.locked"
            />
          </el-form-item>
          <el-form-item :label="t('settings.skillsBody')">
            <el-input
              v-model="editForm.body"
              type="textarea"
              :rows="12"
              :disabled="editSkill.locked"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showEdit = false">{{ t('common.cancel') }}</el-button>
        <el-button
          type="primary"
          :disabled="editSkill?.locked || !editForm.description.trim() || !editForm.body.trim()"
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
import { Plus, Lock, LockOpen, Settings2, Search, BookOpen, FolderOpen } from '@lucide/vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { useSkillStore } from '../stores/skillStore'
import SkillCreateDialog from './SkillCreateDialog.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import type { SkillMeta } from '../types/skill'

const { t } = useI18n()
const store = useSkillStore()

const showCreate = ref(false)
const searchQuery = ref('')

const showEdit = ref(false)
const editSkill = ref<SkillMeta | null>(null)
const editForm = ref({ description: '', body: '' })

const filteredSkills = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return store.skills
  return store.skills.filter(s => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q))
})

async function openEdit(skill: SkillMeta) {
  editSkill.value = skill
  editForm.value = { description: skill.description, body: '' }
  showEdit.value = true
  try {
    editForm.value.body = await store.getBody(skill.name)
  } catch (e) {
    editForm.value.body = ''
  }
}

async function onSaveEdit() {
  if (!editSkill.value) return
  try {
    await store.save(editSkill.value.name, editForm.value.description.trim(), editForm.value.body.trim())
    showEdit.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || 'Save failed')
  }
}

function handleCmd(cmd: string, skill: SkillMeta) {
  if (cmd === 'delete') onDelete(skill)
  else if (cmd === 'edit') openEdit(skill)
}

const actionMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const actionMenuVisible = ref(false)
function onAction(cmd: string, current?: unknown) {
  actionMenuVisible.value = false
  handleCmd(cmd, current as SkillMeta)
}

function openFolder(skill: SkillMeta) {
  store.openFolder(skill.path)
}

async function onDelete(skill: SkillMeta) {
  if (skill.locked) {
    ElMessage.warning(t('settings.skillsDeleteLocked', { name: skill.name }))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('settings.skillsDeleteConfirm', { name: skill.name }),
      t('settings.skillsDelete')
    )
    await store.remove(skill.name)
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
.skills-manager {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}
.skills-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.skills-empty {
  color: var(--el-text-color-secondary);
  padding: 2rem 0;
  text-align: center;
}
.skill-card {
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
.skill-card:hover {
  border-color: var(--el-color-primary);
}
.skill-card-icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}
.skill-card-info {
  flex: 1;
  min-width: 0;
}
.skill-card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.skill-card-name {
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--el-text-color-primary);
}
.skill-card-desc {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-top: 0.125rem;
}
.skill-card-actions {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex-shrink: 0;
}
.skill-card-path {
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
.skill-card-path:hover {
  color: var(--el-color-primary);
}
.skill-card-path-icon {
  flex-shrink: 0;
}
.skill-card-path-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  direction: rtl;
  text-align: left;
}
</style>