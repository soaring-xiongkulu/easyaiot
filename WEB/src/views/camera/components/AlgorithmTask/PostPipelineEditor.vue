<template>
  <div class="post-pipeline-editor">
    <a-alert type="info" show-icon class="mb-3">
      <template #message>后处理规则</template>
      <template #description>
        <div>
          检测结果按下列步骤依次处理，通过后再进入标准告警流程。默认
          <code>区域闸门 → 放行</code>。设备「区域检测」供区域闸门使用；与基础配置中的「业务脚本」相互独立。
        </div>
      </template>
    </a-alert>

    <a-alert
      v-if="postProcessEnabled && !hasUserScript"
      type="warning"
      show-icon
      class="mb-3"
      message="已开启业务脚本，但规则中尚未加入用户脚本步骤"
    >
      <template #description>
        <div>
          若需在规则链路中执行脚本，可插入「用户脚本」步骤；否则脚本按独立业务脚本路径运行。
          <a-button
            size="small"
            type="link"
            :disabled="disabled"
            @click="insertUserScript"
          >
            插入用户脚本
          </a-button>
        </div>
      </template>
    </a-alert>

    <div class="summary mb-3">
      <a-tag :color="summaryTone">{{ summaryText }}</a-tag>
      <span class="summary-hint">{{ summaryHint }}</span>
    </div>

    <div class="toolbar mb-2">
      <a-space wrap>
        <a-button size="small" :disabled="disabled" @click="addStep">添加步骤</a-button>
        <a-button size="small" :disabled="disabled" @click="resetDefault">恢复默认</a-button>
        <a-button
          size="small"
          type="primary"
          :disabled="!taskId"
          :loading="saving"
          @click="savePipelineOnly"
        >
          保存规则
        </a-button>
        <a-button size="small" type="primary" ghost @click="openDebug">规则调试</a-button>
        <a-button size="small" type="link" @click="goPluginManage">管理后处理插件</a-button>
      </a-space>
    </div>

    <div v-if="!steps.length" class="empty-hint">当前无步骤（保存为空时将按「仅放行」处理）。</div>

    <div v-for="(record, index) in steps" :key="record._key" class="step-card">
      <div class="step-head">
        <div class="step-title">
          <span class="step-idx">#{{ index + 1 }}</span>
          <a-tag :color="kindMeta(record.plugin).color">{{ kindMeta(record.plugin).label }}</a-tag>
          <a-select
            v-model:value="record.plugin"
            :disabled="disabled"
            style="min-width: 220px"
            show-search
            :options="pluginOptions"
            @change="() => onPluginChange(record)"
          />
          <a-tag v-if="pluginStatusTag(record.plugin)" :color="pluginStatusTag(record.plugin)!.color">
            {{ pluginStatusTag(record.plugin)!.text }}
          </a-tag>
        </div>
        <a-space>
          <span class="muted">启用</span>
          <a-switch v-model:checked="record.enabled" :disabled="disabled" @change="emitChange" />
          <a-button size="small" type="link" :disabled="disabled || index === 0" @click="move(index, -1)">上移</a-button>
          <a-button
            size="small"
            type="link"
            :disabled="disabled || index === steps.length - 1"
            @click="move(index, 1)"
          >
            下移
          </a-button>
          <a-button size="small" type="link" danger :disabled="disabled" @click="remove(index)">删除</a-button>
        </a-space>
      </div>

      <div class="step-body">
        <a-row :gutter="12">
          <a-col :span="8">
            <div class="field-label">失败策略</div>
            <a-select
              v-model:value="record.fail_strategy"
              :disabled="disabled || isBuiltin(record.plugin)"
              style="width: 100%"
              :options="failStrategyOptions"
              @change="emitChange"
            />
          </a-col>

          <a-col v-if="record.plugin === 'region_gate'" :span="8">
            <div class="field-label">命中模式</div>
            <a-select
              v-model:value="record.hitMode"
              :disabled="disabled"
              style="width: 100%"
              :options="hitModeOptions"
              @change="() => syncRegionParams(record)"
            />
          </a-col>

          <a-col v-if="!isBuiltin(record.plugin)" :span="8">
            <div class="field-label">版本（可选）</div>
            <a-input
              v-model:value="record.version"
              :disabled="disabled"
              placeholder="缺省用已登记版本"
              @blur="emitChange"
            />
          </a-col>
        </a-row>

        <div v-if="record.plugin === 'default_pass'" class="hint-line">
          放行步骤：通过后进入标准告警流程。建议保留在末尾。
        </div>
        <div v-else-if="record.plugin === 'user_script'" class="hint-line">
          在规则链路中执行用户脚本。与基础配置「业务脚本」开关是两条可并存的能力。
        </div>
        <div v-else-if="record.plugin === 'region_gate'" class="hint-line">
          未配置启用区域时自动跳过。请在任务摄像头上配置「区域检测」。
        </div>

        <div v-if="!isBuiltin(record.plugin) || record.plugin === 'user_script'" class="params-block">
          <div class="field-label">高级参数（JSON）</div>
          <a-textarea
            v-model:value="record.paramsText"
            :disabled="disabled"
            :rows="2"
            class="mono"
            placeholder="{}"
            @blur="() => onParamsBlur(record)"
          />
        </div>
      </div>
    </div>

    <a-modal v-model:open="debugOpen" title="规则调试" width="900px" :footer="null" destroy-on-close>
      <a-form layout="vertical">
        <a-alert
          type="info"
          show-icon
          class="mb-3"
          message="在线回放当前规则"
          description="使用样例或自定义检测事件，逐步查看过滤与放行结果。一般无需填写直连地址。"
        />
        <a-form-item label="检测事件 JSON">
          <a-textarea v-model:value="debugEvent" :rows="8" class="mono" />
        </a-form-item>
        <a-collapse ghost>
          <a-collapse-panel key="adv" header="高级：直连调试地址（兜底）">
            <a-input v-model:value="debugBase" placeholder="http://127.0.0.1:8089" addon-before="地址" />
            <div class="hint-line">勾选「强制直连」时由浏览器直接请求，可能受跨域限制。</div>
            <a-checkbox v-model:checked="forceDirect">强制直连</a-checkbox>
          </a-collapse-panel>
        </a-collapse>
        <a-space class="mb-3">
          <a-button type="primary" :loading="debugLoading" @click="runDebug">执行</a-button>
          <a-button @click="fillSampleEvent">填入样例事件</a-button>
        </a-space>

        <div v-if="debugParsed" class="debug-result">
          <div class="debug-summary">
            <a-tag :color="debugParsed.result === 'pass' ? 'green' : 'orange'">
              结果：{{ debugResultLabel }}
            </a-tag>
            <span v-if="debugParsed.drop_reason" class="drop-reason">
              原因：{{ debugParsed.drop_reason }}
            </span>
            <span v-if="debugParsed.alert_payload" class="muted">将产生告警</span>
            <span v-else class="muted">不会产生告警</span>
          </div>

          <div v-if="(debugParsed.trace || []).length" class="trace-list">
            <div class="field-label">执行步骤</div>
            <div v-for="(t, i) in debugParsed.trace" :key="i" class="trace-item">
              <div class="trace-head">
                <span class="step-idx">#{{ i + 1 }}</span>
                <strong>{{ pluginDisplayName(t.plugin) }}</strong>
                <a-tag>{{ decisionLabel(t.decision) }}</a-tag>
                <span class="muted">{{ t.detections_in ?? '?' }} → {{ t.detections_out ?? '?' }} 个目标</span>
                <span class="muted">{{ formatLatency(t.latency_ms) }}</span>
              </div>
              <div v-if="t.drop_reason" class="drop-reason">丢弃：{{ t.drop_reason }}</div>
            </div>
          </div>

          <a-collapse ghost>
            <a-collapse-panel key="raw" header="原始结果">
              <pre class="debug-out mono">{{ debugRaw }}</pre>
            </a-collapse-panel>
            <a-collapse-panel v-if="debugParsed.alert_payload" key="alert" header="告警内容预览">
              <pre class="debug-out mono">{{ JSON.stringify(debugParsed.alert_payload, null, 2) }}</pre>
            </a-collapse-panel>
          </a-collapse>
        </div>
        <pre v-else-if="debugRaw" class="debug-out mono">{{ debugRaw }}</pre>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useMessage } from '@/hooks/web/useMessage';
import {
  debugPostPipeline,
  debugPostPipelineDirect,
  listPostPlugins,
  type PostDebugPipelineResult,
  type PostPluginItem,
} from '@/api/device/post_plugin';
import { updateAlgorithmTask } from '@/api/device/algorithm_task';

export interface PipelineStepUI {
  _key: string;
  plugin: string;
  enabled: boolean;
  fail_strategy: string;
  paramsText: string;
  hitMode?: string;
  version?: string;
  endpoint?: string;
}

const props = defineProps<{
  modelValue?: any[] | null;
  disabled?: boolean;
  taskId?: number | null;
  postProcessEnabled?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: any[] | null): void;
}>();

const { createMessage } = useMessage();
const router = useRouter();
const steps = ref<PipelineStepUI[]>([]);
const registered = ref<PostPluginItem[]>([]);

const BUILTIN = new Set(['region_gate', 'default_pass', 'user_script']);

const builtinOptions = [
  { label: '区域闸门', value: 'region_gate' },
  { label: '放行', value: 'default_pass' },
  { label: '用户脚本', value: 'user_script' },
];

const failStrategyOptions = [
  { label: '失败时跳过本步', value: 'fail_open' },
  { label: '失败时丢弃告警', value: 'fail_closed' },
];

const hitModeOptions = [
  { label: '目标中心点落在区域内', value: 'center' },
  { label: '目标任一角点落在区域内', value: 'any_corner' },
];

const pluginOptions = computed(() => [
  ...builtinOptions,
  ...registered.value.map((p) => ({
    label: `${p.name || p.id}${p.service?.status === 'running' ? ' · 运行中' : ''}`,
    value: p.id,
  })),
]);

const hasUserScript = computed(() =>
  steps.value.some((s) => s.plugin === 'user_script' && s.enabled !== false),
);

const enabledSteps = computed(() => steps.value.filter((s) => s.enabled !== false));

const summaryText = computed(() => {
  if (!enabledSteps.value.length) return '当前：仅放行';
  return enabledSteps.value.map((s) => kindMeta(s.plugin).short).join(' → ');
});

const summaryHint = computed(() => {
  if (!enabledSteps.value.length) return '未启用任何步骤时，检测结果将直接进入标准告警流程。';
  const hasGate = enabledSteps.value.some((s) => s.plugin === 'region_gate');
  if (hasGate) return '含区域闸门：区域外的目标会被过滤，不会产生告警。';
  return '未启用区域闸门：不会按区域过滤目标。';
});

const summaryTone = computed(() => {
  if (!enabledSteps.value.length) return 'default';
  if (enabledSteps.value.some((s) => s.plugin === 'region_gate')) return 'blue';
  return 'green';
});

let keySeq = 0;
function newKey() {
  keySeq += 1;
  return `s-${keySeq}-${Date.now()}`;
}

function isBuiltin(plugin: string) {
  return BUILTIN.has(plugin);
}

function kindMeta(plugin: string) {
  if (plugin === 'region_gate') return { label: '过滤', short: '区域闸门', color: 'orange' };
  if (plugin === 'default_pass') return { label: '放行', short: '放行', color: 'green' };
  if (plugin === 'user_script') return { label: '富化', short: '用户脚本', color: 'purple' };
  return { label: '外置', short: plugin || '插件', color: 'cyan' };
}

function pluginStatusTag(plugin: string) {
  if (isBuiltin(plugin)) return null;
  const p = registered.value.find((x) => x.id === plugin);
  if (!p) return { text: '未登记', color: 'red' };
  if (!p.enabled) return { text: '已禁用', color: 'default' };
  const st = p.service?.status || 'stopped';
  if (st === 'running') return { text: '运行中', color: 'green' };
  if (st === 'stopped') return { text: '已停止', color: 'default' };
  return { text: st, color: 'gold' };
}

function pluginDisplayName(plugin?: string) {
  if (!plugin) return '—';
  const builtin = builtinOptions.find((o) => o.value === plugin);
  if (builtin) return builtin.label;
  const reg = registered.value.find((p) => p.id === plugin);
  return reg?.name || plugin;
}

function decisionLabel(decision?: string) {
  if (decision === 'pass') return '通过';
  if (decision === 'drop') return '丢弃';
  if (decision === 'continue') return '继续';
  return decision || '—';
}

function parseParams(text: string) {
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return {};
  }
}

function toUI(list?: any[] | null): PipelineStepUI[] {
  if (!list || !Array.isArray(list) || list.length === 0) {
    // null / 缺省：编辑器展示默认链；真正写库由用户保存决定
    return defaultSteps();
  }
  return list.map((s) => {
    const params = s.params && typeof s.params === 'object' ? s.params : {};
    return {
      _key: newKey(),
      plugin: String(s.plugin || ''),
      enabled: s.enabled !== false,
      fail_strategy: s.fail_strategy || 'fail_open',
      paramsText: JSON.stringify(params || {}),
      hitMode: String(params.hit_mode || 'center'),
      version: s.version,
      endpoint: s.endpoint,
    };
  });
}

function defaultSteps(): PipelineStepUI[] {
  return [
    {
      _key: newKey(),
      plugin: 'region_gate',
      enabled: true,
      fail_strategy: 'fail_open',
      paramsText: '{"hit_mode":"center"}',
      hitMode: 'center',
    },
    {
      _key: newKey(),
      plugin: 'default_pass',
      enabled: true,
      fail_strategy: 'fail_open',
      paramsText: '{}',
    },
  ];
}

function toModel(list: PipelineStepUI[]): any[] {
  return list.map((s) => {
    let params: any = parseParams(s.paramsText);
    if (s.plugin === 'region_gate') {
      params = { ...params, hit_mode: s.hitMode || 'center' };
    }
    const out: any = {
      plugin: s.plugin,
      enabled: s.enabled,
      params,
      fail_strategy: s.fail_strategy || 'fail_open',
    };
    if (s.version) out.version = s.version;
    if (s.endpoint) out.endpoint = s.endpoint;
    return out;
  });
}

function emitChange() {
  emit('update:modelValue', toModel(steps.value));
}

function syncRegionParams(record: PipelineStepUI) {
  const params = parseParams(record.paramsText);
  params.hit_mode = record.hitMode || 'center';
  record.paramsText = JSON.stringify(params);
  emitChange();
}

function onPluginChange(record: PipelineStepUI) {
  if (record.plugin === 'region_gate') {
    record.hitMode = record.hitMode || 'center';
    syncRegionParams(record);
    return;
  }
  if (record.plugin === 'default_pass') {
    record.paramsText = '{}';
  }
  emitChange();
}

function onParamsBlur(record: PipelineStepUI) {
  try {
    JSON.parse(record.paramsText || '{}');
    emitChange();
  } catch {
    createMessage.warning('params 不是合法 JSON');
  }
}

function addStep() {
  const ext = registered.value.find((p) => p.enabled)?.id;
  steps.value.push({
    _key: newKey(),
    plugin: ext || 'user_script',
    enabled: true,
    fail_strategy: 'fail_open',
    paramsText: '{}',
  });
  emitChange();
}

function insertUserScript() {
  const passIdx = steps.value.findIndex((s) => s.plugin === 'default_pass');
  const step: PipelineStepUI = {
    _key: newKey(),
    plugin: 'user_script',
    enabled: true,
    fail_strategy: 'fail_open',
    paramsText: '{}',
  };
  if (passIdx >= 0) {
    steps.value.splice(passIdx, 0, step);
  } else {
    steps.value.push(step);
  }
  emitChange();
}

function resetDefault() {
  steps.value = defaultSteps();
  emitChange();
}

function remove(index: number) {
  steps.value.splice(index, 1);
  emitChange();
}

function move(index: number, delta: number) {
  const j = index + delta;
  if (j < 0 || j >= steps.value.length) return;
  const arr = steps.value.slice();
  const t = arr[index];
  arr[index] = arr[j];
  arr[j] = t;
  steps.value = arr;
  emitChange();
}

function goPluginManage() {
  router.push('/post-plugin/index');
}

watch(
  () => props.modelValue,
  (v) => {
    const next = toUI(v);
    const cur = JSON.stringify(toModel(steps.value));
    const incoming = JSON.stringify(toModel(next));
    if (cur !== incoming) {
      steps.value = next;
    }
  },
  { immediate: true, deep: true },
);

onMounted(async () => {
  try {
    const data = await listPostPlugins();
    const arr = Array.isArray(data) ? data : (data as any)?.data || [];
    registered.value = arr;
  } catch {
    registered.value = [];
  }
});

const debugOpen = ref(false);
const debugBase = ref(localStorage.getItem('POST_DEBUG_BASE') || 'http://127.0.0.1:8089');
const forceDirect = ref(false);
const debugEvent = ref('');
const debugRaw = ref('');
const debugParsed = ref<PostDebugPipelineResult | null>(null);
const debugLoading = ref(false);
const saving = ref(false);

const debugResultLabel = computed(() => {
  const r = debugParsed.value?.result;
  if (r === 'pass') return '通过';
  if (r === 'drop') return '丢弃';
  return r || '—';
});

async function savePipelineOnly() {
  if (!props.taskId) {
    createMessage.warning('请先保存任务基础配置');
    return;
  }
  saving.value = true;
  try {
    const pipe = toModel(steps.value);
    emit('update:modelValue', pipe);
    await updateAlgorithmTask(props.taskId, { post_pipeline: pipe } as any);
    createMessage.success('规则已保存（运行中任务将立即生效）');
  } catch (e: any) {
    createMessage.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

function fillSampleEvent() {
  debugEvent.value = JSON.stringify(
    {
      schema: 'infer_event.v1',
      event_kind: 'infer',
      correlation_id: `debug-${Date.now()}`,
      task_id: props.taskId || 1,
      task_type: 'realtime',
      device_id: 'cam1',
      timestamp: new Date().toISOString(),
      frame_width: 1920,
      frame_height: 1080,
      detections: [{ bbox: [100, 100, 200, 300], class_name: 'person', confidence: 0.9 }],
    },
    null,
    2,
  );
}

function openDebug() {
  if (!debugEvent.value) fillSampleEvent();
  debugParsed.value = null;
  debugRaw.value = '';
  debugOpen.value = true;
}

function formatLatency(ms?: number) {
  if (ms == null || Number.isNaN(ms)) return '';
  return `${Number(ms).toFixed(1)} ms`;
}

async function runDebug() {
  debugLoading.value = true;
  debugRaw.value = '';
  debugParsed.value = null;
  try {
    localStorage.setItem('POST_DEBUG_BASE', debugBase.value);
    const event = JSON.parse(debugEvent.value);
    if (props.taskId && !event.task_id) event.task_id = props.taskId;
    const body = {
      event,
      pipeline_override: toModel(steps.value),
    };
    let res: PostDebugPipelineResult;
    if (forceDirect.value) {
      res = await debugPostPipelineDirect(debugBase.value, body);
    } else {
      const data = await debugPostPipeline(body);
      res = (data as any)?.data && (data as any).result === undefined ? (data as any).data : (data as any);
    }
    debugParsed.value = res;
    debugRaw.value = JSON.stringify(res, null, 2);
  } catch (e: any) {
    createMessage.error(e?.message || e?.msg || '调试失败');
    debugRaw.value = String(e?.message || e?.msg || e);
  } finally {
    debugLoading.value = false;
  }
}
</script>

<style scoped>
.mb-2 {
  margin-bottom: 8px;
}
.mb-3 {
  margin-bottom: 12px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
}
.summary {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.summary-hint,
.hint-line,
.muted {
  color: #666;
  font-size: 12px;
}
.hint-line {
  margin-top: 8px;
}
.step-card {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  background: #fafafa;
}
.step-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.step-idx {
  font-weight: 600;
  color: #1677ff;
}
.step-body {
  margin-top: 12px;
}
.field-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}
.params-block {
  margin-top: 10px;
}
.empty-hint {
  color: #999;
  padding: 12px 0;
}
.debug-result {
  margin-top: 8px;
}
.debug-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.drop-reason {
  color: #d46b08;
  font-size: 12px;
}
.trace-list {
  margin-bottom: 8px;
}
.trace-item {
  border-left: 3px solid #1677ff;
  padding: 6px 10px;
  margin: 6px 0;
  background: #fff;
}
.trace-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.debug-out {
  margin-top: 8px;
  max-height: 280px;
  overflow: auto;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
}
</style>
