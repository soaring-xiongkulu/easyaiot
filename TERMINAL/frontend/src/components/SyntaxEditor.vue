<template>
  <div
    ref="hostRef"
    class="syntax-editor"
    :class="{ compact, 'theme-dark': isDark }"
    :style="props.fontSize ? { fontSize: props.fontSize + 'px' } : undefined"
  >
    <!-- Custom search/replace bar: the built-in CodeMirror panel's look
         doesn't match the app, so search state/highlighting is managed here
         and the cursor work goes through RegExpCursor. -->
    <div v-if="searchOpen" class="search-bar">
      <div class="search-row">
        <button class="search-icon-btn" :class="{ active: caseSensitive }" :title="t('sftp.edit.matchCase')" @click="caseSensitive = !caseSensitive">
          <el-icon><CaseSensitive :size="'0.875rem'" /></el-icon>
        </button>
        <button class="search-icon-btn" :class="{ active: regexpMode }" :title="t('sftp.edit.regexp')" @click="regexpMode = !regexpMode">
          <el-icon><Regex :size="'0.875rem'" /></el-icon>
        </button>
        <button class="search-icon-btn" :class="{ active: wholeWord }" :title="t('sftp.edit.wholeWord')" @click="wholeWord = !wholeWord">
          <el-icon><WholeWord :size="'0.875rem'" /></el-icon>
        </button>
        <el-input
          ref="searchInputRef"
          v-model="searchText"
          class="search-input"
          size="small"
          :placeholder="t('sftp.edit.search')"
          @keydown.enter.prevent="($event.shiftKey ? findPrev() : findNext())"
          @keydown.esc.stop.prevent="closeSearch"
        >
          <template #suffix>
            <span v-if="searchText" class="match-count" :class="{ none: matchCount === 0 || invalidPattern }">
              {{ invalidPattern ? '0/0' : `${currentMatch}/${matchCount}` }}
            </span>
          </template>
        </el-input>
        <button class="search-icon-btn" :disabled="!matchCount" :title="t('sftp.edit.search')" @click="findPrev">
          <el-icon><ChevronUp :size="'0.875rem'" /></el-icon>
        </button>
        <button class="search-icon-btn" :disabled="!matchCount" :title="t('sftp.edit.search')" @click="findNext">
          <el-icon><ChevronDown :size="'0.875rem'" /></el-icon>
        </button>
        <button
          class="search-icon-btn"
          :class="{ active: replaceRowOpen }"
          :title="t('sftp.edit.replace')"
          @click="replaceRowOpen = !replaceRowOpen; nextTick(() => (replaceRowOpen ? replaceInputRef?.focus() : searchInputRef?.focus()))"
        >
          <el-icon><ChevronsDownUp :size="'0.875rem'" /></el-icon>
        </button>
        <button class="search-icon-btn" title="Esc" @click="closeSearch">
          <el-icon><X :size="'0.875rem'" /></el-icon>
        </button>
      </div>
      <div v-if="replaceRowOpen" class="search-row">
        <span class="replace-spacer" />
        <el-input
          ref="replaceInputRef"
          v-model="replaceText"
          class="search-input"
          size="small"
          :placeholder="t('sftp.edit.replace')"
          @keydown.enter.prevent="replaceCurrent"
          @keydown.esc.stop.prevent="closeSearch"
        />
        <button class="search-icon-btn" :disabled="!matchCount" :title="t('sftp.edit.replace')" @click="replaceCurrent">
          <el-icon><Replace :size="'0.875rem'" /></el-icon>
        </button>
        <button class="search-icon-btn" :disabled="!matchCount" :title="t('sftp.edit.replaceAll')" @click="replaceAllMatches">
          <el-icon><ReplaceAll :size="'0.875rem'" /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { EditorState, StateEffect, StateField } from '@codemirror/state'
import type { Text } from '@codemirror/state'
import { Decoration, DecorationSet } from '@codemirror/view'
import { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection } from '@codemirror/view'
import { defaultKeymap, history, historyKeymap, indentWithTab, undo, redo } from '@codemirror/commands'
import { RegExpCursor } from '@codemirror/search'
import { Clipboard } from '@wailsio/runtime'
import { writeClipboard } from '../composables/useClipboardWrite'
import { useI18n } from '../i18n'
import { CaseSensitive, ChevronDown, ChevronUp, ChevronsDownUp, Regex, Replace, ReplaceAll, WholeWord, X } from '@lucide/vue'
import { syntaxHighlighting, defaultHighlightStyle, bracketMatching, foldGutter, foldKeymap, StreamLanguage } from '@codemirror/language'
import { oneDark } from '@codemirror/theme-one-dark'
import { json } from '@codemirror/lang-json'
import { javascript } from '@codemirror/lang-javascript'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { xml } from '@codemirror/lang-xml'
import { markdown } from '@codemirror/lang-markdown'
import { python } from '@codemirror/lang-python'
import { sql } from '@codemirror/lang-sql'
import { yaml } from '@codemirror/lang-yaml'
import { shell } from '@codemirror/legacy-modes/mode/shell'
import { properties } from '@codemirror/legacy-modes/mode/properties'
import { toml } from '@codemirror/legacy-modes/mode/toml'
import { dockerFile } from '@codemirror/legacy-modes/mode/dockerfile'
import { nginx } from '@codemirror/legacy-modes/mode/nginx'
import { clike } from '@codemirror/legacy-modes/mode/clike'
import { ruby } from '@codemirror/legacy-modes/mode/ruby'
// Official Lezer grammars for the languages that have them — these bring
// syntax-aware folding (the legacy stream modes provide no foldable ranges).
import { go } from '@codemirror/lang-go'
import { cpp } from '@codemirror/lang-cpp'
import { java } from '@codemirror/lang-java'
import { rust } from '@codemirror/lang-rust'
import { useSettingsStore } from '../stores/settingsStore'

const props = defineProps<{
  modelValue: string
  filePath?: string
  compact?: boolean
  lang?: string
  wrap?: boolean
  readonly?: boolean
  fontSize?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  execute: []
  'search-open': [open: boolean]
}>()

const hostRef = ref<HTMLElement | null>(null)
let view: EditorView | null = null
let applyingExternal = false
let resizeObserver: ResizeObserver | null = null

// Follow the app theme (dark/deep-blue → dark, light/system → resolved).
const settingsStore = useSettingsStore()
const isDark = computed(() => settingsStore.resolvedAppTheme === 'dark')

const { t } = useI18n()

// ---------------------------------------------------------------------------
// Search/replace. State lives here (Vue refs) so the bar can be styled with
// the app's UI kit; matches are scanned with RegExpCursor and highlighted via
// a StateField that rebuilds on query effects and document changes.
// ---------------------------------------------------------------------------
interface SearchSpec {
  text: string
  regexp: boolean
  caseSensitive: boolean
  wholeWord: boolean
}

const searchOpen = ref(false)
const replaceRowOpen = ref(false)
const searchText = ref('')
const replaceText = ref('')
const caseSensitive = ref(false)
const regexpMode = ref(false)
const wholeWord = ref(false)
const searchInputRef = ref<{ focus: () => void } | null>(null)
const replaceInputRef = ref<{ focus: () => void } | null>(null)
const matchCount = ref(0)
const currentMatch = ref(0)
const invalidPattern = ref(false)

const MAX_MATCHES = 20000
let searchRanges: { from: number, to: number }[] = []
let currentIdx = -1
let currentSpec: SearchSpec | null = null

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Single source of truth for the match pattern (used by both the scanner and
// the replacer so highlighting and replacement can never disagree).
function buildSource(spec: SearchSpec): string {
  let src = spec.regexp ? spec.text : escapeRegExp(spec.text)
  if (spec.wholeWord) src = `\\b(?:${src})\\b`
  return src
}

function buildSpec(): SearchSpec | null {
  if (!searchText.value) return null
  return {
    text: searchText.value,
    regexp: regexpMode.value,
    caseSensitive: caseSensitive.value,
    wholeWord: wholeWord.value,
  }
}

function scanMatches(spec: SearchSpec, doc: Text): { ranges: { from: number, to: number }[], invalid: boolean } {
  const ranges: { from: number, to: number }[] = []
  try {
    const cursor = new RegExpCursor(doc, buildSource(spec), { ignoreCase: !spec.caseSensitive }, 0, doc.length)
    while (!cursor.next().done) {
      ranges.push({ ...cursor.value })
      if (ranges.length >= MAX_MATCHES) break
    }
  } catch {
    return { ranges: [], invalid: true }
  }
  return { ranges, invalid: false }
}

// Index of the match that should be "current" given the cursor position: the
// first one ending after head, wrapping to the first match.
function idxFromPos(head: number): number {
  if (!searchRanges.length) return -1
  const idx = searchRanges.findIndex(r => r.to > head)
  return idx >= 0 ? idx : 0
}

const setSearchEffect = StateEffect.define<SearchSpec | null>()

const searchDecoField = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(deco, tr) {
    const effect = tr.effects.find(e => e.is(setSearchEffect))
    if (effect) currentSpec = effect.value
    const spec = effect ? effect.value : currentSpec
    if (!spec) {
      if (searchRanges.length || matchCount.value || currentMatch.value) {
        searchRanges = []
        currentIdx = -1
        matchCount.value = 0
        currentMatch.value = 0
        invalidPattern.value = false
      }
      return Decoration.none
    }
    if (!effect && !tr.docChanged) return deco
    const res = scanMatches(spec, tr.state.doc)
    searchRanges = res.ranges
    invalidPattern.value = res.invalid
    matchCount.value = res.ranges.length
    currentIdx = idxFromPos(tr.state.selection.main.head)
    currentMatch.value = currentIdx + 1
    if (!searchRanges.length) return Decoration.none
    const marks = searchRanges.map((r, i) =>
      Decoration.mark({
        class: i === currentIdx ? 'cm-searchMatch cm-searchMatchCurrent' : 'cm-searchMatch',
      }).range(r.from, r.to))
    return Decoration.set(marks, true)
  },
  provide: f => EditorView.decorations.from(f),
})

function findNext() {
  if (!view || !searchRanges.length) return
  const pos = view.state.selection.main.to
  let idx = searchRanges.findIndex(r => r.to > pos)
  if (idx < 0) idx = 0
  gotoMatch(idx)
}

function findPrev() {
  if (!view || !searchRanges.length) return
  const pos = view.state.selection.main.from
  let idx = -1
  for (let i = searchRanges.length - 1; i >= 0; i--) {
    if (searchRanges[i].from < pos) { idx = i; break }
  }
  if (idx < 0) idx = searchRanges.length - 1
  gotoMatch(idx)
}

function gotoMatch(idx: number) {
  if (!view || idx < 0 || idx >= searchRanges.length) return
  currentIdx = idx
  currentMatch.value = idx + 1
  const r = searchRanges[idx]
  view.dispatch({
    selection: { anchor: r.from, head: r.to },
    scrollIntoView: true,
    effects: setSearchEffect.of(currentSpec),
  })
}

// $1..$99 group refs and $$ in regex mode; literal text otherwise.
function expandReplacement(matched: string, groups: (string | undefined)[]): string {
  return replaceText.value.replace(/\$(\$|&|\d{1,2})/g, (_, g: string) => {
    if (g === '$') return '$'
    if (g === '&') return matched
    return groups[Number(g)] ?? ''
  })
}

function computeReplacement(matched: string): string {
  if (!regexpMode.value || !currentSpec) return replaceText.value
  const re = new RegExp(buildSource(currentSpec), caseSensitive.value ? '' : 'i')
  const m = re.exec(matched)
  if (!m) return replaceText.value
  return expandReplacement(m[0], m.slice(1))
}

function replaceCurrent() {
  if (!view || currentIdx < 0 || !searchRanges[currentIdx]) return
  const r = searchRanges[currentIdx]
  const insert = computeReplacement(view.state.sliceDoc(r.from, r.to))
  view.dispatch({
    changes: { from: r.from, to: r.to, insert },
    selection: { anchor: r.from + insert.length },
    effects: setSearchEffect.of(currentSpec),
  })
}

function replaceAllMatches() {
  if (!view || !searchRanges.length || !currentSpec) return
  const spec = currentSpec
  try {
    const re = new RegExp(buildSource(spec), spec.caseSensitive ? 'g' : 'gi')
    const docStr = view.state.doc.toString()
    const out = spec.regexp
      ? docStr.replace(re, (...args: unknown[]) => {
          const groups = args.slice(1, args.length - 2) as (string | undefined)[]
          return expandReplacement(args[0] as string, groups)
        })
      : docStr.replace(re, () => replaceText.value)
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: out },
      selection: { anchor: 0 },
      effects: setSearchEffect.of(spec),
    })
  } catch { /* invalid pattern: nothing to do */ }
}

async function openSearch(replace = false) {
  searchOpen.value = true
  if (replace) replaceRowOpen.value = true
  emit('search-open', true)
  // Re-scan even when the query text didn't change: closeSearch cleared the
  // decorations, and the query watcher only fires on actual changes.
  currentSpec = buildSpec()
  view?.dispatch({ effects: setSearchEffect.of(currentSpec) })
  if (view) {
    const sel = view.state.selection.main
    if (sel.from !== sel.to) {
      const text = view.state.sliceDoc(sel.from, sel.to)
      // Prefill single-line selections only; a multi-line slice is useless as a query.
      if (text.length <= 200 && !/\n/.test(text)) searchText.value = text
    }
  }
  await nextTick()
  if (replaceRowOpen.value) replaceInputRef.value?.focus()
  else searchInputRef.value?.focus()
}

function closeSearch() {
  searchOpen.value = false
  replaceRowOpen.value = false
  emit('search-open', false)
  if (view) view.dispatch({ effects: setSearchEffect.of(null) })
  view?.focus()
}

function toggleSearch(): boolean {
  if (searchOpen.value) closeSearch()
  else void openSearch()
  return searchOpen.value
}

// Clipboard ops, Wails-first (same paths the terminal uses: writeClipboard
// falls back to the browser API; Clipboard.Text avoids the macOS paste
// confirmation prompt that navigator.clipboard.readText pops). Copy/cut are
// no-ops with an empty selection; cut/paste are blocked on readonly editors.
async function copySelection(): Promise<boolean> {
  if (!view) return false
  const { from, to } = view.state.selection.main
  if (from === to) return false
  return writeClipboard(view.state.sliceDoc(from, to))
}

async function cutSelection(): Promise<boolean> {
  if (!view || props.readonly) return false
  const { from, to } = view.state.selection.main
  if (from === to) return false
  const text = view.state.sliceDoc(from, to)
  const ok = await writeClipboard(text)
  if (ok) view.dispatch({ changes: { from, to }, selection: { anchor: from } })
  return ok
}

async function pasteFromClipboard(): Promise<boolean> {
  if (!view || props.readonly) return false
  let text = ''
  try {
    text = typeof Clipboard.Text === 'function' ? await Clipboard.Text() : await navigator.clipboard.readText()
  } catch {
    return false
  }
  if (!text) return false
  const { from, to } = view.state.selection.main
  view.dispatch({ changes: { from, to, insert: text }, selection: { anchor: from + text.length } })
  return true
}

// Any query change re-scans and jumps to the nearest match.
watch([searchText, caseSensitive, regexpMode, wholeWord], () => {
  if (!view) return
  currentSpec = buildSpec()
  view.dispatch({ effects: setSearchEffect.of(currentSpec) })
  if (currentSpec) gotoMatch(idxFromPos(view.state.selection.main.head))
})

function extOf(path: string): string {
  const base = path.replace(/\\/g, '/').split('/').pop() || ''
  const lower = base.toLowerCase()
  if (lower === 'dockerfile' || lower.startsWith('dockerfile.')) return 'dockerfile'
  if (lower === 'makefile' || lower === 'gnumakefile') return 'makefile'
  if (lower === '.bashrc' || lower === '.zshrc' || lower === '.profile' || lower === '.bash_profile') return 'sh'
  if (lower === '.gitignore' || lower === '.dockerignore' || lower === '.env' || lower.endsWith('.env')) return 'conf'
  if (lower === 'nginx.conf' || lower.endsWith('.nginx')) return 'nginx'
  const i = lower.lastIndexOf('.')
  return i >= 0 ? lower.slice(i + 1) : ''
}

// Force a specific highlight mode; matches the extension-based picks. 'text' or
// anything unknown yields no language extension (plain text).
function languageFor(id?: string) {
  switch (id) {
    case 'json': return json()
    case 'js': return javascript()
    case 'ts': return javascript({ typescript: true })
    case 'html': return html()
    case 'css': return css()
    case 'xml': return xml()
    case 'md': return markdown()
    case 'py': return python()
    case 'sql': return sql()
    case 'yaml': return yaml()
    case 'sh': return StreamLanguage.define(shell)
    case 'conf': return StreamLanguage.define(properties)
    case 'toml': return StreamLanguage.define(toml)
    case 'dockerfile': return StreamLanguage.define(dockerFile)
    case 'nginx': return StreamLanguage.define(nginx)
    case 'c':
    case 'cpp': return cpp()
    case 'csharp': return StreamLanguage.define((clike as any).csharp)
    case 'dart': return StreamLanguage.define((clike as any).dart)
    case 'java': return java()
    case 'kotlin': return StreamLanguage.define((clike as any).kotlin)
    case 'scala': return StreamLanguage.define((clike as any).scala)
    case 'go': return go()
    case 'rust': return rust()
    case 'ruby': return StreamLanguage.define(ruby)
    default: return []
  }
}

function languageExtension(path: string) {
  const ext = extOf(path || '')
  switch (ext) {
    case 'json':
    case 'jsonc':
    case 'json5':
      return json()
    case 'js':
    case 'mjs':
    case 'cjs':
    case 'jsx':
    case 'ts':
    case 'tsx':
      return javascript({ typescript: ext === 'ts' || ext === 'tsx', jsx: ext === 'jsx' || ext === 'tsx' })
    case 'html':
    case 'htm':
    case 'vue':
      return html()
    case 'css':
    case 'scss':
    case 'less':
      return css()
    case 'xml':
    case 'svg':
    case 'plist':
      return xml()
    case 'md':
    case 'markdown':
      return markdown()
    case 'py':
      return python()
    case 'sql':
      return sql()
    case 'c':
    case 'h':
    case 'cpp':
    case 'cc':
    case 'cxx':
    case 'hpp':
      return cpp()
    case 'java':
      return java()
    case 'go':
      return go()
    case 'rs':
      return rust()
    case 'sh':
    case 'bash':
    case 'zsh':
    case 'ksh':
    case 'fish':
      return StreamLanguage.define(shell)
    case 'conf':
    case 'cfg':
    case 'ini':
    case 'properties':
    case 'service':
    case 'desktop':
      return StreamLanguage.define(properties)
    case 'toml':
      return StreamLanguage.define(toml)
    case 'dockerfile':
      return StreamLanguage.define(dockerFile)
    case 'nginx':
      return StreamLanguage.define(nginx)
    default:
      if (/\.conf(\.|$)/i.test(path || '') || /\/conf\//i.test(path || '')) {
        return StreamLanguage.define(properties)
      }
      return []
  }
}

function buildExtensions(path: string) {
  return [
    lineNumbers(),
    highlightActiveLine(),
    highlightActiveLineGutter(),
    drawSelection(),
    history(),
    // Own search state: decorations for all matches + the current one (the
    // query itself is managed by the Vue search bar above the editor).
    searchDecoField,
    foldGutter(),
    bracketMatching(),
    // Dark: One Dark tokens; light: defaultHighlightStyle (light-tuned) takes
    // over as the active highlighter via the fallback chain.
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    ...(isDark.value ? [oneDark] : []),
    EditorState.readOnly.of(!!props.readonly),
    EditorView.editable.of(!props.readonly),
    props.lang ? languageFor(props.lang) : languageExtension(path),
    keymap.of([
      {
        key: 'Mod-Enter',
        run: () => {
          emit('execute')
          return true
        },
      },
      {
        key: 'Mod-f',
        run: () => {
          void openSearch()
          return true
        },
      },
      {
        key: 'Mod-h',
        run: () => {
          void openSearch(true)
          return true
        },
      },
      {
        key: 'Escape',
        run: () => {
          if (searchOpen.value) {
            closeSearch()
            return true
          }
          return false
        },
      },
      ...defaultKeymap,
      ...historyKeymap,
      ...foldKeymap,
      indentWithTab,
    ]),
    EditorView.updateListener.of((update) => {
      if (!update.docChanged || applyingExternal) return
      emit('update:modelValue', update.state.doc.toString())
    }),
    EditorView.theme({
      '&': {
        height: '100%',
        width: '100%',
        maxWidth: '100%',
        // Inherit from the host so font-size changes don't need a rebuild
        // (a rebuild would drop undo history and cursor position).
        fontSize: 'inherit',
        outline: 'none',
      },
      '&.cm-editor': {
        height: '100%',
        width: '100%',
      },
      '&.cm-editor.cm-focused': { outline: 'none' },
      '.cm-scroller': {
        fontFamily: 'var(--font-mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace)',
        overflow: 'auto',
        width: '100%',
        minWidth: '0',
      },
      '.cm-content': { minHeight: '100%', minWidth: 0, boxSizing: 'border-box' },
      '.cm-gutters': { backgroundColor: 'transparent', border: 'none' },
      // Strong selection highlight — oneDark default is too subtle, and has-bg
      // mode can further wash it out via global transparent rules.
      '.cm-selectionBackground, &.cm-focused .cm-selectionBackground': {
        backgroundColor: 'rgba(64, 158, 255, 0.45) !important',
      },
      '&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground': {
        backgroundColor: 'rgba(64, 158, 255, 0.45) !important',
      },
      '.cm-content ::selection': {
        backgroundColor: 'rgba(64, 158, 255, 0.45) !important',
      },
      // Search matches: amber for all hits, accent ring for the current one —
      // readable on both the light and One Dark backgrounds.
      '.cm-searchMatch': {
        backgroundColor: 'rgba(250, 204, 21, 0.25)',
      },
      '.cm-searchMatchCurrent': {
        backgroundColor: 'rgba(250, 204, 21, 0.5)',
        outline: '1px solid rgba(245, 158, 11, 0.9)',
      },
    }),
    ...(props.wrap === false ? [] : [EditorView.lineWrapping]),
  ]
}

function requestMeasure() {
  view?.requestMeasure()
}

function createEditor() {
  if (!hostRef.value) return
  view?.destroy()
  view = new EditorView({
    parent: hostRef.value,
    state: EditorState.create({
      doc: props.modelValue || '',
      extensions: buildExtensions(props.filePath || ''),
    }),
  })
  requestMeasure()
}

function setDoc(text: string) {
  if (!view) return
  const cur = view.state.doc.toString()
  if (cur === text) return
  applyingExternal = true
  view.dispatch({
    changes: { from: 0, to: view.state.doc.length, insert: text },
  })
  applyingExternal = false
}

watch(() => props.modelValue, (v) => {
  setDoc(v ?? '')
})

watch(() => [props.filePath, props.lang, props.wrap, props.readonly], async () => {
  const text = view?.state.doc.toString() ?? props.modelValue
  await nextTick()
  createEditor()
  if (text !== props.modelValue) setDoc(text)
})

// Theme swap needs a full rebuild: oneDark vs defaultHighlightStyle are
// different extension sets, and EditorState extensions are immutable.
watch(isDark, async () => {
  const text = view?.state.doc.toString() ?? props.modelValue
  await nextTick()
  createEditor()
  if (text !== props.modelValue) setDoc(text)
})

onMounted(() => {
  createEditor()
  if (hostRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => requestMeasure())
    resizeObserver.observe(hostRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  view?.destroy()
  view = null
})

defineExpose({
  focus: () => view?.focus(),
  getValue: () => view?.state.doc.toString() ?? props.modelValue,
  undo: () => { if (view) return undo(view) },
  redo: () => { if (view) return redo(view) },
  toggleSearch,
  copy: copySelection,
  cut: cutSelection,
  paste: pasteFromClipboard,
  getSelectedOrAll: () => {
    if (!view) return props.modelValue
    const { from, to } = view.state.selection.main
    if (from !== to) return view.state.sliceDoc(from, to)
    return view.state.doc.toString()
  },
})
</script>

<style scoped>
.syntax-editor {
  position: relative;
  width: 100%;
  min-width: 0;
  height: 55vh;
  font-size: 13px;
  border: 1px solid var(--border-subtle);
  border-radius: 0.25rem;
  overflow: hidden;
  background: var(--bg-base);
  color: var(--text-primary);
  box-sizing: border-box;
}
/* Keep the container background in sync with the active CodeMirror theme. */
.syntax-editor.theme-dark {
  background: #282c34;
  color: #abb2bf;
}
.syntax-editor.compact {
  height: 100%;
  width: 100%;
  min-width: 0;
  flex: 1 1 auto;
  align-self: stretch;
  border-radius: var(--radius-sm);
}
.syntax-editor :deep(.cm-editor) {
  position: absolute !important;
  inset: 0 !important;
  width: auto !important;
  height: auto !important;
  max-width: none !important;
}
.syntax-editor :deep(.cm-scroller) {
  min-width: 0 !important;
}
.syntax-editor :deep(.cm-focused) {
  outline: none;
}
.syntax-editor :deep(.cm-selectionBackground),
.syntax-editor :deep(.cm-focused .cm-selectionBackground),
.syntax-editor :deep(.cm-content ::selection) {
  background-color: rgba(64, 158, 255, 0.45) !important;
}
/* Search/replace bar — same tokens as the app chrome, floating top-right. */
.search-bar {
  position: absolute;
  top: 0.25rem;
  right: 0.75rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}
.search-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.search-row .search-input {
  width: 13rem;
}
/* Aligns the replace input under the search input: search row = 3 toggles
   + 3 gaps (between them and before the input); replace row adds one gap
   between the spacer and the input, so the spacer is 2 gaps narrower. */
.search-row .replace-spacer {
  width: calc(3 * 1.625rem + 0.5rem);
  flex-shrink: 0;
}
.match-count {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.match-count.none {
  color: var(--el-color-danger, #f56c6c);
}
.search-icon-btn {
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
.search-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.search-icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
  background: transparent;
  color: var(--text-muted);
}
.search-icon-btn.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
</style>
