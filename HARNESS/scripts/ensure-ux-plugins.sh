#!/usr/bin/env bash
# 确保 web profile 已挂载 UX 插件（文件树侧边栏等）
# 幂等：已安装则跳过；失败不阻断 dsh 启动
set -euo pipefail

DSH_HOME="${DSH_HOME:-/data/dsh-home}"
PROFILE_DIR="${DSH_HOME}/profiles/web"
ENABLE="${HARNESS_ENABLE_SIDEBAR:-1}"
SIDEBAR_SPEC="${HARNESS_SIDEBAR_PACKAGE:-dsh-better-sidebar@0.12.1}"
SEED_DIR="${HARNESS_UX_SEED:-/harness/dsh-seed}"

say() { printf '[harness-ux] %s\n' "$*"; }
warn() { printf '[harness-ux] WARN: %s\n' "$*" >&2; }

if [[ "${ENABLE}" != "1" ]]; then
  say "sidebar disabled (HARNESS_ENABLE_SIDEBAR=${ENABLE})"
  exit 0
fi

mkdir -p "${DSH_HOME}"

# 空 volume：从镜像内预装 seed 复制，避免首次启动联网装包
if [[ ! -d "${PROFILE_DIR}" && -d "${SEED_DIR}/profiles/web" && "${SEED_DIR}" != "${DSH_HOME}" ]]; then
  mkdir -p "${DSH_HOME}/profiles"
  cp -a "${SEED_DIR}/profiles/web" "${PROFILE_DIR}"
  # profiles/node_modules fallback 由 dsh 启动时 heal；若 seed 有也一并复制
  if [[ -d "${SEED_DIR}/profiles/node_modules" && ! -e "${DSH_HOME}/profiles/node_modules" ]]; then
    cp -a "${SEED_DIR}/profiles/node_modules" "${DSH_HOME}/profiles/node_modules" || true
  fi
  say "copied UX profile seed -> ${PROFILE_DIR}"
fi

# 尚无 profile 时，按 dsh 模板最小初始化（再写 allowBuilds，最后 add 插件）
if [[ ! -f "${PROFILE_DIR}/package.json" ]]; then
  mkdir -p "${PROFILE_DIR}"
  cat > "${PROFILE_DIR}/package.json" <<'EOF'
{
  "name": "dsh-profile-web",
  "private": true,
  "dependencies": {},
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-web-app"
      ]
    }
  }
}
EOF
  cat > "${PROFILE_DIR}/cordis.patch.yml" <<'EOF'
# Your patch layer for this dsh profile, applied after every bundle layer:
# a top-level YAML array of loader patch entries (id-targeted config
# overrides, disables, and insert lists; `!!js` expressions allowed).
[]
EOF
  cat > "${PROFILE_DIR}/pnpm-workspace.yaml" <<'EOF'
packages:
  - .

nodeLinker: hoisted
autoInstallPeers: false
EOF
  say "initialized web profile at ${PROFILE_DIR}"
fi

pkg_json="${PROFILE_DIR}/package.json"
AT_FILE_SPEC="${HARNESS_AT_FILE_PACKAGE:-https://github.com/omdsh-dev/dsh-at-file/archive/refs/tags/v0.6.0.tar.gz}"

if ! command -v dsh >/dev/null 2>&1; then
  warn "dsh not on PATH — skip UX plugin install"
  exit 0
fi

# 预写 pnpm 放行（node-pty / protobufjs；与官方 install 脚本对齐）
ws_yml="${PROFILE_DIR}/pnpm-workspace.yaml"
python3 - <<'PY' "${ws_yml}"
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8") if p.exists() else ""
before = t
for key in ("node-pty", "protobufjs"):
    t = re.sub(rf"^(\s*){re.escape(key)}:.*$", rf"\1{key}: true", t, flags=re.M)
if "allowBuilds:" not in t:
    t += "\nallowBuilds:\n  node-pty: true\n  protobufjs: true\n"
else:
    for key in ("node-pty", "protobufjs"):
        if f"{key}: true" not in t:
            t = t.replace("allowBuilds:", f"allowBuilds:\n  {key}: true", 1)
for pkg in ("dsh-better-sidebar", "dsh-at-file"):
    if pkg not in t:
        if "minimumReleaseAgeExclude:" in t:
            t = t.replace("minimumReleaseAgeExclude:", f"minimumReleaseAgeExclude:\n  - {pkg}", 1)
        else:
            t += f"\nminimumReleaseAgeExclude:\n  - {pkg}\n"
if t != before:
    p.write_text(t, encoding="utf-8")
PY

if grep -q '"dsh-better-sidebar"' "${pkg_json}" 2>/dev/null; then
  say "dsh-better-sidebar already in profile"
else
  say "installing ${SIDEBAR_SPEC} into web profile ..."
  if dsh plugin --profile web add "${SIDEBAR_SPEC}"; then
    say "sidebar plugin installed"
  else
    warn "sidebar install failed — UI 仍可用，仅无文件树侧边栏"
  fi
fi

if [[ "${HARNESS_ENABLE_AT_FILE:-1}" = "1" ]]; then
  if grep -q '"dsh-at-file"' "${pkg_json}" 2>/dev/null; then
    say "dsh-at-file already in profile"
  else
    say "installing dsh-at-file (@文件提及) ..."
    if dsh plugin --profile web add "${AT_FILE_SPEC}"; then
      say "at-file plugin installed"
    else
      warn "at-file install failed — 侧边栏自带 @文件 仍可用"
    fi
  fi
fi

# 清理旧版手动挂载，避免双侧边栏
patch_yml="${PROFILE_DIR}/cordis.patch.yml"
if [[ -f "${patch_yml}" ]] && grep -q 'id:[[:space:]]*better-sidebar' "${patch_yml}"; then
  python3 - <<'PY' "${patch_yml}"
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
out, i, lines = [], 0, text.splitlines(keepends=True)
while i < len(lines):
    if re.match(r"^[ \t]*- insert:\s*$", lines[i]):
        block = [lines[i]]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r"^- ", lines[j]):
            block.append(lines[j]); j += 1
        if any(re.search(r"id:\s*better-sidebar\b", x) for x in block):
            i = j
            continue
    out.append(lines[i]); i += 1
new = "".join(out)
if new != text:
    p.write_text(new, encoding="utf-8")
    print("removed manual better-sidebar mount")
PY
fi

exit 0
