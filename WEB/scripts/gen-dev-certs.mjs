#!/usr/bin/env node
/**
 * 生成本机开发用自签证书（localhost / 127.0.0.1），供 HTTP/2 开发服务与可选 nginx 443 使用。
 *
 *   node ./scripts/gen-dev-certs.mjs
 */
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const certDir = path.join(root, 'certs')
const keyPath = path.join(certDir, 'localhost-key.pem')
const certPath = path.join(certDir, 'localhost.pem')
const nginxCrt = path.join(certDir, 'server.crt')
const nginxKey = path.join(certDir, 'server.key')

fs.mkdirSync(certDir, { recursive: true })

if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
  console.log(`[gen-dev-certs] already exists:\n  ${certPath}\n  ${keyPath}`)
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

fs.copyFileSync(certPath, nginxCrt)
fs.copyFileSync(keyPath, nginxKey)
console.log(`[gen-dev-certs] wrote:\n  ${certPath}\n  ${keyPath}\n  ${nginxCrt}\n  ${nginxKey}`)
