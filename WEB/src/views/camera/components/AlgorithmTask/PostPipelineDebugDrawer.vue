<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="后处理规则调试"
    width="920"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
    :z-index="1300"
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="closeDrawer">关闭</Button>
        <Button type="primary" :loading="running" @click="handleRun">运行调试</Button>
      </div>
    </template>

    <Spin :spinning="loadingSample">
      <a-alert
        class="mb-3"
        type="info"
        show-icon
        message="使用样例推理事件试跑规则链或单个插件，查看每步 trace 与最终 pass/drop 结果。"
      />

      <a-tabs v-model:activeKey="debugMode">
        <a-tab-pane key="pipeline" tab="整链调试" />
        <a-tab-pane key="plugin" tab="单插件调试" />
      </a-tabs>

      <a-form layout="vertical" class="debug-form">
        <a-row :gutter="12">
          <a-col :span="8">
            <a-form-item label="调试模式">
              <a-select v-model:value="pipelineScope" :disabled="debugMode !== 'pipeline'">
                <a-select-option value="full">执行完整规则链</a-select-option>
                <a-select-option value="until">执行到指定插件</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="截止插件" v-if="debugMode === 'pipeline' && pipelineScope === 'until'">
              <a-select v-model:value="untilPlugin" placeholder="选择插件">
                <a-select-option v-for="step in pipelineSteps" :key="step.plugin" :value="step.plugin">
                  {{ pluginLabel(allPlugins, step.plugin) }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="目标插件" v-else-if="debugMode === 'plugin'">
              <a-select v-model:value="targetPlugin" placeholder="选择插件">
                <a-select-option v-for="step in pipelineSteps" :key="step.plugin" :value="step.plugin">
                  {{ pluginLabel(allPlugins, step.plugin) }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="设备 ID">
              <a-input v-model:value="deviceId" placeholder="用于加载检测区域" allow-clear />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="样例推理事件 (InferEvent JSON)">
          <a-textarea v-model:value="eventJson" :rows="10" class="mono-textarea" />
          <div class="mt-2">
            <Button size="small" @click="loadSampleFromServer" :disabled="!taskId">从任务加载样例</Button>
            <Button size="small" class="ml-2" @click="formatEventJson">格式化 JSON</Button>
          </div>
        </a-form-item>
      </a-form>

      <template v-if="result || pluginResult">
        <a-divider orientation="left">调试结果</a-divider>
        <div v-if="result && debugMode === 'pipeline'" class="result-banner" :class="resultClass">
          <span class="result-label">结果</span>
          <span class="result-value">{{ pipelineResultLabel }}</span>
          <span v-if="result.drop_reason" class="result-reason">原因：{{ result.drop_reason }}</span>
        </div>

        <div v-if="pluginResult" class="plugin-result mt-3">
          <pre class="json-block">{{ pretty(pluginResult) }}</pre>
        </div>

        <div v-if="traceSteps.length" class="trace-list mt-3">
          <div v-for="(step, idx) in traceSteps" :key="`${step.plugin}-${idx}`" class="trace-item">
            <div class="trace-head">
              <span class="trace-index">{{ idx + 1 }}</span>
              <span class="trace-plugin">{{ pluginLabel(allPlugins, step.plugin) }}</span>
              <a-tag size="small">{{ step.decision }}</a-tag>
              <span class="trace-latency">{{ step.latency_ms?.toFixed?.(2) ?? step.latency_ms }} ms</span>
            </div>
            <div class="trace-body">
              检测框 {{ step.detections_in }} → {{ step.detections_out }}
              <span v-if="step.drop_reason"> · 丢弃原因 {{ step.drop_reason }}</span>
            </div>
            <div v-if="step.enrichment_patch && Object.keys(step.enrichment_patch).length" class="trace-enrich">
              <pre class="json-block sm">{{ pretty(step.enrichment_patch) }}</pre>
            </div>
          </div>
        </div>

        <a-collapse v-if="result.alert_payload" class="mt-3" ghost>
          <a-collapse-panel key="alert" header="告警载荷预览">
            <pre class="json-block">{{ pretty(result.alert_payload) }}</pre>
          </a-collapse-panel>
        </a-collapse>
      </template>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Spin } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  debugPostPipeline,
  debugPostPlugin,
  getPostSampleEvent,
  type PostPipelineDebugResult,
  type PostPipelineStep,
  type PostPluginDebugResult,
  type PostPluginMeta,
  type PostStepTrace,
} from '@/api/device/post_pipeline';
import { localSampleEvent, pluginLabel } from './postPipelineCatalog';

defineOptions({ name: 'PostPipelineDebugDrawer' });

const props = defineProps<{
  taskId?: number | null;
  taskContext?: {
    id?: number | null;
    task_name?: string;
    task_type?: string;
    device_ids?: string[];
  };
  pipelineSteps: PostPipelineStep[];
  allPlugins: PostPluginMeta[];
}>();

const { createMessage } = useMessage();

const debugMode = ref<'pipeline' | 'plugin'>('pipeline');
const pipelineScope = ref<'full' | 'until'>('full');
const untilPlugin = ref<string>('');
const targetPlugin = ref<string>('');
const deviceId = ref('');
const eventJson = ref('');
const running = ref(false);
const loadingSample = ref(false);
const result = ref<PostPipelineDebugResult | null>(null);
const pluginResult = ref<PostPluginDebugResult | null>(null);
const regions = ref<Array<Record<string, unknown>>>([]);

const traceSteps = computed<PostStepTrace[]>(() => result.value?.trace || []);

const pipelineResultLabel = computed(() => {
  const r = result.value?.result;
  if (r === 'pass') return '放行 (pass)';
  if (r === 'drop') return '丢弃 (drop)';
  return r || '-';
});

const resultClass = computed(() => {
  const r = result.value?.result;
  if (r === 'pass') return 'is-pass';
  if (r === 'drop') return 'is-drop';
  return '';
});

function pretty(v: unknown) {
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function parseEvent(): Record<string, unknown> | null {
  try {
    const data = JSON.parse(eventJson.value || '{}');
    if (!data || typeof data !== 'object') throw new Error('无效 JSON');
    return data as Record<string, unknown>;
  } catch (e: any) {
    createMessage.error(e?.message || '事件 JSON 无效');
    return null;
  }
}

function formatEventJson() {
  const data = parseEvent();
  if (data) eventJson.value = pretty(data);
}

async function loadSampleFromServer() {
  if (!props.taskId) {
    eventJson.value = pretty(localSampleEvent(props.taskContext));
    return;
  }
  loadingSample.value = true;
  try {
    const data = await getPostSampleEvent(props.taskId, {
      device_id: deviceId.value || undefined,
    });
    eventJson.value = pretty(data.event);
    regions.value = data.regions || [];
    if (!deviceId.value && data.event?.device_id) {
      deviceId.value = String(data.event.device_id);
    }
  } catch (e: any) {
    createMessage.warning(e?.message || '加载样例失败，已使用本地默认');
    eventJson.value = pretty(localSampleEvent(props.taskContext));
  } finally {
    loadingSample.value = false;
  }
}

async function handleRun() {
  const event = parseEvent();
  if (!event) return;
  running.value = true;
  result.value = null;
  pluginResult.value = null;
  try {
    if (debugMode.value === 'plugin') {
      const plugin = targetPlugin.value || props.pipelineSteps[0]?.plugin;
      if (!plugin) {
        createMessage.warning('请选择要调试的插件');
        return;
      }
      const step = props.pipelineSteps.find((s) => s.plugin === plugin);
      pluginResult.value = await debugPostPlugin({
        plugin,
        endpoint: step?.endpoint,
        params: step?.params || {},
        event: event as any,
        regions: regions.value,
        task: props.taskId
          ? { id: props.taskId, task_type: props.taskContext?.task_type, task_name: props.taskContext?.task_name }
          : undefined,
      });
      createMessage.success('单插件调试完成');
      return;
    }

    const body: Parameters<typeof debugPostPipeline>[0] = {
      event: event as any,
      pipeline_override: props.pipelineSteps,
      regions: regions.value,
    };
    if (pipelineScope.value === 'until' && untilPlugin.value) {
      body.until_plugin = untilPlugin.value;
    }
    if (props.taskId) {
      body.task = {
        id: props.taskId,
        task_type: props.taskContext?.task_type,
        task_name: props.taskContext?.task_name,
      };
    }
    result.value = await debugPostPipeline(body);
    createMessage.success('规则链调试完成');
  } catch (e: any) {
    createMessage.error(e?.message || '调试失败，请确认 POST 服务已开启 POST_DEBUG_HTTP');
  } finally {
    running.value = false;
  }
}

const [register, { closeDrawer }] = useDrawerInner(async (data?: {
  mode?: 'pipeline' | 'plugin';
  plugin?: string;
}) => {
  debugMode.value = data?.mode || 'pipeline';
  targetPlugin.value = data?.plugin || props.pipelineSteps[0]?.plugin || '';
  untilPlugin.value = data?.plugin || props.pipelineSteps[props.pipelineSteps.length - 1]?.plugin || '';
  deviceId.value = props.taskContext?.device_ids?.[0] || '';
  result.value = null;
  pluginResult.value = null;
  await loadSampleFromServer();
});
</script>

<style lang="less" scoped>
.debug-form {
  margin-top: 4px;
}

.mono-textarea {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

.result-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  border: 1px solid #e5e6eb;
  background: #f7f8fa;

  &.is-pass {
    border-color: #b7eb8f;
    background: #f6ffed;
  }

  &.is-drop {
    border-color: #ffa39e;
    background: #fff2f0;
  }
}

.result-label {
  color: #86909c;
  font-size: 12px;
}

.result-value {
  font-weight: 600;
}

.result-reason {
  color: #4e5969;
  font-size: 12px;
}

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trace-item {
  border: 1px solid #e5e6eb;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
}

.trace-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trace-index {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #165dff;
  color: #fff;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.trace-plugin {
  font-weight: 600;
}

.trace-latency {
  margin-left: auto;
  color: #86909c;
  font-size: 12px;
}

.trace-body {
  margin-top: 6px;
  color: #4e5969;
  font-size: 12px;
}

.json-block {
  margin: 0;
  padding: 10px;
  background: #f7f8fa;
  border-radius: 4px;
  font-size: 12px;
  overflow: auto;
  max-height: 280px;

  &.sm {
    max-height: 120px;
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
