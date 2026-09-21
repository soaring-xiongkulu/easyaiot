import { chat, AVAILABLE_TOOLS, ChatCancelledError, ChatTimeoutError } from './llm'
import { executeCommand, startCommand, captureTerminal, collectOutput, sendTerminalKey } from './terminalAgent'
import type { ExecuteResult } from './terminalAgent'
import { useAIStore } from '../stores/aiStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useTabStore } from '../stores/tabStore'
import { usePanelStore } from '../stores/panelStore'
import { useSessionStore } from '../stores/sessionStore'
import { useSkillStore } from '../stores/skillStore'
import { GetSkillFile, ListSkillFiles } from '../../bindings/easyaiot/terminal/app'
import type { AIMessage } from '../types/ai'
import { Events } from '@wailsio/runtime'
import {
  InputValidationError,
  validateRequiredString,
  validateObject,
} from '../utils/runtimeTypeCheck'

// Global token listener management: only one runAgent instance should receive
// ai:token events at a time. Registering a new listener automatically cancels
// the previous one, preventing duplicate streaming into multiple assistant
// messages when a stop/continue sequence races. F-315: each register call
// bumps a generation counter; the returned cleanup only clears module state
// when its generation still matches, so an early-return path that gets
// superseded by a re-entry (approveTool → runAgent; rejectTool / answer /
// dismissQuestion setTimeout→runAgent) can't accidentally clobber a newer
// pair by running its stale cleanup.
let activeTokenUnsubscribe: (() => void) | null = null
let activeAssistantMsg: AIMessage | null = null
let activeGeneration = 0

function registerTokenListener(callback: (data: any) => void): () => void {
  activeTokenUnsubscribe?.()
  activeTokenUnsubscribe =Events.On('ai:token', (ev) => callback(ev.data))
  activeGeneration++
  const myGeneration = activeGeneration
  return () => {
    if (myGeneration !== activeGeneration) return
    activeTokenUnsubscribe?.()
    activeTokenUnsubscribe = null
    activeAssistantMsg = null
  }
}

function setActiveAssistantMsg(msg: AIMessage | null) {
  activeAssistantMsg = msg
}

function getActivePanel() {
  const tabStore = useTabStore()
  const panelStore = usePanelStore()

  // Check for AI-locked panel first
  const lockedPanelId = tabStore.getAILockedPanel()
  if (lockedPanelId) {
    return panelStore.getPanel(lockedPanelId)
  }

  // Fall back to active panel based on tab type
  const activeTab = tabStore.activeTab
  if (!activeTab) return undefined

  if (activeTab.type === 'terminal' || activeTab.type === 'settings') {
    return panelStore.getPanel(activeTab.panelId)
  }

  if (activeTab.type === 'workspace' && activeTab.activePanelId) {
    return panelStore.getPanel(activeTab.activePanelId)
  }

  return undefined
}

function hasActiveSession(): boolean {
  const panel = getActivePanel()
  return !!panel?.sessionId
}

type RiskLevel = 'read' | 'write' | 'dangerous'

export const VALID_RISK: readonly RiskLevel[] = ['read', 'write', 'dangerous']

export function getRisk(tu: { name: string; input: Record<string, unknown> }): RiskLevel {
  if (tu.name !== 'execute_command' && tu.name !== 'start_command') return 'dangerous'
  const risk = tu.input.risk
  if (risk === 'read' || risk === 'write' || risk === 'dangerous') return risk
  return 'dangerous' // default-closed: unknown / missing / wrong-typed → dangerous
}

function shouldConfirm(risk: RiskLevel): boolean {
  const store = useAIStore()
  switch (store.mode) {
    case 'confirm_all': return true
    case 'confirm_write': return risk !== 'read'
    case 'confirm_dangerous': return risk === 'dangerous'
    case 'bypass': return false
    default: return risk !== 'read'
  }
}

// ---- Tool input validators (FE-P0-3) ----
// Hand-rolled shape checks for the 7 most-used tools. The LLM is untrusted;
// `tu.input.command as string` would yield "[object Object]" for `command: {}`.
// On any failure we throw InputValidationError so the dispatch site can
// surface the error back to the model and continue the agent loop.

interface ExecuteCommandInput {
  command: string
  timeout: number
  head_lines: number
  tail_lines: number
  panel?: string
}

function validateExecuteCommandInput(raw: unknown): ExecuteCommandInput {
  const obj = validateObject(raw, 'execute_command input')
  return {
    command: validateRequiredString(obj.command, 'command'),
    timeout: typeof obj.timeout === 'number' && Number.isFinite(obj.timeout) && obj.timeout > 0 ? obj.timeout : 60,
    head_lines: typeof obj.head_lines === 'number' && Number.isFinite(obj.head_lines) ? obj.head_lines : 50,
    tail_lines: typeof obj.tail_lines === 'number' && Number.isFinite(obj.tail_lines) ? obj.tail_lines : 300,
    panel: typeof obj.panel === 'string' ? obj.panel : undefined,
  }
}

interface StartCommandInput {
  command: string
  panel?: string
}

function validateStartCommandInput(raw: unknown): StartCommandInput {
  const obj = validateObject(raw, 'start_command input')
  return {
    command: validateRequiredString(obj.command, 'command'),
    panel: typeof obj.panel === 'string' ? obj.panel : undefined,
  }
}

interface SendTerminalKeyInput {
  input?: string
  control?: 'ctrl_c' | 'ctrl_d' | 'enter'
  send_enter: boolean
  panel?: string
}

function validateSendTerminalKeyInput(raw: unknown): SendTerminalKeyInput {
  const obj = validateObject(raw, 'send_terminal_key input')
  const control = obj.control
  let validatedControl: 'ctrl_c' | 'ctrl_d' | 'enter' | undefined
  if (control === undefined) {
    validatedControl = undefined
  } else if (control === 'ctrl_c' || control === 'ctrl_d' || control === 'enter') {
    validatedControl = control
  } else {
    throw new InputValidationError(`control must be one of ctrl_c, ctrl_d, enter`)
  }
  return {
    input: typeof obj.input === 'string' ? obj.input : undefined,
    control: validatedControl,
    send_enter: typeof obj.send_enter === 'boolean' ? obj.send_enter : true,
    panel: typeof obj.panel === 'string' ? obj.panel : undefined,
  }
}

interface AskUserInput {
  question: string
  header?: string
  options: Array<{ label: string; description: string }>
  multiSelect: boolean
}

function validateAskUserInput(raw: unknown): AskUserInput {
  const obj = validateObject(raw, 'ask_user input')
  const rawOptions = obj.options
  const options: Array<{ label: string; description: string }> = []
  if (Array.isArray(rawOptions)) {
    for (const item of rawOptions) {
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        const o = item as Record<string, unknown>
        const label = typeof o.label === 'string' ? o.label : ''
        const description = typeof o.description === 'string' ? o.description : ''
        if (label) options.push({ label, description })
      }
    }
  }
  return {
    question: validateRequiredString(obj.question, 'question'),
    header: typeof obj.header === 'string' ? obj.header : undefined,
    options,
    multiSelect: typeof obj.multiSelect === 'boolean' ? obj.multiSelect : false,
  }
}

interface SaveSkillInput {
  name: string
  description: string
  body: string
}

function validateSaveSkillInput(raw: unknown): SaveSkillInput {
  const obj = validateObject(raw, 'save_skill input')
  return {
    name: validateRequiredString(obj.name, 'name'),
    description: validateRequiredString(obj.description, 'description'),
    body: validateRequiredString(obj.body, 'body'),
  }
}

interface UseSkillInput {
  name: string
}

function validateUseSkillInput(raw: unknown): UseSkillInput {
  const obj = validateObject(raw, 'use_skill input')
  return { name: validateRequiredString(obj.name, 'name') }
}

interface ReadSkillFileInput {
  name: string
  path: string
}

function validateReadSkillFileInput(raw: unknown): ReadSkillFileInput {
  const obj = validateObject(raw, 'read_skill_file input')
  return {
    name: validateRequiredString(obj.name, 'name'),
    path: validateRequiredString(obj.path, 'path'),
  }
}

// F-312: cap the bytes stored in a tool message so a single tool call can't
// blow up the conversation computed. The model can still see the beginning
// and end of long output; the in-between is dropped with a clear marker.
// 32 KB total, 8 KB head, 16 KB tail — biased to the tail because error
// messages and final state almost always live at the bottom of terminal output.
const TOOL_RESULT_MAX_BYTES = 32 * 1024
const TOOL_RESULT_HEAD_BYTES = 8 * 1024
const TOOL_RESULT_TAIL_BYTES = 16 * 1024

function capToolResult(text: string): string {
  if (text.length <= TOOL_RESULT_MAX_BYTES) return text
  const head = text.slice(0, TOOL_RESULT_HEAD_BYTES)
  const tail = text.slice(text.length - TOOL_RESULT_TAIL_BYTES)
  const omitted = text.length - TOOL_RESULT_HEAD_BYTES - TOOL_RESULT_TAIL_BYTES
  return `${head}\n\n─────── [已截断: 工具结果共 ${text.length} 字节, 已省略 ${omitted} 字节] ────────\n调整工具参数（如 head_lines / tail_lines）或分段调用以查看被截断部分。\n\n${tail}`
}

function formatExecuteResult(result: ExecuteResult): string {
  if (!result.timedOut) {
    return `${result.output}\n\n[COMMAND COMPLETED]`
  }
  // Put the timeout guidance right after the status line so the AI sees the
  // verdict before reading the follow-up advice.
  return `${result.output}\n\n[COMMAND TIMED OUT]\n\n`
    + `⚠️ The command did not finish within the timeout and may still be running.\n`
    + `Do not resend the same command.\n`
    + `• If the output shows progress (percentages, scrolling filenames, etc.) → use collect_output to keep waiting\n`
    + `• If the output shows a password/confirmation prompt → use send_terminal_key to respond\n`
    + `• If the command is stuck and unresponsive → use interrupt_command to cancel`
}

function getShellName(path?: string): string {
  if (!path) return 'Unknown'
  const lower = path.toLowerCase()
  if (lower.includes('pwsh')) return 'PowerShell'
  if (lower.includes('powershell')) return 'Windows PowerShell'
  if (lower.includes('bash')) return 'Bash'
  if (lower.includes('zsh')) return 'Zsh'
  if (lower.includes('fish')) return 'Fish'
  if (lower.includes('cmd')) return 'CMD'
  if (lower.includes('sh')) return 'Sh'
  return path.split(/[\\/]/).pop() || 'Unknown'
}

/**
 * Shell-specific suffix: appended to system rules dynamically (NOT cached).
 * Lightweight enough that it doesn't significantly impact cache efficiency.
 */
function getShellGuidance(shellPath?: string, isWindowsShell?: boolean, isWindowsOpenSSH?: boolean): string {
  if (isWindowsOpenSSH) {
    return '\n\nThe active terminal is a Windows OpenSSH remote. Its shell could be CMD or PowerShell — determine which first (e.g. run `echo %COMSPEC%` / `ver` for CMD, or `$PSVersionTable` for PowerShell), then use the matching syntax: CMD (dir, type, cd, wmic) or PowerShell (Get-ChildItem, Get-Content, Set-Location).'
  }
  if (isWindowsShell) {
    const isCmd = shellPath?.toLowerCase().includes('cmd')
    return isCmd
      ? '\n\nThe active terminal is Windows CMD. Use CMD syntax (dir, cd, type, wmic, etc.).'
      : '\n\nThe active terminal is Windows PowerShell. Use cmdlets like Get-ChildItem, Set-Location, Get-Content, etc.'
  }
  return '\n\nThe active terminal is a Unix-like shell. Use standard Unix syntax (ls, cat, grep, find, etc.).'
}

/**
 * Whether the given panel is a Windows OpenSSH remote, as detected by the
 * backend from the SSH server identification string and reported via the
 * session:status event. Only meaningful once the connection is established.
 */
function isWindowsOpenSSHPanel(p: { sessionId: string | null } | undefined): boolean {
  if (!p?.sessionId) return false
  return useSessionStore().getRemoteOS(p.sessionId) === 'windows-openssh'
}

/**
 * Build the dynamic context header injected into the latest user message.
 * Carries current shell/terminal state WITHOUT polluting the system prompt.
 */
function buildDynamicContext(): string {
  const store = useAIStore()
  const tabStore = useTabStore()
  const panelStore = usePanelStore()

  const lockedPanels = tabStore.getAILockedPanels()
  const panelIds = lockedPanels.length > 0
    ? lockedPanels
    : (() => {
        const activePanel = getActivePanel()
        return activePanel ? [activePanel.id] : []
      })()

  if (panelIds.length === 0) return ''

  const parts: string[] = []
  parts.push('AVAILABLE PANELS:')

  // Collect panels, dedupe titles with id suffix
  const titleCounts = new Map<string, number>()
  const panels = panelIds.map(id => panelStore.getPanel(id)).filter(Boolean)

  // First pass: count titles to detect duplicates
  for (const p of panels) {
    titleCounts.set(p!.title, (titleCounts.get(p!.title) || 0) + 1)
  }

  // Second pass: build display names
  let idx = 1
  for (const p of panels) {
    if (!p) continue
    const shellPath = p.config?.shellPath
    const shellName = shellPath
      ? getShellName(shellPath)
      : (p.type === 'ssh' ? (isWindowsOpenSSHPanel(p) ? 'SSH (Windows OpenSSH)' : 'SSH (Unix-like)') : 'Unknown')

    const displayName = titleCounts.get(p.title)! > 1
      ? `${p.title} (id: ${p.id})`
      : p.title

    const lineParts: string[] = []
    lineParts.push(`  ${idx}. "${displayName}" [${shellName}]`)

    if (p.type === 'ssh' && p.config) {
      lineParts.push(` [SSH: ${p.config.user}@${p.config.host}:${p.config.port}]`)
    }

    parts.push(lineParts.join(''))
    idx++
  }

  parts.push('\n' + '='.repeat(40))

  // Terminal switch detection
  const lastCtx = store.lastPanelContext
  if (lastCtx && lockedPanels.length > 0 && !lockedPanels.includes(lastCtx.panelId)) {
    const prev = lastCtx.shellPath ? getShellName(lastCtx.shellPath) : 'another terminal'
    const firstPanel = panelStore.getPanel(lockedPanels[0])
    const currShell = firstPanel?.config?.shellPath
    const curr = currShell ? getShellName(currShell) : (firstPanel?.type === 'ssh' ? 'SSH' : 'local terminal')
    parts.push(`\n【NOTICE】User changed AI panel selection from "${prev}" to "${curr}". Now targeting "${firstPanel?.title || 'unknown'}". Reassess the environment from scratch.`)
  }

  return parts.join('\n')
}

/**
 * Build the system prompt: static rules from store + lightweight shell guidance.
 * Dynamic context (shell banner, switch notices) goes into the user message.
 */
function buildSystemPrompt(): string {
  const store = useAIStore()
  const activePanel = getActivePanel()
  const shellPath = activePanel?.config?.shellPath
  const isWindowsShell = !!shellPath && (
    shellPath.toLowerCase().includes('powershell') ||
    shellPath.toLowerCase().includes('pwsh') ||
    shellPath.toLowerCase().includes('cmd')
  )
  const isWindowsOpenSSH = isWindowsOpenSSHPanel(activePanel)
  return store.systemPrompt + getShellGuidance(shellPath, isWindowsShell, isWindowsOpenSSH) + buildSkillIndex()
}

/**
 * L1 skill index: name + description of enabled skills, appended to the system
 * prompt so the model knows which skills exist (to invoke or avoid duplicating).
 */
function buildSkillIndex(): string {
  const skillStore = useSkillStore()
  const list = skillStore.enabledSkills.filter(s => s.modelInvocable)
  if (list.length === 0) return ''
  const lines = list.map(s => `- /${s.name}: ${s.description}`).join('\n')
  return `\n\nAVAILABLE SKILLS (when one matches the task, call the use_skill tool with its name to load its full instructions before acting; do NOT duplicate an existing one with save_skill):\n${lines}`
}

export async function runAgent(userInput: string, skillName?: string, skillBody?: string, commandBody?: string) {
  const store = useAIStore()

  if (!hasActiveSession()) {
    // 输入框已禁用，正常流程不会走到这里；兜底直接返回，不写入任何消息
    return
  }

  // Auto-reject any pending command/question from previous turn
  if (userInput && store.pendingCommand) {
    store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'tool',
      content: 'User started a new conversation. Previous command was cancelled.',
      tool_call_id: store.pendingCommand.toolId
    })
    store.clearPendingCommand()
  }
  if (userInput && store.pendingQuestion) {
    store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'tool',
      content: 'User started a new conversation. Previous question was dismissed.',
      tool_call_id: store.pendingQuestion.toolId
    })
    store.clearPendingQuestion()
  }

  store.resetStop()
  store.isRunning = true
  store.status = 'thinking'

  // Record current panel context so buildDynamicContext can detect terminal switches
  const tabStore = useTabStore()
  const lockedPanels = tabStore.getAILockedPanels()
  const activePanel = getActivePanel()
  const trackPanelId = lockedPanels.length > 0 ? lockedPanels[0] : activePanel?.id
  if (trackPanelId) {
    const panelStore = usePanelStore()
    const tp = panelStore.getPanel(trackPanelId)
    store.setLastPanelContext(trackPanelId, tp?.config?.shellPath || '')
  }

  if (userInput || (skillName && skillBody) || commandBody) {
    const dynamicCtx = buildDynamicContext()
    // skill/command 正文进 _contextHeader（发给模型但 UI 隐藏），content 只留用户原始输入
    let header = dynamicCtx || ''
    if (skillName && skillBody) {
      const skillCtx = `[Skill: ${skillName}]\n${skillBody}`
      header = header ? `${skillCtx}\n\n${header}` : skillCtx
      store.addSkillCard(skillName, 'explicit')
    }
    if (commandBody) {
      const cmdCtx = `[Command]\n${commandBody}`
      header = header ? `${cmdCtx}\n\n${header}` : cmdCtx
    }
    // 仅选 skill/命令未输入文字时，给一句明确指令作为 content，避免发送空的 user 消息
    const content = userInput || (skillName ? `请执行 skill「${skillName}」。` : `请执行命令。`)
    store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      _contextHeader: header || undefined
    })
  }

  // Track whether streaming already delivered text, to skip onChunk duplication
  let streamedText = ''

  // Register stream event listener (fires from Go backend SSE events)
  const cleanupTokenListener = registerTokenListener((data: any) => {
    if (store.stopRequested) return
    if (activeAssistantMsg && data.text) {
      activeAssistantMsg.content += data.text
      streamedText += data.text
      store.status = 'outputting'
    }
  })

  function cleanupStreamListeners() {
    cleanupTokenListener()
    setActiveAssistantMsg(null)
  }

  let turnCount = 0
  const maxTurns = useSettingsStore().settings.ai.maxTurns ?? 20

  while (maxTurns === 0 || turnCount < maxTurns) {
    turnCount++

    if (store.stopRequested) {
      store.addMessage({
        id: `msg-${Date.now()}`,
        role: 'tool',
        content: '[INTERRUPTED]'
      })
      store.isRunning = false
      cleanupStreamListeners()
      return
    }

    // Drain queued user messages at the turn boundary. Injected messages become
    // real user turns; reset turnCount so the new instruction regains its full
    // autonomous-turn budget.
    if (store.queuedMessages.length > 0) {
      const drained = store.queuedMessages.splice(0)
      drained.forEach((q, i) => {
        let header = ''
        if (q.skillName && q.skillBody) {
          header = `[Skill: ${q.skillName}]\n${q.skillBody}`
          store.addSkillCard(q.skillName, 'explicit')
        }
        if (q.commandBody) {
          const cmdCtx = `[Command]\n${q.commandBody}`
          header = header ? `${cmdCtx}\n\n${header}` : cmdCtx
        }
        store.addMessage({
          id: `msg-${Date.now()}-${i}`,
          role: 'user',
          content: q.content || (q.skillName ? `请执行 skill「${q.skillName}」。` : `请执行命令。`),
          _contextHeader: header || undefined,
        })
      })
      turnCount = 0
    }

    const assistantMsg = store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: ''
    })
    setActiveAssistantMsg(assistantMsg)

    const toolUses: Array<{ id: string; name: string; input: Record<string, unknown> }> = []

    const chatOptions: any = {
      system: buildSystemPrompt(),
      messages: store.conversation,
      tools: AVAILABLE_TOOLS,
      onChunk: (chunk: string) => {
        if (store.stopRequested) return
        if (streamedText) return // already handled by ai:token events
        assistantMsg.content += chunk
      },
      onToolUse: (tu: { id: string; name: string; input: Record<string, unknown> }) => {
        if (store.stopRequested) return
        toolUses.push(tu)
      }
    }
    try {
      store.status = 'thinking'
      await chat(chatOptions)
      // Preserve raw API message blocks for conversation history
      if (chatOptions._rawApiMsg) {
        assistantMsg._rawApiMsg = chatOptions._rawApiMsg
      }
      // Save immediately so the complete assistant content and raw API message are persisted
      store.doSave()
    } catch (e: any) {
      const errMsg = e.message ?? String(e)
      // Convert the failed assistant placeholder to a display-only tool message.
      // This keeps the error visible in the UI without polluting the API conversation.
      assistantMsg.role = 'tool'
      if (e instanceof ChatCancelledError || store.stopRequested) {
        assistantMsg.content = '[INTERRUPTED]'
      } else if (e instanceof ChatTimeoutError) {
        assistantMsg.content = '[TIMEOUT]'
      } else {
        assistantMsg.content = `[Error: ${errMsg}]`
      }
      delete assistantMsg._rawApiMsg
      delete assistantMsg.tool_calls
      store.setDebugInfo(store.conversation, errMsg)
      store.isRunning = false
      cleanupStreamListeners()
      return
    }

    if (store.stopRequested) {
      // Cancel any tool calls that were received but not executed
      const cancelledIds = new Set<string>()
      const rawContent = assistantMsg._rawApiMsg?.content
      if (Array.isArray(rawContent)) {
        for (const block of rawContent) {
          if (block.type === 'tool_use' && !cancelledIds.has(block.id)) {
            store.addMessage({
              id: `msg-${Date.now()}`,
              role: 'tool',
              content: 'Command was cancelled by user (Stop).',
              tool_call_id: block.id
            })
            cancelledIds.add(block.id)
          }
        }
      }
      // If no tool calls were pending, the user stopped during text generation.
      // Replace the partial assistant message with a clean stop notice.
      if (cancelledIds.size === 0) {
        assistantMsg.role = 'tool'
        assistantMsg.content = '[INTERRUPTED]'
        delete assistantMsg._rawApiMsg
        delete assistantMsg.tool_calls
      }
      store.isRunning = false
      cleanupStreamListeners()
      return
    }

    // Enforce single tool call
    if (toolUses.length > 1) {
      toolUses.splice(1)
    }

    // Store tool calls in the message for UI confirmation
    if (toolUses.length > 0) {
      assistantMsg.tool_calls = toolUses.map(tu => ({
        id: tu.id,
        type: 'function' as const,
        function: {
          name: tu.name,
          arguments: JSON.stringify(tu.input)
        }
      }))
    }

    if (!assistantMsg.content && toolUses.length === 0) {
      assistantMsg.content = '[No response received from the model. Check your API settings and network connection.]'
      store.isRunning = false
      cleanupStreamListeners()
      return
    }

    if (toolUses.length === 0) {
      // If the user queued messages while the model was responding, don't end —
      // continue looping so the next iteration drains and processes them.
      if (store.queuedMessages.length > 0) {
        continue
      }
      store.isRunning = false
      cleanupStreamListeners()
      return
    }

    // Process exactly one tool call
    const tu = toolUses[0]

    // Surface a malformed tool_use back to the model instead of executing it.
    // Returns true if the caller should `continue` (skip this iteration).
    function handleInvalidInput(reason: string): true {
      store.addMessage({
        id: `msg-${Date.now()}`,
        role: 'tool',
        content: `[Error: invalid ${tu.name} input — ${reason}]. Retry with the documented JSON shape.`,
        tool_call_id: tu.id
      })
      return true
    }

    if (tu.name === 'execute_command') {
      let validated: ExecuteCommandInput
      try {
        validated = validateExecuteCommandInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const command = validated.command
      // Honor the model-provided timeout as-is (no clamping); the validator
      // falls back to 60s when the argument is missing or invalid.
      const timeoutMs = validated.timeout * 1000
      const headLines = validated.head_lines
      const tailLines = validated.tail_lines
      const risk = getRisk(tu)

      if (shouldConfirm(risk)) {
        store.setPendingCommand({
          messageId: assistantMsg.id,
          toolId: tu.id,
          toolName: tu.name,
          command,
          risk,
          dangerous: risk === 'dangerous'
        })
        store.status = 'confirming'
        assistantMsg.tool_calls = [{
          id: tu.id,
          type: 'function' as const,
          function: {
            name: tu.name,
            arguments: JSON.stringify(tu.input)
          }
        }]
        store.isRunning = false
        cleanupStreamListeners()
        return
      }

      try {
        store.status = 'executing'
        const panelTitle = validated.panel
        const result = await executeCommand(command, timeoutMs, headLines, tailLines, () => store.stopRequested, panelTitle)
        if (result.cancelled || store.stopRequested) {
          store.addMessage({
            id: `msg-${Date.now()}`,
            role: 'tool',
            content: '[INTERRUPTED]'
          })
          store.isRunning = false
          cleanupStreamListeners()
          return
        }
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(formatExecuteResult(result)),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error executing command: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'start_command') {
      let validated: StartCommandInput
      try {
        validated = validateStartCommandInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const command = validated.command
      const risk = getRisk(tu)

      if (shouldConfirm(risk)) {
        store.setPendingCommand({
          messageId: assistantMsg.id,
          toolId: tu.id,
          toolName: tu.name,
          command,
          risk,
          dangerous: risk === 'dangerous'
        })
        store.status = 'confirming'
        assistantMsg.tool_calls = [{
          id: tu.id,
          type: 'function' as const,
          function: {
            name: tu.name,
            arguments: JSON.stringify(tu.input)
          }
        }]
        store.isRunning = false
        cleanupStreamListeners()
        return
      }

      try {
        store.status = 'executing'
        const panelTitle = validated.panel
        const result = await startCommand(command, panelTitle)
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(result.output || '(command started)'),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error starting command: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'capture_terminal') {
      const tailLines = (tu.input.tail_lines as number) ?? 200
      try {
        store.status = 'executing'
        const panelTitle = tu.input.panel as string | undefined
        const result = captureTerminal(tailLines, panelTitle)
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(result.output || '(terminal is empty)'),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error capturing terminal: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'collect_output') {
      // Honor the model-provided timeout as-is (no clamping); `|| 30` falls
      // back to 30s when the argument is missing or invalid.
      const timeoutMs = ((tu.input.timeout as number) || 30) * 1000
      const headLines = (tu.input.head_lines as number) ?? 100
      const tailLines = (tu.input.tail_lines as number) ?? 300
      try {
        store.status = 'executing'
        const panelTitle = tu.input.panel as string | undefined
        const result = await collectOutput(timeoutMs, headLines, tailLines, () => store.stopRequested, panelTitle)
        if (store.stopRequested) {
          store.addMessage({
            id: `msg-${Date.now()}`,
            role: 'tool',
            content: '[INTERRUPTED]'
          })
          store.isRunning = false
          cleanupStreamListeners()
          return
        }
        const status = result.completed ? '[COMMAND COMPLETED]' : '[COMMAND STILL RUNNING]'
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(`${result.output}\n\n${status}`),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error collecting output: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'send_terminal_key') {
      let validated: SendTerminalKeyInput
      try {
        validated = validateSendTerminalKeyInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const input = validated.input
      const control = validated.control
      const sendEnter = validated.send_enter
      try {
        store.status = 'executing'
        const panelTitle = validated.panel
        const result = await sendTerminalKey(
          input,
          control,
          sendEnter,
          panelTitle
        )
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(result.output || '(input sent)'),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error sending terminal input: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'interrupt_command') {
      try {
        store.status = 'executing'
        const panelTitle = tu.input.panel as string | undefined
        const result = await sendTerminalKey(undefined, 'ctrl_c', true, panelTitle)
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(result.output || 'Sent Ctrl+C to interrupt the running command.'),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error sending Ctrl+C: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'ask_user') {
      let validated: AskUserInput
      try {
        validated = validateAskUserInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const question = validated.question
      const header = validated.header
      const options = validated.options
      const multiSelect = validated.multiSelect

      store.setPendingQuestion({
        messageId: assistantMsg.id,
        toolId: tu.id,
        question,
        header,
        options,
        multiSelect,
      })
      assistantMsg.tool_calls = [{
        id: tu.id,
        type: 'function' as const,
        function: {
          name: tu.name,
          arguments: JSON.stringify(tu.input)
        }
      }]
      store.status = 'confirming'
      store.isRunning = false
      cleanupStreamListeners()
      return
    } else if (tu.name === 'save_skill') {
      let validated: SaveSkillInput
      try {
        validated = validateSaveSkillInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const name = validated.name
      const description = validated.description
      const body = validated.body
      try {
        store.status = 'executing'
        const skillStore = useSkillStore()
        await skillStore.saveByAgent(name, description, body)
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Skill saved: ${name}] The user can now invoke it with /${name}.`,
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error saving skill: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'use_skill') {
      let validated: UseSkillInput
      try {
        validated = validateUseSkillInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const name = validated.name
      try {
        const skillStore = useSkillStore()
        const meta = skillStore.skills.find(s => s.name === name)
        if (!meta) throw new Error(`skill "${name}" not found`)
        if (!meta.enabled) throw new Error(`skill "${name}" is disabled`)
        if (!meta.modelInvocable) throw new Error(`skill "${name}" is not model-invocable; the user must run it manually via /${name}`)
        const body = await skillStore.getBody(name)
        const files = await ListSkillFiles(name)
        store.addSkillCard(name, 'auto')
        const manifest = [
          body,
          files.references.length ? `\n\nREFERENCES:\n${files.references.map(f => `- ${f}`).join('\n')}` : '',
          files.scripts.length ? `\n\nSCRIPTS:\n${files.scripts.map(f => `- ${f}`).join('\n')}` : '',
        ].join('')
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(`[Skill loaded: ${name}]\n${manifest}`),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error loading skill: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    } else if (tu.name === 'read_skill_file') {
      let validated: ReadSkillFileInput
      try {
        validated = validateReadSkillFileInput(tu.input)
      } catch (e: any) {
        if (e instanceof InputValidationError) { if (handleInvalidInput(e.message)) continue }
        throw e
      }
      const name = validated.name
      const path = validated.path
      try {
        const content = await GetSkillFile(name, path)
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: capToolResult(`[Skill file: ${name}/${path}]\n${content}`),
          tool_call_id: tu.id
        })
      } catch (e: any) {
        store.addMessage({
          id: `msg-${Date.now()}`,
          role: 'tool',
          content: `[Error reading skill file: ${e.message ?? e}]`,
          tool_call_id: tu.id
        })
      }
    }
  }

  // Max turns reached - prompt user to continue
  if (turnCount >= maxTurns) {
    store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: `已达到最大对话轮次限制（${maxTurns}轮）。点击"继续"或发送任意消息以继续。`,
      needsContinue: true
    })
  }

  cleanupStreamListeners()
  store.isRunning = false
  store.doSave()
}

export async function continueAgent() {
  const store = useAIStore()
  const lastMsg = store.messages[store.messages.length - 1]
  if (lastMsg?.needsContinue) {
    store.messages.pop()
  }
  await runAgent('')
}

export async function approveTool(_messageId: string) {
  const store = useAIStore()
  const cmd = store.pendingCommand
  if (!cmd) return

  if (!hasActiveSession()) {
    store.clearPendingCommand()
    return
  }

  store.clearPendingCommand()
  store.isRunning = true
  store.status = 'executing'

  try {
    if (cmd.toolName === 'start_command') {
      const result = await startCommand(cmd.command)
      store.addMessage({
        id: `msg-${Date.now()}`,
        role: 'tool',
        content: capToolResult(result.output || '(command started)'),
        tool_call_id: cmd.toolId
      })
    } else {
      const result = await executeCommand(cmd.command)
      store.addMessage({
        id: `msg-${Date.now()}`,
        role: 'tool',
        content: capToolResult(formatExecuteResult(result)),
        tool_call_id: cmd.toolId
      })
    }
  } catch (e: any) {
    store.addMessage({
      id: `msg-${Date.now()}`,
      role: 'tool',
      content: `[Error executing command: ${e.message ?? e}]`,
      tool_call_id: cmd.toolId
    })
  }
  await runAgent('')
}

export function rejectTool(_messageId: string) {
  const store = useAIStore()
  const cmd = store.pendingCommand
  if (!cmd) return

  store.clearPendingCommand()

  store.addMessage({
    id: `msg-${Date.now()}`,
    role: 'tool',
    content: 'User rejected this command.',
    tool_call_id: cmd.toolId
  })

  setTimeout(() => runAgent(''), 0)
}

export function answerQuestion(selectedLabels: string[], customText?: string) {
  const store = useAIStore()
  const q = store.pendingQuestion
  if (!q) return

  store.clearPendingQuestion()

  let answer: string
  if (customText !== undefined && customText.trim() !== '') {
    answer = `User chose "Other": ${customText.trim()}`
  } else if (q.multiSelect && selectedLabels.length > 1) {
    answer = `User selected: ${selectedLabels.join(', ')}`
  } else {
    answer = `User chose: ${selectedLabels[0]}`
  }

  store.addMessage({
    id: `msg-${Date.now()}`,
    role: 'tool',
    content: answer,
    tool_call_id: q.toolId
  })

  setTimeout(() => runAgent(''), 0)
}

export function dismissQuestion() {
  const store = useAIStore()
  const q = store.pendingQuestion
  if (!q) return

  store.clearPendingQuestion()

  store.addMessage({
    id: `msg-${Date.now()}`,
    role: 'tool',
    content: 'User dismissed this question.',
    tool_call_id: q.toolId
  })

  setTimeout(() => runAgent(''), 0)
}
