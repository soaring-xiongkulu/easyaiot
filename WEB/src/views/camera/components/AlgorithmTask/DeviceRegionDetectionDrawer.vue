<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="区域检测配置"
    width="96%"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <div class="region-config-shell">
      <div v-if="initializing" class="region-config-loading">
        <a-spin :tip="initializingTip" size="large" />
      </div>

      <!-- 紧凑摄像头切换条 -->
        <div v-if="devices.length > 0" class="camera-bar">
          <div
            ref="cameraListRef"
            class="camera-bar__list"
            @wheel="onCameraListWheel"
          >
            <div
              v-for="device in devices"
              :key="device.id"
              class="camera-chip"
              :class="{
                'is-active': selectedDeviceId === device.id,
                'is-loading': capturingDeviceIds.has(device.id),
                'is-failed': captureFailedDeviceIds.has(device.id),
              }"
              @click="selectDevice(device)"
            >
              <span class="camera-chip__thumb">
                <img
                  v-if="getDeviceThumb(device.id)"
                  :src="getDeviceThumb(device.id)"
                  :alt="device.name"
                  @error="(e) => handleThumbError(e, device.id)"
                />
                <Icon v-else icon="ant-design:video-camera-outlined" :size="14" />
                <span v-if="capturingDeviceIds.has(device.id)" class="camera-chip__spin">
                  <LoadingOutlined spin />
                </span>
              </span>
              <span class="camera-chip__name">{{ device.name || device.id }}</span>
              <a-tag
                v-if="captureFailedDeviceIds.has(device.id)"
                color="error"
                class="camera-chip__tag"
              >
                失败
              </a-tag>
              <span v-else class="camera-chip__count">{{ getRegionCount(device.id) }}</span>
            </div>
          </div>
          <Button
            class="camera-bar__refresh"
            type="default"
            preIcon="ant-design:reload-outlined"
            :loading="refreshingAll"
            @click="refreshAllSnapshots"
          >
            刷新
          </Button>
        </div>
        <div v-else-if="!initializing" class="camera-bar camera-bar--empty">
          <a-empty description="未加载到任务关联的摄像头" :image="false" />
        </div>

        <!-- 主工作区：画布占满剩余空间 -->
        <div class="region-workspace">
          <DeviceRegionDrawer
            v-if="selectedDeviceId && taskId"
            :key="`${taskId}-${selectedDeviceId}`"
            :task-id="taskId"
            :device-id="selectedDeviceId"
            :device-meta="getSelectedDevice()"
            :initial-regions="deviceRegions[selectedDeviceId] || []"
            :initial-image-id="deviceImageIds[selectedDeviceId]"
            :initial-image-path="deviceImagePaths[selectedDeviceId]"
            :auto-capture="!deviceImagePaths[selectedDeviceId] || captureFailedDeviceIds.has(selectedDeviceId)"
            @save="handleRegionSave"
            @image-captured="handleImageCaptured"
            @cover-updated="handleCoverUpdated"
          />
          <div v-else class="region-workspace__empty">
            <a-empty description="暂无关联摄像头" :image="false" />
          </div>
        </div>
    </div>
  </BasicDrawer>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue';
import { LoadingOutlined } from '@ant-design/icons-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { getDeviceList, getDeviceInfo, type DeviceInfo } from '@/api/device/camera';
import {
  listDeviceRegionsSafe,
  type DeviceDetectionRegion,
} from '@/api/device/device_detection_region';
import { getTaskStreams, type CameraStreamInfo } from '@/api/device/algorithm_task';
import DeviceRegionDrawer from '../DeviceRegionDrawer/index.vue';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { captureSnapshotWithQuality } from '@/views/camera/utils/deviceSnapshotCapture';
import {
  isGb28181Device,
  sleep,
  verifySnapshotQuality,
} from '@/views/camera/utils/snapshotQuality';

defineOptions({ name: 'DeviceRegionDetectionDrawer' });

const { createMessage } = useMessage();

const taskId = ref<number | null>(null);
/** 打开抽屉时锁定的设备 ID，防止抓图后列表被全量设备污染 */
const pinnedDeviceIds = ref<string[] | null>(null);

const devices = ref<DeviceInfo[]>([]);
const selectedDeviceId = ref<string | null>(null);
const deviceRegions = ref<Record<string, DeviceDetectionRegion[]>>({});
const deviceImageIds = ref<Record<string, number>>({});
const deviceImagePaths = ref<Record<string, string>>({});

const initializing = ref(false);
const refreshingAll = ref(false);
const capturingDeviceIds = ref<Set<string>>(new Set());
const captureFailedDeviceIds = ref<Set<string>>(new Set());
const cameraListRef = ref<HTMLElement | null>(null);

function onCameraListWheel(e: WheelEvent) {
  const el = cameraListRef.value;
  if (!el || el.scrollWidth <= el.clientWidth) return;
  el.scrollLeft += e.deltaY;
  e.preventDefault();
}

const hasGbDevice = computed(() => devices.value.some((d) => isGb28181Device(d)));

const loadingElapsedSec = ref(0);
let loadingTimer: ReturnType<typeof setInterval> | null = null;

function startLoadingTimer() {
  loadingElapsedSec.value = 0;
  stopLoadingTimer();
  loadingTimer = setInterval(() => {
    loadingElapsedSec.value += 1;
  }, 1000);
}

function stopLoadingTimer() {
  if (loadingTimer) {
    clearInterval(loadingTimer);
    loadingTimer = null;
  }
}

const initializingTip = computed(() => {
  if (!hasGbDevice.value) {
    return '正在加载摄像头并抓取基准图…';
  }
  if (loadingElapsedSec.value <= 5) {
    return 'GB 设备出图中，请稍候…';
  }
  return `GB 设备出图中，已等待 ${loadingElapsedSec.value} 秒…`;
});

onUnmounted(() => {
  stopLoadingTimer();
});

function getSelectedDevice(): DeviceInfo | undefined {
  if (!selectedDeviceId.value) return undefined;
  return devices.value.find((d) => d.id === selectedDeviceId.value);
}

function getDeviceById(deviceId: string): DeviceInfo | undefined {
  return devices.value.find((d) => d.id === deviceId);
}

function getCaptureGapMs(prevDevice?: DeviceInfo, nextDevice?: DeviceInfo): number {
  const prevGb = isGb28181Device(prevDevice);
  const nextGb = isGb28181Device(nextDevice);
  if (prevGb || nextGb) return 4000;
  return 1500;
}

const [register] = useDrawerInner(async (data) => {
  selectedDeviceId.value = null;
  deviceRegions.value = {};
  deviceImageIds.value = {};
  deviceImagePaths.value = {};
  captureFailedDeviceIds.value = new Set();
  pinnedDeviceIds.value = null;
  taskId.value = null;

  const incomingIds = Array.isArray(data?.deviceIds)
    ? data.deviceIds.map(String).filter(Boolean)
    : [];
  const incomingLabels =
    data?.deviceLabels && typeof data.deviceLabels === 'object' ? data.deviceLabels : {};

  if (data?.taskId) {
    taskId.value = data.taskId;
  }

  // 优先使用表单传入的设备 ID（与任务配置一致），taskId 仅作封面等信息补充
  if (incomingIds.length > 0) {
    pinnedDeviceIds.value = incomingIds;
    await loadDevicesByIds(incomingIds, incomingLabels);
    if (taskId.value) {
      await enrichDevicesFromStreams(taskId.value);
    }
  } else if (taskId.value) {
    await loadTaskDevices(taskId.value);
    pinnedDeviceIds.value = devices.value.map((d) => String(d.id));
  } else {
    await loadDevices();
    pinnedDeviceIds.value = devices.value.map((d) => String(d.id));
  }

  await bootstrapDevices();
});

function extractListData(response: unknown): DeviceInfo[] {
  if (Array.isArray(response)) return response as DeviceInfo[];
  if (response && typeof response === 'object') {
    const obj = response as Record<string, unknown>;
    if (Array.isArray(obj.data)) return obj.data as DeviceInfo[];
    if (obj.data && typeof obj.data === 'object' && Array.isArray((obj.data as any).list)) {
      return (obj.data as any).list as DeviceInfo[];
    }
    if (Array.isArray(obj.list)) return obj.list as DeviceInfo[];
  }
  return [];
}

function parseDeviceInfo(response: unknown): DeviceInfo | null {
  if (!response || typeof response !== 'object') return null;
  const obj = response as Record<string, unknown>;
  if (obj.code === 0 && obj.data && typeof obj.data === 'object' && (obj.data as any).id) {
    return obj.data as DeviceInfo;
  }
  if ('id' in obj && obj.id) {
    return obj as DeviceInfo;
  }
  return null;
}

async function prefetchDeviceMeta(device: DeviceInfo) {
  if (!taskId.value) {
    deviceRegions.value[device.id] = [];
    return;
  }
  try {
    const regions = await listDeviceRegionsSafe(device.id, taskId.value);
    deviceRegions.value[device.id] = regions;

    if (regions.length > 0 && regions[0].image_path) {
      deviceImagePaths.value[device.id] = regions[0].image_path;
      if (regions[0].image_id) {
        deviceImageIds.value[device.id] = regions[0].image_id;
      }
      return;
    }
    if (device.cover_image_path) {
      deviceImagePaths.value[device.id] = device.cover_image_path;
    }
  } catch (error) {
    deviceRegions.value[device.id] = [];
    if (device.cover_image_path) {
      deviceImagePaths.value[device.id] = device.cover_image_path;
    }
    console.warn('加载区域配置失败', device.id, error);
  }
}

async function captureSnapshotForDevice(
  deviceId: string,
  silent = true,
  options?: { skipPreWait?: boolean },
): Promise<boolean> {
  if (capturingDeviceIds.value.has(deviceId)) return false;
  capturingDeviceIds.value = new Set([...capturingDeviceIds.value, deviceId]);
  try {
    const device = getDeviceById(deviceId);
    const result = await captureSnapshotWithQuality(deviceId, {
      silent,
      device,
      skipPreWait: options?.skipPreWait,
    });
    if (result.ok && result.imageUrl) {
      deviceImageIds.value[deviceId] = result.imageId!;
      deviceImagePaths.value[deviceId] = result.imageUrl;
      const idx = devices.value.findIndex((d) => d.id === deviceId);
      if (idx >= 0) {
        devices.value[idx] = {
          ...devices.value[idx],
          cover_image_path: result.imageUrl,
        };
      }
      if (!silent) {
        createMessage.success(isGb28181Device(device) ? '抓图成功' : '抓图成功');
      }
      return true;
    }
    if (!silent) {
      createMessage.error(
        isGb28181Device(device)
          ? '抓图失败或画面未就绪，请稍后重试'
          : '抓图失败，请稍后重试',
      );
    }
    return false;
  } catch (error) {
    console.error('抓图失败', deviceId, error);
    if (!silent) {
      createMessage.error('抓图失败');
    }
    return false;
  } finally {
    const next = new Set(capturingDeviceIds.value);
    next.delete(deviceId);
    capturingDeviceIds.value = next;
  }
}

function clearDeviceImageCache(deviceId: string) {
  delete deviceImagePaths.value[deviceId];
  delete deviceImageIds.value[deviceId];
  const idx = devices.value.findIndex((d) => d.id === deviceId);
  if (idx >= 0 && devices.value[idx].cover_image_path) {
    devices.value[idx] = { ...devices.value[idx], cover_image_path: '' };
  }
}

function markCaptureFailed(deviceId: string) {
  captureFailedDeviceIds.value = new Set([...captureFailedDeviceIds.value, deviceId]);
}

function markCaptureSucceeded(deviceId: string) {
  const next = new Set(captureFailedDeviceIds.value);
  next.delete(deviceId);
  captureFailedDeviceIds.value = next;
}

/** 校验封面是否可用，无效则清除缓存并带重试抓图 */
async function ensureDeviceSnapshot(
  deviceId: string,
  silent = true,
  options?: { skipPreWait?: boolean },
): Promise<boolean> {
  const cachedPath = deviceImagePaths.value[deviceId];
  if (cachedPath) {
    const quality = await verifySnapshotQuality(cachedPath, { bustCache: true });
    if (quality.loadable && quality.valid) {
      markCaptureSucceeded(deviceId);
      return true;
    }
    clearDeviceImageCache(deviceId);
  }
  const ok = await captureSnapshotForDevice(deviceId, silent, options);
  if (ok) {
    markCaptureSucceeded(deviceId);
    return true;
  }
  clearDeviceImageCache(deviceId);
  markCaptureFailed(deviceId);
  if (!silent) {
    const device = getDeviceById(deviceId);
    createMessage.error(
      isGb28181Device(device)
        ? 'GB 设备出图较慢，抓图失败或仍为灰屏，请稍后重试'
        : '抓图失败，请稍后重试',
    );
  }
  return false;
}

/** 后台依次为其余摄像头抓图，不阻塞界面 */
async function prefetchRemainingSnapshots(fromIndex = 1) {
  for (let i = fromIndex; i < devices.value.length; i++) {
    if (i > fromIndex) {
      await sleep(getCaptureGapMs(devices.value[i - 1], devices.value[i]));
    }
    if (deviceImagePaths.value[devices.value[i].id]) continue;
    await ensureDeviceSnapshot(devices.value[i].id, true, { skipPreWait: true });
  }
}

async function bootstrapDevices() {
  if (devices.value.length === 0) return;
  initializing.value = true;
  startLoadingTimer();
  captureFailedDeviceIds.value = new Set();
  try {
    await Promise.all(devices.value.map((d) => prefetchDeviceMeta(d)));

    selectedDeviceId.value = devices.value[0].id;

    // 仅首路摄像头阻塞界面，其余后台抓图
    await ensureDeviceSnapshot(devices.value[0].id, true);
  } finally {
    initializing.value = false;
    stopLoadingTimer();
  }

  if (devices.value.length > 1) {
    void prefetchRemainingSnapshots(1);
  }
}

async function refreshAllSnapshots() {
  if (devices.value.length === 0) return;
  refreshingAll.value = true;
  captureFailedDeviceIds.value = new Set();
  try {
    for (let i = 0; i < devices.value.length; i++) {
      if (i > 0) {
        await sleep(getCaptureGapMs(devices.value[i - 1], devices.value[i]));
      }
      clearDeviceImageCache(devices.value[i].id);
      await ensureDeviceSnapshot(devices.value[i].id, true);
    }
    createMessage.success('已全部刷新基准图');
  } finally {
    refreshingAll.value = false;
  }
}

async function selectDevice(device: DeviceInfo) {
  if (selectedDeviceId.value === device.id) return;

  if (!deviceRegions.value[device.id]) {
    await prefetchDeviceMeta(device);
  }

  selectedDeviceId.value = device.id;

  if (!deviceImagePaths.value[device.id]) {
    void ensureDeviceSnapshot(device.id, true, { skipPreWait: true });
  }
}

function getDeviceThumb(deviceId: string) {
  const raw =
    deviceImagePaths.value[deviceId] ||
    devices.value.find((d) => d.id === deviceId)?.cover_image_path;
  return raw ? resolveAlertImageDisplayUrl(raw) : '';
}

function getRegionCount(deviceId: string) {
  return deviceRegions.value[deviceId]?.length ?? 0;
}

function handleThumbError(e: Event, deviceId: string) {
  const img = e.target as HTMLImageElement;
  img.style.display = 'none';
  clearDeviceImageCache(deviceId);
  void ensureDeviceSnapshot(deviceId, true);
}

function handleRegionSave(regions: DeviceDetectionRegion[]) {
  if (selectedDeviceId.value) {
    deviceRegions.value[selectedDeviceId.value] = regions;
  }
}

function handleImageCaptured(imageId: number, imagePath: string) {
  if (!selectedDeviceId.value) return;
  deviceImageIds.value[selectedDeviceId.value] = imageId;
  deviceImagePaths.value[selectedDeviceId.value] = imagePath;
  markCaptureSucceeded(selectedDeviceId.value);
}

function handleCoverUpdated(imagePath: string) {
  if (!selectedDeviceId.value) return;
  const deviceId = selectedDeviceId.value;
  deviceImagePaths.value[deviceId] = imagePath;
  markCaptureSucceeded(deviceId);
  const idx = devices.value.findIndex((d) => d.id === deviceId);
  if (idx >= 0) {
    devices.value[idx] = { ...devices.value[idx], cover_image_path: imagePath };
  }
}

async function loadTaskDevices(id: number) {
  try {
    const response = await getTaskStreams(id);
    let streams: CameraStreamInfo[] = [];
    if (Array.isArray(response)) {
      streams = response;
    } else if (response && typeof response === 'object' && 'code' in response) {
      if (response.code === 0 && Array.isArray(response.data)) {
        streams = response.data;
      } else {
        createMessage.warning(response.msg || '该任务未关联摄像头');
        devices.value = [];
        return;
      }
    } else {
      devices.value = [];
      return;
    }

    const seen = new Set<string>();
    devices.value = streams
      .filter((stream) => {
        const did = String(stream.device_id);
        if (seen.has(did)) return false;
        seen.add(did);
        return true;
      })
      .map(
        (stream) =>
          ({
            id: stream.device_id,
            name: stream.device_name,
            http_stream: stream.http_stream,
            rtmp_stream: stream.rtmp_stream,
            source: stream.source,
            cover_image_path: stream.cover_image_path,
          }) as DeviceInfo,
      );

    if (devices.value.length === 0) {
      createMessage.warning('该任务未关联摄像头');
    }
  } catch (error) {
    console.error('加载任务关联摄像头失败', error);
    createMessage.error(formatApiErrorMessage(error, '加载任务关联摄像头失败'));
    devices.value = [];
  }
}

async function loadDevicesByIds(
  deviceIds: string[],
  labelMap: Record<string, string> = {},
) {
  const idSet = new Set(deviceIds.map(String));
  const foundMap = new Map<string, DeviceInfo>();

  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    for (const device of extractListData(response)) {
      if (idSet.has(String(device.id))) {
        foundMap.set(String(device.id), device);
      }
    }
  } catch (error) {
    console.warn('批量加载设备列表失败，将逐个查询', error);
  }

  for (const id of deviceIds) {
    const key = String(id);
    if (foundMap.has(key)) continue;
    try {
      const response = await getDeviceInfo(key);
      const device = parseDeviceInfo(response);
      if (device) {
        foundMap.set(key, device);
      }
    } catch (error) {
      console.warn('查询设备失败', key, error);
    }
  }

  devices.value = deviceIds.map((id) => {
    const key = String(id);
    const existing = foundMap.get(key);
    if (existing) {
      return {
        ...existing,
        name: labelMap[key] || existing.name || key,
      };
    }
    return {
      id: key,
      name: labelMap[key] || key,
    } as DeviceInfo;
  });

  if (devices.value.length === 0) {
    createMessage.warning('未找到所选摄像头');
  }
}

async function enrichDevicesFromStreams(id: number) {
  try {
    const response = await getTaskStreams(id);
    let streams: CameraStreamInfo[] = [];
    if (Array.isArray(response)) {
      streams = response;
    } else if (response && typeof response === 'object' && 'code' in response) {
      if (response.code === 0 && Array.isArray(response.data)) {
        streams = response.data;
      }
    }
    const streamMap = new Map(streams.map((s) => [String(s.device_id), s]));
    devices.value = devices.value.map((device) => {
      const stream = streamMap.get(String(device.id));
      if (!stream) return device;
      return {
        ...device,
        name: device.name || stream.device_name || device.id,
        http_stream: stream.http_stream ?? device.http_stream,
        rtmp_stream: stream.rtmp_stream ?? device.rtmp_stream,
        source: stream.source ?? device.source,
        cover_image_path: stream.cover_image_path ?? device.cover_image_path,
      } as DeviceInfo;
    });
  } catch (error) {
    console.warn('补充任务流信息失败', error);
  }
}

async function loadDevices() {
  if (pinnedDeviceIds.value?.length) {
    await loadDevicesByIds(pinnedDeviceIds.value);
    return;
  }
  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    devices.value = extractListData(response);
  } catch (error) {
    console.error('加载设备列表失败', error);
    createMessage.error(formatApiErrorMessage(error, '加载设备列表失败'));
  }
}
</script>

<style lang="less" scoped>
@text: rgba(0, 0, 0, 0.65);
@text-muted: rgba(0, 0, 0, 0.45);
@border: #f0f0f0;
@surface: #fff;

.region-config-shell {
  position: relative;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 96px);
  min-height: 720px;
  min-width: 0;
  gap: 12px;
  padding: 12px 16px 16px;
  background: #fff;
}

.region-config-loading {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.72);
  border-radius: 8px;

  :deep(.ant-spin-text) {
    color: rgba(0, 0, 0, 0.45);
  }
}

.camera-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  min-width: 0;
  min-height: 52px;
  padding: 9px 16px;
  background: @surface;
  border: 1px solid @border;
  border-radius: 8px;
  overflow: hidden;

  &__list {
    flex: 1 1 0;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 8px;
    min-width: 0;
    height: 34px;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0 0 6px;
    margin-bottom: -6px;
    -webkit-overflow-scrolling: touch;
    scroll-behavior: smooth;

    &::-webkit-scrollbar {
      height: 4px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background: rgba(0, 0, 0, 0.12);
      border-radius: 2px;
    }

    &:hover::-webkit-scrollbar-thumb {
      background: rgba(0, 0, 0, 0.22);
    }
  }

  &__refresh {
    flex-shrink: 0;
    height: 34px !important;
    padding-inline: 12px !important;
    line-height: 32px !important;
    display: inline-flex !important;
    align-items: center !important;
  }

  &--empty {
    justify-content: center;
    min-height: 64px;
  }
}

.camera-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  max-width: 180px;
  padding: 0 10px 0 4px;
  border-radius: 17px;
  border: 1px solid @border;
  background: @surface;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.2s, background 0.2s;

  &:hover {
    border-color: #d9d9d9;
    background: #fafafa;
  }

  &.is-active {
    border-color: rgba(22, 119, 255, 0.45);
    background: #fafafa;
  }

  &.is-failed {
    border-color: #ffccc7;
    background: #fff;
  }

  &__thumb {
    position: relative;
    width: 28px;
    height: 26px;
    border-radius: 4px;
    overflow: hidden;
    background: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: @text-muted;
    flex-shrink: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  &__spin {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.35);
    color: @text-muted;
    font-size: 12px;
  }

  &__name {
    flex: 1;
    min-width: 0;
    max-width: 96px;
    font-size: 12px;
    color: @text;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__count {
    font-size: 12px;
    color: @text-muted;
    min-width: 14px;
    text-align: center;
  }

  &__tag {
    margin: 0;
    line-height: 18px;
    font-size: 11px;
  }
}

.region-workspace {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border: 1px solid @border;
  border-radius: 6px;
  background: @surface;

  &__empty {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fafafa;

    :deep(.ant-empty-description) {
      color: @text-muted;
    }
  }
}
</style>
