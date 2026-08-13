#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${HOME}/project-data"
rm -f "${DATA_ROOT}/.ai-env"
rm -f "${DATA_ROOT}/continue/config.yaml"
# keep directory; remove key-bearing files only
if [[ -d "${DATA_ROOT}/continue" ]]; then
  find "${DATA_ROOT}/continue" -type f \( -name 'config.yaml' -o -name '.env' -o -name 'secrets.json' \) -delete 2>/dev/null || true
fi
echo "AI credentials cleared from workspace data volume."
