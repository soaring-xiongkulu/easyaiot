<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    @close="autoRefresh = false"
    title="大模型研判队列"
    width="1180"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <div class="queue-container">
      <div class="queue-stats">
        <div class="stat-card">
          <div class="stat-card__label">实际抽检率</div>
          <div class="stat-card__value">{{ stats.actual_sample_rate_percent || 0 }}%</div>
          <div class="stat-card__meta">已抽检 {{ stats.sampled || 0 }} / 告警 {{ stats.total_alerts || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">完成研判</div>
          <div class="stat-card__value">{{ stats.completed || 0 }}</div>
          <div class="stat-card__meta">成立 {{ stats.confirmed || 0 }} · 误报 {{ stats.rejected || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">队列中</div>
          <div class="stat-card__value">{{ stats.pending || 0 }}</div>
          <div class="stat-card__meta">失败 {{ stats.failed || 0 }} 条</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">平均耗时</div>
          <div class="stat-card__value">{{ formatDuration(stats.avg_duration_ms) }}</div>
          <div class="stat-card__meta">配置抽检 {{ sampleRates }}</div>
        </div>
      </div>

      <div class="queue-panel">
        <div class="queue-toolbar">
          <div class="queue-toolbar__info">
            <span class="queue-toolbar__title">研判记录</span>
            <span class="queue-toolbar__sub">任务：{{ taskName }} · 共 {{ total }} 条</span>
          </div>
          <div class="queue-toolbar__actions">
            <a-segmented v-model:value="status" :options="statusOptions" @change="handleFilterChange" />
            <div class="auto-refresh">
              <a-switch v-model:checked="autoRefresh" size="small" />
              <span>自动刷新</span>
            </div>
            <Button size="small" :loading="loading" @click="refreshAll">
              <template #icon><ReloadOutlined /></template>
              刷新
            </Button>
          </div>
        </div>

        <a-alert v-if="errorMessage" type="error" show-icon message="队列加载失败" :description="errorMessage" class="queue-error">
          <template #action><Button size="small" @click="refreshAll">重试</Button></template>
        </a-alert>
        <a-spin :spinning="loading">
          <div v-if="items.length" class="queue-list">
            <div v-for="item in items" :key="item.id" class="queue-item">
              <div class="queue-item__top">
                <div class="queue-item__identity">
                  <a-tag :color="statusColor(item.status)">{{ statusLabel(item.status) }}</a-tag>
                  <strong>{{ verdict(item) }}</strong>
                  <span>告警 #{{ item.alert_id }}</span>
                  <span>任务 #{{ item.task_id || taskId }}</span>
                </div>
                <time>{{ formatTime(item.created_at) }}</time>
              </div>
              <div class="queue-item__reason">{{ item.reason || item.error_msg || '任务已进入队列，正在等待大模型返回研判结论…' }}</div>
              <div class="queue-item__meta">
                <span><Icon icon="ant-design:file-image-outlined" />{{ item.judge_mode === 'video' ? '视频研判' : '图片研判' }}</span>
                <span v-if="item.confidence != null"><Icon icon="ant-design:dashboard-outlined" />置信度 {{ Math.round(item.confidence * 100) }}%</span>
                <span v-if="item.duration_ms != null"><Icon icon="ant-design:clock-circle-outlined" />耗时 {{ formatDuration(item.duration_ms) }}</span>
                <span v-if="item.correlation_id" class="correlation">ID {{ item.correlation_id }}</span>
              </div>
            </div>
          </div>
          <a-empty v-else-if="!errorMessage" description="暂无符合条件的研判记录" class="queue-empty" />
        </a-spin>

        <div v-if="total > pageSize" class="queue-pagination">
          <a-pagination v-model:current="page" :page-size="pageSize" :total="total" show-quick-jumper @change="loadResults" />
        </div>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import {
  getLlmJudgeStats,
  listLlmJudgeResults,
  type LlmJudgeResult,
  type LlmJudgeResultStatus,
  type LlmJudgeStats,
} from '@/api/device/algorithm_task';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';

defineOptions({ name: 'LlmJudgeQueueDrawer' });

const taskId = ref<number | null>(null);
const taskName = ref('');
const loading = ref(false);
const errorMessage = ref('');
const items = ref<LlmJudgeResult[]>([]);
const stats = ref<LlmJudgeStats>({} as LlmJudgeStats);
const page = ref(1);
const pageSize = 12;
const total = ref(0);
const status = ref<'all' | LlmJudgeResultStatus>('all');
const autoRefresh = ref(false);
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '排队中', value: 'pending' },
  { label: '已完成', value: 'success' },
  { label: '失败', value: 'error' },
  { label: '死信', value: 'dlt' },
];
const sampleRates = computed(() => stats.value.configured_sample_rates?.length ? `${stats.value.configured_sample_rates.join(' / ')}%` : '-');

const [register] = useDrawerInner(async (data) => {
  taskId.value = data?.taskId ?? null;
  taskName.value = data?.taskName || `算法任务 #${taskId.value || '-'}`;
  page.value = 1;
  status.value = 'all';
  await refreshAll();
});

watch(autoRefresh, (enabled) => {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = enabled ? setInterval(() => void refreshAll(true), 8000) : null;
});
onBeforeUnmount(() => refreshTimer && clearInterval(refreshTimer));

async function refreshAll(silent = false) {
  if (!taskId.value) return;
  if (!silent) loading.value = true;
  errorMessage.value = '';
  try {
    await Promise.all([loadResults(undefined, undefined, true), loadStats()]);
  } catch (error) {
    errorMessage.value = formatApiErrorMessage(error, '加载大模型研判队列失败');
  } finally {
    loading.value = false;
  }
}

async function loadStats() {
  if (!taskId.value) return;
  const res: any = await getLlmJudgeStats(taskId.value);
  stats.value = (res?.data || res || {}) as LlmJudgeStats;
}

async function loadResults(_page?: number, _pageSize?: number, managed = false) {
  if (!taskId.value) return;
  if (!managed) loading.value = true;
  try {
    const res: any = await listLlmJudgeResults(taskId.value, {
      page: page.value,
      pageSize,
      status: status.value === 'all' ? undefined : status.value,
    });
    const data = res?.data || res || {};
    items.value = Array.isArray(data.items) ? data.items : [];
    total.value = Number(data.total || 0);
  } catch (error) {
    errorMessage.value = formatApiErrorMessage(error, '加载研判记录失败');
  } finally {
    if (!managed) loading.value = false;
  }
}

function handleFilterChange() {
  page.value = 1;
  void loadResults();
}
function statusLabel(value: LlmJudgeResultStatus) {
  return ({ pending: '排队中', success: '已完成', error: '执行失败', dlt: '死信' } as const)[value] || value;
}
function statusColor(value: LlmJudgeResultStatus) {
  return ({ pending: 'processing', success: 'success', error: 'error', dlt: 'warning' } as const)[value] || 'default';
}
function verdict(item: LlmJudgeResult) {
  if (item.status !== 'success') return item.status === 'pending' ? '等待大模型研判' : '研判未完成';
  return item.confirm === true ? '确认事件成立' : item.confirm === false ? '判定为误报' : '模型已返回结论';
}
function formatDuration(value?: number) {
  const ms = Number(value || 0);
  return ms >= 1000 ? `${(ms / 1000).toFixed(ms >= 10000 ? 0 : 1)}s` : `${ms}ms`;
}
function formatTime(value?: string) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
</script>

<style lang="less" scoped>
.queue-container {
  padding: 0 4px;
}

.queue-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  padding: 12px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fafafa;

  &__label {
    color: #8c8c8c;
    font-size: 12px;
  }

  &__value {
    margin-top: 4px;
    color: #262626;
    font-size: 20px;
    font-weight: 600;
    line-height: 1.3;
  }

  &__meta {
    margin-top: 4px;
    color: #8c8c8c;
    font-size: 12px;
  }
}

.queue-panel {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #fff;
  padding: 16px;
}

.queue-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;

  &__info {
    display: flex;
    align-items: baseline;
    gap: 8px;
    min-width: 0;
  }

  &__title {
    color: #262626;
    font-size: 15px;
    font-weight: 600;
  }

  &__sub {
    overflow: hidden;
    color: #8c8c8c;
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #595959;
  font-size: 12px;
  white-space: nowrap;
}

.queue-error {
  margin-bottom: 12px;
}

.queue-list {
  display: flex;
  flex-direction: column;
}

.queue-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  &__top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
  }

  &__identity {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 12px;
    color: #8c8c8c;
    font-size: 12px;

    :deep(.ant-tag) {
      margin: 0;
    }

    strong {
      color: #262626;
      font-size: 14px;
    }
  }

  time {
    flex-shrink: 0;
    color: #8c8c8c;
    font-size: 12px;
  }

  &__reason {
    margin-top: 8px;
    color: #595959;
    font-size: 13px;
    line-height: 1.6;
    word-break: break-word;
  }

  &__meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 20px;
    margin-top: 8px;
    color: #8c8c8c;
    font-size: 12px;

    span {
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .correlation {
      overflow: hidden;
      max-width: 300px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.queue-empty {
  padding: 60px 0;
}

.queue-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 900px) {
  .queue-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
