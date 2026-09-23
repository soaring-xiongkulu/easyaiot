<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    width="980"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
    :z-index="1200"
    root-class-name="llm-judge-drawer"
  >
    <template #title>
      <div class="llj-title">
        <div class="llj-title__main">
          <div class="llj-title__badge">
            <Icon icon="mdi:brain" :size="19" />
          </div>
          <div class="llj-title__text">
            <div class="llj-title__name">大模型后处理规则</div>
            <div class="llj-title__sub">{{ headerSubtitle }}</div>
          </div>
        </div>
        <div class="llj-title__actions">
          <Button type="primary" :disabled="disabled || !taskId" @click="openEditor()">
            <template #icon><PlusOutlined /></template>
            新增规则
          </Button>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="llj-footer">
        <div class="llj-footer__hint">
          <InfoCircleOutlined />
          <span>告警事件触发后，命中规则的事件由绑定智能体对事件图片/视频独立队列研判，不阻塞算法主链路。</span>
        </div>
        <div class="llj-footer__btns">
          <Button @click="closeDrawer">关闭</Button>
        </div>
      </div>
    </template>

    <Spin :spinning="loading">
      <div class="llj-shell">
        <div class="llj-intro">
          <Icon icon="ant-design:info-circle-filled" :size="14" class="llj-intro__icon" />
          <span>
            规则按<b>优先级</b>匹配告警，检测对象/事件类别留空表示匹配<b>全部</b>，多规则命中时仅最高优先级规则生效；
            开启「二次判断」后，大模型确认事件成立才发送通知。
          </span>
        </div>

        <div class="llj-list">
          <AAlert
            v-if="loadError"
            class="llj-load-error"
            type="error"
            show-icon
            message="研判规则加载失败"
            :description="loadError"
          >
            <template #action>
              <Button size="small" :disabled="loading" @click="reload">重试</Button>
            </template>
          </AAlert>

          <template v-else-if="rules.length">
            <div
              v-for="rule in rules"
              :key="rule.id"
              class="llj-card"
              :class="{ off: !rule.enabled }"
            >
              <div class="llj-card__head">
                <a-tooltip title="优先级 · 数值越大越优先匹配告警">
                  <span class="llj-card__prio" :class="priorityClass(rule.priority)">
                    P{{ rule.priority }}
                  </span>
                </a-tooltip>
                <span class="llj-card__name" :title="rule.rule_name">{{ rule.rule_name }}</span>
                <div class="llj-card__head-right">
                  <a-tag v-if="!rule.enabled" color="default">已停用</a-tag>
                  <a-switch
                    size="small"
                    :checked="rule.enabled"
                    :disabled="disabled"
                    :loading="togglingId === rule.id"
                    @change="(checked: boolean) => toggleEnabled(rule, checked)"
                  />
                </div>
              </div>

              <div class="llj-card__grid">
                <div class="llj-kv">
                  <span class="llj-kv__label">匹配对象</span>
                  <span class="llj-kv__value" :title="(rule.match_objects || []).join('、')">
                    {{ rule.match_objects?.length ? rule.match_objects.join('、') : '全部' }}
                  </span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">匹配事件</span>
                  <span class="llj-kv__value" :title="(rule.match_events || []).join('、')">
                    {{ rule.match_events?.length ? rule.match_events.join('、') : '全部' }}
                  </span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">研判方式</span>
                  <span class="llj-kv__value">
                    {{ judgeModeLabel(rule) }}
                  </span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">通知模式</span>
                  <span class="llj-kv__value">
                    <span class="llj-kv__mode" :class="rule.secondary_judge ? 'is-gate' : 'is-plain'">
                      {{ rule.secondary_judge ? '门控通知' : '仅回写增强' }}
                    </span>
                  </span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">失败策略</span>
                  <span class="llj-kv__value">{{ failPolicyLabel(rule.fail_policy) }}</span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">抽检比例</span>
                  <span class="llj-kv__value">{{ rule.sample_rate_percent ?? 10 }}%</span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">智能体</span>
                  <span class="llj-kv__value" :title="agentName(rule.agent_id)">{{ agentName(rule.agent_id) }}</span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">大模型</span>
                  <span class="llj-kv__value">{{ modelName(rule.model_id) }}</span>
                </div>
                <div class="llj-kv">
                  <span class="llj-kv__label">研判间隔</span>
                  <span class="llj-kv__value">
                    {{ rule.min_interval_sec > 0 ? `≥ ${rule.min_interval_sec}s` : '不限' }}
                  </span>
                </div>
              </div>

              <div class="llj-card__foot">
                <span class="llj-card__time">{{ formatTime(rule.updated_at || rule.created_at) }}</span>
                <div class="llj-card__actions">
                  <Button type="text" size="small" :disabled="disabled" @click="openEditor(rule)">
                    <template #icon><EditOutlined /></template>
                    编辑
                  </Button>
                  <a-popconfirm
                    title="删除后该规则不再参与研判，确定删除？"
                    ok-text="删除"
                    cancel-text="取消"
                    :disabled="disabled"
                    :overlay-style="{ zIndex: 1300 }"
                    @confirm="handleDelete(rule)"
                  >
                    <Button type="text" size="small" danger :disabled="disabled">
                      <template #icon><DeleteOutlined /></template>
                      删除
                    </Button>
                  </a-popconfirm>
                </div>
              </div>
            </div>
          </template>

          <div v-else class="llj-empty">
            <div class="llj-empty__icon">
              <Icon icon="ant-design:audit-outlined" :size="30" />
            </div>
            <div class="llj-empty__title">暂无研判规则</div>
            <div class="llj-empty__desc">创建规则后，命中条件的告警将交由大模型二次研判</div>
            <Button
              v-if="!disabled && taskId"
              type="primary"
              size="small"
              class="llj-empty__btn"
              @click="openEditor()"
            >
              <template #icon><PlusOutlined /></template>
              新增规则
            </Button>
          </div>
        </div>
      </div>
    </Spin>

    <a-modal
      v-model:open="editorOpen"
      :title="editingRule ? '编辑研判规则' : '新增研判规则'"
      :confirm-loading="saving"
      :z-index="1300"
      width="720px"
      ok-text="保存"
      cancel-text="取消"
      destroy-on-close
      @ok="handleSave"
    >
      <a-form ref="ruleFormRef" :model="ruleForm" :rules="ruleRules" layout="vertical">
        <div class="led-section">
          <div class="led-section__title">基础信息</div>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="规则名称" name="rule_name">
                <a-input v-model:value="ruleForm.rule_name" placeholder="如：夜间入侵二次确认" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="优先级" name="priority" help="数值越大越优先匹配告警">
                <a-select
                  v-model:value="ruleForm.priority"
                  :options="priorityOptions"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item
                label="绑定智能体"
                name="agent_id"
                help="AI 模块专家（rag_expert），携带知识库上下文研判"
              >
                <a-select
                  v-model:value="ruleForm.agent_id"
                  placeholder="请选择智能体"
                  show-search
                  :options="agentOptions"
                  option-filter-prop="label"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="大模型" help="留空 = 使用智能体默认模型">
                <a-select
                  v-model:value="ruleForm.model_id"
                  placeholder="默认模型"
                  allow-clear
                  show-search
                  :options="modelOptions"
                  option-filter-prop="label"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <div class="led-section">
          <div class="led-section__title">
            匹配条件
            <span class="led-section__hint">均留空 = 匹配全部告警</span>
          </div>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item
                label="匹配检测对象"
                help="与告警对象/检测类别（小写）匹配，回车可输入多个"
              >
                <a-select
                  v-model:value="ruleForm.match_objects"
                  mode="tags"
                  :token-separators="[',', '，']"
                  placeholder="如 person、vehicle"
                  :options="objectOptions"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="匹配事件类型" help="回车可输入多个，如 intrusion、fighting">
                <a-select
                  v-model:value="ruleForm.match_events"
                  mode="tags"
                  :token-separators="[',', '，']"
                  placeholder="如 intrusion、fighting"
                  :options="eventOptions"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <div class="led-section">
          <div class="led-section__title">研判执行</div>
          <a-form-item label="判断方式" name="judge_mode">
            <div class="led-modes">
              <div
                class="led-mode"
                :class="{ active: ruleForm.judge_mode === 'image' }"
                @click="ruleForm.judge_mode = 'image'"
              >
                <FileImageOutlined class="led-mode__icon" />
                <div class="led-mode__body">
                  <div class="led-mode__name">事件图片研判</div>
                  <div class="led-mode__desc">研判事件抓拍图片，速度快、成本低</div>
                </div>
                <CheckCircleFilled class="led-mode__check" />
              </div>
              <div
                class="led-mode"
                :class="{ active: ruleForm.judge_mode === 'video' }"
                @click="ruleForm.judge_mode = 'video'"
              >
                <VideoCameraOutlined class="led-mode__icon" />
                <div class="led-mode__body">
                  <div class="led-mode__name">事件视频研判</div>
                  <div class="led-mode__desc">研判事件前后片段视频，更准确、成本较高</div>
                </div>
                <CheckCircleFilled class="led-mode__check" />
              </div>
            </div>
          </a-form-item>
          <div v-if="ruleForm.judge_mode === 'video'" class="led-video-box">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="事件前窗口（秒）" name="video_pre_seconds">
                  <a-input-number
                    v-model:value="ruleForm.video_pre_seconds"
                    :min="0"
                    :max="300"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="事件后窗口（秒）" name="video_post_seconds">
                  <a-input-number
                    v-model:value="ruleForm.video_post_seconds"
                    :min="0"
                    :max="300"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="切片最大时长（秒）" name="video_max_seconds">
                  <a-input-number
                    v-model:value="ruleForm.video_max_seconds"
                    :min="1"
                    :max="300"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item
                label="二次判断（门控通知）"
                name="secondary_judge"
                help="开启后：大模型确认事件成立才发送通知，驳回则抑制"
              >
                <a-switch
                  v-model:checked="ruleForm.secondary_judge"
                  checked-children="门控"
                  un-checked-children="回写"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item
                label="研判失败策略"
                name="fail_policy"
                help="大模型调用失败时通知如何处理"
              >
                <a-select
                  v-model:value="ruleForm.fail_policy"
                  :options="failPolicyOptions"
                  :get-popup-container="popupInPlace"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <div class="led-section">
          <div class="led-section__title">调度控制</div>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item
                label="告警抽检比例"
                name="sample_rate_percent"
                help="如 10 = 每 10 条抽 1 条"
              >
                <a-input-number
                  v-model:value="ruleForm.sample_rate_percent"
                  :min="1"
                  :max="100"
                  style="width: 100%"
                >
                  <template #addonAfter>%</template>
                </a-input-number>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item
                label="最小研判间隔（秒）"
                name="min_interval_sec"
                help="0 = 不限，防止重复调用"
              >
                <a-input-number
                  v-model:value="ruleForm.min_interval_sec"
                  :min="0"
                  :max="86400"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="强制 JSON 输出" name="require_json" help="关闭后由模型自由输出">
                <a-switch v-model:checked="ruleForm.require_json" />
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <div class="led-section led-section--last">
          <div class="led-section__title">提示词覆盖</div>
          <a-form-item
            help="留空 = 使用智能体默认提示词；可用占位符：{object_name}、{event}、{detections_json}"
          >
            <a-textarea
              v-model:value="ruleForm.prompt_override"
              :rows="3"
              placeholder="可选，覆盖智能体默认研判提示词"
            />
          </a-form-item>
        </div>
      </a-form>
    </a-modal>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { Alert as AAlert, Spin } from 'ant-design-vue';
import {
  PlusOutlined,
  InfoCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  CheckCircleFilled,
} from '@ant-design/icons-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listLlmJudgeRules,
  createLlmJudgeRule,
  updateLlmJudgeRule,
  deleteLlmJudgeRule,
  type LlmJudgeRule,
  type LlmJudgeRulePayload,
  type LlmJudgeMode,
  type LlmFailPolicy,
} from '@/api/device/algorithm_task';
import { listRagExperts, type RagExpert } from '@/api/device/rag';
import { getLLMList, type LLMModel } from '@/api/device/llm';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';

defineOptions({ name: 'LlmJudgeRuleDrawer' });

const { createMessage } = useMessage();
const emit = defineEmits(['changed']);

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  taskId.value = data?.taskId ?? null;
  taskName.value = data?.taskName || '';
  disabled.value = data?.disabled === true;
  if (taskId.value) {
    await Promise.all([loadRules(), loadExperts(), loadModels()]);
  }
});

const taskId = ref<number | null>(null);
const taskName = ref('');
const disabled = ref(false);
const loading = ref(false);
const saving = ref(false);
const loadError = ref('');
const rules = ref<LlmJudgeRule[]>([]);
const experts = ref<RagExpert[]>([]);
const models = ref<LLMModel[]>([]);
const togglingId = ref<number | null>(null);

const enabledCount = computed(() => rules.value.filter((r) => r.enabled).length);
const totalCount = computed(() => rules.value.length);
const headerSubtitle = computed(() => {
  const base = taskName.value ? `${taskName.value} · ` : '';
  if (!taskId.value) return `${base}保存算法任务后可配置`;
  if (loadError.value) return `${base}规则加载失败`;
  return `${base}已启用 ${enabledCount.value}/${totalCount.value} 条规则`;
});

const agentOptions = computed(() =>
  experts.value.map((e) => ({
    label: `${e.name}${e.is_enabled ? '' : '（已停用）'}`,
    value: e.id,
    disabled: !e.is_enabled,
  })),
);
const modelOptions = computed(() =>
  models.value.map((m) => ({ label: `${m.name}（${m.model_name || m.vendor}）`, value: m.id })),
);
const objectOptions = [
  { label: 'person', value: 'person' },
  { label: 'vehicle', value: 'vehicle' },
  { label: 'car', value: 'car' },
  { label: 'truck', value: 'truck' },
  { label: 'face', value: 'face' },
  { label: 'plate', value: 'plate' },
  { label: 'dog', value: 'dog' },
  { label: 'fire', value: 'fire' },
  { label: 'smoke', value: 'smoke' },
];
const eventOptions = [
  { label: 'intrusion', value: 'intrusion' },
  { label: 'fighting', value: 'fighting' },
  { label: 'fall', value: 'fall' },
  { label: 'loitering', value: 'loitering' },
  { label: 'crowd', value: 'crowd' },
];
const priorityOptions = Array.from({ length: 10 }, (_, i) => ({ label: `P${i + 1}`, value: i + 1 }));
const failPolicyOptions = [
  { label: 'skip · 保持原结果', value: 'skip' },
  { label: 'confirm · 放行通知', value: 'confirm' },
  { label: 'reject · 抑制通知', value: 'reject' },
];

/** 让 Select 下拉渲染在弹窗内部，避免被高层级抽屉遮挡 */
function popupInPlace(triggerNode: HTMLElement): HTMLElement {
  return triggerNode.parentElement || document.body;
}

function agentName(agentId: number): string {
  return experts.value.find((e) => e.id === agentId)?.name || `#${agentId}`;
}
function modelName(modelId?: number | null): string {
  if (!modelId) return '智能体默认';
  return models.value.find((m) => m.id === modelId)?.name || `#${modelId}`;
}
function failPolicyLabel(policy: LlmFailPolicy): string {
  return failPolicyOptions.find((o) => o.value === policy)?.label.split(' · ')[1] || policy;
}
function judgeModeLabel(rule: LlmJudgeRule): string {
  if (rule.judge_mode === 'video') {
    return `视频研判 · 前${rule.video_pre_seconds}s/后${rule.video_post_seconds}s`;
  }
  return '图片研判';
}
function priorityClass(priority: number): string {
  if (priority >= 8) return 'is-high';
  if (priority >= 4) return 'is-mid';
  return 'is-low';
}
function formatTime(value?: string): string {
  if (!value) return '';
  return String(value).replace('T', ' ').slice(0, 16);
}

async function loadRules() {
  if (!taskId.value) return;
  loading.value = true;
  loadError.value = '';
  try {
    const res: any = await listLlmJudgeRules(taskId.value);
    rules.value = Array.isArray(res) ? res : res?.data || [];
  } catch (error: any) {
    rules.value = [];
    loadError.value = formatApiErrorMessage(error, '加载研判规则失败');
  } finally {
    loading.value = false;
  }
}

async function reload() {
  if (!taskId.value) return;
  await Promise.all([loadRules(), loadExperts(), loadModels()]);
}

async function loadExperts() {
  try {
    const res: any = await listRagExperts();
    experts.value = Array.isArray(res) ? res : res?.data || [];
  } catch (error: any) {
    // 智能体不可用时下拉为空，不影响规则加载
    console.error('加载智能体列表失败', error);
  }
}

async function loadModels() {
  try {
    const res: any = await getLLMList({ page: 1, pageSize: 200 });
    const list = res?.data?.list || res?.list || [];
    models.value = Array.isArray(list) ? list : [];
  } catch (error: any) {
    console.error('加载大模型列表失败', error);
  }
}

// ====================== 新增 / 编辑 ======================
const editorOpen = ref(false);
const editingRule = ref<LlmJudgeRule | null>(null);
const ruleFormRef = ref();
const ruleForm = ref<Record<string, any>>({});
const ruleRules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  agent_id: [{ required: true, message: '请选择智能体', trigger: 'change' }],
  judge_mode: [{ required: true, message: '请选择判断方式', trigger: 'change' }],
};

function openEditor(record?: LlmJudgeRule) {
  editingRule.value = record || null;
  ruleForm.value = {
    rule_name: record?.rule_name || '',
    match_objects: record?.match_objects || [],
    match_events: record?.match_events || [],
    agent_id: record?.agent_id ?? undefined,
    model_id: record?.model_id ?? undefined,
    judge_mode: (record?.judge_mode || 'image') as LlmJudgeMode,
    video_pre_seconds: record?.video_pre_seconds ?? 5,
    video_post_seconds: record?.video_post_seconds ?? 10,
    video_max_seconds: record?.video_max_seconds ?? 30,
    secondary_judge: record?.secondary_judge === true,
    fail_policy: (record?.fail_policy || 'skip') as LlmFailPolicy,
    prompt_override: record?.prompt_override || '',
    require_json: record?.require_json !== false,
    sample_rate_percent: record?.sample_rate_percent ?? 10,
    min_interval_sec: record?.min_interval_sec ?? 0,
    priority: record?.priority ?? 5,
    enabled: record?.enabled !== false,
  };
  editorOpen.value = true;
}

async function handleSave() {
  if (!taskId.value) return;
  try {
    await ruleFormRef.value?.validate();
  } catch {
    return;
  }
  saving.value = true;
  try {
    const payload: LlmJudgeRulePayload = {
      rule_name: String(ruleForm.value.rule_name || '').trim(),
      match_objects: Array.isArray(ruleForm.value.match_objects) && ruleForm.value.match_objects.length
        ? ruleForm.value.match_objects.map(String).filter(Boolean)
        : undefined,
      match_events: Array.isArray(ruleForm.value.match_events) && ruleForm.value.match_events.length
        ? ruleForm.value.match_events.map(String).filter(Boolean)
        : undefined,
      agent_id: Number(ruleForm.value.agent_id),
      model_id: ruleForm.value.model_id ? Number(ruleForm.value.model_id) : null,
      judge_mode: ruleForm.value.judge_mode,
      video_pre_seconds: Number(ruleForm.value.video_pre_seconds) || 0,
      video_post_seconds: Number(ruleForm.value.video_post_seconds) || 0,
      video_max_seconds: Number(ruleForm.value.video_max_seconds) || 30,
      secondary_judge: ruleForm.value.secondary_judge === true,
      fail_policy: ruleForm.value.fail_policy,
      prompt_override: ruleForm.value.prompt_override ? String(ruleForm.value.prompt_override) : null,
      require_json: ruleForm.value.require_json !== false,
      sample_rate_percent: Number(ruleForm.value.sample_rate_percent) || 10,
      min_interval_sec: Number(ruleForm.value.min_interval_sec) || 0,
      priority: Number(ruleForm.value.priority) || 5,
      enabled: ruleForm.value.enabled !== false,
    };
    if (editingRule.value) {
      await updateLlmJudgeRule(editingRule.value.id, payload);
      createMessage.success('规则已更新');
    } else {
      await createLlmJudgeRule(taskId.value, payload);
      createMessage.success('规则已创建，任务大模型后处理已自动开启');
    }
    editorOpen.value = false;
    await loadRules();
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '保存规则失败'));
  } finally {
    saving.value = false;
  }
}

async function toggleEnabled(record: LlmJudgeRule, checked: boolean) {
  togglingId.value = record.id;
  try {
    // 后端为整体覆盖语义（rule_name 必填），展开记录仅改 enabled
    await updateLlmJudgeRule(record.id, { ...record, enabled: checked } as LlmJudgeRulePayload);
    record.enabled = checked;
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '更新规则状态失败'));
    // 恢复开关与实际状态一致
    await loadRules();
  } finally {
    togglingId.value = null;
  }
}

async function handleDelete(record: LlmJudgeRule) {
  try {
    await deleteLlmJudgeRule(record.id);
    createMessage.success('规则已删除');
    await loadRules();
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '删除规则失败'));
  }
}
</script>

<style lang="less" scoped>
@llj-primary: #1677ff;

.llj-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 8px;

  &__main {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }

  &__badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 38px;
    border-radius: 10px;
    color: @llj-primary;
    background: fade(@llj-primary, 10%);
    flex-shrink: 0;
  }

  &__text {
    min-width: 0;
  }

  &__name {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.3;
  }

  &__sub {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 520px;
  }

  &__actions {
    flex-shrink: 0;
  }
}

.llj-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  box-sizing: border-box;
}

/* ===== 顶部说明条 ===== */
.llj-intro {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  background: fade(@llj-primary, 6%);
  border: 1px solid fade(@llj-primary, 16%);
  font-size: 12.5px;
  line-height: 1.7;
  color: rgba(0, 0, 0, 0.65);

  b {
    color: rgba(0, 0, 0, 0.82);
    font-weight: 600;
  }

  &__icon {
    color: @llj-primary;
    margin-top: 4px;
    flex-shrink: 0;
  }
}

/* ===== 规则列表 ===== */
.llj-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  min-width: 0;
}

.llj-load-error {
  margin-bottom: 0;
}

.llj-card {
  border: 1px solid #e8e8ec;
  border-radius: 10px;
  background: #fff;
  padding: 14px 16px 10px;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@llj-primary, 45%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  }

  &.off {
    background: #fafafa;

    .llj-card__name,
    .llj-card__grid {
      opacity: 0.55;
    }
  }

  &__head {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__prio {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 34px;
    height: 22px;
    padding: 0 6px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.3px;
    flex-shrink: 0;
    cursor: default;

    &.is-high {
      color: #d4380d;
      background: #fff2e8;
      border: 1px solid #ffbb96;
    }

    &.is-mid {
      color: @llj-primary;
      background: #e6f4ff;
      border: 1px solid #91caff;
    }

    &.is-low {
      color: rgba(0, 0, 0, 0.55);
      background: #f5f5f5;
      border: 1px solid #d9d9d9;
    }
  }

  &__name {
    font-size: 14.5px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
    line-height: 1.4;
    word-break: break-word;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__head-right {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: auto;
    flex-shrink: 0;

    :deep(.ant-tag) {
      margin: 0;
    }
  }

  /* 配置项摘要：3 列栅格 */
  &__grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px 18px;
    margin-top: 12px;
    padding: 12px 14px;
    background: #fafbfc;
    border-radius: 8px;
  }

  &__foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 10px;
    padding-top: 6px;
    border-top: 1px solid #f2f2f5;
  }

  &__time {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.35);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }
}

.llj-kv {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;

  &__label {
    font-size: 11.5px;
    color: rgba(0, 0, 0, 0.4);
    line-height: 1.4;
  }

  &__value {
    font-size: 12.5px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.82);
    line-height: 1.5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__mode {
    display: inline-flex;
    align-items: center;
    gap: 5px;

    &::before {
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    &.is-gate {
      color: #d4380d;

      &::before {
        background: #d4380d;
      }
    }

    &.is-plain {
      color: #389e0d;

      &::before {
        background: #389e0d;
      }
    }
  }
}

/* ===== 空状态 ===== */
.llj-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin-top: 40px;
  padding: 46px 20px;
  border: 1px dashed #d9dde5;
  border-radius: 10px;
  background: #fafbfc;

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #e6f4ff;
    color: @llj-primary;
    margin-bottom: 4px;
  }

  &__title {
    font-size: 14.5px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.75);
  }

  &__desc {
    font-size: 12.5px;
    color: rgba(0, 0, 0, 0.45);
  }

  &__btn {
    margin-top: 10px;
  }
}

/* ===== 底部 ===== */
.llj-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;

  &__hint {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    max-width: 68%;
  }

  &__btns {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }
}

/* ===== 编辑弹窗：分区表单 ===== */
.led-section {
  padding-bottom: 4px;
  margin-bottom: 10px;

  & + .led-section {
    border-top: 1px solid #f0f1f5;
    padding-top: 14px;
  }

  &--last {
    margin-bottom: 0;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13.5px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    margin-bottom: 14px;

    &::before {
      content: '';
      width: 3px;
      height: 13px;
      border-radius: 2px;
      background: @llj-primary;
    }
  }

  &__hint {
    font-size: 12px;
    font-weight: 400;
    color: rgba(0, 0, 0, 0.4);
  }
}

/* 判断方式选项卡 */
.led-modes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.led-mode {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #e4e6ec;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@llj-primary, 55%);
  }

  &.active {
    border-color: @llj-primary;
    background: fade(@llj-primary, 4%);
    box-shadow: 0 0 0 2px fade(@llj-primary, 12%);
  }

  &__icon {
    font-size: 22px;
    color: rgba(0, 0, 0, 0.45);
    flex-shrink: 0;
    transition: color 0.2s;
  }

  &.active &__icon {
    color: @llj-primary;
  }

  &__body {
    min-width: 0;
  }

  &__name {
    font-size: 13.5px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    line-height: 1.4;
  }

  &__desc {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 2px;
    line-height: 1.5;
  }

  &__check {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 16px;
    color: @llj-primary;
    opacity: 0;
    transform: scale(0.6);
    transition: opacity 0.15s, transform 0.15s;
  }

  &.active &__check {
    opacity: 1;
    transform: scale(1);
  }
}

/* 视频窗口参数容器 */
.led-video-box {
  padding: 12px 14px 0;
  margin-bottom: 8px;
  border: 1px dashed #d6dae3;
  border-radius: 8px;
  background: #fafbfc;
}
</style>
