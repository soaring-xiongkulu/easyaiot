<template>
  <section class="tg-panel" data-testid="training-ground">
    <!-- 标题栏：身份 + 环境说明 + 运行状态 -->
    <header class="tg-bar">
      <div class="tg-bar__title">
        <Icon icon="ant-design:aim-outlined" :size="16" color="#0e7490" />
        <strong>训练场</strong>
        <span class="tg-bar__sub">放置并拖动模拟人 · 每帧经真实 MQTT 驱动 POST 插件引擎 · 与生产链路一致</span>
      </div>
      <div class="tg-bar__status">
        <a-tag v-if="running" color="processing">
          <span class="tg-pulse" />投放中 · {{ intervalMs / 1000 }}s/帧
        </a-tag>
        <a-tag v-else color="default">已停止</a-tag>
        <span class="tg-bar__frames">{{ deviceName }} · 已投 {{ framesSent }} 帧</span>
      </div>
    </header>

    <div class="tg-main">
      <!-- 地图区 -->
      <div class="tg-map">
        <svg
          ref="mapRef"
          class="tg-canvas"
          viewBox="0 0 1000 562.5"
          :class="{ 'is-live': running }"
          @pointerdown="onMapPointerDown"
          @pointermove="onMapPointerMove"
          @pointerup="onMapPointerUp"
          @pointerleave="onMapPointerUp"
        >
          <defs>
            <pattern id="tg-grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(14,116,144,.08)" stroke-width="1" />
            </pattern>
            <marker id="tg-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#16a34a" />
            </marker>
            <radialGradient id="tg-actor-grad" cx="35%" cy="30%">
              <stop offset="0%" stop-color="#fdba74" />
              <stop offset="100%" stop-color="#ea580c" />
            </radialGradient>
          </defs>

          <rect x="0" y="0" width="1000" height="562.5" fill="#f8fafc" />
          <rect x="0" y="0" width="1000" height="562.5" fill="url(#tg-grid)" />
          <rect x="0" y="0" width="1000" height="118" class="tg-scene-wall" />
          <rect x="70" y="150" width="860" height="370" class="tg-scene-floor" />
          <rect x="30" y="320" width="105" height="165" class="tg-scene-prop" />
          <rect x="865" y="320" width="105" height="165" class="tg-scene-prop" />
          <text x="500" y="66" text-anchor="middle" class="tg-scene-label">{{ deviceName }} · 训练场景</text>

          <!-- 已绘制图形：线带 A/B 端点与正向箭头，区域带名称 -->
          <g v-for="region in visibleRegions" :key="region.id">
            <line
              v-if="region.type === 'line'"
              :x1="region.points[0].x * 1000"
              :y1="region.points[0].y * 562.5"
              :x2="region.points[1].x * 1000"
              :y2="region.points[1].y * 562.5"
              class="tg-shape-line"
              marker-end="url(#tg-arrow)"
            />
            <template v-if="region.type === 'line'">
              <circle :cx="region.points[0].x * 1000" :cy="region.points[0].y * 562.5" r="9" class="tg-endpoint" />
              <circle :cx="region.points[1].x * 1000" :cy="region.points[1].y * 562.5" r="9" class="tg-endpoint tg-endpoint--b" />
              <text :x="region.points[0].x * 1000" :y="region.points[0].y * 562.5 + 4" text-anchor="middle" class="tg-endpoint-label">A</text>
              <text :x="region.points[1].x * 1000" :y="region.points[1].y * 562.5 + 4" text-anchor="middle" class="tg-endpoint-label">B</text>
            </template>
            <polygon
              v-else
              :points="region.points.map((p) => `${p.x * 1000},${p.y * 562.5}`).join(' ')"
              :class="['tg-shape-poly', { 'is-hot': hotRegionIds.includes(region.id) }]"
            />
            <text :x="regionCenter(region).x" :y="regionCenter(region).y" text-anchor="middle" class="tg-shape-name">
              {{ region.name }}{{ region.type === 'line' ? '' : hotRegionIds.includes(region.id) ? ' · 命中' : '' }}
            </text>
          </g>

          <!-- 拖动尾迹 -->
          <polyline
            v-for="actor in actorsWithTrail"
            :key="`trail-${actor.id}`"
            :points="actor.trail!.map((p) => `${p.x * 1000},${p.y * 562.5}`).join(' ')"
            class="tg-trail"
          />

          <!-- 模拟人 -->
          <g
            v-for="actor in actors"
            :key="actor.id"
            class="tg-person"
            :class="{ 'is-dragging': draggingId === actor.id }"
            :transform="`translate(${actor.x * 1000}, ${actor.y * 562.5})`"
          >
            <circle r="22" class="tg-person-halo" />
            <circle r="15" class="tg-person-body" />
            <text y="4.5" text-anchor="middle" class="tg-person-id">{{ actor.id }}</text>
          </g>

          <!-- 图例（地图右下角） -->
          <g class="tg-legend" transform="translate(778, 496)">
            <rect x="0" y="0" width="208" height="52" rx="6" class="tg-legend-box" />
            <line x1="12" y1="15" x2="44" y2="15" class="tg-shape-line" marker-end="url(#tg-arrow)" />
            <text x="52" y="19" class="tg-legend-text">A→B 为正向</text>
            <rect x="12" y="30" width="26" height="14" class="tg-shape-poly" />
            <text x="52" y="41" class="tg-legend-text">区域（命中高亮）</text>
            <circle cx="222" cy="15" r="8" class="tg-person-body" />
            <text x="222" y="41" text-anchor="middle" class="tg-legend-text">模拟人</text>
          </g>
        </svg>
        <p class="tg-map-hint">点击空白放置模拟人 · 按住拖动（路径实时穿越即计数） · 拖入区域查看命中高亮</p>
      </div>

      <!-- 控制台 -->
      <div class="tg-console">
        <div class="tg-actions">
          <Button size="small" :type="running ? 'primary' : 'default'" :pre-icon="running ? 'ant-design:pause-circle-outlined' : 'ant-design:play-circle-outlined'" @click="toggleRun">
            {{ running ? '停止投放' : '启动投放' }}
          </Button>
          <Button size="small" :disabled="running" pre-icon="ant-design:send-outlined" @click="publishNow">投放一帧</Button>
          <Button size="small" :disabled="!actors.length" pre-icon="ant-design:clear-outlined" @click="clearActors">清空</Button>
          <Button size="small" pre-icon="ant-design:reload-outlined" :loading="statsLoading" @click="loadSummary">刷新</Button>
        </div>
        <div class="tg-rate">
          <span class="tg-rate__label">投放间隔</span>
          <a-radio-group v-model:value="intervalMs" size="small" button-style="solid" :options="rateOptions" option-type="button" />
        </div>

        <div class="tg-stats">
          <div v-for="card in statCards" :key="card.key" class="tg-stat" :class="`is-${card.key}`" :data-testid="`counter-${card.key}`">
            <Icon :icon="card.icon" :size="18" :color="card.color" />
            <div class="tg-stat__body">
              <strong :style="{ color: card.color }">{{ card.value }}</strong>
              <small>{{ card.label }}</small>
            </div>
            <em>{{ card.hint }}</em>
          </div>
        </div>

        <div class="tg-log">
          <div class="tg-log__head">
            <Icon icon="ant-design:history-outlined" :size="13" color="#64748b" />
            <span>触发流水（今日 · 已入库告警）</span>
          </div>
          <ul class="tg-log__list">
            <li v-for="(log, i) in recentLogs" :key="i" :class="`is-${log.kind}`">
              <time>{{ log.time }}</time>
              <span class="tg-log__region">{{ log.region }}</span>
              <a-tag class="tg-log__tag" :color="kindColor(log.kind)">{{ log.text }}</a-tag>
            </li>
            <li v-if="!recentLogs.length" class="tg-log__empty">尚无触发：放置模拟人，拖过线或拖入区域后投放</li>
          </ul>
        </div>
        <p v-if="error" class="tg-error">
          <Icon icon="ant-design:warning-outlined" :size="13" color="#dc2626" />
          {{ error }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue';
import { RadioGroup as ARadioGroup, Tag as ATag } from 'ant-design-vue';
import dayjs from 'dayjs';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import { getPostBusinessResults, postTrainFrame } from '@/api/device/post_pipeline';

const props = defineProps<{
  taskId: number;
  deviceId: string;
  deviceName: string;
  regions: Array<{ id: number; name: string; type: string; points: Array<{ x: number; y: number }>; enabled?: boolean }>;
}>();

interface Actor {
  id: number;
  x: number;
  y: number;
  trail?: Array<{ x: number; y: number }>;
}

const actors = ref<Actor[]>([]);
const running = ref(false);
const intervalMs = ref(1000);
const framesSent = ref(0);
const nextActorId = ref(1);
const draggingId = ref<number | null>(null);
const error = ref('');
const statsLoading = ref(false);
const summary = ref<Record<string, number>>({});
const recentLogs = ref<Array<{ time: string; region: string; kind: string; text: string }>>([]);
const mapRef = ref<SVGSVGElement | null>(null);
const hotRegionIds = ref<number[]>([]);
let publishTimer: ReturnType<typeof setInterval> | null = null;
let pollTimer: ReturnType<typeof setInterval> | null = null;
let lastLogId = 0;

const rateOptions = [
  { value: 500, label: '0.5s' },
  { value: 1000, label: '1s' },
  { value: 2000, label: '2s' },
];

const visibleRegions = computed(() => props.regions.filter((r) => r.enabled !== false && r.points?.length >= 2));
const actorsWithTrail = computed(() => actors.value.filter((a) => (a.trail?.length ?? 0) >= 2));

const statCards = computed(() => [
  { key: 'crossings', icon: 'ant-design:swap-right-outlined', color: '#2563eb', value: summary.value.crossings || 0, label: '越线次数', hint: `正 ${summary.value.forward || 0} · 反 ${summary.value.backward || 0}` },
  { key: 'enter', icon: 'ant-design:login-outlined', color: '#16a34a', value: summary.value.enter || 0, label: '区域进入', hint: `离开 ${summary.value.exit || 0} 含补记` },
  { key: 'peak', icon: 'ant-design:team-outlined', color: '#7c3aed', value: summary.value.peak_count || 0, label: '人数峰值', hint: '聚集阈值触发' },
  { key: 'dwell', icon: 'ant-design:hourglass-outlined', color: '#d97706', value: summary.value.dwell_alerts || 0, label: '逗留提醒', hint: '停留超时' },
]);

function kindColor(kind: string) {
  if (kind === 'forward' || kind === 'enter') return 'success';
  if (kind === 'backward' || kind === 'exit') return 'error';
  if (kind === 'dwell') return 'warning';
  if (kind === 'headcount') return 'purple';
  return 'default';
}

function regionCenter(region: { points: Array<{ x: number; y: number }> }) {
  const n = region.points.length || 1;
  return {
    x: (region.points.reduce((s, p) => s + p.x, 0) / n) * 1000,
    y: (region.points.reduce((s, p) => s + p.y, 0) / n) * 562.5,
  };
}

function eventPoint(e: PointerEvent): { x: number; y: number } | null {
  const svg = mapRef.value;
  if (!svg) return null;
  const rect = svg.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width;
  const y = (e.clientY - rect.top) / rect.height;
  if (x < 0 || x > 1 || y < 0 || y > 1) return null;
  return { x, y };
}

function hitActor(pos: { x: number; y: number }): Actor | null {
  const svg = mapRef.value;
  if (!svg) return null;
  const rect = svg.getBoundingClientRect();
  const rPx = (19 / 1000) * rect.width * 1.4;
  return actors.value.find((a) => Math.hypot((a.x - pos.x) * rect.width, (a.y - pos.y) * rect.height) < rPx) || null;
}

function onMapPointerDown(e: PointerEvent) {
  const pos = eventPoint(e);
  if (!pos) return;
  const hit = hitActor(pos);
  if (hit) {
    draggingId.value = hit.id;
    hit.trail = [{ x: hit.x, y: hit.y }];
  } else {
    const id = nextActorId.value++;
    actors.value.push({ id, x: pos.x, y: pos.y });
    draggingId.value = id;
  }
  (e.currentTarget as Element).setPointerCapture?.(e.pointerId);
}

function onMapPointerMove(e: PointerEvent) {
  if (draggingId.value == null) return;
  const pos = eventPoint(e);
  if (!pos) return;
  const actor = actors.value.find((a) => a.id === draggingId.value);
  if (actor) {
    actor.x = pos.x;
    actor.y = pos.y;
    actor.trail = [...(actor.trail || []), { x: pos.x, y: pos.y }].slice(-14);
    highlightRegions(pos);
  }
}

function onMapPointerUp() {
  draggingId.value = null;
  hotRegionIds.value = [];
}

function highlightRegions(pos: { x: number; y: number }) {
  hotRegionIds.value = visibleRegions.value
    .filter((r) => r.type !== 'line' && pointInPolygon(pos, r.points))
    .map((r) => r.id);
}

function pointInPolygon(pos: { x: number; y: number }, points: Array<{ x: number; y: number }>) {
  let inside = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const xi = points[i].x;
    const yi = points[i].y;
    const xj = points[j].x;
    const yj = points[j].y;
    if ((yi > pos.y) !== (yj > pos.y) && pos.x < ((xj - xi) * (pos.y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

async function publishFrame() {
  try {
    await postTrainFrame(props.taskId, {
      device_id: props.deviceId,
      actors: actors.value.map((a) => ({ track_id: 9_000_000 + a.id, x: a.x, y: a.y })),
    });
    framesSent.value++;
    error.value = '';
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}

function publishNow() {
  void publishFrame();
}

function toggleRun() {
  if (running.value) {
    stopTimers();
  } else {
    running.value = true;
    void publishFrame();
    publishTimer = setInterval(() => void publishFrame(), intervalMs.value);
    pollTimer = setInterval(() => void loadSummary(), 2000);
  }
}

function stopTimers() {
  running.value = false;
  if (publishTimer) {
    clearInterval(publishTimer);
    publishTimer = null;
  }
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function clearActors() {
  actors.value = [];
  draggingId.value = null;
}

async function loadSummary() {
  statsLoading.value = true;
  try {
    const data = await getPostBusinessResults(props.taskId, {
      start: dayjs().startOf('day').toISOString(),
      end: dayjs().toISOString(),
      page: 1,
      page_size: 20,
      device_id: props.deviceId,
    });
    summary.value = data.summary || {};
    const items = (data.items || []).filter((it) => it.id > lastLogId);
    if (items.length) {
      lastLogId = Math.max(...items.map((it) => it.id));
      const logs = items.flatMap((it) => describeResult(it));
      recentLogs.value = [...logs.reverse(), ...recentLogs.value].slice(0, 30);
    }
    error.value = '';
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    statsLoading.value = false;
  }
}

function describeResult(item: { id: number; time: string; region: string; results: Record<string, Record<string, any>> }) {
  const time = dayjs(item.time).format('HH:mm:ss');
  const out: Array<{ time: string; region: string; kind: string; text: string }> = [];
  for (const [plugin, payload] of Object.entries(item.results || {})) {
    const p = payload as any;
    for (const ev of p?.events || []) {
      const label =
        ev.event === 'enter'
          ? '进入'
          : ev.event === 'exit'
            ? ev.synthesized
              ? '离开·补记'
              : '离开'
            : String(ev.event || plugin);
      out.push({ time, region: ev.region_name || item.region, kind: String(ev.event || plugin), text: label });
    }
    // line_cross 输出 crossed[]，方向在 direction 字段
    for (const ev of p?.crossed || []) {
      out.push({
        time,
        region: ev.region_name || item.region,
        kind: String(ev.direction || 'forward'),
        text: ev.direction === 'backward' ? '反向越线' : '正向越线',
      });
    }
    // dwell_timer 输出 dwells[]，无 event 字段
    for (const ev of p?.dwells || []) {
      out.push({
        time,
        region: ev.region_name || item.region,
        kind: 'dwell',
        text: `逗留 ${Math.round(Number(ev.dwell_sec ?? 0))} 秒`,
      });
    }
    // headcount_gate 直接打平在插件载荷上
    if (p?.headcount_gate === 'applied' && p.count != null) {
      out.push({
        time,
        region: item.region,
        kind: 'headcount',
        text: `聚集 ${p.count} 人（阈值 ${p.operator === 'lte' ? '≤' : '≥'} ${p.threshold ?? '?'}）`,
      });
    }
  }
  return out;
}

defineExpose({ loadSummary });

onUnmounted(stopTimers);
void loadSummary();
</script>

<style lang="less" scoped>
@tg-border: #e2e8f0;
@tg-accent: #0e7490;

.tg-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid @tg-border;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

/* 标题栏 */
.tg-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid @tg-border;
  background: linear-gradient(180deg, #f8fafc, #fff);

  &__title {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;

    strong {
      font-size: 14px;
      color: #0f172a;
    }
  }

  &__sub {
    font-size: 12px;
    color: #64748b;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__status {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  &__frames {
    font-size: 12px;
    font-weight: 500;
    color: #0f172a;
    font-variant-numeric: tabular-nums;
  }
}

.tg-pulse {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 5px;
  border-radius: 50%;
  background: #1677ff;
  animation: tg-blink 1.2s ease-in-out infinite;
}

@keyframes tg-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}

.tg-main {
  display: flex;
  gap: 0;
}

/* 地图 */
.tg-map {
  flex: 1 1 62%;
  min-width: 0;
  padding: 10px;
  border-right: 1px solid @tg-border;
}

.tg-canvas {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  user-select: none;
  touch-action: none;
  cursor: crosshair;

  &.is-live {
    border-color: #34d399;
    box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.3);
  }
}

.tg-scene-wall { fill: #c3d2e0; }
.tg-scene-floor { fill: #fbfaf5; stroke: #9db2c5; stroke-width: 6; }
.tg-scene-prop { fill: #dde8dd; stroke: #b6c8b6; stroke-width: 2; }
.tg-scene-label { fill: #64748b; font-size: 24px; letter-spacing: 2px; }

.tg-shape-line {
  stroke: #2563eb;
  stroke-width: 6;
  stroke-linecap: round;
}

.tg-shape-poly {
  fill: rgba(37, 99, 235, 0.1);
  stroke: #2563eb;
  stroke-width: 3.5;
  stroke-dasharray: 10 6;

  &.is-hot {
    fill: rgba(245, 158, 11, 0.28);
    stroke: #f59e0b;
    stroke-dasharray: none;
  }
}

.tg-shape-name {
  fill: #1e40af;
  font-size: 17px;
  font-weight: 600;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.9);
  stroke-width: 4px;
  pointer-events: none;
}

.tg-endpoint {
  fill: #fff;
  stroke: #2563eb;
  stroke-width: 3;

  &--b {
    stroke: #16a34a;
  }
}

.tg-endpoint-label {
  font-size: 11px;
  font-weight: 700;
  fill: #1e40af;
  pointer-events: none;
}

.tg-trail {
  fill: none;
  stroke: rgba(234, 88, 12, 0.4);
  stroke-width: 3;
  stroke-dasharray: 2 6;
  stroke-linecap: round;
  pointer-events: none;
}

.tg-person {
  cursor: grab;

  &.is-dragging {
    cursor: grabbing;
  }
}

.tg-person-halo {
  fill: rgba(234, 88, 12, 0.12);
}

.tg-person-body {
  fill: url(#tg-actor-grad);
  stroke: #fff;
  stroke-width: 3;
}

.tg-person-id {
  fill: #fff;
  font-size: 13px;
  font-weight: 700;
  pointer-events: none;
}

.tg-legend-box {
  fill: rgba(255, 255, 255, 0.92);
  stroke: #cbd5e1;
}

.tg-legend-text {
  fill: #475569;
  font-size: 13px;
}

.tg-map-hint {
  margin: 6px 2px 0;
  font-size: 12px;
  color: #94a3b8;
}

/* 控制台 */
.tg-console {
  flex: 1 1 38%;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
}

.tg-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tg-rate {
  display: flex;
  align-items: center;
  gap: 8px;

  &__label {
    font-size: 12px;
    color: #475569;
  }
}

.tg-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.tg-stat {
  display: grid;
  grid-template-columns: 24px 1fr;
  grid-template-rows: auto auto;
  column-gap: 8px;
  padding: 9px 10px;
  border: 1px solid @tg-border;
  border-radius: 8px;
  background: #fff;
  transition: border-color 0.15s;

  > :first-child {
    grid-row: 1 / 3;
    align-self: center;
  }

  &:hover {
    border-color: #94a3b8;
  }

  strong {
    font-size: 21px;
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
  }

  small {
    font-size: 12px;
    color: #475569;
  }

  em {
    grid-column: 1 / 3;
    font-size: 11px;
    color: #94a3b8;
    font-style: normal;
    margin-top: 3px;
  }
}

.tg-log {
  flex: 1;
  min-height: 140px;
  max-height: 260px;
  display: flex;
  flex-direction: column;
  border: 1px solid @tg-border;
  border-radius: 8px;
  overflow: hidden;

  &__head {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    font-size: 12px;
    color: #475569;
    background: #f8fafc;
    border-bottom: 1px solid @tg-border;
  }

  &__list {
    flex: 1;
    list-style: none;
    margin: 0;
    padding: 4px 8px;
    overflow-y: auto;
    mask-image: linear-gradient(180deg, #000 82%, transparent);
    -webkit-mask-image: linear-gradient(180deg, #000 82%, transparent);

    li {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 3px 4px;
      border-bottom: 1px dashed #f1f5f9;
      font-size: 12px;
    }

    time {
      color: #94a3b8;
      font-variant-numeric: tabular-nums;
      flex-shrink: 0;
    }
  }

  &__region {
    color: #334155;
    min-width: 70px;
    max-width: 96px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-shrink: 0;
  }

  &__tag {
    margin: 0;
    line-height: 18px;
    font-size: 11px;
  }

  &__empty {
    color: #94a3b8;
    padding: 10px 4px;
  }
}

.tg-error {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  color: #dc2626;
  font-size: 12px;
}
</style>
