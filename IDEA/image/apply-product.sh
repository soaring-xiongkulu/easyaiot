#!/usr/bin/env bash
set -euo pipefail

PRODUCT_JSON="${PRODUCT_JSON:-/usr/lib/code-server/lib/vscode/product.json}"
LOGIN_HTML="${LOGIN_HTML:-/usr/lib/code-server/src/browser/pages/login.html}"
PAGES_DIR="${PAGES_DIR:-/usr/lib/code-server/src/browser/pages}"
MEDIA_DIR="${MEDIA_DIR:-/usr/lib/code-server/src/browser/media}"
LOGIN_SRC="${LOGIN_SRC:-/tmp/login-ui}"
BRIDGE_SRC="${BRIDGE_SRC:-/tmp/idea-browser/easyaiot-ide-bridge.js}"
APP_NAME="${IDEA_APP_NAME:-EasyAIoT}"
APP_LONG="${IDEA_APP_LONG:-EasyAIoT 云边端一体化智能算法应用平台}"
WORKBENCH_HTML="${WORKBENCH_HTML:-/usr/lib/code-server/lib/vscode/out/vs/code/browser/workbench/workbench.html}"

if [[ -f "${PRODUCT_JSON}" ]]; then
  if command -v jq >/dev/null 2>&1; then
    tmp="$(mktemp)"
    jq --arg s "${APP_NAME}" --arg l "${APP_LONG}" \
      '.nameShort=$s | .nameLong=$l | .applicationName=($s|ascii_downcase|gsub(" "; "-")) | .win32NameLong=$l | .darwinNameLong=$l' \
      "${PRODUCT_JSON}" > "${tmp}"
    mv "${tmp}" "${PRODUCT_JSON}"
  else
    sed -i \
      -e 's/"nameShort": "[^"]*"/"nameShort": "'"${APP_NAME}"'"/' \
      -e 's/"nameLong": "[^"]*"/"nameLong": "'"${APP_LONG}"'"/' \
      "${PRODUCT_JSON}"
  fi
fi

if [[ -d "${LOGIN_SRC}" ]]; then
  [[ -f "${LOGIN_SRC}/login.html" ]] && cp -f "${LOGIN_SRC}/login.html" "${LOGIN_HTML}"
  [[ -f "${LOGIN_SRC}/login.css" ]] && cp -f "${LOGIN_SRC}/login.css" "${PAGES_DIR}/login.css"
  [[ -f "${LOGIN_SRC}/global.css" ]] && cp -f "${LOGIN_SRC}/global.css" "${PAGES_DIR}/global.css"
  [[ -f "${LOGIN_SRC}/logo.png" ]] && cp -f "${LOGIN_SRC}/logo.png" "${MEDIA_DIR}/easyaiot-logo.png"
  [[ -f "${LOGIN_SRC}/bg.png" ]] && cp -f "${LOGIN_SRC}/bg.png" "${MEDIA_DIR}/login-bg.png"
  [[ -f "${LOGIN_SRC}/favicon.svg" ]] && cp -f "${LOGIN_SRC}/favicon.svg" "${MEDIA_DIR}/favicon-dark-support.svg"
  [[ -f "${LOGIN_SRC}/favicon.svg" ]] && cp -f "${LOGIN_SRC}/favicon.svg" "${MEDIA_DIR}/favicon.svg"
  [[ -f "${LOGIN_SRC}/favicon.ico" ]] && cp -f "${LOGIN_SRC}/favicon.ico" "${MEDIA_DIR}/favicon.ico"
  [[ -f "${LOGIN_SRC}/favicon.png" ]] && cp -f "${LOGIN_SRC}/favicon.png" "${MEDIA_DIR}/favicon.png"
  [[ -f "${LOGIN_SRC}/favicon-32.png" ]] && cp -f "${LOGIN_SRC}/favicon-32.png" "${MEDIA_DIR}/favicon-32.png"
  [[ -f "${LOGIN_SRC}/favicon-16.png" ]] && cp -f "${LOGIN_SRC}/favicon-16.png" "${MEDIA_DIR}/favicon-16.png"
  [[ -f "${LOGIN_SRC}/pwa-icon-192.png" ]] && cp -f "${LOGIN_SRC}/pwa-icon-192.png" "${MEDIA_DIR}/pwa-icon-192.png"
  [[ -f "${LOGIN_SRC}/pwa-icon-512.png" ]] && cp -f "${LOGIN_SRC}/pwa-icon-512.png" "${MEDIA_DIR}/pwa-icon-512.png"

  # Also replace VS Code server favicons / PWA icons when present
  if [[ -f "${LOGIN_SRC}/favicon.ico" ]]; then
    for f in \
      /usr/lib/code-server/lib/vscode/resources/server/favicon.ico \
      /usr/lib/code-server/lib/vscode/resources/server/code-192.png \
      /usr/lib/code-server/lib/vscode/resources/server/code-512.png; do
      [[ -e "$f" ]] || continue
    done
    cp -f "${LOGIN_SRC}/favicon.ico" /usr/lib/code-server/lib/vscode/resources/server/favicon.ico 2>/dev/null || true
    [[ -f "${LOGIN_SRC}/pwa-icon-192.png" ]] && cp -f "${LOGIN_SRC}/pwa-icon-192.png" /usr/lib/code-server/lib/vscode/resources/server/code-192.png 2>/dev/null || true
    [[ -f "${LOGIN_SRC}/pwa-icon-512.png" ]] && cp -f "${LOGIN_SRC}/pwa-icon-512.png" /usr/lib/code-server/lib/vscode/resources/server/code-512.png 2>/dev/null || true
  fi
fi

# Explorer 拖文件 → 门户 / HARNESS：注入 workbench bridge（内联，避免缓存/CSP）
if [[ -f "${BRIDGE_SRC}" ]]; then
  cp -f "${BRIDGE_SRC}" "${MEDIA_DIR}/easyaiot-ide-bridge.js"
  if [[ -f "${WORKBENCH_HTML}" ]]; then
    python3 - <<'PY' "${WORKBENCH_HTML}" "${BRIDGE_SRC}"
from pathlib import Path
import re, sys
wb, bridge_path = Path(sys.argv[1]), Path(sys.argv[2])
bridge = bridge_path.read_text(encoding="utf-8")
html = wb.read_text(encoding="utf-8")
html = re.sub(r'\s*<script src="\{\{BASE\}\}/_static/src/browser/media/easyaiot-ide-bridge\.js"></script>\s*', "\n", html)
html = re.sub(r"<!-- easyaiot-ide-bridge -->.*?</script>\s*", "", html, flags=re.S)
idx = html.rfind("</html>")
if idx < 0:
    raise SystemExit("workbench.html: missing </html>")
html = html[:idx] + "\n\t<!-- easyaiot-ide-bridge -->\n\t<script>\n" + bridge.replace("</script>", "<\\/script>") + "\n\t</script>\n</html>\n"
wb.write_text(html, encoding="utf-8")
print("[idea] injected easyaiot-ide-bridge into workbench.html")
PY
  fi
fi

chown -R coder:coder \
  "${PRODUCT_JSON}" \
  "${PAGES_DIR}" \
  "${MEDIA_DIR}/easyaiot-logo.png" \
  "${MEDIA_DIR}/login-bg.png" \
  "${MEDIA_DIR}/favicon-dark-support.svg" \
  "${MEDIA_DIR}/favicon.ico" \
  "${MEDIA_DIR}/favicon.png" \
  "${MEDIA_DIR}/pwa-icon-192.png" \
  "${MEDIA_DIR}/pwa-icon-512.png" 2>/dev/null || true
chmod u+rw "${PRODUCT_JSON}" 2>/dev/null || true
