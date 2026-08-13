#!/usr/bin/env bash
set -euo pipefail

PRODUCT_JSON="${PRODUCT_JSON:-/usr/lib/code-server/lib/vscode/product.json}"
LOGIN_HTML="${LOGIN_HTML:-/usr/lib/code-server/src/browser/pages/login.html}"
PAGES_DIR="${PAGES_DIR:-/usr/lib/code-server/src/browser/pages}"
MEDIA_DIR="${MEDIA_DIR:-/usr/lib/code-server/src/browser/media}"
LOGIN_SRC="${LOGIN_SRC:-/tmp/login-ui}"
APP_NAME="${IDEA_APP_NAME:-EasyAIoT}"
APP_LONG="${IDEA_APP_LONG:-EasyAIoT 云边端一体化智能算法应用平台}"

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
