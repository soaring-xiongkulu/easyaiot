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
    root-class-name="sam-auto-label-drawer"
  >
    <template #title>
      <div class="detail-drawer-header">
        <div class="detail-drawer-header__icon">
          <Icon icon="ant-design:deployment-unit-outlined" :size="18" />
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
        <div v-if="taskStatus" class="detail-drawer-header__tags">
          <Tag :color="taskStatusTagColor">{{ statusLabel }}</Tag>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleClose">{{ taskRunning ? COPY.footer.minimize : COPY.footer.close }}</Button>
        <div class="footer-nav">
          <template v-if="activeTab === 'config' && !taskRunning">
            <Button v-if="configStep > 0" @click="handleConfigPrev">{{ COPY.footer.prev }}</Button>
            <Button
              v-if="!isLastConfigStep"
              type="primary"
              :disabled="!canProceedConfigStep"
              @click="handleConfigNext"
            >
              {{ COPY.footer.next }}
            </Button>
            <Button
              v-else
              type="primary"
              :loading="starting"
              :disabled="!canStart"
              @click="startTask"
            >
              {{ COPY.footer.start }}
            </Button>
          </template>
          <template v-else>
            <Button v-if="taskRunning && taskStatus !== 'PAUSED'" @click="handlePause">{{ COPY.footer.pause }}</Button>
            <Button v-if="taskStatus === 'PAUSED'" type="primary" @click="handleResume">{{ COPY.footer.resume }}</Button>
            <PopConfirmButton
              v-if="taskRunning"
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
          <div class="config-wizard">
            <div class="setup-steps-card">
              <Steps
                class="setup-steps"
                :current="configStep"
                :items="configStepItems"
                @change="handleConfigStepChange"
              />
            </div>

            <div class="setup-content-card">
              <div class="step-panel-head">
                <h3 class="step-panel-title">{{ currentStepCopy.title }}</h3>
              </div>

              <div v-show="activeConfigStepKey === 'basic'" class="step-panel-body">
                <Form
                  :label-col="SETUP_FORM_LABEL_COL"
                  :wrapper-col="SETUP_FORM_WRAPPER_COL"
                  class="setup-resource-form"
                >
                  <FormItem :label="COPY.form.classes" required>
                    <Select
                      v-model:value="form.text_prompts"
                      mode="tags"
                      :placeholder="COPY.form.classesPlaceholder"
                      style="width: 100%"
                    />
                    <p class="form-hint">{{ COPY.form.classesHint }}</p>
                  </FormItem>

                  <FormItem :label="COPY.form.annotation">
                    <RadioButtonGroup
                      v-model:value="form.annotation_type"
                      :options="annotationTypeOptions"
                    />
                  </FormItem>
                </Form>
              </div>

              <div v-show="activeConfigStepKey === 'batch'" class="step-panel-body">
                <Form
                  :label-col="SETUP_FORM_LABEL_COL"
                  :wrapper-col="SETUP_FORM_WRAPPER_COL"
                  class="setup-resource-form"
                >
                  <FormItem :label="COPY.form.batchLimit">
                    <div class="field-control">
                      <span class="field-value">{{ form.bootstrap_limit }} 张</span>
                      <Slider v-model:value="form.bootstrap_limit" :min="50" :max="2000" :step="50" />
                    </div>
                  </FormItem>
                  <FormItem :label="COPY.form.batchSelection">
                    <Select v-model:value="form.bootstrap_selection" style="width: 100%">
                      <SelectOption value="unlabeled_first">未标注优先</SelectOption>
                      <SelectOption value="unlabeled_only">仅未标注</SelectOption>
                      <SelectOption value="random">随机抽样</SelectOption>
                    </Select>
                  </FormItem>
                </Form>
              </div>
            </div>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane key="monitor" :tab="COPY.tabs.monitor">
          <div class="monitor-pane">
            <template v-if="activeTask">
              <section class="monitor-section">
                <div class="monitor-section__head">
                  <span class="monitor-section__title">{{ COPY.monitor.progress }}</span>
                </div>
                <Progress
                  :percent="progressPercent"
                  :status="taskStatus === 'FAILED' ? 'exception' : taskStatus === 'COMPLETED' ? 'success' : 'active'"
                />
              </section>

              <section class="monitor-section">
                <div class="monitor-section__title">{{ COPY.monitor.metrics }}</div>
                <Description
                  :use-collapse="false"
                  bordered
                  :column="3"
                  :schema="monitorDescSchema"
                  :data="monitorDescData"
                  class="setup-desc"
                />
              </section>

              <Alert
                v-if="bootstrapQualityAlert"
                :type="bootstrapQualityAlert.type"
                show-icon
                class="monitor-alert sam-quality-alert"
              >
                <template #message>{{ bootstrapQualityAlert.title }}</template>
                <template #description>
                  <p>{{ bootstrapQualityAlert.desc }}</p>
                  <p v-if="bootstrapStatus" class="sam-quality-stats">
                    识别率 {{ bootstrapStatus.recognition_rate_pct ?? 0 }}%
                    （有检出 {{ bootstrapStatus.sam_hit_count ?? 0 }} 张 /
                    空结果 {{ bootstrapStatus.sam_empty_count ?? 0 }} 张，
                    阈值 {{ bootstrapStatus.min_hit_rate_pct ?? 30 }}%）
                  </p>
                  <Space v-if="bootstrapQualityAlert.showActions" class="sam-quality-actions">
                    <Button size="small" :loading="resetLoading" @click="handleResetBootstrap">
                      恢复冷启动标注
                    </Button>
                    <Button size="small" type="primary" @click="emitOpenAutoLabel">
                      改用自动标注（YOLO）
                    </Button>
                  </Space>
                  <Space v-else-if="bootstrapStatus && !bootstrapStatus.review_passed" class="sam-quality-actions">
                    <Button size="small" type="primary" :loading="reviewLoading" @click="handleSubmitReview">
                      抽检通过，继续训练
                    </Button>
                  </Space>
                </template>
              </Alert>

              <Alert
                v-if="taskStatus === 'COMPLETED' && !bootstrapQualityAlert"
                type="success"
                show-icon
                class="monitor-alert"
                message="SAM 冷启动标注已完成"
              />
              <Alert v-if="taskStatus === 'PAUSED'" type="warning" show-icon class="monitor-alert" :message="COPY.monitor.paused" />
              <Alert v-if="taskStatus === 'CANCELLED'" type="error" show-icon class="monitor-alert" :message="COPY.monitor.cancelled" />
              <Alert
                v-if="taskStatus === 'FAILED'"
                type="error"
                show-icon
                class="monitor-alert"
                :message="activeTask.error_message || COPY.monitor.failed"
              />

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
import { computed, onUnmounted, reactive, ref, watch } from 'vue';
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
  Slider,
  Space,
  Steps,
  Tabs,
  Tag,
} from 'ant-design-vue';
import { Button, PopConfirmButton } from '@/components/Button';
import { CodeEditor } from '@/components/CodeEditor';
import { CollapseContainer } from '@/components/Container';
import { Description } from '@/components/Description';
import type { DescItem } from '@/components/Description';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Icon } from '@/components/Icon';
import {
  startSamBootstrap,
  getAutoLabelTask,
  listAutoLabelTasks,
  pauseAutoLabelTask,
  resumeAutoLabelTask,
  cancelAutoLabelTask,
  getSamBootstrapStatus,
  resetSamBootstrapAnnotations,
  completeSamBootstrapReview,
  trainBootstrapSmallModel,
} from '@/api/device/auto-label';
import type { SamBootstrapStatus } from '@/api/device/auto-label';
import { useMessage } from '@/hooks/web/useMessage';
import { SETUP_FORM_LABEL_COL, SETUP_FORM_WRAPPER_COL } from '@/views/node/utils/constants';

const SelectOption = Select.Option;

defineOptions({ name: 'SamAutoLabelDrawer' });

const props = defineProps<{
  datasetId: number;
}>();

const emit = defineEmits<{
  success: [payload: { taskId: number }];
  'open-auto-label': [];
  register: [];
}>();

const { createMessage } = useMessage();

const drawerWidth = 'calc(100vw - 200px)';

/** 界面文案 */
const COPY = {
  drawerTitle: '智能标注',
  drawerDesc: 'SAM 冷启动标注，对数据集中已有图片批量生成初始标注',
  tabs: { config: '参数配置', monitor: '运行监控' },
  footer: {
    close: '关闭',
    minimize: '收起',
    prev: '上一步',
    next: '下一步',
    start: '启动标注',
    pause: '暂停',
    resume: '继续',
    cancel: '取消任务',
    cancelConfirm: '确认取消？已标注数据保留。',
  },
  steps: {
    basic: { title: '基础配置', desc: '类别与格式' },
    batch: { title: '批量参数', desc: '规模与选图' },
  },
  form: {
    classes: '检测类别',
    classesHint: '英文类别名，须与后续 YOLO 训练 class 一致。',
    classesPlaceholder: '例如 helmet, vest, person',
    annotation: '标注格式',
    batchLimit: '首批规模',
    batchSelection: '选图规则',
  },
  monitor: {
    empty: '暂无任务记录，完成参数配置后点击「启动标注」。',
    progress: '执行进度',
    metrics: '运行指标',
    logs: '运行日志',
    paused: '任务已暂停，点击「继续」恢复。',
    cancelled: '任务已取消。',
    failed: '任务执行失败',
    samQualityLowTitle: 'SAM 识别率偏低，建议改用手动或 YOLO 自动标注',
    samQualityLowDesc:
      '当前行业数据可能不适合 SAM3 零样本识别。请恢复冷启动自动标注到初始状态，改用手动标注或使用已训练的 YOLO 模型进行自动标注。',
    samQualityOkTitle: 'SAM 冷启动识别率正常',
    samQualityOkDesc: '请随机抽查 10–20 张修正明显错误后确认通过，再进入训练。',
  },
} as const;

const annotationTypeOptions = [
  { label: '检测框', value: 'rectangle' },
  { label: '多边形分割', value: 'polygon' },
];

const loading = ref(false);
const starting = ref(false);
const activeTab = ref<'config' | 'monitor'>('config');
const configStep = ref(0);
const taskId = ref<number | null>(null);
const activeTask = ref<Record<string, any> | null>(null);
const taskStatus = ref('');
const bootstrapStatus = ref<SamBootstrapStatus | null>(null);
const resetLoading = ref(false);
const reviewLoading = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

const form = reactive({
  text_prompts: [] as string[],
  bootstrap_limit: 200,
  bootstrap_selection: 'unlabeled_first' as 'unlabeled_first' | 'unlabeled_only' | 'random',
  annotation_type: 'rectangle' as 'rectangle' | 'polygon',
  confidence_threshold: 0.45,
});

const canStart = computed(() => form.text_prompts.length > 0 && !starting.value);

type ConfigStepKey = 'basic' | 'batch';

interface ConfigStepDef {
  key: ConfigStepKey;
  title: string;
  description: string;
}

const configSteps = computed<ConfigStepDef[]>(() => [
  { key: 'basic', title: COPY.steps.basic.title, description: COPY.steps.basic.desc },
  { key: 'batch', title: COPY.steps.batch.title, description: COPY.steps.batch.desc },
]);

const currentStepCopy = computed(
  () => configSteps.value[configStep.value] ?? COPY.steps.basic,
);

const activeConfigStepKey = computed(
  () => configSteps.value[configStep.value]?.key ?? 'basic',
);

const isLastConfigStep = computed(
  () => configStep.value >= configSteps.value.length - 1,
);

const configStepItems = computed(() =>
  configSteps.value.map((step, index) => ({
    title: step.title,
    description: step.description,
    status: (index < configStep.value
      ? 'finish'
      : index === configStep.value
        ? 'process'
        : 'wait') as 'wait' | 'process' | 'finish',
  })),
);

const canProceedConfigStep = computed(() => {
  if (activeConfigStepKey.value === 'basic') return form.text_prompts.length > 0;
  return true;
});

const taskRunning = computed(() =>
  ['PENDING', 'PROCESSING', 'PAUSED'].includes(taskStatus.value),
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

const pipelineLogs = computed(() => {
  const logs = activeTask.value?.pipeline_config?.logs;
  return Array.isArray(logs) ? logs : [];
});

const monitorDescData = computed(() => ({
  labeled_count: activeTask.value?.success_count ?? 0,
  failed_count: activeTask.value?.failed_count ?? 0,
  total_images: activeTask.value?.total_images ?? form.bootstrap_limit,
  status: statusLabel.value,
}));

const monitorDescSchema = computed<DescItem[]>(() => [
  { field: 'total_images', label: '计划规模' },
  { field: 'labeled_count', label: '标注完成' },
  { field: 'failed_count', label: '失败张数' },
  { field: 'status', label: '任务状态' },
]);

const logContent = computed(() =>
  pipelineLogs.value
    .map((log) => `${formatLogTime(log.time)}  ${log.message}`)
    .join('\n'),
);

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

const progressPercent = computed(() => {
  if (!activeTask.value) return 0;
  const total = activeTask.value.total_images || form.bootstrap_limit;
  const done = activeTask.value.processed_images || 0;
  if (!total) return 0;
  return Math.min(100, Math.round((done / total) * 100));
});

const bootstrapQualityAlert = computed(() => {
  const status = bootstrapStatus.value;
  if (!status?.bootstrap_done && !status?.awaiting_sam_review) return null;
  if (status.review_recommended || status.awaiting_sam_review) {
    return {
      type: 'warning' as const,
      title: COPY.monitor.samQualityLowTitle,
      desc: COPY.monitor.samQualityLowDesc,
      showActions: true,
    };
  }
  if (status.sam_quality_passed && !status.review_passed) {
    return {
      type: 'info' as const,
      title: COPY.monitor.samQualityOkTitle,
      desc: COPY.monitor.samQualityOkDesc,
      showActions: false,
    };
  }
  return null;
});

watch(taskRunning, (running) => {
  if (running) activeTab.value = 'monitor';
});

function handleConfigPrev(): void {
  if (configStep.value > 0) configStep.value -= 1;
}

function handleConfigNext(): void {
  if (!canProceedConfigStep.value) {
    createMessage.warning('请补全当前步骤必填项');
    return;
  }
  if (!isLastConfigStep.value) configStep.value += 1;
}

function handleConfigStepChange(idx: number): void {
  if (idx <= configStep.value) {
    configStep.value = idx;
    return;
  }
  if (idx === configStep.value + 1 && canProceedConfigStep.value) {
    configStep.value = idx;
  }
}

const [register, { closeDrawer }] = useDrawerInner(async () => {
  activeTab.value = 'config';
  configStep.value = 0;
  await resumeActiveTask();
});

function formatLogTime(iso?: string): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

async function resumeActiveTask(): Promise<void> {
  loading.value = true;
  try {
    const res = await listAutoLabelTasks(props.datasetId, { page: 1, page_size: 5 });
    const data = res?.data ?? res;
    const list = data?.list ?? [];
    const running = list.find(
      (t: { status?: string; phase?: string }) =>
        ['PENDING', 'PROCESSING', 'PAUSED'].includes(t.status || '') && t.phase !== 'PIPELINE',
    );
    if (running) {
      taskId.value = running.id;
      activeTask.value = running;
      taskStatus.value = running.status;
      activeTab.value = 'monitor';
      startPolling();
    }
  } catch {
    /* ignore */
  } finally {
    loading.value = false;
  }
}

async function startTask(): Promise<void> {
  if (!canStart.value || starting.value) return;
  starting.value = true;
  try {
    const res = await startSamBootstrap(props.datasetId, {
      text_prompts: form.text_prompts,
      bootstrap_limit: form.bootstrap_limit,
      bootstrap_selection: form.bootstrap_selection,
      annotation_type: form.annotation_type,
      confidence_threshold: form.confidence_threshold,
      return_masks: form.annotation_type === 'polygon',
    });
    const id = res?.task_id ?? res?.data?.task_id;
    if (!id) {
      createMessage.error('启动失败：未返回任务 ID');
      return;
    }
    taskId.value = id;
    taskStatus.value = 'PENDING';
    activeTab.value = 'monitor';
    createMessage.success('SAM 标注任务已启动');
    emit('success', { taskId: id });
    startPolling();
  } catch (e: any) {
    const msg = e?.response?.data?.msg || e?.message || '启动失败';
    if (String(msg).includes('已有进行中')) {
      createMessage.warning(msg);
      await resumeActiveTask();
    } else {
      createMessage.error(msg);
    }
  } finally {
    starting.value = false;
  }
}

async function loadBootstrapStatus(): Promise<void> {
  try {
    const res = await getSamBootstrapStatus(props.datasetId);
    bootstrapStatus.value = (res?.data ?? res) as SamBootstrapStatus;
  } catch {
    bootstrapStatus.value = null;
  }
}

async function handleResetBootstrap(): Promise<void> {
  resetLoading.value = true;
  try {
    const res = await resetSamBootstrapAnnotations(props.datasetId);
    const count = res?.data?.reset_count ?? res?.reset_count ?? 0;
    createMessage.success(`已恢复 ${count} 张图片到未标注状态`);
    bootstrapStatus.value = null;
    await resumeActiveTask();
    emit('success', { taskId: taskId.value ?? 0 });
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '恢复失败');
  } finally {
    resetLoading.value = false;
  }
}

async function handleSubmitReview(): Promise<void> {
  reviewLoading.value = true;
  try {
    await completeSamBootstrapReview(props.datasetId, { review_passed: true });
    await trainBootstrapSmallModel(props.datasetId);
    createMessage.success('抽检已通过，YOLO 小模型训练已启动');
    await loadBootstrapStatus();
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '提交失败');
  } finally {
    reviewLoading.value = false;
  }
}

function emitOpenAutoLabel(): void {
  emit('open-auto-label');
  handleClose();
}

function startPolling(): void {
  if (pollTimer) clearInterval(pollTimer);
  const poll = async () => {
    if (!taskId.value) return;
    try {
      const res = await getAutoLabelTask(props.datasetId, taskId.value);
      const task = res?.data ?? res;
      activeTask.value = task;
      taskStatus.value = task?.status || '';
      const phase = task?.pipeline_config?.pipeline_phase;
      const bootstrapDone =
        taskStatus.value === 'COMPLETED'
        || phase === 'bootstrap_sam'
        || task?.phase === 'BOOTSTRAP'
        || task?.pipeline_config?.awaiting_sam_review;
      if (bootstrapDone || task?.pipeline_config?.awaiting_sam_review) {
        await loadBootstrapStatus();
      }
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(taskStatus.value)) {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = null;
        if (taskStatus.value === 'COMPLETED') {
          createMessage.success('智能标注任务已完成');
          emit('success', { taskId: taskId.value });
        }
      }
    } catch {
      /* 轮询失败不关闭 UI */
    }
  };
  poll();
  pollTimer = setInterval(poll, 2500);
}

function handleClose(): void {
  closeDrawer();
}

async function handlePause(): Promise<void> {
  if (!taskId.value) return;
  try {
    await pauseAutoLabelTask(props.datasetId, taskId.value);
    taskStatus.value = 'PAUSED';
    createMessage.success('任务已暂停');
  } catch (e: any) {
    createMessage.error(e?.message || '暂停失败');
  }
}

async function handleResume(): Promise<void> {
  if (!taskId.value) return;
  try {
    await resumeAutoLabelTask(props.datasetId, taskId.value);
    taskStatus.value = 'PROCESSING';
    createMessage.success('任务已恢复');
    startPolling();
  } catch (e: any) {
    createMessage.error(e?.message || '恢复失败');
  }
}

async function handleCancel(): Promise<void> {
  if (!taskId.value) return;
  try {
    await cancelAutoLabelTask(props.datasetId, taskId.value);
    taskStatus.value = 'CANCELLED';
    if (pollTimer) clearInterval(pollTimer);
    createMessage.success('任务已取消');
  } catch (e: any) {
    createMessage.error(e?.message || '取消失败');
  }
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<style lang="less" scoped>
@import '@/views/node/utils/setup-panel.less';

.detail-drawer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding-right: 32px;
}

.detail-drawer-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef4ff, #dce8ff);
  color: @node-primary;
  flex-shrink: 0;
}

.detail-drawer-header__line {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  font-size: 13px;
  line-height: 20px;
}

.detail-drawer-header__title {
  flex-shrink: 0;
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.detail-drawer-header__desc {
  flex-shrink: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(0, 0, 0, 0.55);
}

.detail-drawer-header__meta {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.4);
  font-size: 12px;
}

.detail-drawer-header__sep {
  flex-shrink: 0;
  margin: 0 6px;
  color: rgba(0, 0, 0, 0.25);
}

.detail-drawer-header__tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;

  :deep(.ant-tag) {
    margin: 0;
    line-height: 18px;
    font-size: 12px;
  }
}

.detail-drawer-content {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.config-wizard {
  display: flex;
  flex-direction: column;
  gap: @setup-section-gap;
}

.setup-steps-card {
  padding: @setup-section-header-padding;
  border-radius: @setup-panel-radius;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: @setup-panel-shadow;
}

.setup-steps {
  :deep(.ant-steps-item) {
    flex: 1;
    min-width: 0;
  }

  :deep(.ant-steps-item-icon) {
    width: 28px;
    height: 28px;
    line-height: 28px;
    font-size: 13px;
    margin-inline-end: 8px !important;
  }

  :deep(.ant-steps-item-title) {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.4;
  }

  :deep(.ant-steps-item-description) {
    font-size: 12px;
    line-height: 1.4;
    max-width: none;
    white-space: nowrap;
    color: rgba(0, 0, 0, 0.45);
  }

  :deep(.ant-steps-item-tail) {
    top: 14px;
  }

  :deep(.ant-steps-item-process .ant-steps-item-icon) {
    background: @node-primary;
    border-color: @node-primary;
  }
}

.setup-content-card {
  .setup-section-card();
  padding: 0;
  overflow: hidden;
}

.step-panel-head {
  padding: @setup-section-header-padding;
  border-bottom: 1px solid #f0f0f0;
}

.step-panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
  line-height: 1.4;
}

.step-panel-body {
  padding: @setup-section-body-padding;
}

.field-control {
  width: 100%;
}

.field-value {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: @node-primary;
  line-height: 1.4;
}

.checkbox-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}

.list-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
}

.list-panel-scroll {
  max-height: 240px;
}

.list-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
}

.list-panel-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;

  &:last-child {
    border-bottom: none;
  }
}

.list-panel-row__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.list-panel-row__title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.88);
  line-height: 1.4;
}

.list-panel-row__sub {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  word-break: break-all;
  line-height: 1.4;
}

.footer-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-nav {
  display: flex;
  gap: 8px;
}

.detail-tabs {
  :deep(.ant-tabs-nav) {
    margin-bottom: 0;
    padding: 0 4px;
    background: #fff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: @setup-panel-radius;
    box-shadow: @setup-panel-shadow;

    &::before {
      border-bottom: none;
    }
  }

  :deep(.ant-tabs-tab) {
    padding: 12px 24px;
    font-size: 14px;
  }

  :deep(.ant-tabs-content-holder) {
    padding-top: @setup-section-gap;
  }
}

.monitor-pane {
  .setup-section-card();
  padding: @setup-section-body-padding;
}

.monitor-section {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.monitor-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.monitor-section__title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
  line-height: 1.4;
}

.monitor-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.setup-desc {
  .setup-desc();
}

.pipeline-steps {
  margin-bottom: 20px;
}

.monitor-alert {
  margin-bottom: 16px;
}

.sam-quality-stats {
  margin: 8px 0 0;
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
}

.sam-quality-actions {
  margin-top: 12px;
}

.log-editor {
  height: 280px;
}

.text-muted {
  color: rgba(0, 0, 0, 0.35);
}

.setup-resource-form {
  :deep(.ant-form-item:last-child) {
    margin-bottom: 0;
  }
}
</style>

<style lang="less">
.sam-auto-label-drawer {
  .ant-drawer-header {
    padding: 10px 20px;
    min-height: auto;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-close {
    top: 10px;
    inset-inline-end: 16px;
    width: 32px;
    height: 32px;
    line-height: 32px;
  }

  .ant-drawer-title {
    flex: 1;
    min-width: 0;
    line-height: 1;
  }

  .ant-drawer-body {
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 120px);
  }

  .scrollbar__wrap {
    padding: 20px 24px !important;
  }

  .ant-drawer-footer {
    padding: 12px 24px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }
}
</style>
