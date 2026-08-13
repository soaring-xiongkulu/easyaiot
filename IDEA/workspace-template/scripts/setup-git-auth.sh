#!/usr/bin/env bash
# 在本工作区配置 Git HTTPS Token（仅写入个人数据卷，不上报门户）
set -euo pipefail

PROVIDER="${IDEA_GIT_PROVIDER:-${1:-}}"
LOGIN="${IDEA_GIT_LOGIN:-${2:-}}"
DATA_ROOT="${HOME}/project-data"
CRED_FILE="${DATA_ROOT}/.git-credentials"
GITCONFIG_SCOPE="${GIT_CONFIG_SCOPE:-local}"  # local | global

mkdir -p "${DATA_ROOT}"

usage() {
  cat <<'EOF'
用法:
  bash scripts/idea/setup-git-auth.sh [gitee|github|gitlab] [login]

说明:
  - Token 只写入本工作区数据卷: ~/project-data/.git-credentials
  - 不会上传到 EasyAIoT 门户或镜像仓库
  - Gitee: 私人令牌需勾选 projects 等权限
  - GitHub: 使用 Fine-grained / classic PAT（repo 权限）

也可用环境变量非交互写入（注意历史记录）:
  IDEA_GIT_PROVIDER=gitee IDEA_GIT_LOGIN=alice GIT_HTTPS_TOKEN=xxx \
    bash scripts/idea/setup-git-auth.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -z "${PROVIDER}" ]]; then
  echo "选择平台: 1) gitee  2) github  3) gitlab"
  read -r choice
  case "${choice}" in
    1|gitee|Gitee) PROVIDER=gitee ;;
    2|github|GitHub) PROVIDER=github ;;
    3|gitlab|GitLab) PROVIDER=gitlab ;;
    *) echo "无效选择"; exit 1 ;;
  esac
fi

case "${PROVIDER}" in
  gitee) HOST=gitee.com ;;
  github) HOST=github.com ;;
  gitlab)
    HOST="${GIT_HTTPS_HOST:-}"
    if [[ -z "${HOST}" ]]; then
      read -r -p "GitLab 主机名 (例如 gitlab.example.com): " HOST
    fi
    ;;
  *) echo "不支持的 provider: ${PROVIDER}"; exit 1 ;;
esac

if [[ -z "${LOGIN}" ]]; then
  read -r -p "Git 用户名 (login): " LOGIN
fi
if [[ -z "${LOGIN}" ]]; then
  echo "login 不能为空" >&2
  exit 1
fi

TOKEN="${GIT_HTTPS_TOKEN:-}"
if [[ -z "${TOKEN}" ]]; then
  echo "请粘贴 HTTPS Token（输入不可见），然后回车："
  read -r -s TOKEN
  echo
fi
if [[ -z "${TOKEN}" ]]; then
  echo "Token 为空" >&2
  exit 1
fi

# URL-encode 不安全字符（粗略）
enc() {
  python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

ENC_USER="$(enc "${LOGIN}")"
ENC_TOKEN="$(enc "${TOKEN}")"
LINE="https://${ENC_USER}:${ENC_TOKEN}@${HOST}"

# 去掉同 host 旧行后追加
if [[ -f "${CRED_FILE}" ]]; then
  grep -v "@${HOST}\$" "${CRED_FILE}" > "${CRED_FILE}.tmp" || true
  mv "${CRED_FILE}.tmp" "${CRED_FILE}"
fi
printf '%s\n' "${LINE}" >> "${CRED_FILE}"
chmod 600 "${CRED_FILE}"

REPO_DIR="${IDEA_OPEN_FOLDER:-$(pwd)}"
if [[ -d "${REPO_DIR}/.git" || -L "${REPO_DIR}" ]]; then
  REAL="${REPO_DIR}"
  if [[ -L "${REPO_DIR}" ]]; then
    REAL="$(readlink -f "${REPO_DIR}")"
  fi
  git -C "${REAL}" config --local credential.helper "store --file=${CRED_FILE}"
else
  git config --global credential.helper "store --file=${CRED_FILE}"
fi

# 清掉变量，降低泄露到子进程的概率
unset TOKEN ENC_TOKEN LINE GIT_HTTPS_TOKEN

cat <<EOF
[setup-git-auth] 已配置 ${PROVIDER} (${LOGIN})
  凭据文件: ${CRED_FILE}
  helper: store --file=...

验证:
  git ls-remote origin
  git push -u origin HEAD

清除凭据:
  bash scripts/idea/clear-git-auth.sh
EOF
