#!/usr/bin/env bash
# 兼容 dsh 0.1.0-rc.6：没有可用 HMR 配置监听器时保留静态补丁，关闭补丁文件热重载。
set -euo pipefail

readonly PATCH_MARKER="EASYAIOT_DSH_PATCH_WATCH_COMPAT"
readonly DEFAULT_DSH_APP_BOOT="/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js"

if [[ -n "${DSH_APP_BOOT_FILE:-}" && ! -f "${DSH_APP_BOOT_FILE}" ]]; then
  echo "[harness] ERROR: DSH_APP_BOOT_FILE 不存在: ${DSH_APP_BOOT_FILE}" >&2
  exit 1
fi

find_dsh_app_boot() {
  local candidate=""

  if [[ -n "${DSH_APP_BOOT_FILE:-}" ]]; then
    printf '%s\n' "${DSH_APP_BOOT_FILE}"
    return 0
  fi

  for candidate in \
    "${DEFAULT_DSH_APP_BOOT}" \
    "/usr/local/lib/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js" \
    "/harness/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  while IFS= read -r candidate; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done < <(
    find /usr/local/lib/node_modules /harness/node_modules /app/node_modules /opt \
      -type f -path '*/@deepseek-ai/dsh-app-boot/lib/index.js' -print 2>/dev/null || true
  )

  return 1
}

if ! DSH_APP_BOOT="$(find_dsh_app_boot)"; then
  echo "[harness] dsh-app-boot 未安装，跳过补丁监听兼容处理"
  exit 0
fi

node - "${DSH_APP_BOOT}" "${PATCH_MARKER}" <<'NODE'
const fs = require('node:fs')

const filename = process.argv[2]
const marker = process.argv[3]
const source = fs.readFileSync(filename, 'utf8')

if (source.includes(marker)) {
  console.log(`[harness] dsh patch-watch compatibility already applied: ${filename}`)
  process.exit(0)
}

const incompatibleGuard = 'if (hmr === void 0) throw new Error(`${binName}: user patch-layer watching requires the Cordis HMR service`);'

if (!source.includes(incompatibleGuard)) {
  if (source.includes('user patch-layer watching requires the Cordis HMR service')) {
    console.error(`[harness] ERROR: dsh patch-watch guard changed; refusing an unsafe patch: ${filename}`)
    process.exit(1)
  }
  console.log(`[harness] dsh patch-watch compatibility is not required: ${filename}`)
  process.exit(0)
}

const compatibleGuard = `// ${marker}
\tif (hmr === void 0 || typeof hmr.registerConfig !== "function") {
\t\tconsole.warn(\`\${binName}: Cordis HMR config watching is unavailable; using the static user patch layer\`);
\t\treturn async () => {};
\t}`

const patched = source.replace(incompatibleGuard, compatibleGuard)
if (patched === source) {
  console.error(`[harness] ERROR: failed to apply dsh patch-watch compatibility: ${filename}`)
  process.exit(1)
}

const stat = fs.statSync(filename)
const temporary = `${filename}.easyaiot-${process.pid}.tmp`
fs.writeFileSync(temporary, patched, { mode: stat.mode })
fs.chmodSync(temporary, stat.mode)
fs.renameSync(temporary, filename)
console.log(`[harness] applied dsh patch-watch compatibility: ${filename}`)
NODE
