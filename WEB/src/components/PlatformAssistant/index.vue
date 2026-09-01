<template>
  <Teleport to="body">
    <button v-if="!open" class="assistant-fab" type="button" title="打开 EasyAIoT 智能助手" @click="openAssistant">
      <span class="assistant-fab__halo" />
      <RobotOutlined />
    </button>

    <Transition name="assistant-panel">
      <section
        v-if="open"
        class="assistant-panel"
        :class="{ expanded, 'theme-dark': isDark }"
        :style="panelStyle"
        aria-label="EasyAIoT 平台智能助手"
      >
        <!-- 头部 -->
        <header class="assistant-header">
          <div class="assistant-brand">
            <span class="assistant-logo"><RobotOutlined /></span>
            <div class="assistant-brand__text">
              <strong>EasyAIoT 智能助手</strong>
              <span class="assistant-model"><i :class="{ online: !!activeModel }" />{{ activeModel ? `由 ${activeModel.model_name} 提供能力` : '尚未启用大模型' }}</span>
            </div>
          </div>
          <div class="assistant-actions">
            <button type="button" title="新对话" @click="newChat"><PlusOutlined /></button>
            <button type="button" :title="expanded ? '还原窗口' : '全屏展开'" @click="expanded = !expanded"><ExpandOutlined /></button>
            <button type="button" title="关闭" @click="open = false"><CloseOutlined /></button>
          </div>
        </header>
        <div class="assistant-header__accent" />

        <!-- 消息区 -->
        <div ref="messageList" class="assistant-messages" @scroll="onScroll" @click="onMessagesClick">
          <div v-if="!messages.length" class="assistant-welcome">
            <div class="assistant-welcome__hero">
              <span class="assistant-welcome__icon"><RobotOutlined /></span>
            </div>
            <h3 class="assistant-welcome__title">你好，我是<span> EasyAIoT 智能助手</span></h3>
            <p>我知道你正位于「{{ pageTitle }}」，可以帮你理解功能、排查问题并给出下一步操作。</p>
            <div class="quick-grid">
              <button v-for="item in quickQuestions" :key="item.text" type="button" @click="send(item.text)">
                <span class="quick-grid__icon"><component :is="item.icon" /></span>
                <span class="quick-grid__text">{{ item.text }}</span>
                <ArrowRightOutlined class="quick-grid__arrow" />
              </button>
            </div>
            <div class="assistant-tags">
              <span v-for="tag in abilityTags" :key="tag.text"><component :is="tag.icon" />{{ tag.text }}</span>
            </div>
          </div>

          <template v-for="(message, index) in messages" :key="index">
            <div class="message" :class="message.role">
              <div v-if="message.role === 'assistant'" class="message-meta">
                <span class="message-avatar"><RobotOutlined /></span>
                <span class="message-name">平台助手</span>
                <span v-if="message.ts" class="message-time">{{ formatTime(message.ts) }}</span>
              </div>
              <div class="message-body" :class="message.role">
                <div class="message-bubble">
                  <div v-if="isStreamingIndex(index) && !message.content" class="message-thinking"><span /><span /><span /></div>
                  <div v-else-if="isStreamingIndex(index)" class="message-streaming" :class="{ 'is-plain': !mdStreamable(message.content) }" v-html="renderStream(message.content)" />
                  <div v-else class="md-rendered" v-html="renderMarkdown(message.content)" />
                </div>
                <div v-if="message.role === 'assistant'" class="message-actions">
                  <button type="button" class="message-action" @click="copyMessage(message, index)">
                    <CheckOutlined v-if="copiedIndex === index" /><CopyOutlined v-else />{{ copiedIndex === index ? '已复制' : '复制' }}
                  </button>
                  <button v-if="index === messages.length - 1 && !loading" type="button" class="message-action" @click="regenerate"><RedoOutlined />重新生成</button>
                </div>
                <div v-if="index === messages.length - 1 && message.role === 'assistant' && !loading && suggestions.length" class="message-suggestions">
                  <span v-for="s in suggestions" :key="s" role="button" tabindex="0" @click="send(s)">{{ s }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- 未启用模型警示 -->
        <div v-if="!activeModel" class="assistant-warning">
          <WarningOutlined /><span>请先在「大模型管理」中配置并启用一个模型</span>
          <button type="button" @click="goModelManage">去配置</button>
        </div>

        <!-- 输入区 -->
        <footer class="assistant-composer">
          <div class="context-chip"><EnvironmentOutlined /> 当前页面：{{ pageTitle }}</div>
          <div class="composer-box">
            <textarea
              ref="composerEl"
              v-model="draft"
              :disabled="!activeModel || loading"
              rows="1"
              maxlength="4000"
              placeholder="询问平台功能、配置方法或故障排查…"
              @input="autoResize"
              @keydown.enter.exact.prevent="onEnterKey"
            />
            <button v-if="loading" class="send send--stop" type="button" title="停止生成" @click="stop">
              <StopOutlined />
            </button>
            <button v-else class="send" type="button" :disabled="!canSend" title="发送" @click="send()">
              <ArrowUpOutlined />
            </button>
          </div>
          <small>Enter 发送 · Shift + Enter 换行 · 回答由大模型生成，请核对关键操作</small>
        </footer>

        <!-- 拖拽调整大小 -->
        <span class="assistant-resize" title="拖动调整大小" @mousedown.prevent="onResizeStart" />
      </section>
    </Transition>
  </Teleport>
</template>

<script lang="ts" setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRightOutlined, ArrowUpOutlined, BulbOutlined, CheckOutlined, CloseOutlined, CodeOutlined,
  CopyOutlined, EnvironmentOutlined, ExpandOutlined, MessageOutlined, PlusOutlined, RedoOutlined,
  RobotOutlined, RocketOutlined, SafetyCertificateOutlined, StopOutlined, ThunderboltOutlined,
  ToolOutlined, WarningOutlined,
} from '@ant-design/icons-vue'
import { getLLMList, type LLMChatMessage, type LLMModel } from '@/api/device/llm'
import { getAccessToken } from '@/utils/auth'
import { useRootSetting } from '@/hooks/setting/useRootSetting'
import { escapeHtml, isUnbalancedFence, renderMarkdown } from './utils/markdown'

defineOptions({ name: 'PlatformAssistant' })

/** 与旧版存储 key 保持一致，可读入已保存的历史消息 */
const STORAGE_KEY = 'easyaiot.platform-assistant.messages.v1'
const SIZE_KEY = 'easyaiot.platform-assistant.size.v1'
const CHAT_URL = `${import.meta.env.VITE_GLOB_API_URL || ''}${import.meta.env.VITE_GLOB_API_URL_PREFIX || ''}/model/llm/chat`

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  ts?: number
}

const route = useRoute()
const router = useRouter()
const { getDarkMode } = useRootSetting()

const open = ref(false)
const expanded = ref(false)
const loading = ref(false)
const draft = ref('')
const activeModel = ref<LLMModel | null>(null)
const messages = ref<ChatMsg[]>([])
const messageList = ref<HTMLElement | null>(null)
const abortCtrl = ref<AbortController | null>(null)
const copiedIndex = ref(-1)
const showSuggestions = ref(false)
const stickToBottom = ref(true)
const composerEl = ref<HTMLTextAreaElement | null>(null)

/** 面板尺寸（可拖拽，localStorage 记忆） */
const panelW = ref(540)
const panelH = ref(720)
const isDark = computed(() => getDarkMode.value === 'dark')
const panelStyle = computed(() =>
  typeof window !== 'undefined' && window.innerWidth <= 600 ? {} : { width: `${panelW.value}px`, height: `${panelH.value}px` },
)
const pageTitle = computed(() => String(route.meta?.title || route.name || '当前页面'))
const canSend = computed(() => !!activeModel.value && !loading.value && !!draft.value.trim())
const quickQuestions = computed(() => [
  { icon: BulbOutlined, text: `介绍一下「${pageTitle.value}」页面能做什么` },
  { icon: ThunderboltOutlined, text: '我应该从哪里开始配置设备？' },
  { icon: ToolOutlined, text: '帮我梳理一次常见故障排查步骤' },
  { icon: RocketOutlined, text: '当前启用的大模型如何被平台调用？' },
])
const abilityTags = [
  { icon: MessageOutlined, text: '实时问答' },
  { icon: CodeOutlined, text: '代码示例' },
  { icon: ToolOutlined, text: '故障排查' },
  { icon: SafetyCertificateOutlined, text: '安全建议' },
]
const suggestions = computed(() => {
  if (!showSuggestions.value) return []
  return [
    '能给我一份可操作的分步清单吗？',
    '回答里有哪些常见误区需要注意？',
    `结合「${pageTitle.value}」页面，我现在应该先做什么？`,
  ]
})

const isStreamingIndex = (index: number) =>
  loading.value && index === messages.value.length - 1 && messages.value[index]?.role === 'assistant'

/** 流式中：代码围栏未闭合时退化为纯文本，避免整段被当作代码块 */
const mdStreamable = (content: string) => !isUnbalancedFence(content)
const renderStream = (content: string) => (mdStreamable(content) ? renderMarkdown(content) : escapeHtml(content))

// ---------- 持久化 ----------

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value.slice(-30)))
  } catch { /* ignore */ }
}

function restore() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    if (Array.isArray(value)) {
      messages.value = value
        .filter((item) => ['user', 'assistant'].includes(item?.role) && typeof item?.content === 'string')
        .slice(-30)
        .map((item) => ({ role: item.role, content: item.content, ts: typeof item.ts === 'number' ? item.ts : undefined }))
    }
  } catch {
    messages.value = []
  }
}

function restoreSize() {
  try {
    const size = JSON.parse(localStorage.getItem(SIZE_KEY) || 'null')
    if (size && typeof size.w === 'number' && typeof size.h === 'number') {
      panelW.value = clamp(size.w, 360, 880)
      panelH.value = clamp(size.h, 480, window.innerHeight - 24)
    }
  } catch { /* ignore */ }
  panelW.value = Math.min(panelW.value, window.innerWidth - 32)
  panelH.value = Math.min(panelH.value, window.innerHeight - 60)
}

// ---------- 对话 ----------

async function loadActiveModel() {
  try {
    const result: any = await getLLMList({ page: 1, pageSize: 1, is_active: 'true' })
    const list = result?.data?.list || result?.list || []
    activeModel.value = list[0] || null
  } catch {
    activeModel.value = null
  }
}

async function openAssistant() {
  open.value = true
  stickToBottom.value = true
  await loadActiveModel()
  scrollToBottom()
}

async function send(prefill?: string) {
  const text = (prefill || draft.value).trim()
  if (!text || loading.value || !activeModel.value) return
  const history: LLMChatMessage[] = messages.value.slice(-16).map((m) => ({ role: m.role, content: m.content }))
  messages.value.push({ role: 'user', content: text, ts: Date.now() })
  messages.value.push({ role: 'assistant', content: '', ts: Date.now() })
  draft.value = ''
  if (composerEl.value) composerEl.value.style.height = 'auto'
  loading.value = true
  showSuggestions.value = false
  stickToBottom.value = true
  scrollToBottom()
  const ok = await streamChat(text, history)
  loading.value = false
  if (ok) showSuggestions.value = true
  persist()
  scrollToBottom()
}

/** SSE 流式对话：data: {"content": "..."} 分块，data: [DONE] 结束 */
async function streamChat(prompt: string, history: LLMChatMessage[]): Promise<boolean> {
  const controller = new AbortController()
  abortCtrl.value = controller
  const current = messages.value[messages.value.length - 1]
  try {
    const res = await fetch(CHAT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAccessToken() || ''}`,
      },
      body: JSON.stringify({
        prompt,
        messages: history,
        context: { pageTitle: pageTitle.value, pagePath: route.fullPath },
        stream: true,
      }),
      signal: controller.signal,
    })
    if (!res.ok || !res.body) throw new Error(`请求失败（HTTP ${res.status}）`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let full = ''
    let chunkCount = 0
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 1)
        if (!line.startsWith('data:')) continue
        const payload = line.slice(5).trim()
        if (payload === '[DONE]') return true
        try {
          const json = JSON.parse(payload)
          const delta = json?.content
          if (typeof delta === 'string' && delta) {
            full += delta
            current.content = full
            // 节流滚动，避免每块都触发
            if (++chunkCount % 3 === 1) scrollToBottom()
          }
        } catch { /* 忽略非 JSON 行 */ }
      }
    }
    if (!full) current.content = '模型未返回内容。'
    return true
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      current.content = current.content ? `${current.content}\n\n> ⏹ 已停止生成` : '⏹ 已停止生成。'
    } else {
      current.content = `请求失败：${error?.message || '请检查模型配置和网络连接。'}`
    }
    return false
  } finally {
    abortCtrl.value = null
  }
}

function stop() {
  abortCtrl.value?.abort()
}

function regenerate() {
  if (loading.value) return
  let lastUserIndex = -1
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') {
      lastUserIndex = i
      break
    }
  }
  if (lastUserIndex < 0) return
  const prompt = messages.value[lastUserIndex].content
  messages.value = messages.value.slice(0, lastUserIndex)
  persist()
  send(prompt)
}

function newChat() {
  if (loading.value) stop()
  messages.value = []
  showSuggestions.value = false
  persist()
  nextTick(scrollToBottom)
}

function goModelManage() {
  open.value = false
  router.push({ path: '/train', query: { tab: '5' } }).catch(() => {})
}

// ---------- 消息操作 ----------

async function copyMessage(message: ChatMsg, index: number) {
  try {
    await navigator.clipboard?.writeText(message.content)
    copiedIndex.value = index
    setTimeout(() => {
      if (copiedIndex.value === index) copiedIndex.value = -1
    }, 1500)
  } catch { /* ignore */ }
}

/** 代码块“复制”按钮走事件委托（按钮由 v-html 渲染，无法直接绑定） */
function onMessagesClick(e: MouseEvent) {
  const btn = (e.target as HTMLElement).closest?.('.md-code__copy')
  if (!btn) return
  const code = btn.closest('.md-code')?.querySelector('pre code')?.textContent || ''
  if (code) navigator.clipboard?.writeText(code).catch(() => {})
  const label = btn.textContent
  btn.textContent = '已复制'
  setTimeout(() => {
    if (btn.isConnected) btn.textContent = label
  }, 1200)
}

function formatTime(ts?: number) {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ---------- 输入区 ----------

function onEnterKey(e: KeyboardEvent) {
  if ((e as any).isComposing) return
  send()
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`
}

// ---------- 滚动 ----------

let rafPending = false

function scrollToBottom() {
  if (!stickToBottom.value || rafPending) return
  rafPending = true
  requestAnimationFrame(() => {
    rafPending = false
    const el = messageList.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function onScroll() {
  const el = messageList.value
  if (!el) return
  stickToBottom.value = el.scrollHeight - el.scrollTop - el.clientHeight < 90
}

// ---------- 拖拽调整大小 ----------

function clamp(v: number, min: number, max: number) {
  return Math.min(Math.max(v, min), max)
}

function onResizeStart(e: MouseEvent) {
  if (window.innerWidth <= 600) return
  expanded.value = false
  const startX = e.clientX
  const startY = e.clientY
  const startW = panelW.value
  const startH = panelH.value
  const onMove = (ev: MouseEvent) => {
    panelW.value = clamp(startW + ev.clientX - startX, 360, Math.min(880, window.innerWidth - 24))
    panelH.value = clamp(startH + ev.clientY - startY, 480, window.innerHeight - 24)
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    try {
      localStorage.setItem(SIZE_KEY, JSON.stringify({ w: panelW.value, h: panelH.value }))
    } catch { /* ignore */ }
  }
  document.body.style.cursor = 'nwse-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

onMounted(() => {
  restore()
  restoreSize()
})
onBeforeUnmount(() => {
  if (abortCtrl.value) abortCtrl.value.abort()
})
</script>

<style scoped>
/* ========== 主题变量 ========== */
.assistant-panel {
  --brand: #266cfb;
  --brand-2: #3d7bff;
  --brand-3: #1d5ce0;
  --brand-soft: #eaf1fe;
  --bg: #ffffff;
  --bg-soft: #f5f7fc;
  --bg-chat: #f8fafd;
  --bubble: #ffffff;
  --bubble-border: #e7ebf3;
  --text: #1b2337;
  --text-2: #66708a;
  --text-3: #9aa3b8;
  --border: #e7eaf2;
  --md-inline-bg: #eef1f8;
  --md-inline-text: #d6336c;
}
.assistant-panel.theme-dark {
  --brand: #4d8dff;
  --brand-2: #6ba1ff;
  --brand-3: #3d7bff;
  --brand-soft: rgba(77, 141, 255, 0.16);
  --bg: #131722;
  --bg-soft: #1a2030;
  --bg-chat: #10141d;
  --bubble: #1a2030;
  --bubble-border: #2a3245;
  --text: #e6eaf3;
  --text-2: #9aa4bd;
  --text-3: #6b7590;
  --border: #242c3e;
  --md-inline-bg: #252d40;
  --md-inline-text: #f472b6;
}

/* ========== 悬浮球 ========== */
.assistant-fab {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 1190;
  display: grid;
  place-items: center;
  width: 60px;
  height: 60px;
  border: 0;
  border-radius: 20px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb 55%, #1d5ce0);
  box-shadow: 0 12px 30px rgba(38, 108, 251, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  cursor: pointer;
  font-size: 26px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.assistant-fab:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 18px 40px rgba(38, 108, 251, 0.46), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
.assistant-fab__halo {
  position: absolute;
  inset: -6px;
  border: 1.5px solid rgba(38, 108, 251, 0.35);
  border-radius: 24px;
  pointer-events: none;
  animation: halo 2.6s ease-out infinite;
}
@keyframes halo {
  0% { transform: scale(0.92); opacity: 0.8; }
  70%, 100% { transform: scale(1.18); opacity: 0; }
}

/* ========== 面板骨架 ========== */
.assistant-panel {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1195;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 24px;
  color: var(--text);
  background: var(--bg);
  box-shadow: 0 2px 8px rgba(24, 39, 75, 0.06), 0 24px 60px rgba(24, 39, 75, 0.16), 0 60px 140px rgba(24, 39, 75, 0.12);
  transform-origin: bottom right;
}
.assistant-panel.expanded {
  width: min(880px, calc(100vw - 40px)) !important;
  height: min(880px, calc(100vh - 40px)) !important;
}
.theme-dark.assistant-panel {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), 0 24px 60px rgba(0, 0, 0, 0.5), 0 60px 140px rgba(0, 0, 0, 0.45);
}

/* ========== 头部 ========== */
.assistant-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 17px 13px;
  background: linear-gradient(180deg, var(--bg), var(--bg-soft));
  user-select: none;
}
.assistant-header__accent {
  flex: 0 0 2px;
  background: linear-gradient(90deg, transparent, var(--brand), var(--brand-2), transparent);
  opacity: 0.85;
}
.assistant-brand {
  display: flex;
  gap: 11px;
  align-items: center;
  min-width: 0;
}
.assistant-logo {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb 55%, #1d5ce0);
  box-shadow: 0 8px 18px rgba(38, 108, 251, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  font-size: 20px;
}
.assistant-brand__text {
  min-width: 0;
}
.assistant-brand__text strong {
  display: block;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.2px;
}
.assistant-model {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
  max-width: 250px;
  overflow: hidden;
  color: var(--text-2);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.assistant-model i {
  flex: 0 0 auto;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.18);
}
.assistant-model i.online {
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.18);
}
.assistant-actions {
  display: flex;
  gap: 3px;
}
.assistant-actions button {
  display: grid;
  place-items: center;
  width: 31px;
  height: 31px;
  border: 0;
  border-radius: 9px;
  color: var(--text-2);
  background: transparent;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.assistant-actions button:hover {
  color: var(--brand);
  background: var(--brand-soft);
}

/* ========== 消息区 ========== */
.assistant-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 17px 14px;
  background:
    radial-gradient(1200px 420px at 88% -60px, rgba(38, 108, 251, 0.055), transparent 60%),
    var(--bg-chat);
  scroll-behavior: smooth;
}
.assistant-messages::-webkit-scrollbar {
  width: 6px;
}
.assistant-messages::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: rgba(120, 130, 160, 0.25);
}

/* ========== 欢迎页 ========== */
.assistant-welcome {
  padding: 22px 6px 8px;
  text-align: center;
}
.assistant-welcome__hero {
  position: relative;
  display: grid;
  place-items: center;
  width: 88px;
  height: 88px;
  margin: 0 auto 15px;
}
.assistant-welcome__hero::before {
  content: '';
  position: absolute;
  inset: 6px;
  border-radius: 28px;
  background: linear-gradient(135deg, #3d7bff, #266cfb 60%, #5b8cff);
  filter: blur(16px);
  opacity: 0.4;
  animation: hero-breathe 3.2s ease-in-out infinite;
}
@keyframes hero-breathe {
  0%, 100% { transform: scale(0.94); opacity: 0.32; }
  50% { transform: scale(1.06); opacity: 0.5; }
}
.assistant-welcome__icon {
  position: relative;
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 24px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb 55%, #1d5ce0);
  box-shadow: 0 16px 32px rgba(38, 108, 251, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  font-size: 34px;
}
.assistant-welcome__title {
  margin: 0 0 9px;
  font-size: 19px;
  font-weight: 700;
}
.assistant-welcome__title span {
  background: linear-gradient(120deg, var(--brand), var(--brand-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.assistant-welcome > p {
  margin: 0 auto 20px;
  max-width: 350px;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.75;
}
.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  text-align: left;
}
.quick-grid button {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 56px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
  color: var(--text);
  background: var(--bg);
  cursor: pointer;
  font-size: 12.5px;
  line-height: 1.5;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.quick-grid button:hover {
  transform: translateY(-2px);
  border-color: rgba(38, 108, 251, 0.5);
  box-shadow: 0 8px 20px rgba(38, 108, 251, 0.12);
}
.quick-grid__icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  color: var(--brand);
  background: var(--brand-soft);
  font-size: 15px;
}
.quick-grid__text {
  flex: 1;
}
.quick-grid__arrow {
  flex: 0 0 auto;
  color: var(--text-3);
  font-size: 11px;
  transition: transform 0.18s ease, color 0.18s ease;
}
.quick-grid button:hover .quick-grid__arrow {
  transform: translateX(3px);
  color: var(--brand);
}
.assistant-tags {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}
.assistant-tags span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-3);
  font-size: 11px;
}
.assistant-tags span svg {
  font-size: 13px;
}

/* ========== 消息 ========== */
.message {
  display: flex;
  flex-direction: column;
  margin: 0 0 20px;
  animation: msg-in 0.28s ease both;
}
@keyframes msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.message.user {
  align-items: flex-end;
}
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 6px 3px;
}
.message-avatar {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: 9px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb);
  box-shadow: 0 4px 10px rgba(38, 108, 251, 0.28);
  font-size: 14px;
}
.message-name {
  font-size: 12px;
  font-weight: 600;
}
.message-time {
  color: var(--text-3);
  font-size: 10.5px;
}
.message-body {
  max-width: 88%;
}
.message-body.assistant {
  max-width: 94%;
}
.message-bubble {
  padding: 11px 14px;
  border: 1px solid var(--bubble-border);
  border-radius: 4px 16px 16px 16px;
  color: var(--text);
  background: var(--bubble);
  box-shadow: 0 1px 2px rgba(20, 30, 60, 0.04);
  font-size: 13.5px;
  line-height: 1.7;
  word-break: break-word;
}
.message.user .message-bubble {
  border: 0;
  border-radius: 16px 4px 16px 16px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb 60%, #1d5ce0);
  box-shadow: 0 6px 16px rgba(38, 108, 251, 0.28);
}
.message-streaming {
  min-height: 1.2em;
}
.message-streaming.is-plain {
  white-space: pre-wrap;
}
.message-streaming::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 14px;
  margin-left: 3px;
  border-radius: 1px;
  background: var(--brand);
  vertical-align: -2px;
  animation: caret-blink 0.9s steps(2) infinite;
}
@keyframes caret-blink {
  50% { opacity: 0; }
}
.message-thinking {
  display: flex;
  gap: 5px;
  padding: 5px 2px;
}
.message-thinking span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand);
  opacity: 0.4;
  animation: think 1.2s ease-in-out infinite;
}
.message-thinking span:nth-child(2) { animation-delay: 0.15s; }
.message-thinking span:nth-child(3) { animation-delay: 0.3s; }
@keyframes think {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 消息操作条 */
.message-actions {
  display: flex;
  gap: 2px;
  margin-top: 5px;
  padding-left: 4px;
  opacity: 0;
  transition: opacity 0.18s ease;
}
.message:hover .message-actions,
.message-actions:focus-within {
  opacity: 1;
}
.message-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 0;
  border-radius: 7px;
  color: var(--text-3);
  background: transparent;
  cursor: pointer;
  font-size: 11.5px;
  transition: color 0.15s, background 0.15s;
}
.message-action:hover {
  color: var(--brand);
  background: var(--brand-soft);
}

/* 追问建议 */
.message-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 9px;
  padding-left: 2px;
}
.message-suggestions span {
  padding: 6px 13px;
  border: 1px solid rgba(38, 108, 251, 0.35);
  border-radius: 999px;
  color: var(--brand);
  background: var(--brand-soft);
  cursor: pointer;
  font-size: 12px;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.message-suggestions span:hover {
  border-color: var(--brand);
  color: #fff;
  background: var(--brand);
}

/* ========== Markdown 渲染（v-html 内容，需要 :deep） ========== */
.message-bubble :deep(.md-p) {
  margin: 0 0 8px;
}
.message-bubble :deep(.md-p:last-child) {
  margin-bottom: 0;
}
.message-bubble :deep(.md-h) {
  margin: 10px 0 6px;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
}
.message-bubble :deep(.md-h1) { font-size: 15.5px; }
.message-bubble :deep(.md-h2) { font-size: 15px; }
.message-bubble :deep(.md-h3) { font-size: 14px; }
.message-bubble :deep(.md-h4) { font-size: 13.5px; }
.message-bubble :deep(.md-list) {
  margin: 4px 0 8px;
  padding-left: 19px;
}
.message-bubble :deep(.md-list li) {
  margin: 3px 0;
}
.message-bubble :deep(.md-code-inline) {
  padding: 1.5px 5px;
  border-radius: 5px;
  color: var(--md-inline-text);
  background: var(--md-inline-bg);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}
.message-bubble :deep(.md-code) {
  margin: 9px 0;
  overflow: hidden;
  border-radius: 12px;
  background: #0f172a;
}
.message-bubble :deep(.md-code__bar) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.06);
}
.message-bubble :deep(.md-code__lang) {
  color: #93a3c0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
}
.message-bubble :deep(.md-code__copy) {
  border: 0;
  color: #8fa0bd;
  background: transparent;
  cursor: pointer;
  font-size: 11px;
  transition: color 0.15s;
}
.message-bubble :deep(.md-code__copy:hover) {
  color: #fff;
}
.message-bubble :deep(.md-code__pre) {
  margin: 0;
  padding: 10px 13px;
  overflow-x: auto;
}
.message-bubble :deep(.md-code__pre code) {
  color: #e2e8f0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
}
.message-bubble :deep(.md-quote) {
  margin: 9px 0;
  padding: 7px 12px;
  border-left: 3px solid var(--brand);
  border-radius: 0 9px 9px 0;
  color: var(--text-2);
  background: var(--brand-soft);
  font-size: 12.5px;
}
.message-bubble :deep(.md-hr) {
  margin: 11px 0;
  border: 0;
  border-top: 1px dashed var(--border);
}
.message-bubble :deep(.md-table-wrap) {
  margin: 9px 0;
  overflow-x: auto;
}
.message-bubble :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.message-bubble :deep(.md-table th),
.message-bubble :deep(.md-table td) {
  padding: 5px 9px;
  border: 1px solid var(--border);
  text-align: left;
}
.message-bubble :deep(.md-table th) {
  background: var(--bg-soft);
}
.message-bubble :deep(a) {
  color: var(--brand);
}

/* ========== 无模型警示 ========== */
.assistant-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-top: 1px solid #f5e3ad;
  color: #92610c;
  background: linear-gradient(90deg, #fff7e0, #fff3d1);
  font-size: 12.5px;
}
.assistant-warning button {
  margin-left: auto;
  padding: 5px 13px;
  border: 0;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb);
  box-shadow: 0 4px 10px rgba(38, 108, 251, 0.3);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}
.theme-dark .assistant-warning {
  border-top-color: rgba(240, 195, 109, 0.2);
  color: #f0c36d;
  background: rgba(240, 195, 109, 0.1);
}

/* ========== 输入区 ========== */
.assistant-composer {
  padding: 12px 14px 10px;
  border-top: 1px solid var(--border);
  background: var(--bg);
}
.context-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 8px;
  padding: 4px 9px;
  border-radius: 999px;
  color: var(--text-2);
  background: var(--bg-soft);
  font-size: 11px;
}
.composer-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 8px 8px 13px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--bg-soft);
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}
.composer-box:focus-within {
  border-color: var(--brand);
  background: var(--bg);
  box-shadow: 0 0 0 3px rgba(38, 108, 251, 0.13);
}
textarea {
  flex: 1;
  min-height: 24px;
  max-height: 120px;
  padding: 0;
  resize: none;
  border: 0;
  outline: 0;
  color: var(--text);
  background: transparent;
  font: 13.5px/1.6 inherit;
}
textarea::placeholder {
  color: var(--text-3);
}
textarea:disabled {
  cursor: not-allowed;
}
.send {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #3d7bff, #266cfb 60%, #1d5ce0);
  box-shadow: 0 5px 12px rgba(38, 108, 251, 0.32);
  cursor: pointer;
  transition: transform 0.15s, opacity 0.15s;
}
.send:hover:not(:disabled) {
  transform: translateY(-1px);
}
.send:disabled {
  color: #aeb4c3;
  background: #edf0f4;
  box-shadow: none;
  cursor: not-allowed;
}
.send--stop {
  background: linear-gradient(135deg, #f87171, #ef4444);
  box-shadow: 0 5px 12px rgba(239, 68, 68, 0.32);
}
.assistant-composer small {
  display: block;
  margin-top: 7px;
  text-align: center;
  color: var(--text-3);
  font-size: 10.5px;
}

/* ========== 拖拽手柄 ========== */
.assistant-resize {
  position: absolute;
  right: 0;
  bottom: 0;
  z-index: 3;
  width: 18px;
  height: 18px;
  cursor: nwse-resize;
  opacity: 0;
  transition: opacity 0.2s;
}
.assistant-resize::after {
  content: '';
  position: absolute;
  right: 5px;
  bottom: 5px;
  width: 7px;
  height: 7px;
  border-right: 2px solid var(--text-3);
  border-bottom: 2px solid var(--text-3);
  border-radius: 0 0 3px 0;
}
.assistant-panel:hover .assistant-resize {
  opacity: 1;
}

/* ========== 过渡与响应式 ========== */
.assistant-panel-enter-active,
.assistant-panel-leave-active {
  transition: opacity 0.24s ease, transform 0.24s cubic-bezier(0.16, 1, 0.3, 1);
}
.assistant-panel-enter-from,
.assistant-panel-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}
@media (max-width: 600px) {
  .assistant-panel,
  .assistant-panel.expanded {
    right: 8px !important;
    bottom: 8px !important;
    width: calc(100vw - 16px) !important;
    height: calc(100vh - 16px) !important;
    border-radius: 18px;
  }
  .quick-grid {
    grid-template-columns: 1fr;
  }
  .assistant-fab {
    right: 16px;
    bottom: 16px;
  }
  .assistant-resize {
    display: none;
  }
}
</style>
