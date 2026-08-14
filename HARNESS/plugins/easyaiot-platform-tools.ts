/**
 * EasyAIoT 平台 Tool 插件 — 供 DeepSeek Harness Agent 调用
 */
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'easyaiot-platform-tools'
export const inject = ['tools'] as const

const MODULES: Record<string, string> = {
  WEB: 'Web 管控台（Vue），默认 :8888',
  DEVICE: 'Java 设备平台（Gateway :48080），物模型 / MQTT / 规则链',
  AI: 'Python AI 服务（:5000），模型训练 / 推理 / LLM',
  VIDEO: 'Python 视频服务（:6000），摄像头 / 算法任务 / 告警',
  RTC: '消费级摄像头 P2P 桥接（go2rtc，:6100）',
  RUNTIME: 'C++ 高速执行层，拉流解码 YOLO 推理',
  EDGE: 'C# 边缘采集运行时，Modbus / OPC UA',
  NODE: 'Go 协议网关 / 节点 Agent',
  TRANSFORM: '多向业务流转（:48096），对接 MES/ERP 等',
  PANEL: '运维控制台（:9200），装机 / 容器 / 诊断',
  IDEA: '社区在线 IDE（:9300），code-server + Copilot',
  HARNESS: '本模块 — DeepSeek Harness Agent（:3080）',
  VISUALIZE: '可视化大屏编辑器（:8002）',
  COMPILE: '多平台打包交付',
}

function gatewayBase(): string {
  return (process.env.EASYAIOT_GATEWAY_URL || 'http://host.docker.internal:48080').replace(/\/$/, '')
}

async function fetchJson(url: string, signal: AbortSignal): Promise<{ ok: boolean; status: number; data: unknown }> {
  const resp = await fetch(url, { signal })
  let data: unknown = null
  const text = await resp.text()
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  return { ok: resp.ok, status: resp.status, data }
}

function healthOutputSchema() {
  return {
    type: 'object' as const,
    additionalProperties: false as const,
    properties: {
      url: { type: 'string' as const },
      ok: { type: 'boolean' as const },
      status: { type: 'number' as const },
      body: { type: 'string' as const, description: 'Response body JSON string' },
    },
  }
}

export function apply(ctx: Context) {
  ctx.tools.register(
    defineTool({
      name: 'easyaiot_gateway_health',
      description: '检查 EasyAIoT DEVICE Gateway 健康状态（Spring Actuator /actuator/health）。',
      parameters: {},
      output: {
        schema: healthOutputSchema(),
        render: (_args, value) => [
          {
            type: 'text',
            text: `Gateway ${value.url}\nHTTP ${value.status}\n${value.body}`,
          },
        ],
      },
      async execute(_args, exec) {
        const url = `${gatewayBase()}/actuator/health`
        const result = await fetchJson(url, exec.signal)
        return {
          url,
          ok: result.ok,
          status: result.status,
          body: JSON.stringify(result.data, null, 2),
        }
      },
    }),
  )

  ctx.tools.register(
    defineTool({
      name: 'easyaiot_list_modules',
      description: '列出 EasyAIoT 核心模块名称与一句话说明，帮助回答架构与端口问题。',
      parameters: {
        module: {
          type: 'string',
          description: '可选：只返回指定模块（如 WEB、DEVICE、VIDEO）',
        },
      },
      output: {
        schema: {
          type: 'object',
          additionalProperties: false,
          properties: {
            modules: {
              type: 'array',
              items: {
                type: 'object',
                additionalProperties: false,
                properties: {
                  name: { type: 'string' },
                  summary: { type: 'string' },
                },
              },
            },
          },
        },
        render: (_args, value) => [
          {
            type: 'text',
            text: value.modules.map((m: { name: string; summary: string }) => `- **${m.name}**: ${m.summary}`).join('\n'),
          },
        ],
      },
      async execute(args) {
        const filter = typeof args.module === 'string' ? args.module.trim().toUpperCase() : ''
        const entries = Object.entries(MODULES)
          .filter(([key]) => !filter || key === filter)
          .map(([name, summary]) => ({ name, summary }))
        return { modules: entries }
      },
    }),
  )

  ctx.tools.register(
    defineTool({
      name: 'easyaiot_service_health',
      description: '检查 EasyAIoT 指定后端服务健康（gateway / ai / video / rtc）。',
      parameters: {
        service: {
          type: 'string',
          required: true,
          description: '服务名：gateway | ai | video | rtc',
        },
      },
      output: {
        schema: {
          type: 'object',
          additionalProperties: false,
          properties: {
            service: { type: 'string' },
            url: { type: 'string' },
            ok: { type: 'boolean' },
            status: { type: 'number' },
            body: { type: 'string' },
          },
        },
        render: (_args, value) => [
          {
            type: 'text',
            text: `[${value.service}] ${value.url}\nHTTP ${value.status}\n${value.body}`,
          },
        ],
      },
      async execute(args, exec) {
        const key = String(args.service || '').trim().toLowerCase()
        const host = 'host.docker.internal'
        const map: Record<string, string> = {
          gateway: `${gatewayBase()}/actuator/health`,
          ai: `http://${host}:5000/actuator/health`,
          video: `http://${host}:6000/actuator/health`,
          rtc: `http://${host}:6100/actuator/health`,
        }
        const url = map[key]
        if (!url) {
          throw new Error(`unknown service: ${args.service}. use gateway|ai|video|rtc`)
        }
        const result = await fetchJson(url, exec.signal)
        return {
          service: key,
          url,
          ok: result.ok,
          status: result.status,
          body: JSON.stringify(result.data, null, 2),
        }
      },
    }),
  )

  console.log('[easyaiot-platform-tools] registered easyaiot_gateway_health, easyaiot_list_modules, easyaiot_service_health')
}
