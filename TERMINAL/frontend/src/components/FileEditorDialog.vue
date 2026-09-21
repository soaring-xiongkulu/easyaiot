<template>
  <el-dialog
    append-to-body
    :model-value="visible"
    :title="editorTitle"
    width="80%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    destroy-on-close
    @update:model-value="(v: boolean) => emit('update:visible', v)"
    @closed="onClosed"
  >
    <div class="editor-toolbar">
      <!-- Clipboard ops: cut/copy/paste through the editor (Wails clipboard). -->
      <button class="toolbar-icon-btn" :title="t('sftp.cut')" @click="editorRef?.cut()">
        <el-icon><Scissors :size="'0.875rem'" /></el-icon>
      </button>
      <button class="toolbar-icon-btn" :title="t('sftp.copy')" @click="editorRef?.copy()">
        <el-icon><Copy :size="'0.875rem'" /></el-icon>
      </button>
      <button class="toolbar-icon-btn" :title="t('sftp.paste')" @click="editorRef?.paste()">
        <el-icon><ClipboardPaste :size="'0.875rem'" /></el-icon>
      </button>
      <span class="toolbar-divider" />
      <!-- Edit ops: undo/redo wired to CodeMirror history. -->
      <button class="toolbar-icon-btn" @click="editorRef?.undo()" :title="t('sftp.edit.undo')">
        <el-icon><Undo2 :size="'0.875rem'" /></el-icon>
      </button>
      <button class="toolbar-icon-btn" @click="editorRef?.redo()" :title="t('sftp.edit.redo')">
        <el-icon><Redo2 :size="'0.875rem'" /></el-icon>
      </button>
      <span class="toolbar-divider" />
      <!-- View: font size. -->
      <button class="toolbar-icon-btn" @click="fontSizeDown" :title="t('sftp.edit.fontSize')">
        <el-icon><ZoomOut :size="'0.875rem'" /></el-icon>
      </button>
      <span class="font-size-label">{{ fontSize }}px</span>
      <button class="toolbar-icon-btn" @click="fontSizeUp" :title="t('sftp.edit.fontSize')">
        <el-icon><ZoomIn :size="'0.875rem'" /></el-icon>
      </button>
      <span class="toolbar-divider" />
      <!-- Search toggle (the editor owns the search bar; Ctrl+F also opens it). -->
      <button
        class="toolbar-icon-btn"
        :class="{ active: searchOpen }"
        :title="t('sftp.edit.search')"
        @click="searchOpen = editorRef?.toggleSearch() ?? false"
      >
        <el-icon><Search :size="'0.875rem'" /></el-icon>
      </button>
      <!-- View: wrap toggle. Language / encoding / line-ending stay in the
           footer's options row. -->
      <button
        class="toolbar-icon-btn"
        :class="{ active: editorWrapEnabled && !wrapDisabled }"
        :disabled="wrapDisabled"
        @click="editorWrapEnabled = !editorWrapEnabled"
        :title="t('sftp.edit.wrap')"
      >
        <el-icon><WrapText :size="'0.875rem'" /></el-icon>
      </button>
    </div>
    <div class="editor-host">
      <SyntaxEditor
        ref="editorRef"
        v-model="editorContent"
        :file-path="editorPath"
        :lang="syntaxLang"
        :wrap="editorWrapEnabled"
        :font-size="fontSize"
        :compact="true"
        @search-open="(v: boolean) => (searchOpen = v)"
      />
    </div>
    <template #footer>
      <div class="editor-footer">
        <div class="editor-opts">
          <el-select v-model="syntaxLang" style="width: 6.875rem" filterable>
            <el-option v-for="l in LANG_OPTIONS" :key="l.value" :label="l.label" :value="l.value" />
          </el-select>
          <button
            ref="encodingBtn"
            class="editor-encoding-btn"
            @click.stop="encodingMenu?.toggle(encodingBtn as HTMLElement)"
          >
            {{ encodingLabel(editorEncoding) }}
            <ChevronDown :size="'0.875rem'" />
          </button>
          <Menu ref="encodingMenu" v-model:visible="encodingMenuVisible">
            <MenuSubmenu :label="t('sftp.edit.reopenWith')">
              <MenuItem
                v-for="e in ENCODINGS"
                :key="e.value"
                :class="{ active: e.value === editorEncoding }"
                @click="onReopenWith(e.value)"
              >{{ e.label }}</MenuItem>
            </MenuSubmenu>
            <MenuDivider />
            <MenuSubmenu :label="t('sftp.edit.saveWith')">
              <MenuItem
                v-for="e in ENCODINGS"
                :key="e.value"
                :class="{ active: e.value === editorEncoding }"
                @click="onSaveWith(e.value)"
              >{{ e.label }}</MenuItem>
            </MenuSubmenu>
          </Menu>
          <el-select v-model="editorLineEnding" style="width: 8.75rem">
            <el-option label="LF (Linux/macOS)" value="lf" />
            <el-option label="CRLF (Windows)" value="crlf" />
            <el-option label="CR (old Mac)" value="cr" />
          </el-select>
        </div>
        <div class="editor-buttons">
          <el-button size="small" @click="onExternal">{{ t('sftp.editExternal') }}</el-button>
          <el-button @click="close">{{ t('sftp.dialog.cancel') }}</el-button>
          <el-button :loading="saving" @click="onSave(false)">{{ t('sftp.edit.save') }}</el-button>
          <el-button type="primary" :loading="saving" @click="onSave(true)">{{ t('sftp.edit.saveClose') }}</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { useLocalStateStore } from '../stores/localStateStore'
import { utf8ToBase64 } from '../utils/base64'
import {
  SftpGetContent, SftpLocalGetContent, SftpPutContent, SftpLocalPutContent,
  SftpOpenExternalEditor, OpenExternalEditorLocal,
} from '../../bindings/easyaiot/terminal/app'
import SyntaxEditor from './SyntaxEditor.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuSubmenu from './MenuSubmenu.vue'
import MenuDivider from './MenuDivider.vue'
import { Undo2, Redo2, ZoomOut, ZoomIn, WrapText, Search, Scissors, Copy, ClipboardPaste, ChevronDown } from '@lucide/vue'

const { t } = useI18n()
const localStateStore = useLocalStateStore()

const props = defineProps<{
  visible?: boolean
  sessionId?: string
  mode?: 'remote' | 'local'
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'saved'): void
}>()

const editorRef = ref<{ focus: () => void; undo: () => void; redo: () => void; toggleSearch: () => boolean; cut: () => Promise<boolean>; copy: () => Promise<boolean>; paste: () => Promise<boolean> } | null>(null)
// Mirrors the editor's search-bar visibility (kept in sync via the
// search-open event, so Ctrl+F inside the editor updates the button too).
const searchOpen = ref(false)
const editorTitle = ref('')
const editorPath = ref('')
const editorContent = ref('')
const editorRawBytes = ref<Uint8Array | null>(null)
const editorEncoding = ref<Encoding>('utf-8')
const editorLineEnding = ref<LineEnding>('lf')
// Encoding menu (button trigger in the footer + two-level action menu).
const encodingMenu = ref<InstanceType<typeof Menu> | null>(null)
const encodingBtn = ref<HTMLElement | null>(null)
const encodingMenuVisible = ref(false)
const editorWrapEnabled = ref(true)
const saving = ref(false)

const wrapDisabled = computed(() => /\.(?:pem|key|crt|p7b)$/i.test(editorPath.value))

// Editor font size, 10–24px. Session-scoped: applies via the host element's
// font-size (SyntaxEditor inherits it), so changes never rebuild the editor.
const fontSize = ref(13)
const FONT_MIN = 10
const FONT_MAX = 24
function fontSizeDown() { fontSize.value = Math.max(FONT_MIN, fontSize.value - 1) }
function fontSizeUp() { fontSize.value = Math.min(FONT_MAX, fontSize.value + 1) }

// Syntax-highlighting language override. Defaults to the language the current
// file's extension maps to (Plain Text when nothing matches), and the rest are
// sorted alphabetically so the dropdown stays scannable.
const syntaxLang = ref('text')

// Map a file path to the language id its extension would highlight as, so the
// dropdown reflects the active mode. Mirrors SyntaxEditor's extension picks.
function langFromPath(path: string): string {
  const base = path.replace(/\\/g, '/').split('/').pop() || ''
  const lower = base.toLowerCase()
  if (lower === 'dockerfile' || lower.startsWith('dockerfile.')) return 'dockerfile'
  if (lower === 'makefile' || lower === 'gnumakefile') return 'conf'
  if (lower === '.bashrc' || lower === '.zshrc' || lower === '.profile' || lower === '.bash_profile') return 'sh'
  if (lower === '.gitignore' || lower === '.dockerignore' || lower === '.env' || lower.endsWith('.env')) return 'conf'
  if (lower === 'nginx.conf' || lower.endsWith('.nginx')) return 'nginx'
  const i = lower.lastIndexOf('.')
  const ext = i >= 0 ? lower.slice(i + 1) : ''
  const map: Record<string, string> = {
    json: 'json', jsonc: 'json', js: 'js', mjs: 'js', cjs: 'js', jsx: 'js', ts: 'ts', tsx: 'ts',
    html: 'html', htm: 'html', vue: 'html', css: 'css', scss: 'css', less: 'css',
    xml: 'xml', svg: 'xml', md: 'md', markdown: 'md', py: 'py', sql: 'sql',
    yml: 'yaml', yaml: 'yaml', sh: 'sh', bash: 'sh', zsh: 'sh', ksh: 'sh', fish: 'sh',
    conf: 'conf', cfg: 'conf', ini: 'conf', properties: 'conf', toml: 'toml',
    c: 'c', h: 'c', cpp: 'cpp', cc: 'cpp', cxx: 'cpp', hpp: 'cpp', cs: 'csharp',
    dart: 'dart', java: 'java', kt: 'kotlin', scala: 'scala',
    go: 'go', rs: 'rust', rb: 'ruby',
  }
  return map[ext] || 'text'
}
const LANG_OPTIONS = [
  { value: 'c', label: 'C' },
  { value: 'cpp', label: 'C++' },
  { value: 'csharp', label: 'C#' },
  { value: 'css', label: 'CSS' },
  { value: 'dart', label: 'Dart' },
  { value: 'dockerfile', label: 'Dockerfile' },
  { value: 'go', label: 'Go' },
  { value: 'html', label: 'HTML' },
  { value: 'java', label: 'Java' },
  { value: 'js', label: 'JavaScript' },
  { value: 'json', label: 'JSON' },
  { value: 'kotlin', label: 'Kotlin' },
  { value: 'md', label: 'Markdown' },
  { value: 'nginx', label: 'Nginx' },
  { value: 'text', label: 'Plain Text' },
  { value: 'conf', label: 'Properties/INI' },
  { value: 'py', label: 'Python' },
  { value: 'ruby', label: 'Ruby' },
  { value: 'rust', label: 'Rust' },
  { value: 'scala', label: 'Scala' },
  { value: 'sh', label: 'Shell' },
  { value: 'sql', label: 'SQL' },
  { value: 'toml', label: 'TOML' },
  { value: 'ts', label: 'TypeScript' },
  { value: 'xml', label: 'XML' },
  { value: 'yaml', label: 'YAML' },
].sort((a, b) => a.label.localeCompare(b.label))

type Encoding = 'utf-8' | 'utf-16le' | 'utf-16be' | 'gbk'
type LineEnding = 'lf' | 'crlf' | 'cr'

const ENCODINGS: { value: Encoding, label: string }[] = [
  { value: 'utf-8', label: 'UTF-8' },
  { value: 'utf-16le', label: 'UTF-16 LE' },
  { value: 'utf-16be', label: 'UTF-16 BE' },
  { value: 'gbk', label: 'GBK' },
]
function encodingLabel(enc: Encoding): string {
  return ENCODINGS.find(e => e.value === enc)?.label || enc
}

function fromBase64(b64: string): Uint8Array {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes
}

function detectEncoding(bytes: Uint8Array): { encoding: Encoding, hasBom: boolean } {
  if (bytes.length >= 2) {
    if (bytes[0] === 0xFF && bytes[1] === 0xFE) return { encoding: 'utf-16le', hasBom: true }
    if (bytes[0] === 0xFE && bytes[1] === 0xFF) return { encoding: 'utf-16be', hasBom: true }
  }
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
    return { encoding: 'utf-8', hasBom: true }
  }
  let nullCount = 0
  const checkLen = Math.min(bytes.length, 1024)
  for (let i = 0; i < checkLen; i++) { if (bytes[i] === 0) nullCount++ }
  if (nullCount > checkLen * 0.3) return { encoding: 'utf-16le', hasBom: false }
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(bytes)
    return { encoding: 'utf-8', hasBom: false }
  } catch {
    return { encoding: 'gbk', hasBom: false }
  }
}

function detectLineEnding(text: string): LineEnding {
  let crlf = 0, lf = 0, cr = 0
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '\r' && text[i + 1] === '\n') { crlf++; i++ }
    else if (text[i] === '\n') lf++
    else if (text[i] === '\r') cr++
  }
  if (crlf > lf && crlf > cr) return 'crlf'
  if (cr > lf && cr > crlf) return 'cr'
  return 'lf'
}

function decodeContent(bytes: Uint8Array, enc: Encoding): string {
  if (enc === 'gbk') {
    try { return new TextDecoder('gbk').decode(bytes) }
    catch { return new TextDecoder('utf-8').decode(bytes) }
  }
  return new TextDecoder(enc === 'utf-16le' ? 'utf-16le' : enc === 'utf-16be' ? 'utf-16be' : 'utf-8').decode(bytes)
}

function encodeContent(text: string, enc: Encoding, lineEnding: LineEnding): string {
  let normalized = text
  if (lineEnding === 'crlf') normalized = text.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n')
  else if (lineEnding === 'cr') normalized = text.replace(/\r\n/g, '\n').replace(/\n/g, '\r')
  else normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

  if (enc === 'utf-8' || enc === 'gbk') {
    // Always encode as UTF-8; the backend re-encodes to GBK when needed.
    return utf8ToBase64(normalized)
  }
  const buf = new Uint8Array(normalized.length * 2 + 2)
  let pos = 0
  buf[pos++] = enc === 'utf-16le' ? 0xFF : 0xFE
  buf[pos++] = enc === 'utf-16le' ? 0xFE : 0xFF
  for (let i = 0; i < normalized.length; i++) {
    const code = normalized.charCodeAt(i)
    buf[pos++] = enc === 'utf-16le' ? (code & 0xFF) : ((code >> 8) & 0xFF)
    buf[pos++] = enc === 'utf-16le' ? ((code >> 8) & 0xFF) : (code & 0xFF)
  }
  let binary = ''
  for (let i = 0; i < pos; i++) binary += String.fromCharCode(buf[i])
  return btoa(binary)
}

function isBinaryContent(bytes: Uint8Array): boolean {
  const sample = bytes.slice(0, 8192)
  if (!sample.length) return false
  let nonPrintable = 0
  for (let i = 0; i < sample.length; i++) {
    const c = sample[i]
    if (c < 0x09 || (c > 0x0D && c < 0x20)) nonPrintable++
  }
  return nonPrintable > sample.length * 0.3
}

// The active local/remote mode for the file being edited. Passed per open() rather
// than read from the `mode` prop, which updates reactively AFTER the parent calls
// open() — reading props.mode here would race and use the previous pane's mode.
const activeMode = ref<'remote' | 'local'>(props.mode || 'remote')

const isLocal = computed(() => activeMode.value === 'local')

async function open(path: string, title: string, mode?: 'remote' | 'local') {
  activeMode.value = mode ?? props.mode ?? 'remote'
  editorPath.value = path
  editorTitle.value = title
  editorContent.value = ''
  editorRawBytes.value = null
  lastDecoded.value = ''
  syntaxLang.value = langFromPath(path)
  editorVisibleInternal = true
  emit('update:visible', true)
  const sid = props.sessionId
  if (!sid) return
  try {
    const rawB64 = isLocal.value
      ? await SftpLocalGetContent(sid, path)
      : await SftpGetContent(sid, path)
    const bytes = fromBase64(rawB64)
    if (isBinaryContent(bytes)) {
      close()
      msg.warning(t('sftp.edit.binaryFile'))
      return
    }
    const detected = detectEncoding(bytes)
    editorEncoding.value = detected.encoding
    editorRawBytes.value = bytes
    const text = decodeContent(bytes, detected.encoding)
    editorLineEnding.value = detectLineEnding(text)
    editorContent.value = text
    lastDecoded.value = text
    await nextTick()
    editorRef.value?.focus()
  } catch (e: any) {
    close()
    msg.error(e?.toString?.() || 'Failed to read file')
  }
}

let editorVisibleInternal = false

watch(() => props.visible, (v) => { editorVisibleInternal = v })

// Text the buffer currently mirrors (set on open and on reopen). Content
// differing from it means unsaved user edits; the encoding menu's reopen path
// discards them (with confirmation), the save-with path never touches content.
const lastDecoded = ref('')

// Re-decode the on-disk bytes with the chosen encoding (fix wrong detection /
// mojibake). Discards unsaved edits, so confirm first when the buffer is dirty.
async function onReopenWith(enc: Encoding) {
  encodingMenuVisible.value = false
  const bytes = editorRawBytes.value
  if (!bytes) return
  if (editorContent.value !== lastDecoded.value) {
    try {
      await ElMessageBox.confirm(t('sftp.edit.reopenConfirm'), t('sftp.edit.reopenWith'))
    } catch {
      return // cancelled
    }
  }
  const text = decodeContent(bytes, enc)
  editorEncoding.value = enc
  editorLineEnding.value = detectLineEnding(text)
  editorContent.value = text
  lastDecoded.value = text
}

// Change only the encoding the file will be saved with; the buffer stays as-is.
function onSaveWith(enc: Encoding) {
  encodingMenuVisible.value = false
  editorEncoding.value = enc
}

// Switch to the configured external editor: close this dialog and open the same
// file there (remote → download/auto-upload flow, local → open in place).
async function onExternal() {
  const path = editorPath.value
  if (!path) return
  const cmd = localStateStore.state.externalEditor?.trim()
  if (!cmd) {
    msg.warning(t('sftp.editExternalNotConfigured'))
    return
  }
  close()
  try {
    if (isLocal.value) {
      await OpenExternalEditorLocal(path, cmd)
    } else {
      if (!props.sessionId) return
      await SftpOpenExternalEditor(props.sessionId, path, cmd)
    }
    msg.info(t('sftp.editExternalStart', { path }))
  } catch (e: any) {
    msg.error(e?.toString?.() || 'Failed to open external editor')
  }
}

async function onSave(closeAfter: boolean) {
  const sid = props.sessionId
  if (!sid || !editorPath.value) return
  saving.value = true
  try {
    const contentBase64 = encodeContent(editorContent.value, editorEncoding.value, editorLineEnding.value)
    if (isLocal.value) {
      await SftpLocalPutContent(sid, editorPath.value, contentBase64, editorEncoding.value)
    } else {
      await SftpPutContent(sid, editorPath.value, contentBase64, editorEncoding.value)
    }
    emit('saved')
    if (closeAfter) close()
  } catch (e: any) {
    msg.error(e?.toString?.() || 'Failed to save file')
  } finally {
    saving.value = false
  }
}

function close() {
  if (!editorVisibleInternal && !props.visible) return
  emit('update:visible', false)
}

function onClosed() {
  editorPath.value = ''
  editorContent.value = ''
  editorRawBytes.value = null
  lastDecoded.value = ''
  editorVisibleInternal = false
}

defineExpose({ open })
</script>

<style scoped>
/* Slim toolbar above the editor, same icon-button style as the SFTP
   flat toolbar (FileList.vue .filter-icon-btn): transparent, muted,
   hover-bright, with hairline dividers between groups. */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  padding: 0 0.625rem 0.375rem;
}
.toolbar-divider {
  width: 1px;
  height: 1rem;
  margin: 0 0.1875rem;
  flex-shrink: 0;
  background: var(--border-subtle);
}
.toolbar-icon-btn {
  width: 1.625rem;
  height: 1.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.12s ease;
}
.toolbar-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.toolbar-icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
  background: transparent;
  color: var(--text-muted);
}
.toolbar-icon-btn.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
.font-size-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  min-width: 2.25rem;
  text-align: center;
  flex-shrink: 0;
}
.editor-host {
  height: 60vh;
  border: 1px solid var(--border-subtle);
  border-radius: 0.25rem;
  overflow: hidden;
  background: #282c34;
}
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
}
.editor-buttons {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
/* el-button adds a default 0.75rem left margin between siblings; drop it so the
   buttons sit at the flex gap instead of 0.5rem+0.75rem. */
.editor-buttons .el-button + .el-button {
  margin-left: 0;
}
.editor-opts {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
/* Encoding menu trigger, styled to sit next to the el-selects like a select. */
.editor-encoding-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  height: 2rem;
  padding: 0 0.625rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.12s ease;
}
.editor-encoding-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
</style>