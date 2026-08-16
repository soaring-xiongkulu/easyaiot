#!/usr/bin/env node
/**
 * IDEA / 本地开发：HTTPS + HTTP/2 启动 Vite。
 *
 * 浏览器对 HTTP/2 会把同 origin 的多路 /live FLV 复用到一条连接上，
 * 不再受 HTTP/1.1「每域名约 6 路」限制。
 *
 * 用法（IDEA Run 配置 / pnpm serve）：
 *   pnpm dev:http2
 * 浏览器打开（首次需信任自签证书）：
 *   https://localhost:<VITE_PORT>/
 *
 * 普通 `pnpm dev` 仍是 HTTP/1.1，继续用 127.0.0.x 连接池兜底。
 *
 * HMR：挂在同一 HTTPS 端口（WSS / HTTP/1.1 upgrade）。UnoCSS 依赖 HMR
 * 把扫描到的 utility 推到浏览器；关掉 HMR 会导致登录页等布局「裸奔」。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createSecureServer } from 'node:http2'
import { spawnSync } from 'node:child_process'
import { createServer as createViteServer, loadEnv } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const certDir = path.join(root, 'certs')
const keyPath = path.join(certDir, 'localhost-key.pem')
const certPath = path.join(certDir, 'localhost.pem')

function ensureCerts() {
  if (fs.existsSync(keyPath) && fs.existsSync(certPath)) return
  console.log('[dev-http2] generating self-signed certs...')
  const r = spawnSync(process.execPath, [path.join(__dirname, 'gen-dev-certs.mjs')], {
    cwd: root,
    stdio: 'inherit',
  })
  if (r.status !== 0) process.exit(r.status || 1)
}

ensureCerts()

const mode = 'development'
const env = loadEnv(mode, root, '')
const port = Number(env.VITE_PORT || process.env.VITE_PORT || 8888)
const tls = {
  key: fs.readFileSync(keyPath),
  cert: fs.readFileSync(certPath),
}

/**
 * Node HTTP/2 兼容层会把 :path/:authority 等伪头挂在 req.headers 上；
 * Vite 的 http-proxy 按 HTTP/1.1 原样转发时会报
 * "Header name must be a valid HTTP token [\":path\"]"。
 *
 * 不能直接 delete :path（req.url 依赖它），改为覆盖 headers 视图。
 */
function sanitizeHttp2Request(req) {
  const src = req.headers
  if (!src) return
  const cleaned = Object.create(null)
  for (const key of Object.keys(src)) {
    if (key.startsWith(':')) continue
    cleaned[key] = src[key]
  }
  if (!cleaned.host && src[':authority']) {
    cleaned.host = src[':authority']
  }
  Object.defineProperty(req, 'headers', {
    value: cleaned,
    writable: true,
    configurable: true,
    enumerable: true,
  })
}

/** HTTP/2 禁止回写 Connection / Transfer-Encoding 等 hop-by-hop 头 */
const HOP_BY_HOP = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'proxy-connection',
  'te',
  'trailers',
  'transfer-encoding',
  'upgrade',
  'http2-settings',
])

function sanitizeHttp2Response(res) {
  // HTTP/2 无 status message（RFC7540 8.1.2.4）
  try {
    res.statusMessage = ''
  } catch {
    /* ignore */
  }

  const setHeader = res.setHeader.bind(res)
  res.setHeader = (name, value) => {
    if (HOP_BY_HOP.has(String(name).toLowerCase())) return res
    try {
      return setHeader(name, value)
    } catch (err) {
      if (err && err.code === 'ERR_HTTP2_INVALID_CONNECTION_HEADERS') return res
      throw err
    }
  }

  const writeHead = res.writeHead.bind(res)
  res.writeHead = (statusCode, reasonOrHeaders, maybeHeaders) => {
    let reason = reasonOrHeaders
    let headers = maybeHeaders
    if (typeof reasonOrHeaders === 'object' && reasonOrHeaders !== null) {
      headers = reasonOrHeaders
      reason = undefined
    }
    if (headers && typeof headers === 'object') {
      for (const key of Object.keys(headers)) {
        if (HOP_BY_HOP.has(key.toLowerCase())) delete headers[key]
      }
    }
    try {
      // 不传 reason，避免 UnsupportedWarning: Status message is not supported by HTTP/2
      return writeHead(statusCode, headers)
    } catch (err) {
      if (err && err.code === 'ERR_HTTP2_INVALID_CONNECTION_HEADERS') {
        return writeHead(statusCode)
      }
      throw err
    }
  }
}

// 先建 server，再交给 Vite 挂 HMR upgrade（同端口 WSS）
const server = createSecureServer({ ...tls, allowHTTP1: true })

const vite = await createViteServer({
  configFile: path.join(root, 'vite.config.ts'),
  root,
  mode,
  appType: 'spa',
  server: {
    middlewareMode: true,
    // 勿设 server.https：会触发 vite-plugin-mkcert；TLS 由外层 http2.createSecureServer 负责
    hmr: {
      server,
      protocol: 'wss',
      host: 'localhost',
      port,
      clientPort: port,
    },
  },
})

server.on('request', (req, res) => {
  sanitizeHttp2Request(req)
  sanitizeHttp2Response(res)
  vite.middlewares(req, res, () => {
    if (!res.writableEnded) {
      res.statusCode = 404
      res.end('Not found')
    }
  })
})

server.listen(port, '0.0.0.0', () => {
  console.log('')
  console.log('[dev-http2] HTTPS + HTTP/2 ready (HMR via WSS on same port)')
  console.log(`  Local:   https://localhost:${port}/`)
  console.log(`  Network: https://<lan-ip>:${port}/`)
  console.log('  Tip: 首次请在浏览器信任自签证书；DevTools → Network 协议列应显示 h2')
  console.log('')
})

server.on('error', (err) => {
  console.error('[dev-http2] listen error:', err)
  if (err && err.code === 'EADDRINUSE') {
    console.error(
      `[dev-http2] 端口 ${port} 已被占用。请先停掉旧的 vite/serve（或: fuser -k ${port}/tcp），再重新运行。`,
    )
  }
  process.exit(1)
})

const shutdown = async () => {
  try {
    await vite.close()
  } catch {
    /* ignore */
  }
  server.close(() => process.exit(0))
}
process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)
