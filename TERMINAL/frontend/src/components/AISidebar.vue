<template>
  <div ref="sidebarEl" class="ai-sidebar" :class="{ collapsed: !aiStore.visible, resizing: isResizing, maximized: isMaximized }" :style="{ width: sidebarWidth + 'px' }">
    <div class="resize-handle" @mousedown="onResizeStart" />
    <div class="ai-header">
      <span>{{ t('ai.title') }}</span>
      <div class="ai-actions">
        <button class="ai-action-btn" @click="onNewSession" :title="t('ai.newSession')">
          <el-icon><MessageSquarePlus :size="'0.875rem'" /></el-icon>
        </button>
        <button v-if="aiStore.sessions.length > 0" class="ai-action-btn" :title="t('ai.recentSessions')" @click.stop="sessionMenuRef?.toggle($event.currentTarget)" >
          <el-icon><History :size="'0.875rem'" /></el-icon>
        </button>
        <Menu ref="sessionMenuRef" v-model:visible="sessionMenuVisible">
          <MenuItem
            v-for="s in aiStore.sessions"
            :key="s.id"
            :class="{ active: s.id === aiStore.currentSessionId }"
            @click="onSessionSelect(s.id)"
          >
            <span class="session-item-name">{{ s.name }}</span>
            <span class="session-time">{{ formatRelativeTime(s.updatedAt) }}</span>
            <template #trailing>
              <el-icon class="session-delete" :title="t('ai.renameSession')" @click.stop="onSessionRename(s.id); closeMenus()"><Pencil :size="'0.875rem'" /></el-icon>
              <el-icon class="session-delete" @click.stop="aiStore.deleteSession(s.id); closeMenus()"><Trash2 :size="'0.875rem'" /></el-icon>
            </template>
          </MenuItem>
        </Menu>
        <button class="ai-action-btn" @click="searchVisible = !searchVisible" :title="t('ai.search')">
          <el-icon><Search :size="'0.875rem'" /></el-icon>
        </button>
        <button class="ai-action-btn" @click="toggleMaximize" :title="isMaximized ? t('ai.restore') : t('ai.maximize')">
          <el-icon><Shrink v-if="isMaximized" :size="'0.875rem'" /><Expand v-else :size="'0.875rem'" /></el-icon>
        </button>
        <button class="ai-action-btn" @click="onClose" :title="t('sidebar.collapse')">
          <el-icon><X :size="'0.875rem'" /></el-icon>
        </button>
      </div>
    </div>

    <div v-show="searchVisible" class="ai-search-bar">
      <input
        ref="searchInputRef"
        v-model="searchText"
        class="search-input"
        :placeholder="t('ai.searchPlaceholder')"
        @input="onSearchInput"
        @keydown.enter.prevent="onSearchNext"
        @keydown.shift.enter.prevent="onSearchPrev"
        @keydown.escape="closeSearch"
      />
      <span class="search-count" v-if="searchText">{{ currentMatchIndex + 1 }}/{{ totalMatchCount || 0 }}</span>
      <button class="search-btn" @click="onSearchPrev" :title="t('terminal.searchPrev')">
        <ChevronUp :size="'0.875rem'" />
      </button>
      <button class="search-btn" @click="onSearchNext" :title="t('terminal.searchNext')">
        <ChevronDown :size="'0.875rem'" />
      </button>
      <button class="search-btn" @click="closeSearch" :title="t('ai.close')">
        <el-icon><X :size="'0.75rem'" /></el-icon>
      </button>
    </div>

    <div ref="messagesRef" class="ai-messages" @contextmenu="onAIContextMenu">
      <div
        v-for="msg in visibleMessages"
        :key="msg.id"
        @contextmenu.stop.prevent="onMessageContextMenu($event, msg.id)"
      >
        <AIMessage
          :message="msg"
          :search-text="searchText"
          @approve="onApprove"
          @reject="onReject"
          @continue="onContinue"
          @answer="onAnswer"
          @dismiss="onDismiss"
        />
      </div>
      <div v-if="aiStore.isRunning || aiStore.pendingCommand || aiStore.pendingQuestion" class="ai-thinking">
        <div class="thinking-text">{{ statusText }}</div>
      </div>
    </div>

    <!-- AI messages context menu -->
    <Menu ref="aiMenuRef" v-model:visible="aiMenuVisible">
      <MenuItem @click="aiCopySelection">{{ t('terminal.copy') }}</MenuItem>
      <MenuItem @click="aiAskSelection">{{ t('terminal.askAI') }}</MenuItem>
    </Menu>

    <!-- Message context menu: right-click a message bubble for export /
         delete / rollback; falls back to copy / ask-AI when text is selected. -->
    <Menu ref="msgCtxMenuRef" v-model:visible="msgCtxMenuVisible">
      <template v-if="msgCtxId">
        <template v-if="msgCtxHasSelection">
          <MenuItem @click="aiCopySelection">{{ t('terminal.copy') }}</MenuItem>
          <MenuItem @click="aiAskSelection">{{ t('terminal.askAI') }}</MenuItem>
          <MenuDivider />
        </template>
        <MenuItem @click="onMsgCtxExport">{{ t('ai.exportMd') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onMsgCtxDelete(msgCtxId)">{{ t('ai.deleteMessage') }}</MenuItem>
        <MenuItem @click="onMsgCtxTruncate(msgCtxId)">{{ t('ai.truncateFrom') }}</MenuItem>
      </template>
    </Menu>

    <div class="ai-input">
      <!-- Panel tags area -->
      <div class="ai-panel-tags">
        <div class="panel-tags-list">
          <template v-if="lockedPanels.length === 0 && currentIsTerminal">
            <span class="panel-tag panel-tag-default">{{ currentTerminalLabel }}</span>
          </template>
          <template v-else-if="lockedPanels.length > 0">
            <span
              v-for="pid in lockedPanels"
              :key="pid"
              class="panel-tag"
            >
              {{ getPanelDisplayName(pid) }}
              <button class="panel-tag-close" @click="onRemovePanelTag(pid)">&times;</button>
            </span>
          </template>
          <button class="panel-tag-add-btn" :title="t('ai.addTerminal')" @click.stop="addTagMenuRef?.toggle($event.currentTarget)">+</button>
            <Menu ref="addTagMenuRef" v-model:visible="addTagMenuVisible">
              <MenuItem
                v-for="p in availableTerminalPanels"
                :key="p.id"
                :class="{ active: lockedPanels.includes(p.id) }"
                @click="onAddPanelTagSelect(p.id)"
              >
                <span>{{ getPanelDisplayName(p.id) }}</span>
                <span class="panel-shell-hint">{{ getPanelShellHint(p.id) }}</span>
              </MenuItem>
            </Menu>
        </div>
      </div>

      <div class="input-container">
        <!-- # reference dropdown -->
        <div
          v-if="hashDropdownVisible && hashMatchingPanels.length > 0"
          class="hash-dropdown"
        >
          <div
            v-for="(p, i) in hashMatchingPanels"
            :key="p.id"
            class="hash-dropdown-item"
            :class="{ highlighted: i === hashHighlightIndex }"
            @mousedown.prevent="onSelectHashPanel(p.title)"
          >
            <span class="hash-panel-name">#{{ p.title }}</span>
            <span v-if="lockedPanels.includes(p.id)" class="hash-associated-badge">已关联</span>
            <span class="hash-panel-hint">{{ getPanelShellHint(p.id) }}</span>
          </div>
        </div>

        <!-- / skill & command dropdown -->
        <div
          v-if="skillDropdownVisible && skillMatchingItems.length > 0"
          class="skill-dropdown"
        >
          <div
            v-for="(item, i) in skillMatchingItems"
            :key="item.kind + '/' + item.name"
            class="skill-dropdown-item"
            :class="{ highlighted: i === skillHighlightIndex }"
            @mousedown.prevent="onSelectItem(item)"
          >
            <component :is="item.kind === 'command' ? Terminal : BookOpen" :size="'0.8125rem'" class="skill-dropdown-kind-icon" />
            <span class="skill-dropdown-name">/{{ item.name }}</span>
            <span v-if="item.kind === 'command' && item.argumentHint" class="skill-dropdown-args">{{ item.argumentHint }}</span>
            <span class="skill-dropdown-desc">{{ item.description }}</span>
          </div>
        </div>

        <div v-if="aiStore.queuedMessages.length" class="queued-area">
          <div v-for="q in aiStore.queuedMessages" :key="q.id" class="queued-chip">
            <span class="queued-text">{{ q.content }}</span>
            <button class="queued-remove" :title="t('ai.queueRemove')" @click="aiStore.removeQueuedMessage(q.id)">
              <X :size="'0.75rem'" />
            </button>
          </div>
        </div>
        <div class="textarea-wrap">
          <div
            ref="editableRef"
            class="ai-editable"
            :contenteditable="lockedPanels.length > 0 || currentIsTerminal ? 'true' : 'false'"
            :data-placeholder="lockedPanels.length === 0 && !currentIsTerminal ? t('ai.noTerminalHint') : t('ai.placeholder')"
            @input="onEditableInput"
            @keydown="onKeydown"
            @paste="onPaste"
          />
        </div>
        <div class="input-actions">
          <div class="input-actions-left">
            <button class="ghost-btn hash-btn" title="引用终端" @click="onHashButtonClick">
              <span class="hash-btn-icon">#</span>
            </button>
            <button class="ghost-btn hash-btn" title="Skill / 命令" @click="onSlashButtonClick">
              <span class="hash-btn-icon">/</span>
            </button>
            <template v-if="settingsStore.settings.ai.models.length > 0">
              <button class="ghost-btn model-btn" :title="currentModelName" @click.stop="modelMenuRef?.toggle($event.currentTarget)">{{ currentModelName }}</button>
              <Menu ref="modelMenuRef" v-model:visible="modelMenuVisible">
                <MenuItem
                  v-for="m in settingsStore.settings.ai.models"
                  :key="m.id"
                  :class="{ active: m.id === settingsStore.settings.ai.activeModelId }"
                  @click="onModelSelect(m.id)"
                >
                  <span>{{ m.name }}</span>
                </MenuItem>
                <MenuDivider />
                <MenuItem iconic :icon="Plus" @click="onModelSelect('__add_model__')">
                  {{ t('settings.addModel') }}
                </MenuItem>
              </Menu>
            </template>
            <button v-else class="ghost-btn model-btn add-model-btn" @click="onModelChange('__add_model__')">
            <Plus :size="'0.875rem'" />
            <span>{{ t('settings.addModel') }}</span>
          </button>
          </div>
          <div class="input-actions-right">
            <button class="ghost-btn mode-btn" :title="modeLabel" @click.stop="modeMenuRef?.toggle($event.currentTarget)">{{ modeLabel }}</button>
            <Menu ref="modeMenuRef" v-model:visible="modeMenuVisible">
              <MenuItem @click="onModeSelect('confirm_all')">
                <span class="mode-option mode-confirm">{{ t('ai.confirmAll') }}</span>
              </MenuItem>
              <MenuItem @click="onModeSelect('confirm_write')">
                <span class="mode-option mode-write">{{ t('ai.confirmWrite') }}</span>
              </MenuItem>
              <MenuItem @click="onModeSelect('confirm_dangerous')">
                <span class="mode-option mode-warning">{{ t('ai.confirmDangerous') }}</span>
              </MenuItem>
              <MenuItem @click="onModeSelect('bypass')">
                <span class="mode-option mode-auto">{{ t('ai.bypass') }}</span>
              </MenuItem>
            </Menu>
            <button
              v-if="!(busy && !inputText.trim())"
              class="send-btn"
              :disabled="(!inputText.trim() && !hasSkillTag && !hasCommandTag) || (lockedPanels.length === 0 && !currentIsTerminal)"
              :title="busy ? t('ai.queue') : t('ai.send')"
              @click="onSend"
            >
              <ArrowUp :size="'1.125rem'" />
            </button>
            <button v-else class="send-btn stop" :title="t('ai.stop')" @click="onStop">
              <Square :size="'0.9375rem'" :fill="'currentColor'" />
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, watch, onMounted, onUnmounted } from 'vue'
import { X, Trash2, Expand, Shrink, History, MessageSquarePlus, Search, ChevronDown, ChevronUp, ArrowUp, Square, Plus, BookOpen, Terminal, Pencil } from '@lucide/vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAIStore } from '../stores/aiStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useSkillStore } from '../stores/skillStore'
import { useCommandStore } from '../stores/commandStore'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useI18n } from '../i18n'
import { runAgent, approveTool, rejectTool, continueAgent, answerQuestion, dismissQuestion } from '../services/agent'
import { CancelChatStream, SaveFileDialogFiltered, WriteFileBase64 } from '../../bindings/easyaiot/terminal/app'
import type { ExecutionMode } from '../types/ai'
import AIMessage from './AIMessage.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import { Clipboard } from '@wailsio/runtime'
import MenuDivider from './MenuDivider.vue'
import { writeClipboard } from '../composables/useClipboardWrite'

const aiStore = useAIStore()
const settingsStore = useSettingsStore()
const tabStore = useTabStore()
const panelStore = usePanelStore()
const skillStore = useSkillStore()
const commandStore = useCommandStore()
const { t } = useI18n()
const editableRef = ref<HTMLDivElement | null>(null)

// Derive plain text from contenteditable div (hash-tag spans contribute #PanelName)
function getEditableText(): string {
  const el = editableRef.value
  if (!el) return ''
  let text = ''
  const walk = (node: Node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      text += node.textContent || ''
    } else if (node instanceof HTMLElement) {
      if (node.classList.contains('skill-tag')) {
        // skill tag 不贡献文本(skill 正文单独注入,不发给终端)
        return
      }
      if (node.classList.contains('command-tag')) {
        return // command tag 不贡献文本（正文后台组装）
      }
      if (node.classList.contains('hash-tag')) {
        text += node.getAttribute('data-ref') || node.textContent || ''
      } else {
        node.childNodes.forEach(walk)
      }
    }
  }
  el.childNodes.forEach(walk)
  return text
}

// 从输入框里提取已插入的 skill 名(取第一个 skill-tag)
function extractSkillFromInput(): string | null {
  const el = editableRef.value
  if (!el) return null
  const tag = el.querySelector('.skill-tag')
  return tag?.getAttribute('data-skill') || null
}

// Create a skill inline tag span (/name), styled like a hash-tag, carries data-skill
function createSkillTagSpan(name: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'hash-tag skill-tag'
  span.setAttribute('data-skill', name)
  span.contentEditable = 'false'
  span.textContent = '/' + name
  const el = editableRef.value
  if (el) {
    for (const attr of el.attributes) {
      if (attr.name.startsWith('data-v-')) {
        span.setAttribute(attr.name, '')
        break
      }
    }
  }
  return span
}

function createCommandTagSpan(name: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'hash-tag command-tag'
  span.setAttribute('data-command', name)
  span.contentEditable = 'false'
  span.textContent = '/' + name
  const el = editableRef.value
  if (el) {
    for (const attr of el.attributes) {
      if (attr.name.startsWith('data-v-')) { span.setAttribute(attr.name, ''); break }
    }
  }
  return span
}

function extractCommandFromInput(): { name: string; args: string } | null {
  const el = editableRef.value
  if (!el) return null
  const tag = el.querySelector('.command-tag')
  const name = tag?.getAttribute('data-command')
  if (!name) return null
  // 参数 = tag 之后的纯文本
  let args = ''
  let after = false
  const walk = (node: Node) => {
    if (node === tag) { after = true; return }
    if (!after) return
    if (node.nodeType === Node.TEXT_NODE) { args += node.textContent || ''; return }
    // skill/command/hash tag 的文本（/name、#panel）不是参数，跳过
    if (node instanceof HTMLElement && (node.classList.contains('skill-tag') || node.classList.contains('command-tag') || node.classList.contains('hash-tag'))) return
    node.childNodes.forEach(walk)
  }
  el.childNodes.forEach(walk)
  return { name, args: args.trim() }
}

// Create a hash-tag span with scoped CSS attribute so styles apply
function createHashTagSpan(panelTitle: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'hash-tag'
  span.setAttribute('data-ref', '#' + panelTitle)
  span.contentEditable = 'false'
  span.textContent = '#' + panelTitle
  // Copy scoped style attribute from editable div so Vue scoped CSS matches
  const el = editableRef.value
  if (el) {
    for (const attr of el.attributes) {
      if (attr.name.startsWith('data-v-') || attr.name.startsWith('data-v')) {
        span.setAttribute(attr.name, '')
        break
      }
    }
  }
  return span
}

// Computed: input text (for watch)
const inputText = ref('')
const hasSkillTag = ref(false)
const hasCommandTag = ref(false)
function syncInputText() {
  inputText.value = getEditableText()
  hasSkillTag.value = extractSkillFromInput() !== null
  hasCommandTag.value = extractCommandFromInput() !== null
}

function onEditableInput() {
  syncInputText(); refreshHashDropdown(); refreshSkillDropdown()
}

// MutationObserver as backup — catches changes that don't fire 'input' event
onMounted(() => {
  if (editableRef.value) {
    editableObserver = new MutationObserver(() => { syncInputText(); refreshHashDropdown(); refreshSkillDropdown() })
    editableObserver.observe(editableRef.value, { childList: true, subtree: true, characterData: true })
  }
})

function focusInput() {
  nextTick(() => {
    editableRef.value?.focus()
  })
}

const visibleMessages = computed(() => {
  return aiStore.messages.filter(m => {
    if (m.role === 'tool' && m.tool_call_id) return false
    if (m.role === 'tool' && !m.tool_call_id) return true
    if (m.role !== 'assistant') return true
    const hasPending = aiStore.pendingCommand?.messageId === m.id
    return m.content || m.tool_calls?.length || hasPending || m.needsContinue
  })
})

// ── Search ──
const searchVisible = ref(false)
const searchText = ref('')
const searchInputRef = ref<HTMLInputElement>()
const currentMatchIndex = ref(0)
const totalMatchCount = ref(0)

function onSearchInput() {
  currentMatchIndex.value = 0
  highlightMatches()
}

function highlightMatches() {
  nextTick(() => {
    const marks = messagesRef.value?.querySelectorAll('mark.ai-search-highlight')
    totalMatchCount.value = marks?.length || 0
    updateActiveMark()
  })
}

function updateActiveMark() {
  const marks = messagesRef.value?.querySelectorAll('mark.ai-search-highlight')
  marks?.forEach((m, i) => {
    m.classList.toggle('active', i === currentMatchIndex.value)
  })
  if (marks && marks[currentMatchIndex.value]) {
    marks[currentMatchIndex.value].scrollIntoView({ block: 'center', behavior: 'smooth' })
  }
}

function onSearchNext() {
  if (totalMatchCount.value === 0) return
  currentMatchIndex.value = (currentMatchIndex.value + 1) % totalMatchCount.value
  updateActiveMark()
}

function onSearchPrev() {
  if (totalMatchCount.value === 0) return
  currentMatchIndex.value = (currentMatchIndex.value - 1 + totalMatchCount.value) % totalMatchCount.value
  updateActiveMark()
}

function closeSearch() {
  searchVisible.value = false
  searchText.value = ''
  currentMatchIndex.value = 0
  totalMatchCount.value = 0
}

// Watch for DOM changes (messages loaded/streamed) to re-count highlights
watch(() => [searchText.value, visibleMessages.value.length], () => {
  if (searchText.value) highlightMatches()
})
const statusText = computed(() => {
  if (aiStore.pendingCommand) return t('ai.confirming')
  if (aiStore.pendingQuestion) return t('ai.awaitingAnswer')
  const key = `ai.${aiStore.status}` as any
  return t(key) || t('ai.thinking')
})

const messagesRef = ref<HTMLDivElement>()
const sidebarWidth = ref(360)
const isResizing = ref(false)
const isMaximized = ref(false)
const preMaxWidth = ref(360)

function toggleMaximize() {
  if (isMaximized.value) {
    sidebarWidth.value = preMaxWidth.value
    isMaximized.value = false
    window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
  } else {
    preMaxWidth.value = sidebarWidth.value
    isMaximized.value = true
    window.dispatchEvent(new CustomEvent('rdp:overlay-push'))
  }
}

function onClose() {
  if (isMaximized.value) {
    isMaximized.value = false
    sidebarWidth.value = preMaxWidth.value
    window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
  }
  aiStore.toggle()
}
const sidebarEl = ref<HTMLDivElement>()
const aiMenuVisible = ref(false)
const aiMenuRef = ref<InstanceType<typeof Menu> | null>(null)

// ── Trigger menus (Menu.vue teleported .conn-context-menu) ──
const sessionMenuVisible = ref(false)
const addTagMenuVisible = ref(false)
const modelMenuVisible = ref(false)
const modeMenuVisible = ref(false)

const sessionMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const addTagMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const modelMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const modeMenuRef = ref<InstanceType<typeof Menu> | null>(null)

function onSessionSelect(id: string) { closeMenus(); onSessionCommand(id) }
function onAddPanelTagSelect(id: string) { closeMenus(); onAddPanelTag(id) }
function onModelSelect(id: string) { closeMenus(); onModelChange(id) }
function onModeSelect(mode: string) { closeMenus(); onModeChange(mode) }

// ── Session rename (pencil button in the history dropdown) ──
async function onSessionRename(id: string) {
  const s = aiStore.sessions.find(x => x.id === id)
  if (!s) return
  try {
    const name = await ElMessageBox.prompt('', t('ai.renameSession'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputValue: s.name,
    })
    const v = (name.value || '').trim()
    if (v) aiStore.renameSession(id, v)
  } catch { /* cancelled */ }
}

// ── Markdown export of the current session (message context menu) ──
async function onMsgCtxExport() {
  msgCtxMenuVisible.value = false
  const id = aiStore.currentSessionId
  const s = aiStore.sessions.find(x => x.id === id)
  if (!s) return
  try {
    const md = aiStore.exportSessionMarkdown(id)
    const safe = s.name.replace(/[\\/:*?"<>|]/g, '_').slice(0, 60)
    const path = await SaveFileDialogFiltered(t('ai.exportMd'), `${safe}.md`, 'Markdown File', '*.md')
    if (!path) return
    const bytes = new TextEncoder().encode(md)
    let bin = ''
    for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i])
    await WriteFileBase64(path, btoa(bin))
    ElMessage.success(t('ai.exportDone', { name: s.name }))
  } catch (e: any) {
    ElMessage.error(e?.message || String(e))
  }
}

// ── Message context menu ──
const msgCtxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const msgCtxMenuVisible = ref(false)
const msgCtxId = ref('')
const msgCtxHasSelection = ref(false)
const aiSelectionText = ref('')

function captureAISelection() {
  aiSelectionText.value = window.getSelection()?.toString() || ''
}

function onMessageContextMenu(e: MouseEvent, id: string) {
  e.preventDefault()
  captureAISelection()
  msgCtxId.value = id
  msgCtxHasSelection.value = !!(window.getSelection()?.toString())
  msgCtxMenuRef.value?.openAt(e.clientX, e.clientY, id)
}

function onMsgCtxDelete(id: string) {
  msgCtxMenuVisible.value = false
  aiStore.deleteMessage(id)
}

function onMsgCtxTruncate(id: string) {
  msgCtxMenuVisible.value = false
  aiStore.truncateFrom(id)
}
const isAtBottom = ref(true)
let editableObserver: MutationObserver | null = null
let messagesObserver: MutationObserver | null = null

const modeLabel = computed(() => {
  switch (aiStore.mode) {
    case 'bypass': return t('ai.bypass')
    case 'confirm_dangerous': return t('ai.confirmDangerous')
    case 'confirm_write': return t('ai.confirmWrite')
    case 'confirm_all': return t('ai.confirmAll')
    default: return t('ai.confirmDangerous')
  }
})

const currentModelName = computed(() => {
  const m = settingsStore.settings.ai.models.find(m => m.id === settingsStore.settings.ai.activeModelId)
  return m?.name || 'Model'
})

const busy = computed(() => aiStore.isRunning || !!aiStore.pendingCommand || !!aiStore.pendingQuestion)

// Panel tags
const lockedPanels = computed(() => [...tabStore.aiLockedPanelIds])

const currentIsTerminal = computed(() => {
  const tab = tabStore.activeTab
  if (tab?.type === 'terminal') return true
  if (tab?.type === 'workspace') {
    const pid = (tab as any).activePanelId
    return !!(pid && panelStore.getPanel(pid))
  }
  return false
})

const currentTerminalLabel = computed(() => {
  const tab = tabStore.activeTab
  if (!tab) return t('ai.currentTerminal')
  let panelId: string | undefined
  if (tab.type === 'terminal') {
    panelId = (tab as any).panelId
  } else if (tab.type === 'workspace') {
    panelId = (tab as any).activePanelId
  }
  if (!panelId) return t('ai.currentTerminal')
  const panel = panelStore.getPanel(panelId)
  return panel ? `${t('ai.currentTerminal')}: ${panel.title}` : t('ai.currentTerminal')
})

const availableTerminalPanels = computed(() => {
  const result: Array<{ id: string; title: string; type: string; shellPath?: string; config?: any }> = []
  const seen = new Set<string>()
  for (const tab of tabStore.tabs) {
    if (tab.type === 'terminal' && (tab as any).panelId) {
      const p = panelStore.getPanel((tab as any).panelId)
      if (p && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl') && !seen.has(p.id)) {
        seen.add(p.id)
        result.push({ id: p.id, title: p.title, type: p.type, shellPath: p.config?.shellPath, config: p.config })
      }
    }
    if (tab.type === 'workspace' && (tab as any).panelIds) {
      for (const pid of (tab as any).panelIds) {
        const p = panelStore.getPanel(pid)
        if (p && (p.type === 'ssh' || p.type === 'local' || p.type === 'wsl') && !seen.has(p.id)) {
          seen.add(p.id)
          result.push({ id: p.id, title: p.title, type: p.type, shellPath: p.config?.shellPath, config: p.config })
        }
      }
    }
  }
  return result
})

function getPanelDisplayName(panelId: string): string {
  const p = panelStore.getPanel(panelId)
  if (!p) return panelId
  const dup = availableTerminalPanels.value.filter(ap => ap.title === p.title)
  return dup.length > 1 ? `${p.title} (id: ${p.id})` : p.title
}

function getPanelShellHint(panelId: string): string {
  const p = panelStore.getPanel(panelId)
  if (!p) return ''
  const shellPath = p.config?.shellPath
  if (shellPath) {
    const lower = shellPath.toLowerCase()
    if (lower.includes('bash') || lower.includes('sh')) return 'Bash'
    if (lower.includes('powershell') || lower.includes('pwsh')) return 'PowerShell'
    if (lower.includes('cmd')) return 'CMD'
    if (lower.includes('zsh')) return 'Zsh'
    return shellPath.split(/[\\/]/).pop() || 'Shell'
  }
  if (p.type === 'ssh') return 'SSH'
  return ''
}

function onRemovePanelTag(panelId: string) {
  tabStore.removeAILockedPanel(panelId)
}

function onAddPanelTag(panelId: string) {
  if (tabStore.isPanelAILocked(panelId)) {
    tabStore.removeAILockedPanel(panelId)
  } else {
    tabStore.addAILockedPanel(panelId)
  }
}

// # reference state
const hashQuery = ref('')
const hashDropdownVisible = ref(false)
const hashHighlightIndex = ref(0)

const skillQuery = ref('')
const skillDropdownVisible = ref(false)
const skillHighlightIndex = ref(0)

const hashMatchingPanels = computed(() => {
  const src = hashDropdownVisible.value && !hashQuery.value
    ? availableTerminalPanels.value
    : availableTerminalPanels.value
  let list = hashQuery.value
    ? src.filter(p => p.title.toLowerCase().includes(hashQuery.value.toLowerCase()))
    : [...src]
  // Sort: associated panels first
  list = [...list].sort((a, b) => {
    const aLocked = lockedPanels.value.includes(a.id) ? 0 : 1
    const bLocked = lockedPanels.value.includes(b.id) ? 0 : 1
    return aLocked - bLocked
  })
  return list
})

// `/` 补全的查询串可能带参数（如 `review 修复 bug`）：首段是名字用于匹配。
const skillNameToken = computed(() => skillQuery.value.trimStart().split(/\s+/)[0] || '')

type SlashItem = { kind: 'skill' | 'command'; name: string; description: string; argumentHint?: string }

const skillMatchingItems = computed<SlashItem[]>(() => {
  const q = skillNameToken.value.toLowerCase()
  const commands: SlashItem[] = commandStore.enabledCommands.map(c => ({ kind: 'command', name: c.name, description: c.description, argumentHint: c.argumentHint }))
  const skills: SlashItem[] = skillStore.enabledSkills.map(s => ({ kind: 'skill', name: s.name, description: s.description }))
  let list = [...commands, ...skills]
  if (q) list = list.filter(i => i.name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q))
  return list.slice(0, 8)
})

function findLastSkillSlash(text: string): number {
  for (let i = text.length - 1; i >= 0; i--) {
    if (text[i] === '/') {
      if (i === 0 || /[\s,;:.(\{\[]/.test(text[i - 1])) {
        return i
      }
    }
  }
  return -1
}

function detectSlashQuery(): string | null {
  const sel = window.getSelection()
  const el = editableRef.value
  if (!sel || !sel.rangeCount || !el) return null
  const node = sel.anchorNode
  if (!node || !el.contains(node)) return null
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent?.slice(0, sel.anchorOffset) || ''
    const idx = findLastSkillSlash(text)
    if (idx >= 0) {
      return text.slice(idx + 1)
    }
  }
  return null
}

function refreshSkillDropdown() {
  const query = detectSlashQuery()
  if (query !== null) {
    skillDropdownVisible.value = true
    skillQuery.value = query
    skillHighlightIndex.value = 0
  } else {
    skillDropdownVisible.value = false
    skillQuery.value = ''
  }
}

function onSelectSkill(name: string) {
  const el = editableRef.value
  // 删除输入框里正在输入的 /query 片段（无论从补全还是按钮触发），只留 chip
  if (el) {
    const sel = window.getSelection()
    let removed = false
    if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
      const node = sel.anchorNode
      if (node && node.nodeType === Node.TEXT_NODE) {
        const tn = node as Text
        const caretPos = sel.anchorOffset
        const c = tn.textContent || ''
        const hi = c.slice(0, caretPos).lastIndexOf('/')
        if (hi >= 0) {
          const delRange = document.createRange()
          delRange.setStart(tn, hi)
          delRange.setEnd(tn, caretPos)
          delRange.deleteContents()
          sel.removeAllRanges()
          sel.addRange(delRange)
          removed = true
        }
      }
    }
    // 兜底：若光标不在输入框（如按钮触发），按文本删掉末尾的 /query
    if (!removed) {
      const text = getEditableText()
      const idx = findLastSkillSlash(text)
      if (idx >= 0) {
        el.textContent = text.slice(0, idx) + text.slice(idx).replace(/^\/\S*/, '')
      }
    }
  }
  // 移除已有的 skill tag（只允许一个），再在光标处插入新的
  if (el) {
    el.querySelectorAll('.skill-tag').forEach(n => n.remove())
    const tagSpan = createSkillTagSpan(name)
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
      const range = sel.getRangeAt(0)
      range.collapse(false)
      range.insertNode(tagSpan)
      const trailing = document.createTextNode(' ')
      tagSpan.after(trailing)
      range.setStart(trailing, 1)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
    } else {
      // 光标不在输入框（按钮触发）：插到开头
      el.insertBefore(tagSpan, el.firstChild)
      el.insertBefore(document.createTextNode(' '), tagSpan.nextSibling)
    }
  }
  skillDropdownVisible.value = false
  skillQuery.value = ''
  syncInputText()
}

// 占位符替换：先 $1..$9 按空格分词逐个替换，再处理 $ARGUMENTS；无占位符时把参数追加到末尾。
function applyArguments(body: string, args: string): string {
  let out = body
  const words = args.trim() === '' ? [] : args.trim().split(/\s+/)
  for (let i = 1; i <= 9; i++) {
    out = out.split(`$${i}`).join(words[i - 1] ?? '')
  }
  if (out.includes('$ARGUMENTS')) {
    out = out.split('$ARGUMENTS').join(args)
  } else if (args.trim() !== '') {
    out = out.trimEnd() + '\n\n' + args
  }
  return out
}

function onSelectCommand(name: string) {
  const el = editableRef.value
  // 删除输入框里正在输入的 /query 片段（无论从补全还是按钮触发），只留 chip
  if (el) {
    const sel = window.getSelection()
    let removed = false
    if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
      const node = sel.anchorNode
      if (node && node.nodeType === Node.TEXT_NODE) {
        const tn = node as Text
        const caretPos = sel.anchorOffset
        const c = tn.textContent || ''
        const hi = c.slice(0, caretPos).lastIndexOf('/')
        if (hi >= 0) {
          const delRange = document.createRange()
          delRange.setStart(tn, hi)
          delRange.setEnd(tn, caretPos)
          delRange.deleteContents()
          sel.removeAllRanges()
          sel.addRange(delRange)
          removed = true
        }
      }
    }
    // 兜底：若光标不在输入框（如按钮触发），按文本删掉末尾的 /query
    if (!removed) {
      const text = getEditableText()
      const idx = findLastSkillSlash(text)
      if (idx >= 0) {
        el.textContent = text.slice(0, idx) + text.slice(idx).replace(/^\/\S*/, '')
      }
    }
  }
  // 移除已有的 command tag（只允许一个），再在光标处插入新的
  if (el) {
    el.querySelectorAll('.command-tag').forEach(n => n.remove())
    const tagSpan = createCommandTagSpan(name)
    const sel = window.getSelection()
    if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
      const range = sel.getRangeAt(0)
      range.collapse(false)
      range.insertNode(tagSpan)
      const trailing = document.createTextNode(' ')
      tagSpan.after(trailing)
      range.setStart(trailing, 1)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
    } else {
      // 光标不在输入框（按钮触发）：插到开头
      el.insertBefore(tagSpan, el.firstChild)
      el.insertBefore(document.createTextNode(' '), tagSpan.nextSibling)
    }
  }
  skillDropdownVisible.value = false
  skillQuery.value = ''
  syncInputText()
}

// `/` 下拉选中：skill/command 都走插 tag（正文后台组装，不在输入框展开）。
function onSelectItem(item: SlashItem) {
  if (item.kind === 'skill') {
    onSelectSkill(item.name)
    return
  }
  onSelectCommand(item.name)
}

// Detect an active #query at the caret. Works on the DOM text node the caret
// sits in, so an adjacent hash-tag span never interferes with the check.
function detectHashQuery(): string | null {
  const sel = window.getSelection()
  const el = editableRef.value
  if (!sel || !sel.rangeCount || !el) return null
  const node = sel.anchorNode
  if (!node || node.nodeType !== Node.TEXT_NODE || !el.contains(node)) return null
  const caret = sel.anchorOffset
  const before = (node.textContent || '').slice(0, caret)
  // Find last # in this text node before the caret
  const hashIdx = before.lastIndexOf('#')
  if (hashIdx < 0) return null
  const query = before.slice(hashIdx + 1)
  // query must not contain whitespace
  if (/\s/.test(query)) return null
  // char before # (within this node) must be empty or a separator
  if (hashIdx > 0 && !/[\s,;:.(\{\[]/.test(before[hashIdx - 1])) return null
  return query
}

function refreshHashDropdown() {
  const query = detectHashQuery()
  if (query !== null) {
    hashDropdownVisible.value = true
    hashQuery.value = query
    hashHighlightIndex.value = 0
  } else {
    hashDropdownVisible.value = false
    hashQuery.value = ''
  }
}

function onSelectHashPanel(panelTitle: string) {
  const el = editableRef.value
  if (!el) return

  const text = getEditableText()
  const lastHashIdx = -1

  if (lastHashIdx >= 0) {
    // Text-triggered: replace #query with tag span
    const before = text.slice(0, lastHashIdx)
    const after = text.slice(lastHashIdx + 1)
    const spaceIdx = after.indexOf(' ')
    const rest = spaceIdx >= 0 ? after.slice(spaceIdx) : ' '

    const tagSpan = createHashTagSpan(panelTitle)

    // Rebuild content
    el.innerHTML = ''
    if (before) el.appendChild(document.createTextNode(before))
    el.appendChild(tagSpan)
    if (rest) el.appendChild(document.createTextNode(rest))
    // Place cursor after tag, delay to let DOM settle
    nextTick(() => {
      const sel2 = window.getSelection()
      if (sel2) {
        const range = document.createRange()
        range.setStartAfter(tagSpan)
        range.collapse(true)
        sel2.removeAllRanges()
        sel2.addRange(range)
      }
    })
  } else {
    // Button-triggered: append tag span at cursor position
    const sel = window.getSelection()
    // Remove the typed #query first (caret text node), then insert the tag
    if (sel && sel.rangeCount > 0 && sel.anchorNode && sel.anchorNode.nodeType === Node.TEXT_NODE && el.contains(sel.anchorNode)) {
      const tn = sel.anchorNode as Text
      const caretPos = sel.anchorOffset
      const c = tn.textContent || ''
      const hi = c.slice(0, caretPos).lastIndexOf('#')
      if (hi >= 0) {
        const delRange = document.createRange()
        delRange.setStart(tn, hi)
        delRange.setEnd(tn, caretPos)
        delRange.deleteContents()
        sel.removeAllRanges()
        sel.addRange(delRange)
      }
    }
    if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
      const range = sel.getRangeAt(0)
      range.collapse(false) // collapse to end

      const tagSpan = createHashTagSpan(panelTitle)

      range.insertNode(tagSpan)
      const trailingBtn = document.createTextNode(' ')
      tagSpan.after(trailingBtn)
      range.setStart(trailingBtn, 0)
      range.collapse(true)
      sel.removeAllRanges()
      sel.addRange(range)
    } else {
      // Fallback: append at end
      const tagSpan = createHashTagSpan(panelTitle)
      el.appendChild(tagSpan)
      el.appendChild(document.createTextNode(' '))
    }
  }

  syncInputText(); refreshHashDropdown()
  hashDropdownVisible.value = false
  hashQuery.value = ''
  hashHighlightIndex.value = 0

  // Auto-add to locked panels
  const panel = availableTerminalPanels.value.find(p => p.title === panelTitle)
  if (panel && !tabStore.isPanelAILocked(panel.id)) {
    tabStore.addAILockedPanel(panel.id)
  }
}

function onHashButtonClick() {
  const el = editableRef.value
  if (!el) return
  el.focus()

  const sel = window.getSelection()
  if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
    const range = sel.getRangeAt(0)
    range.deleteContents()
    const textNode = document.createTextNode('#')
    range.insertNode(textNode)
    range.setStart(textNode, 1)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
  } else {
    const textNode = document.createTextNode('#')
    el.appendChild(textNode)
    const range = document.createRange()
    range.setStart(textNode, 1)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
  }
  syncInputText(); refreshHashDropdown()
}

function onSlashButtonClick() {
  const el = editableRef.value
  if (!el) return
  el.focus()

  const sel = window.getSelection()
  if (sel && sel.rangeCount > 0 && el.contains(sel.anchorNode)) {
    const range = sel.getRangeAt(0)
    range.deleteContents()
    const textNode = document.createTextNode('/')
    range.insertNode(textNode)
    range.setStart(textNode, 1)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
  } else {
    const textNode = document.createTextNode('/')
    el.appendChild(textNode)
    const range = document.createRange()
    range.setStart(textNode, 1)
    range.collapse(true)
    sel.removeAllRanges()
    sel.addRange(range)
  }
  syncInputText(); refreshSkillDropdown()
}

function onEscHashDropdown() {
  hashDropdownVisible.value = false
  hashQuery.value = ''
}

function onModeChange(mode: string) {
  aiStore.mode = mode as ExecutionMode
}

const emit = defineEmits<{
  'open-settings': []
}>()

function onModelChange(modelId: string) {
  if (modelId === '__add_model__') {
    emit('open-settings')
    nextTick(() => {
      settingsStore.openCategory = 'ai'
    })
    return
  }
  settingsStore.setActiveModel(modelId)
}

function formatRelativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return t('ai.justNow')
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t('ai.minutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('ai.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  if (days < 30) return t('ai.daysAgo', { n: days })
  const months = Math.floor(days / 30)
  if (months < 12) return t('ai.monthsAgo', { n: months })
  const years = Math.floor(months / 12)
  return t('ai.yearsAgo', { n: years })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      isAtBottom.value = true
    }
  })
}

function onMessagesScroll() {
  if (!messagesRef.value) return
  const el = messagesRef.value
  isAtBottom.value = el.scrollTop + el.clientHeight >= el.scrollHeight - 30
}

function autoScrollToBottom() {
  if (isAtBottom.value && messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function closeMenus() {
  aiMenuVisible.value = false
  sessionMenuVisible.value = false
  msgCtxMenuVisible.value = false
  addTagMenuVisible.value = false
  modelMenuVisible.value = false
  modeMenuVisible.value = false
}

function onAIContextMenu(e: MouseEvent) {
  e.preventDefault()
  captureAISelection()
  // Position at the pointer; Menu.openAt is viewport-clamped + single-open.
  aiMenuRef.value?.openAt(e.clientX, e.clientY)
}

function aiCopySelection() {
  if (aiSelectionText.value) void writeClipboard(aiSelectionText.value)
  aiMenuVisible.value = false
  msgCtxMenuVisible.value = false
}

function aiAskSelection() {
  if (aiSelectionText.value) {
    const el = editableRef.value
    if (el) el.textContent = aiSelectionText.value
    syncInputText(); refreshHashDropdown()
    if (!aiStore.visible) {
      aiStore.visible = true
    }
  }
  aiMenuVisible.value = false
  msgCtxMenuVisible.value = false
}

function onNewSession() {
  aiStore.createSession()
}

function onSessionCommand(sessionId: string) {
  aiStore.switchSession(sessionId)
}

watch(() => aiStore.currentSessionId, () => {
  isAtBottom.value = true
  scrollToBottom()
})

watch(() => aiStore.visible, (visible) => {
  if (visible) {
    nextTick(() => editableRef.value?.focus())
  }
  if (!visible && isMaximized.value) {
    isMaximized.value = false
    sidebarWidth.value = preMaxWidth.value
    window.dispatchEvent(new CustomEvent('rdp:overlay-pop'))
  }
})

function onKeydown(e: KeyboardEvent) {
  // Hash dropdown navigation
  if (hashDropdownVisible.value) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onEscHashDropdown()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      hashHighlightIndex.value = Math.min(hashHighlightIndex.value + 1, hashMatchingPanels.value.length - 1)
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      hashHighlightIndex.value = Math.max(hashHighlightIndex.value - 1, 0)
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      if (hashMatchingPanels.value.length > 0) {
        onSelectHashPanel(hashMatchingPanels.value[hashHighlightIndex.value].title)
      }
      return
    }
  }

  // Skill dropdown navigation
  if (skillDropdownVisible.value) {
    if (e.key === 'Escape') {
      e.preventDefault()
      skillDropdownVisible.value = false
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      skillHighlightIndex.value = Math.min(skillHighlightIndex.value + 1, skillMatchingItems.value.length - 1)
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      skillHighlightIndex.value = Math.max(skillHighlightIndex.value - 1, 0)
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      if (skillMatchingItems.value.length > 0) {
        onSelectItem(skillMatchingItems.value[skillHighlightIndex.value])
      }
      return
    }
  }

  // Cmd/Ctrl+V: paste via Wails clipboard (DOM paste unreliable in WKWebView)
  if ((e.metaKey || e.ctrlKey) && !e.shiftKey && !e.altKey && (e.key === 'v' || e.key === 'V')) {
    e.preventDefault()
    Clipboard.Text().then(text => { if (text) insertTextAtCursor(text) }).catch(() => {})
    return
  }

  // Normal Enter to send
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

function onPaste(e: ClipboardEvent) {
  e.preventDefault()
  Clipboard.Text().then(text => { if (text) insertTextAtCursor(text) }).catch(() => {})
}

function insertTextAtCursor(text: string) {
  const el = editableRef.value
  if (!el) return
  el.focus()
  const sel = window.getSelection()
  if (sel && sel.rangeCount > 0) {
    const range = sel.getRangeAt(0)
    range.deleteContents()
    range.insertNode(document.createTextNode(text))
    range.collapse(false)
    sel.removeAllRanges()
    sel.addRange(range)
  } else {
    el.textContent += text
  }
  syncInputText()
  refreshHashDropdown()
}

function clearInput() {
  const el = editableRef.value
  if (el) el.innerHTML = ''
  syncInputText(); refreshHashDropdown()
}

async function onSend() {
  const text = getEditableText().trim()

  // F6: command tag —— 取 tag 后参数,后台组装正文作为 user 消息
  const cmd = extractCommandFromInput()
  // F5: 显式调用 skill —— 输入框里挂了 skill tag 则注入其 L2 正文
  const skillName = extractSkillFromInput()
  if (!text && !skillName && !cmd) return
  let skillBody = ''
  if (skillName) {
    try {
      skillBody = await skillStore.getBody(skillName)
    } catch (e) {
      console.error('Failed to get skill body:', e)
    }
  }

  let final = text
  if (cmd) {
    let body = ''
    try {
      body = await commandStore.getBody(cmd.name)
    } catch (e) {
      console.error('Failed to get command body:', e)
    }
    final = body ? applyArguments(body, cmd.args) : cmd.args
  }

  // 正文拉取失败时不要静默跑空 user turn，直接提示并终止
  if (cmd && !final.trim()) {
    ElMessage.error(t('ai.commandLoadFailed', { name: cmd.name }))
    return
  }
  if (!cmd && skillName && !text && !skillBody) {
    ElMessage.error(t('ai.skillLoadFailed', { name: skillName }))
    return
  }

  if (busy.value) {
    if (cmd) aiStore.addCommandCard(cmd.name, cmd.args)
    aiStore.enqueueMessage(cmd ? '' : final, skillName || undefined, skillBody || undefined, cmd ? final : undefined)
    clearInput()
    return
  }
  clearInput()
  scrollToBottom()
  if (cmd) aiStore.addCommandCard(cmd.name, cmd.args)
  await runAgent(cmd ? '' : final, skillName, skillBody, cmd ? final : undefined)
  scrollToBottom()
}

function onStop() {
  if (aiStore.pendingCommand) {
    const cmd = aiStore.pendingCommand
    aiStore.clearPendingCommand()
    aiStore.addMessage({
      id: `msg-${Date.now()}`,
      role: 'tool',
      content: 'User cancelled this command.',
      tool_call_id: cmd.toolId
    })
    aiStore.clearQueue()
    return
  }
  if (aiStore.pendingQuestion) {
    dismissQuestion()
    aiStore.clearQueue()
    return
  }
  CancelChatStream().catch(() => { /* ignore */ })
  aiStore.stop()
}

async function onApprove(messageId: string) {
  await approveTool(messageId)
  scrollToBottom()
}

function onReject(messageId: string) {
  rejectTool(messageId)
  scrollToBottom()
}

function onAnswer(selectedLabels: string[], customText?: string) {
  answerQuestion(selectedLabels, customText)
  scrollToBottom()
}

function onDismiss() {
  dismissQuestion()
  scrollToBottom()
}

async function onContinue() {
  await continueAgent()
  scrollToBottom()
}

function onResizeStart(e: MouseEvent) {
  isResizing.value = true
  const el = sidebarEl.value
  if (!el) return
  const startX = e.clientX
  const startWidth = el.offsetWidth

  window.dispatchEvent(new CustomEvent('split:resize-start'))

  function onMouseMove(ev: MouseEvent) {
    if (!isResizing.value) return
    const delta = startX - ev.clientX
    const newWidth = Math.min(Math.max(startWidth + delta, 300), 800)
    if (el) el.style.width = newWidth + 'px'
  }

  function onMouseUp() {
    isResizing.value = false
    sidebarWidth.value = el.offsetWidth
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    window.dispatchEvent(new CustomEvent('split:resize-end'))
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

function onAskAI(e: Event) {
  const text = (e as CustomEvent).detail as string
  if (text) {
    const el = editableRef.value
    if (el) el.textContent = text
    syncInputText(); refreshHashDropdown()
    if (!aiStore.visible) {
      aiStore.visible = true
    }
  }
}

onMounted(() => {
  window.addEventListener('ai:ask', onAskAI)
  skillStore.load()
  commandStore.load()

  if (messagesRef.value) {
    messagesRef.value.addEventListener('scroll', onMessagesScroll)
    messagesObserver = new MutationObserver(() => {
      if (isAtBottom.value) {
        autoScrollToBottom()
      }
    })
    messagesObserver.observe(messagesRef.value, { childList: true, subtree: true })
  }
  scrollToBottom()
})

onUnmounted(() => {
  window.removeEventListener('ai:ask', onAskAI)

  if (messagesRef.value) {
    messagesRef.value.removeEventListener('scroll', onMessagesScroll)
  }
  editableObserver?.disconnect()
  messagesObserver?.disconnect()
})

defineExpose({ focusInput })
</script>

<style scoped>
.ai-sidebar {
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  position: relative;
  flex-shrink: 0;
}
.ai-sidebar.collapsed {
  width: 0 !important;
  overflow: hidden;
}
.ai-sidebar.maximized {
  position: absolute !important;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100% !important;
  z-index: 100;
}
.ai-sidebar.resizing {
  transition: none;
}
.resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0.375rem;
  cursor: col-resize;
  z-index: 10;
  background: transparent;
  transition: background 0.15s ease;
}

.resize-handle::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 1px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    var(--accent-subtle) 20%,
    var(--accent-glow) 50%,
    var(--accent-subtle) 80%,
    transparent 100%
  );
  transition: opacity 0.15s;
}

.resize-handle:hover::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 0.1875rem;
  background: var(--accent);
  box-shadow: 0 0 0.375rem var(--accent-glow);
}

.resize-handle:hover::before {
  opacity: 0;
}
.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-family: var(--font-ui);
  font-weight: 600;
  color: var(--text-primary);
}
.ai-actions {
  display: flex;
  gap: 0.125rem;
}
.ai-action-btn {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.625rem;
  height: 1.625rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.12s ease;
}
.ai-action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.ai-session-bar {
  padding: 0.375rem 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.session-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 1.75rem;
  padding: 0 0.625rem;
  box-sizing: border-box;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.75rem;
  font-family: var(--font-ui);
  color: var(--text-primary);
  box-shadow: inset 0 0 0 1px var(--border-subtle);
  transition: all 0.12s ease;
}
.session-trigger:hover {
  background: var(--bg-hover);
  box-shadow: inset 0 0 0 1px var(--border-hover);
}
.session-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-time {
  margin-left: 0.5rem;
  font-size: 0.625rem;
  font-family: var(--font-mono);
  color: var(--text-muted);
  white-space: nowrap;
}
.session-delete {
  margin-left: 0.5rem;
  color: var(--text-muted);
}
.session-delete:hover {
  color: var(--text-primary);
}
/* Row layout + hover reveal for the #trailing zone now live in MenuItem.vue
   (.menu-item.has-trailing / .menu-trailing). */
.ai-search-bar {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.625rem;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
}
.ai-search-bar .search-input {
  flex: 1;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.5rem;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  outline: none;
}
.ai-search-bar .search-input:focus {
  border-color: var(--accent);
}
.ai-search-bar .search-count {
  font-size: 0.6875rem;
  color: var(--text-muted);
  white-space: nowrap;
}
.ai-search-bar .search-btn {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.125rem;
}
.ai-search-bar .search-btn:hover {
  color: var(--text-primary);
}
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
  user-select: text;
  -webkit-user-select: text;
}
.ai-thinking {
  display: flex;
  align-items: center;
  padding: 0.625rem 0.875rem;
}
.thinking-text {
  font-size: 0.6875rem;
  font-family: var(--font-ui);
  color: var(--text-muted);
  font-style: italic;
  animation: status-pulse 1.2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.ai-input {
  padding: 0.625rem 1rem;
  flex-shrink: 0;
  position: relative;
}
.input-container {
  border: 1px solid var(--border-subtle);
  border-top-color: transparent;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  background: var(--bg-elevated);
  transition: border-color 0.15s ease;
  position: relative;
}
.input-container:focus-within {
  border-color: var(--accent);
  border-top-color: var(--accent);
}
.textarea-wrap {
  position: relative;
}
.ai-editable {
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-family: var(--font-ui);
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
  min-height: 3.75rem;
  max-height: 13.75rem;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  /* WebKit/WKWebView (macOS): body sets -webkit-user-select: none, which makes
     a contenteditable div impossible to focus/position the caret with the
     mouse — clicks land but no cursor appears and no typing happens. Native
     <input>/<textarea> are exempt via the UA stylesheet, but contenteditable
     is not, so restore text selection explicitly here. */
  user-select: text;
  -webkit-user-select: text;
  cursor: text;
}
.ai-editable:empty::before {
  content: attr(data-placeholder);
  color: var(--text-muted);
  pointer-events: none;
}
.hash-tag {
  display: inline;
  background: var(--accent);
  color: var(--on-accent);
  border-radius: 0.1875rem;
  padding: 1px 0.3125rem;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
  user-select: none;
  margin: 0 0.125rem;
}
.input-actions {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
  padding: 0 0.5rem 0.5rem 0.5rem;
}
.input-actions-left {
  display: flex;
  gap: 0.125rem;
  align-items: center;
}
.input-actions-right {
  display: flex;
  gap: 0.375rem;
  align-items: center;
}
/* Ghost buttons: no border/background by default, reveal on hover */
.ghost-btn {
  display: inline-block;
  box-sizing: border-box;
  height: 1.5rem;
  line-height: 1.5rem;
  padding: 0 0.375rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition: background 0.12s ease, color 0.12s ease;
}
.ghost-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.model-btn {
  max-width: 6rem;
}
.add-model-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  max-width: none;
}
.mode-btn {
  max-width: 6.75rem;
}
/* Send / Stop icon button */
.send-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.875rem;
  height: 1.875rem;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: var(--on-accent);
  cursor: pointer;
  transition: background 0.12s ease, opacity 0.12s ease;
}
.send-btn:hover:not(:disabled) {
  background: var(--accent);
}
.send-btn:disabled {
  background: var(--bg-active);
  color: var(--text-disabled);
  cursor: not-allowed;
}
.send-btn.stop {
  background: var(--error);
  color: var(--on-accent);
}
.send-btn.stop:hover {
  background: var(--error);
  opacity: 0.85;
}
.mode-option {
  font-size: 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
}
.mode-auto {
  color: var(--error);
}
.mode-confirm {
  color: var(--success);
}
.mode-write {
  color: var(--accent);
}
.mode-warning {
  color: var(--warning);
}

.ai-panel-tags {
  padding: 0.25rem 0.75rem;
  background: var(--bg-overlay);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.panel-tags-list {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
  min-height: 1.375rem;
}
.panel-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.1875rem;
  padding: 1px 0.375rem;
  font-size: 0.6875rem;
  background: var(--accent-subtle);
  color: var(--accent);
  border: 1px solid var(--accent-glow);
  border-radius: var(--radius-sm);
  line-height: 1.5;
}
.panel-tag-default {
  background: var(--bg-overlay);
  color: var(--text-muted);
  border-color: var(--border-subtle);
}
.panel-tag-skill-icon {
  flex-shrink: 0;
}
.panel-tag-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 0.8125rem;
  line-height: 1;
  color: var(--text-muted);
  transition: color 0.15s;
}
.panel-tag-close:hover {
  color: var(--text-primary);
}
.panel-tag-add-btn {
  background: none;
  border: 1px dashed var(--border-hover);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  width: 1.25rem;
  height: 1.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  line-height: 1;
  padding: 0;
  transition: border-color 0.15s, color 0.15s;
}
.panel-tag-add-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.no-terminal-hint {
  font-size: 0.6875rem;
  color: var(--text-muted);
}
.panel-shell-hint {
  margin-left: 0.5rem;
  font-size: 0.625rem;
  color: var(--text-muted);
}
.hash-dropdown {
  position: absolute;
  bottom: 100%;
  left: -1px;
  right: -1px;
  max-height: 11.25rem;
  overflow-y: auto;
  background: var(--bg-surface);
  border: 1px solid var(--accent-glow);
  border-radius: var(--radius-sm);
  box-shadow: 0 -0.25rem 0.75rem rgba(0, 0, 0, 0.4);
  z-index: 100;
  margin-bottom: 0.25rem;
}
.hash-dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.375rem 0.625rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background 0.1s;
}
.hash-dropdown-item:hover,
.hash-dropdown-item.highlighted {
  background: var(--accent-subtle);
}
.hash-panel-name {
  color: var(--accent);
  font-weight: 500;
}
.hash-panel-hint {
  font-size: 0.625rem;
  color: var(--text-muted);
  margin-left: auto;
}
.hash-associated-badge {
  font-size: 0.5625rem;
  color: var(--accent);
  background: var(--accent-subtle);
  padding: 0 0.25rem;
  border-radius: 0.125rem;
  margin-left: 0.25rem;
  flex-shrink: 0;
}
.hash-btn-icon {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 600;
}

/* Skill dropdown (紧凑单行，仿 TRAE) */
.skill-dropdown {
  position: absolute;
  bottom: 100%;
  left: -1px;
  right: -1px;
  max-height: 13.75rem;
  overflow-y: auto;
  background: var(--bg-surface);
  border: 1px solid var(--accent-glow);
  border-radius: var(--radius-sm);
  box-shadow: 0 -0.25rem 0.75rem rgba(0, 0, 0, 0.4);
  z-index: 100;
  margin-bottom: 0.25rem;
}
.skill-dropdown-item {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background 0.1s;
}
.skill-dropdown-item:hover,
.skill-dropdown-item.highlighted {
  background: var(--accent-subtle);
}
.skill-dropdown-name {
  color: var(--accent);
  font-weight: 500;
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.skill-dropdown-kind-icon {
  color: var(--text-muted);
  flex-shrink: 0;
  align-self: center;
}
.skill-dropdown-args {
  color: var(--text-muted);
  font-size: 0.6875rem;
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.skill-dropdown-desc {
  flex: 1;
  min-width: 0;
  color: var(--text-muted);
  font-size: 0.6875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* Skill chip */
.queued-area {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem 0.5rem 0 0.5rem;
}
.queued-chip {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-family: var(--font-ui);
  color: var(--text-secondary);
}
.queued-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.queued-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
}
.queued-remove:hover {
  color: var(--text-primary);
}
</style>
