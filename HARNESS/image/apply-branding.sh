#!/usr/bin/env bash
set -euo pipefail

BRAND_SRC="${BRAND_SRC:-/harness/image/branding}"
APP_NAME="${HARNESS_APP_NAME:-EasyAIoT}"
APP_SHORT="${HARNESS_APP_SHORT:-EasyAIoT}"
LOGO_PATH="${HARNESS_BRAND_LOGO:-/easyaiot-brand-logo.svg}"

export NODE_PATH="/usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules:/usr/local/lib/node_modules${NODE_PATH:+:${NODE_PATH}}"

FE_DIST=""
if FE_DIST="$(node -e "const p=require('path'); console.log(p.join(p.dirname(require.resolve('@deepseek-ai/dsh-web-frontend/package.json')), 'dist'))" 2>/dev/null)"; then
  :
else
  for cand in \
    /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-web-frontend/dist \
    /usr/local/lib/node_modules/@deepseek-ai/dsh-web-frontend/dist; do
    if [[ -f "${cand}/index.html" ]]; then
      FE_DIST="${cand}"
      break
    fi
  done
fi

INDEX_HTML="${FE_DIST:+${FE_DIST}/index.html}"
MANIFEST="${FE_DIST:+${FE_DIST}/manifest.webmanifest}"

if [[ -z "${FE_DIST}" || ! -f "${INDEX_HTML}" ]]; then
  echo "[harness-brand] skip: dsh-web-frontend dist not found" >&2
  exit 0
fi

if [[ -f "${BRAND_SRC}/favicon.svg" ]]; then
  cp -f "${BRAND_SRC}/favicon.svg" "${FE_DIST}/favicon.svg"
fi

if [[ -f "${BRAND_SRC}/logo.png" ]]; then
  cp -f "${BRAND_SRC}/logo.png" "${FE_DIST}/easyaiot-brand-logo.png"
  LOGO_PATH="/easyaiot-brand-logo.png"
elif [[ -f "${BRAND_SRC}/favicon.svg" ]]; then
  cp -f "${BRAND_SRC}/favicon.svg" "${FE_DIST}/easyaiot-brand-logo.svg"
  LOGO_PATH="/easyaiot-brand-logo.svg"
fi

cp -f "${BRAND_SRC}/brand.css" "${FE_DIST}/easyaiot-brand.css"
cp -f "${BRAND_SRC}/brand.js" "${FE_DIST}/easyaiot-brand.js"

IDEA_URL="${EASYAIOT_IDEA_URL:-}"
if [[ -z "${IDEA_URL}" ]]; then
  IDEA_URL=""
fi

cat > "${FE_DIST}/easyaiot-brand-config.js" <<EOF
window.__EASYAIOT_HARNESS_BRAND__={name:${APP_NAME@Q},short:${APP_SHORT@Q},logo:${LOGO_PATH@Q},ideaUrl:${IDEA_URL@Q}};
EOF

python3 - <<'PY' "${INDEX_HTML}" "${APP_NAME}"
import re, sys
path, title = sys.argv[1], sys.argv[2]
html = open(path, encoding="utf-8").read()
html = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", html, count=1)
if "easyaiot-brand.css" not in html:
    html = html.replace("</head>", '    <link rel="stylesheet" href="/easyaiot-brand.css" />\n    <script src="/easyaiot-brand-config.js"></script>\n    <script src="/easyaiot-brand.js" defer></script>\n  </head>', 1)
# 强制刷新静态资源缓存
import time
v = str(int(time.time()))
html = re.sub(r'href="/easyaiot-brand\.css[^"]*"', f'href="/easyaiot-brand.css?v={v}"', html)
html = re.sub(r'src="/easyaiot-brand-config\.js[^"]*"', f'src="/easyaiot-brand-config.js?v={v}"', html)
html = re.sub(r'src="/easyaiot-brand\.js[^"]*"', f'src="/easyaiot-brand.js?v={v}"', html)
open(path, "w", encoding="utf-8").write(html)
PY

if [[ -f "${MANIFEST}" ]]; then
  python3 - <<'PY' "${MANIFEST}" "${APP_NAME}" "${APP_SHORT}"
import json, sys
path, name, short = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(path, encoding="utf-8"))
data["name"] = name
data["short_name"] = short
json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(path, "a").write("\n")
PY
fi

echo "[harness-brand] applied name=${APP_NAME} dist=${FE_DIST}"
