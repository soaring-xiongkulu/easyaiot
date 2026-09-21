<template>
  <el-dialog
    :model-value="true"
    :title="t('settings.skillsCreateTitle')"
    width="33.75rem"
    @close="$emit('close')"
  >
    <div class="skill-create-body">
      <div
        class="upload-zone"
        :class="{ parsed: parseState === 'ok', failed: parseState === 'fail' }"
        @dragover.prevent
        @drop.prevent="onDrop"
        @click="fileInput?.click()"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".md,.zip,.skill"
          style="display:none"
          @change="onFileChange"
        />
        <template v-if="!uploadFile">
          <FileUp :size="'1.5rem'" class="upload-icon" />
          <p class="upload-hint">{{ t('settings.skillsUploadHint') }}</p>
        </template>
        <template v-else>
          <FileUp :size="'1.5rem'" class="upload-icon" />
          <p class="upload-file-name">{{ uploadFile }}</p>
          <p v-if="parseState === 'ok'" class="parse-ok">
            <CircleCheck :size="'0.875rem'" /> {{ t('settings.skillsParseOk') }}
          </p>
          <p v-else-if="parseState === 'fail'" class="parse-fail">
            {{ parseError }}
          </p>
        </template>
      </div>

      <div class="import-actions">
        <el-button size="small" @click="importZip">{{ t('settings.skillsImportZip') }}</el-button>
        <el-button size="small" @click="importDir">{{ t('settings.skillsImportDir') }}</el-button>
        <span class="import-hint">{{ t('settings.skillsImportFolderHint') }}</span>
      </div>

      <el-form label-position="right" label-width="4.5rem" size="small">
        <el-form-item required :label="t('settings.skillsName')">
          <el-input
            v-model="form.name"
            :placeholder="t('settings.skillsNamePlaceholder')"
          />
        </el-form-item>
        <el-form-item required :label="t('settings.skillsDescription')">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            :placeholder="t('settings.skillsDescriptionPlaceholder')"
          />
        </el-form-item>
        <el-form-item required :label="t('settings.skillsBody')">
          <el-input
            v-model="form.body"
            type="textarea"
            :rows="8"
            :placeholder="t('settings.skillsBodyPlaceholder')"
          />
        </el-form-item>
      </el-form>

      <p class="security-tip">{{ t('settings.skillsSecurityTip') }}</p>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :disabled="!canCreate" @click="onCreate">
        {{ t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { FileUp, CircleCheck } from '@lucide/vue'
import { useI18n } from '../i18n'
import { useSkillStore } from '../stores/skillStore'
import { OpenFileDialogFiltered, OpenDirectoryDialog, ImportSkillFromZip, ImportSkillFromDir } from '../../bindings/easyaiot/terminal/app'

const { t } = useI18n()
const store = useSkillStore()

const SKILL_TEMPLATE = `## Purpose
Investigate high disk usage on a Linux host and identify the largest space consumers.

## Steps
1. Show overall disk usage per mount point:
   \`df -hT\`
2. Find the top-level directories consuming the most space (start from the full mount):
   \`du -xh --max-depth=1 / 2>/dev/null | sort -rh | head -n 20\`
3. Drill down into the largest directory reported above, repeating step 2 until the culprit is found.
4. List the largest individual files:
   \`find <suspect_dir> -xdev -type f -printf '%s\\t%p\\n' 2>/dev/null | sort -rn | head -n 20\`
5. Check for deleted-but-open files still holding space:
   \`lsof +L1 2>/dev/null | awk '$5=="REG"' | sort -k7 -rn | head\`

## Notes
- Always use \`-x\`/\`-xdev\` to stay on one filesystem and avoid crossing into /proc, /sys, or network mounts.
- Do NOT delete anything automatically. Report findings first and let the user confirm.
- If a mount is at 100%, note it explicitly and prioritize freeing it.
`

const emit = defineEmits<{
  close: []
  created: []
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const uploadFile = ref('')
const parseState = ref<'idle' | 'ok' | 'fail'>('idle')
const parseError = ref('')
const form = ref({ name: '', description: '', body: SKILL_TEMPLATE })

const canCreate = computed(() => {
  return form.value.name.trim() && form.value.description.trim() && form.value.body.trim()
})

function onDrop(e: DragEvent) {
  const files = e.dataTransfer?.files
  if (files && files.length > 0) handleFile(files[0])
}

function onFileChange() {
  const files = fileInput.value?.files
  if (files && files.length > 0) handleFile(files[0])
}

// 解析 SKILL.md：frontmatter(name/description) + 正文，自动填充表单
function parseSkillMd(content: string): { name: string; description: string; body: string } | null {
  const trimmed = content.replace(/^﻿/, '').trimStart()
  if (!trimmed.startsWith('---')) return null
  const rest = trimmed.slice(3).replace(/^\r?\n/, '')
  const endIdx = rest.search(/\n---/)
  if (endIdx < 0) return null
  const fmBlock = rest.slice(0, endIdx)
  const body = rest.slice(endIdx + 4).replace(/^[-\s]*\r?\n/, '').trim()

  let name = ''
  let description = ''
  let curKey = ''
  for (const raw of fmBlock.split('\n')) {
    const line = raw.replace(/\r$/, '')
    if (!line.trim()) continue
    // 折叠标量续行（description: > 的多行）
    if (/^[\t ]/.test(line) && curKey === 'description') {
      description += (description ? ' ' : '') + line.trim()
      continue
    }
    const m = line.match(/^([\w-]+):\s*(.*)$/)
    if (!m) continue
    curKey = m[1]
    const val = m[2].replace(/^["']|["']$/g, '')
    if (curKey === 'name') name = val
    else if (curKey === 'description' && !['>', '|', '>-', '|-'].includes(val)) description = val
  }
  if (!name && !description) return null
  return { name, description, body }
}

async function handleFile(file: File) {
  uploadFile.value = file.name
  parseState.value = 'idle'
  parseError.value = ''

  const lower = file.name.toLowerCase()
  if (lower.endsWith('.md')) {
    try {
      const content = await file.text()
      const parsed = parseSkillMd(content)
      if (parsed) {
        form.value.name = parsed.name
        form.value.description = parsed.description
        form.value.body = parsed.body
        parseState.value = 'ok'
      } else {
        // 无 frontmatter：整个内容作为正文，文件名作为 name 候选
        form.value.body = content.trim()
        if (!form.value.name) {
          form.value.name = file.name.replace(/\.md$/i, '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '')
        }
        parseState.value = 'ok'
      }
    } catch (e: any) {
      parseState.value = 'fail'
      parseError.value = e?.message || t('settings.skillsParseFail')
    }
  } else if (lower.endsWith('.zip') || lower.endsWith('.skill')) {
    // 拖入的 zip 拿不到磁盘路径，引导用下方「导入 Zip」按钮走原生对话框
    parseState.value = 'fail'
    parseError.value = t('settings.skillsZipHint')
  } else {
    parseState.value = 'fail'
    parseError.value = t('settings.skillsParseFail')
  }
}

async function onCreate() {
  if (!canCreate.value) return
  try {
    await store.create(
      form.value.name.trim(),
      form.value.description.trim(),
      form.value.body.trim()
    )
    emit('created')
  } catch (e: any) {
    ElMessage.error(e?.message || 'Creation failed')
  }
}

// 通过 Wails 原生对话框选 zip / 文件夹，走后端导入（支持文件夹型 skill）
async function importZip() {
  try {
    const path = await OpenFileDialogFiltered(t('settings.skillsImportZip'), 'Skill', '*.zip;*.skill')
    if (!path) return
    const name = await ImportSkillFromZip(path)
    await store.reload()
    ElMessage.success(t('settings.skillsImportOk', { name }))
    emit('created')
  } catch (e: any) {
    ElMessage.error(e?.message || 'Import failed')
  }
}

async function importDir() {
  try {
    const path = await OpenDirectoryDialog()
    if (!path) return
    const name = await ImportSkillFromDir(path)
    await store.reload()
    ElMessage.success(t('settings.skillsImportOk', { name }))
    emit('created')
  } catch (e: any) {
    ElMessage.error(e?.message || 'Import failed')
  }
}
</script>

<style scoped>
.skill-create-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  border: 1px dashed var(--el-border-color);
  border-radius: 0.5rem;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s;
}
.import-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.import-hint {
  font-size: 0.6875rem;
  color: var(--el-text-color-secondary);
}
.upload-zone:hover {
  border-color: var(--el-color-primary);
}
.upload-zone.parsed {
  border-color: var(--el-color-success);
}
.upload-zone.failed {
  border-color: var(--el-color-danger);
}
.upload-icon {
  color: var(--el-text-color-secondary);
}
.upload-hint {
  color: var(--el-text-color-secondary);
  font-size: 0.8125rem;
  margin: 0;
}
.upload-file-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}
.parse-ok {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--el-color-success);
  margin: 0;
}
.parse-fail {
  font-size: 0.75rem;
  color: var(--el-color-danger);
  margin: 0;
}
.security-tip {
  font-size: 0.75rem;
  color: var(--el-color-warning);
  margin: 0;
}
</style>