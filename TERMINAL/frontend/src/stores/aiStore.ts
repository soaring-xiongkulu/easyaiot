import { defineStore } from 'pinia'
import { ref, computed, reactive, watch } from 'vue'
import type { AIMessage, ExecutionMode, AISession, AIAgentStatus } from '../types/ai'
import { SaveAISessions, LoadAISessions } from '../../bindings/easyaiot/terminal/app'
import { useLocalStateStore } from './localStateStore'
import { t } from '../i18n'

/**
 * Estimate token count for a string using character-based heuristics.
 * ASCII/English: ~3.5 chars per token. CJK/non-ASCII: ~1.8 chars per token.
 * Accurate to within ~15% for typical mixed content.
 */
function estimateTokens(text: string): number {
  let asciiChars = 0
  let nonAsciiChars = 0
  for (let i = 0; i < text.length; i++) {
    if (text.charCodeAt(i) <= 0x7f) {
      asciiChars++
    } else {
      nonAsciiChars++
    }
  }
  return Math.ceil(asciiChars / 3.5 + nonAsciiChars / 1.8)
}

/**
 * Estimate tokens for an AIMessage, including content, tool_calls, and
 * serialized _rawApiMsg.
 */
function estimateMessageTokens(msg: AIMessage): number {
  let total = estimateTokens(msg.content)
  if (msg.tool_calls) {
    for (const tc of msg.tool_calls) {
      total += estimateTokens(tc.function.name)
      total += estimateTokens(tc.function.arguments)
    }
  }
  if (msg._rawApiMsg) {
    total += estimateTokens(JSON.stringify(msg._rawApiMsg))
  }
  return total
}

/**
 * Static AI system rules — immutable per app version, always cacheable.
 * Dynamic shell/panel context is injected into the latest user message instead.
 */
const SYSTEM_RULES = `You are an AI assistant inside Terminal, a terminal emulator. You can execute shell commands in the user's active terminal to help them complete tasks.

AVAILABLE TOOLS:
1. execute_command — Run a shell command and wait for its output. Set timeout based on expected duration. Use head_lines/tail_lines to control how much output you receive.
2. start_command — Start a background/long-running command (servers, daemons). Returns initial output immediately without waiting.
3. capture_terminal — Take an instant snapshot of the terminal screen. Use to check current state without running commands.
4. collect_output — Wait and collect new terminal output. Pure passive listening — does NOT send anything to the terminal. Use when a command is still running and you want to see progress.
5. send_terminal_key — Send text or control keys to the terminal. Use ONLY when you can SEE an interactive prompt (password, y/n, confirmation). By default, send_enter=true automatically appends Enter after your input, so "y" becomes "y" + Enter. Set send_enter=false only when you need to type raw characters without submitting.
6. interrupt_command — Send Ctrl+C to cancel the running command.
7. save_skill — Create or update a reusable skill (a command-line workflow / SOP) invokable later via /name. Use when the user asks to save the current approach as a skill, or when you just worked out a repeatable command-line procedure worth keeping.

SKILL AUTHORING (when using save_skill):
- name: kebab-case (lowercase letters, digits, hyphens), e.g. "git-clean-branches". Becomes the /trigger.
- description: one line stating BOTH what it does AND when to use it — this drives future matching. E.g. "Clean up merged local git branches. Use when the user wants to delete/tidy git branches."
- body: imperative markdown steps. Write a THIN skill — only include steps you would NOT do by default. Do NOT include YAML frontmatter (name/description are passed separately).
- Locked skills are rejected by the backend when overwriting.

CRITICAL RULES:
- You can only send ONE tool call at a time. Never send multiple tool calls in a single response.
- Always explain what you are about to do before executing commands.
- If a command might be destructive, warn the user.

TIMEOUT GUIDELINES:
- 5-10s: quick commands (ls, cat, pwd, whoami)
- 15-30s: moderate commands (grep, find, df, systemctl status)
- 60-120s: build/install tasks (npm install, pip install, apt-get)
- 120-300s: very long tasks (docker build, large git clone, full compilation)

HANDLING TIMEOUTS:
When execute_command times out, read the output carefully:
- If output shows progress (percentages, file names scrolling): use collect_output to keep waiting.
- If output shows a prompt (password, y/n, [sudo], "Are you sure?"): ask the user for credentials, then use send_terminal_key.
- If output is empty or shows an error: use interrupt_command, then reassess.
- NEVER re-send the same command after a timeout — this causes duplicate commands to pile up.

INTERACTIVE PROMPTS:
- Password prompt: ask the user (NEVER guess passwords).
- y/n confirmation: use send_terminal_key with input: "y" (send_enter defaults to true, so Enter is sent automatically).
- Pager (less/more): use send_terminal_key with control: "ctrl_c" to exit.
- send_enter parameter: defaults to true, automatically appends Enter after your input. Set to false only when you need to type raw characters without submitting.

OUTPUT READING:
- To check if shell prompt is back after a command: use capture_terminal.
- To track progress of a running command: use collect_output.
- Output was truncated: adjust head_lines/tail_lines and re-run.

PROHIBITED:
- NEVER execute clear/cls/Reset. The user must always see command history.
- NEVER use send_terminal_key with unknown prompts — you must SEE the prompt first.
- NEVER send multiple tool calls in one response.

SHELL AWARENESS:
- At the START of EVERY response, read the shell/panel context in the user's message. IGNORE any memory of what the previous shell was — only the latest context matters.
- The user may switch terminal tabs at any time. Each terminal is an independent environment.
- When the terminal type changes, switch to the NEW shell's command syntax immediately.
- Do NOT invoke a different shell executable from within the current terminal.

RISK CLASSIFICATION:
Every execute_command call MUST include a "risk" field:
- "read": only inspects/views data, no modifications at all
- "write": modifies or creates data, but not system-destructive
- "dangerous": potentially destructive or system-altering
For chained commands, classify based on the MOST risky operation in the chain.

--- NEGATIVE EXAMPLES (STRICTLY FORBIDDEN) ---
❌ In Git Bash, do NOT run: Get-CimInstance Win32_LogicalDisk
❌ In PowerShell, do NOT run: ls -la /mnt/c/
❌ In CMD, do NOT run: df -h
❌ In Git Bash, do NOT run: powershell.exe -Command "..."
❌ In PowerShell, do NOT run: bash -c "..."
Use ONLY the current shell's native syntax.`

async function loadSessionsFromBackend(): Promise<{ sessions: AISession[], currentSessionId: string | null }> {
  try {
    const data = await LoadAISessions() as any
    const sessions: AISession[] = (data.sessions || []).map((s: any) => ({
      id: s.id,
      name: s.name,
      createdAt: s.createdAt,
      updatedAt: s.updatedAt,
      messages: (s.messages || []).map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        tool_call_id: m.tool_call_id,
        tool_calls: m.tool_calls || [],
        pendingTools: m.pendingTools || [],
        _rawApiMsg: m._rawApiMsg ? JSON.parse(m._rawApiMsg) : undefined,
      }))
    }))
    return { sessions, currentSessionId: data.currentSessionId || null }
  } catch {
    return { sessions: [], currentSessionId: null }
  }
}

export const useAIStore = defineStore('ai', () => {
  const visible = ref(false)
  const messages = ref<AIMessage[]>([])
  const mode = ref<ExecutionMode>('confirm_dangerous')
  const isRunning = ref(false)
  const status = ref<AIAgentStatus>('thinking')
  const stopRequested = ref(false)
  const sessions = ref<AISession[]>([])
  const currentSessionId = ref<string | null>(null)
  const lastDebugInfo = ref<{ request: string; error: string } | null>(null)
  const initialized = ref(false)
  const pendingCommand = ref<{
    messageId: string
    toolId: string
    toolName: string
    command: string
    risk: string
    dangerous: boolean
  } | null>(null)
  const pendingQuestion = ref<{
    messageId: string
    toolId: string
    question: string
    header?: string
    options: Array<{ label: string; description: string }>
    multiSelect: boolean
  } | null>(null)
  const lastPanelContext = ref<{ panelId: string; shellPath: string } | null>(null)
  const queuedMessages = ref<{ id: string; content: string; skillName?: string; skillBody?: string; commandBody?: string }[]>([])

  function setLastPanelContext(panelId: string, shellPath: string) {
    lastPanelContext.value = { panelId, shellPath }
  }

  function enqueueMessage(content: string, skillName?: string, skillBody?: string, commandBody?: string) {
    const trimmed = content.trim()
    if (!trimmed && !commandBody && !skillName) return
    queuedMessages.value.push({
      id: `q-${Date.now()}-${queuedMessages.value.length}`,
      content: trimmed,
      skillName,
      skillBody,
      commandBody,
    })
  }

  function removeQueuedMessage(id: string) {
    queuedMessages.value = queuedMessages.value.filter(q => q.id !== id)
  }

  function clearQueue() {
    queuedMessages.value = []
  }

  async function saveVisible() {
    try {
      useLocalStateStore().update({ aiSidebarVisible: visible.value })
    } catch {
      // ignore save errors
    }
  }

  // Auto-persist AI sidebar visibility whenever it changes
  watch(visible, () => {
    saveVisible()
  })

  function setDebugInfo(request: unknown, error: string) {
    try {
      lastDebugInfo.value = {
        request: JSON.stringify(request, null, 2),
        error
      }
    } catch {
      lastDebugInfo.value = {
        request: String(request),
        error
      }
    }
  }

  function clearDebugInfo() {
    lastDebugInfo.value = null
  }

  function setPendingCommand(cmd: { messageId: string; toolId: string; command: string; risk: string; dangerous: boolean }) {
    pendingCommand.value = cmd
  }

  function clearPendingCommand() {
    pendingCommand.value = null
  }

  function setPendingQuestion(q: { messageId: string; toolId: string; question: string; header?: string; options: Array<{ label: string; description: string }>; multiSelect: boolean }) {
    pendingQuestion.value = q
  }

  function clearPendingQuestion() {
    pendingQuestion.value = null
  }

  function toggle() {
    visible.value = !visible.value
  }

  function addMessage(msg: AIMessage): AIMessage {
    const r = reactive({ ...msg }) as AIMessage
    messages.value.push(r)
    if (currentSessionId.value) {
      const s = sessions.value.find(s => s.id === currentSessionId.value)
      if (s) {
        s.messages.push(r)
        s.updatedAt = Date.now()
        // Move to top on new activity
        const idx = sessions.value.indexOf(s)
        if (idx > 0) {
          sessions.value.splice(idx, 1)
          sessions.value.unshift(s)
        }
        if (msg.role === 'user' && s.name === t('ai.newSession')) {
          const trimmed = msg.content.trim()
          if (trimmed) {
            s.name = trimmed.length > 20 ? trimmed.slice(0, 20) + '...' : trimmed
          }
        }
        doSave()
      }
    }
    return r
  }

  function addSkillCard(name: string, source: 'explicit' | 'auto') {
    const r = reactive({
      id: `skill-${Date.now()}`,
      role: 'user' as const,
      content: '',
      skillName: name,
      skillSource: source,
    }) as AIMessage
    messages.value.push(r)
    if (currentSessionId.value) {
      const s = sessions.value.find(s => s.id === currentSessionId.value)
      if (s) {
        s.messages.push(r)
        s.updatedAt = Date.now()
        doSave()
      }
    }
  }

  function addCommandCard(name: string, args: string) {
    const r = reactive({
      id: `cmd-${Date.now()}`,
      role: 'user' as const,
      content: '',
      commandName: name,
      commandArgs: args,
    }) as AIMessage
    messages.value.push(r)
    if (currentSessionId.value) {
      const s = sessions.value.find(s => s.id === currentSessionId.value)
      if (s) {
        s.messages.push(r)
        s.updatedAt = Date.now()
        doSave()
      }
    }
  }

  function clearMessages() {
    messages.value = []
    if (currentSessionId.value) {
      const s = sessions.value.find(s => s.id === currentSessionId.value)
      if (s) {
        s.messages = []
        s.updatedAt = Date.now()
        doSave()
      }
    }
  }

  async function init() {
    const data = await loadSessionsFromBackend()
    sessions.value = data.sessions
      .filter(s => s.messages.length > 0)
      .sort((a, b) => b.updatedAt - a.updatedAt)
    // Always start with a fresh session after restart
    currentSessionId.value = null
    initialized.value = true

    // Load sidebar visibility from local state
    try {
      const ls = useLocalStateStore()
      if (!ls.loaded) await ls.init()
      visible.value = ls.state.aiSidebarVisible ?? false
    } catch {
      // keep default
    }

    // Restore current session or create a new one
    if (currentSessionId.value) {
      const s = sessions.value.find(s => s.id === currentSessionId.value)
      if (s) {
        messages.value = s.messages.map(m => {
          const msg = { ...m }
          if (typeof msg._rawApiMsg === 'string' && msg._rawApiMsg) {
            try { msg._rawApiMsg = JSON.parse(msg._rawApiMsg) } catch { delete msg._rawApiMsg }
          }
          return reactive(msg) as AIMessage
        })
      } else {
        createSession()
      }
    } else {
      createSession()
    }
  }


  async function doSave() {
    try {
      const data = {
        sessions: sessions.value.map(s => ({
          id: s.id,
          name: s.name,
          createdAt: s.createdAt,
          updatedAt: s.updatedAt,
          messages: s.messages.map(m => ({
            id: m.id,
            role: m.role,
            content: m.content,
            tool_call_id: m.tool_call_id || '',
            tool_calls: m.tool_calls || [],
            pendingTools: m.pendingTools || [],
            _rawApiMsg: m._rawApiMsg ? JSON.stringify(m._rawApiMsg) : '',
          }))
        })),
        currentSessionId: currentSessionId.value || '',
      }
      await SaveAISessions(data as any)
    } catch {
      // ignore save errors
    }
  }

  function createSession(name?: string) {
    const now = Date.now()
    const session: AISession = {
      id: `session-${now}`,
      name: name || t('ai.newSession'),
      createdAt: now,
      updatedAt: now,
      messages: []
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    messages.value = []
    // Trim to max 15 sessions
    if (sessions.value.length > 15) {
      sessions.value = sessions.value.slice(0, 15)
    }
    clearQueue()
    // Don't save empty sessions — only persist when first message is added
  }

  function switchSession(sessionId: string) {
    const s = sessions.value.find(s => s.id === sessionId)
    if (!s) return
    currentSessionId.value = sessionId
    messages.value = s.messages.map(m => reactive({ ...m }) as AIMessage)
    clearQueue()
  }

  function deleteSession(sessionId: string) {
    const idx = sessions.value.findIndex(s => s.id === sessionId)
    if (idx === -1) return
    sessions.value.splice(idx, 1)
    doSave()
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        switchSession(sessions.value[0].id)
      } else {
        createSession()
      }
    }
  }

  // Issue #756: drop one message (and its tool-result pairs) from the current
  // session. messages[] and the owning session share the same reactive objects,
  // so splicing the view array also splices the session; doSave persists it.
  function deleteMessage(messageId: string) {
    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx === -1) return
    const m = messages.value[idx]
    // Remove matching tool messages so the API never sees an orphaned
    // tool_result (conversation() filters dangling ones, but the UI should
    // not keep dead rows either).
    let end = idx + 1
    if (m.role === 'assistant' && m.tool_calls?.length) {
      const ids = new Set(m.tool_calls.map(tc => tc.id))
      while (end < messages.value.length) {
        const n = messages.value[end]
        if (n.role === 'tool' && n.tool_call_id && ids.has(n.tool_call_id)) end++
        else break
      }
    }
    messages.value.splice(idx, end - idx)
    doSave()
  }

  // Issue #756: drop the message AND everything after it (context rollback,
  // Trae-style partial deletion). Same shared-array semantics as deleteMessage.
  function truncateFrom(messageId: string) {
    const idx = messages.value.findIndex(m => m.id === messageId)
    if (idx === -1) return
    messages.value.splice(idx)
    doSave()
  }

  // Issue #756: serialize the current session to markdown for export.
  function exportSessionMarkdown(sessionId: string): string {
    const s = sessions.value.find(x => x.id === sessionId)
    if (!s) return ''
    const lines: string[] = [
      `# ${s.name}`,
      '',
      `> ${new Date(s.createdAt).toLocaleString()} · Terminal AI Assistant`,
    ]
    for (const m of s.messages) {
      if (m.role === 'tool') continue
      const who = m.role === 'user' ? '🧑 User' : '🤖 Assistant'
      lines.push('', `## ${who}`, '', m.content || '')
      if (m.role === 'assistant' && m.tool_calls?.length) {
        for (const tc of m.tool_calls) {
          lines.push('', `**Tool call: \`${tc.function.name}\`**`, '', '```', tc.function.arguments, '```')
        }
      }
    }
    return lines.join('\n') + '\n'
  }

  function renameSession(sessionId: string, name: string) {
    const s = sessions.value.find(s => s.id === sessionId)
    if (s) {
      s.name = name
      doSave()
    }
  }

  function stop() {
    stopRequested.value = true
    isRunning.value = false
    clearQueue()
  }

  function resetStop() {
    stopRequested.value = false
  }

  // Build Anthropic-native message array (system is separate top-level field)
  const conversation = computed(() => {
    // Token budget: 80% of Claude's 200K context window, minus headroom
    const MAX_CONTEXT_TOKENS = 160000

    // Estimate static overhead (cached, counted once)
    // Tools definition is small and static (~1KB); hardcode estimate to avoid
    // a circular dependency on llm.ts
    const systemTokens = estimateTokens(SYSTEM_RULES)
    const toolsTokens = 250  // ~1KB execute_command tool definition
    let tokenCount = systemTokens + toolsTokens

    // Walk backwards through messages, accumulate token estimates.
    // Stop when we exceed the budget.
    const kept: typeof messages.value = []
    for (let i = messages.value.length - 1; i >= 0; i--) {
      const msg = messages.value[i]
      const msgTokens = estimateMessageTokens(msg)
      if (tokenCount + msgTokens > MAX_CONTEXT_TOKENS) break
      tokenCount += msgTokens
      kept.unshift(msg)
    }

    let recentMsgs = kept

    // Don't start the conversation with an orphaned tool_result whose matching
    // tool_use was truncated out of the window. Strip leading tool messages
    // until we hit a user or assistant message.
    while (recentMsgs.length > 0 && recentMsgs[0].role === 'tool') {
      recentMsgs.shift()
    }

    // Collect all resolved tool_use IDs from tool_result messages
    const resolvedIds = new Set<string>()
    for (const m of recentMsgs) {
      if (m.role === 'tool' && m.tool_call_id) {
        resolvedIds.add(m.tool_call_id)
      }
    }

    const result: Array<Record<string, unknown>> = []

    for (const m of recentMsgs) {
      if (m.id.startsWith('dbg-')) continue
      if (m.needsContinue) continue  // UI-only prompts, not part of LLM conversation
      // skill/command cards are UI-only markers; never send them to the API
      if ((m.skillName || m.commandName) && !m.content) continue
      // restored/legacy empty user messages produce invalid empty text blocks
      if (m.role === 'user' && !m.content && !m._contextHeader) continue

      // Tool messages: ones with tool_call_id are real tool_results for the API;
      // ones without are display-only system errors and must not be sent.
      if (m.role === 'tool') {
        if (m.tool_call_id) {
          result.push({
            role: 'user',
            content: [{ type: 'tool_result', tool_use_id: m.tool_call_id, content: m.content }]
          })
        }
        continue
      }

      // Skip assistant messages that are API error placeholders from before the fix
      if (m.role === 'assistant' && typeof m.content === 'string' && m.content.includes('[Error:')) {
        continue
      }

      // Assistant with raw API blocks: filter dangling tool_use blocks without matching tool_result
      if (m._rawApiMsg) {
        const raw = m._rawApiMsg as Record<string, unknown>
        const content = raw.content
        if (Array.isArray(content)) {
          const filtered = (content as Array<Record<string, unknown>>).filter((block: Record<string, unknown>) => {
            if (block.type === 'tool_use') {
              return resolvedIds.has(block.id as string)
            }
            return true
          })
          if (filtered.length === 0 && !m.content && !(m.pendingTools?.length || pendingCommand.value?.messageId === m.id)) continue
          result.push({ ...raw, role: (raw.role as string) || 'assistant', content: filtered })
        } else {
          result.push({ ...raw, role: (raw.role as string) || 'assistant' })
        }
        continue
      }

      // Assistant with legacy tool_calls: filter dangling ones, build content blocks
      if (m.role === 'assistant' && m.tool_calls?.length) {
        const resolved = m.tool_calls.filter(tc => resolvedIds.has(tc.id))
        if (!m.content && resolved.length === 0 && !(m.pendingTools?.length || pendingCommand.value?.messageId === m.id)) continue

        const blocks: Array<Record<string, unknown>> = []
        if (m.content) {
          blocks.push({ type: 'text', text: m.content })
        }
        for (const tc of resolved) {
          let input: Record<string, unknown> = {}
          try { input = JSON.parse(tc.function.arguments) } catch { /* passthrough */ }
          blocks.push({ type: 'tool_use', id: tc.id, name: tc.function.name, input })
        }
        result.push({ role: 'assistant', content: blocks })
        continue
      }

      // Skip empty assistant messages (no content, no tool calls, no raw api msg, no pending tools)
      if (m.role === 'assistant' && !m.content && !(m.pendingTools?.length || pendingCommand.value?.messageId === m.id)) continue

      // Inject dynamic context header into user messages for the API
      // (hidden from UI, stored in _contextHeader)
      if (m.role === 'user' && m._contextHeader) {
        result.push({ role: m.role, content: m._contextHeader + '\n\n' + m.content })
      } else {
        result.push({ role: m.role || 'user', content: m.content })
      }
    }

    // Final safety pass: enforce that every tool_use is immediately followed
    // by a user message containing its matching tool_result, and every
    // tool_result is immediately preceded by an assistant with its tool_use.
    // The Anthropic API rejects tool_use blocks that are not resolved in the
    // very next message.
    const cleaned: Array<Record<string, unknown>> = []
    for (let i = 0; i < result.length; i++) {
      const msg = result[i]

      if (msg.role === 'assistant' && Array.isArray(msg.content)) {
        const nextMsg = i + 1 < result.length ? result[i + 1] : null
        const blocks = (msg.content as Array<Record<string, unknown>>).filter((block) => {
          if (block.type === 'tool_use') {
            if (!nextMsg || nextMsg.role !== 'user' || !Array.isArray(nextMsg.content)) {
              return false
            }
            return (nextMsg.content as Array<Record<string, unknown>>).some(
              (nb) => nb.type === 'tool_result' && nb.tool_use_id === block.id
            )
          }
          return true
        })
        if (blocks.length === 0) continue
        cleaned.push({ ...msg, content: blocks })
      } else if (msg.role === 'user' && Array.isArray(msg.content)) {
        const prevMsg = i > 0 ? result[i - 1] : null
        const blocks = (msg.content as Array<Record<string, unknown>>).filter((block) => {
          if (block.type === 'tool_result') {
            if (!prevMsg || prevMsg.role !== 'assistant' || !Array.isArray(prevMsg.content)) {
              return false
            }
            return (prevMsg.content as Array<Record<string, unknown>>).some(
              (pb) => pb.type === 'tool_use' && pb.id === block.tool_use_id
            )
          }
          return true
        })
        if (blocks.length === 0) continue
        cleaned.push({ ...msg, content: blocks })
      } else {
        cleaned.push(msg)
      }
    }

    // Additional validation: ensure no consecutive user messages ( Anthropic rejects this )
    const deduped: Array<Record<string, unknown>> = []
    for (const msg of cleaned) {
      if (msg.role === 'user' && deduped.length > 0 && deduped[deduped.length - 1].role === 'user') {
        const prev = deduped[deduped.length - 1]
        const prevBlocks = Array.isArray(prev.content) ? prev.content : [{ type: 'text', text: prev.content }]
        const msgBlocks = Array.isArray(msg.content) ? msg.content : [{ type: 'text', text: msg.content }]
        prev.content = [...prevBlocks, ...msgBlocks]
      } else {
        deduped.push(msg)
      }
    }

    // Messages are inherently dynamic — no cache_control breakpoints here.
    // Caching is handled entirely on the system prompt (see llm.ts).

    return deduped
  })

  const systemPrompt = computed(() => SYSTEM_RULES)

  return {
    visible,
    toggle,
    messages,
    addMessage, addSkillCard, addCommandCard,
    clearMessages,
    mode,
    isRunning,
    status,
    conversation,
    systemPrompt,
    stopRequested,
    stop,
    resetStop,
    sessions,
    currentSessionId,
    createSession,
    switchSession,
    deleteSession,
    deleteMessage,
    truncateFrom,
    exportSessionMarkdown,
    renameSession,
    lastDebugInfo,
    setDebugInfo,
    clearDebugInfo,
    pendingCommand,
    setPendingCommand,
    clearPendingCommand,
    pendingQuestion,
    setPendingQuestion,
    clearPendingQuestion,
    initialized,
    init,
    lastPanelContext,
    setLastPanelContext,
    queuedMessages,
    enqueueMessage,
    removeQueuedMessage,
    clearQueue,
    doSave
  }
})
