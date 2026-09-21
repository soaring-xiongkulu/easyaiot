<template>
  <el-dialog append-to-body v-model="visible" :title="isEdit ? t('theme.editTitle') : t('theme.newTitle')" width="40rem" class="theme-editor-dialog">
    <div class="theme-editor">
      <div class="theme-editor-top">
        <el-input v-model="draft.name" :placeholder="t('theme.namePlaceholder')" class="theme-name-input" />
        <el-radio-group v-model="draft.type">
          <el-radio-button value="dark">{{ t('theme.typeDark') }}</el-radio-button>
          <el-radio-button value="light">{{ t('theme.typeLight') }}</el-radio-button>
        </el-radio-group>
        <button class="btn btn-ghost btn-icon btn-sm" :title="t('theme.importItermcolors')" @click="onImport">
          <Upload :size="'0.875rem'" />
        </button>
        <button class="btn btn-ghost btn-icon btn-sm" :title="t('theme.exportItermcolors')" @click="onExport">
          <Download :size="'0.875rem'" />
        </button>
      </div>

      <div class="theme-preview" :style="previewStyle">
        <div class="theme-preview-line">
          <span :style="{ color: draft.colors.green }">user@host</span><span :style="{ color: draft.colors.foreground }">:</span><span :style="{ color: draft.colors.blue }">~/terminal</span><span :style="{ color: draft.colors.foreground }">$ ls -la</span>
        </div>
        <div class="theme-preview-line">
          <span :style="{ color: draft.colors.brightBlack }">total 32</span>
        </div>
        <div class="theme-preview-line">
          <span :style="{ color: draft.colors.blue }">drwxr-xr-x</span>
          <span :style="{ color: draft.colors.foreground }"> 5 user staff  160 Jul  3 12:00 </span>
          <span :style="{ color: draft.colors.cyan }">.</span>
        </div>
        <div class="theme-preview-line">
          <span :style="{ color: draft.colors.foreground }">-rw-r--r-- 1 user staff  512 Jul  3 12:00 </span>
          <span :style="{ color: draft.colors.yellow }">README.md</span>
        </div>
        <div class="theme-preview-line">
          <span :style="{ color: draft.colors.foreground }">$ </span>
          <span class="theme-preview-cursor" :style="{ background: draft.colors.cursor }"></span>
        </div>
        <div class="theme-preview-swatches">
          <span
            v-for="key in ansiOrder"
            :key="key"
            class="theme-preview-swatch"
            :style="{ background: draft.colors[key] }"
            :title="key"
          />
        </div>
      </div>

      <div class="theme-color-group">
        <div class="theme-color-group-title">{{ t('theme.groupGeneral') }}</div>
        <div class="theme-color-grid">
          <div v-for="key in generalKeys" :key="key" class="theme-color-field">
            <el-color-picker v-model="draft.colors[key]" size="small" />
            <span class="theme-color-label">{{ t('theme.color.' + key) }}</span>
            <el-input v-model="draft.colors[key]" size="small" class="theme-color-hex" />
          </div>
        </div>
      </div>

      <div class="theme-color-group">
        <div class="theme-color-group-title">{{ t('theme.groupNormal') }}</div>
        <div class="theme-color-grid">
          <div v-for="key in normalKeys" :key="key" class="theme-color-field">
            <el-color-picker v-model="draft.colors[key]" size="small" />
            <span class="theme-color-label">{{ t('theme.color.' + key) }}</span>
            <el-input v-model="draft.colors[key]" size="small" class="theme-color-hex" />
          </div>
        </div>
      </div>

      <div class="theme-color-group">
        <div class="theme-color-group-title">{{ t('theme.groupBright') }}</div>
        <div class="theme-color-grid">
          <div v-for="key in brightKeys" :key="key" class="theme-color-field">
            <el-color-picker v-model="draft.colors[key]" size="small" />
            <span class="theme-color-label">{{ t('theme.color.' + key) }}</span>
            <el-input v-model="draft.colors[key]" size="small" class="theme-color-hex" />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="theme-editor-footer">
        <el-button v-if="isEdit" class="theme-editor-delete-btn" @click="onDelete">{{ t('theme.delete') }}</el-button>
        <div class="theme-editor-footer-spacer" />
        <el-button @click="visible = false">{{ t('conn.cancel') }}</el-button>
        <el-button type="primary" @click="onSave">{{ t('conn.save') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { msg } from '../services/message'
import { Upload, Download } from '@lucide/vue'
import { useSettingsStore } from '../stores/settingsStore'
import { useI18n } from '../i18n'
import type { CustomTerminalTheme, TerminalThemeColors } from '../types/settings'
import { parseItermColors, buildItermColors } from '../composables/itermcolorsParser'
import { OpenFileDialogFiltered, SaveFileDialogFiltered, ReadFileBase64, WriteFileBase64 } from '../../bindings/easyaiot/terminal/app'

const props = defineProps<{
  modelValue: boolean
  /** id of an existing custom theme to edit, or a built-in theme id to clone as a starting point for a new one, or undefined for a blank default */
  sourceThemeId?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [id: string]
}>()

const { t } = useI18n()
const settingsStore = useSettingsStore()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const generalKeys: (keyof TerminalThemeColors)[] = ['background', 'foreground', 'cursor', 'selection']
const normalKeys: (keyof TerminalThemeColors)[] = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
const brightKeys: (keyof TerminalThemeColors)[] = ['brightBlack', 'brightRed', 'brightGreen', 'brightYellow', 'brightBlue', 'brightMagenta', 'brightCyan', 'brightWhite']
const ansiOrder = [...normalKeys, ...brightKeys]

const DEFAULT_COLORS: TerminalThemeColors = {
  background: '#14171d',
  foreground: '#e6e8ed',
  cursor: '#22d3ee',
  selection: 'rgba(34, 211, 238, 0.2)',
  black: '#1e1e22',
  red: '#f87171',
  green: '#34d399',
  yellow: '#fbbf24',
  blue: '#60a5fa',
  magenta: '#c084fc',
  cyan: '#22d3ee',
  white: '#b0b0b8',
  brightBlack: '#3f3f46',
  brightRed: '#fca5a5',
  brightGreen: '#6ee7b7',
  brightYellow: '#fde68a',
  brightBlue: '#93c5fd',
  brightMagenta: '#d8b4fe',
  brightCyan: '#67e8f9',
  brightWhite: '#d0d0d8'
}

const isEdit = ref(false)
const editingId = ref('')
const draft = ref<CustomTerminalTheme>({
  id: '',
  name: '',
  type: 'dark',
  colors: { ...DEFAULT_COLORS }
})

const previewStyle = computed(() => ({
  background: draft.value.colors.background,
  color: draft.value.colors.foreground
}))

watch(() => props.modelValue, (open) => {
  if (!open) return
  const existing = settingsStore.settings.customTerminalThemes.find(t => t.id === props.sourceThemeId)
  if (existing) {
    isEdit.value = true
    editingId.value = existing.id
    draft.value = { id: existing.id, name: existing.name, type: existing.type, colors: { ...existing.colors } }
  } else {
    isEdit.value = false
    editingId.value = ''
    draft.value = {
      id: '',
      name: t('theme.newDefaultName'),
      type: 'dark',
      colors: { ...DEFAULT_COLORS }
    }
  }
})

function onSave() {
  const id = isEdit.value ? editingId.value : (crypto.randomUUID?.() || `custom-${Date.now()}`)
  const theme: CustomTerminalTheme = {
    id,
    name: draft.value.name.trim() || t('theme.newDefaultName'),
    type: draft.value.type,
    colors: { ...draft.value.colors }
  }
  if (isEdit.value) {
    settingsStore.updateCustomTheme(id, theme)
  } else {
    settingsStore.addCustomTheme(theme)
  }
  emit('saved', id)
  visible.value = false
}

async function onDelete() {
  try {
    await ElMessageBox.confirm(t('theme.deleteConfirm'), t('theme.deleteTitle'), {
      confirmButtonText: t('sftp.dialog.confirm'),
      cancelButtonText: t('conn.cancel'),
      type: 'warning'
    })
  } catch {
    return
  }
  settingsStore.removeCustomTheme(editingId.value)
  visible.value = false
}

async function onImport() {
  let path: string
  try {
    path = await OpenFileDialogFiltered(t('theme.importItermcolors'), 'iTerm2 Color Preset', '*.itermcolors')
  } catch {
    return
  }
  if (!path) return
  try {
    const b64 = await ReadFileBase64(path)
    const xml = atob(b64)
    draft.value.colors = parseItermColors(xml, draft.value.colors)
    if (!draft.value.name.trim() || draft.value.name === t('theme.newDefaultName')) {
      const base = path.split(/[\\/]/).pop() || ''
      draft.value.name = base.replace(/\.itermcolors$/i, '') || draft.value.name
    }
    msg.success(t('theme.importSuccess'))
  } catch {
    msg.error(t('theme.importFailed'))
  }
}

async function onExport() {
  const defaultName = `${draft.value.name.trim() || t('theme.newDefaultName')}.itermcolors`
  let path: string
  try {
    path = await SaveFileDialogFiltered(t('theme.exportItermcolors'), defaultName, 'iTerm2 Color Preset', '*.itermcolors')
  } catch {
    return
  }
  if (!path) return
  try {
    const xml = buildItermColors(draft.value.colors)
    await WriteFileBase64(path, btoa(xml))
    msg.success(t('theme.exportSuccess'))
  } catch {
    msg.error(t('theme.exportFailed'))
  }
}
</script>

<style scoped>
.theme-editor {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.theme-editor-top {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.theme-name-input {
  flex: 1;
}

.theme-preview {
  border-radius: var(--radius-md);
  padding: 0.75rem 0.875rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px var(--border-subtle);
}

.theme-preview-line {
  white-space: pre;
}

.theme-preview-cursor {
  display: inline-block;
  width: 0.4375rem;
  height: 0.875rem;
  vertical-align: middle;
}

.theme-preview-swatches {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.theme-preview-swatch {
  width: 1rem;
  height: 1rem;
  border-radius: var(--radius-sm);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15);
}

.theme-color-group-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.theme-color-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem 1rem;
}

.theme-color-field {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.theme-color-label {
  flex: 1;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.theme-color-hex {
  width: 6.25rem;
  flex-shrink: 0;
}

.theme-editor-footer {
  display: flex;
  align-items: center;
}

.theme-editor-delete-btn {
  color: var(--error);
}

.theme-editor-footer-spacer {
  flex: 1;
}
</style>
