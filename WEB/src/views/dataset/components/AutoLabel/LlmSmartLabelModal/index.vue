<template>
  <BasicModal
    @register="register"
    width="860px"
    :can-fullscreen="false"
    :show-ok-btn="false"
    :show-cancel-btn="false"
    :mask-closable="!running"
    :get-container="getContainer"
    @cancel="handleClose"
  >
    <template #title>
      <span class="modal-title"><Icon icon="ant-design:thunderbolt-outlined" /> 大模型智能标注</span>
    </template>

    <Alert type="info" show-icon class="value-alert">
      <template #message>用自然语言定义真实场景，比固定标签更懂你的标注目标</template>
      <template #description>
        本能力基于 HARNESS 统一大模型底座，以自然语言完成零样本冷启动。首批标注进入后台任务，完成后可抽检修正并用于训练贴合现场的小模型。
      </template>
    </Alert>

    <Form layout="vertical" :model="form" class="smart-form">
      <FormItem label="场景标注要求" required>
        <Input.TextArea
          v-model:value="form.sceneDescription"
          :rows="5"
          :maxlength="1200"
          show-count
          placeholder="例如：标注化工车间内未正确佩戴安全帽的作业人员；只标正在作业区域内的人，排除办公室、海报和屏幕中的人物。标签名统一为“未戴安全帽人员”。"
          :disabled="running"
        />
        <div class="form-tip">建议写清“标什么、在什么场景、满足什么状态、排除什么”，自然语言越充分，结果越贴合现场。</div>
      </FormItem>

      <FormItem label="输出标签（可选）">
        <Select
          v-model:value="form.labels"
          mode="tags"
          :options="labelOptions"
          placeholder="输入期望标签名后回车；留空则由大模型从描述中归纳"
          :disabled="running"
        />
      </FormItem>

      <div class="form-grid">
        <FormItem label="冷启动选图">
          <Radio.Group v-model:value="form.scope" :disabled="running">
            <Radio.Button value="unlabeled">仅未标注图片</Radio.Button>
            <Radio.Button value="all">全部图片</Radio.Button>
          </Radio.Group>
        </FormItem>
        <FormItem label="本次最多处理">
          <InputNumber v-model:value="form.limit" :min="1" :max="availableImages" :disabled="running" />
          <span class="count-unit">张（当前可用 {{ availableImages }} 张）</span>
        </FormItem>
      </div>
    </Form>

    <section v-if="running || progress.processed" class="progress-card">
      <div class="progress-head">
        <span>{{ running ? '自然语言冷启动运行中' : '冷启动任务结果' }}</span>
        <span>{{ progress.processed }}/{{ progress.total }}</span>
      </div>
      <Progress :percent="progressPercent" :status="progress.failed ? 'active' : progressPercent === 100 ? 'success' : 'active'" />
      <div class="progress-stats">
        任务 #{{ taskId || '-' }} · {{ taskStatusLabel }} · 成功 {{ progress.success }} 张 · 无目标 {{ progress.empty }} 张 · 失败 {{ progress.failed }} 张
      </div>
      <Alert v-if="lastError" type="warning" show-icon :message="lastError" class="error-alert" />
      <Alert
        v-if="quality && taskStatus === 'COMPLETED'"
        :type="quality.sam_quality_passed ? 'info' : 'warning'"
        show-icon
        class="error-alert"
        :message="quality.sam_quality_passed ? '大模型冷启动质量达标，请抽检后确认' : '冷启动检出率偏低，请调整自然语言描述后重试'"
      >
        <template #description>
          检出率 {{ quality.recognition_rate_pct ?? 0 }}%，有目标 {{ quality.sam_hit_count ?? 0 }} 张，空结果 {{ quality.sam_empty_count ?? 0 }} 张。
          <Button
            v-if="quality.sam_quality_passed && !quality.review_passed"
            type="link"
            size="small"
            :loading="reviewing"
            @click="confirmReview"
          >抽检通过，进入小模型训练准备</Button>
          <span v-else-if="quality.review_passed">已抽检通过，可进入训练。</span>
        </template>
      </Alert>
    </section>

    <template #footer>
      <div class="modal-footer">
        <Button v-if="running" @click="requestCancel">收起监控</Button>
        <Button
          type="primary"
          :loading="running"
          :disabled="!canStart"
          @click="startLabeling"
        >
          <template #icon><Icon icon="ant-design:play-circle-outlined" /></template>
          开始大模型智能标注
        </Button>
        <Button :disabled="running" @click="handleClose">关闭</Button>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, onUnmounted, reactive, ref } from 'vue';
import { Alert, Form, FormItem, Input, InputNumber, Progress, Radio, Select } from 'ant-design-vue';
import { BasicModal, useModal } from '@/components/Modal';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  completeSamBootstrapReview,
  getAutoLabelTask,
  getSamBootstrapStatus,
  startLlmBootstrap,
  trainBootstrapSmallModel,
} from '@/api/device/auto-label';

defineOptions({ name: 'LlmSmartLabelModal' });

interface DatasetImage {
  id: number;
  name: string;
  path: string;
  annotations: unknown[] | string;
  completed: 0 | 1;
  modificationCount: number;
}

interface DatasetLabel { name: string; shortcut: string; color: string }
const props = defineProps<{
  datasetId: number;
  images: DatasetImage[];
  datasetLabels: DatasetLabel[];
  getContainer?: () => HTMLElement;
}>();
const emit = defineEmits<{ success: [] }>();
const { createMessage } = useMessage();
const [register, { openModal, closeModal }] = useModal();

const running = ref(false);
const cancelRequested = ref(false);
const lastError = ref('');
const taskId = ref<number | null>(null);
const taskStatus = ref('');
const quality = ref<Record<string, any> | null>(null);
const reviewing = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;
const progress = reactive({ total: 0, processed: 0, success: 0, empty: 0, failed: 0 });
const form = reactive({ sceneDescription: '', labels: [] as string[], scope: 'unlabeled', limit: 100 });

const labelOptions = computed(() => props.datasetLabels.map((label) => ({ label: label.name, value: label.name })));
const candidates = computed(() => props.images.filter((image) => form.scope === 'all' || !hasAnnotations(image)));
const availableImages = computed(() => Math.max(1, candidates.value.length));
const canStart = computed(() => !running.value && form.sceneDescription.trim().length >= 8 && candidates.value.length > 0);
const progressPercent = computed(() => progress.total ? Math.round(progress.processed / progress.total * 100) : 0);
const taskStatusLabel = computed(() => ({
  PENDING: '排队中', PROCESSING: '运行中', COMPLETED: '已完成', FAILED: '失败',
  PAUSED: '已暂停', CANCELLED: '已取消',
}[taskStatus.value] || taskStatus.value || '未启动'));

function hasAnnotations(image: DatasetImage): boolean {
  try {
    const value = typeof image.annotations === 'string' ? JSON.parse(image.annotations) : image.annotations;
    return Array.isArray(value) && value.length > 0;
  } catch { return false; }
}

async function startLabeling(): Promise<void> {
  if (!canStart.value) return;
  running.value = true;
  cancelRequested.value = false;
  lastError.value = '';
  Object.assign(progress, { total: 0, processed: 0, success: 0, empty: 0, failed: 0 });
  try {
    const response = await startLlmBootstrap(props.datasetId, {
      scene_description: form.sceneDescription.trim(),
      output_labels: form.labels,
      bootstrap_limit: Math.min(form.limit, candidates.value.length),
      bootstrap_selection: form.scope === 'all' ? 'all' : 'unlabeled_only',
      confidence_threshold: 0.3,
    });
    const data = response?.data ?? response;
    taskId.value = Number(data?.task_id);
    if (!taskId.value) throw new Error('服务端未返回任务 ID');
    taskStatus.value = 'PENDING';
    await pollTask();
    pollTimer = setInterval(pollTask, 2500);
  } catch (error) {
    running.value = false;
    lastError.value = error instanceof Error ? error.message : String(error);
    createMessage.error(lastError.value);
  }
}

async function pollTask(): Promise<void> {
  if (!taskId.value) return;
  try {
    const response = await getAutoLabelTask(props.datasetId, taskId.value);
    const task = (response?.data ?? response) as Record<string, any>;
    taskStatus.value = String(task.status || '');
    progress.total = Number(task.total_images || 0);
    progress.processed = Number(task.processed_images || 0);
    progress.failed = Number(task.failed_count || 0);
    const cfg = task.pipeline_config || {};
    progress.success = Number(cfg.llm_hit_count ?? task.success_count ?? 0);
    progress.empty = Number(cfg.llm_empty_count || 0);
    if (taskStatus.value === 'COMPLETED' || taskStatus.value === 'FAILED' || taskStatus.value === 'CANCELLED') {
      clearPolling();
      running.value = false;
      if (taskStatus.value === 'COMPLETED') {
        await loadQuality();
        createMessage.success(`自然语言冷启动完成：处理 ${progress.processed} 张，成功 ${progress.success} 张`);
        emit('success');
      } else {
        lastError.value = String(task.error_message || '冷启动任务失败');
      }
    }
  } catch (error) {
    lastError.value = error instanceof Error ? error.message : String(error);
  }
}

async function loadQuality(): Promise<void> {
  const response = await getSamBootstrapStatus(props.datasetId);
  quality.value = (response?.data ?? response) as Record<string, any>;
}

async function confirmReview(): Promise<void> {
  reviewing.value = true;
  try {
    await completeSamBootstrapReview(props.datasetId, {
      review_passed: true,
      reviewer_note: '大模型自然语言冷启动抽检通过',
    });
    await trainBootstrapSmallModel(props.datasetId);
    await loadQuality();
    createMessage.success('抽检已通过，YOLO 小模型训练已启动');
  } catch (error) {
    createMessage.error(error instanceof Error ? error.message : '提交抽检结果失败');
  } finally {
    reviewing.value = false;
  }
}

function clearPolling(): void {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
}

function handleClose(): void {
  if (!running.value) closeModal();
}

function requestCancel(): void {
  // 当前任务由后台执行；停止按钮仅停止本窗口轮询，任务可继续在统一任务监控中查看。
  cancelRequested.value = true;
  clearPolling();
  running.value = false;
  createMessage.info('已收起本窗口监控，后台冷启动任务继续执行');
}

onUnmounted(clearPolling);

defineExpose({ openModal });
</script>

<style scoped lang="less">
.modal-title { display: inline-flex; align-items: center; gap: 8px; }
.value-alert { margin-bottom: 20px; }
.smart-form { margin-top: 8px; }
.form-tip { margin-top: 7px; color: #7a8499; font-size: 13px; }
.form-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; }
.count-unit { margin-left: 8px; color: #7a8499; }
.progress-card { padding: 16px; border: 1px solid #e8ebf2; border-radius: 8px; background: #fafbff; }
.progress-head, .modal-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.progress-stats { color: #697386; font-size: 13px; }
.error-alert { margin-top: 12px; }
.modal-footer { justify-content: flex-end; }
</style>
