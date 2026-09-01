<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="`AI 研判 · 告警 #${alertId || '-'}`"
    :footer="null"
    :maskClosable="true"
    :width="1200"
    :top="48"
    :use-wrapper="false"
    @cancel="handleCancel"
  >
    <div class="lj-modal">
      <!-- 左：告警现场图片（主体视觉） -->
      <div class="lj-scene">
        <img
          v-if="mediaUrl && !sceneError"
          :src="mediaUrl"
          alt="告警图片"
          class="lj-scene__img"
          @error="sceneError = true"
        />
        <div v-else class="lj-scene__empty">
          <Icon icon="ant-design:picture-outlined" :size="48" />
          <span>告警图片不存在</span>
        </div>

        <div class="lj-scene__badge" :class="`lj-scene__badge--${status}`">
          <Icon :icon="badgeIcon" :size="15" />
          <span>{{ statusLabel }}</span>
        </div>

        <div class="lj-scene__meta">
          <span v-if="deviceName" class="lj-scene__meta-item">
            <Icon icon="ant-design:camera-outlined" :size="13" />{{ deviceName }}
          </span>
          <span v-if="eventLabel" class="lj-scene__meta-item">
            <Icon icon="ant-design:alert-outlined" :size="13" />{{ eventLabel }}
          </span>
          <span v-if="timeLabel" class="lj-scene__meta-item">
            <Icon icon="ant-design:clock-circle-outlined" :size="13" />{{ timeLabel }}
          </span>
        </div>
      </div>

      <!-- 右：大模型研判结论面板 -->
      <div class="lj-panel">
        <div class="lj-panel__head">
          <span class="lj-panel__head-title">大模型研判结论</span>
          <Button size="small" :loading="loading" @click="reload">刷新</Button>
        </div>

        <AAlert
          v-if="errorMsg"
          type="error"
          show-icon
          message="研判详情加载失败"
          :description="errorMsg"
        />

        <template v-else>
          <!-- 已出结论：确认成立 / 判定误报 -->
          <div v-if="verdict" class="lj-verdict" :class="`lj-verdict--${verdictType}`">
            <div class="lj-verdict__icon">
              <Icon :icon="verdictIcon" :size="26" />
            </div>
            <div class="lj-verdict__body">
              <div class="lj-verdict__head">
                <span class="lj-verdict__title">{{ verdictTitle }}</span>
                <span v-if="confidence != null" class="lj-verdict__conf">
                  <a-progress
                    :percent="Math.round(confidence * 100)"
                    :show-info="true"
                    :status="verdictType === 'rejected' ? 'exception' : 'success'"
                    size="small"
                    class="lj-verdict__progress"
                  />
                </span>
              </div>
              <div v-if="reason" class="lj-verdict__reason">{{ reason }}</div>
            </div>
          </div>

          <!-- 排队中 -->
          <div v-else-if="status === 'pending'" class="lj-pending">
            <Spin size="large" />
            <div class="lj-pending__title">大模型研判中</div>
            <div class="lj-pending__desc">{{ statusHint }}</div>
          </div>

          <!-- 其他非结论状态（兼容未抽检/限流等历史入口） -->
          <div v-else class="lj-pending">
            <Icon :icon="pendingIcon" :size="36" />
            <div class="lj-pending__title">{{ statusLabel }}</div>
            <div class="lj-pending__desc">{{ statusHint }}</div>
          </div>

          <!-- 研判失败原因 -->
          <AAlert
            v-if="failedReason"
            type="error"
            show-icon
            class="lj-fail"
            message="研判执行失败"
            :description="failedReason"
          />

          <!-- 告警信息 -->
          <div class="lj-section">
            <div class="lj-section__title">告警信息</div>
            <div class="lj-attrs">
              <div class="lj-attr">
                <span class="lj-attr__key">设备</span>
                <span class="lj-attr__value" :title="deviceId">{{ deviceName || deviceId || '-' }}</span>
              </div>
              <div class="lj-attr">
                <span class="lj-attr__key">算法任务</span>
                <span class="lj-attr__value" :title="taskName">{{ taskName || '-' }}</span>
              </div>
              <div class="lj-attr">
                <span class="lj-attr__key">检测对象</span>
                <span class="lj-attr__value">{{ objectLabel || '-' }}</span>
              </div>
              <div class="lj-attr">
                <span class="lj-attr__key">告警时间</span>
                <span class="lj-attr__value">{{ timeLabel || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 结构化属性 -->
          <div v-if="attributes && Object.keys(attributes).length" class="lj-section">
            <div class="lj-section__title">结构化属性</div>
            <div class="lj-attrs">
              <div v-for="(value, key) in attributes" :key="key" class="lj-attr">
                <span class="lj-attr__key">{{ formatAttrKey(key) }}</span>
                <span class="lj-attr__value">{{ formatAttrValue(value) }}</span>
              </div>
            </div>
          </div>

          <!-- 执行信息 -->
          <div class="lj-section">
            <div class="lj-section__title">执行信息</div>
            <div class="lj-meta">
              <div v-if="ruleName" class="lj-meta__row">
                <span class="lj-meta__label">命中规则</span>
                <span class="lj-meta__value" :title="ruleName">{{ ruleName }}</span>
              </div>
              <div v-if="rule && rule.sample_rate_percent" class="lj-meta__row">
                <span class="lj-meta__label">抽检比例</span>
                <span class="lj-meta__value">{{ rule.sample_rate_percent }}%</span>
              </div>
              <div class="lj-meta__row">
                <span class="lj-meta__label">研判耗时</span>
                <span class="lj-meta__value">{{ durationLabel }}</span>
              </div>
              <div class="lj-meta__row">
                <span class="lj-meta__label">研判时间</span>
                <span class="lj-meta__value">{{ judgedAtLabel }}</span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Button, Spin } from 'ant-design-vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { getAlertLlmJudgement } from '@/api/device/algorithm_task';

/** 告警 LLM 后处理状态（与 iot-sink 回写枚举一致） */
export type LlmJudgeAlertStatus =
  | 'not_sampled'
  | 'pending'
  | 'confirmed'
  | 'rejected'
  | 'error'
  | 'rate_limited'
  | 'skipped';

const { createMessage } = useMessage();

const loading = ref(false);
const alertId = ref(0);
const deviceId = ref('');
const deviceName = ref('');
const eventLabel = ref('');
const objectLabel = ref('');
const taskName = ref('');
const timeLabel = ref('');
const mediaUrl = ref('');
const sceneError = ref(false);
const status = ref<LlmJudgeAlertStatus>('pending');
const errorMsg = ref('');
const statusHint = ref('');
const verdictTitle = ref('');
const verdictType = ref<'confirmed' | 'rejected' | 'error'>('confirmed');
const verdictIcon = ref('');
const confidence = ref<number | null>(null);
const reason = ref('');
const attributes = ref<Record<string, any> | null>(null);
const failedReason = ref('');
const ruleName = ref('');
const rule = ref<any>(null);
const judgeModeLabel = ref('-');
const durationLabel = ref('-');
const judgedAtLabel = ref('-');
const modelId = ref<number | null>(null);
const agentId = ref<number | null>(null);

const STATUS_LABELS: Record<LlmJudgeAlertStatus, string> = {
  not_sampled: '未抽检',
  pending: '研判中',
  confirmed: '确认成立',
  rejected: '判定误报',
  error: '研判失败',
  rate_limited: '限流跳过',
  skipped: '已跳过',
};

const STATUS_HINTS: Record<LlmJudgeAlertStatus, string> = {
  not_sampled: '该告警未命中任务的比例抽检，未进入大模型研判队列。可在算法任务的大模型后处理规则中调整抽检比例。',
  pending: '告警已进入大模型研判队列，结论产出后将自动回挂到本告警。',
  confirmed: '大模型确认该告警事件成立，予以保留并作为有效告警处理。',
  rejected: '大模型判定该告警为误报，可用于修正算法阈值或抽查规则。',
  error: '大模型研判执行失败，可检查模型服务状态后重新抽检。',
  rate_limited: '告警命中了比例抽检，但同设备/规则在最小研判间隔内已有研判，本次跳过以控成本。',
  skipped: '该告警因规则配置被跳过，未进入大模型研判队列。',
};

const statusLabel = computed(() => STATUS_LABELS[status.value] || status.value);
const verdict = computed(() => ['confirmed', 'rejected'].includes(status.value));
const pendingIcon = computed(() =>
  status.value === 'not_sampled'
    ? 'ant-design:inbox-outlined'
    : status.value === 'rate_limited'
      ? 'ant-design:clock-circle-outlined'
      : 'ant-design:exclamation-circle-outlined',
);
const badgeIcon = computed(() =>
  status.value === 'confirmed'
    ? 'ant-design:check-circle-filled'
    : status.value === 'rejected'
      ? 'ant-design:close-circle-filled'
      : status.value === 'error'
        ? 'ant-design:close-circle-filled'
        : status.value === 'pending'
          ? 'ant-design:loading-outlined'
          : 'ant-design:info-circle-outlined',
);

const [register, { closeModal }] = useModalInner(async (data) => {
  reset();
  const record = data?.record || data || {};
  alertId.value = Number(record.id);
  deviceId.value = record.device_id || '';
  deviceName.value = record.device_name || '';
  eventLabel.value = record.event || '';
  objectLabel.value = record.object || '';
  timeLabel.value = record.time || '';
  const url = resolveAlertImageDisplayUrl(record.image_url || record.imageUrl);
  if (url) mediaUrl.value = url;

  // 列表已带研判状态则先渲染，再拉取完整详情（含规则快照与结论）
  applyAlertStatus(record.llm_judge_status, record.llm_judge_detail);
  if (alertId.value) {
    await reload();
  }
});

function reset() {
  alertId.value = 0;
  deviceId.value = '';
  deviceName.value = '';
  eventLabel.value = '';
  objectLabel.value = '';
  taskName.value = '';
  timeLabel.value = '';
  mediaUrl.value = '';
  sceneError.value = false;
  status.value = 'pending';
  errorMsg.value = '';
  statusHint.value = STATUS_HINTS.pending;
  verdictTitle.value = '';
  verdictType.value = 'confirmed';
  verdictIcon.value = '';
  confidence.value = null;
  reason.value = '';
  attributes.value = null;
  failedReason.value = '';
  ruleName.value = '';
  rule.value = null;
  judgeModeLabel.value = '-';
  durationLabel.value = '-';
  judgedAtLabel.value = '-';
  modelId.value = null;
  agentId.value = null;
}

function applyAlertStatus(rawStatus?: string | null, rawDetail?: any) {
  if (!rawStatus) return;
  const st = String(rawStatus) as LlmJudgeAlertStatus;
  if (!(st in STATUS_LABELS)) return;
  status.value = st;
  statusHint.value = STATUS_HINTS[st];
  if (st === 'confirmed' || st === 'rejected') {
    verdictType.value = st;
    verdictIcon.value = st === 'confirmed' ? 'ant-design:check-circle-filled' : 'ant-design:close-circle-filled';
    verdictTitle.value = st === 'confirmed' ? '确认成立' : '判定误报';
  }
  if (rawDetail && typeof rawDetail === 'object') {
    if (rawDetail.confirm != null) {
      verdictType.value = rawDetail.confirm ? 'confirmed' : 'rejected';
      verdictIcon.value = rawDetail.confirm ? 'ant-design:check-circle-filled' : 'ant-design:close-circle-filled';
      verdictTitle.value = rawDetail.confirm ? '确认成立' : '判定误报';
      status.value = rawDetail.confirm ? 'confirmed' : 'rejected';
      statusHint.value = STATUS_HINTS[status.value];
    }
    if (typeof rawDetail.confidence === 'number') confidence.value = rawDetail.confidence;
    if (rawDetail.reason) reason.value = String(rawDetail.reason);
    if (rawDetail.attributes && typeof rawDetail.attributes === 'object') attributes.value = rawDetail.attributes;
    if (rawDetail.judge_mode) judgeModeLabel.value = rawDetail.judge_mode === 'video' ? '视频研判' : '图片研判';
    if (typeof rawDetail.duration_ms === 'number') durationLabel.value = formatDuration(rawDetail.duration_ms);
    if (rawDetail.judged_at) judgedAtLabel.value = formatJudgedAt(rawDetail.judged_at);
    if (rawDetail.model_id) modelId.value = Number(rawDetail.model_id);
    if (rawDetail.agent_id) agentId.value = Number(rawDetail.agent_id);
    if (rawDetail.rule_id && !ruleName.value) ruleName.value = `#${rawDetail.rule_id}`;
  }
}

async function reload() {
  if (!alertId.value) return;
  loading.value = true;
  errorMsg.value = '';
  try {
    const res: any = await getAlertLlmJudgement(alertId.value);
    const data = res?.data || res || {};
    if (!data || typeof data !== 'object') return;
    if (data.image_url) {
      const url = resolveAlertImageDisplayUrl(data.image_url);
      if (url) mediaUrl.value = url;
    }
    if (data.device_name) deviceName.value = data.device_name;
    if (data.device_id) deviceId.value = data.device_id;
    if (data.event) eventLabel.value = data.event;
    if (data.object) objectLabel.value = data.object;
    if (data.task_name) taskName.value = data.task_name;
    if (data.time) timeLabel.value = String(data.time).replace('T', ' ').slice(0, 19);
    if (data.status) {
      const st = String(data.status) as LlmJudgeAlertStatus;
      if (st in STATUS_LABELS) {
        status.value = st;
        statusHint.value = STATUS_HINTS[st];
      }
    }
    applyAlertStatus(data.status, data.detail);
    const resultRow: any = data.result || {};
    if (resultRow && typeof resultRow === 'object') {
      if (resultRow.status === 'error') {
        failedReason.value = resultRow.error_msg || '模型调用失败';
        status.value = 'error';
        statusHint.value = STATUS_HINTS.error;
      }
      if (resultRow.duration_ms != null) durationLabel.value = formatDuration(resultRow.duration_ms);
      if (resultRow.created_at) judgedAtLabel.value = formatJudgedAt(resultRow.created_at);
      if (resultRow.judge_mode) judgeModeLabel.value = resultRow.judge_mode === 'video' ? '视频研判' : '图片研判';
      if (resultRow.confirm === true || resultRow.confirm === false) {
        verdictType.value = resultRow.confirm ? 'confirmed' : 'rejected';
        verdictIcon.value = resultRow.confirm ? 'ant-design:check-circle-filled' : 'ant-design:close-circle-filled';
        verdictTitle.value = resultRow.confirm ? '确认成立' : '判定误报';
        // 告警状态列可能滞后于研判结果行，以结果行为准
        status.value = resultRow.confirm ? 'confirmed' : 'rejected';
        statusHint.value = STATUS_HINTS[status.value];
      }
      if (resultRow.confidence != null) confidence.value = Number(resultRow.confidence);
      if (resultRow.reason) reason.value = String(resultRow.reason);
      if (resultRow.structured && typeof resultRow.structured === 'object') {
        attributes.value = resultRow.structured;
      }
    }
    const ruleRow: any = data.rule || null;
    if (ruleRow && typeof ruleRow === 'object') {
      rule.value = ruleRow;
      if (ruleRow.rule_name) ruleName.value = ruleRow.rule_name;
    }
  } catch (error: any) {
    errorMsg.value = formatApiErrorMessage(error, '加载研判详情失败');
    createMessage.error(errorMsg.value);
  } finally {
    loading.value = false;
  }
}

function formatDuration(ms: number): string {
  if (ms == null) return '-';
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function formatJudgedAt(value: unknown): string {
  if (!value) return '-';
  const num = Number(value);
  const date = Number.isNaN(num) ? new Date(String(value)) : new Date(num > 1e12 ? num : num * 1000);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString();
}

function formatAttrKey(key: string): string {
  return String(key)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatAttrValue(value: any): string {
  if (value == null) return '-';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function handleCancel() {
  reset();
  closeModal();
}
</script>

<style lang="less">
.lj-modal {
  display: flex;
  gap: 20px;
  min-height: 480px;
  align-items: stretch;
}

/* ===== 左：现场图片 ===== */
.lj-scene {
  position: relative;
  flex: 0 0 52%;
  border-radius: 10px;
  overflow: hidden;
  background: #0b1220;
  display: flex;
  align-items: center;
  justify-content: center;

  .lj-scene__img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }

  .lj-scene__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    color: rgba(255, 255, 255, 0.55);
    font-size: 13px;
  }

  .lj-scene__badge {
    position: absolute;
    top: 12px;
    left: 12px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    color: #fff;
    backdrop-filter: blur(6px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);

    &--confirmed {
      background: rgba(22, 163, 74, 0.88);
    }

    &--rejected {
      background: rgba(217, 119, 6, 0.9);
    }

    &--error {
      background: rgba(220, 38, 38, 0.9);
    }

    &--pending {
      background: rgba(99, 102, 241, 0.9);
    }

    &--not_sampled,
    &--rate_limited,
    &--skipped {
      background: rgba(100, 116, 139, 0.85);
    }
  }

  .lj-scene__meta {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    padding: 10px 14px;
    font-size: 12px;
    color: #e5e7eb;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.82));
  }

  .lj-scene__meta-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* ===== 右：结论面板 ===== */
.lj-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;

  .lj-panel__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0;
  }

  .lj-panel__head-title {
    font-size: 15px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
  }
}

/* 结论卡片：朴素白卡 + 左侧色条 */
.lj-verdict {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-left: 4px solid #16a34a;
  flex-shrink: 0;

  &--rejected {
    border-left-color: #d97706;
  }

  &--error {
    border-left-color: #dc2626;
  }

  .lj-verdict__icon {
    flex-shrink: 0;
    color: #16a34a;
    margin-top: 2px;
  }

  &--rejected .lj-verdict__icon {
    color: #d97706;
  }

  &--error .lj-verdict__icon {
    color: #dc2626;
  }

  .lj-verdict__body {
    flex: 1;
    min-width: 0;
  }

  .lj-verdict__head {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .lj-verdict__title {
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
    line-height: 22px;
  }

  .lj-verdict__conf {
    min-width: 160px;
    max-width: 220px;
  }

  .lj-verdict__progress {
    :deep(.ant-progress-text) {
      font-size: 12px;
    }
  }

  .lj-verdict__reason {
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.7;
    color: rgba(0, 0, 0, 0.78);
    white-space: pre-wrap;
    word-break: break-word;
  }
}

/* 排队/说明 */
.lj-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 34px 20px;
  color: rgba(0, 0, 0, 0.45);
  border: 1px dashed #d9d9d9;
  border-radius: 10px;
  background: #fafafa;

  .lj-pending__title {
    font-size: 15px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.65);
  }

  .lj-pending__desc {
    font-size: 12px;
    text-align: center;
    line-height: 1.7;
    max-width: 320px;
  }
}

.lj-fail {
  margin-top: 2px;
}

/* 区块 */
.lj-section {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 8px 12px;
  background: #fafcff;
  flex-shrink: 0;

  .lj-section__title {
    font-size: 12px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.45);
    margin-bottom: 6px;
    letter-spacing: 0.5px;
  }
}

/* 告警信息/结构化属性：网格 */
.lj-attrs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.lj-attr {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 7px 10px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  min-width: 0;

  .lj-attr__key {
    font-size: 11px;
    color: rgba(0, 0, 0, 0.45);
  }

  .lj-attr__value {
    font-size: 12.5px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.85);
    word-break: break-word;
  }
}

/* 执行信息：两列 key-value */
.lj-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 18px;

  .lj-meta__row {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 12.5px;
    line-height: 24px;
    border-bottom: 1px dashed #f5f5f5;

    &:last-child {
      border-bottom: none;
    }
  }

  .lj-meta__label {
    color: rgba(0, 0, 0, 0.45);
    flex-shrink: 0;
  }

  .lj-meta__value {
    color: rgba(0, 0, 0, 0.85);
    font-weight: 500;
    text-align: right;
    min-width: 0;
    word-break: break-word;
  }
}
</style>
