<template>
  <div class="camera-map-panel">
    <div class="camera-map-panel__layout">
      <aside class="camera-map-panel__sider">
        <div class="camera-map-panel__sider-head">
          <div class="camera-map-panel__sider-title">
            <span class="camera-map-panel__sider-icon">
              <Icon icon="ant-design:video-camera-outlined" :size="15" />
            </span>
            <div class="camera-map-panel__sider-heading">
              <span class="camera-map-panel__sider-name">摄像头目录</span>
              <span class="camera-map-panel__sider-desc">共 {{ deviceList.length }} 路</span>
            </div>
          </div>
          <AButton size="small" :loading="listLoading" @click="reloadAll">
            <template #icon>
              <Icon icon="ant-design:reload-outlined" />
            </template>
            刷新
          </AButton>
        </div>

        <div class="camera-map-panel__stats">
          <button
            type="button"
            class="camera-map-panel__stat"
            :class="{ 'is-active': locateFilter === 'all' }"
            @click="locateFilter = 'all'"
          >
            <strong>{{ deviceList.length }}</strong>
            <span>全部</span>
          </button>
          <button
            type="button"
            class="camera-map-panel__stat is-located"
            :class="{ 'is-active': locateFilter === 'located' }"
            @click="locateFilter = 'located'"
          >
            <strong>{{ locatedCount }}</strong>
            <span>已上图</span>
          </button>
          <button
            type="button"
            class="camera-map-panel__stat is-pending"
            :class="{ 'is-active': locateFilter === 'unlocated' }"
            @click="locateFilter = 'unlocated'"
          >
            <strong>{{ unlocatedCount }}</strong>
            <span>待上图</span>
          </button>
        </div>

        <div class="camera-map-panel__search">
          <a-input
            v-model:value="keyword"
            allow-clear
            placeholder="搜索摄像头名称或地址"
          >
            <template #prefix>
              <Icon icon="ant-design:search-outlined" />
            </template>
          </a-input>
        </div>

        <div class="camera-map-panel__list">
          <a-spin :spinning="listLoading">
            <div v-if="!filteredList.length" class="camera-map-panel__empty">
              <Icon icon="ant-design:inbox-outlined" :size="28" />
              <p>{{ emptyText }}</p>
              <AButton
                v-if="unlocatedCount > 0 && locateFilter === 'located'"
                type="primary"
                ghost
                size="small"
                @click="locateFilter = 'unlocated'"
              >
                去设置坐标
              </AButton>
            </div>

            <div
              v-for="group in groupedList"
              :key="group.key"
              class="camera-map-panel__group"
            >
              <button
                type="button"
                class="camera-map-panel__group-head"
                @click="toggleGroup(group.key)"
              >
                <Icon
                  :icon="collapsedGroups[group.key] ? 'ant-design:caret-right-filled' : 'ant-design:caret-down-filled'"
                  :size="12"
                />
                <span class="camera-map-panel__group-title">{{ group.title }}</span>
                <span class="camera-map-panel__group-count">{{ group.items.length }}</span>
              </button>

              <div v-show="!collapsedGroups[group.key]" class="camera-map-panel__group-body">
                <div
                  v-for="item in group.items"
                  :key="item.id"
                  class="camera-map-panel__item"
                  :class="{
                    'is-active': selectedId === item.id,
                    'is-located': hasLocation(item),
                    'is-online': item.online === true,
                    'is-loading': playLoadingId === item.id,
                  }"
                >
                  <div
                    class="camera-map-panel__item-body"
                    @click="handleSelectDevice(item)"
                  >
                    <span
                      class="camera-map-panel__dot"
                      :title="item.online ? '在线' : '离线'"
                    />
                    <div class="camera-map-panel__item-main">
                      <div class="camera-map-panel__item-name" :title="item.name">
                        {{ item.name || item.id }}
                      </div>
                      <div class="camera-map-panel__item-meta">
                        <span v-if="hasLocation(item)" class="camera-map-panel__addr">
                          <Icon icon="ant-design:environment-filled" :size="11" />
                          {{ item.address || formatCoord(item) }}
                        </span>
                        <span v-else class="camera-map-panel__id">{{ item.id }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="camera-map-panel__item-actions">
                    <template v-if="hasLocation(item)">
                      <AButton
                        type="default"
                        size="small"
                        class="camera-map-panel__action-btn"
                        @click="flyToDevice(item)"
                      >
                        <template #icon>
                          <Icon icon="ant-design:aim-outlined" :size="13" />
                        </template>
                        定位
                      </AButton>
                      <AButton
                        type="text"
                        size="small"
                        class="camera-map-panel__action-link"
                        @click="openLocationModal(item)"
                      >
                        改坐标
                      </AButton>
                    </template>
                    <AButton
                      v-else
                      type="primary"
                      size="small"
                      ghost
                      class="camera-map-panel__action-btn is-set"
                      @click="openLocationModal(item)"
                    >
                      <template #icon>
                        <Icon icon="ant-design:environment-outlined" :size="13" />
                      </template>
                      设置坐标
                    </AButton>
                  </div>
                </div>
              </div>
            </div>
          </a-spin>
        </div>

        <div class="camera-map-panel__sider-foot">
          <span v-if="locatedCount > 0">点击左侧摄像头弹框看监控 · 地图图标可内联预览</span>
          <span v-else>设置坐标后，摄像头会出现在右侧地图</span>
        </div>
      </aside>

      <section class="camera-map-panel__content">
        <div class="camera-map-panel__map-wrap">
          <DeviceMonitorMap
            ref="mapRef"
            height="100%"
            @marker-click="onMarkerClick"
          />

          <transition name="camera-preview-fade">
            <div
              v-if="previewDevice"
              class="camera-map-panel__preview"
            >
              <div class="camera-map-panel__preview-head">
                <div class="camera-map-panel__preview-title">
                  <Icon icon="ant-design:video-camera-filled" :size="14" />
                  <span :title="previewDevice.name">{{ previewDevice.name || previewDevice.id }}</span>
                </div>
                <div class="camera-map-panel__preview-actions">
                  <AButton
                    v-if="canPtzPreview"
                    size="small"
                    type="text"
                    class="camera-map-panel__preview-btn"
                    :class="{ 'is-active': ptzOpen }"
                    @click="ptzOpen = !ptzOpen"
                  >
                    <template #icon>
                      <Icon icon="ant-design:control-outlined" :size="14" />
                    </template>
                    云台
                  </AButton>
                  <AButton
                    size="small"
                    type="text"
                    class="camera-map-panel__preview-btn"
                    @click="openLocationModal(previewDevice)"
                  >
                    <template #icon>
                      <Icon icon="ant-design:environment-outlined" :size="14" />
                    </template>
                    改坐标
                  </AButton>
                  <button
                    type="button"
                    class="camera-map-panel__preview-close"
                    title="关闭预览"
                    @click="closePreview"
                  >
                    <Icon icon="ant-design:close-outlined" :size="14" />
                  </button>
                </div>
              </div>
              <CameraInlinePreview
                :device-id="previewDevice.id"
                :device-name="previewDevice.name"
              />
              <CameraPtzPad
                v-if="ptzOpen && canPtzPreview"
                :device-id="previewDevice.id"
                :device-kind="previewDevice.device_kind"
              />
            </div>
          </transition>
        </div>
      </section>
    </div>

    <DeviceLocationDrawer @register="registerLocationModal" @success="reloadAll" />
    <DialogPlayer title="视频播放" @register="registerPlayerModal" @cancel="clearListSelection" />
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue';
import { Button as AButton } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { useModal } from '@/components/Modal';
import { DeviceMonitorMap } from '@/components/TiandituMap';
import type { MapMarkerData } from '@/components/TiandituMap';
import CameraInlinePreview from '@/components/TiandituMap/src/components/CameraInlinePreview.vue';
import CameraPtzPad from '@/components/TiandituMap/src/components/CameraPtzPad.vue';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';
import {
  getDeviceInfo,
  getDeviceLocations,
  type DeviceInfo,
  type DeviceLocationInfo,
} from '@/api/device/camera';
import { useMessage } from '@/hooks/web/useMessage';
import { triggerWindowResize } from '@/utils/event';
import { canSetDeviceLocation, hasDeviceLocation } from '@/views/camera/utils/deviceLocation';
import { openDeviceInDialogPlayer } from '@/views/camera/utils/devicePlay';
import DeviceLocationDrawer from '@/views/camera/components/DeviceLocationDrawer/index.vue';

defineOptions({ name: 'CameraMapPanel' });

type LocateFilter = 'all' | 'located' | 'unlocated';

interface DeviceGroup {
  key: string;
  title: string;
  order: number;
  items: DeviceLocationInfo[];
}

const DEVICE_KIND_META: Record<string, { title: string; order: number }> = {
  direct: { title: '直连摄像头', order: 1 },
  gb28181: { title: '国标通道', order: 2 },
  nvr_channel: { title: 'NVR 通道', order: 3 },
};

const { createMessage } = useMessage();
const mapRef = ref<InstanceType<typeof DeviceMonitorMap> | null>(null);
const listLoading = ref(false);
const keyword = ref('');
const locateFilter = ref<LocateFilter>('all');
const selectedId = ref<string | null>(null);
const previewId = ref<string | null>(null);
const ptzOpen = ref(false);
const deviceList = ref<DeviceLocationInfo[]>([]);
const collapsedGroups = reactive<Record<string, boolean>>({});

const [registerLocationModal, { openModal: openLocationModalInner }] = useModal();
const [registerPlayerModal, { openModal: openPlayerModal }] = useModal();
const playLoadingId = ref<string | null>(null);
/** 快速连点时只保留最后一次打开，避免排队等待 */
let playSeq = 0;

function hasLocation(item: DeviceLocationInfo) {
  return hasDeviceLocation(item);
}

function formatCoord(item: DeviceLocationInfo) {
  if (item.longitude == null || item.latitude == null) return '';
  return `${Number(item.longitude).toFixed(5)}, ${Number(item.latitude).toFixed(5)}`;
}

const locatedCount = computed(() => deviceList.value.filter((d) => hasLocation(d)).length);
const unlocatedCount = computed(() => deviceList.value.length - locatedCount.value);

const filteredList = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  return deviceList.value.filter((item) => {
    if (locateFilter.value === 'located' && !hasLocation(item)) return false;
    if (locateFilter.value === 'unlocated' && hasLocation(item)) return false;
    if (!kw) return true;
    const name = (item.name || '').toLowerCase();
    const id = (item.id || '').toLowerCase();
    const addr = (item.address || '').toLowerCase();
    return name.includes(kw) || id.includes(kw) || addr.includes(kw);
  });
});

const groupedList = computed<DeviceGroup[]>(() => {
  const map = new Map<string, DeviceGroup>();
  for (const item of filteredList.value) {
    const kind = item.device_kind || 'direct';
    const meta = DEVICE_KIND_META[kind] || { title: '其他摄像头', order: 9 };
    if (!map.has(kind)) {
      map.set(kind, { key: kind, title: meta.title, order: meta.order, items: [] });
    }
    map.get(kind)!.items.push(item);
  }
  return [...map.values()]
    .map((g) => ({
      ...g,
      items: [...g.items].sort((a, b) => {
        const locDiff = Number(hasLocation(b)) - Number(hasLocation(a));
        if (locDiff !== 0) return locDiff;
        const onlineDiff = Number(b.online === true) - Number(a.online === true);
        if (onlineDiff !== 0) return onlineDiff;
        return (a.name || '').localeCompare(b.name || '', 'zh');
      }),
    }))
    .sort((a, b) => a.order - b.order || a.title.localeCompare(b.title, 'zh'));
});

const emptyText = computed(() => {
  if (listLoading.value) return '正在加载摄像头目录...';
  if (!deviceList.value.length) return '暂无摄像头，请先在「设备列表」中添加';
  if (locateFilter.value === 'located') return '还没有摄像头上图';
  if (locateFilter.value === 'unlocated') return '全部摄像头均已设置坐标';
  return '没有匹配的摄像头';
});

interface PreviewCamera {
  id: string;
  name?: string;
  device_kind?: string;
  ptz_type?: number | null;
  support_move?: boolean | null;
}

const previewDevice = computed<PreviewCamera | null>(() => {
  if (!previewId.value) return null;
  const fromList = deviceList.value.find((d) => d.id === previewId.value);
  if (fromList) return fromList;
  const fromMap = mapRef.value?.findById?.(previewId.value);
  if (!fromMap) return null;
  return {
    id: fromMap.id,
    name: fromMap.name,
    device_kind: fromMap.device_kind,
    ptz_type: fromMap.ptz_type,
    support_move: fromMap.support_move,
  };
});

const canPtzPreview = computed(() => {
  const cam = previewDevice.value;
  if (!cam) return false;
  return cam.ptz_type === 1
    || cam.ptz_type === 4
    || cam.ptz_type === 5
    || cam.support_move === true;
});

function toggleGroup(key: string) {
  collapsedGroups[key] = !collapsedGroups[key];
}

async function loadDeviceList() {
  listLoading.value = true;
  try {
    const res = (await getDeviceLocations({ has_location: false })) as
      | DeviceLocationInfo[]
      | { data?: DeviceLocationInfo[] };
    deviceList.value = Array.isArray(res) ? res : res?.data || [];
  } catch (e) {
    console.error(e);
    deviceList.value = [];
    createMessage.error('加载摄像头目录失败');
  } finally {
    listLoading.value = false;
  }
}

async function ensureMapReady() {
  await nextTick();
  mapRef.value?.updateMapSize?.();
  await new Promise<void>((r) => requestAnimationFrame(() => r()));
  mapRef.value?.updateMapSize?.();
  triggerWindowResize();
}

async function reloadAll() {
  await Promise.all([loadDeviceList(), mapRef.value?.refresh?.()]);
  await ensureMapReady();
}

function flyToDevice(item: DeviceLocationInfo) {
  if (!hasLocation(item) || item.longitude == null || item.latitude == null) return;
  selectedId.value = item.id;
  mapRef.value?.flyTo(Number(item.longitude), Number(item.latitude));
}

/**
 * 拉取设备详情后打开弹窗；国标通道在弹窗内 WVP 点播，直连设备预解析流地址。
 */
async function playDeviceInDialog(item: PreviewCamera | DeviceLocationInfo) {
  const seq = ++playSeq;
  playLoadingId.value = item.id;

  try {
    let record = {
      ...(item as DeviceInfo),
      name: item.name || item.id,
    } as DeviceInfo;

    try {
      const res = (await getDeviceInfo(item.id, item.name ? { name: item.name } : undefined)) as
        | DeviceInfo
        | { data?: DeviceInfo };
      record = (res as { data?: DeviceInfo })?.data || (res as DeviceInfo) || record;
    } catch {
      /* 用列表快照兜底 */
    }

    if (seq !== playSeq) return;

    const ok = await openDeviceInDialogPlayer(openPlayerModal, record, { enableAi: true });
    if (seq !== playSeq) return;
    if (!ok) {
      createMessage.warning('该摄像头暂无可播放地址');
    }
  } catch (e) {
    if (seq !== playSeq) return;
    console.error(e);
    createMessage.error('打开监控画面失败');
  } finally {
    if (seq === playSeq) playLoadingId.value = null;
  }
}

function handleSelectDevice(item: DeviceLocationInfo) {
  selectedId.value = item.id;
  if (hasLocation(item) && item.longitude != null && item.latitude != null) {
    mapRef.value?.flyTo(Number(item.longitude), Number(item.latitude));
  }
  void playDeviceInDialog(item);
}

function openPreview(deviceId: string) {
  selectedId.value = deviceId;
  previewId.value = deviceId;
  ptzOpen.value = false;
}

function closePreview() {
  previewId.value = null;
  ptzOpen.value = false;
}

function clearListSelection() {
  selectedId.value = null;
  playLoadingId.value = null;
}

function onMarkerClick(marker: MapMarkerData) {
  if (marker.kind !== 'camera') return;
  selectedId.value = marker.id;
  mapRef.value?.flyTo(marker.lng, marker.lat);
  openPreview(marker.id);
}

function openLocationModal(item: PreviewCamera | DeviceLocationInfo) {
  if (!canSetDeviceLocation(item)) {
    createMessage.warning('该设备不支持单独设置坐标');
    return;
  }
  selectedId.value = item.id;
  const record = deviceList.value.find((d) => d.id === item.id) || item;
  openLocationModalInner(true, {
    deviceId: item.id,
    record,
  });
}

onMounted(async () => {
  await loadDeviceList();
  await mapRef.value?.refresh?.();
  await ensureMapReady();
  window.setTimeout(() => void ensureMapReady(), 200);
});

defineExpose({
  refresh: reloadAll,
  resizeMap: () => void ensureMapReady(),
});
</script>

<style scoped lang="less">
.camera-map-panel {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;

  &__layout {
    flex: 1;
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: flex;
    flex-direction: row;
    background: #fff;
    overflow: hidden;
  }

  &__sider {
    width: 380px;
    flex: 0 0 380px;
    border-right: 1px solid #e5e7eb;
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: #fff;
  }

  &__sider-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 12px 12px 10px;
    flex-shrink: 0;
    background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
    border-bottom: 1px solid #eef0f3;
  }

  &__sider-title {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  &__sider-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: #eff6ff;
    color: #3b82f6;
    flex-shrink: 0;
  }

  &__sider-heading {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  &__sider-name {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    line-height: 1.2;
  }

  &__sider-desc {
    font-size: 12px;
    color: #9ca3af;
    line-height: 1.2;
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    padding: 10px 12px 0;
    flex-shrink: 0;
  }

  &__stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 8px 4px;
    border: 1px solid #eef0f3;
    border-radius: 8px;
    background: #fafbfc;
    cursor: pointer;
    transition: all 0.15s ease;
    color: #6b7280;

    strong {
      font-size: 16px;
      font-weight: 600;
      color: #111827;
      font-variant-numeric: tabular-nums;
      line-height: 1.2;
    }

    span {
      font-size: 12px;
      line-height: 1.2;
    }

    &:hover {
      border-color: #dbeafe;
      background: #f8fbff;
    }

    &.is-active {
      border-color: #93c5fd;
      background: #eff6ff;
      color: #2563eb;

      strong {
        color: #1d4ed8;
      }
    }

    &.is-pending.is-active {
      border-color: #fcd34d;
      background: #fffbeb;
      color: #d97706;

      strong {
        color: #b45309;
      }
    }
  }

  &__search {
    padding: 10px 12px;
    flex-shrink: 0;
  }

  &__list {
    flex: 1;
    min-height: 0;
    overflow: auto;
    padding: 0 8px 8px;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 48px 16px;
    text-align: center;
    color: #9ca3af;

    p {
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
    }
  }

  &__group {
    margin-bottom: 4px;
  }

  &__group-head {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 8px;
    border: 0;
    background: transparent;
    cursor: pointer;
    border-radius: 6px;

    &:hover {
      background: #f9fafb;
    }
  }

  &__group-title {
    flex: 1;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
  }

  &__group-count {
    min-width: 18px;
    height: 18px;
    padding: 0 6px;
    border-radius: 9px;
    background: #f3f4f6;
    color: #6b7280;
    font-size: 11px;
    line-height: 18px;
    text-align: center;
    font-variant-numeric: tabular-nums;
  }

  &__group-body {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #f0f0f0;
    background: #fff;
    transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;

    &:hover {
      border-color: #dbeafe;
      background: #f8fbff;
    }

    &.is-active {
      border-color: #93c5fd;
      background: #eff6ff;
      box-shadow: 0 0 0 1px #bfdbfe inset;
    }

    &.is-loading {
      opacity: 0.72;
      pointer-events: none;
    }
  }

  &__item-body {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    flex: 1;
    min-width: 0;
    cursor: pointer;
  }

  &__dot {
    display: block;
    width: 8px;
    height: 8px;
    margin-top: 5px;
    border-radius: 50%;
    background: #d1d5db;
    flex-shrink: 0;
  }

  &__item.is-online &__dot {
    background: #22c55e;
    box-shadow: 0 0 0 3px #dcfce7;
  }

  &__item-main {
    flex: 1;
    min-width: 0;
  }

  &__item-name {
    font-size: 13px;
    font-weight: 500;
    color: #111827;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__item-meta {
    margin-top: 3px;
    font-size: 12px;
    color: #9ca3af;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__addr {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    color: #2563eb;
  }

  &__id {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 11px;
  }

  &__item-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  &__action-btn {
    height: 28px;
    padding: 0 10px;
    font-size: 12px;
    border-radius: 6px;

    &.is-set {
      min-width: 88px;
    }
  }

  &__action-link {
    height: 28px;
    padding: 0 6px;
    font-size: 12px;
    color: #6b7280;

    &:hover {
      color: #2563eb;
    }
  }

  &__sider-foot {
    padding: 10px 12px;
    border-top: 1px solid #eef0f3;
    background: #fafbfc;
    font-size: 12px;
    color: #9ca3af;
    flex-shrink: 0;
    line-height: 1.4;
  }

  &__content {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
    min-height: 0;
    height: 100%;
    background: #e8edf3;
  }

  &__map-wrap {
    position: relative;
    flex: 1;
    min-height: 0;
    height: 100%;
    overflow: hidden;

    :deep(.device-monitor-map) {
      position: absolute;
      inset: 0;
      height: auto;
      min-height: 0;
      border-radius: 0;

      .ant-card,
      .ant-card-body,
      .ant-spin-nested-loading,
      .ant-spin-container {
        height: 100%;
      }
    }

    :deep(.basic-tianditu-map) {
      position: absolute;
      inset: 0;
      height: auto;
    }
  }

  &__preview {
    position: absolute;
    left: 16px;
    bottom: 16px;
    z-index: 20;
    width: min(360px, calc(100% - 32px));
    padding: 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #e5e7eb;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.16);
    backdrop-filter: blur(8px);
  }

  &__preview-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
  }

  &__preview-title {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    font-size: 13px;
    font-weight: 600;
    color: #111827;

    span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    :deep(.anticon),
    :deep(svg) {
      color: #2563eb;
      flex-shrink: 0;
    }
  }

  &__preview-actions {
    display: flex;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
  }

  &__preview-btn {
    height: 28px;
    padding: 0 8px;
    font-size: 12px;
    color: #6b7280;

    &:hover,
    &.is-active {
      color: #2563eb;
    }
  }

  &__preview-close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: #9ca3af;
    cursor: pointer;

    &:hover {
      background: #f3f4f6;
      color: #111827;
    }
  }

  &__preview :deep(.camera-inline-preview) {
    margin-top: 0;
  }
}

.camera-preview-fade-enter-active,
.camera-preview-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.camera-preview-fade-enter-from,
.camera-preview-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
