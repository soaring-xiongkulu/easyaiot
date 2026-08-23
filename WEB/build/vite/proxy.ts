/**
 * Used to parse the .env.development proxy configuration
 * Node-RED 代理规则对齐 WEB/conf/nginx.conf：
 *   location ^~ /dev-api/nodeRed/  → rewrite 去掉前缀 → 1880
 *   location ^~ /nodeRed           → rewrite 去掉前缀 → 1880
 */
import type { ProxyOptions } from 'vite'

type ProxyItem = [string, string]

type ProxyList = ProxyItem[]

type ProxyTargetList = Record<string, ProxyOptions>

const httpsRE = /^https:\/\//

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Generate proxy
 * @param list
 */
export function createProxy(list: ProxyList = []) {
  const ret: ProxyTargetList = {}
  for (const [prefix, target] of list) {
    const isHttps = httpsRE.test(target)
    const isNodeRed
      = prefix === '/dev-api/nodeRed'
        || prefix === '/nodeRed'
        || prefix.endsWith('/nodeRed')

    // https://github.com/http-party/node-http-proxy#options
    ret[prefix] = {
      target,
      changeOrigin: true,
      ws: true,
      // 与 nginx rewrite 一致：剥前缀后若为空则落到 /
      rewrite: (path) => {
        const next = path.replace(new RegExp(`^${escapeRegExp(prefix)}`), '')
        return next.length > 0 ? next : '/'
      },
      ...(isHttps ? { secure: false } : {}),
      ...(isNodeRed
        ? {
            // Node-RED 编辑器 / 管理 API 常带长连接与 WebSocket
            configure: (proxy) => {
              proxy.on('proxyRes', (proxyRes) => {
                // 允许被同源 iframe 嵌入（对齐 nginx 部署体验）
                delete proxyRes.headers['x-frame-options']
                const csp = proxyRes.headers['content-security-policy']
                if (typeof csp === 'string' && /frame-ancestors/i.test(csp)) {
                  proxyRes.headers['content-security-policy'] = csp
                    .replace(/frame-ancestors[^;]*;?/gi, '')
                    .trim()
                }
              })
            },
          }
        : {}),
    }
  }
  return ret
}
