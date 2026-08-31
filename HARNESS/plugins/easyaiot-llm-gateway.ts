/**
 * EasyAIoT LLM 统一网关 — 平台页面与 Agent 的模型调用统一收口。
 *
 * - ctx.effect 自起 HTTP server（监听 127.0.0.1:${LLM_GATEWAY_PORT:-3082}，由入口 socat 转发），
 *   不依赖 dsh 内部路由 API，规避 Developer Preview 版本变化风险；
 * - 模型配置来自平台 AI 模块「当前启用模型」（EASYAIOT_GATEWAY_URL），启动拉取 + 30s 轮询；
 * - 全部转发走 OpenAI 兼容协议 /chat/completions；API Key 仅驻内存，不落盘、不打日志。
 */
import type { Context } from '@deepseek-ai/cordis'
import http from 'node:http'
import { Readable } from 'node:stream'

export const name = 'easyaiot-llm-gateway'
export const inject = [] as const

interface ActiveModelConfig {
  id: number
  name: string
  model_name: string
  base_url: string
  api_key: string
  temperature: number
  max_tokens: number
  timeout: number
}

const POLL_INTERVAL_MS = 30_000
// 调用时缓存超过该时长则先重新拉取（覆盖「管理员切换模型后立即生效」，无需等轮询）
const REVALIDATE_MS = 15_000
const REQUEST_TIMEOUT_MS = 300_000

// 与平台 AI 模块 enhance_prompt 保持一致的模式提示词模板（media 取决于 files 中的类型）
const VISION_PROMPT_BY_MODE: Record<string, string> = {
  inference: '作为视觉推理专家，请分析这张图片：{prompt}',
  understanding: '作为视觉理解专家，请深入理解这张图片：{prompt}',
  'deep-thinking': '作为深度思考专家，请对这张图片进行多角度深度分析：{prompt}',
}
const VIDEO_PROMPT_BY_MODE: Record<string, string> = {
  inference: '作为视觉推理专家，请分析这个视频：{prompt}',
  understanding: '{prompt}',
  'deep-thinking': '作为深度思考专家，请对这段视频进行多角度深度分析：{prompt}',
}

function gatewayBase(): string {
  return (process.env.EASYAIOT_GATEWAY_URL || 'http://host.docker.internal:48080').replace(/\/$/, '')
}

function gatewayPort(): number {
  const port = Number.parseInt(process.env.LLM_GATEWAY_PORT || '3082', 10)
  return Number.isFinite(port) && port > 0 ? port : 3082
}

/** 与平台侧 build_chat_url 一致：兼容 /v1 结尾、/v4 等版本段、完整路径三种写法 */
function buildUpstreamUrl(baseUrl: string): string {
  let url = (baseUrl || '').trim().replace(/\/+$/, '')
  if (url.endsWith('/chat/completions'))
    return url
  if (/\/v\d+$/.test(url) || url.includes('/v1'))
    return `${url}/chat/completions`
  return `${url}/v1/chat/completions`
}

export function apply(ctx: Context) {
  // 父进程退出导致 stdout 管道断裂（EPIPE）时保持存活，不抛未捕获错误
  process.stdout.on('error', () => {})
  process.stderr.on('error', () => {})
  const token = (process.env.LLM_GATEWAY_TOKEN || '').trim()
  let cache: { model: ActiveModelConfig | null; fetchedAt: number; lastError: string } = {
    model: null,
    fetchedAt: 0,
    lastError: '',
  }

  async function fetchActiveModel(): Promise<void> {
    // 专用配置端点：列表接口的 api_key 是脱敏的，此处返回完整配置
    const url = `${gatewayBase()}/model/llm/active-config`
    try {
      const resp = await fetch(url, { signal: AbortSignal.timeout(10_000) })
      const body = await resp.json() as any
      const item = body?.data
      if (body?.code === 0 && item) {
        cache = {
          model: {
            id: item.id,
            name: item.name,
            model_name: item.model_name,
            base_url: item.base_url,
            api_key: item.api_key || '',
            temperature: item.temperature ?? 0.7,
            max_tokens: item.max_tokens ?? 2000,
            timeout: (item.timeout ?? 60) * 1000,
          },
          fetchedAt: Date.now(),
          lastError: '',
        }
        console.log(`[easyaiot-llm-gateway] 配置已加载: 模型 id=${item.id}（${item.model_name}）`)
      }
      else {
        cache = { ...cache, model: null, fetchedAt: Date.now(), lastError: `平台无启用模型 (code=${body?.code})` }
      }
    }
    catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      cache = { ...cache, fetchedAt: Date.now(), lastError: msg }
      console.warn(`[easyaiot-llm-gateway] 拉取启用模型失败（沿用旧缓存）: ${msg}`)
    }
  }

  function authorized(req: http.IncomingMessage): boolean {
    if (!token)
      return false // 未配置 token 时拒绝所有 API 请求（health 除外）
    const header = req.headers.authorization || ''
    const bearer = header.startsWith('Bearer ') ? header.slice(7) : ''
    const alt = (req.headers['x-llm-token'] as string | undefined) || ''
    return bearer === token || alt === token
  }

  function cors(res: http.ServerResponse): void {
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-LLM-Token')
  }

  function sendJson(res: http.ServerResponse, status: number, body: unknown): void {
    const payload = JSON.stringify(body)
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(payload)
  }

  function readBody(req: http.IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = []
      let size = 0
      req.on('data', (chunk: Buffer) => {
        size += chunk.length
        if (size > 64 * 1024 * 1024) {
          reject(new Error('request body too large'))
          req.destroy()
          return
        }
        chunks.push(chunk)
      })
      req.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')))
      req.on('error', reject)
    })
  }

  interface ForwardOptions {
    stream: boolean
    temperature?: number
    max_tokens?: number
    messages?: unknown
  }

  async function forward(model: ActiveModelConfig, options: ForwardOptions): Promise<{ response: Response; errorText?: string }> {
    // 厂商参数差异自动降级重试（顺序：temperature→1 为 KIMI K2 等强制要求；max_tokens→max_completion_tokens 为 OpenAI gpt-5.x 等）
    let useMaxCompletionTokens = false
    let temperature = options.temperature ?? model.temperature
    const build = () => {
      const payload: Record<string, unknown> = {
        model: model.model_name,
        messages: options.messages,
        stream: options.stream,
        temperature,
      }
      const mt = options.max_tokens ?? model.max_tokens
      if (useMaxCompletionTokens)
        payload.max_completion_tokens = mt
      else
        payload.max_tokens = mt
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (model.api_key)
        headers.Authorization = `Bearer ${model.api_key}`
      return fetch(buildUpstreamUrl(model.base_url), {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      })
    }

    let resp = await build()
    if (!resp.ok) {
      const text = await resp.text().catch(() => '')
      let retried = false
      if (text.includes('temperature') && text.includes('only 1 is allowed')) {
        console.warn(`[easyaiot-llm-gateway] 厂商要求 temperature 必须为 1，自动降级重试: ${text.slice(0, 120)}`)
        temperature = 1
        retried = true
      }
      else if (text.includes('max_tokens') && text.includes('max_completion_tokens')) {
        console.warn(`[easyaiot-llm-gateway] 厂商不支持 max_tokens，改用 max_completion_tokens 重试: ${text.slice(0, 120)}`)
        useMaxCompletionTokens = true
        retried = true
      }
      if (!retried)
        return { response: resp, errorText: text }
      resp = await build()
      if (resp.ok)
        return { response: resp }
      const text2 = await resp.text().catch(() => '')
      return { response: resp, errorText: text2 }
    }
    return { response: resp }
  }

  async function requireModel(res: http.ServerResponse): Promise<ActiveModelConfig | null> {
    // 设计策略：无配置、上次拉取失败、或缓存超过 REVALIDATE_MS 时，调用现场立即重拉一次
    if (!cache.model || cache.lastError || Date.now() - cache.fetchedAt > REVALIDATE_MS) {
      await fetchActiveModel()
    }
    if (!cache.model) {
      sendJson(res, 502, {
        error: { message: '平台未启用任何大模型或配置尚未拉取成功', type: 'no_active_model', code: cache.lastError },
      })
      return null
    }
    return cache.model
  }

  const server = http.createServer(async (req, res) => {
    const start = Date.now()
    const path = (req.url || '/').split('?')[0]
    cors(res)
    res.setHeader('X-LLM-Active-Model', cache.model?.model_name ?? '')

    const audit = (status: number) => {
      console.log(`[easyaiot-llm-gateway] ${req.method} ${path} -> ${status} (${Date.now() - start}ms) model=${cache.model?.model_name ?? '-'}`)
    }

    if (req.method === 'OPTIONS') {
      res.writeHead(204)
      res.end()
      return
    }

    if (path === '/api/llm/health') {
      sendJson(res, 200, {
        ok: true,
        model: cache.model?.model_name ?? null,
        model_name: cache.model?.name ?? null,
        fetched_at: cache.fetchedAt ? new Date(cache.fetchedAt).toISOString() : null,
        stale: cache.lastError ? true : Date.now() - cache.fetchedAt > POLL_INTERVAL_MS * 3,
        last_error: cache.lastError || null,
      })
      return
    }

    if (!authorized(req)) {
      audit(401)
      sendJson(res, token ? 401 : 503, {
        error: {
          message: token ? 'Unauthorized: missing or invalid LLM gateway token' : 'LLM_GATEWAY_TOKEN 未配置，网关拒绝服务',
          type: 'unauthorized',
        },
      })
      return
    }

    try {
      // OpenAI SDK 的 client.models.list() 会请求 GET /models（baseURL 为 /v1 时）；两条路径都返回 OpenAI 风格列表
      if (req.method === 'GET' && (path === '/api/llm/v1/models' || path === '/v1/models' || path === '/models')) {
        const model = await requireModel(res)
        if (!model) {
          audit(502)
          return
        }
        audit(200)
        sendJson(res, 200, { object: 'list', data: [{ id: model.model_name, object: 'model', owned_by: 'easyaiot' }] })
        return
      }

      if (req.method !== 'POST') {
        audit(404)
        sendJson(res, 404, { error: { message: `Not found: ${req.method} ${path}` } })
        return
      }

      const model = await requireModel(res)
      if (!model) {
        audit(502)
        return
      }

      const raw = await readBody(req)
      let body: any = {}
      try {
        body = raw ? JSON.parse(raw) : {}
      }
      catch {
        audit(400)
        sendJson(res, 400, { error: { message: 'Invalid JSON body' } })
        return
      }

      // 平台语义简版：{prompt, mode?, files?, stream?} → 组装多模态 messages
      if (path === '/api/llm/chat') {
        const prompt = (body.prompt || '').trim()
        if (!prompt) {
          audit(400)
          sendJson(res, 400, { code: 400, msg: 'prompt 不能为空' })
          return
        }
        const files: Array<{ type?: string, url?: string }> = Array.isArray(body.files) ? body.files : []
        const mediaParts: unknown[] = []
        let hasVideo = false
        for (const f of files) {
          const type = (f.type || 'image').toLowerCase()
          const url = f.url || ''
          if (!url)
            continue
          if (type === 'video') {
            hasVideo = true
            mediaParts.push({ type: 'video_url', video_url: { url } })
          }
          else {
            mediaParts.push({ type: 'image_url', image_url: { url } })
          }
        }
        const mode = typeof body.mode === 'string' ? body.mode : ''
        const table = hasVideo ? VIDEO_PROMPT_BY_MODE : VISION_PROMPT_BY_MODE
        const finalPrompt = mode ? (table[mode] || '{prompt}').replaceAll('{prompt}', prompt) : prompt
        body.messages = mediaParts.length
          ? [{ role: 'user', content: [{ type: 'text', text: finalPrompt }, ...mediaParts] }]
          : [{ role: 'user', content: finalPrompt }]
      }

      if (!Array.isArray(body.messages) || !body.messages.length) {
        audit(400)
        sendJson(res, 400, { error: { message: 'messages is required' } })
        return
      }

      const stream = body.stream === true
      const { response: upstream, errorText } = await forward(model, {
        stream,
        temperature: body.temperature,
        max_tokens: body.max_tokens,
        messages: body.messages,
      })

      if (!upstream.ok || !upstream.body) {
        const errText = errorText ?? await upstream.text().catch(() => '')
        audit(upstream.status)
        sendJson(res, upstream.status || 502, {
          error: { message: `厂商端点返回 ${upstream.status}`, type: 'upstream_error', detail: errText.slice(0, 2000) },
        })
        return
      }

      if (stream) {
        // SSE 透传（厂商响应本身即 OpenAI 兼容流）
        res.writeHead(200, {
          'Content-Type': 'text/event-stream; charset=utf-8',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
          'X-Accel-Buffering': 'no',
        })
        const nodeStream = Readable.fromWeb(upstream.body as any)
        nodeStream.on('end', () => audit(200))
        nodeStream.pipe(res)
        return
      }

      const result = await upstream.json() as any
      audit(200)
      if (path === '/api/llm/chat') {
        // 平台语义包装
        const text = result?.choices?.[0]?.message?.content ?? ''
        sendJson(res, 200, { code: 0, msg: 'success', data: { response: text, usage: result?.usage ?? null, model: model.model_name } })
      }
      else {
        sendJson(res, 200, result)
      }
    }
    catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      audit(502)
      sendJson(res, 502, { error: { message: `网关转发失败: ${msg}`, type: 'gateway_error' } })
    }
  })

  ctx.effect(() => {
    server.listen(gatewayPort(), '127.0.0.1', () => {
      console.log(`[easyaiot-llm-gateway] listening 127.0.0.1:${gatewayPort()} (auth=${token ? 'token' : 'DISABLED — 请配置 LLM_GATEWAY_TOKEN'})`)
    })
    void fetchActiveModel()
    const timer = setInterval(() => void fetchActiveModel(), POLL_INTERVAL_MS)
    return () => {
      clearInterval(timer)
      server.close()
    }
  })
}
