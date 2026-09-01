<template>
  <BasicModal
    @register="register"
    width="720px"
    title="SAM 冷启动标注向导"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="true"
    cancelText="关闭"
    :get-container="getContainer"
  >
    <Steps :current="currentStep" size="small" class="wizard-steps">
      <Step title="类别词" />
      <Step title="批量标注" />
      <Step title="抽检" />
      <Step title="训练引导" />
    </Steps>

    <div v-show="currentStep === 0" class="step-body">
      <Alert type="info" show-icon message="输入英文类别词，与后续 YOLO 训练 class 保持一致" />
      <div class="field">
        <div class="label">文本类别</div>
        <Select v-model:value="form.text_prompts" mode="tags" placeholder="helmet, vest, person" style="width: 100%" />
      </div>
      <div class="field">
        <div class="label">首批数量（{{ form.bootstrap_limit }} 张）</div>
        <Slider v-model:value="form.bootstrap_limit" :min="100" :max="500" :step="50" />
      </div>
      <div class="field">
        <div class="label">标注形态</div>
        <RadioGroup v-model:value="form.annotation_type">
          <Radio value="rectangle">检测框（推荐冷启动）</Radio>
          <Radio value="polygon">分割多边形</Radio>
        </RadioGroup>
      </div>
      <Button type="primary" :disabled="!form.text_prompts.length" @click="startBootstrap">开始 SAM 标注</Button>
    </div>

    <div v-show="currentStep === 1" class="step-body">
      <Progress :percent="progressPercent" :status="taskStatus === 'FAILED' ? 'exception' : undefined" />
      <p class="progress-text">
        已处理 {{ task?.processed_images ?? 0 }} / {{ task?.total_images ?? form.bootstrap_limit }}
        （成功 {{ task?.success_count ?? 0 }}）
      </p>
      <p v-if="taskStatus === 'COMPLETED'" class="success-tip">标注完成，请进入画布抽检修正</p>
    </div>

    <div v-show="currentStep === 2" class="step-body">
      <Alert
        v-if="bootstrapStatus?.review_recommended"
        type="warning"
        show-icon
        class="review-alert"
        message="SAM 识别率偏低，不适合继续智能标注"
      >
        <template #description>
          <p>
            识别率 {{ bootstrapStatus?.recognition_rate_pct ?? 0 }}%
            （有检出 {{ bootstrapStatus?.sam_hit_count ?? 0 }} 张 / 空结果 {{ bootstrapStatus?.sam_empty_count ?? 0 }} 张）。
            行业数据建议恢复冷启动标注后，改用手动标注或 YOLO 自动标注。
          </p>
          <Space class="mt-3">
            <Button :loading="resetLoading" @click="handleReset">恢复冷启动标注</Button>
            <Button type="primary" @click="emit('open-auto-label')">改用自动标注（YOLO）</Button>
          </Space>
        </template>
      </Alert>
      <Alert
        v-else
        type="warning"
        show-icon
        message="请随机抽查 10–20 张，修正明显错误后确认通过"
      />
      <Input.TextArea v-model:value="reviewNote" placeholder="抽检备注（可选）" :rows="3" class="mt-3" />
      <Button
        v-if="!bootstrapStatus?.review_recommended"
        type="primary"
        class="mt-3"
        :loading="reviewLoading"
        @click="submitReview"
      >
        抽检通过
      </Button>
    </div>

    <div v-show="currentStep === 3" class="step-body">
      <Alert type="success" show-icon message="冷启动完成！下一步：划分用途 → 训练 YOLO → 用 model_id 批量标注剩余图片" />
      <Button type="link" @click="goTrain">前往训练中心</Button>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Alert, Button, Input, Progress, Radio, RadioGroup, Select, Slider, Space, Steps } from 'ant-design-vue';
import { BasicModal, useModal } from '@/components/Modal';
import {
  startSamBootstrap,
  getAutoLabelTask,
  getSamBootstrapStatus,
  resetSamBootstrapAnnotations,
  completeSamBootstrapReview,
} from '@/api/device/auto-label';
import type { SamBootstrapStatus } from '@/api/device/auto-label';
import { useMessage } from '@/hooks/web/useMessage';

const Step = Steps.Step;
defineOptions({ name: 'SamBootstrapWizard' });

const props = defineProps<{
  datasetId: number;
  getContainer?: () => HTMLElement;
}>();

const emit = defineEmits(['success', 'register', 'open-auto-label']);
const { createMessage } = useMessage();
const router = useRouter();

const currentStep = ref(0);
const form = ref({
  text_prompts: [] as string[],
  bootstrap_limit: 200,
  annotation_type: 'rectangle' as 'rectangle' | 'polygon',
  confidence_threshold: 0.45,
});
const taskId = ref<number | null>(null);
const task = ref<any>(null);
const taskStatus = ref('');
const bootstrapStatus = ref<SamBootstrapStatus | null>(null);
const reviewNote = ref('');
const reviewLoading = ref(false);
const resetLoading = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

const progressPercent = computed(() => {
  const total = task.value?.total_images || form.value.bootstrap_limit;
  const done = task.value?.processed_images || 0;
  if (!total) return 0;
  return Math.min(100, Math.round((done / total) * 100));
});

const [register, { openModal: openModalInner }] = useModal();

function openModal() {
  currentStep.value = 0;
  bootstrapStatus.value = null;
  openModalInner();
}

defineExpose({ openModal });

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

async function loadBootstrapStatus() {
  try {
    const res = await getSamBootstrapStatus(props.datasetId);
    bootstrapStatus.value = (res?.data ?? res) as SamBootstrapStatus;
  } catch {
    bootstrapStatus.value = null;
  }
}

async function startBootstrap() {
  try {
    const res = await startSamBootstrap(props.datasetId, {
      text_prompts: form.value.text_prompts,
      bootstrap_limit: form.value.bootstrap_limit,
      annotation_type: form.value.annotation_type,
      bootstrap_selection: 'unlabeled_first',
      confidence_threshold: form.value.confidence_threshold,
      return_masks: form.value.annotation_type === 'polygon',
    });
    taskId.value = res?.task_id ?? res?.data?.task_id;
    currentStep.value = 1;
    startPolling();
  } catch (e: any) {
    createMessage.error(e?.message || '启动失败');
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (!taskId.value) return;
    try {
      const data = await getAutoLabelTask(props.datasetId, taskId.value);
      task.value = data;
      taskStatus.value = data?.status || '';
      if (taskStatus.value === 'COMPLETED' || taskStatus.value === 'FAILED') {
        if (pollTimer) clearInterval(pollTimer);
        if (taskStatus.value === 'COMPLETED') {
          await loadBootstrapStatus();
          currentStep.value = 2;
          emit('success');
        }
      }
    } catch {
      /* ignore poll errors */
    }
  }, 2000);
}

async function handleReset() {
  resetLoading.value = true;
  try {
    const res = await resetSamBootstrapAnnotations(props.datasetId);
    const count = res?.data?.reset_count ?? res?.reset_count ?? 0;
    createMessage.success(`已恢复 ${count} 张图片到未标注状态`);
    bootstrapStatus.value = null;
    currentStep.value = 0;
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '恢复失败');
  } finally {
    resetLoading.value = false;
  }
}

async function submitReview() {
  reviewLoading.value = true;
  try {
    await completeSamBootstrapReview(props.datasetId, {
      review_passed: true,
      reviewer_note: reviewNote.value,
    });
    currentStep.value = 3;
    createMessage.success('抽检已通过');
  } catch (e: any) {
    createMessage.error(e?.response?.data?.msg || e?.message || '提交失败');
  } finally {
    reviewLoading.value = false;
  }
}

function goTrain() {
  router.push({ path: '/train/index', query: { tab: '6' } });
}
</script>

<style lang="less" scoped>
.wizard-steps {
  margin-bottom: 20px;
}
.step-body {
  min-height: 200px;
}
.field {
  margin: 16px 0;
}
.label {
  margin-bottom: 8px;
  font-weight: 500;
}
.progress-text {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.65);
}
.success-tip {
  color: #52c41a;
}
.mt-3 {
  margin-top: 12px;
}
.review-alert {
  margin-bottom: 12px;
}
</style>
