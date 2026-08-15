#!/usr/bin/env bash
# EasyAIoT HARNESS 冒烟测试（不输出密钥）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"

pass=0
fail=0

ok() { echo "[PASS] $*"; pass=$((pass + 1)); }
bad() { echo "[FAIL] $*"; fail=$((fail + 1)); }

echo "=== HARNESS smoke test ==="

if curl -fsS -o /dev/null http://127.0.0.1:3080/; then
  ok "Web UI http://127.0.0.1:3080"
else
  bad "Web UI unreachable (bash install.sh start ?)"
fi

if docker ps --filter name=easyaiot-harness --filter status=running | grep -q easyaiot-harness; then
  ok "container easyaiot-harness running"
else
  bad "container not running"
fi

if docker logs easyaiot-harness 2>&1 | grep -q 'easyaiot-platform-tools'; then
  ok "EasyAIoT platform tools plugin loaded"
else
  bad "platform tools plugin not found in logs"
fi

if docker logs easyaiot-harness 2>&1 | grep -qE 'easyaiot-workspace-seed|workspace-seed'; then
  ok "workspace seed plugin touched logs"
else
  # 插件可能已静默成功；退而检查 profile / 脚本存在
  if docker exec easyaiot-harness test -f /harness/plugins/easyaiot-workspace-seed.ts; then
    ok "workspace seed plugin present in image"
  else
    bad "workspace seed plugin missing"
  fi
fi

if docker exec easyaiot-harness sh -c 'test -f /data/dsh-home/profiles/web/package.json && grep -q dsh-better-sidebar /data/dsh-home/profiles/web/package.json'; then
  ok "dsh-better-sidebar installed in web profile"
elif docker exec easyaiot-harness sh -c 'test -f /harness/dsh-seed/profiles/web/package.json && grep -q dsh-better-sidebar /harness/dsh-seed/profiles/web/package.json'; then
  ok "dsh-better-sidebar present in image seed (volume may need recreate)"
else
  bad "dsh-better-sidebar not found (set HARNESS_ENABLE_SIDEBAR=1 and rebuild)"
fi

if docker exec easyaiot-harness curl -fsS http://host.docker.internal:48080/actuator/health | grep -q '"status":"UP"'; then
  ok "Gateway health from harness container"
else
  bad "Gateway health check failed"
fi

if docker exec easyaiot-harness test -f /workspace/easyaiot/AGENTS.md; then
  ok "ontology AGENTS.md linked in workspace"
else
  bad "AGENTS.md missing in workspace"
fi

openai_len="$(docker exec easyaiot-harness sh -c 'echo ${#OPENAI_API_KEY}')"
deepseek_len="$(docker exec easyaiot-harness sh -c 'echo ${#DEEPSEEK_API_KEY}')"
if [[ "${openai_len}" -gt 0 || "${deepseek_len}" -gt 0 ]]; then
  ok "LLM credential env present (openai_len=${openai_len}, deepseek_len=${deepseek_len})"
else
  bad "no LLM API key in container env — edit HARNESS/harness.env then restart"
fi

echo ""
echo "=== optional: LLM chat (requires valid paid API key) ==="
if [[ "${deepseek_len}" -gt 0 ]]; then
  if docker exec easyaiot-harness sh -c 'export DEEPSEEK_API_KEY; dsh --profile headless "回复：pong"' 2>&1 | grep -qi pong; then
    ok "headless chat (deepseek)"
  else
    bad "headless chat failed — check DEEPSEEK_API_KEY / account balance"
  fi
elif [[ "${openai_len}" -gt 0 ]]; then
  echo "[INFO] OPENAI key set but headless defaults to DeepSeek — configure Models in Web UI or set DEEPSEEK_API_KEY"
fi

echo ""
echo "result: ${pass} passed, ${fail} failed"
exit "$([[ ${fail} -eq 0 ]] && echo 0 || echo 1)"
