<template>
  <section class="binding-panel">
    <div class="binding-title">
      <strong>② 为此{{ isLine ? '检测线' : '区域' }}设置监测规则</strong
      ><a-tag>{{ region.region_name }}</a-tag>
    </div>
    <p class="binding-sub">
      {{ isLine ? '检测线 → 人流 / 越线 → 该线统计' : '检测区域 → 独立业务规则 → 该区域统计' }}
    </p>
    <div class="instant-feedback">
      {{
        isLine
          ? `今日穿越 ${stats.crossings || 0} 次 · 正向 ${stats.forward || 0} / 反向 ${stats.backward || 0}`
          : `今日进入 ${stats.enter || 0} / 离开 ${stats.exit || 0} · 逗留提醒 ${stats.dwell_alerts || 0}`
      }}
    </div>
    <a-tabs v-model:active-key="activeTab" size="small">
      <a-tab-pane key="rule" tab="规则设置">
        <a-alert v-if="warning" type="warning" show-icon :message="warning" />
        <a-alert
          v-if="state?.legacy_plugins.length"
          type="info"
          show-icon
          message="保存会将旧空间插件转换为按图形独立触发，保留原有参数。原全画面人数规则需核对区域范围；没有对应图形的旧规则会暂停。"
        />
        <a-select
          v-model:value="plugin"
          :options="options"
          style="width: 100%"
          @change="loadDraft"
        />
        <div class="relation">
          <span>{{ region.region_name }}</span
          ><b>→</b><span>{{ pluginName }}</span
          ><a-tag :color="bound ? 'green' : 'default'">{{
            bound ? (bound.enabled === false ? '已暂停' : '已绑定') : '待绑定'
          }}</a-tag>
        </div>
        <div v-if="plugin === 'line_cross'" class="field">
          <label>穿越方向</label
          ><a-select v-model:value="params.direction" :options="directionOptions" /><small
            >画面绿色箭头为正向。双向会分别统计正向、反向穿越次数。</small
          >
        </div>
        <div v-if="plugin === 'region_enter_exit'" class="field">
          <label>监测事件</label
          ><a-select v-model:value="params.event_type" :options="eventOptions" />
        </div>
        <div v-if="plugin === 'headcount_gate'" class="field">
          <label>人数达到</label
          ><a-input-number
            v-model:value="params.threshold"
            :min="1"
            :precision="0"
            addon-after="人"
          /><label>重复提醒间隔</label
          ><a-input-number v-model:value="params.cooldown_sec" :min="0" addon-after="秒" />
        </div>
        <div v-if="plugin === 'dwell_timer'" class="field">
          <label>停留超过</label
          ><a-input-number v-model:value="params.min_dwell_sec" :min="1" addon-after="秒" />
        </div>
        <div class="field">
          <label>模型目标类别</label
          ><a-select
            v-model:value="params.target_classes"
            mode="tags"
            placeholder="例如 person，需与模型类别一致"
          /><small>此{{ isLine ? '线' : '区域' }}的适用模型沿用上方选择。</small>
        </div>
        <a-space wrap
          ><a-switch
            v-model:checked="enabled"
          checked-children="启用"
            un-checked-children="暂停"
          /><a-button
            type="primary"
            :loading="busy"
            :disabled="saving || !!warning || !state"
            @click="save(false)"
            >{{ bound ? '保存规则' : '建立绑定' }}</a-button
          ><a-popconfirm
            v-if="bound"
            title="解除这条监测规则？保留图形和历史数据。"
            @confirm="save(true)"
            ><a-button danger :disabled="busy || saving">解除绑定</a-button></a-popconfirm
          ></a-space
        >
        <p v-if="saving" class="binding-sub">正在保存图形，完成后即可绑定…</p>
        <a-alert v-if="feedback" :type="feedbackType" show-icon :message="feedback" />
        <a-popconfirm v-if="failedDraft" title="重新载入会放弃本次未保存的规则参数，是否继续？" @confirm="reloadLatest"><a-button>重新载入最新配置</a-button></a-popconfirm>
      </a-tab-pane>
      <a-tab-pane key="feedback" tab="统计反馈">
        <div class="stats-heading">
          <strong>③ 此{{ isLine ? '检测线' : '区域' }}今日反馈</strong
          ><a-button size="small" :loading="statsLoading" @click="loadStats">刷新</a-button>
        </div>
        <div class="region-stats">
          <template v-if="isLine"
            ><div>
              <strong>{{ stats.crossings || 0 }}</strong
              ><small>穿越总次数</small>
            </div>
            <div>
              <strong>{{ stats.forward || 0 }} / {{ stats.backward || 0 }}</strong
              ><small>正向 / 反向</small>
            </div></template
          ><template v-else
            ><div>
              <strong>{{ stats.enter || 0 }} / {{ stats.exit || 0 }}</strong
              ><small>进入 / 离开</small>
            </div>
            <div>
              <strong>{{ stats.dwell_alerts || 0 }}</strong
              ><small>逗留提醒</small>
            </div>
            <div>
              <strong>{{ stats.peak_count || 0 }}</strong
              ><small>提醒记录人数峰值</small>
            </div></template
          >
        </div>
        <p v-if="isLine" class="binding-sub">
          正向 {{ stats.forward || 0 }} · 反向
          {{ stats.backward || 0 }}。仅统计此图形已入库事件，穿越次数不等于去重人数。
        </p>
        <p v-else class="binding-sub">
          仅统计此区域已入库事件；离开含目标消失后的超时补记，同一目标重复进出会重复计数。
        </p>
        <p class="binding-sub">
          任务{{ state?.task.run_status === 'running' ? '运行中' : '未运行' }} ·
          {{
            lastEvent
              ? `最近事件 ${lastEvent}`
              : '暂无事件：请检查任务运行、追踪、类别及实际穿越动作'
          }}
        </p>
        <a-alert v-if="statsError" type="error" :message="statsError" />
      </a-tab-pane>
    </a-tabs>
  </section>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { Alert as AAlert, Button as AButton, InputNumber as AInputNumber, Popconfirm as APopconfirm, Select as ASelect, Space as ASpace, Switch as ASwitch, Tabs as ATabs, Tag as ATag } from 'ant-design-vue';
const ATabPane = ATabs.TabPane;
import dayjs from 'dayjs';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import type { DeviceDetectionRegion } from '@/api/device/device_detection_region';
import {
  savePostRegionBinding,
  getPostBusinessResults,
  type PostBindingState,
} from '@/api/device/post_pipeline';
const props = defineProps<{
  taskId: number;
  region: DeviceDetectionRegion;
  state: PostBindingState | null;
  revision: number;
  saving: boolean;
}>();
const emit = defineEmits<{ (e: 'saved', state: PostBindingState): void; (e: 'reload'): void; (e:'reload-latest'):void }>();
const isLine = computed(() => props.region.region_type === 'line');
const names: Record<string, string> = {
  line_cross: '人流 / 越线监测',
  region_enter_exit: '区域进出',
  headcount_gate: '人员聚集',
  dwell_timer: '逗留提醒',
};
const options = computed(() =>
  (isLine.value ? ['line_cross'] : ['region_enter_exit', 'headcount_gate', 'dwell_timer']).map(
    (value) => ({ value, label: names[value] }),
  ),
);
const plugin = ref('line_cross');
const params = ref<Record<string, any>>({});
const enabled = ref(true);
const busy = ref(false);
const activeTab = ref('rule');
const feedback = ref('');
const failedDraft = ref(false);
function reloadLatest() { failedDraft.value=false;feedback.value='';emit('reload-latest'); }
const feedbackType = ref<'success' | 'warning' | 'error'>('success');
const bound = computed(
  () =>
    props.state?.pipeline.find(
      (s) =>
        s.plugin === plugin.value &&
        (s.params?.region_ids as number[] | undefined)?.includes(props.region.id),
    ) ||
    props.state?.pipeline.find(
      (s) => s.plugin === plugin.value && !(s.params?.region_ids as number[] | undefined)?.length,
    ),
);
const pluginName = computed(() => names[plugin.value]);
const directionOptions = [
  { label: '双向（分别统计）', value: 'both' },
  { label: '仅正向（绿色箭头）', value: 'forward' },
  { label: '仅反向', value: 'backward' },
];
const eventOptions = [
  { label: '进入与离开', value: 'both' },
  { label: '仅进入', value: 'enter' },
  { label: '仅离开', value: 'exit' },
];
const warning = computed(() => {
  if (!props.state) return '正在加载规则配置';
  const t = props.state.task;
  if (!t.alert_event_enabled) return '请先在任务设置中开启告警事件并保存任务，再配置监测规则。';
  if (
    plugin.value !== 'headcount_gate' &&
    (t.task_type !== 'realtime' || t.executor === 'cpp' || !t.tracking_enabled)
  )
    return '此规则需要 Python 实时模式并开启目标追踪，请先修改并保存任务设置。';
  if (
    plugin.value !== 'headcount_gate' &&
    (t.post_process_enabled || t.pose_analysis_enabled || t.pose_intent_enabled)
  )
    return '此连续轨迹规则暂不能与业务脚本或姿态分析混用。';
  return '';
});
function loadDraft() {
  failedDraft.value=false;
  params.value = JSON.parse(
    JSON.stringify(
      bound.value?.params || {
        direction: 'both',
        sample_point: 'bottom',
        event_type: 'both',
        hit_mode: 'bottom_center',
        threshold: 5,
        operator: 'gte',
        cooldown_sec: 60,
        min_dwell_sec: 30,
        target_classes: ['person'],
      },
    ),
  );
  enabled.value = bound.value?.enabled !== false;
  feedback.value = '';
}
async function save(remove: boolean) {
  if (!props.state || props.region.id <= 0) return;
  busy.value = true;
  feedback.value = '';
  try {
    const state = await savePostRegionBinding(props.taskId, props.region.id, {
      expected_revision: props.revision,
      plugin: plugin.value,
      params: params.value,
      enabled: enabled.value,
      remove,
    });
    emit('saved', state);
    failedDraft.value=false;
    feedbackType.value = state.runtime_sync_status === 'pending' ? 'warning' : 'success';
    feedback.value =
      state.runtime_sync_status === 'pending'
        ? '规则已保存，运行配置同步中'
        : state.runtime_sync_status === 'not_running'
          ? '规则已保存，将在任务启动时生效'
          : '规则已保存并同步到运行配置';
  } catch (e) {
    feedbackType.value = 'error';
    failedDraft.value=true;
    feedback.value = formatApiErrorMessage(e,'保存失败，已保留本次参数，可重试或重新载入最新配置');
    emit('reload');
  } finally {
    busy.value = false;
  }
}
const stats = ref<Record<string, number>>({});
const statsLoading = ref(false);
const statsError = ref('');
const lastEvent = ref('');
let sequence = 0;
async function loadStats() {
  const seq = ++sequence;
  stats.value = {};
  lastEvent.value = '';
  statsError.value = '';
  if (props.region.id <= 0) return;
  statsLoading.value = true;
  try {
    const now = dayjs();
    const data = await getPostBusinessResults(props.taskId, {
      region_id: props.region.id,
      device_id: props.region.device_id,
      start: now.startOf('day').toISOString(),
      end: now.add(1, 'day').startOf('day').toISOString(),
      page: 1,
      page_size: 1,
    });
    if (seq !== sequence) return;
    stats.value = data.summary;
    lastEvent.value = data.items[0] ? dayjs(data.items[0].time).format('HH:mm:ss') : '';
  } catch (e) {
    if (seq === sequence) statsError.value = e instanceof Error ? e.message : '统计加载失败';
  } finally {
    if (seq === sequence) statsLoading.value = false;
  }
}
watch(
  () => `${props.region.id}:${props.region.region_type}`,
  () => {
    plugin.value = isLine.value ? 'line_cross' : 'region_enter_exit';
    loadDraft();
    void loadStats();
  },
  { immediate: true },
);
watch(
  () => props.state,
  () => {
    if (failedDraft.value) return;
    const previous = feedback.value;
    loadDraft();
    feedback.value = previous;
  },
);
</script>

<style lang="less" scoped>
.binding-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-top: 1px solid #dbeafe;
  background: #f8fbff;
  flex-shrink: 0;
}
.binding-title,
.stats-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}
.binding-sub {
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
  margin: 0;
}
.relation {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 10px;
  border: 1px solid #bfdbfe;
  background: #fff;
  border-radius: 8px;
  font-size: 12px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  small {
    color: #64748b;
    font-size: 12px;
  }
}
.region-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  div {
    display: flex;
    flex-direction: column;
    padding: 10px;
    border-radius: 8px;
    background: #fff;
    border: 1px solid #e2e8f0;
  }
  strong {
    font-size: 22px;
    color: #2563eb;
  }
  small {
    color: #64748b;
  }
}
.instant-feedback {
  font-size: 12px;
  color: #1d4ed8;
  padding: 8px;
  border-radius: 8px;
  background: #eff6ff;
}
.binding-panel :deep(.ant-tabs-tabpane) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
