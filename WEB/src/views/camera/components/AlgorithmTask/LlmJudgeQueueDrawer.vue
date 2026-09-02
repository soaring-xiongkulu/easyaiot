<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    @close="autoRefresh = false"
    width="1180"
    placement="right"
    :showFooter="false"
    destroy-on-close
    :z-index="1150"
    root-class-name="llm-judge-queue-drawer"
  >
    <template #title>
      <div class="queue-title">
        <div class="queue-title__mark"><Icon icon="ant-design:robot-outlined" :size="24" /></div>
        <div class="queue-title__copy">
          <div class="queue-title__name">大模型研判队列</div>
          <div class="queue-title__sub">{{ taskName }} · 配置与运行结果独立管理</div>
        </div>
        <div class="queue-title__actions">
          <a-switch v-model:checked="autoRefresh" size="small" />
          <span>自动刷新</span>
          <Button :loading="loading" @click="refreshAll">
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
        </div>
      </div>
    </template>

    <div class="queue-shell">
      <div class="queue-hero">
        <div>
          <div class="queue-hero__eyebrow">LLM POST-PROCESSING</div>
          <div class="queue-hero__title">从算法检出，到可信结论</div>
          <div class="queue-hero__desc">这里仅展示独立队列的执行过程与研判结果；规则配置仍在算法任务的新增、编辑和详情中维护。</div>
        </div>
        <div class="queue-hero__pulse">
          <span :class="{ active: stats.pending > 0 }" />
          {{ stats.pending > 0 ? `${stats.pending} 条正在处理` : '队列当前空闲' }}
        </div>
      </div>

      <div class="queue-stats">
        <div class="stat-card stat-card--primary">
          <div class="stat-card__label">实际抽检率</div>
          <div class="stat-card__value">{{ stats.actual_sample_rate_percent || 0 }}<small>%</small></div>
          <div class="stat-card__meta">已抽检 {{ stats.sampled || 0 }} / 告警 {{ stats.total_alerts || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">完成研判</div>
          <div class="stat-card__value">{{ stats.completed || 0 }}</div>
          <div class="stat-card__meta"><span class="ok">成立 {{ stats.confirmed || 0 }}</span> · <span class="reject">误报 {{ stats.rejected || 0 }}</span></div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">队列状态</div>
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
          <div>
            <div class="queue-toolbar__title">研判记录</div>
            <div class="queue-toolbar__sub">共 {{ total }} 条，按进入队列时间倒序展示</div>
          </div>
          <a-segmented v-model:value="status" :options="statusOptions" @change="handleFilterChange" />
        </div>

        <a-alert v-if="errorMessage" type="error" show-icon message="队列加载失败" :description="errorMessage" class="queue-error">
          <template #action><Button size="small" @click="refreshAll">重试</Button></template>
        </a-alert>
        <a-spin :spinning="loading">
          <div v-if="items.length" class="queue-list">
            <div v-for="item in items" :key="item.id" class="queue-item" :class="`queue-item--${item.status}`">
              <div class="queue-item__rail"><span /></div>
              <div class="queue-item__main">
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
.queue-title { display:flex; align-items:center; gap:12px; width:100%; padding-right:8px; }
.queue-title__mark { display:grid; place-items:center; width:42px; height:42px; color:#fff; border-radius:13px; background:linear-gradient(135deg,#4f46e5,#1677ff 58%,#06b6d4); box-shadow:0 8px 20px rgba(22,119,255,.24); }
.queue-title__copy { min-width:0; flex:1; }
.queue-title__name { font-size:17px; font-weight:700; color:#172033; }
.queue-title__sub { margin-top:2px; overflow:hidden; color:rgba(0,0,0,.45); font-size:12px; text-overflow:ellipsis; white-space:nowrap; }
.queue-title__actions { display:flex; align-items:center; gap:8px; color:rgba(0,0,0,.55); font-size:12px; }
.queue-shell { display:flex; flex-direction:column; gap:16px; padding-bottom:20px; }
.queue-hero { display:flex; align-items:center; justify-content:space-between; gap:24px; padding:24px 28px; overflow:hidden; color:#fff; border-radius:16px; background:radial-gradient(circle at 80% -40%,rgba(34,211,238,.5),transparent 45%),linear-gradient(120deg,#111b45,#243b8f 58%,#135c89); box-shadow:0 12px 30px rgba(20,47,110,.18); }
.queue-hero__eyebrow { color:#8ee7ff; font-size:11px; font-weight:700; letter-spacing:1.8px; }
.queue-hero__title { margin-top:5px; font-size:23px; font-weight:700; letter-spacing:.5px; }
.queue-hero__desc { max-width:720px; margin-top:6px; color:rgba(255,255,255,.7); font-size:13px; line-height:1.7; }
.queue-hero__pulse { display:flex; align-items:center; gap:8px; flex-shrink:0; padding:9px 14px; border:1px solid rgba(255,255,255,.18); border-radius:999px; background:rgba(255,255,255,.09); font-size:12px; backdrop-filter:blur(8px); }
.queue-hero__pulse span { width:8px; height:8px; border-radius:50%; background:#5eead4; box-shadow:0 0 0 5px rgba(94,234,212,.12); }
.queue-hero__pulse span.active { animation:pulse 1.6s infinite; }
.queue-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
.stat-card { padding:17px 18px; border:1px solid #e7ebf2; border-radius:13px; background:#fff; box-shadow:0 5px 16px rgba(28,45,80,.05); }
.stat-card--primary { border-color:#cbdcff; background:linear-gradient(145deg,#f4f7ff,#fff); }
.stat-card__label { color:#65708a; font-size:12px; }
.stat-card__value { margin-top:5px; color:#172033; font-size:28px; font-weight:750; line-height:1.2; }
.stat-card__value small { margin-left:2px; font-size:15px; }
.stat-card__meta { margin-top:6px; color:#8b94a8; font-size:12px; }
.stat-card__meta .ok { color:#159b62; } .stat-card__meta .reject { color:#d97706; }
.queue-panel { padding:20px; border:1px solid #e7ebf2; border-radius:15px; background:#fff; box-shadow:0 7px 22px rgba(28,45,80,.05); }
.queue-toolbar { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:16px; }
.queue-toolbar__title { color:#172033; font-size:16px; font-weight:700; }
.queue-toolbar__sub { margin-top:3px; color:#929bad; font-size:12px; }
.queue-error { margin-bottom:14px; }
.queue-list { display:flex; flex-direction:column; }
.queue-item { display:flex; gap:16px; padding:17px 6px; border-top:1px solid #f0f2f6; }
.queue-item:first-child { border-top:0; }
.queue-item__rail { width:12px; padding-top:5px; flex-shrink:0; }
.queue-item__rail span { display:block; width:10px; height:10px; border:3px solid #fff; border-radius:50%; background:#9ca3af; box-shadow:0 0 0 2px #d7dce5; }
.queue-item--pending .queue-item__rail span { background:#1677ff; box-shadow:0 0 0 2px #b8d6ff; }
.queue-item--success .queue-item__rail span { background:#22a06b; box-shadow:0 0 0 2px #bce8d3; }
.queue-item--error .queue-item__rail span,.queue-item--dlt .queue-item__rail span { background:#e5484d; box-shadow:0 0 0 2px #ffc9cb; }
.queue-item__main { min-width:0; flex:1; }
.queue-item__top { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; }
.queue-item__identity { display:flex; align-items:center; flex-wrap:wrap; gap:7px 14px; color:#7a8499; font-size:12px; }
.queue-item__identity :deep(.ant-tag) { margin:0; }
.queue-item__identity strong { color:#20283a; font-size:14px; }
.queue-item__top time { flex-shrink:0; color:#9aa2b2; font-size:12px; }
.queue-item__reason { margin-top:9px; color:#4e586d; font-size:13px; line-height:1.7; word-break:break-word; }
.queue-item__meta { display:flex; align-items:center; flex-wrap:wrap; gap:8px 20px; margin-top:10px; color:#8a93a5; font-size:12px; }
.queue-item__meta span { display:flex; align-items:center; gap:5px; }
.queue-item__meta .correlation { overflow:hidden; max-width:300px; text-overflow:ellipsis; white-space:nowrap; }
.queue-empty { padding:70px 0; }
.queue-pagination { display:flex; justify-content:flex-end; padding-top:18px; border-top:1px solid #f0f2f6; }
@keyframes pulse { 50% { box-shadow:0 0 0 9px rgba(94,234,212,0); } }
@media (max-width:900px) { .queue-stats { grid-template-columns:repeat(2,minmax(0,1fr)); } .queue-hero { align-items:flex-start; flex-direction:column; } }
</style>
