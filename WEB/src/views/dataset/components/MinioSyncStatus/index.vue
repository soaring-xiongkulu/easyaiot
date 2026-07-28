<template>
  <section
    v-if="visible"
    class="minio-sync-status"
    :class="[`status-${status.syncStatus.toLowerCase()}`, { compact, 'connection-error': !!connectionError }]"
    aria-live="polite"
  >
    <div class="status-icon" aria-hidden="true">
      <Icon :icon="statusIcon" :class="{ spinning: active }"/>
    </div>
    <div class="status-content">
      <div class="status-heading">
        <strong>{{ title }}</strong>
        <span class="status-badge">{{ badgeText }}</span>
      </div>
      <div class="status-detail">{{ detail }}</div>

      <div v-if="active || status.syncStatus === 'FAILED'" class="progress-row">
        <div class="progress-track" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
          <span class="progress-value" :style="{ width: `${progress}%` }"/>
        </div>
        <span class="progress-text">{{ progress }}%</span>
      </div>

      <div v-if="metaItems.length" class="status-meta">
        <span v-for="item in metaItems" :key="item.label">
          {{ item.label }} {{ item.value }}
        </span>
      </div>

      <div v-if="connectionError" class="connection-warning">
        <Icon icon="ant-design:disconnect-outlined"/>
        状态连接中断，正在自动重试
      </div>
    </div>
    <div class="status-actions">
      <Button
        v-if="connectionError"
        size="small"
        type="default"
        preIcon="ant-design:reload-outlined"
        @click="emit('refresh')"
      >
        刷新状态
      </Button>
      <Button
        v-if="status.syncStatus === 'FAILED'"
        size="small"
        type="primary"
        preIcon="ant-design:redo-outlined"
        @click="emit('retry')"
      >
        重新同步
      </Button>
      <Button
        v-if="status.syncStatus === 'SUCCEEDED'"
        size="small"
        type="primary"
        preIcon="ant-design:rocket-outlined"
        @click="emit('start-train')"
      >
        创建训练任务
      </Button>
    </div>
  </section>
</template>

<script setup lang="ts">
import {computed} from 'vue';
import {Button} from '@/components/Button';
import {Icon} from '@/components/Icon';
import type {DatasetSyncCheckResult, DatasetSyncStage} from '@/api/device/dataset';

const props = withDefaults(defineProps<{
  status: DatasetSyncCheckResult;
  connectionError?: string | null;
  compact?: boolean;
}>(), {
  connectionError: null,
  compact: false,
});

const emit = defineEmits<{
  (event: 'refresh'): void;
  (event: 'retry'): void;
  (event: 'start-train'): void;
}>();

const stageLabels: Record<DatasetSyncStage, string> = {
  WAITING: '等待后台执行',
  PREPARING: '准备数据目录',
  EXPORTING: '导出图片与标注',
  PACKAGING: '生成配置并打包',
  UPLOADING: '上传到 MinIO',
  FINALIZING: '保存同步结果',
  COMPLETED: '同步完成',
  FAILED: '同步失败',
};

const visible = computed(() => props.status.syncStatus !== 'IDLE' || !!props.connectionError);
const active = computed(() => ['QUEUED', 'RUNNING'].includes(props.status.syncStatus));
const progress = computed(() => Math.max(0, Math.min(100, props.status.syncProgress || 0)));

const statusIcon = computed(() => {
  if (props.connectionError && props.status.syncStatus === 'IDLE') return 'ant-design:disconnect-outlined';
  if (active.value) return 'ant-design:loading-outlined';
  if (props.status.syncStatus === 'SUCCEEDED') return 'ant-design:check-circle-filled';
  return 'ant-design:close-circle-filled';
});

const title = computed(() => {
  if (props.connectionError && props.status.syncStatus === 'IDLE') return '同步状态暂不可用';
  switch (props.status.syncStatus) {
    case 'QUEUED': return '同步任务已提交';
    case 'RUNNING': return '正在同步到 MinIO';
    case 'SUCCEEDED': return 'MinIO 同步完成';
    case 'FAILED': return 'MinIO 同步失败';
    default: return 'MinIO 同步状态';
  }
});

const badgeText = computed(() => {
  if (props.connectionError && props.status.syncStatus === 'IDLE') return '查询失败';
  switch (props.status.syncStatus) {
    case 'QUEUED': return '排队中';
    case 'RUNNING': return stageLabels[props.status.syncStage || 'PREPARING'];
    case 'SUCCEEDED': return '已完成';
    case 'FAILED': return '需要处理';
    default: return '未开始';
  }
});

const detail = computed(() => {
  if (props.connectionError && props.status.syncStatus === 'IDLE') {
    return '未能连接状态服务，请刷新后重试。';
  }
  if (props.status.syncStatus === 'QUEUED') {
    return '任务已进入后台队列，等待执行。';
  }
  if (props.status.syncStatus === 'RUNNING') {
    if (props.status.syncStage === 'EXPORTING' && props.status.totalImages > 0) {
      return `正在处理图片与标注：${props.status.processedImages}/${props.status.totalImages} 张`;
    }
    return stageLabels[props.status.syncStage || 'PREPARING'];
  }
  if (props.status.syncStatus === 'FAILED') {
    return props.status.syncError || '同步过程中发生异常，请重新提交。';
  }
  return '训练数据包已生成，可以直接创建模型训练任务。';
});

const metaItems = computed(() => {
  const items: Array<{label: string; value: string}> = [];
  if (props.status.syncSubmittedAt) items.push({label: '提交', value: formatTime(props.status.syncSubmittedAt)});
  if (props.status.syncStartedAt) items.push({label: '开始', value: formatTime(props.status.syncStartedAt)});
  if (props.status.syncFinishedAt) items.push({label: '结束', value: formatTime(props.status.syncFinishedAt)});
  return items;
});

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}
</script>

<style scoped lang="less">
.minio-sync-status {
  --status-color: #1677ff;
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-left: 4px solid var(--status-color);
  border-radius: 4px;
  background: #fff;
  color: #262626;

  &.compact {
    padding: 8px 14px;
    border-right: 0;
    border-left-width: 3px;
    border-radius: 0;
  }

  &.status-succeeded {
    --status-color: #389e0d;
    background: #f6ffed;
  }

  &.status-failed {
    --status-color: #cf1322;
    background: #fff2f0;
  }

  &.connection-error {
    --status-color: #d48806;
    background: #fffbe6;
  }
}

.status-icon {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: var(--status-color);
  font-size: 22px;
}

.spinning {
  animation: sync-spin 1s linear infinite;
}

.status-content {
  min-width: 0;
}

.status-heading {
  display: flex;
  gap: 8px;
  align-items: center;
  min-width: 0;
  font-size: 14px;
}

.status-badge {
  flex: none;
  padding: 1px 7px;
  border: 1px solid color-mix(in srgb, var(--status-color) 45%, #fff);
  border-radius: 3px;
  color: var(--status-color);
  background: color-mix(in srgb, var(--status-color) 8%, #fff);
  font-size: 12px;
}

.status-detail,
.status-meta,
.connection-warning {
  margin-top: 3px;
  color: #595959;
  font-size: 12px;
  line-height: 18px;
}

.status-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  color: #8c8c8c;
}

.progress-row {
  display: grid;
  grid-template-columns: minmax(120px, 360px) 38px;
  gap: 8px;
  align-items: center;
  margin-top: 7px;
}

.progress-track {
  overflow: hidden;
  height: 6px;
  border-radius: 3px;
  background: #f0f0f0;
}

.progress-value {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--status-color);
  transition: width 300ms ease;
}

.progress-text {
  color: #595959;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
}

.connection-warning {
  display: flex;
  gap: 5px;
  align-items: center;
  color: #ad6800;
}

.status-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

@keyframes sync-spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 720px) {
  .minio-sync-status {
    grid-template-columns: 28px minmax(0, 1fr);
  }

  .status-icon {
    width: 28px;
  }

  .status-actions {
    grid-column: 2;
    justify-content: flex-start;
  }
}
</style>
