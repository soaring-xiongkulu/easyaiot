#!/usr/bin/env node
/**
 * 生成本机开发 / Docker nginx 用自签证书（localhost / 127.0.0.1）。
 *
 *   node ./scripts/gen-dev-certs.mjs
 *
 * 产出：
 *   WEB/certs/localhost.pem + localhost-key.pem   — IDEA `pnpm dev:http2`
 *   WEB/certs/server.crt + server.key             — 兼容旧文档路径
 *   WEB/conf/ssl/server.crt + server.key          — docker-compose 挂载到 nginx
 */
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const certDir = path.join(root, 'certs')
const sslDir = path.join(root, 'conf', 'ssl')
const keyPath = path.join(certDir, 'localhost-key.pem')
const certPath = path.join(certDir, 'localhost.pem')
const nginxCrt = path.join(certDir, 'server.crt')
const nginxKey = path.join(certDir, 'server.key')
const composeCrt = path.join(sslDir, 'server.crt')
const composeKey = path.join(sslDir, 'server.key')

fs.mkdirSync(certDir, { recursive: true })
fs.mkdirSync(sslDir, { recursive: true })

function syncNginxCopies() {
  fs.copyFileSync(certPath, nginxCrt)
  fs.copyFileSync(keyPath, nginxKey)
  fs.copyFileSync(certPath, composeCrt)
  fs.copyFileSync(keyPath, composeKey)
}

if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
  syncNginxCopies()
  console.log(
    `[gen-dev-certs] already exists, synced nginx copies:\n  ${certPath}\n  ${keyPath}\n  ${composeCrt}\n  ${composeKey}`,
  )
  process.exit(0)
}

const conf = `
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = localhost

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
`

const confPath = path.join(certDir, 'localhost.cnf')
fs.writeFileSync(confPath, conf.trim() + '\n')

try {
  execFileSync(
    'openssl',
    [
      'req',
      '-x509',
      '-nodes',
      '-newkey',
      'rsa:2048',
      '-keyout',
      keyPath,
      '-out',
      certPath,
      '-days',
      '825',
      '-config',
      confPath,
      '-extensions',
      'v3_req',
    ],
    { stdio: 'inherit' },
  )
} catch (e) {
  console.error('[gen-dev-certs] openssl failed. Please install openssl.')
  process.exit(1)
}

syncNginxCopies()
console.log(
  `[gen-dev-certs] wrote:\n  ${certPath}\n  ${keyPath}\n  ${nginxCrt}\n  ${nginxKey}\n  ${composeCrt}\n  ${composeKey}`,
)
