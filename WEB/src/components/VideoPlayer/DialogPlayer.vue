<template>
  <BasicModal
    @register="register"
    :title="modalTitle"
    :footer="null"
    :zIndex="10000"
    @cancel="handleCancel"
  >
    <div class="monitor-dialog" :class="{ 'monitor-dialog--vod': state.vodMode }">
      <template v-if="state.vodMode">
        <div class="monitor-dialog__vod-viewer">
          <div class="monitor-dialog__video-body">
            <video
              v-if="state.currentUrl && !state.nativeVodFailed"
              :key="`native-vod-${state.currentUrl}`"
              class="monitor-dialog__native-vod"
              :src="state.currentUrl"
              controls
              autoplay
              playsinline
              preload="metadata"
              @error="handleNativeVodError"
            />
            <Jessibuca
              v-else-if="state.currentUrl"
              :key="`${playerKey}-${state.currentUrl}`"
              ref="jessibucaRef"
              :playUrl="state.currentUrl"
              :hasAudio="false"
              :vodMode="true"
            />
            <div v-else-if="state.playLoading" class="monitor-dialog__loading">
              <Spin size="large" />
              <span>录像加载中...</span>
            </div>
            <div v-else class="monitor-dialog__loading">
              <Icon icon="ant-design:video-camera-outlined" :size="48" />
              <span>暂无播放地址</span>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
      <MonitorControlPanel
        v-if="showControlPanel"
        :talk-protocol="talkProtocol"
        :talk-status="activeTalk.status"
        :talk-info-text="activeTalk.infoText"
        :talk-volume="activeTalk.volume"
        :talk-noise-suppression="activeTalk.noiseSuppression"
        :talk-echo-cancellation="activeTalk.echoCancellation"
        :talk-level="activeTalk.level"
        :show-presets="state.isGb28181 || state.isOnvif"
        :presets="state.presets"
        :preset-loading="state.presetLoading"
        @talk-start="handleStartTalk"
        @talk-stop="handleStopTalk"
        @talk-volume-change="activeTalk.updateVolume"
        @talk-noise-change="(v) => (activeTalk.noiseSuppression = v)"
        @talk-echo-change="(v) => (activeTalk.echoCancellation = v)"
        @ptz="handlePtzCamera"
        @aux="handleAuxControl"
        @preset-call="handlePresetCall"
        @preset-set="handlePresetSet"
        @preset-delete="handlePresetDelete"
        @preset-add="handlePresetAdd"
      />

      <div class="monitor-dialog__main">
        <div class="monitor-dialog__video">
          <div v-if="!state.vodMode" class="monitor-dialog__video-bar">
            <div class="monitor-dialog__video-bar-left">
              <span class="monitor-dialog__live-tag" :class="{ 'is-live': !state.vodMode && state.currentUrl }">
                <span class="monitor-dialog__live-dot" />
                {{ streamLabel }}
              </span>
              <label v-if="showEnableAiToggle" class="monitor-dialog__ai-toggle">
                <Checkbox v-model:checked="enableAi" />
                <span class="monitor-dialog__ai-toggle-text">启用 AI</span>
              </label>
            </div>
            <div class="monitor-dialog__video-bar-right">
              <span class="monitor-dialog__status-chip" :class="playStatusClass">{{ playStatusText }}</span>
            </div>
          </div>
          <div class="monitor-dialog__video-body">
            <Jessibuca
              v-if="state.currentUrl"
              :key="`${playerKey}-${state.currentUrl}`"
              ref="jessibucaRef"
              :playUrl="state.currentUrl"
              :hasAudio="!!talkProtocol"
              :vodMode="state.vodMode"
              :fill-video="!state.vodMode"
              :ai-with-fallback="!state.vodMode && !!state.fallbackUrl"
              @stream-error="handleStreamError"
            />
            <div v-else-if="state.playLoading" class="monitor-dialog__loading">
              <Spin size="large" />
              <span>{{ state.vodMode ? '录像加载中...' : '正在请求点播...' }}</span>
            </div>
            <div v-else class="monitor-dialog__loading">
              <Icon icon="ant-design:video-camera-outlined" :size="48" />
              <span>暂无播放地址</span>
            </div>
          </div>
        </div>
        <div class="monitor-dialog__statusbar">
          <span>{{ state.deviceName || '摄像机' }}</span>
          <span v-if="state.currentUrl">码率 {{ bitrateText }}</span>
        </div>
      </div>
      </template>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, nextTick, reactive, ref, watch } from 'vue';
import { Spin, Checkbox } from 'ant-design-vue';
import { useModalInner } from '@/components/Modal';
import BasicModal from '@/components/Modal/src/BasicModal.vue';
import Jessibuca from '@/components/Player/module/jessibuca.vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { controlPTZ, callOnvifPreset, deleteOnvifPreset, queryOnvifPresets, setOnvifPreset } from '@/api/device/camera';
import {
  addGbPreset,
  callGbPreset,
  controlGbFocus,
  controlGbIris,
  controlGbPtz,
  deleteGbPreset,
  playByDeviceAndChannel,
  queryGbPreset,
} from '@/api/device/gb28181';
import {
  formatCameraDeviceLabel,
  getGb28181PlayIds,
  shouldPlayViaGb28181,
} from '@/views/camera/utils/deviceLabel';
import {
  pickWvpPlayUrl,
  AI_PLAY_FALLBACK_MS,
  isAiStreamPlayUrl,
  isGb28181LivePlaceholderStreamUrl,
  isGb28181PlaceholderStreamUrl,
  pickDirectPlayUrls,
  resolveGbChannelPlayUrls,
  schedulePendingAiStreamUpgrade,
} from '@/views/camera/utils/devicePlay';
import { isVodPlaybackUrl } from '@/utils/alertRecord';
import {
  resolveDeviceTalkProtocol,
  supportsMonitorControl,
  isOnvifDevice,
} from '@/views/camera/utils/deviceTalkProtocol';
import MonitorControlPanel from './monitor/MonitorControlPanel.vue';
import { useOnvifAudioTalk } from './monitor/useOnvifAudioTalk';
import { useGb28181AudioTalk } from './monitor/useGb28181AudioTalk';
import type { PresetItem } from './monitor/MonitorPresetPanel.vue';

const emit = defineEmits<{ cancel: [] }>();

const { createMessage } = useMessage();
const jessibucaRef = ref();
const playerKey = ref(0);
const enableAi = ref(true);
const enableAiReloading = ref(false);

const state = reactive({
  deviceName: '',
  deviceId: '',
  deviceIdentification: '',
  channelId: '',
  presetPos: '',
  currentUrl: '',
  fallbackUrl: null as string | null,
  preferAi: false,
  playLoading: false,
  vodMode: false,
  nativeVodFailed: false,
  isGb28181: false,
  isOnvif: false,
  presets: [] as PresetItem[],
  presetLoading: false,
  record: null as Record<string, any> | null,
});

let aiFallbackTimer: ReturnType<typeof setTimeout> | null = null;

function clearAiFallbackTimer() {
  if (aiFallbackTimer != null) {
    window.clearTimeout(aiFallbackTimer);
    aiFallbackTimer = null;
  }
}

function schedulePendingAiUpgrade(primaryUrl: string, pendingAiUrl: string) {
  schedulePendingAiStreamUpgrade(
    pendingAiUrl,
    primaryUrl,
    () => {
      const ai = pendingAiUrl.trim();
      return state.currentUrl === primaryUrl && state.currentUrl !== ai && !state.vodMode;
    },
    () => {
      state.fallbackUrl = primaryUrl;
      state.preferAi = false;
      state.currentUrl = '';
      void nextTick().then(() => {
        state.currentUrl = pendingAiUrl.trim();
        playerKey.value += 1;
        triggerPlayerFillResize();
      });
    },
  );
}

function scheduleAiFallback(primaryUrl: string) {
  clearAiFallbackTimer();
  const fb = state.fallbackUrl?.trim();
  if (!state.preferAi || !fb || fb === primaryUrl) return;

  aiFallbackTimer = window.setTimeout(() => {
    aiFallbackTimer = null;
    if (state.currentUrl !== primaryUrl) return;
    if (jessibucaRef.value?.playing) return;

    void switchToFallbackUrl(fb);
  }, AI_PLAY_FALLBACK_MS);
}

async function switchToFallbackUrl(url: string) {
  clearAiFallbackTimer();
  state.fallbackUrl = null;
  state.preferAi = false;
  state.currentUrl = '';
  await nextTick();
  state.currentUrl = url;
  playerKey.value += 1;
}

function handleStreamError() {
  const fb = state.fallbackUrl?.trim();
  if (fb && fb !== state.currentUrl && !isGb28181LivePlaceholderStreamUrl(fb)) {
    clearAiFallbackTimer();
    void switchToFallbackUrl(fb);
    return;
  }
  if (state.isGb28181 && state.deviceIdentification && state.presetPos) {
    void startGb28181WvpPlay();
  }
}

async function reloadGb28181Stream() {
  await startGb28181WvpPlay();
}

const talkProtocol = computed(() => resolveDeviceTalkProtocol(state.record));

const onvifTalk = useOnvifAudioTalk(() => state.deviceId);
const gbTalk = useGb28181AudioTalk(
  () => state.deviceIdentification,
  () => state.presetPos || state.channelId,
);

const audioTalk = computed(() => (talkProtocol.value === 'gb28181' ? gbTalk : onvifTalk));
const activeTalk = computed(() => audioTalk.value);

const showControlPanel = computed(() => supportsMonitorControl(state.record, state.vodMode));
const showEnableAiToggle = computed(
  () => !state.vodMode && !!state.record && !enableAiReloading.value,
);
const modalTitle = computed(() => (state.vodMode ? '录像回放' : state.deviceName || '视频监控'));
const streamLabel = computed(() => {
  if (state.vodMode) return '录像回放';
  if (state.isGb28181) return '国标通道';
  if (isAiStreamPlayUrl(state.currentUrl)) return 'AI 预览';
  return '实时预览';
});
const playStatusText = computed(() => {
  if (state.playLoading) return '连接中';
  if (state.currentUrl) return '已连接';
  return '未连接';
});
const playStatusClass = computed(() => {
  if (state.playLoading) return 'is-connecting';
  if (state.currentUrl) return 'is-online';
  return 'is-offline';
});
const bitrateText = ref('— kbps');

async function resolveLivePlayUrls(record: Record<string, any>) {
  const gbIds = getGb28181PlayIds(record);
  if (gbIds || shouldPlayViaGb28181(record)) {
    const sipDeviceId =
      gbIds?.sipDeviceId ?? String(record.deviceIdentification || record.sip_device_id || '').trim();
    const channelId =
      gbIds?.channelId ??
      String(record.channelId || record.presetPos || record.channel_id || '').trim();
    if (!sipDeviceId || !channelId) {
      return { url: null as string | null, fallbackUrl: null as string | null, preferAi: false };
    }
    return resolveGbChannelPlayUrls(sipDeviceId, channelId, {
      enableAi: enableAi.value,
      synced: record,
    });
  }

  return pickDirectPlayUrls(record, enableAi.value);
}

async function applyResolvedStream(
  record: Record<string, any>,
  resolved: {
    url: string | null;
    fallbackUrl?: string | null;
    preferAi?: boolean;
    pendingAiUrl?: string | null;
  },
) {
  if (!resolved.url || isGb28181LivePlaceholderStreamUrl(resolved.url)) {
    createMessage.warning(
      enableAi.value ? '该设备暂无 AI 流或原始流播放地址' : '该设备暂无可播放地址',
    );
    state.currentUrl = '';
    state.fallbackUrl = null;
    state.preferAi = false;
    return;
  }

  state.deviceId = String(record.id ?? state.deviceId);
  state.fallbackUrl = resolved.fallbackUrl?.trim() || null;
  state.preferAi = !!resolved.preferAi;
  state.vodMode = false;
  state.currentUrl = '';
  await nextTick();
  state.currentUrl = resolved.url;
  playerKey.value += 1;
  scheduleAiFallback(resolved.url);
  const pendingAi = resolved.pendingAiUrl?.trim();
  if (pendingAi && pendingAi !== resolved.url) {
    schedulePendingAiUpgrade(resolved.url, pendingAi);
  }
  triggerPlayerFillResize();
}

function triggerPlayerFillResize() {
  const run = () => {
    const inst = jessibucaRef.value?.jessibuca;
    if (!inst || !jessibucaRef.value?.playing) return;
    try {
      inst.setScaleMode?.(0);
      inst.resize?.();
    } catch {
      /* 播放器尚未就绪 */
    }
  };
  nextTick(() => {
    requestAnimationFrame(run);
    window.setTimeout(run, 300);
    window.setTimeout(run, 800);
  });
}

async function reloadStreamForAiToggle() {
  const record = state.record;
  if (!record || state.vodMode) return;

  enableAiReloading.value = true;
  clearAiFallbackTimer();
  state.currentUrl = '';

  try {
    if (state.isGb28181 && state.deviceIdentification && state.presetPos) {
      let pendingAi: string | null = null;
      if (enableAi.value) {
        const resolved = await resolveGbChannelPlayUrls(
          state.deviceIdentification,
          state.presetPos,
          { enableAi: true, synced: record },
        );
        pendingAi = resolved.pendingAiUrl?.trim() || null;
      }
      await startGb28181WvpPlay(pendingAi);
      return;
    }

    state.playLoading = true;
    const resolved = await resolveLivePlayUrls(record);
    await applyResolvedStream(record, resolved);
  } finally {
    state.playLoading = false;
    enableAiReloading.value = false;
  }
}

function handleEnableAiChange() {
  void reloadStreamForAiToggle();
}

let skipEnableAiWatch = false;

watch(enableAi, () => {
  if (skipEnableAiWatch || state.vodMode || !state.record) return;
  handleEnableAiChange();
});

async function startGb28181WvpPlay(pendingAiUrl?: string | null) {
  if (!state.deviceIdentification || !state.presetPos) return;
  state.currentUrl = '';
  state.playLoading = true;
  try {
    const res = await playByDeviceAndChannel(state.deviceIdentification, state.presetPos);
    const streamContent = res?.data?.data ?? res?.data;
    const url = pickWvpPlayUrl(streamContent) || '';
    if (!url || isGb28181LivePlaceholderStreamUrl(url)) {
      createMessage.error(streamContent?.msg || res?.data?.msg || '未获取到播放地址');
      return;
    }
    state.vodMode = false;
    state.fallbackUrl = null;
    state.preferAi = false;
    await nextTick();
    state.currentUrl = url;
    playerKey.value += 1;
    const pending = pendingAiUrl?.trim();
    if (pending && pending !== url && enableAi.value) {
      schedulePendingAiUpgrade(url, pending);
    }
    triggerPlayerFillResize();
  } catch {
    createMessage.error('点播失败，请检查设备连接');
  } finally {
    state.playLoading = false;
  }
}

async function loadStream(record: Record<string, any>) {
  clearAiFallbackTimer();
  state.nativeVodFailed = false;
  state.fallbackUrl = null;
  state.preferAi = false;

  const gbIds = getGb28181PlayIds(record);
  const sipDeviceId = gbIds?.sipDeviceId ?? String(record.deviceIdentification || '').trim();
  const channelId =
    gbIds?.channelId ??
    String(record.channelId || record.presetPos || record.channel_id || '').trim();
  const gbRecord = shouldPlayViaGb28181(record) || record._forceGbWvp === true;

  state.deviceIdentification = gbRecord ? sipDeviceId : '';
  state.channelId = channelId;
  state.presetPos = gbRecord ? channelId : '';
  state.isGb28181 = gbRecord;
  state.isOnvif = gbRecord ? false : isOnvifDevice(record);
  state.deviceId = String(record.id ?? '');

  const recordPendingAi = String(record._pendingAiUrl ?? '').trim() || null;

  // 国标通道：始终 WVP 点播，忽略 record.http_stream 中的 DB 占位地址
  if (gbRecord && sipDeviceId && channelId) {
    await startGb28181WvpPlay(recordPendingAi);
    return;
  }

  const preResolvedUrl = String(record.http_stream ?? '').trim();
  const recordFallback = String(record._fallbackUrl ?? '').trim() || null;
  const recordPreferAi = !!record._preferAi;
  const recordPendingAiNonGb = String(record._pendingAiUrl ?? '').trim() || null;

  if (preResolvedUrl && !isGb28181LivePlaceholderStreamUrl(preResolvedUrl)) {
    state.playLoading = false;
    state.vodMode = record._forceVod === true || isVodPlaybackUrl(preResolvedUrl);
    state.fallbackUrl =
      recordFallback && !isGb28181LivePlaceholderStreamUrl(recordFallback) ? recordFallback : null;
    state.preferAi = recordPreferAi;
    await nextTick();
    state.currentUrl = preResolvedUrl;
    playerKey.value += 1;
    scheduleAiFallback(preResolvedUrl);
    if (recordPendingAiNonGb && recordPendingAiNonGb !== preResolvedUrl) {
      schedulePendingAiUpgrade(preResolvedUrl, recordPendingAiNonGb);
    }
    triggerPlayerFillResize();
    return;
  }

  state.deviceId = String(record.id ?? '');
  const streamUrl = String(record.http_stream ?? '').trim();
  if (!streamUrl && record._pendingRecord) {
    state.currentUrl = '';
    state.vodMode = false;
    state.playLoading = true;
    return;
  }

  if (!streamUrl || isGb28181LivePlaceholderStreamUrl(streamUrl)) {
    state.playLoading = false;
    state.currentUrl = '';
    return;
  }

  state.playLoading = false;
  state.vodMode = record._forceVod === true || isVodPlaybackUrl(streamUrl);
  await nextTick();
  state.currentUrl = streamUrl;
  playerKey.value += 1;
}

function handleNativeVodError() {
  // Chrome/Safari cannot decode FLV natively.  Keep the existing Jessibuca
  // decoder as a transparent fallback while MP4/WebM use native Range/VOD.
  state.nativeVodFailed = true;
  playerKey.value += 1;
}

async function loadOnvifPresets() {
  if (!state.isOnvif || !state.deviceId) return;
  state.presetLoading = true;
  try {
    const res: any = await queryOnvifPresets(state.deviceId);
    const body = res?.data ?? res;
    const list = body?.data ?? body?.list ?? body;
    const items = Array.isArray(list) ? list : [];
    state.presets = items.map((item: any, idx: number) => ({
      id: String(item.token ?? item.preset_token ?? idx + 1),
      name: item.name ?? `预置点 ${idx + 1}`,
    }));
  } catch {
    state.presets = [];
  } finally {
    state.presetLoading = false;
  }
}

async function loadPresets() {
  if (state.isGb28181) {
    await loadGbPresets();
  } else if (state.isOnvif) {
    await loadOnvifPresets();
  }
}

async function loadGbPresets() {
  if (!state.isGb28181 || !state.deviceIdentification || !state.presetPos) return;
  state.presetLoading = true;
  try {
    const res: any = await queryGbPreset(state.deviceIdentification, state.presetPos);
    const body = res?.data ?? res;
    const list = body?.data ?? body?.list ?? body;
    const items = Array.isArray(list) ? list : [];
    state.presets = items.map((item: any, idx: number) => ({
      id: Number(item.presetId ?? item.id ?? idx + 1),
      name: item.presetName ?? item.name ?? `预置点 ${item.presetId ?? idx + 1}`,
    }));
  } catch {
    state.presets = Array.from({ length: 0 });
  } finally {
    state.presetLoading = false;
  }
}

async function handleStopTalk() {
  await audioTalk.value.stop();
}

async function handleStartTalk() {
  await audioTalk.value.start();
}

const [register, { closeModal, setModalProps }] = useModalInner((record) => {
  void handleModalOpen(record);
});

async function handleModalOpen(record: Record<string, any>) {
  const vod = record._forceVod === true || isVodPlaybackUrl(String(record.http_stream ?? ''));
  skipEnableAiWatch = true;
  enableAi.value = record._enableAi !== false;
  state.record = record;
  state.deviceName = formatCameraDeviceLabel(record);
  state.vodMode = vod;
  state.nativeVodFailed = false;
  state.presets = [];
  applyModalLayout(vod);

  await handleStopTalk();
  await loadStream(record);
  skipEnableAiWatch = false;
  if (talkProtocol.value === 'onvif') {
    await onvifTalk.checkCapabilities();
  }
  await loadPresets();
}

function applyModalLayout(vodMode: boolean) {
  if (vodMode) {
    setModalProps({
      defaultFullscreen: false,
      canFullscreen: false,
      width: 1000,
      title: '录像回放',
      minHeight: 0,
      bodyStyle: { padding: 0 },
      wrapClassName: 'monitor-dialog-wrap monitor-dialog-wrap--vod',
    });
    return;
  }
  setModalProps({
    defaultFullscreen: true,
    canFullscreen: true,
    draggable: false,
    useWrapper: false,
    width: 'min(1280px, 96vw)',
    title: state.deviceName || '视频监控',
    minHeight: 0,
    bodyStyle: { padding: 0, height: '100%', overflow: 'hidden' },
    wrapClassName: 'monitor-dialog-wrap monitor-dialog-wrap--live',
  });
}

async function handlePresetAdd() {
  if (state.isOnvif) {
    const name = `预置点 ${state.presets.length + 1}`;
    try {
      await setOnvifPreset(state.deviceId, { name });
      createMessage.success(`${name} 已添加`);
      await loadOnvifPresets();
    } catch {
      createMessage.error('添加预置点失败');
    }
    return;
  }
  const lastId = Number(state.presets[state.presets.length - 1]?.id ?? 0);
  const nextId = lastId + 1;
  if (nextId > 255) {
    createMessage.warning('预置点编号已达上限');
    return;
  }
  handlePresetSet(nextId);
}

const gbCommandMap: Record<string, string> = {
  UP: 'up',
  DOWN: 'down',
  LEFT: 'left',
  RIGHT: 'right',
  LEFT_UP: 'upleft',
  RIGHT_UP: 'upright',
  LEFT_DOWN: 'downleft',
  RIGHT_DOWN: 'downright',
  ZOOM_IN: 'zoomin',
  ZOOM_OUT: 'zoomout',
  STOP: 'stop',
};

async function handlePtzCamera(command: string, speed: number) {
  if (state.deviceIdentification && state.presetPos) {
    const gbCommand = gbCommandMap[command];
    if (!gbCommand) return;
    await controlGbPtz(state.deviceIdentification, state.presetPos, {
      command: gbCommand,
      horizonSpeed: ['LEFT', 'RIGHT', 'LEFT_UP', 'RIGHT_UP', 'LEFT_DOWN', 'RIGHT_DOWN'].includes(command)
        ? speed
        : 0,
      verticalSpeed: ['UP', 'DOWN', 'LEFT_UP', 'RIGHT_UP', 'LEFT_DOWN', 'RIGHT_DOWN'].includes(command)
        ? speed
        : 0,
      zoomSpeed: ['ZOOM_IN', 'ZOOM_OUT'].includes(command)
        ? Math.min(Math.max(Math.round(speed / 10), 1), 15)
        : 0,
    });
    return;
  }

  const directionMap: Record<string, { x: number; y: number; z: number }> = {
    UP: { x: 0, y: speed, z: 0 },
    DOWN: { x: 0, y: -speed, z: 0 },
    LEFT: { x: -speed, y: 0, z: 0 },
    RIGHT: { x: speed, y: 0, z: 0 },
    ZOOM_IN: { x: 0, y: 0, z: speed },
    ZOOM_OUT: { x: 0, y: 0, z: -speed },
  };
  if (command === 'STOP') {
    controlPTZ(state.deviceId, { x: 0, y: 0, z: 0 });
  } else if (directionMap[command]) {
    controlPTZ(state.deviceId, directionMap[command]);
  }
}

async function handleAuxControl(type: 'focus' | 'iris', action: 'in' | 'out' | 'stop') {
  if (!state.isGb28181 || !state.deviceIdentification || !state.presetPos) return;
  if (type === 'focus') {
    const cmd = action === 'in' ? 'near' : action === 'out' ? 'far' : 'stop';
    await controlGbFocus(state.deviceIdentification, state.presetPos, cmd);
  } else {
    const cmd = action === 'stop' ? 'stop' : action;
    await controlGbIris(state.deviceIdentification, state.presetPos, cmd);
  }
}

async function handlePresetCall(id: string | number) {
  if (state.isOnvif) {
    await callOnvifPreset(state.deviceId, String(id));
    return;
  }
  if (!state.deviceIdentification || !state.presetPos) return;
  await callGbPreset(state.deviceIdentification, state.presetPos, Number(id));
}

async function handlePresetSet(id: string | number) {
  if (state.isOnvif) {
    const preset = state.presets.find((p) => p.id === id);
    const name = preset?.name ?? `预置点 ${id}`;
    try {
      await setOnvifPreset(state.deviceId, {
        name,
        preset_token: String(id),
      });
      createMessage.success(`${name} 已更新`);
      await loadOnvifPresets();
    } catch {
      createMessage.error('设置预置点失败');
    }
    return;
  }
  if (!state.deviceIdentification || !state.presetPos) return;
  await addGbPreset(state.deviceIdentification, state.presetPos, Number(id));
  createMessage.success(`预置点 ${id} 已设置`);
  await loadGbPresets();
}

async function handlePresetDelete(id: string | number) {
  if (state.isOnvif) {
    try {
      await deleteOnvifPreset(state.deviceId, String(id));
      createMessage.success('预置点已删除');
      await loadOnvifPresets();
    } catch {
      createMessage.error('删除预置点失败');
    }
    return;
  }
  if (!state.deviceIdentification || !state.presetPos) return;
  await deleteGbPreset(state.deviceIdentification, state.presetPos, Number(id));
  createMessage.success(`预置点 ${id} 已删除`);
  await loadGbPresets();
}

function handleCancel() {
  clearAiFallbackTimer();
  handleStopTalk();
  state.currentUrl = '';
  state.fallbackUrl = null;
  state.preferAi = false;
  state.playLoading = false;
  state.vodMode = false;
  state.record = null;
  closeModal();
  emit('cancel');
}
</script>

<style lang="less">
.monitor-dialog-wrap {
  .ant-modal-body {
    padding: 0 !important;
  }

  &.fullscreen-modal {
    padding: 22px !important;
    box-sizing: border-box !important;
    overflow: hidden !important;

    .ant-modal {
      position: relative !important;
      top: 0 !important;
      left: 0 !important;
      right: auto !important;
      bottom: auto !important;
      inset: auto !important;
      width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      margin: 0 !important;
      padding-bottom: 0 !important;
      transform: none !important;
      border-radius: 10px;
      overflow: hidden;
    }

    .ant-modal-content {
      height: 100%;
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .ant-modal-header {
      flex-shrink: 0;
    }

    .ant-modal-body {
      flex: 1;
      min-height: 0;
      overflow: hidden !important;
      display: flex;
      flex-direction: column;
    }

    .ant-modal-body > .scrollbar,
    .ant-modal-body .scrollbar__wrap,
    .ant-modal-body .scroll-container,
    .ant-modal-body .scrollbar__view,
    .ant-modal-body .ant-spin-nested-loading,
    .ant-modal-body .ant-spin-container {
      height: 100% !important;
      max-height: 100% !important;
      min-height: 0 !important;
    }

    .ant-modal-body .scroll-container .scrollbar__wrap {
      margin-bottom: 0 !important;
      overflow: hidden !important;
    }

    .ant-modal-body .ant-spin-container > div {
      height: 100% !important;
      max-height: 100% !important;
      min-height: 0 !important;
    }
  }

  &.monitor-dialog-wrap--live.fullscreen-modal {
    .ant-modal-body {
      display: flex !important;
      flex-direction: column !important;
      overflow: hidden !important;
    }

    .ant-modal-body > .ant-spin-nested-loading,
    .ant-modal-body .ant-spin-container {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .modal-wrapper__body {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }

    .monitor-dialog {
      flex: 1;
      height: auto !important;
      min-height: 0 !important;
      max-height: 100% !important;
      overflow: hidden;
    }

    .monitor-control {
      height: 100%;
      max-height: 100%;
      min-height: 0;
      overflow-x: hidden;
      overflow-y: auto;
    }

    .monitor-dialog__main {
      flex: 1;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .monitor-dialog__video {
      flex: 1;
      min-height: 0;
    }
  }

  &.fullscreen-modal .monitor-dialog {
    height: 100%;
    min-height: 0;
    max-height: 100%;
  }

  .ant-modal-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
  }

  .ant-modal-title {
    font-size: 15px;
    font-weight: 600;
  }

  .monitor-ptz {
    .ant-slider-track {
      background-color: #3b6cf5;
    }

    .ant-slider-handle::after {
      box-shadow: 0 0 0 2px #3b6cf5;
    }
  }

  .audio-talk {
    .ant-slider-track {
      background-color: #3b6cf5;
    }

    .ant-slider-handle::after {
      box-shadow: 0 0 0 2px #3b6cf5;
    }
  }
}

.monitor-dialog-wrap--vod {
  .ant-modal-content {
    padding: 0 !important;
    background: #000;
  }

  .ant-modal-body {
    padding: 0 !important;
    background: #000;
  }

  .ant-modal-body > .scrollbar {
    padding: 0 !important;
  }

  .ant-modal-body .scrollbar__wrap {
    margin: 0 !important;
  }

  .ant-modal-body .scroll-container {
    padding: 0 !important;
  }

  .monitor-dialog--vod {
    display: block;
    height: auto;
    min-height: 0;
    background: #000;
    line-height: 0;
  }

  .monitor-dialog__vod-viewer {
    padding: 0;
    margin: 0;
    background: #000;
  }

  .monitor-dialog__vod-viewer .monitor-dialog__video-body {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    max-height: 70vh;
    height: auto;
    margin: 0;
    padding: 0;
    background: #000;
    border-radius: 0;
    overflow: hidden;
    line-height: 0;

    > .jessibuca-root,
    > div {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      line-height: normal;
    }

    .jessibuca-container {
      width: 100% !important;
      height: 100% !important;
    }
  }
}

.monitor-dialog {
  display: flex;
  height: min(72vh, 640px);
  min-height: 420px;
  max-height: 100%;
  overflow: hidden;
  background: #f1f5f9;
}

.monitor-dialog__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #0a0f1a;
}

.monitor-dialog__video {
  flex: 1;
  min-height: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  background: #000;
}

.monitor-dialog__video-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
  padding: 0 14px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(15, 23, 42, 0.88));
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.monitor-dialog__video-bar-left,
.monitor-dialog__video-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.monitor-dialog__live-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  white-space: nowrap;
  line-height: 1;

  &.is-live {
    background: rgba(59, 108, 245, 0.18);
    color: #93bbfd;
  }
}

.monitor-dialog__live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #64748b;
  flex-shrink: 0;

  .is-live & {
    background: #5b8df7;
    box-shadow: 0 0 0 3px rgba(91, 141, 247, 0.28);
  }
}

.monitor-dialog__status-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  white-space: nowrap;
  line-height: 1.2;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.72);

  &.is-online {
    background: rgba(59, 108, 245, 0.2);
    color: #93bbfd;
  }

  &.is-connecting {
    background: rgba(245, 158, 11, 0.18);
    color: #fcd34d;
  }

  &.is-offline {
    background: rgba(148, 163, 184, 0.16);
    color: #cbd5e1;
  }
}

.monitor-dialog__video-body {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  background: #000;

  > .monitor-dialog__native-vod,
  > .jessibuca-root,
  > .monitor-dialog__loading {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }

  > .monitor-dialog__native-vod {
    display: block;
    object-fit: contain;
    background: #000;
  }

  :deep(.jessibuca-container) {
    width: 100% !important;
    height: 100% !important;
  }
}

.monitor-dialog__ai-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  cursor: pointer;

  :deep(.ant-checkbox-wrapper) {
    margin-inline-end: 0;
    line-height: 1;
  }

  :deep(.ant-checkbox .ant-checkbox-inner) {
    background-color: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.45);
  }

  :deep(.ant-checkbox-checked .ant-checkbox-inner) {
    background-color: #3b6cf5;
    border-color: #3b6cf5;
  }
}

.monitor-dialog__ai-toggle-text {
  color: #fff;
  font-size: 12px;
  line-height: 1;
  white-space: nowrap;
  user-select: none;
}

.monitor-dialog__loading {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
}

.monitor-dialog__statusbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 14px;
  background: rgba(15, 23, 42, 0.96);
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);

  span:first-child {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  span:last-child {
    flex-shrink: 0;
    white-space: nowrap;
  }
}
</style>
