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
          <Icon icon="mdi:brain" :size="22" class="llj-title__icon" />
          <div>
            <div class="llj-title__text">大模型后处理规则</div>
            <div class="llj-title__sub">{{ headerSubtitle }}</div>
          </div>
        </div>
        <div class="llj-title__actions">
          <Button
            type="primary"
            size="small"
            :disabled="disabled || !taskId"
            @click="openEditor()"
          >
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
        <AAlert
          class="llj-intro"
          type="info"
          show-icon
          message="规则按优先级匹配告警：检测对象/事件类别留空表示匹配全部，多规则命中时仅最高优先级规则生效；开启「二次判断」后，大模型确认事件成立才发送通知。"
        />

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
              <Button size="small" :disabled="loading" @click="reload">
                重试
              </Button>
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
                <div class="llj-card__title">{{ rule.rule_name }}</div>
                <a-switch
                  size="small"
                  :checked="rule.enabled"
                  :disabled="disabled"
                  checked-children="启"
                  un-checked-children="停"
                  @change="(checked: boolean) => toggleEnabled(rule, checked)"
                />
              </div>
              <div class="llj-card__tags">
                <template v-if="rule.match_objects?.length || rule.match_events?.length">
                  <a-tag v-for="obj in rule.match_objects || []" :key="'o' + obj" color="blue">{{ obj }}</a-tag>
                  <a-tag v-for="evt in rule.match_events || []" :key="'e' + evt" color="purple">{{ evt }}</a-tag>
                </template>
                <a-tag v-else color="default">匹配全部</a-tag>
                <a-tag v-if="rule.judge_mode === 'video'" color="orange">视频研判</a-tag>
                <a-tag v-else color="cyan">图片研判</a-tag>
                <a-tag v-if="rule.secondary_judge" color="red">门控通知</a-tag>
                <a-tag v-else color="green">仅回写</a-tag>
              </div>
              <div class="llj-card__meta">
                <span>{{ agentName(rule.agent_id) }}</span>
                <span v-if="rule.judge_mode === 'video'">
                  前{{ rule.video_pre_seconds }}s / 后{{ rule.video_post_seconds }}s
                </span>
                <span>失败:{{ failPolicyLabel(rule.fail_policy) }}</span>
                <span>优先级 {{ rule.priority }}</span>
                <span v-if="rule.min_interval_sec > 0">研判间隔 ≥{{ rule.min_interval_sec }}s</span>
                <div class="llj-card__actions">
                  <Button type="link" size="small" :disabled="disabled" @click="openEditor(rule)">
                    编辑
                  </Button>
                  <a-popconfirm
                    title="删除后该规则不再参与研判，确定删除？"
                    ok-text="删除"
                    cancel-text="取消"
                    :disabled="disabled"
                    @confirm="handleDelete(rule)"
                  >
                    <Button type="link" size="small" danger :disabled="disabled">删除</Button>
                  </a-popconfirm>
                </div>
              </div>
            </div>
          </template>
          <AEmpty
            v-else
            description="暂无研判规则，点击右上角「新增规则」创建"
            :image="false"
            class="llj-empty"
          />
        </div>
      </div>
    </Spin>

    <a-modal
      v-model:open="editorOpen"
      :title="editingRule ? '编辑研判规则' : '新增研判规则'"
      :confirm-loading="saving"
      width="720"
      ok-text="保存"
      cancel-text="取消"
      @ok="handleSave"
    >
      <a-form ref="ruleFormRef" :model="ruleForm" :rules="ruleRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="规则名称" name="rule_name">
              <a-input v-model:value="ruleForm.rule_name" placeholder="如：夜间入侵二次确认" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="优先级" help="越大越优先匹配">
              <a-input-number v-model:value="ruleForm.priority" :min="1" :max="100" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="匹配检测对象"
              help="留空=全部；与告警对象/检测类别（小写）匹配，回车可输入多个"
            >
              <a-select
                v-model:value="ruleForm.match_objects"
                mode="tags"
                :token-separators="[',', '，']"
                placeholder="如 person、vehicle"
                :options="objectOptions"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="匹配事件类型" help="留空=全部；回车可输入多个">
              <a-select
                v-model:value="ruleForm.match_events"
                mode="tags"
                :token-separators="[',', '，']"
                placeholder="如 intrusion、fighting"
                :options="eventOptions"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="绑定智能体" name="agent_id" help="AI 模块专家（rag_expert），携带知识库上下文研判">
              <a-select
                v-model:value="ruleForm.agent_id"
                placeholder="请选择智能体"
                show-search
                :options="agentOptions"
                option-filter-prop="label"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="大模型" help="留空=智能体/系统默认模型">
              <a-select
                v-model:value="ruleForm.model_id"
                placeholder="默认模型"
                allow-clear
                show-search
                :options="modelOptions"
                option-filter-prop="label"
              />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="判断方式" name="judge_mode">
              <a-radio-group v-model:value="ruleForm.judge_mode">
                <a-radio value="image">事件图片（快、省）</a-radio>
                <a-radio value="video">事件间隔视频（更准）</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
          <template v-if="ruleForm.judge_mode === 'video'">
            <a-col :span="8">
              <a-form-item label="事件前窗口（秒）">
                <a-input-number v-model:value="ruleForm.video_pre_seconds" :min="0" :max="300" style="width: 100%" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="事件后窗口（秒）">
                <a-input-number v-model:value="ruleForm.video_post_seconds" :min="0" :max="300" style="width: 100%" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="切片最大时长（秒）">
                <a-input-number v-model:value="ruleForm.video_max_seconds" :min="1" :max="300" style="width: 100%" />
              </a-form-item>
            </a-col>
          </template>
          <a-col :span="12">
            <a-form-item label="二次判断（门控通知）" name="secondary_judge" help="开启后：大模型确认事件成立才发送通知，驳回则抑制">
              <a-switch
                v-model:checked="ruleForm.secondary_judge"
                checked-children="门控"
                un-checked-children="仅回写"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="研判失败策略" name="fail_policy" help="大模型调用失败时通知如何处理">
              <a-select v-model:value="ruleForm.fail_policy" :options="failPolicyOptions" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="同任务最小研判间隔（秒）" help="0=不限，防止高频事件重复调用大模型">
              <a-input-number v-model:value="ruleForm.min_interval_sec" :min="0" :max="86400" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="强制 JSON 输出">
              <a-switch v-model:checked="ruleForm.require_json" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item
              label="提示词覆盖"
              help="留空=使用智能体默认提示词。可用占位符：{object_name}、{event}、{detections_json}"
            >
              <a-textarea
                v-model:value="ruleForm.prompt_override"
                :rows="3"
                placeholder="可选，覆盖智能体默认研判提示词"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { Alert as AAlert, Empty as AEmpty, Spin } from 'ant-design-vue';
import { PlusOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
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
const failPolicyOptions = [
  { label: 'skip：不改动原结果', value: 'skip' },
  { label: 'confirm：放行通知', value: 'confirm' },
  { label: 'reject：抑制通知', value: 'reject' },
];

function agentName(agentId: number): string {
  return experts.value.find((e) => e.id === agentId)?.name || `#${agentId}`;
}
function failPolicyLabel(policy: LlmFailPolicy): string {
  return failPolicyOptions.find((o) => o.value === policy)?.label.split('：')[0] || policy;
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
  try {
    // 后端为整体覆盖语义（rule_name 必填），展开记录仅改 enabled
    await updateLlmJudgeRule(record.id, { ...record, enabled: checked } as LlmJudgeRulePayload);
    record.enabled = checked;
    emit('changed');
  } catch (error: any) {
    createMessage.error(formatApiErrorMessage(error, '更新规则状态失败'));
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

  &__icon {
    color: #1677ff;
    flex-shrink: 0;
  }

  &__text {
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

.llj-intro {
  margin-bottom: 0;
}

.llj-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  min-width: 0;
}

.llj-load-error {
  margin-bottom: 0;
}

.llj-card {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  background: #fff;
  padding: 12px 14px;
  transition: border-color 0.15s, background 0.15s;

  &.off {
    opacity: 0.6;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__title {
    font-weight: 600;
    font-size: 14px;
    line-height: 1.4;
    word-break: break-word;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 10px;

    :deep(.ant-tag) {
      margin: 0;
    }
  }

  &__meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 16px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #f0f0f0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.55);
    line-height: 1.5;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-left: auto;
  }
}

.llj-empty {
  margin-top: 60px;
}

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
</style>
