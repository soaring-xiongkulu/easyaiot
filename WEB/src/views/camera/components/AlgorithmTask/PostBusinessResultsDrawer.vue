<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="后处理业务看板"
    width="1100"
    :showFooter="false"
    destroy-on-close
  >
    <div class="business-board">
      <div class="board-heading">
        <div>
          <h2>{{ taskName }}</h2>
          <span>查看已入库的越线、进出、停留和人数阈值事件</span>
        </div>
        <a-button :loading="loading" @click="load">刷新数据</a-button>
      </div>
      <a-space wrap class="filters">
        <a-date-picker v-model:value="day" :allow-clear="false" @change="resetPage" />
        <a-select
          v-model:value="plugin"
          style="width: 160px"
          :options="pluginOptions"
          @change="resetPage"
        />
        <a-input
          v-model:value="deviceId"
          placeholder="摄像头 ID（可选）"
          allow-clear
          @pressEnter="resetPage"
        />
        <a-button @click="resetPage">查询</a-button>
      </a-space>
      <a-alert v-if="error" type="error" show-icon :message="error" />
      <div class="metrics">
        <div v-for="metric in metrics" :key="metric.key" class="metric">
          <span>{{ metric.label }}</span
          ><strong>{{ summary[metric.key] || 0 }}</strong>
          <small>{{ metric.hint }}</small>
        </div>
      </div>
      <a-alert
        type="info"
        show-icon
        message="统计范围为所选日期已入库且通过整条规则链的事件。越线按穿越次数计数；正反向由画线起点→终点决定，重复往返会重复计数。人数峰值仅代表触发阈值时的记录。"
      />
      <a-table
        :data-source="items"
        :columns="columns"
        :loading="loading"
        row-key="id"
        :pagination="{ current: page, pageSize: 20, total, showSizeChanger: false }"
        :scroll="{ x: 850 }"
        @change="changePage"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'time'">{{
            dayjs(record.time).format('MM-DD HH:mm:ss')
          }}</template>
          <template v-else-if="column.key === 'device'">{{
            record.device_name || record.device_id
          }}</template>
          <template v-else-if="column.key === 'results'">
            <a-tag v-for="(text, index) in describe(record)" :key="index" color="blue">{{
              text
            }}</a-tag>
          </template>
        </template>
        <template #emptyText
          ><a-empty
            description="暂无触发记录。请确认任务正在运行、已开启追踪，并为摄像头绘制对应检测线或区域。"
        /></template>
      </a-table>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Alert as AAlert, Button as AButton, DatePicker as ADatePicker, Empty as AEmpty, Input as AInput, Select as ASelect, Space as ASpace, Table as ATable, Tag as ATag } from 'ant-design-vue';
import dayjs from 'dayjs';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { getPostBusinessResults, type PostBusinessResult } from '@/api/device/post_pipeline';

const taskId = ref(0);
const taskName = ref('');
const day = ref(dayjs());
const plugin = ref('');
const deviceId = ref('');
const page = ref(1);
const total = ref(0);
const loading = ref(false);
const error = ref('');
const items = ref<PostBusinessResult[]>([]);
const summary = ref<Record<string, number>>({});
let requestVersion = 0;
const pluginOptions = [
  { label: '全部业务插件', value: '' },
  { label: '越线 / 人流', value: 'line_cross' },
  { label: '区域进出', value: 'region_enter_exit' },
  { label: '停留超时', value: 'dwell_timer' },
  { label: '人数阈值', value: 'headcount_gate' },
];
const metrics = computed(() => [
  {
    key: 'crossings',
    label: '越线次数',
    hint: `正向 ${summary.value.forward || 0} · 反向 ${summary.value.backward || 0}`,
  },
  { key: 'enter', label: '进入次数', hint: `离开 ${summary.value.exit || 0} 次` },
  { key: 'dwell_alerts', label: '停留超时事件', hint: '通过规则链的告警条数' },
  { key: 'peak_count', label: '触发记录人数峰值', hint: '当前筛选范围内' },
]);
const columns = [
  { title: '发生时间', key: 'time', width: 150 },
  { title: '摄像头', key: 'device', width: 180 },
  { title: '区域', dataIndex: 'region', width: 140 },
  { title: '业务结果', key: 'results' },
];
function describe(row: Record<string, any>): string[] {
  const result: string[] = [];
  const r = row.results as PostBusinessResult['results'];
  for (const e of r.line_cross?.crossed || [])
    result.push(
      `${e.region_name || '检测线'} · ${e.direction === 'forward' ? '正向' : e.direction === 'backward' ? '反向' : '越线'} · 目标 ${e.track_id}`,
    );
  for (const e of r.region_enter_exit?.events || [])
    result.push(
      `${e.region_name || '区域'} · ${e.event === 'enter' ? '进入' : '离开'} · 目标 ${e.track_id}`,
    );
  for (const e of r.dwell_timer?.dwells || [])
    result.push(`目标 ${e.track_id} · 停留 ${Number(e.dwell_sec).toFixed(1)} 秒`);
  if (r.headcount_gate)
    result.push(`人数 ${r.headcount_gate.count} · 阈值 ${r.headcount_gate.threshold}`);
  return result;
}
async function load() {
  const version = ++requestVersion;
  loading.value = true;
  error.value = '';
  try {
    const data = await getPostBusinessResults(taskId.value, {
      start: day.value.startOf('day').toISOString(),
      end: day.value.add(1, 'day').startOf('day').toISOString(),
      page: page.value,
      page_size: 20,
      plugin: plugin.value,
      device_id: deviceId.value.trim(),
    });
    if (version !== requestVersion) return;
    items.value = data.items;
    summary.value = data.summary;
    total.value = data.total;
  } catch (e) {
    if (version !== requestVersion) return;
    items.value = [];
    summary.value = {};
    total.value = 0;
    error.value = e instanceof Error ? e.message : '加载失败，请重试';
  } finally {
    if (version === requestVersion) loading.value = false;
  }
}
function resetPage() {
  page.value = 1;
  void load();
}
function changePage(pagination: { current?: number }) {
  page.value = pagination.current || 1;
  void load();
}
const [register] = useDrawerInner((data: { id: number; task_name?: string }) => {
  taskId.value = data.id;
  taskName.value = data.task_name || `任务 ${data.id}`;
  day.value = dayjs();
  plugin.value = '';
  deviceId.value = '';
  page.value = 1;
  items.value = [];
  summary.value = {};
  total.value = 0;
  void load();
});
</script>

<style scoped lang="less">
.business-board {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 8px;
}
.board-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  h2 {
    margin: 0 0 6px;
  }
  span {
    color: #64748b;
  }
}
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}
.metric {
  padding: 20px;
  background: linear-gradient(135deg, #f0f7ff, #fff);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  span,
  small {
    color: #64748b;
  }
  strong {
    font-size: 32px;
    color: #1d4ed8;
  }
}
@media (max-width: 760px) {
  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
