import { ChatCompletion } from '../../bindings/easyaiot/terminal/app'
import { Events } from '@wailsio/runtime'
import { useSettingsStore } from '../stores/settingsStore'

export interface ChatOptions {
  system: string
  messages: Array<Record<string, unknown>>
  tools?: Array<{
    name: string
    description: string
    input_schema: object
  }>
  onChunk?: (chunk: string) => void
  onToolUse?: (tool: { id: string; name: string; input: Record<string, unknown> }) => void
}

export class ChatCancelledError extends Error {
  constructor() {
    super('Chat was cancelled by user')
    this.name = 'ChatCancelledError'
  }
}

export class ChatTimeoutError extends Error {
  constructor() {
    super('Chat request timed out')
    this.name = 'ChatTimeoutError'
  }
}

function isCancellationError(raw: string): boolean {
  const lower = raw.toLowerCase()
  return lower.includes('context canceled') || lower.includes('context cancelled')
}

function formatAPIError(raw: string): string {
  // Parse Go backend error format: "HTTP <code>: <json body>"
  const match = raw.match(/^HTTP\s+(\d+):\s*(.+)/)
  if (!match) return `API Error: ${raw}`

  const code = match[1]
  const bodyStr = match[2]
  try {
    const body = JSON.parse(bodyStr)
    const msg = body?.error?.message || body?.message || bodyStr
    return `API Error: ${code} ${msg}`
  } catch {
    return `API Error: ${code} ${bodyStr}`
  }
}

export async function chat(options: ChatOptions): Promise<void> {
  const settingsStore = useSettingsStore()
  const activeModel = settingsStore.activeModel

  const apiKey = activeModel?.apiKey || ''
  const baseURL = activeModel?.baseURL || ''
  const model = activeModel?.model || ''
  const protocol = activeModel?.protocol || 'anthropic'
  const userAgent = activeModel?.userAgent || ''
  const proxyId = activeModel?.proxyId || ''

  if (!apiKey) throw new Error('API key not configured')

  const requestBody: Record<string, unknown> = {
    model,
    max_tokens: 16384,
    system: options.system,
    messages: options.messages,
    tools: options.tools,
  }

  const requestJSON = JSON.stringify(requestBody)

  let responseText: string
  // Streamed tokens are emitted via Wails events. Some protocol paths (notably
  // OpenAI before the text-buffer flush fix) returned empty content[].text in
  // the final JSON while still emitting ai:token — so callers that only read
  // onChunk from the final payload (DB/Mongo assistants) saw empty results.
  // Accumulate tokens as a fallback; do NOT forward them to onChunk here (the
  // agent already listens to ai:token and would double-append).
  let streamedText = ''
  const unsubToken =Events.On('ai:token', (ev) => { const data: any = ev.data; 
    const text = typeof data === 'string' ? data : (data?.text ?? data?.Text ?? '')
    if (text) streamedText += text
   })
  try {
    responseText = await ChatCompletion(apiKey, baseURL, model, requestJSON, protocol, userAgent, proxyId)
  } catch (e: any) {
    const raw = e?.message || String(e)
    if (isCancellationError(raw)) {
      throw new ChatCancelledError()
    }
    if (raw.includes('AI_REQUEST_TIMEOUT')) {
      throw new ChatTimeoutError()
    }
    throw new Error(formatAPIError(raw))
  } finally {
    unsubToken?.()
  }

  let json: any
  try {
    json = JSON.parse(responseText)
  } catch (e: any) {
    throw new Error(`Failed to parse LLM response: ${e.message}`)
  }

  if (json.error) {
    const errMsg = json.error.message || JSON.stringify(json.error)
    throw new Error(`LLM API error: ${errMsg}`)
  }

  const rawContent = json.content
  if (!Array.isArray(rawContent)) {
    throw new Error('Unexpected Anthropic response: content is not an array')
  }

  // Store raw message for history preservation
  ;(options as any)._rawApiMsg = {
    role: json.role || 'assistant',
    content: rawContent
  }

  // Dispatch text and tool_use blocks.
  let finalText = ''
  for (const block of rawContent) {
    switch (block.type) {
      case 'text':
        finalText += block.text || ''
        break
      case 'tool_use':
        options.onToolUse?.({
          id: block.id,
          name: block.name,
          input: block.input || {}
        })
        break
    }
  }
  const textOut = finalText || streamedText
  if (textOut) {
    options.onChunk?.(textOut)
  }
}

export const AVAILABLE_TOOLS = [
  {
    name: 'execute_command',
    description: 'Execute a shell command in the active terminal session and return its output. You MUST classify every command with a risk level. Use "timeout" to control how long to wait — short commands need less time, long tasks (builds, installs) need more.',
    input_schema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The shell command to execute. Use syntax appropriate for the current shell (provided in context).'
        },
        risk: {
          type: 'string',
          enum: ['read', 'write', 'dangerous'],
          description: 'The risk level of this command:\n- "read": only inspects/views data, absolutely no modifications (e.g. ls, cat, grep, head, tail, df, du, ps, top, find, pwd, whoami, git status, git log, docker ps, npm list)\n- "write": modifies or creates data but not system-destructive (e.g. echo > file, touch, mkdir, cp, mv, git commit, curl POST, npm install, pip install)\n- "dangerous": potentially destructive or system-altering (e.g. rm, > overwrite, chmod, chown, shutdown, mkfs, dd, reboot, force push)'
        },
        timeout: {
          type: 'number',
          description: 'Maximum seconds to wait for command completion. Default 60s. Use 5-10s for quick commands (ls, cat, pwd), 30-60s for moderate tasks, 120-300s for long tasks (npm install, docker build, git clone). NEVER set below 5s.'
        },
        head_lines: {
          type: 'number',
          description: 'Number of lines to keep from the START of output when truncation occurs. Default 50. Increase to see more of the beginning.'
        },
        tail_lines: {
          type: 'number',
          description: 'Number of lines to keep from the END of output when truncation occurs. Default 300. Increase to see more recent output (errors usually at the end).'
        },
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      },
      required: ['command', 'risk']
    }
  },
  {
    name: 'start_command',
    description: 'Start a background/long-running command and return its initial output (first 3 seconds). Use this for servers (npm run dev, redis-server, python -m http.server) or any command you do NOT want to wait for. You MUST classify every command with a risk level.',
    input_schema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The shell command to start. It will keep running after this tool returns.'
        },
        risk: {
          type: 'string',
          enum: ['read', 'write', 'dangerous'],
          description: 'The risk level of this command:\n- "read": only inspects/views data, absolutely no modifications\n- "write": modifies or creates data but not system-destructive\n- "dangerous": potentially destructive or system-altering'
        },
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      },
      required: ['command', 'risk']
    }
  },
  {
    name: 'capture_terminal',
    description: 'Take an instant snapshot of the terminal screen. Use this to check what is currently visible without running any command. Useful after a command times out or returns, to see if the shell prompt is back or to read error messages on screen.',
    input_schema: {
      type: 'object',
      properties: {
        tail_lines: {
          type: 'number',
          description: 'Lines from the bottom of the buffer. Default 200. Increase to see more of the recent output.'
        },
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      }
    }
  },
  {
    name: 'collect_output',
    description: 'Wait and collect terminal output WITHOUT sending any command or text to the terminal. Pure passive listening. Use this when a command is still running and you want to wait for more output. You can call this repeatedly to wait in stages.',
    input_schema: {
      type: 'object',
      properties: {
        timeout: {
          type: 'number',
          description: 'Seconds to wait. Default 30s. Use 15-30s for active progress checks, 60-120s for slower operations.'
        },
        head_lines: {
          type: 'number',
          description: 'Head lines to keep on truncation. Default 100.'
        },
        tail_lines: {
          type: 'number',
          description: 'Tail lines to keep on truncation. Default 300.'
        },
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      }
    }
  },
  {
    name: 'send_terminal_key',
    description: 'Send text or a control character to the active terminal. Use this ONLY when you can SEE an interactive prompt in the output (password request, y/n confirmation, etc.). NEVER guess that a prompt is there.',
    input_schema: {
      type: 'object',
      properties: {
        input: {
          type: 'string',
          description: 'Text to send to the terminal (e.g., a password, "y" for confirmation, or a command fragment).'
        },
        control: {
          type: 'string',
          enum: ['ctrl_c', 'ctrl_d', 'enter'],
          description: 'Send a control character instead of text. "ctrl_c" interrupts/cancels the running command. "ctrl_d" sends EOF. "enter" sends a newline/Enter key.'
        },
        send_enter: {
          type: 'boolean',
          description: 'Whether to send an Enter/Return key after the input text to submit it. Default true. Set to false only when you need to send partial input without submitting (e.g., typing a password character by character). Ignored when using control.'
        },
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      }
    }
  },
  {
    name: 'interrupt_command',
    description: 'Send Ctrl+C to cancel the currently running command. Use this when a command is stuck, hanging, or needs to be stopped before running a different command.',
    input_schema: {
      type: 'object',
      properties: {
        panel: {
          type: 'string',
          description: 'Target panel by its title. Use the exact title from AVAILABLE PANELS in context. Omit to use the default panel.'
        }
      }
    }
  },
  {
    name: 'ask_user',
    description: 'Ask the user a question with predefined options. Use this when you need the user to make a choice, confirm an action, or provide input. The user can select from your options or type a custom answer via the always-present "Other" option.',
    input_schema: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'The question to ask the user. Be clear and specific. End with a question mark.'
        },
        header: {
          type: 'string',
          description: 'Short label displayed as a chip/tag, max 12 chars. Examples: "Auth method", "Library", "Approach".'
        },
        options: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              label: {
                type: 'string',
                description: 'Display text for this option. Concise, 1-5 words.'
              },
              description: {
                type: 'string',
                description: 'Explanation of what this option means or what will happen if chosen.'
              }
            },
            required: ['label', 'description']
          },
          minItems: 2,
          maxItems: 4,
          description: 'Available choices. 2-4 options. An "Other" option is always appended automatically for custom answers.'
        },
        multiSelect: {
          type: 'boolean',
          description: 'Set to true to allow the user to select multiple options. Default false.'
        }
      },
      required: ['question', 'options']
    }
  },
  {
    name: 'save_skill',
    description: 'Create or update a reusable skill (a command-line workflow / SOP) so it can be invoked later via /name. Use this when the user asks to save the current approach as a skill, or when you and the user just worked out a repeatable command-line procedure worth keeping. Write a thin skill: only include steps the model would NOT do by default, use imperative steps, state clearly in the description what it does AND when to use it. Locked skills cannot be overwritten.',
    input_schema: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Skill identifier in kebab-case (lowercase letters, digits, hyphens), e.g. "git-clean-branches". This becomes the /trigger.'
        },
        description: {
          type: 'string',
          description: 'One line: what the skill does AND when to use it (drives matching). E.g. "Clean up merged local git branches. Use when the user wants to delete/tidy git branches."'
        },
        body: {
          type: 'string',
          description: 'The skill instructions as markdown (imperative steps). Do NOT include YAML frontmatter — name/description are passed separately.'
        }
      },
      required: ['name', 'description', 'body']
    }
  },
  {
    name: 'use_skill',
    description: 'Load the full instructions (body) of an available skill, plus a manifest of its bundled reference docs and scripts. Call this when a skill from AVAILABLE SKILLS matches the current task, BEFORE acting on it. Scripts are returned as text; to run one, read it with read_skill_file then execute it via execute_command in the target terminal.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'The skill name from AVAILABLE SKILLS (without the leading /).' }
      },
      required: ['name']
    }
  },
  {
    name: 'read_skill_file',
    description: 'Read a single bundled file of a skill (a reference doc or a script) as text. Use after use_skill to fetch a specific file listed in its manifest.',
    input_schema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'The skill name.' },
        path: { type: 'string', description: 'Relative path inside the skill dir, as listed by use_skill (e.g. "references/guide.md" or "scripts/check.sh").' }
      },
      required: ['name', 'path']
    }
  }
]
