<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :width="drawerWidth"
    placement="right"
    :loading="loading"
    :showFooter="true"
    :showOkBtn="false"
    :showCancelBtn="false"
    :maskClosable="false"
    destroy-on-close
    root-class-name="unattended-label-drawer"
  >
    <template #title>
      <div class="detail-drawer-header">
        <div class="detail-drawer-header__icon">
          <Icon icon="ant-design:cluster-outlined" :size="18" />
        </div>
        <div class="detail-drawer-header__line">
          <span class="detail-drawer-header__title">{{ COPY.drawerTitle }}</span>
          <span class="detail-drawer-header__sep">·</span>
          <span class="detail-drawer-header__desc">{{ COPY.drawerDesc }}</span>
          <template v-if="taskRunning && taskId">
            <span class="detail-drawer-header__sep">·</span>
            <span class="detail-drawer-header__meta">任务 #{{ taskId }}</span>
          </template>
        </div>
        <Tag v-if="taskStatus" :color="taskStatusTagColor">{{ statusLabel }}</Tag>
      </div>
    </template>

    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleClose">{{ taskRunning ? COPY.footer.minimize : COPY.footer.close }}</Button>
        <div class="footer-nav">
          <template v-if="activeTab === 'config' && !taskRunning">
            <Button v-if="configStep > 0" @click="configStep -= 1">{{ COPY.footer.prev }}</Button>
            <Button
              v-if="!isLastStep"
              type="primary"
              :disabled="!canProceedStep"
              @click="handleNext"
            >
              {{ COPY.footer.next }}
            </Button>
            <Button
              v-else
              type="primary"
              :loading="submitting"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              {{ COPY.deploy.start }}
            </Button>
          </template>
          <template v-else-if="taskRunning">
            <Button v-if="taskStatus !== 'PAUSED'" @click="handlePause">{{ COPY.footer.pause }}</Button>
            <Button v-if="taskStatus === 'PAUSED'" type="primary" @click="handleResume">{{ COPY.footer.resume }}</Button>
            <PopConfirmButton
              danger
              ghost
              :title="COPY.footer.cancelConfirm"
              @confirm="handleCancel"
            >
              {{ COPY.footer.cancel }}
            </PopConfirmButton>
          </template>
        </div>
      </div>
    </template>

    <div class="detail-drawer-content">
      <Tabs v-model:activeKey="activeTab" class="detail-tabs">
        <Tabs.TabPane key="config" :tab="COPY.tabs.config" :disabled="taskRunning">
          <Steps class="setup-steps" :current="configStep" :items="stepItems" />

          <div class="setup-content-card">
            <div v-show="configStep === 0" class="step-panel-body">
              <Form :label-col="SETUP_FORM_LABEL_COL" :wrapper-col="SETUP_FORM_WRAPPER_COL">
                <FormItem :label="COPY.model.originFilter">
                  <RadioButtonGroup v-model:value="originFilter" :options="originFilterOptions" />
                </FormItem>
                <FormItem :label="COPY.model.label" required>
                  <Select
                    v-model:value="form.model_id"
                    show-search
                    :filter-option="filterOption"
                    :placeholder="COPY.model.empty"
                    :options="filteredModelOptions"
                    style="width: 100%"
                    @change="handleModelChange"
                  />
                  <p class="form-hint">{{ COPY.model.hint }}</p>
                </FormItem>
                <FormItem label="检测类别" required>
                  <Select
                    v-model:value="form.text_prompts"
                    mode="tags"
                    placeholder="与模型 class 一致，如 helmet, person"
                    style="width: 100%"
                  />
                </FormItem>
                <Alert v-if="selectedModelOrigin" type="info" show-icon :message="selectedModelLabel">
                  <template #description>
                    来源：{{ MODEL_ORIGIN_LABELS[selectedModelOrigin] }}
                  </template>
                </Alert>
              </Form>
            </div>

            <div v-show="configStep === 1" class="step-panel-body">
              <Form :label-col="SETUP_FORM_LABEL_COL" :wrapper-col="SETUP_FORM_WRAPPER_COL">
                <FormItem label="视频流抽帧任务" required>
                  <div class="camera-toolbar">
                    <Button size="small" :disabled="!frameTasks.length" @click="toggleAllFrameTasks">
                      {{ allFrameTasksSelected ? '取消全选' : COPY.cameras.selectAll }}
                    </Button>
                    <Button size="small" type="link" @click="emit('open-frame-tasks')">
                      {{ COPY.cameras.goFrameTasks }}
                    </Button>
                    <span class="camera-count">已选 {{ form.frame_task_ids.length }} / {{ frameTasks.length }}</span>
                  </div>
                  <CheckboxGroup v-model:value="form.frame_task_ids" class="frame-task-list">
                    <div v-for="ft in frameTasks" :key="ft.id" class="frame-task-item">
                      <Checkbox :value="ft.id">
                        {{ ft.taskName || `任务 #${ft.id}` }}
                        <span v-if="ft.rtmpUrl" class="frame-task-url">{{ ft.rtmpUrl }}</span>
                      </Checkbox>
                    </div>
                  </CheckboxGroup>
                  <Empty v-if="!frameTasks.length" :description="COPY.cameras.empty" />
                  <p v-else class="form-hint">{{ COPY.cameras.hint }}</p>
                </FormItem>
              </Form>
            </div>

            <div v-show="configStep === 2" class="step-panel-body">
              <Form :label-col="SETUP_FORM_LABEL_COL" :wrapper-col="SETUP_FORM_WRAPPER_COL">
                <FormItem :label="COPY.deploy.execution">
                  <RadioButtonGroup v-model:value="form.execution_mode" :options="EXECUTION_MODE_OPTIONS" />
                  <p v-if="form.execution_mode === 'cluster'" class="form-hint">
                    {{ COPY.deploy.scheduleHint }}
                    <Button type="link" size="small" @click="goNodeManage">{{ COPY.deploy.nodeSync }}</Button>
                  </p>
                </FormItem>
                <FormItem :label="COPY.deploy.duration">
                  <InputNumber v-model:value="form.duration_hours" :min="1" :max="48" style="width: 100%" />
                </FormItem>
                <FormItem :label="COPY.deploy.interval">
                  <InputNumber v-model:value="form.capture_interval_sec" :min="5" :max="600" style="width: 100%" />
                </FormItem>
                <FormItem :label="COPY.deploy.annotatedOnly">
                  <Switch v-model:checked="form.keep_annotated_images_only" />
                  <p class="form-hint">{{ COPY.deploy.annotatedOnlyHint }}</p>
                </FormItem>
                <FormItem :label="COPY.deploy.autoExport">
                  <Checkbox v-model:checked="form.auto_export">启用</Checkbox>
                </FormItem>
              </Form>
            </div>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="monitor" :tab="COPY.tabs.monitor">
          <div class="monitor-pane">
            <template v-if="activeTask">
              <Progress
                :percent="progressPercent"
                :status="taskStatus === 'FAILED' ? 'exception' : taskStatus === 'COMPLETED' ? 'success' : 'active'"
              />
              <Description
                class="setup-desc monitor-desc"
                :use-collapse="false"
                bordered
                :column="2"
                :schema="monitorDescSchema"
                :data="monitorDescData"
              />
              <section v-if="subtasks.length" class="subtasks-section">
                <div class="subtasks-title">{{ COPY.monitor.subtasks }}</div>
                <Table
                  size="small"
                  :pagination="false"
                  :columns="subtaskColumns"
                  :data-source="subtasks"
                  row-key="id"
                />
              </section>
              <Alert
                v-if="taskStatus === 'COMPLETED'"
                type="success"
                show-icon
                class="monitor-alert"
                :message="COPY.monitor.completed"
              />
              <Alert v-if="taskStatus === 'PAUSED'" type="warning" show-icon class="monitor-alert" :message="COPY.monitor.paused" />
              <Alert v-if="taskStatus === 'FAILED'" type="error" show-icon class="monitor-alert" :message="activeTask.error_message || COPY.monitor.failed" />
              <CollapseContainer v-if="pipelineLogs.length" :title="COPY.monitor.logs">
                <CodeEditor class="log-editor" :value="logContent" readonly bordered />
              </CollapseContainer>
            </template>
            <Empty v-else :description="COPY.monitor.empty" />
          </div>
        </Tabs.TabPane>
      </Tabs>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, onDeactivated, onUnmounted, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  Alert,
  Checkbox,
  CheckboxGroup,
  Empty,
  Form,
  FormItem,
  InputNumber,
  Progress,
  Select,
  Steps,
  Switch,
  Table,
  Tabs,
  Tag,
} from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button';
import { CodeEditor } from '@/components/CodeEditor';
import { CollapseContainer } from '@/components/Container';
import { Description } from '@/components/Description';
import type { DescItem } from '@/components/Description';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { RadioButtonGroup } from '@/components/Form';
import { Icon } from '@/components/Icon';
import { getModelDetail, getModelPage, parseModelClassPayload } from '@/api/device/model';
import { getDatasetFrameTaskPage } from '@/api/device/dataset';
import {
  startSamPipeline,
  getAutoLabelTask,
  listAutoLabelTasks,
  getAutoLabelSubtasks,
  pauseAutoLabelTask,
  resumeAutoLabelTask,
  cancelAutoLabelTask,
} from '@/api/device/auto-label';
import { useMessage } from '@/hooks/web/useMessage';
import {
  filterModelsByOrigin,
  formatModelOptionLabel,
  MODEL_ORIGIN_LABELS,
  resolveModelOrigin,
  type ModelListItem,
  type ModelOrigin,
} from '@/utils/modelSource';
import {
  COPY,
  EXECUTION_MODE_OPTIONS,
  SETUP_FORM_LABEL_COL,
  SETUP_FORM_WRAPPER_COL,
} from './constants';

defineOptions({ name: 'UnattendedLabelDrawer' });

const props = defineProps<{
  datasetId: number;
}>();

const emit = defineEmits<{
  success: [payload: { taskId: number }];
  'open-frame-tasks': [];
  register: [];
}>();

const { createMessage } = useMessage();
const router = useRouter();

const drawerWidth = 'calc(100vw - 240px)';
const loading = ref(false);
const submitting = ref(false);
const activeTab = ref<'config' | 'monitor'>('config');
const configStep = ref(0);
const originFilter = ref<ModelOrigin | 'all'>('all');
const models = ref<ModelListItem[]>([]);
const frameTasks = ref<Array<{ id: number; taskName?: string; rtmpUrl?: string }>>([]);
const taskId = ref<number | null>(null);
const activeTask = ref<Record<string, any> | null>(null);
const taskStatus = ref('');
const subtasks = ref<Record<string, any>[]>([]);
let pollTimer: ReturnType<typeof setInterval> | null = null;

function resolveDatasetId(): number | null {
  const datasetId = Number(props.datasetId);
  return Number.isInteger(datasetId) && datasetId > 0 ? datasetId : null;
}

function stopPolling(): void {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
}

const form = reactive({
  model_id: undefined as number | undefined,
  text_prompts: [] as string[],
  frame_task_ids: [] as number[],
  execution_mode: 'local' as 'local' | 'cluster',
  duration_hours: 8,
  capture_interval_sec: 30,
  keep_annotated_images_only: true,
  auto_export: true,
});

const stepItems = computed(() =>
  [COPY.steps.model, COPY.steps.cameras, COPY.steps.deploy].map((s, i) => ({
    title: s.title,
    description: s.desc,
    status: (i < configStep.value ? 'finish' : i === configStep.value ? 'process' : 'wait') as
      | 'wait'
      | 'process'
      | 'finish',
  })),
);

const originFilterOptions = computed(() => [
  { label: COPY.model.originAll, value: 'all' },
  ...(['upload', 'auto_label', 'smart_label', 'train'] as ModelOrigin[]).map((o) => ({
    label: MODEL_ORIGIN_LABELS[o],
    value: o,
  })),
]);

const filteredModelOptions = computed(() =>
  filterModelsByOrigin(models.value, originFilter.value).map((m) => ({
    label: formatModelOptionLabel(m),
    value: m.id,
  })),
);

const selectedModel = computed(() => models.value.find((m) => m.id === form.model_id));
const selectedModelOrigin = computed(() =>
  selectedModel.value ? resolveModelOrigin(selectedModel.value) : null,
);
const selectedModelLabel = computed(() =>
  selectedModel.value ? formatModelOptionLabel(selectedModel.value) : '',
);

const allFrameTasksSelected = computed(
  () => frameTasks.value.length > 0 && form.frame_task_ids.length === frameTasks.value.length,
);

const isLastStep = computed(() => configStep.value >= 2);
const taskRunning = computed(() =>
  ['PENDING', 'PROCESSING', 'PAUSED'].includes(taskStatus.value),
);

const canProceedStep = computed(() => {
  if (configStep.value === 0) return Boolean(form.model_id && form.text_prompts.length > 0);
  if (configStep.value === 1) return form.frame_task_ids.length > 0;
  return true;
});

const canSubmit = computed(() =>
  Boolean(form.model_id && form.text_prompts.length && form.frame_task_ids.length),
);

const taskStatusTagColor = computed(() => {
  const map: Record<string, string> = {
    PENDING: 'default',
    PROCESSING: 'processing',
    PAUSED: 'warning',
    COMPLETED: 'success',
    FAILED: 'error',
    CANCELLED: 'default',
  };
  return map[taskStatus.value] || 'default';
});

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    PENDING: '排队中',
    PROCESSING: '运行中',
    PAUSED: '已暂停',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消',
  };
  return map[taskStatus.value] || taskStatus.value || '-';
});

const pipelineConfig = computed(() => activeTask.value?.pipeline_config ?? {});

const pipelineLogs = computed(() => {
  const logs = pipelineConfig.value?.logs;
  return Array.isArray(logs) ? logs : [];
});

const logContent = computed(() =>
  pipelineLogs.value
    .map((log: { time?: string; message?: string }) => `${formatLogTime(log.time)}  ${log.message}`)
    .join('\n'),
);

const progressPercent = computed(() => {
  const cfg = pipelineConfig.value;
  const captured = Number(cfg.captured_count ?? 0);
  const labeled = Number(cfg.labeled_count ?? 0);
  const total = Math.max(captured, labeled, 1);
  return Math.min(100, Math.round((labeled / total) * 100));
});

const monitorDescData = computed(() => ({
  execution_mode: activeTask.value?.execution_mode === 'cluster' ? '集群多节点' : '本机',
  camera_count: pipelineConfig.value.camera_count ?? subtasks.value.length ?? '-',
  captured_count: pipelineConfig.value.captured_count ?? 0,
  labeled_count: pipelineConfig.value.labeled_count ?? activeTask.value?.success_count ?? 0,
  duration_hours: pipelineConfig.value.duration_hours ?? '-',
  keep_annotated_images_only: pipelineConfig.value.keep_annotated_images_only === false ? '否' : '是',
  status: statusLabel.value,
}));

const monitorDescSchema = computed<DescItem[]>(() => [
  { field: 'execution_mode', label: '执行方式' },
  { field: 'camera_count', label: '摄像头路数' },
  { field: 'captured_count', label: '已抽帧' },
  { field: 'labeled_count', label: '已标注' },
  { field: 'duration_hours', label: '计划时长(h)' },
  { field: 'keep_annotated_images_only', label: COPY.deploy.annotatedOnly },
  { field: 'status', label: '状态' },
]);

const subtaskColumns = [
  { title: '抽帧任务', dataIndex: 'frame_task_name', key: 'frame_task_name' },
  {
    title: '运行节点',
    key: 'runtime_node',
    customRender: ({ record }: { record: Record<string, unknown> }) => {
      const host = record.assigned_node_host || '';
      const nodeId = record.assigned_node_id;
      if (!host && nodeId == null) return '--';
      return nodeId != null ? `${host || '—'} / #${nodeId}` : String(host);
    },
  },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '已标注', dataIndex: 'labeled_count', key: 'labeled_count', width: 80 },
];

function filterOption(input: string, option: { label?: string }): boolean {
  return (option?.label ?? '').toLowerCase().includes(input.toLowerCase());
}

function formatLogTime(iso?: string): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

function handleNext(): void {
  if (!canProceedStep.value) {
    createMessage.warning('请补全当前步骤必填项');
    return;
  }
  configStep.value += 1;
}

function goNodeManage(): void {
  router.push({ path: '/node', query: { tab: '1' } });
}

function toggleAllFrameTasks(): void {
  form.frame_task_ids = allFrameTasksSelected.value
    ? []
    : frameTasks.value.map((ft) => ft.id);
}

async function handleModelChange(): Promise<void> {
  if (!form.model_id) return;
  try {
    const res = await getModelDetail(form.model_id);
    const { classNames } = parseModelClassPayload(res);
    if (classNames.length) form.text_prompts = [...classNames];
  } catch {
    /* keep */
  }
}

async function loadModels(): Promise<void> {
  try {
    const res = await getModelPage({ pageNo: 1, pageSize: 200, has_weights: true });
    const list = res?.data?.list ?? res?.list ?? res?.data ?? [];
    models.value = Array.isArray(list) ? list : [];
  } catch {
    models.value = [];
  }
}

async function loadFrameTasks(): Promise<void> {
  const datasetId = resolveDatasetId();
  if (!datasetId) {
    frameTasks.value = [];
    return;
  }
  try {
    const res = await getDatasetFrameTaskPage({
      datasetId,
      pageNo: 1,
      pageSize: 200,
    });
    const list = res?.data?.list ?? res?.list ?? [];
    frameTasks.value = list;
    const availableIds = new Set(list.map((ft: { id: number }) => ft.id));
    form.frame_task_ids = form.frame_task_ids.filter((id) => availableIds.has(id));
    if (!form.frame_task_ids.length && list.length) {
      form.frame_task_ids = list.map((ft: { id: number }) => ft.id);
    }
  } catch {
    frameTasks.value = [];
  }
}

defineExpose({ reloadFrameTasks: loadFrameTasks });

async function loadSubtasks(datasetId = resolveDatasetId()): Promise<void> {
  if (!taskId.value || !datasetId) return;
  try {
    const res = await getAutoLabelSubtasks(datasetId, taskId.value);
    const data = res?.data ?? res;
    subtasks.value = data?.subtasks ?? [];
  } catch {
    subtasks.value = [];
  }
}

async function resumeActivePipeline(): Promise<void> {
  const datasetId = resolveDatasetId();
  if (!datasetId) return;
  loading.value = true;
  try {
    const res = await listAutoLabelTasks(datasetId, { page: 1, page_size: 10 });
    const list = res?.data?.list ?? res?.list ?? [];
    const running = list.find(
      (t: { status?: string; phase?: string }) =>
        t.phase === 'PIPELINE' && ['PENDING', 'PROCESSING', 'PAUSED'].includes(t.status || ''),
    );
    if (running) {
      taskId.value = running.id;
      activeTask.value = running;
      taskStatus.value = running.status || '';
      activeTab.value = 'monitor';
      await loadSubtasks(datasetId);
      startPolling();
    }
  } catch {
    /* ignore */
  } finally {
    loading.value = false;
  }
}

const [register, { closeDrawer, getOpen }] = useDrawerInner(async () => {
  stopPolling();
  activeTab.value = 'config';
  configStep.value = 0;
  form.model_id = undefined;
  form.text_prompts = [];
  form.frame_task_ids = [];
  form.execution_mode = 'local';
  form.duration_hours = 8;
  form.capture_interval_sec = 30;
  form.keep_annotated_images_only = true;
  form.auto_export = true;
  originFilter.value = 'all';
  taskId.value = null;
  activeTask.value = null;
  taskStatus.value = '';
  subtasks.value = [];
  await Promise.all([loadModels(), loadFrameTasks()]);
  await resumeActivePipeline();
});

if (getOpen) {
  watch(getOpen, (open) => {
    if (!open) stopPolling();
  });
}

async function handleSubmit(): Promise<void> {
  if (!canSubmit.value || submitting.value) return;
  const datasetId = resolveDatasetId();
  if (!datasetId) {
    createMessage.error('数据集ID无效，请重新进入数据集详情页');
    return;
  }
  submitting.value = true;
  try {
    const res = await startSamPipeline(datasetId, {
      text_prompts: form.text_prompts,
      model_id: form.model_id,
      duration_hours: form.duration_hours,
      capture_interval_sec: form.capture_interval_sec,
      keep_annotated_images_only: form.keep_annotated_images_only,
      auto_export: form.auto_export,
      execution_mode: form.execution_mode,
      frame_task_ids: form.frame_task_ids,
      confidence_threshold: 0.5,
      annotation_type: 'rectangle',
      strategy: {
        initial_model_id: form.model_id,
        skip_sam_cold_start: true,
        auto_train_yolo: false,
        sam_supplement_enabled: false,
        yolo_confidence: 0.5,
      },
    });
    const id = res?.data?.task_id ?? res?.task_id;
    if (!id) {
      createMessage.error('启动失败：未返回任务 ID');
      return;
    }
    taskId.value = id;
    taskStatus.value = 'PENDING';
    activeTab.value = 'monitor';
    createMessage.success(res?.msg ?? res?.data?.msg ?? '无人值守扩充已启动');
    emit('success', { taskId: id });
    startPolling();
  } catch (e: any) {
    const msg = e?.response?.data?.msg || e?.message || '启动失败';
    if (String(msg).includes('已有进行中')) {
      createMessage.warning(msg);
      await resumeActivePipeline();
    } else {
      createMessage.error(msg);
    }
  } finally {
    submitting.value = false;
  }
}

function startPolling(): void {
  stopPolling();
  const pollingDatasetId = resolveDatasetId();
  if (!pollingDatasetId || !taskId.value) {
    if (!pollingDatasetId) {
      createMessage.warning('数据集ID无效，已停止任务状态查询');
    }
    return;
  }
  let consecutiveFailures = 0;
  let pollInFlight = false;
  const poll = async () => {
    if (pollInFlight || !taskId.value) return;
    if (resolveDatasetId() !== pollingDatasetId) {
      stopPolling();
      return;
    }
    pollInFlight = true;
    try {
      const res = await getAutoLabelTask(pollingDatasetId, taskId.value);
      consecutiveFailures = 0;
      const task = res?.data ?? res;
      activeTask.value = task;
      taskStatus.value = task?.status || '';
      if (task?.execution_mode === 'cluster') await loadSubtasks(pollingDatasetId);
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(taskStatus.value)) {
        stopPolling();
        if (taskStatus.value === 'COMPLETED') {
          createMessage.success(COPY.monitor.completed);
          emit('success', { taskId: taskId.value });
        }
      }
    } catch {
      consecutiveFailures += 1;
      if (consecutiveFailures >= 5) {
        stopPolling();
        createMessage.warning('任务状态查询连续失败，已停止自动刷新');
      }
    } finally {
      pollInFlight = false;
    }
  };
  void poll();
  pollTimer = setInterval(poll, 3000);
}

function handleClose(): void {
  stopPolling();
  closeDrawer();
}

async function handlePause(): Promise<void> {
  if (!taskId.value) return;
  const datasetId = resolveDatasetId();
  if (!datasetId) return;
  try {
    await pauseAutoLabelTask(datasetId, taskId.value);
    taskStatus.value = 'PAUSED';
    createMessage.success('任务已暂停');
  } catch (e: any) {
    createMessage.error(e?.message || '暂停失败');
  }
}

async function handleResume(): Promise<void> {
  if (!taskId.value) return;
  const datasetId = resolveDatasetId();
  if (!datasetId) return;
  try {
    await resumeAutoLabelTask(datasetId, taskId.value);
    taskStatus.value = 'PROCESSING';
    createMessage.success('任务已恢复');
    startPolling();
  } catch (e: any) {
    createMessage.error(e?.message || '恢复失败');
  }
}

async function handleCancel(): Promise<void> {
  if (!taskId.value) return;
  const datasetId = resolveDatasetId();
  if (!datasetId) return;
  try {
    await cancelAutoLabelTask(datasetId, taskId.value);
    taskStatus.value = 'CANCELLED';
    stopPolling();
    createMessage.success('任务已取消');
  } catch (e: any) {
    createMessage.error(e?.message || '取消失败');
  }
}

onDeactivated(stopPolling);
onUnmounted(stopPolling);
</script>

<style scoped lang="less">
.detail-drawer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: rgba(59, 130, 246, 0.12);
    color: #3b82f6;
  }

  &__line {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 6px;
    flex: 1;
  }

  &__title {
    font-weight: 600;
    font-size: 15px;
  }

  &__sep {
    color: rgba(0, 0, 0, 0.25);
  }

  &__desc,
  &__meta {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.setup-steps {
  margin-bottom: 20px;
}

.setup-content-card {
  padding: 8px 4px;
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}

.camera-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.camera-count {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-left: auto;
}

.frame-task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.frame-task-item {
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
}

.frame-task-url {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: rgba(0, 0, 0, 0.35);
  word-break: break-all;
}

.footer-buttons {
  display: flex;
  justify-content: space-between;
  width: 100%;
}

.footer-nav {
  display: flex;
  gap: 8px;
}

.monitor-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.monitor-desc {
  margin-top: 8px;
}

.monitor-alert {
  margin-top: 4px;
}

.subtasks-section {
  margin-top: 8px;
}

.subtasks-title {
  font-weight: 500;
  margin-bottom: 8px;
}

.log-editor {
  min-height: 160px;
}
</style>
