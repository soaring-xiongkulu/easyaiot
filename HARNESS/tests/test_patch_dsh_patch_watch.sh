#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_SCRIPT="${ROOT}/scripts/patch-dsh-patch-watch.sh"
FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "${FIXTURE_DIR}"' EXIT

FIXTURE="${FIXTURE_DIR}/index.js"
cat > "${FIXTURE}" <<'EOF'
async function watchUserPatches(ctx, options) {
	const { binName, filename } = options;
	const hmr = ctx.get("hmr");
	if (hmr === void 0) throw new Error(`${binName}: user patch-layer watching requires the Cordis HMR service`);
	const register = hmr.registerConfig(filename, async () => {});
	return await register;
}
EOF

DSH_APP_BOOT_FILE="${FIXTURE}" bash "${PATCH_SCRIPT}"
grep -q 'EASYAIOT_DSH_PATCH_WATCH_COMPAT' "${FIXTURE}"
grep -q 'typeof hmr.registerConfig !== "function"' "${FIXTURE}"
grep -q 'return async () => {}' "${FIXTURE}"

FIRST_HASH="$(sha256sum "${FIXTURE}" | awk '{print $1}')"
DSH_APP_BOOT_FILE="${FIXTURE}" bash "${PATCH_SCRIPT}"
SECOND_HASH="$(sha256sum "${FIXTURE}" | awk '{print $1}')"
[[ "${FIRST_HASH}" == "${SECOND_HASH}" ]]

printf '%s\n' 'export const compatible = true' > "${FIXTURE}"
DSH_APP_BOOT_FILE="${FIXTURE}" bash "${PATCH_SCRIPT}"
grep -q 'export const compatible = true' "${FIXTURE}"

if DSH_APP_BOOT_FILE="${FIXTURE_DIR}/missing.js" bash "${PATCH_SCRIPT}" >/dev/null 2>&1; then
  echo "[FAIL] 显式指定不存在的 dsh-app-boot 文件时应失败" >&2
  exit 1
fi

echo "[PASS] dsh patch-watch compatibility patch"
