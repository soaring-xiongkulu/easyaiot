<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { DatePicker } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { AlertDeviceMap } from '@/components/TiandituMap';
import CameraInlinePreview from '@/components/TiandituMap/src/components/CameraInlinePreview.vue';
import CameraPtzPad from '@/components/TiandituMap/src/components/CameraPtzPad.vue';
import type { AlertMapQuery } from '@/components/TiandituMap';
import type { MapMarkerData } from '@/components/TiandituMap';
import { MapLayerSwitcher } from '@/components/MapLayerSwitcher';
import { getAlertMapFilterFormConfig } from '@/views/alert/Data';
import { formatAlertEvent, formatAlertListTitle } from '@/views/alert/alertDisplay';
import { getFaceTrajectory, type FaceTrajectoryPoint } from '@/api/device/face_library';
import { getPlateTrajectory, type PlateTrajectoryPoint } from '@/api/device/plate_library';
import { canSetDeviceLocation, formatLocationSummary } from '@/views/camera/utils/deviceLocation';
import {
  normalizeAlertQueryParams,
  snapshotAlertFilters,
  toAlertMapQuery,
} from '@/views/alert/utils/alertQueryParams';

defineOptions({ name: 'AlertMapPanel' });

const emit = defineEmits<{
  viewImage: [record: Record<string, unknown>];
  viewVideo: [record: Record<string, unknown>];
  setLocation: [device: Record<string, unknown>];
  play: [device: Record<string, unknown>];
  view: [device: Record<string, unknown>];
  edit: [device: Record<string, unknown>];
  statsChange: [payload: { located: number; unlocated: number }];
}>();

const TIME_RANGE_KEY = '[begin_datetime, end_datetime]';

interface FilterChip {
  key: string;
  label: string;
}

const router = useRouter();
const mapRef = ref<InstanceType<typeof AlertDeviceMap> | null>(null);
const mapQuery = ref<AlertMapQuery>({ pageNo: 1, pageSize: 500 });
const selectedAlertId = ref<string | null>(null);
const selectedCameraId = ref<string | null>(null);
const previewOpen = ref(false);
const ptzOpen = ref(false);
const showCameras = ref(true);
const showAlerts = ref(true);
const appliedFilters = ref<Record<string, unknown>>({});

// —— 地图多模式：device=设备/告警核心视图；face=人脸时空轨迹视图；plate=车牌轨迹视图（相互独立） ——
const mapMode = ref<'device' | 'face' | 'plate'>('device');

function switchMapMode(mode: 'device' | 'face' | 'plate') {
  if (mapMode.value === mode) return;
  mapMode.value = mode;
  if (mode === 'device') {
    // 回到设备视图：清除轨迹 URL 参数，恢复侧栏筛选
    const q = { ...router.currentRoute.value.query };
    delete q.trajectory_person;
    delete q.trajectory_plate;
    delete q.trajectory_date;
    router.replace({ query: q });
  }
}

// —— 出现轨迹：从 URL 参数进入（trajectory_person=人脸 / trajectory_plate=车牌），加载并叠加到地图 ——
const trajectoryPerson = ref('');
const trajectoryPlate = ref('');
const trajectoryDate = ref('');
const trajectoryPoints = ref<Array<FaceTrajectoryPoint | PlateTrajectoryPoint>>([]);
const trajectoryLoading = ref(false);

/** 轨迹主体标题：人员姓名或车牌号 */
const trajectoryTitle = computed(() => trajectoryPerson.value || trajectoryPlate.value);

async function loadTrajectoryFromQuery() {
  const q = router.currentRoute.value.query;
  const person = String(q.trajectory_person || '').trim();
  const plate = String(q.trajectory_plate || '').trim();
  trajectoryPerson.value = person;
  trajectoryPlate.value = plate;
  trajectoryDate.value = String(q.trajectory_date || '').trim();
  // 带轨迹参数进入 → 直接轨迹视图；无参数 → 默认设备视图
  mapMode.value = person ? 'face' : plate ? 'plate' : 'device';
  if (!person && !plate) {
    trajectoryPoints.value = [];
    return;
  }
  trajectoryLoading.value = true;
  try {
    const date = trajectoryDate.value || new Date().toISOString().slice(0, 10);
    let points: Array<FaceTrajectoryPoint | PlateTrajectoryPoint> = [];
    if (person) {
      const res = (await getFaceTrajectory({
        person_name: person,
        date,
      })) as any;
      const data = res?.data ?? res;
      points = Array.isArray(data?.points) ? data.points : [];
    } else {
      const res = (await getPlateTrajectory({
        plate_no: plate,
        date,
      })) as any;
      const data = res?.data ?? res;
      points = Array.isArray(data?.points) ? data.points : [];
    }
    trajectoryPoints.value = points;
    trajectoryDate.value = date;
  } catch {
    trajectoryPoints.value = [];
  } finally {
    trajectoryLoading.value = false;
  }
}

function clearTrajectoryQuery() {
  trajectoryPerson.value = '';
  trajectoryPlate.value = '';
  trajectoryDate.value = '';
  trajectoryPoints.value = [];
  mapMode.value = 'device';
  mapRef.value?.clearTrajectory?.();
  router.replace({
    query: {
      ...router.currentRoute.value.query,
      trajectory_person: undefined,
      trajectory_plate: undefined,
      trajectory_date: undefined,
    },
  });
}

/** 轨迹模式：切换查看日期（更新 URL 参数并重新加载轨迹） */
function changeTrajectoryDate(dateStr: string | string[]) {
  const d = Array.isArray(dateStr) ? dateStr[0] : dateStr;
  if (!d || (!trajectoryPerson.value && !trajectoryPlate.value)) return;
  const query: Record<string, unknown> = {
    ...router.currentRoute.value.query,
    trajectory_date: d,
  };
  if (trajectoryPerson.value) {
    query.trajectory_person = trajectoryPerson.value;
    delete query.trajectory_plate;
  } else {
    query.trajectory_plate = trajectoryPlate.value;
    delete query.trajectory_person;
  }
  router.replace({ query });
}

watch(
  () => [
    router.currentRoute.value.query.trajectory_person,
    router.currentRoute.value.query.trajectory_plate,
    router.currentRoute.value.query.trajectory_date,
  ],
  () => loadTrajectoryFromQuery(),
);

// 切换选中摄像头时关闭内联预览/云台，避免操作到上一台设备
watch(selectedCameraId, () => {
  previewOpen.value = false;
  ptzOpen.value = false;
});

// 复用地图组件内部的 useAlertMapData 实例（地图通过 defineExpose 暴露），
// 避免侧栏再单独拉取一份告警+摄像头数据造成重复请求
const mapData = computed(() => mapRef.value?.alertData ?? null);

const locatedCount = computed(() => mapData.value?.alertsWithLocation.value.length ?? 0);
const unlocatedCount = computed(() =>
  mapData.value ? mapData.value.alerts.value.length - mapData.value.alertsWithLocation.value.length : 0,
);
const dataLoading = computed(() => mapData.value?.loading.value ?? false);

watch(
  [locatedCount, unlocatedCount],
  () => {
    emit('statsChange', { located: locatedCount.value, unlocated: unlocatedCount.value });
  },
  { immediate: true },
);

const selectedAlert = computed(() => {
  if (!selectedAlertId.value) return null;
  return mapData.value?.alertsWithLocation.value.find((a) => String(a.id) === selectedAlertId.value) ?? null;
});

const selectedCamera = computed(() => {
  if (!selectedCameraId.value) return null;
  return mapData.value?.deviceData.findById(selectedCameraId.value) ?? null;
});

// 可转动相机才显示云台：GB28181 ptzType ∈ {1球机,4遥控枪机,5遥控半球} 或具备 PTZ 转动能力
const canPtzSelectedCamera = computed(() => {
  const cam = selectedCamera.value;
  if (!cam) return false;
  return cam.ptz_type === 1 || cam.ptz_type === 4 || cam.ptz_type === 5 || cam.support_move === true;
});

const linkedCamera = computed(() => {
  const alert = selectedAlert.value;
  if (!alert?.device_id) return null;
  return mapData.value?.deviceData.findById(String(alert.device_id)) ?? null;
});

const canSetSelectedCameraLocation = computed(() =>
  selectedCamera.value ? canSetDeviceLocation({ id: selectedCamera.value.id }) : false,
);

const canSetLinkedCameraLocation = computed(() =>
  linkedCamera.value ? canSetDeviceLocation({ id: linkedCamera.value.id }) : false,
);

const hasSelection = computed(() => !!(selectedAlert.value || selectedCamera.value));

const filterChips = computed<FilterChip[]>(() => {
  const f = appliedFilters.value;
  const chips: FilterChip[] = [];
  if (f.begin_datetime || f.end_datetime) {
    chips.push({
      key: 'time',
      label: `${f.begin_datetime || '…'} ~ ${f.end_datetime || '…'}`,
    });
  }
  if (f.task_name) {
    chips.push({ key: 'task_name', label: `任务 ${f.task_name}` });
  }
  if (f.device_id) {
    chips.push({ key: 'device_id', label: `摄像头 ${f.device_id}` });
  }
  if (f.event) {
    chips.push({ key: 'event', label: formatAlertEvent(f.event as string) });
  }
  if (f.business_tags) {
    chips.push({ key: 'business_tags', label: `标签 ${f.business_tags}` });
  }
  return chips;
});

const [registerForm, { validate, setFieldsValue, resetFields, getFieldsValue }] = useForm(
  getAlertMapFilterFormConfig(),
);

async function loadData() {
  // 数据加载只走地图组件（其 loadAlerts 已做并发去重），侧栏统计响应式读取同一实例
  await mapRef.value?.refresh();
  await nextTick();
  mapRef.value?.updateMapSize?.();
}

function resizeMap() {
  mapRef.value?.updateMapSize?.();
  requestAnimationFrame(() => mapRef.value?.updateMapSize?.());
  requestAnimationFrame(() => mapRef.value?.updateMapSize?.());
}

async function handleSearch() {
  let formData: Record<string, unknown>;
  try {
    formData = await validate();
  } catch (error: any) {
    // 面板刚挂载表单未注册（tab 切换瞬间）时 validate 会抛
    // "The form instance has not been obtained"，此时跳过校验直接按现有条件查询
    if (error?.outOfDate && (!error?.errorFields || error.errorFields.length === 0)) {
      formData = getFieldsValue();
    } else if (String(error?.message || '').includes('form instance has not been obtained')) {
      formData = getFieldsValue();
    } else {
      throw error;
    }
  }
  const processed = normalizeAlertQueryParams(
    formData as Record<string, unknown>,
    router.currentRoute.value.query.task_name as string | undefined,
  );
  appliedFilters.value = snapshotAlertFilters(processed);
  mapQuery.value = toAlertMapQuery(appliedFilters.value);
  selectedAlertId.value = null;
  selectedCameraId.value = null;
  await loadData();
}

async function handleReset() {
  await resetFields();
  appliedFilters.value = {};
  mapQuery.value = { pageNo: 1, pageSize: 500 };
  selectedAlertId.value = null;
  selectedCameraId.value = null;
  await loadData();
}

async function removeFilterChip(key: string) {
  const fields = { ...(getFieldsValue() as Record<string, unknown>) };
  switch (key) {
    case 'time':
      fields[TIME_RANGE_KEY] = null;
      break;
    case 'task_name':
      fields.task_name = '';
      break;
    case 'device_id':
      fields.device_id = '';
      break;
    case 'event':
      fields.event = null;
      break;
    case 'business_tags':
      fields.business_tags = undefined;
      break;
    default:
      return;
  }
  await setFieldsValue(fields);
  await handleSearch();
}

function clearSelection() {
  selectedAlertId.value = null;
  selectedCameraId.value = null;
}

function onMarkerClick(marker: MapMarkerData) {
  if (marker.kind === 'alert') {
    selectedAlertId.value = String(marker.id);
    selectedCameraId.value = null;
    return;
  }
  if (marker.kind === 'camera') {
    // 仅选中、打开右侧详情；不再自动放大/平移地图（点击即猛缩放体验不佳）
    selectedCameraId.value = marker.id;
    selectedAlertId.value = null;
  }
}

function onAlertClick(payload: Record<string, unknown>) {
  selectedAlertId.value = String(payload.id ?? '');
  selectedCameraId.value = null;
}

function handleAlertAction(alert: Record<string, unknown>, action: 'image' | 'video') {
  if (action === 'image') emit('viewImage', alert);
  else emit('viewVideo', alert);
}

function buildCameraPayload(cam: NonNullable<typeof selectedCamera.value>) {
  return {
    id: cam.id,
    name: cam.name,
    device_kind: (cam as { device_kind?: string }).device_kind,
    longitude: cam.lng,
    latitude: cam.lat,
    altitude: cam.altitude,
    address: cam.address,
    heading: cam.heading,
    location_source: cam.location_source,
  };
}

function handleSetLocation(cam = selectedCamera.value) {
  if (!cam) return;
  emit('setLocation', buildCameraPayload(cam));
}

function handlePlay() {
  const cam = selectedCamera.value;
  if (cam) emit('play', buildCameraPayload(cam));
}

function handleView() {
  const cam = selectedCamera.value;
  if (cam) emit('view', buildCameraPayload(cam));
}

function handleEdit() {
  const cam = selectedCamera.value;
  if (cam) emit('edit', buildCameraPayload(cam));
}

async function applyFilters(params: Record<string, unknown>) {
  const fields: Record<string, unknown> = { ...params };
  if (fields.begin_datetime || fields.end_datetime) {
    fields[TIME_RANGE_KEY] = [
      fields.begin_datetime ?? null,
      fields.end_datetime ?? null,
    ];
    delete fields.begin_datetime;
    delete fields.end_datetime;
  }
  await setFieldsValue(fields);
  await handleSearch();
}

async function init() {
  const taskName = router.currentRoute.value.query.task_name;
  if (taskName) {
    await setFieldsValue({ task_name: taskName });
  }
  await loadTrajectoryFromQuery();
  await handleSearch();
}

defineExpose({ refresh: loadData, resizeMap, applyFilters, init });
</script>

<template>
  <div class="geo-loc">
    <div class="geo-loc__workspace">
      <section class="geo-loc__map-area" aria-label="告警地图">
        <AlertDeviceMap
          ref="mapRef"
          embedded
          :query="mapQuery"
          :show-cameras="showCameras"
          :show-alerts="showAlerts"
          :map-mode="mapMode"
          :trajectory="trajectoryPoints"
          :trajectory-title="trajectoryTitle"
          height="100%"
          @marker-click="onMarkerClick"
          @alert-click="onAlertClick"
        />
        <!-- 地图模式切换：设备视图 / 人脸轨迹 / 车牌轨迹（设备视图在右侧，轨迹视图在左侧） -->
        <div
          class="map-mode-switch"
          :class="{ 'map-mode-switch--left': mapMode !== 'device' }"
        >
          <button
            type="button"
            class="map-mode-switch__btn"
            :class="{ 'map-mode-switch__btn--active': mapMode === 'device' }"
            @click="switchMapMode('device')"
          >
            <Icon icon="ant-design:video-camera-outlined" />
            设备视图
          </button>
          <button
            type="button"
            class="map-mode-switch__btn"
            :class="{ 'map-mode-switch__btn--active': mapMode === 'face' }"
            @click="switchMapMode('face')"
          >
            <Icon icon="icon-park-outline:map-draw" />
            人脸轨迹
          </button>
          <button
            type="button"
            class="map-mode-switch__btn"
            :class="{ 'map-mode-switch__btn--active': mapMode === 'plate' }"
            @click="switchMapMode('plate')"
          >
            <Icon icon="ant-design:car-outlined" />
            车牌轨迹
          </button>
        </div>
        <!-- 轨迹工具栏（仅轨迹视图显示；设备视图与轨迹完全独立） -->
        <div v-if="(mapMode === 'face' || mapMode === 'plate') && trajectoryTitle" class="traj-banner">
          <Icon icon="icon-park-outline:map-draw" class="traj-banner__icon" />
          <span class="traj-banner__text">
            {{ mapMode === 'plate' ? '车牌轨迹' : '人物轨迹' }}：
            <b>{{ trajectoryTitle }}</b>
            <DatePicker
              class="traj-banner__date"
              :value="trajectoryDate"
              size="small"
              allow-clear
              @change="changeTrajectoryDate"
            />
            <template v-if="trajectoryLoading">（加载中…）</template>
            <template v-else>（{{ trajectoryPoints.length }} 个出现点，点击标点查看详情）</template>
          </span>
          <Button type="link" size="small" class="traj-banner__clear" @click="clearTrajectoryQuery">
            清除
          </Button>
        </div>
        <!-- 轨迹视图空态：无轨迹数据时提示进入方式 -->
        <div v-if="(mapMode === 'face' || mapMode === 'plate') && !trajectoryPoints.length" class="traj-empty">
          <Icon icon="icon-park-outline:map-draw" :size="40" />
          <p class="traj-empty__title">暂无轨迹数据</p>
          <p class="traj-empty__sub">
            <template v-if="mapMode === 'plate'">
              请通过车牌告警弹框的「查看轨迹」或车牌管理页的「出现轨迹」进入
            </template>
            <template v-else>
              请通过人员详情的「出现轨迹」或人脸告警弹框的头像进入
            </template>
          </p>
        </div>
      </section>

      <aside v-if="mapMode === 'device'" class="geo-loc-panel" aria-label="告警筛选">
        <header class="geo-loc-panel__header">
          <div class="geo-loc-panel__header-main">
            <h3 class="geo-loc-panel__title">告警筛选</h3>
            <span class="geo-loc-panel__stat">
              <strong>{{ locatedCount }}</strong> 已上图
              <template v-if="unlocatedCount > 0">
                <span class="geo-loc-panel__stat-sep">·</span>
                {{ unlocatedCount }} 无坐标
              </template>
            </span>
          </div>
          <MapLayerSwitcher
            v-model:show-cameras="showCameras"
            v-model:show-alerts="showAlerts"
            layout="inline"
            label=""
          />
        </header>

        <section class="geo-loc-panel__filter">
          <h4 class="geo-loc-panel__filter-title">查询条件</h4>
          <div class="geo-loc-panel__filter-scroll">
            <div class="geo-loc-panel__form">
              <BasicForm @register="registerForm" @submit="handleSearch" />
            </div>
          </div>
          <div v-if="filterChips.length" class="geo-loc-panel__chips">
            <a-tag
              v-for="chip in filterChips"
              :key="chip.key"
              closable
              class="geo-loc-panel__chip"
              @close.prevent="removeFilterChip(chip.key)"
            >
              {{ chip.label }}
            </a-tag>
            <Button type="link" size="small" class="geo-loc-panel__chip-clear" @click="handleReset">
              清空
            </Button>
          </div>
          <div class="geo-loc-panel__actions">
            <Button class="geo-loc-panel__btn-reset" @click="handleReset">
              重置
            </Button>
            <Button
              type="primary"
              class="geo-loc-panel__btn-submit"
              :loading="dataLoading"
              @click="handleSearch"
            >
              查询
            </Button>
          </div>
        </section>

        <footer v-if="hasSelection" class="geo-loc-panel__detail">
          <div class="geo-loc-panel__detail-head">
            <h4 class="geo-loc-panel__detail-title">
              {{ selectedCamera ? '摄像头' : '告警详情' }}
            </h4>
            <button type="button" class="geo-loc-panel__detail-close" @click="clearSelection">
              <Icon icon="ant-design:close-outlined" :size="14" />
            </button>
          </div>

          <template v-if="selectedCamera">
            <p class="alert-map-detail-name">{{ selectedCamera.name }}</p>
            <p v-if="selectedCamera.lng != null" class="alert-map-detail-coord">
              {{ formatLocationSummary({ longitude: selectedCamera.lng, latitude: selectedCamera.lat }) }}
            </p>
            <div class="alert-map-detail-actions">
              <Button size="small" type="primary" preIcon="octicon:play-16" @click="handlePlay">播放</Button>
              <Button
                size="small"
                :type="previewOpen ? 'primary' : 'default'"
                preIcon="ant-design:video-camera-outlined"
                @click="previewOpen = !previewOpen"
              >
                {{ previewOpen ? '收起' : '预览' }}
              </Button>
              <Button size="small" preIcon="ant-design:eye-filled" @click="handleView">详情</Button>
              <Button size="small" preIcon="ant-design:edit-filled" @click="handleEdit">编辑</Button>
              <Button
                v-if="canPtzSelectedCamera"
                size="small"
                :type="ptzOpen ? 'primary' : 'default'"
                preIcon="ant-design:control-outlined"
                @click="ptzOpen = !ptzOpen"
              >
                云台
              </Button>
              <Button
                v-if="canSetSelectedCameraLocation"
                size="small"
                preIcon="ant-design:environment-outlined"
                @click="handleSetLocation()"
              >
                设置坐标
              </Button>
            </div>
            <CameraInlinePreview v-if="previewOpen" :device-id="selectedCamera.id" />
            <CameraPtzPad
              v-if="ptzOpen && canPtzSelectedCamera"
              :device-id="selectedCamera.id"
              :device-kind="selectedCamera.device_kind"
            />
          </template>

          <template v-else-if="selectedAlert">
            <p class="alert-map-detail-name">{{ formatAlertListTitle(selectedAlert) }}</p>
            <p class="alert-map-detail-meta">
              {{ selectedAlert.device_name || selectedAlert.device_id }}
              <span v-if="selectedAlert.time" class="alert-map-detail-meta__time">{{ selectedAlert.time }}</span>
            </p>
            <div class="alert-map-detail-actions">
              <Button
                v-if="selectedAlert.image_url"
                size="small"
                preIcon="ion:image-sharp"
                @click="handleAlertAction(selectedAlert as Record<string, unknown>, 'image')"
              >
                图片
              </Button>
              <Button
                v-if="selectedAlert.device_id && selectedAlert.time"
                size="small"
                preIcon="icon-park-outline:video"
                @click="handleAlertAction(selectedAlert as Record<string, unknown>, 'video')"
              >
                录像
              </Button>
              <Button
                v-if="canSetLinkedCameraLocation && linkedCamera"
                size="small"
                preIcon="ant-design:environment-outlined"
                @click="handleSetLocation(linkedCamera)"
              >
                设置坐标
              </Button>
            </div>
          </template>
        </footer>
      </aside>
    </div>
  </div>
</template>

<style scoped lang="less">
@primary: #266cfb;
@border: #e4e9f2;
@divider: #f0f2f7;
@text: rgba(0, 0, 0, 0.88);
@text-2: rgba(0, 0, 0, 0.55);
@text-3: rgba(0, 0, 0, 0.35);
@panel-width: 420px;

.geo-loc {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 120px);
  background: #fff;
}

.geo-loc__workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.geo-loc__map-area {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background: #e8ebf2;

  // 地图模式切换（左上角）：设备视图 / 人脸时空视图
  .map-mode-switch {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 20;
    display: inline-flex;
    gap: 2px;
    padding: 3px;
    background: rgba(255, 255, 255, 0.96);
    border-radius: 10px;
    border: 1px solid #e4e9f2;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.1);

    // 轨迹视图（人脸/车牌）时回到左上角，与轨迹横幅同一侧
    &--left {
      right: auto;
      left: 12px;
    }

    &__btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 6px 12px;
      border: none;
      border-radius: 8px;
      background: transparent;
      font-size: 13px;
      color: rgba(0, 0, 0, 0.65);
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background: rgba(0, 0, 0, 0.05);
      }

      &--active {
        background: #266cfb;
        color: #fff;

        &:hover {
          background: #266cfb;
        }
      }
    }
  }

  // 人脸时空视图空态（地图中央提示）
  .traj-empty {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 20;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 24px 36px;
    background: rgba(255, 255, 255, 0.96);
    border-radius: 14px;
    border: 1px solid #e4e9f2;
    box-shadow: 0 8px 28px rgba(15, 23, 42, 0.12);
    color: #266cfb;

    &__title {
      margin: 0;
      font-size: 15px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.85);
    }

    &__sub {
      margin: 0;
      font-size: 13px;
      color: rgba(0, 0, 0, 0.45);
    }
  }

  // 人物出现轨迹提示条（人脸时空模式工具栏）
  .traj-banner {
    position: absolute;
    top: 52px;
    left: 12px;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.96);
    border-radius: 10px;
    border: 1px solid #e4e9f2;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.1);
    font-size: 13px;

    &__icon {
      color: #266cfb;
    }

    &__text {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: rgba(0, 0, 0, 0.75);

      b {
        color: #266cfb;
        font-weight: 600;
      }
    }

    &__date {
      width: 130px;
    }

    &__clear {
      height: auto;
      padding: 0 4px;
      font-size: 12px;
    }
  }

  :deep(.alert-device-map),
  :deep(.alert-device-map--embedded) {
    position: absolute;
    inset: 0;
    width: 100%;
    height: auto !important;
    min-height: 0;
    border-radius: 0;
    background: transparent !important;
    box-shadow: none !important;
  }

  :deep(.alert-device-map__map),
  :deep(.alert-device-map .ant-spin-nested-loading),
  :deep(.alert-device-map .ant-spin-container) {
    height: 100% !important;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  :deep(.basic-tianditu-map) {
    position: absolute;
    inset: 0;
    width: 100%;
    height: auto;
    min-height: 0;
  }
}

.geo-loc-panel {
  width: @panel-width;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: linear-gradient(180deg, #fff 0%, #fafbfd 100%);
  border-left: 1px solid rgba(228, 233, 242, 0.85);
  box-shadow: -6px 0 28px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.geo-loc-panel__header {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 20px 12px;
  border-bottom: 1px solid @divider;
}

.geo-loc-panel__header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.geo-loc-panel__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: @text;
  flex-shrink: 0;
}

.geo-loc-panel__stat {
  font-size: 12px;
  color: @text-2;
  white-space: nowrap;

  strong {
    color: @primary;
    font-weight: 600;
  }
}

.geo-loc-panel__stat-sep {
  margin: 0 4px;
  color: @text-3;
}

.geo-loc-panel__filter {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.geo-loc-panel__filter-title {
  flex-shrink: 0;
  margin: 0;
  padding: 14px 20px 0;
  font-size: 13px;
  font-weight: 600;
  color: @text-2;
}

.geo-loc-panel__filter-scroll {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 10px 20px 4px;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: #d0d5df;
    border-radius: 3px;
  }
}

.geo-loc-panel__form :deep(.ant-form-item) {
  margin-bottom: 10px;
}

.geo-loc-panel__form :deep(.ant-picker),
.geo-loc-panel__form :deep(.ant-select) {
  width: 100%;
}

.geo-loc-panel__form :deep(.ant-form-item-label > label) {
  font-size: 12px;
}

.geo-loc-panel__chips {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 8px 20px 0;
  border-top: 1px dashed @divider;
}

.geo-loc-panel__chip {
  margin: 0;
  font-size: 12px;
  line-height: 20px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.geo-loc-panel__chip-clear {
  padding: 0 4px;
  height: auto;
  font-size: 12px;
}

.geo-loc-panel__actions {
  flex-shrink: 0;
  display: flex;
  gap: 10px;
  margin: 0;
  padding: 12px 20px 14px;
  border-top: 1px solid @divider;
  background: #fff;
}

.geo-loc-panel__btn-reset {
  flex: 0 0 88px;
  height: 36px;
  padding: 0 12px;
  font-size: 14px;
  border-radius: 6px;
  border-color: @border;
  color: @text-2;
  background: #fff;

  &:hover {
    color: @primary;
    border-color: rgba(38, 108, 251, 0.45);
  }
}

.geo-loc-panel__btn-submit {
  flex: 1;
  height: 36px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
  box-shadow: none;
}

.geo-loc-panel__detail {
  flex-shrink: 0;
  padding: 12px 20px 16px;
  border-top: 1px solid @divider;
  background: #f8f9fc;
  box-shadow: 0 -4px 16px rgba(15, 23, 42, 0.04);
}

.geo-loc-panel__detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.geo-loc-panel__detail-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: @text-2;
}

.geo-loc-panel__detail-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: @text-3;
  cursor: pointer;

  &:hover {
    background: rgba(0, 0, 0, 0.06);
    color: @text-2;
  }
}

.alert-map-detail-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  color: @text;
  line-height: 1.4;
}

.alert-map-detail-meta {
  margin: 0 0 10px;
  font-size: 12px;
  color: @text-2;

  &__time {
    margin-left: 8px;
    color: @text-3;
  }
}

.alert-map-detail-coord {
  margin: 0 0 10px;
  font-size: 12px;
  font-family: ui-monospace, Menlo, monospace;
  color: @primary;
}

.alert-map-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
