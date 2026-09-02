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
    root-class-name="smart-label-drawer"
  >
    <template #title>
      <div class="detail-drawer-header">
        <div class="detail-drawer-header__icon">
          <Icon :icon="isLlm ? 'ant-design:thunderbolt-outlined' : 'ant-design:deployment-unit-outlined'" :size="18" />
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
                <p class="step-panel-desc">{{ currentStepCopy.description }}</p>
              </div>

              <div v-show="activeConfigStepKey === 'basic'" class="step-panel-body">
                <Form
                  v-if="isLlm"
                  :label-col="SETUP_FORM_LABEL_COL"
                  :wrapper-col="SETUP_FORM_WRAPPER_COL"
                  class="setup-resource-form"
                >
                  <FormItem :label="COPY.form.scene" required>
                    <Input.TextArea
                      v-model:value="form.scene_description"
                      :rows="5"
                      :maxlength="1200"
                      show-count
                      :placeholder="COPY.form.scenePlaceholder"
                    />
                    <p class="form-hint">{{ COPY.form.sceneHint }}</p>
                  </FormItem>
                  <FormItem :label="COPY.form.labels">
                    <Select
                      v-model:value="form.output_labels"
                      mode="tags"
                      :options="labelOptions"
                      :placeholder="COPY.form.labelsPlaceholder"
                      style="width: 100%"
                    />
                    <p class="form-hint">{{ COPY.form.labelsHint }}</p>
                  </FormItem>
                </Form>
                <Form
                  v-else
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
                    <p class="form-hint">{{ batchLimitHint }}</p>
                  </FormItem>
                  <FormItem :label="COPY.form.batchSelection">
                    <Select v-model:value="form.bootstrap_selection" style="width: 100%">
                      <SelectOption value="unlabeled_first">未标注优先</SelectOption>
                      <SelectOption value="unlabeled_only">仅未标注</SelectOption>
                      <SelectOption value="random">随机抽样</SelectOption>
                    </Select>
                  </FormItem>
                  <FormItem :label="COPY.form.confidence">
                    <div class="field-control">
                      <span class="field-value">{{ form.confidence_threshold.toFixed(2) }}</span>
                      <Slider
                        v-model:value="form.confidence_threshold"
                        :min="0.1"
                        :max="0.9"
                        :step="0.05"
                      />
                    </div>
                    <p class="form-hint">{{ COPY.form.confidenceHint }}</p>
                  </FormItem>
                </Form>
              </div>

              <div v-show="activeConfigStepKey === 'relay'" class="step-panel-body">
                <Form
                  :label-col="SETUP_FORM_LABEL_COL"
                  :wrapper-col="SETUP_FORM_WRAPPER_COL"
                  class="setup-resource-form"
                >
                  <FormItem :label="COPY.form.autoTrain" required>
                    <Switch v-model:checked="form.auto_train" />
                    <p class="form-hint">{{ COPY.form.autoTrainHint }}</p>
                  </FormItem>
                  <template v-if="form.auto_train">
                    <FormItem :label="COPY.form.trainEpochs">
                      <InputNumber v-model:value="form.train_epochs" :min="10" :max="300" :step="10" />
                      <span class="count-unit">epochs</span>
                    </FormItem>
                    <FormItem :label="COPY.form.useGpu">
                      <Switch v-model:checked="form.use_gpu" />
                    </FormItem>
                  </template>
                  <FormItem :label="COPY.form.autoRelay">
                    <Switch v-model:checked="form.auto_relay" :disabled="!form.auto_train" />
                    <p class="form-hint">{{ COPY.form.autoRelayHint }}</p>
                  </FormItem>
                  <FormItem v-if="form.auto_relay" :label="COPY.form.relayConfidence">
                    <div class="field-control">
                      <span class="field-value">{{ form.relay_confidence.toFixed(2) }}</span>
                      <Slider
                        v-model:value="form.relay_confidence"
                        :min="0.5"
                        :max="0.95"
                        :step="0.05"
                      />
                    </div>
                    <p class="form-hint">{{ COPY.form.relayConfidenceHint }}</p>
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
                      确认抽检通过
                    </Button>
                  </Space>
                </template>
              </Alert>

              <section v-if="bootstrapStatus" class="monitor-section">
                <div class="monitor-section__head">
                  <span class="monitor-section__title">{{ COPY.monitor.relayTitle }}</span>
                  <Tag v-if="relayStateTag" :color="relayStateTag.color">{{ relayStateTag.text }}</Tag>
                </div>
                <div class="relay-card">
                  <template v-if="trainingInProgress">
                    <p class="relay-text">
                      YOLO 小模型训练进行中（第 {{ trainRound }} 轮），训练完成后{{
                        form.auto_relay ? '将自动接力标注剩余未标注图片' : '可在下方手动启动接力标注'
                      }}。
                    </p>
                  </template>
                  <template v-else-if="boundModel">
                    <div class="relay-model-row">
                      <Icon icon="ant-design:rocket-outlined" class="relay-model-icon" />
                      <div class="relay-model-info">
                        <p class="relay-model-name">
                          {{ boundModel.name }}<span v-if="boundModel.version"> · v{{ boundModel.version }}</span>
                        </p>
                        <p class="relay-model-desc">数据集已绑定该小模型。接力标注只处理剩余未标注图片，已有的冷启动标注不会被覆盖。</p>
                      </div>
                      <Space :size="8" class="relay-model-actions">
                        <Button
                          size="small"
                          :loading="retrainStarting"
                          :disabled="taskRunning || trainingInProgress"
                          @click="handleRetrainWithAccumulated"
                        >
                          {{ COPY.monitor.retrainButton }}
                        </Button>
                        <Button
                          size="small"
                          type="primary"
                          :loading="relayStarting"
                          :disabled="taskRunning"
                          @click="handleStartRelay"
                        >
                          启动接力标注
                        </Button>
                      </Space>
                    </div>
                    <p class="form-hint relay-retrain-hint">{{ COPY.monitor.retrainHint }}</p>
                  </template>
                  <template v-else>
                    <p class="relay-text">{{ COPY.monitor.relayEmpty }}</p>
                  </template>
                </div>
              </section>

              <Alert
                v-if="taskStatus === 'COMPLETED' && !bootstrapQualityAlert"
                type="success"
                show-icon
                class="monitor-alert"
                :message="COPY.monitor.completed"
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
  Empty,
  Form,
  FormItem,
  Input,
  InputNumber,
  Progress,
  Select,
  Slider,
  Space,
  Steps,
  Switch,
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
  startLlmBootstrap,
  startAutoLabel,
  getAutoLabelTask,
  listAutoLabelTasks,
  pauseAutoLabelTask,
  resumeAutoLabelTask,
  cancelAutoLabelTask,
  getSamBootstrapStatus,
  resetSamBootstrapAnnotations,
  completeSamBootstrapReview,
  trainBootstrapSmallModel,
  updateAutoLabelModel,
} from '@/api/device/auto-label';
import type { SamBootstrapStatus } from '@/api/device/auto-label';
import { useMessage } from '@/hooks/web/useMessage';
import { RadioButtonGroup } from '@/components/Form';
import { SETUP_FORM_LABEL_COL, SETUP_FORM_WRAPPER_COL } from '@/views/node/utils/constants';

const SelectOption = Select.Option;

defineOptions({ name: 'SmartLabelDrawer' });

const props = withDefaults(
  defineProps<{
    datasetId: number;
    /** 标注引擎：sam3 = SAM3 开放词汇冷启动；llm = HARNESS 视觉大模型自然语言冷启动 */
    engine?: 'sam3' | 'llm';
    /** 可选：数据集标签库（大模型输出标签候选） */
    datasetLabels?: { name: string; shortcut?: string; color?: string }[];
    /** 可选：用于展示未标注规模提示 */
    totalImages?: number;
    annotatedCount?: number;
  }>(),
  {
    engine: 'sam3',
    datasetLabels: () => [],
    totalImages: undefined,
    annotatedCount: undefined,
  },
);

const emit = defineEmits<{
  success: [payload: { taskId: number }];
  'open-auto-label': [];
  register: [];
}>();

const { createMessage } = useMessage();

const drawerWidth = 'calc(100vw - 200px)';

const isLlm = computed(() => props.engine === 'llm');

interface SmartLabelCopy {
  drawerTitle: string;
  drawerDesc: string;
  tabs: { config: string; monitor: string };
  footer: {
    close: string;
    minimize: string;
    prev: string;
    next: string;
    start: string;
    pause: string;
    resume: string;
    cancel: string;
    cancelConfirm: string;
  };
  steps: {
    basic: { title: string; desc: string };
    batch: { title: string; desc: string };
    relay: { title: string; desc: string };
  };
  form: {
    scene: string;
    scenePlaceholder: string;
    sceneHint: string;
    labels: string;
    labelsPlaceholder: string;
    labelsHint: string;
    classes: string;
    classesHint: string;
    classesPlaceholder: string;
    annotation: string;
    batchLimit: string;
    batchSelection: string;
    confidence: string;
    confidenceHint: string;
    autoTrain: string;
    autoTrainHint: string;
    trainEpochs: string;
    useGpu: string;
    autoRelay: string;
    autoRelayHint: string;
    relayConfidence: string;
    relayConfidenceHint: string;
  };
  monitor: {
    empty: string;
    progress: string;
    metrics: string;
    logs: string;
    paused: string;
    cancelled: string;
    failed: string;
    completed: string;
    relayTitle: string;
    relayEmpty: string;
    retrainButton: string;
    retrainHint: string;
    samQualityLowTitle: string;
    samQualityLowDesc: string;
    samQualityOkTitle: string;
    samQualityOkDesc: string;
  };
}

/** 界面文案（按引擎区分；两套引擎共用全部字段，仅取值不同） */
const COPY = computed<SmartLabelCopy>(() => {
  const llm = isLlm.value;
  return {
    drawerTitle: llm ? '大模型智能标注' : 'SAM3 智能标注',
    drawerDesc: llm
      ? '大模型冷启动标注，用自然语言描述真实场景，对数据集中已有图片批量生成初始标注'
      : 'SAM3 冷启动标注，对数据集中已有图片批量生成初始标注',
    tabs: { config: '参数配置', monitor: '运行监控' },
    footer: {
      close: '关闭',
      minimize: '收起',
      prev: '上一步',
      next: '下一步',
      start: llm ? '启动大模型标注' : '启动标注',
      pause: '暂停',
      resume: '继续',
      cancel: '取消任务',
      cancelConfirm: '确认取消？已标注数据保留。',
    },
    steps: {
      basic: llm
        ? { title: '场景配置', desc: '自然语言定义标注目标' }
        : { title: '基础配置', desc: '类别与格式' },
      batch: { title: '批量参数', desc: '规模与选图' },
      relay: { title: '接力与训练', desc: '小模型量产闭环' },
    },
    form: {
      scene: '场景标注要求',
      scenePlaceholder: llm
        ? '例如：标注化工车间内未正确佩戴安全帽的作业人员；只标正在作业区域内的人，排除办公室、海报和屏幕中的人物。标签名统一为“未戴安全帽人员”。'
        : '',
      sceneHint: '建议写清“标什么、在什么场景、满足什么状态、排除什么”，自然语言越充分，结果越贴合现场。',
      labels: '输出标签（可选）',
      labelsPlaceholder: '输入期望标签名后回车；留空则由大模型从描述中归纳',
      labelsHint: '标签名与小模型训练类别一致，后续接力标注与手动标注共用同一套标签。',
      classes: '检测类别',
      classesHint: '英文类别名，须与后续 YOLO 训练 class 一致。',
      classesPlaceholder: '例如 helmet, vest, person',
      annotation: '标注格式',
      batchLimit: '首批规模',
      batchSelection: '选图规则',
      confidence: '置信度阈值',
      confidenceHint: llm
        ? '低于该置信度的大模型结果将被丢弃，过高易漏、过低易错，建议 0.3 起步。'
        : '过滤低置信度检出，过高会漏检、过低会误检。',
      autoTrain: '自动训练小模型',
      autoTrainHint: '冷启动抽检通过后，自动把已标注数据导出为 YOLO 训练集并开始训练。',
      trainEpochs: '训练轮数',
      useGpu: '使用 GPU 训练',
      autoRelay: '训练完成后自动接力标注',
      autoRelayHint: '小模型训练完成后，自动标注数据集剩余未标注图片；已有冷启动标注受保护不被覆盖。',
      relayConfidence: '接力置信度',
      relayConfidenceHint: '小模型接力标注的置信度下限（不低于 0.5，防止低质结果污染数据集）。',
    },
    monitor: {
      empty: '暂无任务记录，完成参数配置后点击「启动」。',
      progress: '执行进度',
      metrics: '运行指标',
      logs: '运行日志',
      paused: '任务已暂停，点击「继续」断点恢复。',
      cancelled: '任务已取消，已标注部分保留。',
      failed: '任务执行失败',
      completed: llm ? '大模型冷启动标注已完成' : 'SAM3 冷启动标注已完成',
      relayTitle: '小模型接力标注',
      relayEmpty: '完成冷启动抽检并训练 YOLO 小模型后，即可用小模型高速接力标注剩余图片，成本远低于大模型/SAM3。',
      retrainButton: '用沉淀数据再训一轮',
      retrainHint:
        '人工修正与接力标注沉淀后，以当前绑定小模型为基座再训练新版本；新版本发布后自动成为对外生效版本，旧版本保留可回退。',
      samQualityLowTitle: llm
        ? '大模型冷启动识别率偏低，建议调整场景描述后重试'
        : 'SAM3 识别率偏低，建议改用手动或 YOLO 自动标注',
      samQualityLowDesc: llm
        ? '当前数据与场景描述匹配度不足。请恢复冷启动标注到初始状态，调整自然语言描述后重试，或改用手动标注 / YOLO 自动标注。'
        : '当前行业数据可能不适合 SAM3 零样本识别。请恢复冷启动标注到初始状态，改用手动标注或使用已训练的 YOLO 模型进行自动标注。',
      samQualityOkTitle: llm ? '大模型冷启动识别率正常' : 'SAM3 冷启动识别率正常',
      samQualityOkDesc: '请随机抽查 10–20 张并修正明显错误，确认通过后进入小模型训练。',
    },
  };
});

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
const relayStarting = ref(false);
const retrainStarting = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;
let statusTimer: ReturnType<typeof setInterval> | null = null;

const form = reactive({
  // SAM3 引擎
  text_prompts: [] as string[],
  annotation_type: 'rectangle' as 'rectangle' | 'polygon',
  // 大模型引擎
  scene_description: '',
  output_labels: [] as string[],
  // 共用批量参数
  bootstrap_limit: 200,
  bootstrap_selection: 'unlabeled_first' as 'unlabeled_first' | 'unlabeled_only' | 'random',
  confidence_threshold: 0.45,
  // 接力与训练
  auto_train: true,
  train_epochs: 50,
  use_gpu: true,
  auto_relay: true,
  relay_confidence: 0.5,
});

const labelOptions = computed(() =>
  (props.datasetLabels || []).map((label) => ({ label: label.name, value: label.name })),
);

const unlabeledCount = computed(() => {
  if (props.totalImages === undefined || props.annotatedCount === undefined) return null;
  return Math.max(0, props.totalImages - props.annotatedCount);
});

const batchLimitHint = computed(() =>
  unlabeledCount.value === null
    ? '首批规模越大，小模型越早可用；建议先跑 100–300 张抽检。'
    : `当前未标注约 ${unlabeledCount.value} 张。首批规模越大，小模型越早可用；建议先跑 100–300 张抽检。`,
);

const canStart = computed(() => {
  if (starting.value) return false;
  return isLlm.value ? form.scene_description.trim().length >= 8 : form.text_prompts.length > 0;
});

type ConfigStepKey = 'basic' | 'batch' | 'relay';

interface ConfigStepDef {
  key: ConfigStepKey;
  title: string;
  description: string;
}

const configSteps = computed<ConfigStepDef[]>(() => [
  { key: 'basic', title: COPY.value.steps.basic.title, description: COPY.value.steps.basic.desc },
  { key: 'batch', title: COPY.value.steps.batch.title, description: COPY.value.steps.batch.desc },
  { key: 'relay', title: COPY.value.steps.relay.title, description: COPY.value.steps.relay.desc },
]);

const currentStepCopy = computed(
  () => configSteps.value[configStep.value] ?? configSteps.value[0],
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
  if (activeConfigStepKey.value === 'basic') return canStart.value;
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

const boundModel = computed(() => bootstrapStatus.value?.bound_model || null);
const trainingInProgress = computed(() => {
  const ts = bootstrapStatus.value?.train_state;
  return !!ts && (ts.pending_train || ts.pipeline_phase === 'TRAINING');
});
const trainRound = computed(() => bootstrapStatus.value?.train_state?.train_round ?? 1);

const relayStateTag = computed<{ color: string; text: string } | null>(() => {
  if (trainingInProgress.value) return { color: 'processing', text: '小模型训练中' };
  if (boundModel.value) return { color: 'success', text: '小模型就绪' };
  return null;
});

const monitorDescData = computed(() => ({
  total_images: activeTask.value?.total_images ?? form.bootstrap_limit,
  labeled_count: activeTask.value?.success_count ?? 0,
  failed_count: activeTask.value?.failed_count ?? 0,
  hit_count: bootstrapStatus.value?.sam_hit_count ?? '-',
  empty_count: bootstrapStatus.value?.sam_empty_count ?? '-',
  status: statusLabel.value,
}));

const monitorDescSchema = computed<DescItem[]>(() => [
  { field: 'total_images', label: '计划规模' },
  { field: 'labeled_count', label: '标注完成' },
  { field: 'failed_count', label: '失败张数' },
  { field: 'hit_count', label: '有检出' },
  { field: 'empty_count', label: '空结果' },
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
      title: COPY.value.monitor.samQualityLowTitle,
      desc: COPY.value.monitor.samQualityLowDesc,
      showActions: true,
    };
  }
  if (status.sam_quality_passed && !status.review_passed) {
    return {
      type: 'info' as const,
      title: COPY.value.monitor.samQualityOkTitle,
      desc: COPY.value.monitor.samQualityOkDesc,
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
  form.confidence_threshold = isLlm.value ? 0.3 : 0.45;
  stopStatusPolling();
  await resumeActiveTask();
  await loadBootstrapStatus();
  if (shouldPollStatus()) startStatusPolling();
});

function formatLogTime(iso?: string): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false });
  } catch {
    return iso;
  }
}

function adoptTask(id: number, status = 'PENDING'): void {
  taskId.value = id;
  taskStatus.value = status;
  activeTab.value = 'monitor';
  startPolling();
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
    const payload = {
      bootstrap_limit: form.bootstrap_limit,
      bootstrap_selection: form.bootstrap_selection,
      confidence_threshold: form.confidence_threshold,
    };
    const res = isLlm.value
      ? await startLlmBootstrap(props.datasetId, {
          scene_description: form.scene_description.trim(),
          output_labels: form.output_labels,
          ...payload,
        })
      : await startSamBootstrap(props.datasetId, {
          text_prompts: form.text_prompts,
          annotation_type: form.annotation_type,
          return_masks: form.annotation_type === 'polygon',
          ...payload,
        });
    const id = res?.task_id ?? res?.data?.task_id;
    if (!id) {
      createMessage.error('启动失败：未返回任务 ID');
      return;
    }
    createMessage.success(isLlm.value ? '大模型冷启动标注任务已启动' : 'SAM3 冷启动标注任务已启动');
    emit('success', { taskId: id });
    adoptTask(id);
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

/** 抽检/训练推进期间持续刷新冷启动状态 */
function shouldPollStatus(): boolean {
  const s = bootstrapStatus.value;
  if (!s) return false;
  if (s.awaiting_sam_review) return true;
  if (s.bootstrap_done && s.sam_quality_passed && !s.review_passed) return true;
  const ts = s.train_state;
  return !!ts && (ts.pending_train || ts.pipeline_phase === 'TRAINING');
}

function startStatusPolling(): void {
  if (statusTimer) return;
  statusTimer = setInterval(async () => {
    await loadBootstrapStatus();
    if (!shouldPollStatus()) stopStatusPolling();
  }, 8000);
}

function stopStatusPolling(): void {
  if (statusTimer) clearInterval(statusTimer);
  statusTimer = null;
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
    if (form.auto_train) {
      await trainBootstrapSmallModel(props.datasetId, {
        auto_relay: form.auto_relay,
        relay_confidence: form.relay_confidence,
        train_epochs: form.train_epochs,
        use_gpu: form.use_gpu,
      });
      createMessage.success(
        form.auto_relay
          ? '抽检已通过，小模型训练已启动；训练完成后将自动接力标注剩余图片'
          : '抽检已通过，小模型训练已启动',
      );
    } else {
      createMessage.success('抽检已通过。未开启自动训练，可直接用已有小模型接力或稍后手动训练');
    }
    await loadBootstrapStatus();
    startStatusPolling();
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '提交失败');
  } finally {
    reviewLoading.value = false;
  }
}

/** 用数据集已沉淀的标注（人工修正 + 接力结果）对当前绑定小模型再训练一轮新版本 */
async function handleRetrainWithAccumulated(): Promise<void> {
  const model = boundModel.value;
  if (!model?.id) return;
  retrainStarting.value = true;
  try {
    await updateAutoLabelModel(props.datasetId, { base_model_id: model.id });
    createMessage.success(
      model.version
        ? `已提交再训练：基于 v${model.version} 用数据集沉淀标注再训练一轮，完成后自动发布新版本`
        : '已提交再训练：用数据集沉淀标注再训练一轮，完成后自动发布新版本',
    );
    await loadBootstrapStatus();
    startStatusPolling();
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '再训练提交失败');
  } finally {
    retrainStarting.value = false;
  }
}

async function handleStartRelay(): Promise<void> {
  const modelId = boundModel.value?.id;
  if (!modelId) return;
  relayStarting.value = true;
  try {
    const res = await startAutoLabel(props.datasetId, {
      label_mode: 'yolo',
      model_id: modelId,
      confidence_threshold: bootstrapStatus.value?.relay_confidence ?? form.relay_confidence,
      sample_selection: 'unlabeled_only',
    });
    const id = res?.task_id ?? res?.data?.task_id;
    if (!id) {
      createMessage.error('接力标注启动失败：未返回任务 ID');
      return;
    }
    createMessage.success('小模型接力标注已启动');
    emit('success', { taskId: id });
    adoptTask(id);
  } catch (e: any) {
    const msg = e?.response?.data?.msg || e?.message || '接力标注启动失败';
    if (String(msg).includes('已有进行中')) {
      createMessage.warning(msg);
      await resumeActiveTask();
    } else {
      createMessage.error(msg);
    }
  } finally {
    relayStarting.value = false;
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
        if (shouldPollStatus()) startStatusPolling();
      }
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(taskStatus.value)) {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = null;
        if (taskStatus.value === 'COMPLETED') {
          createMessage.success(isLlm.value ? '大模型冷启动标注完成' : '智能标注任务已完成');
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
    createMessage.success('任务已暂停，可点击「继续」断点恢复');
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
    pollTimer = null;
    createMessage.success('任务已取消');
  } catch (e: any) {
    createMessage.error(e?.message || '取消失败');
  }
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
  stopStatusPolling();
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

.step-panel-desc {
  margin: 2px 0 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
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

.form-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}

.count-unit {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
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

.setup-desc {
  .setup-desc();
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

.relay-card {
  padding: 14px 16px;
  border: 1px dashed rgba(0, 0, 0, 0.12);
  border-radius: @setup-panel-radius;
  background: #fafbff;
}

.relay-text {
  margin: 0;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.6;
}

.relay-model-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.relay-model-icon {
  flex-shrink: 0;
  font-size: 22px;
  color: @node-primary;
}

.relay-model-info {
  flex: 1;
  min-width: 0;
}

.relay-model-name {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.relay-model-desc {
  margin: 2px 0 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}

.relay-model-actions {
  flex-shrink: 0;
}

.relay-retrain-hint {
  margin: 8px 0 0;
}

.log-editor {
  height: 280px;
}

.setup-resource-form {
  :deep(.ant-form-item:last-child) {
    margin-bottom: 0;
  }
}
</style>

<style lang="less">
.smart-label-drawer {
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
