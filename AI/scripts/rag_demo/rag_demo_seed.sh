#!/usr/bin/env bash
# ============================================================
# RAG 四层模型 demo 造数与业务链验证脚本
#   知识文档 -> 知识片段(自动切片/人工编辑/启停) -> 知识集(跨文档复用) -> RAG 专家(组合知识集问答)
# 用法: bash rag_demo_seed.sh [--reset]
#   默认要求库中无数据; --reset 会先清空 专家/知识集/文档 再重建
# ============================================================
set -euo pipefail

BASE="${RAG_API_BASE:-http://localhost:5000/model/rag}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESET=0
[[ "${1:-}" == "--reset" ]] && RESET=1

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
cyan()  { printf '\033[36m%s\033[0m\n' "$*"; }
fail()  { red "✗ $*"; exit 1; }

api_get()  { curl -s -m 10 "$BASE$1"; }
api_send() { # method path json_body
  local method="$1" path="$2" body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -s -m 120 -X "$method" -H 'Content-Type: application/json' -d "$body" "$BASE$path"
  else
    curl -s -m 120 -X "$method" "$BASE$path"
  fi
}
assert_ok() { # json [context]
  local json="$1" ctx="${2:-}"
  if [[ "$(jq -r '.code' <<<"$json")" != "0" ]]; then
    red "接口失败: $ctx -> $(jq -c '{code,msg}' <<<"$json")"; exit 1
  fi
}

# ---------------- 0. 清空旧数据 ----------------
if [[ "$RESET" == 1 ]]; then
  cyan "== 清空现有 RAG 数据 =="
  for id in $(api_get /experts | jq -r '.data[].id'); do
    api_send DELETE "/experts/$id" >/dev/null && green "  删除专家 #$id"
  done
  for id in $(api_get /knowledge-sets | jq -r '.data[].id'); do
    api_send DELETE "/knowledge-sets/$id" >/dev/null && green "  删除知识集 #$id"
  done
  for id in $(api_get /documents | jq -r '.data[].id'); do
    api_send DELETE "/documents/$id" >/dev/null && green "  删除文档 #$id"
  done
fi

existing=$(api_get /documents | jq -r '.data | length')
[[ "$existing" != "0" ]] && fail "库中已有 $existing 个文档, 如需重建请加 --reset"

# ---------------- 1. 上传知识文档(自动切片) ----------------
cyan "== 第 1 层: 上传知识文档 =="
declare -A DOC_ID
for file in "$DIR"/*.md; do
  name=$(basename "$file")
  json=$(curl -s -m 120 -F "file=@$file" "$BASE/documents")
  assert_ok "$json" "上传 $name"
  id=$(jq -r '.data.id' <<<"$json")
  DOC_ID["$name"]=$id
  green "  上传 [$id] $name -> 切片 $(jq -r '.data.segment_count' <<<"$json") 个"
done

doc() { # md 文件名 -> id
  local key
  for key in "${!DOC_ID[@]}"; do [[ "$key" == *"$1"* ]] && { echo "${DOC_ID[$key]}"; return; }; done
  fail "找不到文档 $1"
}

seg_by_doc() { # document_id -> "id1 id2 ..." (按 segment_index 顺序)
  api_get "/documents/$1/segments" | jq -r '.data[] | select(.is_enabled==true) | .id'
}
seg_idx() { # document_id 索引(从0, 按 segment_index)
  api_get "/documents/$1/segments" | jq -r ".data[$2].id"
}

D1=$(doc 摄像头) D2=$(doc 巡检) D3=$(doc 告警) D4=$(doc 标注)

# ---------------- 2. 知识片段: 人工编辑标题/标签 + 停用示例 ----------------
cyan "== 第 2 层: 知识片段人工维护 =="
curate() { # document_id seg_index title tags...
  local doc_id="$1" idx="$2" title="$3"; shift 3
  local sid tags body
  sid=$(seg_idx "$doc_id" "$idx")
  content=$(api_get "/documents/$doc_id/segments" | jq -r ".data[$idx].content | @json")
  tags=$(printf '%s' "$*" | jq -Rc 'split(" ") | map(select(length>0))')
  body="{\"title\":$(jq -Rc <<<"$title"),\"content\":$content,\"tags\":$tags,\"is_enabled\":true}"
  json=$(api_send PUT "/segments/$sid" "$body")
  assert_ok "$json" "编辑片段 #$sid"
  green "  片段 #$sid  <- $title"
}
curate "$D1" 0 "RTSP 与 ONVIF 接入方式"        摄像头接入 RTSP ONVIF
curate "$D1" 1 "码流与存储配置要求"              码流 H264 存储
curate "$D1" 2 "点位安装高度与角度要求"          点位规划 安装
curate "$D1" 3 "重点区域覆盖与点位命名"          覆盖规则 命名
curate "$D2" 0 "巡检频次与时段"                  巡检 频次
curate "$D2" 1 "人员安全防护检测判定标准"        安全帽 反光衣 检测
curate "$D2" 2 "设备消防与危化品巡检项"          设备巡检 消防通道 危化品
curate "$D2" 3 "巡检记录与异常闭环"              巡检记录 闭环
curate "$D3" 0 "告警分级标准"                    告警分级
curate "$D3" 1 "告警处置时限要求"                处置时限
curate "$D3" 2 "值班交接班要求"                  值班 交接班
curate "$D3" 3 "告警升级上报路径"                升级上报
curate "$D4" 0 "标注类别定义"                    标注 类别
curate "$D4" 1 "标注框准则"                      标注框
curate "$D4" 2 "难例与数据均衡要求"              难例 数据均衡
curate "$D4" 3 "质检与通过标准"                  质检 验收

D3S2=$(seg_idx "$D3" 2)
content=$(api_get "/documents/$D3/segments" | jq -r ".data[2].content | @json")
json=$(api_send PUT "/segments/$D3S2" "{\"title\":\"值班交接班要求\",\"content\":$content,\"tags\":[\"值班\",\"交接班\"],\"is_enabled\":false}")
assert_ok "$json" "停用片段 #$D3S2"
red "  片段 #$D3S2 已停用(不参与检索), 用于验证启停生效"

# ---------------- 3. 知识集: 跨文档组合片段, 验证片段复用 ----------------
cyan "== 第 3 层: 知识集(跨文档组合) =="
make_set() { # name category description seg_ids...
  local name="$1" cat="$2" desc="$3"; shift 3
  local ids=()
  for s in "$@"; do ids+=("$s"); done
  body=$(jq -nc --arg n "$name" --arg c "$cat" --arg d "$desc" \
        '{name:$n,category:$c,description:$d,segment_ids:[$ARGS.positional[]]}' --args "${ids[@]}")
  json=$(api_send POST /knowledge-sets "$body")
  assert_ok "$json" "创建知识集 $name"
  id=$(jq -r '.data.id' <<<"$json")
  green "  知识集 [$id] $name($(jq -r '.data.segment_count' <<<"$json") 片段, $(jq -r '.data.document_count' <<<"$json") 文档)" >&2
  echo "$id"
}
S1=$(make_set "摄像头点位与码流配置" "工业制造" "摄像头接入、码流存储、点位安装与覆盖规范" $(seg_by_doc $D1))
S2=$(make_set "安全巡检执行规范" "工业制造" "巡检频次、安全防护检测标准、巡检项与告警分级" $(seg_by_doc $D2) $(seg_idx $D3 0))
S3=$(make_set "告警处置与值班流程" "工业制造" "告警分级、处置时限与升级上报; 复用巡检规范中的检测标准" $(seg_idx $D3 0) $(seg_idx $D3 1) $(seg_idx $D3 3) $(seg_idx $D2 1))
S4=$(make_set "安全帽检测标注规范" "工业制造" "模型训练数据标注类别、标注框、难例与质检标准" $(seg_by_doc $D4))
cyan "  片段复用验证: 告警分级片段 #$(seg_idx $D3 0) 同时被 知识集$S2 与 $S3 引用; 检测标准片段 #$(seg_idx $D2 1) 同时被 知识集$S2 与 $S3 引用"

# ---------------- 4. RAG 专家: 组合知识集 ----------------
cyan "== 第 4 层: RAG 专家 =="
make_expert() { # name category prompt welcome set_ids...
  local name="$1" cat="$2" prompt="$3" welcome="$4"; shift 4
  local ids=()
  for s in "$@"; do ids+=("$s"); done
  body=$(jq -nc --arg n "$name" --arg c "$cat" --arg p "$prompt" --arg w "$welcome" \
        '{name:$n,category:$c,system_prompt:$p,welcome_message:$w,knowledge_set_ids:[$ARGS.positional[]]}' --args "${ids[@]}")
  json=$(api_send POST /experts "$body")
  assert_ok "$json" "创建专家 $name"
  id=$(jq -r '.data.id' <<<"$json")
  green "  专家 [$id] $name -> 知识集: $(jq -r '.data.knowledge_set_names | join(", ")' <<<"$json")" >&2
  echo "$id"
}
E1=$(make_expert "安全生产值班助手" "工业制造" \
  "你是工厂安全生产值班助手。回答必须严格依据提供的资料, 引用格式使用【资料 N】; 资料不足时明确说明缺少的信息, 不得编造; 涉及处置时限、上报路径等规定时给出具体数值与步骤。" \
  "您好, 我是安全生产值班助手, 可解答摄像头点位、巡检规范、告警处置与上报流程等问题。" \
  "$S1" "$S2" "$S3")
E2=$(make_expert "数据标注质检助手" "工业制造" \
  "你是安全帽检测模型的数据标注与质检助手。回答须严格依据提供的标注规范与检测标准资料, 引用格式使用【资料 N】; 资料不足时明确说明, 不得编造。" \
  "您好, 我是数据标注质检助手, 可解答安全帽/反光衣标注类别、标注框、难例与质检标准等问题。" \
  "$S4" "$S2")

# ---------------- 5. 业务链验证 ----------------
cyan "== 业务链验证: 知识集检索 =="
test_search() { # set_id query expect_text
  local set_id="$1" query="$2" expect="$3"
  json=$(api_send POST "/knowledge-sets/$set_id/search" "{\"query\":$(jq -Rc <<<"$query"),\"top_k\":5}")
  assert_ok "$json" "检索 '$query'"
  local hits docs
  hits=$(jq -r '.data | length' <<<"$json")
  docs=$(jq -r '[.data[].document_name] | unique | join(", ")' <<<"$json")
  if [[ "$hits" == "0" ]]; then
    red "  ✗ 检索「$query」无命中 (期望: $expect)"
  elif jq -e --arg t "$expect" '[.data[].content | contains($t)] | any' <<<"$json" >/dev/null; then
    green "  ✓ 检索「$query」命中 $hits 条, 来源: $docs"
  else
    red "  ! 检索「$query」命中 $hits 条($docs), 但未见期望内容: $expect"
  fi
}
test_search "$S1" "RTSP 拉流地址怎么配置" "RTSP 拉流地址"
test_search "$S1" "摄像头安装高度有什么要求" "安装高度"
test_search "$S2" "巡检频次和时段怎么安排" "班前巡检"
test_search "$S2" "安全帽未佩戴如何判定违规" "连续 5 秒"
test_search "$S3" "一级告警多久内必须处置" "60 秒"
test_search "$S4" "标注框要贴边留多少余量" "5%"

cyan "== 业务链验证: 停用片段不参与检索 =="
json=$(api_send POST "/knowledge-sets/$S3/search" "{\"query\":\"值班交接班要求\",\"top_k\":5}")
assert_ok "$json" "停用验证检索"
if jq -e --argjson sid "$D3S2" '[.data[].segment_id] | index($sid)' <<<"$json" >/dev/null; then
  red "  ✗ 已停用片段 #$D3S2 仍被检索到"
else
  green "  ✓ 已停用片段 #$D3S2 未出现在检索结果中(命中 $(jq -r '.data|length' <<<"$json") 条其他片段), 启停机制生效"
fi

cyan "== 业务链验证: RAG 专家问答(真实模型) =="
test_chat() { # expert_id question
  local expert_id="$1" question="$2"
  printf '  Q: %s\n' "$question"
  json=$(api_send POST "/experts/$expert_id/chat" "{\"question\":$(jq -Rc <<<"$question"),\"top_k\":5}")
  assert_ok "$json" "专家问答"
  local model sources
  model=$(jq -r '.data.model // "无(降级检索)"' <<<"$json")
  sources=$(jq -r '.data.sources | length' <<<"$json")
  printf '  模型: %s | 检索来源 %s 条\n' "$model" "$sources"
  jq -r '.data.response' <<<"$json" | sed 's/^/    /'
  echo
}
test_chat "$E1" "夜班值班时收到未戴安全帽的一级告警，我该怎么处理？"
test_chat "$E1" "新装的摄像头点位命名有什么要求？"
test_chat "$E1" "帮我把今天的天气编一首诗"   # 越界问题: 应明确说明资料不足
test_chat "$E2" "安全帽的标注框画到什么程度算合格？"

# ---------------- 6. 汇总 ----------------
cyan "== 汇总 =="
printf '文档: %s | 片段: %s | 知识集: %s | 专家: %s\n' \
  "$(api_get /documents | jq -r '.data|length')" \
  "$(api_get /segments | jq -r '.data|length')" \
  "$(api_get /knowledge-sets | jq -r '.data|length')" \
  "$(api_get /experts | jq -r '.data|length')"
green "Demo 数据就绪, 可直接在前端 训练->大模型->LLM 训练 页面查看各层数据。"
