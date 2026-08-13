#!/usr/bin/env bash
# 清除本工作区保存的 Git HTTPS 凭据
set -euo pipefail

DATA_ROOT="${HOME}/project-data"
CRED_FILE="${DATA_ROOT}/.git-credentials"
PROVIDER="${1:-}"
REPO_DIR="${IDEA_OPEN_FOLDER:-$(pwd)}"

if [[ -n "${PROVIDER}" ]]; then
  case "${PROVIDER}" in
    gitee) HOST=gitee.com ;;
    github) HOST=github.com ;;
    *) echo "usage: clear-git-auth.sh [gitee|github]"; exit 1 ;;
  esac
  if [[ -f "${CRED_FILE}" ]]; then
    grep -v "@${HOST}\$" "${CRED_FILE}" > "${CRED_FILE}.tmp" || true
    mv "${CRED_FILE}.tmp" "${CRED_FILE}"
    echo "[clear-git-auth] removed entries for ${HOST}"
  fi
else
  rm -f "${CRED_FILE}"
  echo "[clear-git-auth] removed ${CRED_FILE}"
fi

if [[ -d "${REPO_DIR}/.git" || -L "${REPO_DIR}" ]]; then
  REAL="${REPO_DIR}"
  [[ -L "${REPO_DIR}" ]] && REAL="$(readlink -f "${REPO_DIR}")"
  git -C "${REAL}" config --local --unset-all credential.helper 2>/dev/null || true
fi

echo "done"
