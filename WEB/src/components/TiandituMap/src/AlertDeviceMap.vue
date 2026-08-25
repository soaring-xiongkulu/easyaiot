<script setup lang="ts">
import { Spin } from 'ant-design-vue';
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';
import dayjs from 'dayjs';
import Overlay from 'ol/Overlay';
import { useRouter } from 'vue-router';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import BasicTiandituMap from './BasicTiandituMap.vue';
import AlertMapFloatLayer from './components/AlertMapFloatLayer.vue';
import CameraAlertCard from './components/CameraAlertCard.vue';
import { useMapMarkers } from '../composables/useMapMarkers';
import { useMapHeatmap } from '../composables/useMapHeatmap';
import { useMapMeasure } from '../composables/useMapMeasure';
import { useMapSpatialQuery } from '../composables/useMapSpatialQuery';
import { useMapPulse } from '../composables/useMapPulse';
import { useMapDisplayFilters } from '../composables/useMapDisplayFilters';
import { MAP_LAYER_ZINDEX } from '../constants';
import { useAlertMapData, type AlertMapQuery } from '../business/useAlertMapData';
import type { FaceTrajectoryPoint } from '@/api/device/face_library';
import type { PlateTrajectoryPoint } from '@/api/device/plate_library';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import LineString from 'ol/geom/LineString';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import Style from 'ol/style/Style';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import Stroke from 'ol/style/Stroke';
import Text from 'ol/style/Text';
import RegularShape from 'ol/style/RegularShape';
import { fromLonLat } from 'ol/proj';
import { boundingExtent } from 'ol/extent';
import type { EventsKey } from 'ol/events';
import { useMessage } from '@/hooks/web/useMessage';
import type { AlertMapItem, MapHoverInfo, MapMarkerData, TiandituBaseMapType } from '../types';

const props = withDefaults(defineProps<{
  query?: AlertMapQuery;
  showCameras?: boolean;
  showAlerts?: boolean;
  height?: string;
  enableCluster?: boolean;
  /** 显示告警热力图层 */
  showHeat?: boolean;
  /** 同坐标聚合点展开后，点击叶子是否自动收起（默认 false=保持展开便于连续查看） */
  spiderfyCollapseOnSelect?: boolean;
  /** 嵌入全屏弹窗：去掉 Card 外壳，铺满地图区域 */
  embedded?: boolean;
  /** 地图模式：device=设备/告警核心视图；face=人脸时空轨迹视图；plate=车牌轨迹视图（相互独立） */
  mapMode?: 'device' | 'face' | 'plate';
  /** 出现轨迹（某天被各摄像头识别命中的地图坐标时间线），人脸/车牌轨迹点通用 */
  trajectory?: Array<FaceTrajectoryPoint | PlateTrajectoryPoint>;
  /** 轨迹对应主体（人员姓名或车牌号，详情卡片标题/清除提示） */
  trajectoryTitle?: string;
}>(), {
  showCameras: true,
  showAlerts: true,
  height: '100%',
  enableCluster: true,
  showHeat: false,
  spiderfyCollapseOnSelect: false,
  embedded: false,
  mapMode: 'device',
  trajectory: () => [],
  trajectoryTitle: '',
});

const cardBodyStyle = computed(() => ({
  padding: 0,
  height: props.height,
  minHeight: 0,
}));

const emit = defineEmits<{
  (e: 'marker-click', marker: MapMarkerData): void;
  (e: 'alert-click', alert: Record<string, unknown>): void;
}>();

const { createMessage } = useMessage();
const router = useRouter();
const mapRef = ref<InstanceType<typeof BasicTiandituMap> | null>(null);
const mapInstance = computed(() => mapRef.value?.map ?? null);
const baseMapType = ref<TiandituBaseMapType>('vec');
const alertData = useAlertMapData();

const markers = useMapMarkers({
  map: mapInstance,
  onMarkerClick: (m) => {
    emit('marker-click', m);
    if (m.kind === 'alert') emit('alert-click', m.payload || {});
  },
  enableCluster: computed(() => props.enableCluster),
  showLabels: false,
  collapseSpiderOnSelect: computed(() => props.spiderfyCollapseOnSelect),
  onHover: onMarkerHover,
  disableClickPopup: true, // 告警图用悬浮卡片替代点击文字气泡
});

// —— 出现轨迹：序号圆点 + 连线，点击标点显示详情；人脸/车牌轨迹模式支持时间轴回放 ——
type TrajectoryPoint = FaceTrajectoryPoint | PlateTrajectoryPoint;

/** 轨迹点缩略图 URL（人脸/车牌轨迹点图片字段名不同） */
function trajectoryThumbUrl(p: TrajectoryPoint): string {
  const plate = p as PlateTrajectoryPoint;
  const face = p as FaceTrajectoryPoint;
  const raw = plate.plate_image_url || face.face_image_url;
  return raw ? resolveAlertImageDisplayUrl(raw) : '';
}

/** 模板中按车牌/人脸视角读取轨迹点字段（联合类型属性需显式收窄） */
const trajPointAsPlate = computed<PlateTrajectoryPoint | null>(() =>
  trajDetail.value ? (trajDetail.value.point as PlateTrajectoryPoint) : null,
);
const trajPointAsFace = computed<FaceTrajectoryPoint | null>(() =>
  trajDetail.value ? (trajDetail.value.point as FaceTrajectoryPoint) : null,
);

const trajSource = new VectorSource();
const trajLayer = new VectorLayer({ source: trajSource, zIndex: MAP_LAYER_ZINDEX.track + 5 });
let trajClickKey: EventsKey | null = null;
let trajLayerAdded = false;
const trajDetail = ref<{ step: number; point: TrajectoryPoint; imageUrl: string } | null>(null);

// 时间轴回放状态：-1 静态全览；>=0 回放到第 N 个点
const trajPlayIndex = ref(-1);
const trajPlaying = ref(false);
let trajTimer: ReturnType<typeof setInterval> | null = null;

const trajectoryPoints = computed(() => props.trajectory || []);

function trajPlayToggle() {
  if (trajPlaying.value) {
    trajStopPlay();
    return;
  }
  const list = trajectoryPoints.value;
  if (!list.length) return;
  if (trajPlayIndex.value >= list.length - 1) trajPlayIndex.value = -1;
  trajPlaying.value = true;
  trajTimer = setInterval(() => {
    const n = trajectoryPoints.value.length;
    if (trajPlayIndex.value >= n - 1) {
      trajStopPlay();
      return;
    }
    trajPlayIndex.value += 1;
  }, 1600);
}

function trajStopPlay() {
  trajPlaying.value = false;
  if (trajTimer) {
    clearInterval(trajTimer);
    trajTimer = null;
  }
}

function trajSeek(idx: number) {
  trajStopPlay();
  trajPlayIndex.value = idx;
}

/** 时间轴：当前进度百分比（静态全览=100%，回放/拖动=当前站比例） */
const playPercent = computed(() => {
  const n = trajectoryPoints.value.length;
  if (n <= 1) return '100%';
  const idx = trajPlayIndex.value < 0 ? n - 1 : Math.min(trajPlayIndex.value, n - 1);
  return `${(idx / (n - 1)) * 100}%`;
});

/** 时间轴刻度：第 i 站在轨道上的左侧位置 */
function tickLeft(i: number): string {
  const n = trajectoryPoints.value.length;
  if (n <= 1) return '0%';
  return `${(i / (n - 1)) * 100}%`;
}

function timeLabel(p?: TrajectoryPoint): string {
  return p?.time ? String(p.time).slice(11, 16) : '';
}

/** 时间轴进度条交互：点击/拖动定位 */
const trackRef = ref<HTMLElement | null>(null);
let trackDragging = false;

function onTrackDown(evt: PointerEvent) {
  const el = trackRef.value;
  if (!el) return;
  trackDragging = true;
  el.setPointerCapture(evt.pointerId);
  seekFromEvent(evt);
  const onMove = (e: PointerEvent) => seekFromEvent(e);
  const onUp = (e: PointerEvent) => {
    trackDragging = false;
    el.removeEventListener('pointermove', onMove);
    el.removeEventListener('pointerup', onUp);
    if (el.hasPointerCapture(e.pointerId)) el.releasePointerCapture(e.pointerId);
  };
  el.addEventListener('pointermove', onMove);
  el.addEventListener('pointerup', onUp);
}

function seekFromEvent(evt: PointerEvent) {
  const el = trackRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (evt.clientX - rect.left) / rect.width));
  const n = trajectoryPoints.value.length;
  const idx = Math.round(ratio * (n - 1));
  trajStopPlay();
  trajPlayIndex.value = idx;
}

// 回放/拖动时：详情卡片自动跟随当前点
watch(trajPlayIndex, (idx) => {
  if (idx < 0) return;
  const p = trajectoryPoints.value[idx];
  if (!p) return;
  trajDetail.value = {
    step: idx + 1,
    point: p,
    imageUrl: trajectoryThumbUrl(p),
  };
  drawTrajectory();
});

function ensureTrajLayer() {
  const m = mapInstance.value;
  if (!m || trajLayerAdded) return;
  m.addLayer(trajLayer);
  trajLayerAdded = true;
  trajClickKey = m.on('singleclick', (evt) => {
    if (!trajSource) return;
    const hit = m.forEachFeatureAtPixel(evt.pixel, (f) => f);
    if (hit?.get('trajPoint')) {
      const point = hit.get('trajPoint') as TrajectoryPoint;
      trajDetail.value = {
        step: hit.get('trajStep'),
        point,
        imageUrl: trajectoryThumbUrl(point),
      };
    } else {
      trajDetail.value = null;
    }
  });
}

function drawTrajectory() {
  const m = mapInstance.value;
  if (!m) return;
  ensureTrajLayer();
  trajSource.clear();
  const list = trajectoryPoints.value;
  if (!list.length) {
    trajDetail.value = null;
    return;
  }

  const reached = trajPlayIndex.value; // -1=全览
  const features: Feature[] = [];
  const coords = list.map((p) => fromLonLat([p.longitude, p.latitude]));

  // 分段连线 + 方向箭头（已到达段深蓝实线，未到达段浅灰虚线）
  for (let i = 0; i < list.length - 1; i++) {
    const segReached = reached < 0 || i < reached;
    const segColor = segReached ? '#0071e3' : '#c4d0ea';
    const line = new Feature({
      geometry: new LineString([coords[i], coords[i + 1]]),
    });
    line.setStyle(
      new Style({
        stroke: new Stroke({
          color: segColor,
          width: segReached ? 3.5 : 2.5,
          lineDash: segReached ? undefined : [4, 6],
        }),
      }),
    );
    features.push(line);
    // 段中点方向箭头
    const midX = (coords[i][0] + coords[i + 1][0]) / 2;
    const midY = (coords[i][1] + coords[i + 1][1]) / 2;
    const angle = Math.atan2(coords[i + 1][1] - coords[i][1], coords[i + 1][0] - coords[i][0]);
    const arrow = new Feature({ geometry: new Point([midX, midY]) });
    arrow.setStyle(
      new Style({
        image: new RegularShape({
          points: 3,
          radius: 7,
          fill: new Fill({ color: segColor }),
          rotation: angle,
        }),
      }),
    );
    features.push(arrow);
  }

  // 轨迹点：已到达=蓝实心+序号+时间标签；当前=橙色大点高亮；未到达=灰色小点
  list.forEach((p, i) => {
    const isReached = reached < 0 || i <= reached;
    const isCurrent = reached >= 0 && i === reached;
    const radius = isCurrent ? 18 : isReached ? 14 : 8;
    const color = isCurrent ? '#ff9500' : isReached ? '#0071e3' : '#b8c4dd';
    const feat = new Feature({ geometry: new Point(coords[i]) });
    feat.set('trajPoint', p);
    feat.set('trajStep', i + 1);
    const styles: Style[] = [
      new Style({
        image: new Circle({
          radius,
          fill: new Fill({ color }),
          stroke: new Stroke({ color: '#ffffff', width: isCurrent ? 3 : 2.5 }),
        }),
        text: isReached
          ? new Text({
              text: String(i + 1),
              font: 'bold 12px sans-serif',
              fill: new Fill({ color: '#ffffff' }),
            })
          : undefined,
      }),
    ];
    // 到达点上方标注时间（HH:MM）
    if (isReached && p.time) {
      styles.push(
        new Style({
          text: new Text({
            text: String(p.time).slice(11, 16),
            offsetY: -radius - 10,
            font: '11px sans-serif',
            fill: new Fill({ color: '#1d1d1f' }),
            stroke: new Stroke({ color: '#ffffff', width: 3 }),
          }),
        }),
      );
    }
    feat.setStyle(styles);
    features.push(feat);
  });
  trajSource.addFeatures(features);

  // 视野适配：静态全览或回放开始时 fit 一次，播放中保持视野稳定
  if (reached < 0 || reached === 0) {
    if (list.length > 1) {
      m.getView().fit(boundingExtent(coords), {
        padding: [90, 90, 90, 90],
        duration: 400,
        maxZoom: 17,
      });
    } else {
      m.getView().setCenter(coords[0]);
      m.getView().setZoom(16);
    }
  }
}

function clearTrajectory() {
  trajSource.clear();
  trajDetail.value = null;
}

function formatTrajSim(sim: unknown): string {
  if (sim == null || Number.isNaN(Number(sim))) return '-';
  return `${(Number(sim) * 100).toFixed(1)}%`;
}

function goTrajAlert(point: TrajectoryPoint) {
  router.push({ path: '/alert', query: { tab: 'events', task_name: point.task_name || '' } });
}

watch(
  () => props.trajectory,
  () => {
    // 新轨迹数据：重置回放状态后全览绘制
    trajStopPlay();
    trajPlayIndex.value = -1;
    drawTrajectory();
  },
  { deep: true },
);

// 悬浮提示：摄像头→告警卡片；聚合簇→数量/告警/操作提示。hover 打开、可悬停进卡片、移出延时关闭
const hoverCardEl = ref<HTMLElement | null>(null);
const hoverInfo = ref<MapHoverInfo | null>(null);
let hoverOverlay: Overlay | null = null;
let hideTimer: ReturnType<typeof setTimeout> | null = null;

const hoverCamera = computed<MapMarkerData | null>(() =>
  hoverInfo.value?.type === 'camera' ? hoverInfo.value.marker : null,
);
const hoverCluster = computed(() => (hoverInfo.value?.type === 'cluster' ? hoverInfo.value : null));
const hoverAlerts = computed<AlertMapItem[]>(() =>
  hoverCamera.value ? (alertData.alertsByDevice.value.get(hoverCamera.value.id) ?? []) : [],
);

function ensureHoverOverlay() {
  const m = mapInstance.value;
  if (!m || hoverOverlay || !hoverCardEl.value) return;
  hoverOverlay = new Overlay({
    element: hoverCardEl.value,
    positioning: 'bottom-center',
    offset: [0, -18],
    stopEvent: true,
  });
  m.addOverlay(hoverOverlay);
}

function clearHideTimer() {
  if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
}
function scheduleHideHover() {
  clearHideTimer();
  hideTimer = setTimeout(() => {
    hoverInfo.value = null;
    hoverOverlay?.setPosition(undefined);
  }, 160);
}
function onMarkerHover(info: MapHoverInfo | null, coord: number[] | null) {
  if (info && coord) {
    clearHideTimer();
    hoverInfo.value = info;
    ensureHoverOverlay();
    placeHoverCard(coord);
  } else {
    scheduleHideHover();
  }
}

/** 按摄像头在视口中的位置自动选边：靠顶翻到下方、靠左右改对齐，避免卡片被裁剪；间隙取小贴近标记 */
function placeHoverCard(coord: number[]) {
  if (!hoverOverlay) return;
  const m = mapInstance.value;
  const px = m?.getPixelFromCoordinate(coord);
  const size = m?.getSize();
  if (!px || !size) {
    hoverOverlay.setPositioning('bottom-center');
    hoverOverlay.setOffset([0, -12]);
    hoverOverlay.setPosition(coord);
    return;
  }
  const [w] = size;
  const CARD_W = 260;
  const CARD_H = 300;
  const vert = px[1] < CARD_H + 16 ? 'top' : 'bottom';
  const horiz = px[0] > w - CARD_W / 2 - 8 ? 'right' : px[0] < CARD_W / 2 + 8 ? 'left' : 'center';
  const positioning = vert === 'bottom'
    ? (horiz === 'right' ? 'bottom-right' : horiz === 'left' ? 'bottom-left' : 'bottom-center')
    : (horiz === 'right' ? 'top-right' : horiz === 'left' ? 'top-left' : 'top-center');
  hoverOverlay.setPositioning(positioning);
  hoverOverlay.setOffset([0, vert === 'bottom' ? -12 : 18]); // 上方留小间隙；下方避开图标
  hoverOverlay.setPosition(coord);
}

const heatEnabled = ref(props.showHeat);
const showLabel = ref(true);
const { offlineOnly, categoryFilter, apply: applyDisplayFilters } = useMapDisplayFilters();
const heat = useMapHeatmap({ map: mapInstance, enabled: heatEnabled });
const measure = useMapMeasure({ map: mapInstance });
const pulse = useMapPulse({ map: mapInstance });
const spatialFilterIds = ref<string[] | null>(null);
const spatial = useMapSpatialQuery({
  map: mapInstance,
  getPoints: () => markerList.value.map((m) => ({ id: m.id, lng: m.lng, lat: m.lat })),
  onResult: (ids) => {
    spatialFilterIds.value = ids;
    applyMarkers();
    if (ids) createMessage.success(`框选范围内 ${ids.length} 个点位`);
  },
});

const activeTool = computed<string | null>(() => measure.active.value ?? spatial.active.value ?? null);

const markerList = computed(() => {
  if (props.showCameras && props.showAlerts) return alertData.toCombinedMarkers();
  if (props.showAlerts) return alertData.toAlertedCameraMarkers();
  if (props.showCameras) return alertData.toCameraMarkers();
  return [];
});

function parseAlertTime(t?: string): number {
  if (!t) return 0;
  const d = dayjs(t);
  return d.isValid() ? d.valueOf() : 0;
}

/** 时间最新的一条告警（用于"定位最新告警"，无论是否在近期窗口内） */
const latestAlert = computed(() => {
  const list = alertData.alertsWithLocation.value;
  if (!list.length) return null;
  return list.reduce((a, b) => (parseAlertTime(b.time) > parseAlertTime(a.time) ? b : a));
});

/**
 * 用于脉冲高亮的"近期"告警：相对当前时间 30 分钟内。
 * nowTick 每分钟推进一次，驱动该集合随时间收缩——过期告警自动停止脉冲，
 * 集合空后脉冲层无要素、动画循环自然停止，不会永久空转占 CPU。
 */
const RECENT_WINDOW_MS = 30 * 60 * 1000;
const nowTick = ref(dayjs().valueOf());
let pulseTimer: ReturnType<typeof setInterval> | null = null;

const pulseAlerts = computed(() => {
  const now = nowTick.value;
  return alertData.alertsWithLocation.value.filter(
    (a) => parseAlertTime(a.time) > 0 && now - parseAlertTime(a.time) <= RECENT_WINDOW_MS,
  );
});

watch(
  pulseAlerts,
  (list) => pulse.setPoints(list.map((a) => ({ lng: Number(a.lng), lat: Number(a.lat) }))),
  { immediate: true },
);

pulseTimer = setInterval(() => { nowTick.value = dayjs().valueOf(); }, 60 * 1000);
onBeforeUnmount(() => {
  if (pulseTimer) { clearInterval(pulseTimer); pulseTimer = null; }
  trajStopPlay();
  clearHideTimer();
});

function displayMarkers(): MapMarkerData[] {
  let list = markerList.value;
  const ids = spatialFilterIds.value;
  if (ids) {
    const idSet = new Set(ids); // includes() 在 filter 内是 O(n²)，用 Set 降到 O(n)
    list = list.filter((m) => idSet.has(m.id));
  }
  return applyDisplayFilters(list);
}

const offlineCount = computed(
  () => alertData.deviceData.devices.value.filter((d) => d.online === false).length,
);

watch([offlineOnly, categoryFilter], () => markers.setMarkers(displayMarkers()), { deep: true });

function applyMarkers() {
  markers.setMarkers(displayMarkers());
  // 热力点由 watch(heatEnabled) 驱动（仅热力开启时才重建要素，避免隐藏时空跑）
  // 脉冲点由 watch(pulseAlerts) 驱动（随时间收缩），此处无需重复设置
}

// —— 地图多模式（相互独立）：device=设备/告警视图（不显示轨迹）；face/plate=纯轨迹视图 ——
const isTrajMode = computed(() => props.mapMode === 'face' || props.mapMode === 'plate');

watch(
  () => props.mapMode,
  (mode) => {
    if (mode === 'face' || mode === 'plate') {
      // 轨迹模式：隐藏设备/告警标记与附加图层，绘制轨迹 + 时间轴
      markers.setMarkers([]);
      if (heatEnabled.value) heatEnabled.value = false;
      if (trajectoryPoints.value.length) {
        drawTrajectory();
      }
    } else {
      // 设备模式：恢复设备/告警标记；轨迹线完全清除（各模式互不叠加）
      applyMarkers();
      trajSource.clear();
      trajDetail.value = null;
      trajStopPlay();
      trajPlayIndex.value = -1;
    }
  },
  { immediate: true },
);

// 仅在热力层开启时喂点；告警集合变化时若已开启则刷新
watch(
  [heatEnabled, () => alertData.alertsWithLocation.value],
  () => {
    if (!heatEnabled.value) return;
    heat.setPoints(
      alertData.alertsWithLocation.value.map((a) => ({ lng: Number(a.lng), lat: Number(a.lat) })),
    );
  },
  { immediate: true },
);

async function refresh() {
  await alertData.loadAlerts(props.query);
  spatialFilterIds.value = null; // 重新加载数据时清除框选过滤
  applyMarkers();
  markers.fitToMarkers();
  await nextTick();
  mapRef.value?.tryInitMap?.();
  mapRef.value?.updateSize?.();
  requestAnimationFrame(() => {
    mapRef.value?.tryInitMap?.();
    mapRef.value?.updateSize?.();
  });
}

async function onMapReady() {
  await nextTick();
  mapRef.value?.updateSize?.();
  void refresh();
  drawTrajectory(); // 地图就绪后补绘人物轨迹（可能早于地图 ready 传入）
  requestAnimationFrame(() => mapRef.value?.updateSize?.());
  window.setTimeout(() => mapRef.value?.updateSize?.(), 200);
  window.setTimeout(() => mapRef.value?.updateSize?.(), 500);
}

function updateMapSize() {
  mapRef.value?.tryInitMap?.();
  mapRef.value?.updateSize?.();
}

watch(baseMapType, (type) => {
  mapRef.value?.switchBaseMap(type);
});

watch(showLabel, (v) => {
  mapRef.value?.setLabelVisible?.(v);
});

// 数据加载由父级(AlertMapPanel)通过 refresh() 显式驱动，便于「相同查询强制刷新」
// 且避免与显式 refresh 重复触发；故不再监听 props.query 自动加载。
watch(() => [props.showCameras, props.showAlerts], () => {
  // 切换图层会改变 markerList，旧框选 id 可能已不在新集合中导致空屏，故先清掉框选
  spatial.clear();
  applyMarkers();
});

function flyTo(lng: number, lat: number, zoom = 16) {
  mapRef.value?.flyTo(lng, lat, zoom);
}

function handleFitAll() {
  markers.fitToMarkers();
}

function handleReset() {
  mapRef.value?.resetView?.();
}

function handleSearchSelect(p: { lng: number; lat: number }) {
  mapRef.value?.flyTo(p.lng, p.lat, 16);
}

function handleLocateLatest() {
  const latest = latestAlert.value;
  if (!latest || latest.lng == null || latest.lat == null) {
    createMessage.info('暂无可定位的告警');
    return;
  }
  mapRef.value?.flyTo(Number(latest.lng), Number(latest.lat), 17);
}

function handleTool(key: string) {
  switch (key) {
    case 'measure-line': measure.start('line'); break;
    case 'measure-area': measure.start('area'); break;
    case 'select-circle': spatial.start('circle'); break;
    case 'select-rect': spatial.start('rect'); break;
    case 'select-polygon': spatial.start('polygon'); break;
    case 'clear':
      measure.clear();
      spatial.clear();
      break;
    default: break;
  }
}

defineExpose({ refresh, alerts: alertData.alertsWithLocation, flyTo, updateMapSize, alertData, clearTrajectory });
</script>

<template>
  <div
    class="alert-device-map"
    :class="{ 'alert-device-map--embedded': embedded }"
    :style="embedded ? { height } : undefined"
  >
    <!-- 悬浮提示（OL Overlay 会把此元素移入地图覆盖层并定位）：摄像头→告警卡片，聚合簇→数量+操作提示 -->
    <div ref="hoverCardEl" class="alert-device-map__hovercard" @mouseenter="clearHideTimer" @mouseleave="scheduleHideHover">
      <CameraAlertCard
        v-if="hoverCamera"
        :name="hoverCamera.title"
        :online="hoverCamera.online"
        :alerts="hoverAlerts"
      />
      <div v-else-if="hoverCluster" class="cluster-tip">
        <div class="cluster-tip__line">
          <b>{{ hoverCluster.count }}</b> 台摄像头
          <template v-if="hoverCluster.alertCount">
            · <span class="cluster-tip__alert">{{ hoverCluster.alertCount }}</span> 条告警
          </template>
        </div>
        <div class="cluster-tip__hint">
          {{ hoverCluster.canZoom ? '点击放大查看' : `点击展开 ${hoverCluster.count} 个点位` }}
        </div>
      </div>
    </div>

    <!-- 出现轨迹：点击标点的详情卡片（人脸/车牌通用） -->
    <div v-if="trajDetail" class="alert-device-map__traj-card">
      <div class="traj-card__head">
        <span class="traj-card__title">
          <template v-if="trajectoryTitle">{{ trajectoryTitle }} · </template>第 {{ trajDetail.step }} 站
        </span>
        <span class="traj-card__time">{{ trajDetail.point.time }}</span>
        <button type="button" class="traj-card__close" @click="trajDetail = null">
          <Icon icon="ant-design:close-outlined" :size="12" />
        </button>
      </div>
      <div class="traj-card__body">
        <div class="traj-card__thumb">
          <img
            v-if="trajDetail.imageUrl"
            :src="trajDetail.imageUrl"
            :alt="props.mapMode === 'plate' ? '车牌' : '人脸'"
            @error="trajDetail.imageUrl = ''"
          />
          <Icon
            v-else
            :icon="props.mapMode === 'plate' ? 'ant-design:car-outlined' : 'ant-design:user-outlined'"
            :size="18"
          />
        </div>
        <div class="traj-card__facts">
          <div class="traj-card__row">
            <span class="label">设备</span>
            <span class="value">{{ trajDetail.point.device_name }}</span>
          </div>
          <div class="traj-card__row">
            <span class="label">地点</span>
            <span class="value">{{ trajDetail.point.address || '-' }}</span>
          </div>
          <template v-if="props.mapMode === 'plate'">
            <div class="traj-card__row">
              <span class="label">置信度</span>
              <span class="value sim">{{ formatTrajSim(trajPointAsPlate?.detect_conf) }}</span>
            </div>
            <div v-if="trajPointAsPlate?.plate_no" class="traj-card__row">
              <span class="label">车牌</span>
              <span class="value">{{ trajPointAsPlate?.plate_no }}</span>
            </div>
          </template>
          <template v-else>
            <div class="traj-card__row">
              <span class="label">相似度</span>
              <span class="value sim">{{ formatTrajSim(trajPointAsFace?.similarity) }}</span>
            </div>
          </template>
          <div v-if="trajDetail.point.library_name" class="traj-card__row">
            <span class="label">{{ props.mapMode === 'plate' ? '车牌库' : '人脸库' }}</span>
            <span class="value">{{ trajDetail.point.library_name }}</span>
          </div>
        </div>
      </div>
      <div v-if="trajDetail.point.alert_id" class="traj-card__foot">
        <Button size="small" type="primary" ghost @click="goTrajAlert(trajDetail.point)">
          查看告警
        </Button>
      </div>
    </div>

    <Spin
      :spinning="alertData.loading.value"
      :wrapper-class-name="embedded ? 'alert-device-map__spin' : undefined"
    >
      <a-card
        v-if="!embedded"
        :bordered="false"
        :body-style="cardBodyStyle"
        class="alert-device-map__card"
      >
        <BasicTiandituMap ref="mapRef" :show-toolbar="false" show-overview @ready="onMapReady">
          <AlertMapFloatLayer
            v-if="!isTrajMode"
            v-model:base-map-type="baseMapType"
            v-model:show-label="showLabel"
            v-model:show-heat="heatEnabled"
            v-model:offline-only="offlineOnly"
            v-model:category-filter="categoryFilter"
            :loading="alertData.loading.value"
            :camera-count="alertData.deviceData.devices.value.length"
            :alert-count="alertData.alertsWithLocation.value.length"
            :offline-count="offlineCount"
            :map="mapInstance"
            :show-heat-legend="heatEnabled"
            :active-tool="activeTool"
            @refresh="refresh"
            @fit="handleFitAll"
            @reset="handleReset"
            @search="handleSearchSelect"
            @locate-latest="handleLocateLatest"
            @tool="handleTool"
          />
        </BasicTiandituMap>
      </a-card>
      <div v-else class="alert-device-map__map" :style="{ height }">
        <BasicTiandituMap ref="mapRef" :show-toolbar="false" show-overview @ready="onMapReady">
          <AlertMapFloatLayer
            v-if="!isTrajMode"
            v-model:base-map-type="baseMapType"
            v-model:show-label="showLabel"
            v-model:show-heat="heatEnabled"
            v-model:offline-only="offlineOnly"
            v-model:category-filter="categoryFilter"
            :loading="alertData.loading.value"
            :camera-count="alertData.deviceData.devices.value.length"
            :alert-count="alertData.alertsWithLocation.value.length"
            :offline-count="offlineCount"
            :map="mapInstance"
            :show-heat-legend="heatEnabled"
            :active-tool="activeTool"
            @refresh="refresh"
            @fit="handleFitAll"
            @reset="handleReset"
            @search="handleSearchSelect"
            @locate-latest="handleLocateLatest"
            @tool="handleTool"
          />
        </BasicTiandituMap>
      </div>
    </Spin>

    <!-- 人脸时空模式：轨迹回放时间轴（底部全宽进度条 + 时间刻度 + 当前站信息） -->
    <div
      v-if="isTrajMode && trajectoryPoints.length > 1"
      class="traj-timeline"
    >
      <button
        type="button"
        class="traj-timeline__play"
        :title="trajPlaying ? '暂停回放' : '播放轨迹回放'"
        @click="trajPlayToggle"
      >
        <Icon :icon="trajPlaying ? 'ant-design:pause-filled' : 'ant-design:caret-right-filled'" :size="20" />
      </button>
      <div class="traj-timeline__main">
        <div class="traj-timeline__ticks">
          <span
            v-for="(p, i) in trajectoryPoints"
            :key="i"
            class="traj-timeline__tick"
            :class="{ 'traj-timeline__tick--active': trajPlayIndex >= 0 && i === trajPlayIndex }"
            :style="{ left: tickLeft(i) }"
            @click="trajSeek(i)"
          >
            {{ timeLabel(p) }}
          </span>
        </div>
        <div
          ref="trackRef"
          class="traj-timeline__track"
          @pointerdown="onTrackDown"
        >
          <div class="traj-timeline__fill" :style="{ width: playPercent }" />
          <div class="traj-timeline__thumb" :style="{ left: playPercent }" />
        </div>
      </div>
      <div class="traj-timeline__info">
        <template v-if="trajPlayIndex >= 0 && trajectoryPoints[trajPlayIndex]">
          <span class="traj-timeline__step">
            第 {{ trajPlayIndex + 1 }}/{{ trajectoryPoints.length }} 站
          </span>
          <span class="traj-timeline__time">{{ timeLabel(trajectoryPoints[trajPlayIndex]) }}</span>
          <span class="traj-timeline__device">{{ trajectoryPoints[trajPlayIndex].device_name }}</span>
        </template>
        <template v-else>
          <span class="traj-timeline__hint">{{ trajectoryPoints.length }} 个出现点 · 点击播放，按时间顺序回顾移动轨迹</span>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
// 人脸时空模式：底部轨迹回放时间轴（大进度条 + 时间刻度 + 当前站信息）
.traj-timeline {
  position: absolute;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 18px;
  width: min(920px, calc(100% - 48px));
  padding: 16px 22px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  border: 1px solid #e4e9f2;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.22);

  // 播放/暂停大圆按钮
  &__play {
    flex: 0 0 48px;
    width: 48px;
    height: 48px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 50%;
    background: #266cfb;
    color: #fff;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(38, 108, 251, 0.4);
    transition: transform 0.15s, box-shadow 0.15s;

    &:hover {
      transform: scale(1.06);
      box-shadow: 0 6px 18px rgba(38, 108, 251, 0.5);
    }

    &:active {
      transform: scale(0.96);
    }
  }

  // 主区：刻度 + 进度条
  &__main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  // 时间刻度（轨道上方，各站时间点）
  &__ticks {
    position: relative;
    height: 16px;

    .traj-timeline__tick {
      position: absolute;
      top: 0;
      transform: translateX(-50%);
      font-size: 11px;
      line-height: 16px;
      color: #9aa4b8;
      white-space: nowrap;
      cursor: pointer;
      user-select: none;
      transition: color 0.2s;

      &:first-child {
        transform: translateX(0);
      }

      &:last-child {
        transform: translateX(-100%);
      }

      &:hover {
        color: #266cfb;
      }

      &--active {
        color: #266cfb;
        font-weight: 700;
      }
    }
  }

  // 进度条轨道
  &__track {
    position: relative;
    height: 10px;
    border-radius: 5px;
    background: #e8ecf4;
    cursor: pointer;
    touch-action: none;
  }

  // 已播放填充
  &__fill {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    border-radius: 5px;
    background: linear-gradient(90deg, #266cfb, #5b8ff9);
    pointer-events: none;
  }

  // 滑块
  &__thumb {
    position: absolute;
    top: 50%;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #fff;
    border: 3px solid #266cfb;
    box-shadow: 0 2px 8px rgba(38, 108, 251, 0.35);
    transform: translate(-50%, -50%);
    pointer-events: none;
  }

  // 当前站信息
  &__info {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.85);
    white-space: nowrap;
    overflow: hidden;

    .traj-timeline__step {
      color: #266cfb;
      font-weight: 700;
    }

    .traj-timeline__time {
      font-variant-numeric: tabular-nums;
      font-weight: 600;
    }

    .traj-timeline__device {
      color: rgba(0, 0, 0, 0.55);
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .traj-timeline__hint {
      color: #9aa4b8;
    }
  }
}

// 人物出现轨迹：点击标点的详情卡片（地图右下角浮层）
.alert-device-map__traj-card {
  position: absolute;
  right: 16px;
  bottom: 16px;
  z-index: 20;
  width: 300px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.18);
  border: 1px solid #e8ecf4;
  overflow: hidden;
  pointer-events: auto;

  .traj-card__head {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: #f0f7ff;
    border-bottom: 1px solid #e8ecf4;

    .traj-card__title {
      font-size: 13px;
      font-weight: 600;
      color: #266cfb;
    }

    .traj-card__time {
      flex: 1;
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
    }

    .traj-card__close {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      padding: 0;
      border: none;
      border-radius: 4px;
      background: transparent;
      color: rgba(0, 0, 0, 0.35);
      cursor: pointer;

      &:hover {
        background: rgba(0, 0, 0, 0.06);
      }
    }
  }

  .traj-card__body {
    display: flex;
    gap: 12px;
    padding: 12px 14px;

    .traj-card__thumb {
      width: 56px;
      height: 56px;
      flex: 0 0 56px;
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f7fa;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .traj-card__facts {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 5px;

      .traj-card__row {
        display: flex;
        gap: 8px;
        font-size: 12px;
        line-height: 1.5;

        .label {
          flex: 0 0 44px;
          color: rgba(0, 0, 0, 0.45);
        }

        .value {
          color: rgba(0, 0, 0, 0.85);
          word-break: break-all;
        }

        .sim {
          color: #266cfb;
          font-weight: 600;
        }
      }
    }
  }

  .traj-card__foot {
    padding: 8px 14px 10px;
    border-top: 1px solid #f0f2f7;
    display: flex;
    justify-content: flex-end;
  }
}

.cluster-tip {
  padding: 8px 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e8ecf4;
  box-shadow: 0 8px 28px rgb(15 23 42 / 16%);
  pointer-events: auto;
  white-space: nowrap;

  &__line {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.82);

    b { font-size: 15px; color: #266cfb; }
  }

  &__alert {
    font-weight: 700;
    color: #ff4d4f;
  }

  &__hint {
    margin-top: 3px;
    font-size: 11px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.alert-device-map {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgb(0 0 0 / 4%);

  &--embedded {
    width: 100%;
    height: 100%;
    min-height: 0;
    border-radius: 0;
    box-shadow: none;
    background: transparent;
  }

  &__map {
    flex: 1;
    width: 100%;
    min-width: 0;
    min-height: 0;
    padding: 0;
    background: #e8ebf2;
    position: relative;
    overflow: hidden;

    :deep(.basic-tianditu-map) {
      position: absolute;
      inset: 0;
      width: 100%;
      height: auto;
      min-height: 0;
      border-radius: 0;
    }
  }

  &__card:deep(.ant-card) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  &__card:deep(.ant-card-body) {
    flex: 1;
    min-height: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  &--embedded :deep(.alert-device-map__spin),
  &--embedded :deep(.ant-spin-nested-loading),
  &--embedded :deep(.ant-spin-container) {
    flex: 1;
    min-height: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :deep(.ant-spin-nested-loading),
  :deep(.ant-spin-container) {
    flex: 1;
    min-height: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  &--embedded :deep(.basic-tianditu-map) {
    position: absolute;
    inset: 0;
    width: 100%;
    height: auto;
    min-height: 0;
  }

  :deep(.basic-tianditu-map) {
    flex: 1;
    width: 100%;
    min-height: 0;
    height: 100%;
  }

  &--embedded :deep(.basic-tianditu-map__canvas) {
    width: 100%;
    height: 100%;
  }
}
</style>
