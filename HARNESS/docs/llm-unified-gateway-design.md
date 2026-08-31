# EasyAIoT 大模型能力统一化与 HARNESS 收口设计文档

- 状态：评审稿
- 范围：AI 模块（LLM 配置与调用）、WEB 控制台（LLM 管理页与业务调用方）、HARNESS（统一网关）
- 本文档描述的改造目标：**一套模板、一个启用模型、一个调用入口**

---

## 1. 背景与目标

### 1.1 现状问题

| 编号 | 问题 | 现状证据 |
|------|------|----------|
| P1 | 厂商分支代码重复膨胀 | `AI/app/blueprints/llm.py`（1718 行）按 `vendor == 'aliyun'` 拆出专门分支（`call_aliyun_qwenvl3`、`call_aliyun_video_with_mode`、`test_aliyun_qwenvl3`），其余走 generic/local，共 7 个调用函数，逻辑重复 |
| P2 | 模型类型区分无实际意义 | `model_type`（text/vision/multimodal）只参与列表过滤与存储，不驱动任何调用逻辑；主流模型本身支持多模态，业务接口却按能力拆成 6 个（vision/analyze、vision/inference、vision/understanding、vision/deep-thinking、video/inference、video/understanding） |
| P3 | 激活唯一性只有接口约定、无兜底 | `activate` 接口内全量置 false 再激活（`llm.py:299`），但并发/直改库可产生多条 `is_active=True`；`get_active_model()` 用 `.first()` 取第一条，不保证确定性 |
| P4 | 前端存在模型选择交互，管控语义不彻底 | `AiModelTool` 提供 LLM 下拉选择（`AiModelTool/index.vue:111`），与"平台统一管控启用模型"矛盾 |
| P5 | 模型配置两套体系 | 平台业务用 AI 模块 DB（`LLMModel` 表），HARNESS 聊天用 dsh 自身 `settings.yaml` + `.credentials.yaml`，互不相通；密钥分散存储 |
| P6 | 页面调用无统一入口 | WEB 前端直连 AI 模块 LLM 接口，无网关层，无法统一鉴权/审计/路由 |

### 1.2 目标

- **G1 模板化**：厂商差异收敛为「一个 OpenAI 兼容协议模板」+「预置端点模板」，`vendor`/`model_type` 不再驱动代码分支。
- **G2 单模型管控**：全平台同一时刻只启用 **1 个大模型**；所有 LLM 能力调用自动使用当前启用模型，前端不提供模型选择。
- **G3 HARNESS 收口**：页面的大模型调用统一汇聚到 HARNESS 网关执行调用与返回；模型接入配置在平台页面管理，密钥只在服务端流转。
- **G4 兼容平滑**：既有接口 URL 与前端方法签名保持兼容，分阶段落地，可随时回退。

### 1.3 不在本次范围

- 本地 Qwen 一键部署（`llm_deploy.py` / `llm_deploy_service.py` / `qwen_models.py`）：独立能力，保持现状。
- dsh 聊天界面自身的模型选择器：维持 dsh 原生行为，通过 4.5 节的 Tool 打通平台模型。

---

## 2. 现状盘点

### 2.1 AI 模块 LLM 接口（`app/blueprints/llm.py`）

**配置管理接口**（保留，微调）：

| 接口 | 说明 |
|------|------|
| GET /model/llm/list | 列表（支持 name/vendor/model_type/is_active 过滤） |
| GET /model/llm/detail/<id> | 详情（返回完整 api_key 用于编辑） |
| POST /model/llm/create | 创建配置 |
| PUT /model/llm/update/<id> | 更新配置 |
| DELETE /model/llm/delete/<id> | 删除 |
| POST /model/llm/activate/<id> | 激活（现有：全量置 false 后激活 → 互斥） |
| POST /model/llm/deactivate/<id> | 停用 |
| POST /model/llm/test/<id> | 连通性测试（3 套分支） |
| POST /model/llm/image_upload | 图片上传（历史遗留，保留） |

**业务能力接口**（保留 URL，内部收敛）：

| 接口 | 输入 | 现状调用链 |
|------|------|-----------|
| POST /model/llm/vision/analyze | multipart(image, prompt) | get_active_model → aliyun/generic/local 三分支 |
| POST /model/llm/vision/inference | multipart(image, prompt) | 同上（inference 模式） |
| POST /model/llm/vision/understanding | 同上 | 同上（understanding 模式） |
| POST /model/llm/vision/deep-thinking | 同上 | 同上（deep-thinking 模式） |
| POST /model/llm/video/inference | multipart(video)/video_url + prompt | aliyun 分支 / generic（stream=True） |
| POST /model/llm/video/understanding | 同上 | 同上 |

**数据模型 `LLMModel`**（`db_models.py:269`）：name(unique)、service_type(online/local)、vendor(aliyun/openai/anthropic/local)、model_type(text/vision/multimodal)、model_name、base_url、api_key、api_version、temperature(0.7)、max_tokens(2000)、timeout(60)、is_active、status、last_test_time/result、description、icon_url。

### 2.2 WEB 前端

- 配置页：`views/train/components/LLMManage/`（index.vue 表格/卡片双视图 + LLMModal.vue 表单 + LLMManageCardList.vue）
- 业务调用：`views/train/components/LLMManage/VisionInferenceModal.vue`、`VideoInferenceModal.vue`、`views/train/components/AiModelTool/index.vue`
- API 封装：`src/api/device/llm.ts`（方法签名 = 上表接口）
- 承载页签：`views/train/index.vue`（页签 2=AiModelTool、页签 5=LLMManage）

### 2.3 HARNESS（现状要点）

- 镜像内 `@deepseek-ai/dsh@0.1.0-rc.6`（cordis 插件体系），入口 `docker-entrypoint.sh` 以 `--profile web --patch cordis.patch.yml` 启动。
- 插件注入：`cordis.patch.yml` 挂载 `easyaiot-platform-tools`（Agent Tool）、`easyaiot-workspace-seed`。
- 网络：容器内 dsh 监听 `127.0.0.1:3081`，embed_gate（Python 反代）对外 `3080`，仅做 iframe 门禁 + 反代，**无 API 鉴权**。
- 配置：`harness.env`（DEEPSEEK_API_KEY / OPENAI_API_KEY / OPENAI_BASE_URL）首启 seed 到 `$DSH_HOME/.credentials.yaml`；模型 provider 在 dsh `settings.yaml`。
- 平台访问：容器内经 `host.docker.internal` 可直达 Gateway `:48080`（已有先例：`easyaiot-platform-tools` 的 `EASYAIOT_GATEWAY_URL`）。

---

## 3. 总体架构

### 3.1 改造前

```
WEB 页面（LLMManage 配置 / Vision·Video 弹窗 / AiModelTool 选模型）
   │ 直连（两套配置、无统一入口、密钥分散）
   ▼
AI 模块 :5000 ──vendor 三分支──▶ 百炼 / OpenAI 兼容 / 本地
HARNESS :3080（dsh 聊天，独立 settings.yaml + credentials.yaml）──▶ DeepSeek / OpenAI
```

### 3.2 改造后

```
                          ┌─────────────────────────────────────┐
WEB 页面（配置页：模板化表单 + 启用唯一模型）                    │
   │ 配置管理（直连 AI 模块，不变）                              │
   ▼                                                             │
AI 模块 :5000（配置中心 + 模板调用引擎 + 降级直连）              │
   │ 业务能力调用（默认经网关，可开关降级直连）                   │
   ▼                                                             │
HARNESS :3080（easyaiot-llm-gateway 插件 = 统一网关）            │
   │ 启动/定时拉取「启用模型」配置（内存缓存，不落盘）            │
   ▼                                                             │
  厂商：百炼 / DeepSeek / 智谱 / OpenAI / Anthropic 兼容 …◀──────┘
                    （全部走 OpenAI 兼容协议 /v1/chat/completions）

HARNESS Agent（dsh 聊天）──easyaiot_llm_chat Tool──▶ 网关（与页面共用同一启用模型）
```

**三个收口含义**：配置收口在平台页面（AI 模块 DB）；调用收口在 HARNESS 网关（页面 + Agent 共用）；模型收口为「同一时刻仅 1 个启用」。

---

## 4. 详细设计

### 4.1 LLM 配置模板化（G1）

#### 4.1.1 数据模型（`LLMModel` 表，不迁移）

| 字段 | 改造后语义 |
|------|-----------|
| `vendor` | 保留，值变为「模板 key」（见 4.1.2），**不再驱动任何代码分支**；存量值（aliyun/openai/anthropic/local）兼容映射到模板 |
| `model_type` | 保留字段、废弃逻辑：列表过滤参数保留兼容，表单不再展示；调用不再区分 text/vision/multimodal |
| `service_type` | online / local 保留（local 用于指向本地 vLLM 端点，同样走 OpenAI 兼容模板） |
| `base_url` | 模板选定后自动预填，可再编辑 |
| `model_name` | 厂商端点的模型 ID，自由填写（硬约束 = 端点提供什么就填什么） |
| 其余 | 不变 |

#### 4.1.2 预置模板注册表（新，`app/config/llm_templates.py`）

```python
@dataclass(frozen=True)
class LLMTemplate:
    key: str            # 模板标识，写回 LLMModel.vendor
    label: str          # 页面显示名
    base_url: str       # 预填端点（OpenAI 兼容 /v1 根地址，如 https://api.deepseek.com/v1）
    doc_url: str = ''   # 控制台获取 Key 的文档链接
    builtin_models: tuple[str, ...] = ()  # 常见模型 ID，页面下拉建议

LLM_TEMPLATES: dict[str, LLMTemplate] = {
    'deepseek':   LLMTemplate('deepseek',   'DeepSeek',  'https://api.deepseek.com/v1',  'https://platform.deepseek.com/',  ('deepseek-chat', 'deepseek-v4-flash')),
    'dashscope':  LLMTemplate('dashscope',  '阿里云百炼', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'https://bailian.console.aliyun.com/', ('qwen3-max', 'qwen3-plus', 'qwen3-vl-plus')),
    'zhipu':      LLMTemplate('zhipu',      '智谱 GLM',  'https://open.bigmodel.cn/api/paas/v4',  'https://open.bigmodel.cn/',  ('glm-5.3-flash', 'glm-4.5')),
    'openai':     LLMTemplate('openai',     'OpenAI',    'https://api.openai.com/v1',   'https://platform.openai.com/',  ('gpt-4.1', 'gpt-4.1-mini')),
    'anthropic':  LLMTemplate('anthropic',  'Anthropic 兼容', '',  'https://console.anthropic.com/', ()),  # 需走 OpenAI 兼容网关
    'custom':     LLMTemplate('custom',     '自定义 OpenAI 兼容', '', '', ()),
}
```

> 说明：Anthropic 官方 `/v1/messages` 协议不在本次支持范围（现状亦不支持），模板中「Anthropic 兼容」要求用户提供 OpenAI 兼容代理端点；如需官方协议，可在 HARNESS dsh 侧自定义 provider 单独使用（见 4.5）。

#### 4.1.3 统一调用引擎（消灭三分支）

新增 `app/services/llm_gateway_client.py`（或收敛于 `llm.py` 工具区）：

```python
def call_openai_compatible(model: LLMModel, messages: list[dict],
                           stream: bool = False, timeout: int | None = None,
                           temperature: float | None = None,
                           max_tokens: int | None = None,
                           extra_body: dict | None = None) -> requests.Response:
    """全平台唯一出站函数：所有模型调用都走这里。"""
    url = model.base_url.rstrip('/') + '/chat/completions'
    if '/v1' in url:                      # 兼容用户填了 /v1 前缀
        url = url.replace('/v1/chat/completions', '/chat/completions')
    payload = {
        'model': model.model_name,
        'messages': messages,             # OpenAI 兼容多模态结构：
        'stream': stream,                 #   [{'role':'user','content':[{'type':'text','text':...},{'type':'image_url','image_url':{'url':...}}]}]
        'temperature': temperature if temperature is not None else model.temperature,
        'max_tokens': max_tokens or model.max_tokens,
    }
    if extra_body: payload.update(extra_body)
    return requests.post(url, headers=build_headers(model), json=payload,
                         timeout=timeout or model.timeout, stream=stream)
```

- `build_headers`：`Authorization: Bearer <api_key>`（统一，不再区分厂商）。
- 多模态统一：图片以 `image_url`（平台 MinIO 的 http URL 或 data:base64）放入 messages，**不再有 vision/video 专用 payload 构造分支**。
- 删除：`call_aliyun_qwenvl3`、`call_generic_vision_llm`、`call_local_vision_llm`、`call_aliyun_video_with_mode`、`call_generic_video_llm`、`call_aliyun_vision_with_mode`、`call_vision_llm_with_mode`、`test_aliyun_qwenvl3`、`test_generic_llm`、`test_local_llm`。
- 统一测试：`test_model(model)` = 发一条最小消息 `Hello, reply 'ok'` 到 `call_openai_compatible`，解析状态码与 `choices[0].message.content`；结果写 `last_test_time/last_test_result`。

#### 4.1.4 业务能力接口收敛

- 6 个业务接口 **URL 与方法签名保持不变**（前端零改动成本），内部实现统一为：

```
1. model = get_active_model()            # 未启用 → 400「请先启用一个大模型」
2. 文件 → MinIO 上传取 URL（图片/视频），或直接用传入 URL
3. messages = 组装 OpenAI 兼容多模态结构（text + image_url/video_url 按厂商能力放 content 或 extra_body）
4. call_openai_compatible(model, messages, stream=True)
5. 流式 SSE 转发 / 非流式聚合后返回（沿用 code/msg/data 包装）
```

- **新增通用对话接口**：`POST /model/llm/chat`（JSON：`{prompt, files?: [{type:'image'|'video', url}]}`，SSE 流式）——页面任何"要 LLM 能力"的地方统一用它，不再按能力新开接口。

### 4.2 单模型管控（G2）

#### 4.2.1 激活唯一性兜底

- `activate_llm` 改为事务化：`db.session.begin_nested()` 内「全量置 false → 激活目标」，提交冲突（SQLite 锁）时重试一次；并发双激活的窗口期由自愈兜底。
- `get_active_model()` 自愈：查询结果若多于 1 条，取第一条、将其余置 false、记 warning 日志（"检测到 N 条激活记录，已收敛"）——保证 `.first()` 语义确定。
- 前端 `LLMManage` 启用交互加确认提示：「启用后将替代当前启用模型（平台同时仅启用 1 个模型）」。

#### 4.2.2 调用路径强制

- 所有业务接口与网关强制走 `get_active_model()`；未启用时统一返回 `400 {'code':400,'msg':'请先启用一个大模型'}`。
- `AiModelTool` 的 LLM 下拉改为**只读展示当前启用模型**（列表仍从 `/model/llm/list?is_active=true` 取），移除切换交互。

### 4.3 HARNESS 统一网关（G3，核心）

#### 4.3.1 插件形态

- 新增插件 `HARNESS/plugins/easyaiot-llm-gateway.ts`，挂载进 `cordis.patch.yml`（与 `easyaiot-platform-tools` 并列）。
- **实现方式：`ctx.effect()` 自起 Node HTTP server**，监听容器内 `127.0.0.1:${LLM_GATEWAY_PORT:-3082}`。不依赖 dsh 内部路由 API（dsh 0.1.0-rc.6 为 Developer Preview，自起 server 与主进程解耦、升级风险最小）。
- 暴露方式：embed_gate 之外再加一层 socat（`docker-entrypoint.sh` 追加 `socat TCP-LISTEN:3082,...,bind=0.0.0.0` 转发到 `127.0.0.1:3082`），或直接复用 embed_gate 所在进程再开一个 TCP 转发；端口与业务端口冲突时改 `LLM_GATEWAY_PUBLIC_PORT`。

#### 4.3.2 网关 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/llm/v1/chat/completions` | POST | **OpenAI 兼容**：`{model, messages, stream, temperature, max_tokens}`；`messages` 支持多模态（text/image_url/video_url）；`stream=true` 时 SSE 透传厂商流；响应结构完全对齐 OpenAI 格式 |
| `/api/llm/v1/models` | GET | 返回 `{data:[{id, object:'model'}]}`，即当前启用模型（对齐 OpenAI `/models`） |
| `/api/llm/chat` | POST | 平台语义简版：`{prompt, mode?, files?:[{type,url}], stream?}`；`mode`（inference/understanding/deep-thinking）按 AI 模块同款提示词模板增强，内部组装为 chat/completions 并转发；返回 `{code,msg,data:{response,usage}}`（非流式）或 SSE（stream=true） |
| `/api/llm/health` | GET | 网关存活 + 当前启用模型名 + 配置缓存时间戳 |

#### 4.3.3 配置获取与缓存

- 来源：`GET ${EASYAIOT_GATEWAY_URL}/model/llm/list?is_active=true&pageSize=1`（经 `host.docker.internal:48080`）。
- 策略：启动拉取 + 每 30s 轮询 + 调用时发现缓存过期/无配置立即重拉；命中即用。
- **密钥不落盘**：`api_key` 仅存内存缓存（`Map<modelId, config>`），不进 dsh `settings.yaml` / `.credentials.yaml` / 日志。
- 轮询失败：保留旧缓存继续服务，连续失败 3 次后在 `/api/llm/health` 与日志中标记 `stale`。

#### 4.3.4 鉴权与审计

- 鉴权：`harness.env` 新增 `LLM_GATEWAY_TOKEN`（安装脚本生成随机串）。所有 `/api/llm/*` 请求须带 `Authorization: Bearer <token>` 或 `X-LLM-Token`；缺失/错误 → 401。embed_gate 不拦截 API（其只拦顶层文档），鉴权由网关自身完成。
- 审计：网关记结构化日志（时间、方法、路径、模型 id、token 消耗、耗时、状态码）输出到 stdout（容器日志），不记录 prompt 明文（可选开关 `LLM_GATEWAY_AUDIT_PROMPT=1`）。

#### 4.3.5 降级与回退

- `harness.env` 新增 `EASYAIOT_LLM_GATEWAY_MODE=harness|direct`（默认 `harness`）。
- `harness`：WEB 前端 LLM 调用 baseURL 指向 `http://<host>:3082/api/llm`，失败（502/超时）时前端可配置自动重试直连 AI 模块（`fallback` 开关，默认开）。
- `direct`：前端直连 AI 模块（现状），网关不参与——回退通道，保证 HARNESS 实验模块故障时平台业务不中断。

### 4.4 前端改造

| 文件 | 改动 |
|------|------|
| `src/api/device/llm.ts` | 新增 `chat`、`gatewayHealth`；业务方法签名不变，baseURL 按 `LLM_GATEWAY_MODE` 切换（环境变量 `VITE_LLM_GATEWAY_URL` / 后端下发的运行配置） |
| `LLMManage/LLMModal.vue` | vendor 下拉 → 模板下拉（4.1.2 注册表）；选择模板自动填 base_url + 常见 model 下拉；**删除 model_type 下拉**；「启用」按钮加唯一性确认 |
| `LLMManage/index.vue` / `LLMManageCardList.vue` | 启用/停用交互不变；状态展示保持；卡片可展示「当前启用」角标 |
| `AiModelTool/index.vue` | LLM 下拉 → 只读展示当前启用模型（复用 getLLMList is_active 过滤） |
| `VisionInferenceModal.vue` / `VideoInferenceModal.vue` | payload 不变，请求路径经网关（4.3.5 开关）；文件先传 MinIO 取 URL（若平台流程已具备则复用） |

### 4.5 HARNESS Agent 与平台模型打通

- 不自动改写 dsh `settings.yaml`（内部格式随 dsh 版本变化，风险高）。
- 新增 Agent Tool `easyaiot_llm_chat`（在 `easyaiot-platform-tools.ts` 或独立插件注册）：Agent 在对话中可调用平台「启用模型」做业务分析（如看图、总结告警），请求走网关本机地址 `http://127.0.0.1:3082/api/llm/chat`（容器内直接访问，不经公网）。
- 效果：页面与 Agent 共用同一启用模型、同一网关、同一密钥，构成单模型闭环；dsh 聊天自身的模型选择器维持原生行为（可另配便宜模型跑闲聊，业务分析走平台模型）。

### 4.6 兼容与迁移

- **DB**：`LLMModel` 表结构不变，无迁移脚本；存量 vendor（aliyun/openai/anthropic/local）映射到模板显示（aliyun→dashscope、openai→openai、anthropic→anthropic 兼容、local→custom），`base_url` 按模板补全提示；存量 `model_type` 值保留展示。
- **API**：全部旧 URL 保留；新增 `/model/llm/chat` 与网关 4 个接口；被删函数仅内部实现替换。
- **前端**：`llm.ts` 方法签名不变；`LLMModal` 表单变化需要回归（vendor 值提交仍为字符串，后端 `update/create` 对 vendor/model_type 的写入逻辑保留，仅新增模板预填）。
- **验收清单**：见第 5 节各阶段。

---

## 5. 落地步骤

### 阶段 1：AI 模块模板化（后端）

1. 新增 `app/config/llm_templates.py` 注册表。
2. 新增 `call_openai_compatible` 统一出站函数；重构 `test_llm` 为统一测试；删除 7 个分支调用函数与 3 个分支测试函数。
3. 6 个业务接口内部统一走模板引擎；新增 `POST /model/llm/chat`（SSE）。
4. `activate_llm` 事务化 + `get_active_model` 自愈收敛。
5. 验收：6 个旧接口行为回归通过（用百炼/DeepSeek 各配一个模型跑 vision/analyze、video/inference）；`/chat` 流式可用；`test` 接口对所有模板返回一致结构。

### 阶段 2：前端配置页模板化 + 单模型管控

1. `LLMModal.vue` 模板下拉 + 删除 model_type + 启用确认；`AiModelTool` 只读展示启用模型。
2. 验收：新建模型按模板一键填端点；启用 A 时提示唯一性；AiModelTool 无模型选择交互；vision/video 弹窗回归。

### 阶段 3：HARNESS 网关插件

1. 新增 `plugins/easyaiot-llm-gateway.ts`（ctx.effect 起 server + 配置轮询 + 鉴权 + 审计），挂 `cordis.patch.yml`。
2. `docker-entrypoint.sh` 增加网关端口 socat；`harness.env.example` 新增 `LLM_GATEWAY_PORT`、`LLM_GATEWAY_TOKEN`、`EASYAIOT_LLM_GATEWAY_MODE`、`LLM_GATEWAY_AUDIT_PROMPT`；install.sh 生成随机 token。
3. `easyaiot-platform-tools.ts` 注册 `easyaiot_llm_chat` Tool。
4. 验收：`curl` 网关 `/v1/chat/completions`（带 token）流式返回；不带 token 401；改平台启用模型后 ≤30s 网关生效；容器重启后网关恢复。

### 阶段 4：页面收口切换

1. `llm.ts` 网关 baseURL 切换 + fallback 逻辑；`Vision/Video` 弹窗与 `AiModelTool` 走网关。
2. 验收：页面业务调用经网关成功（HARNESS 容器日志见审计记录）；停掉 HARNESS 容器后页面自动回退直连成功（或按开关明确失败提示）。

---

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| dsh 0.1.0-rc.6 为 Developer Preview，内部 API 变化 | 网关插件失效 | 网关用 `ctx.effect` 自起 server，最小化依赖 dsh 内部 API；锁 `DSH_VERSION`，升级前回归 |
| HARNESS 单点故障影响全平台 LLM | 页面 AI 功能不可用 | `EASYAIOT_LLM_GATEWAY_MODE=direct` 回退直连 AI 模块（AI 模块模板引擎本就保留能力）；网关无状态，后续可水平铺开 |
| 密钥泄露（日志/页面/Agent 输出） | 模型额度被盗用 | 密钥只在平台 DB + 网关内存；日志脱敏（`sk-***`）；审计默认不记 prompt；网关鉴权 token 随机化 |
| SQLite 并发双激活 | 启用模型不确定 | 激活事务化 + `get_active_model` 自愈收敛 + 页面确认提示 |
| 存量数据/前端回归 | 配置页不可用 | 表结构与 API URL 全部不变；阶段 1/2 验收清单强制回归旧接口 |
| 文件经网关传输体积大 | 网关压力/超时 | 图片/视频先落 MinIO 取 URL，网关只传 JSON；网关超时按模型 timeout 透传 |

---

## 7. 关键结论

1. 改造后代码中**不再存在厂商分支**：所有厂商（百炼、DeepSeek、智谱、OpenAI、Anthropic 兼容、本地 vLLM）走同一个 `call_openai_compatible` 模板；新厂商接入 = 配置页加一个模板条目，零代码。
2. **单模型管控由平台强制执行**：激活唯一（事务 + 自愈）+ 调用强制取激活模型 + 前端无选择交互。
3. **HARNESS 网关是纯转发层**（无状态、无密钥落盘、可降级直连），平台业务能力仍保留在 AI 模块，HARNESS 故障不导致业务中断。
4. 分 4 个阶段落地，每阶段可独立验收、可回退。

---

## 8. 实施记录（as-built，2026-08）

四个阶段已全部落地并通过验证，以下为与设计稿的差异与部署要点：

1. **网关 `/api/llm/chat` 支持 `mode`**：提示词按模式增强（inference/understanding/deep-thinking）的模板在网关内与 AI 模块各保留一份（常量表，逻辑一致）。已验证两条链路（经网关 / 直连）到达厂商的 messages 完全一致。
2. **前端切换采用构建期环境变量**（设计稿中「后端下发运行配置」未实现）：`VITE_LLM_GATEWAY_MODE`（`harness`|`direct`，默认 `harness`）、`VITE_LLM_GATEWAY_URL`（基址含 `/api/llm`，留空则等效 direct）、`VITE_LLM_GATEWAY_TOKEN`。行为：网关优先，任意失败（连接拒绝/401/5xx/超时）自动回退直连 AI 模块，console.warn 记录一次。Token 与 `VITE_IDEA_TOKEN` 同级（浏览器可见，轻量防护）。
3. **文件传输**：前端把 File 转 base64 data-URL 后走网关 JSON（视频支持直接传 url），未做「先传 MinIO 取 URL」改造；网关侧请求体上限 64MB，覆盖现有图片/短视频场景，大视频建议传 url。
4. **`build_chat_url` 版本段兼容**：智谱 `/api/paas/v4` 等版本段结尾的 base_url 旧代码会拼出错误端点，现已支持（`/v\d+` 结尾或含 `/v1` 直接追加，否则补 `/v1`）。
5. **未实现项**：`LLM_GATEWAY_AUDIT_PROMPT` 开关（审计日志固定不含 prompt，保持隐私安全）；`EASYAIOT_LLM_GATEWAY_MODE` 服务端模式变量（由前端 `VITE_LLM_GATEWAY_MODE` 取代）。
6. **插件加载**：`docker-compose.yml` 热挂载 `./plugins:/harness/plugins:ro`（改插件免重建镜像，仅重启容器）；`docker-entrypoint.sh` 启动时补齐 plugins 的 `@deepseek-ai/cordis` 软链并经 socat 暴露网关端口（容器内仍只监听 127.0.0.1）。
7. **上线步骤**：① WEB 按需配置三个 `VITE_LLM_GATEWAY_*` 后重新构建；② HARNESS 目录执行 `docker compose build && docker compose up -d`（存量容器仍是旧镜像，网关需重建/重启后生效）；③ `curl http://<host>:3082/api/llm/health` 验证。

### 真实厂商联调补充（2026-08，GLM + DeepSeek 实测）

1. **api_key 脱敏坑（已修复）**：列表接口经 `to_dict()` 对 `api_key` 脱敏（前 10 位 + `***`），网关按列表拉配置会把残缺密钥转发给厂商导致 401。新增专用端点 `GET /model/llm/active-config`（返回当前启用模型完整配置，含完整 `api_key`），网关轮询改用它；密钥仍只驻内存。
2. **调用时重校验（15s）**：网关在缓存为空、上次拉取失败、或缓存超过 15s（`REVALIDATE_MS`）时，先重新拉取再转发。实测：平台切换启用模型后，下一次调用 ≤15s 内生效，无需等 30s 轮询。
3. **进程容错**：网关忽略 stdout/stderr 的 EPIPE，父进程退出/管道断裂时保持存活。
4. **推理模型注意**：`deepseek-v4-*`、`glm-5.x` 等带思考（`reasoning_content`）的模型，`max_tokens` 设置过小（如 50）会被思考过程耗尽、`content` 返回空。平台默认 2000 足够，配置页保持默认即可；SSE 透传的 delta 含 `reasoning_content`，客户端按 OpenAI 兼容解析（展示或忽略思考内容）。
5. **错误透传**：厂商错误（如智谱 429 余额不足）以厂商原始状态码 + `detail` 原样透传给调用方（`upstream_error`），前端据此回退直连或提示。
6. **实测结果**：GLM（模板创建→激活→网关调用→厂商 429 错误透传）、DeepSeek 文本/SSE 流式/图片理解（直连与网关两路均返回正确结果）、启用互斥、15s 重校验、30s 轮询、审计日志无 prompt 明文——15/15 用例通过。

### OpenAI 实测与 gpt-5.x 兼容修复（2026-08）

1. **`max_completion_tokens` 自动降级（已修复）**：OpenAI `gpt-5.x` 系列推理模型不再接受 `max_tokens` 参数，报 `invalid_request_error: Unsupported parameter: 'max_tokens'... Use 'max_completion_tokens' instead`。AI 模块 `call_openai_compatible` 与网关 `forward()` 均已在收到该错误时自动改用 `max_completion_tokens` 重试一次（请求体只含其一）。验证：mock 厂商模拟拒绝后网关重试成功（请求参数 `['max_tokens'] → ['max_completion_tokens']`）；真实 OpenAI `gpt-5.4-mini` 首次被拒后自动重试，直连与网关两路均返回真实回答（图片分析「黑色」/文本「正常」）——8/8 用例通过。
2. **模板推荐清单更新**：openai 模板 `builtin_models` 更新为 `('gpt-5.6-luna', 'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.5', 'gpt-5.4-mini', 'gpt-4.1-mini')`。真实 key 拉取的账户模型列表（247 个）中 gpt-5.6 系列、gpt-5.x、gpt-4.1 系列均存在；`gpt-5.4-mini` 为该 key 有额度的可用模型。注意 gpt-5.6-luna 等接受 `max_completion_tokens` 后仍会因 `credit_balance_exhausted` 被拒——额度问题与协议兼容无关，透传展示即可。
3. **OpenAI 实测结论**：直连与经网关两条链路的真实响应一致（与 DeepSeek 结论相同）；OpenAI 未对平台返回的 `model` 字段做改写，透传原始模型名。
4. **视觉能力说明**：多模态与文本统一为单模型接入，`gpt-5.4-mini`（支持图像输入）在模板清单中作为视觉可用项；纯文本的 `gpt-5.6-luna/sol/terra` 推理模型配置后调用文本能力，图片类提示词会因厂商侧拒绝而透传错误——配置时按实际用途选择模型即可，平台不做视觉/文本分类（单模型管控设计使然）。

### Kimi（月之暗面 Moonshot）接入（2026-08）

1. **模板条目**：`LLM_TEMPLATES` 新增 `kimi`（label「Kimi（月之暗面）」），`base_url=https://api.moonshot.cn/v1`，`doc_url=https://platform.moonshot.cn/`，`builtin_models=('kimi-k2.6', 'kimi-k2.7-code')`——按该 key 实测拉取的账户模型列表（2 个）填写，其余为猜测的模型名不收录。前端模板下拉由 `/model/llm/templates` 动态下发，无需改前端。
2. **temperature 强制 1 降级（已修复）**：KIMI K2 系列仅接受 `temperature=1`，其余值报 `invalid temperature: only 1 is allowed for this model`。AI 模块 `call_openai_compatible` 与网关 `forward()` 的自动降级重试已扩展为顺序降级：先试 `temperature→1`（KIMI K2），再试 `max_tokens→max_completion_tokens`（OpenAI gpt-5.x），各自至多重试一次、请求体只含生效参数。配置页仍可填任意 temperature，调用时自动收敛，无需用户感知。
3. **实测结果（9 项全过）**：模板下发与字段、创建时模板联动 base_url（未传自动填）、detail 返回 `template=kimi`、激活、直连真实回答「接口正常」（温度降级日志可见）、经网关真实回答「网关正常」（200，17.9s 含推理时间）、SSE 流式 58 chunks 聚合「1,2,3,4,5」、429 限流以 `upstream_error` 透传（该 key 组织 RPM=3，每分钟最多 3 次调用，测试需串行间隔）。
4. **K2 为文本推理模型**：`kimi-k2.6`/`kimi-k2.7-code` 不支持图像输入，图片类提示词会透传厂商错误；首 token 延迟较高（本机实测约 3-18s），属推理模型常态，`timeout` 建议 ≥60s。

### 预置模板数据 + 外部服务接入（2026-08）

1. **一键部署预置模板数据**：AI 模块启动初始化（`db.create_all()` + 迁移后）调用 `ensure_llm_template_seed()`，**仅当 llm_config 表完全为空时**播种 5 条厂商模板数据（DeepSeek / 阿里云百炼 / 智谱 GLM / OpenAI / Kimi，各选该厂商当前推荐模型，端点、温度、超时等按最佳实践预置）。这些是**真实可用的模板**——填上真实 API 密钥即可启用，不是演示数据。幂等：重复启动不重复插入；已有任何真实数据的环境绝不混入。
2. **占位密钥与激活拦截**：模板数据统一占位密钥 `sk-placeholder-*`（非真实 key，零落库标记：`api_key` 前缀派生 `is_preset`，填入真实密钥后自动消失）。`/activate/<id>` 与 `/test/<id>` 对占位密钥返回 400 并引导「先在编辑中填入真实 API 密钥」；前端激活按钮对 `is_preset` 数据直接弹引导（去编辑），卡片/表格带「模板」徽章，编辑弹窗顶部提示 + 「去厂商控制台获取密钥」链接（模板 doc_url）。体验闭环：见模板 → 点激活 → 被引导去填 key → 保存 → 激活 → 全平台生效。
3. **其他服务直接使用（OpenAI SDK 兼容）**：网关任何 POST 路径（含 `/v1/chat/completions`）本就走 OpenAI 兼容转发，本次补齐 `GET /v1/models`（OpenAI SDK `client.models.list()` 路径，与 `/api/llm/v1/models` 等价）。外部服务用法：
   ```python
   from openai import OpenAI
   client = OpenAI(
       base_url="http://<host>:3082/v1",            # 网关对外端口（socat 已暴露）
       api_key="<LLM_GATEWAY_TOKEN>",               # HARNESS harness.env 里的网关令牌
   )
   resp = client.chat.completions.create(           # 非流式
       model="任意值，会被替换为平台当前启用模型",
       messages=[{"role": "user", "content": "你好"}],
   )
   print(resp.choices[0].message.content)
   # 流式：create(..., stream=True) 逐块返回；models.list() 可查当前启用模型
   ```
   要点：`model` 参数被网关替换为平台当前启用模型（单模型管控的对外体现）；错误统一 `{error:{message,type,detail}}`（上游错误带原始 detail）；`GET /health` 免鉴权，其余请求需 `Authorization: Bearer <token>`（未配置 token 则 503）；请求体上限 64MB。
4. **验证**：播种（空表 5 条/幂等/非空表跳过/均未激活/密钥脱敏）、拦截（激活与测试均 400 引导）、替换密钥后 `is_preset` 消失并激活成功、`GET /v1/models` 返回启用模型、`POST /v1/chat/completions` 非流式返回完整 OpenAI 格式（`object:'chat.completion'`、`model` 为启用模型）、流式 SSE 透传、无 token 401、平台 `/chat` 直连——17/17 用例通过。
