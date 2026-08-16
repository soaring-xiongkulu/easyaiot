<template>
  <div class="video-monitor" :class="{ 'preset-panel-open': presetPanelOpen }">
    <div class="monitor-header" :class="{ 'panel-open': presetPanelOpen }">
      <div class="header-title">实时监控</div>
      <div class="enable-ai-wrap">
        <a-checkbox v-model:checked="enableAi">启用 AI</a-checkbox>
      </div>
      <div class="header-time">{{ currentTime }}</div>
      <div class="header-location">{{ currentLocation }}</div>
      <div class="header-toolbar">
        <!-- 分屏切换 -->
        <div class="split-toolbar">
          <div
            v-for="layout in splitLayouts"
            :key="layout.value"
            :class="['split-btn', { active: currentLayout === layout.value }]"
            :title="layout.label"
            @click="switchLayout(layout.value)"
          >
            {{ layout.label }}
          </div>
        </div>
        <!-- 布局方案入口 -->
        <div
          :class="['toolbar-trigger', 'layout-preset-trigger', { open: presetPanelOpen, 'has-active': !!activePresetId }]"
          @click="presetPanelOpen = !presetPanelOpen"
        >
          <Icon icon="ant-design:layout-outlined" :size="15" />
          <span class="trigger-label">布局方案</span>
          <span v-if="activePresetSummary" class="trigger-badge">{{ activePresetSummary }}</span>
          <Icon :icon="presetPanelOpen ? 'ant-design:up-outlined' : 'ant-design:down-outlined'" :size="12" />
        </div>
      </div>
      <LayoutPresetPanel
        :open="presetPanelOpen"
        :presets="layoutPresets"
        :active-preset-id="activePresetId"
        :current-layout="currentLayout"
        :current-camera-count="currentCameraCount"
        :can-save-current="canSaveCurrentLayout"
        @close="presetPanelOpen = false"
        @apply="handleApplyPreset"
        @save="handleSavePreset"
        @delete="handleDeletePreset"
      />
    </div>

    <div v-if="presetPanelOpen" class="preset-panel-backdrop" @click="presetPanelOpen = false"></div>

    <div class="monitor-content" :class="`layout-${currentLayout}`">
      <!-- 根据当前布局渲染视频窗口 -->
      <div
        v-for="(video, index) in displayVideos"
        :key="`slot-${index}`"
        :class="[
          'video-window',
          getVideoClass(index),
          {
            'drag-over': dragOverIndex === index,
            'is-dragging': dragSourceIndex === index,
          },
        ]"
        @click="handleVideoClick(index)"
        @contextmenu.prevent="removeVideoAtIndex(index)"
        @dragover.prevent="handleDragOver(index)"
        @dragleave="handleDragLeave(index)"
        @drop.prevent="handleDrop(index)"
      >
        <div class="video-container">
          <div v-if="!video.url" class="video-placeholder">
            <img src="@/assets/images/bigscreen/camera-icon.svg" alt="摄像头" class="camera-icon" />
            <div class="placeholder-text">{{ displayVideoName(video, index) }}</div>
          </div>
          <Jessibuca
            v-else
            :key="`player-${index}-${video.deviceId || video.url}`"
            :playUrl="video.url"
            :hasAudio="false"
            :fill-video="true"
            :multi-view="getMaxVideoCount(currentLayout) > 1"
            :ai-with-fallback="!!video.fallbackUrl"
            :ref="el => setVideoRef(el, index)"
            class="video-player"
            @stream-error="handleStreamError(index)"
          />
          <div
            class="drag-zone"
            draggable="true"
            title="拖拽到目标通道交换位置"
            @dragstart="handleDragStart(index, $event)"
            @dragend="handleDragEnd"
          />
          <button
            v-if="hasVideoContent(video)"
            type="button"
            class="video-close-btn"
            title="移除通道"
            @click.stop="removeVideoAtIndex(index)"
          >
            <Icon icon="ant-design:close-outlined" :size="14" />
          </button>
          <div class="video-label" :title="displayVideoName(video, index)">
            {{ displayVideoName(video, index) }}
          </div>
          <div v-if="index === activeVideoIndex" class="video-active-indicator"></div>
        </div>
      </div>
    </div>
    
    <!-- 告警录像列表 -->
    <div class="alert-record-list">
      <div class="alert-record-header">
        <span class="header-title">告警录像</span>
        <span class="header-count">共 {{ alertRecordList.length }} 条</span>
      </div>
      <div class="alert-record-wrapper">
        <!-- 左滑动按钮 -->
        <div
          v-if="canScrollLeft"
          class="scroll-btn scroll-btn-left"
          @click="scrollLeft"
        >
          <Icon icon="ant-design:left-outlined" :size="20" />
        </div>
        <!-- 右滑动按钮 -->
        <div
          v-if="canScrollRight"
          class="scroll-btn scroll-btn-right"
          @click="scrollRight"
        >
          <Icon icon="ant-design:right-outlined" :size="20" />
        </div>
        <div
          ref="scrollContainerRef"
          class="alert-record-scroll"
          @scroll="handleScroll"
        >
          <div
            v-for="(record, index) in alertRecordList"
            :key="record.id || index"
            class="alert-record-item"
            @click="handleRecordClick(record)"
          >
            <div class="record-info">
              <div class="record-title">{{ formatAlertListTitle(record) }}</div>
              <div class="record-meta">
                <span class="record-device">{{ record.device_name || record.device_id || '未知设备' }}</span>
                <span class="record-time">{{ formatTime(record.time) }}</span>
                <Icon icon="ant-design:play-circle-outlined" :size="20" class="play-icon" />
              </div>
            </div>
          </div>
          <div v-if="alertRecordList.length === 0" class="empty-records">
            <Icon icon="ant-design:inbox-outlined" :size="32" />
            <span>暂无告警录像</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="boxfoot"></div>
    
    <!-- 视频播放器弹窗 -->
    <DialogPlayer @register="registerPlayerModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Checkbox as ACheckbox } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import { queryAlarmList } from '@/api/device/calculate'
import { playAlertRecordInModal } from '@/utils/alertRecordPlayback'
import { useMessage } from '@/hooks/web/useMessage'
import Jessibuca from '@/components/Player/module/jessibuca.vue'
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue'
import LayoutPresetPanel from './LayoutPresetPanel.vue'
import { useModal } from '@/components/Modal'
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage'
import { formatAlertListTitle, isSnapAlertTask } from '@/views/alert/alertDisplay'
import { formatCameraDeviceLabel, formatCameraShortName, isGb28181Device } from '@/views/camera/utils/deviceLabel'
import {
  AI_PLAY_FALLBACK_MS,
  AI_STREAM_PROBE_MULTI_VIEW_MS,
  pickDirectPlayUrls,
  resolveGbChannelPlayUrls,
  schedulePendingAiStreamUpgrade,
  isAiStreamPlayUrl,
  toMultiViewPlayUrl,
} from '@/views/camera/utils/devicePlay'
import { parseGbChannelKey } from '@/views/camera/utils/gb28181Tree'
import type { MonitorTreeDeviceNode } from '@/api/device/camera'
import {
  MAX_MONITOR_LAYOUT_PRESETS,
  loadMonitorLayoutStorage,
  saveMonitorLayoutStorage,
  serializeDeviceSnapshot,
  type MonitorLayoutPreset,
  type MonitorLayoutSlot,
} from '../utils/monitorLayoutStorage'

/** 多分屏同时起播并发上限，避免后几路卡在「疯狂加载中」 */
const MULTI_VIEW_PLAY_CONCURRENCY = 2

async function runWithConcurrency<T>(
  items: T[],
  concurrency: number,
  worker: (item: T, index: number) => Promise<void>,
  staggerMs = 220,
): Promise<void> {
  if (!items.length) return
  const limit = Math.max(1, Math.min(concurrency, items.length))
  let cursor = 0
  const runOne = async () => {
    while (cursor < items.length) {
      const index = cursor++
      await worker(items[index]!, index)
      if (staggerMs > 0 && cursor < items.length) {
        await new Promise((r) => window.setTimeout(r, staggerMs))
      }
    }
  }
  await Promise.all(Array.from({ length: limit }, () => runOne()))
}

const playStartQueue: Array<() => Promise<void>> = []
let playStartActive = 0

function enqueuePlayStart<T>(job: () => Promise<T>): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    playStartQueue.push(async () => {
      try {
        resolve(await job())
      } catch (e) {
        reject(e)
      }
    })
    drainPlayStartQueue()
  })
}

function drainPlayStartQueue() {
  while (playStartActive < MULTI_VIEW_PLAY_CONCURRENCY && playStartQueue.length) {
    const next = playStartQueue.shift()
    if (!next) return
    playStartActive += 1
    void next().finally(() => {
      playStartActive -= 1
      drainPlayStartQueue()
    })
  }
}

function isMultiViewLayout(): boolean {
  return getMaxVideoCount(currentLayout.value) > 1
}

function shouldEnableAiForPlay(): boolean {
  return enableAi.value
}

/** 与 monitor/index.vue 中 MONITOR_OVERLAY_Z_INDEX 保持一致 */
const MONITOR_OVERLAY_Z_INDEX = 10050

defineOptions({
  name: 'VideoMonitor'
})

const props = defineProps<{
  device?: any
  videoList?: any[]
}>()

const emit = defineEmits<{
  'video-list-change': [videos: any[]]
}>()

const { createMessage, createConfirm } = useMessage()

// 播放器弹窗
const [registerPlayerModal, { openModal: openPlayerModal, closeModal: closePlayerModal, setModalProps: setPlayerModalProps }] = useModal()

const currentTime = ref('')
const activeVideoIndex = ref(0)
const dragSourceIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const currentLayout = ref('1')
/** 勾选后点播 AI 流；默认开，先播 /live 原始流，AI 就绪后无感升级，失败则快速回退 */
/** 勾选后点播 AI 流（检测框由算法任务烧录）；默认关，避免多分屏误探 /ai 占满连接 */
const enableAi = ref(true)
const videoRefs = ref<(InstanceType<typeof Jessibuca> | null)[]>([])
const alertRecordList = ref<any[]>([])
const loadingRecords = ref(false)
const scrollContainerRef = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const internalVideoList = ref<any[]>([])
const skipDefaultVideoInit = ref(false)
const layoutPresets = ref<Record<number, MonitorLayoutPreset>>({})
const activePresetId = ref<number | null>(null)
const isRestoringLayout = ref(false)
const presetPanelOpen = ref(false)

function displayVideoName(video: { name?: string }, index: number) {
  const shortName = formatCameraShortName(video?.name)
  return shortName || `视频${index + 1}`
}

function getPresetDisplayName(preset: MonitorLayoutPreset | undefined, id: number) {
  if (!preset) return `方案 ${id}`
  return preset.name?.trim() || `方案 ${id}`
}

const currentCameraCount = computed(() =>
  internalVideoList.value.filter((v) => v?.deviceId).length,
)

const canSaveCurrentLayout = computed(() => currentCameraCount.value > 0)

const activePresetSummary = computed(() => {
  if (!activePresetId.value) return ''
  const preset = layoutPresets.value[activePresetId.value]
  if (!preset) return `方案 ${activePresetId.value}`
  const count = preset.slots.filter((s) => s.deviceId).length
  return `${getPresetDisplayName(preset, activePresetId.value)} · ${count}路`
})

function initLayoutPresetsFromStorage() {
  const storage = loadMonitorLayoutStorage()
  const presets: Record<number, MonitorLayoutPreset> = {}
  for (const [key, preset] of Object.entries(storage.presets)) {
    const id = Number(key)
    if (id >= 1 && id <= MAX_MONITOR_LAYOUT_PRESETS) {
      presets[id] = preset
    }
  }
  layoutPresets.value = presets
  activePresetId.value = storage.activePresetId
}

function persistLayoutPresets() {
  const presets: Record<string, MonitorLayoutPreset> = {}
  for (const [key, preset] of Object.entries(layoutPresets.value)) {
    presets[String(key)] = preset
  }
  saveMonitorLayoutStorage({
    presets,
    activePresetId: activePresetId.value,
  })
}

function saveToLayoutPreset(presetId: number, options?: { keepName?: boolean }) {
  if (!canSaveCurrentLayout.value) {
    createMessage.warning('当前没有已选摄像头，无法保存布局')
    return false
  }

  const existing = layoutPresets.value[presetId]
  const preset: MonitorLayoutPreset = {
    id: presetId,
    name: options?.keepName !== false && existing?.name ? existing.name : undefined,
    layout: currentLayout.value,
    enableAi: enableAi.value,
    slots: buildCurrentLayoutSlots(),
    updatedAt: Date.now(),
  }
  layoutPresets.value = { ...layoutPresets.value, [presetId]: preset }
  activePresetId.value = presetId
  persistLayoutPresets()
  createMessage.success(`已保存到${getPresetDisplayName(preset, presetId)}`)
  return true
}

function buildCurrentLayoutSlots(): MonitorLayoutSlot[] {
  const maxCount = getMaxVideoCount(currentLayout.value)
  const slots: MonitorLayoutSlot[] = []
  for (let i = 0; i < maxCount; i++) {
    const video = internalVideoList.value[i]
    if (video?.deviceId) {
      slots.push({
        deviceId: video.deviceId,
        name: video.name || `视频${i + 1}`,
        location: video.location || '',
        device: serializeDeviceSnapshot(video.device),
      })
    } else {
      slots.push({
        deviceId: '',
        name: video?.name || `视频${i + 1}`,
      })
    }
  }
  return slots
}

function applyPresetStructure(preset: MonitorLayoutPreset) {
  skipDefaultVideoInit.value = true
  currentLayout.value = normalizeSplitLayout(preset.layout)
  enableAi.value = preset.enableAi
  activeVideoIndex.value = 0

  const maxCount = getMaxVideoCount(currentLayout.value)
  internalVideoList.value = []
  for (let i = 0; i < maxCount; i++) {
    const saved = preset.slots[i]
    if (saved?.deviceId) {
      internalVideoList.value.push({
        id: `video-${saved.deviceId}-${i}`,
        url: '',
        name: saved.name,
        deviceId: saved.deviceId,
        location: saved.location || '',
        device: saved.device,
        pendingRestore: true,
      })
    } else {
      internalVideoList.value.push({
        id: `placeholder-${i}`,
        url: '',
        name: saved?.name || `视频${i + 1}`,
      })
    }
  }
}

async function playSavedSlot(index: number, saved: MonitorLayoutSlot) {
  const playId = saved.deviceId
  if (!playId) return

  if (playId.startsWith('gb_ch_')) {
    const gb = parseGbChannelKey(playId)
    if (!gb) return
    const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolveGbChannelPlayUrls(
      gb.sipDeviceId,
      gb.channelId,
      { enableAi: shouldEnableAiForPlay(), synced: saved.device },
    )
    if (!url) {
      createMessage.warn(`方案恢复失败：${saved.name}`)
      return
    }
    await startPlayAtScreen(index, {
      id: `video-${playId}-${index}`,
      name: saved.name,
      url,
      deviceId: playId,
      location: saved.location,
      device: saved.device,
      fallbackUrl,
      preferAi,
      pendingAiUrl,
    })
    return
  }

  const dev = saved.device
  if (!dev) {
    createMessage.warn(`方案恢复失败：${saved.name}（缺少设备信息）`)
    return
  }
  const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolvePlayUrlsForDevice(dev)
  if (!url) {
    createMessage.warn(`方案恢复失败：${saved.name}`)
    return
  }
  await startPlayAtScreen(index, {
    id: `video-${playId}-${index}`,
    name: saved.name,
    url,
    deviceId: playId,
    location: saved.location,
    device: dev,
    fallbackUrl,
    preferAi,
    pendingAiUrl,
  })
}

async function restorePendingVideos() {
  if (isRestoringLayout.value) return
  isRestoringLayout.value = true
  try {
    const pending: Array<{ idx: number; slot: MonitorLayoutSlot }> = []
    internalVideoList.value.forEach((slot, idx) => {
      if (!slot?.pendingRestore || !slot.deviceId) return
      pending.push({
        idx,
        slot: {
          deviceId: slot.deviceId,
          name: slot.name,
          location: slot.location,
          device: slot.device,
        },
      })
    })
    const maxCount = getMaxVideoCount(currentLayout.value)
    await runWithConcurrency(
      pending,
      MULTI_VIEW_PLAY_CONCURRENCY,
      async ({ idx, slot }) => {
        await playSavedSlot(idx, slot).finally(() => {
          const current = internalVideoList.value[idx]
          if (current) current.pendingRestore = false
        })
      },
    )
  } finally {
    isRestoringLayout.value = false
  }
}

async function activateLayoutPreset(presetId: number) {
  const preset = layoutPresets.value[presetId]
  if (!preset) return

  videoRefs.value.forEach((ref) => {
    if (ref) {
      ref._unmounting = true
    }
  })
  videoRefs.value = []
  aiFallbackTimers.forEach((id) => window.clearTimeout(id))
  aiFallbackTimers.clear()

  activePresetId.value = presetId
  persistLayoutPresets()
  applyPresetStructure(preset)
  await nextTick()
  await restorePendingVideos()
}

async function handleApplyPreset(presetId: number) {
  await activateLayoutPreset(presetId)
  presetPanelOpen.value = false
}

function handleSavePreset(presetId: number) {
  saveToLayoutPreset(presetId)
}

function handleDeletePreset(presetId: number) {
  const preset = layoutPresets.value[presetId]
  if (!preset) return
  const label = getPresetDisplayName(preset, presetId)
  createConfirm({
    iconType: 'warning',
    title: '删除布局方案',
    content: `确定删除「${label}」吗？删除后无法恢复。`,
    zIndex: MONITOR_OVERLAY_Z_INDEX,
    onOk: () => {
      const next = { ...layoutPresets.value }
      delete next[presetId]
      layoutPresets.value = next
      if (activePresetId.value === presetId) {
        activePresetId.value = null
      }
      persistLayoutPresets()
      createMessage.success('已删除布局方案')
    },
  })
}

initLayoutPresetsFromStorage()

// 防重复提示：记录最近提示的时间和内容
let lastVideoErrorTime = 0
let lastVideoErrorMsg = ''

// 获取录像播放地址（参考录像空间的处理方式）
const getVideoUrl = (videoUrl: string): string => {
  if (!videoUrl) return ''
  // 如果是完整URL，直接返回
  if (videoUrl.startsWith('http://') || videoUrl.startsWith('https://')) {
    return videoUrl
  }
  // 如果是相对路径（以/api/v1/buckets开头），添加前端启动地址前缀
  if (videoUrl.startsWith('/api/v1/buckets')) {
    return `${window.location.origin}${videoUrl}`
  }
  // 其他相对路径，拼接API前缀
  if (videoUrl.startsWith('/')) {
    return `${import.meta.env.VITE_GLOB_API_URL || ''}${videoUrl}`
  }
  // 其他情况直接返回
  return videoUrl
}

// 防重复提示函数：3秒内相同错误只提示一次
function showVideoErrorOnce(message: string) {
  const now = Date.now()
  // 如果3秒内提示过相同内容，则不再提示
  if (now - lastVideoErrorTime < 3000 && lastVideoErrorMsg === message) {
    return
  }
  lastVideoErrorTime = now
  lastVideoErrorMsg = message
  createMessage.warn(message)
}

// 分屏布局配置
const splitLayouts = [
  { value: '1', label: '1分屏' },
  { value: '4', label: '4分屏' },
  { value: '9', label: '9分屏' },
  { value: '16', label: '16分屏' }
]

function normalizeSplitLayout(layout: string) {
  if (splitLayouts.some((item) => item.value === layout)) return layout
  const count = parseInt(layout) || 1
  if (count <= 1) return '1'
  if (count <= 4) return '4'
  if (count <= 9) return '9'
  return '16'
}

// 设置视频引用
const setVideoRef = (el: any, index: number) => {
  if (el) {
    videoRefs.value[index] = el
  }
}

// 获取当前布局需要的最大视频数量
const getMaxVideoCount = (layout: string) => {
  const count = parseInt(layout)
  return isNaN(count) ? 1 : count
}

if (activePresetId.value && layoutPresets.value[activePresetId.value]) {
  applyPresetStructure(layoutPresets.value[activePresetId.value])
}

// 获取视频列表（填充到需要的数量）
const videoListWithPlaceholder = computed(() => {
  // 合并内部列表和props列表
  const baseList = props.videoList || []
  const maxCount = getMaxVideoCount(currentLayout.value)
  
  // 初始化内部列表（如果为空且未从布局方案恢复）
  if (!skipDefaultVideoInit.value && internalVideoList.value.length === 0 && baseList.length > 0) {
    internalVideoList.value = baseList.map((v, i) => ({
      ...v,
      id: v.id || `video-${i}`,
      url: v.url || '',
      name: v.name || `视频${i + 1}`
    }))
  }
  
  // 确保内部列表长度足够
  while (internalVideoList.value.length < maxCount) {
    internalVideoList.value.push({
      id: `placeholder-${internalVideoList.value.length}`,
      url: '',
      name: `视频${internalVideoList.value.length + 1}`
    })
  }
  
  return internalVideoList.value.slice(0, maxCount)
})

// 显示的视频列表
const displayVideos = computed(() => {
  return videoListWithPlaceholder.value
})

// 获取正在播放的视频列表（有URL的视频）
const activeVideos = computed(() => {
  return internalVideoList.value.filter(video => video && video.url && video.url.trim() !== '')
})

// 获取当前应该显示的摄像头短名（不含目录路径与类型前缀）
const currentLocation = computed(() => {
  if (activeVideos.value.length > 0) {
    const shortName = formatCameraShortName(activeVideos.value[0].name)
    if (shortName) return shortName
  }
  const deviceShortName = formatCameraShortName(props.device?.name || props.device?.device)
  if (deviceShortName) return deviceShortName
  return '未选择设备'
})

const aiFallbackTimers = new Map<number, number>()

function clearAiFallbackTimer(screenIdx: number) {
  const timerId = aiFallbackTimers.get(screenIdx)
  if (timerId != null) {
    window.clearTimeout(timerId)
    aiFallbackTimers.delete(screenIdx)
  }
}

// 切换布局
const switchLayout = (layout: string) => {
  currentLayout.value = normalizeSplitLayout(layout)
  activeVideoIndex.value = 0
}

// 获取视频窗口的类名
const getVideoClass = (index: number) => {
  const classes: string[] = []

  if (index === activeVideoIndex.value) {
    classes.push('active')
  }

  return classes.join(' ')
}

// 处理视频点击
const handleVideoClick = (index: number) => {
  activeVideoIndex.value = index
}

function hasVideoContent(video: { url?: string } | null | undefined) {
  return !!(video?.url && video.url.trim())
}

function createPlaceholderSlot(index: number) {
  return {
    id: `placeholder-${index}`,
    url: '',
    name: `视频${index + 1}`,
  }
}

function removeVideoAtIndex(index: number) {
  if (!hasVideoContent(internalVideoList.value[index])) return

  clearAiFallbackTimer(index)
  internalVideoList.value[index] = createPlaceholderSlot(index)
  videoRefs.value[index] = null
  createMessage.success('已移除视频流')
}

function handleDragStart(index: number, event: DragEvent) {
  dragSourceIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function handleDragEnd() {
  dragSourceIndex.value = null
  dragOverIndex.value = null
}

function handleDragOver(index: number) {
  if (dragSourceIndex.value === null || dragSourceIndex.value === index) return
  dragOverIndex.value = index
}

function handleDragLeave(index: number) {
  if (dragOverIndex.value === index) {
    dragOverIndex.value = null
  }
}

async function swapVideoChannels(fromIndex: number, toIndex: number) {
  if (fromIndex === toIndex) return

  clearAiFallbackTimer(fromIndex)
  clearAiFallbackTimer(toIndex)

  const fromSlot = { ...internalVideoList.value[fromIndex] }
  const toSlot = { ...internalVideoList.value[toIndex] }

  internalVideoList.value[fromIndex] = hasVideoContent(toSlot)
    ? { ...toSlot, id: `video-${toSlot.deviceId || 'slot'}-${fromIndex}` }
    : createPlaceholderSlot(fromIndex)
  internalVideoList.value[toIndex] = hasVideoContent(fromSlot)
    ? { ...fromSlot, id: `video-${fromSlot.deviceId || 'slot'}-${toIndex}` }
    : createPlaceholderSlot(toIndex)

  if (activeVideoIndex.value === fromIndex) {
    activeVideoIndex.value = toIndex
  } else if (activeVideoIndex.value === toIndex) {
    activeVideoIndex.value = fromIndex
  }

  const moved = hasVideoContent(fromSlot) || hasVideoContent(toSlot)
  if (moved) {
    createMessage.success('已调整通道位置')
  }
}

async function handleDrop(targetIndex: number) {
  const sourceIndex = dragSourceIndex.value
  dragSourceIndex.value = null
  dragOverIndex.value = null
  if (sourceIndex === null || sourceIndex === targetIndex) return
  await swapVideoChannels(sourceIndex, targetIndex)
}

// 查找空屏幕
const findEmptyScreen = (): number | null => {
  const maxCount = getMaxVideoCount(currentLayout.value)
  // 确保内部列表已初始化
  if (internalVideoList.value.length === 0) {
    return 0
  }
  
  for (let i = 0; i < maxCount; i++) {
    const video = internalVideoList.value[i]
    // 判断是否为空屏幕：没有视频对象，或者没有URL，或者URL为空字符串
    if (!video || !video.url || video.url.trim() === '') {
      return i
    }
  }
  return null
}

function resolveTargetScreenIndex(): number | null {
  if (currentLayout.value === '1') return 0
  return findEmptyScreen()
}

async function startPlayAtScreen(
  targetIndex: number,
  payload: {
    id: string
    name: string
    url: string
    deviceId?: string
    location?: string
    device?: MonitorTreeDeviceNode
    fallbackUrl?: string | null
    preferAi?: boolean
    pendingAiUrl?: string | null
  },
) {
  return enqueuePlayStart(async () => {
    clearAiFallbackTimer(targetIndex)
    liveRemountRetries.delete(targetIndex)

    const useMultiViewUrl = isMultiViewLayout()
    const primaryUrl = (useMultiViewUrl ? toMultiViewPlayUrl(payload.url) : null) || payload.url
    const fallbackRaw = payload.fallbackUrl?.trim()
    const fallbackUrl = fallbackRaw
      ? ((useMultiViewUrl ? toMultiViewPlayUrl(fallbackRaw) : null) || fallbackRaw)
      : ''
    const pendingRaw = payload.pendingAiUrl?.trim()
    const pendingAi = pendingRaw
      ? ((useMultiViewUrl ? toMultiViewPlayUrl(pendingRaw) : null) || pendingRaw)
      : ''
    const hasFallback = !!(payload.preferAi && fallbackUrl && fallbackUrl !== primaryUrl)
    const allowAiUpgrade = shouldEnableAiForPlay()

    internalVideoList.value[targetIndex] = {
      id: payload.id,
      url: primaryUrl,
      name: payload.name,
      deviceId: payload.deviceId,
      location: payload.location || '',
      device: payload.device,
      fallbackUrl: hasFallback && allowAiUpgrade ? fallbackUrl : null,
    }

    // 启用 AI：先播 /live；多分屏串行探测 /ai，就绪后再逐路升级，失败保持 /live
    if (allowAiUpgrade && pendingAi && pendingAi !== primaryUrl && payload.deviceId) {
      const multi = isMultiViewLayout()
      schedulePendingAiStreamUpgrade(
        pendingAi,
        primaryUrl,
        () => {
          const slot = internalVideoList.value[targetIndex]
          return !!slot && slot.deviceId === payload.deviceId && slot.url !== pendingAi
        },
        () => {
          const slot = internalVideoList.value[targetIndex]
          if (!slot) return
          internalVideoList.value[targetIndex] = {
            ...slot,
            url: pendingAi,
            fallbackUrl: primaryUrl,
          }
        },
        {
          serialize: true,
          probeMs: multi ? AI_STREAM_PROBE_MULTI_VIEW_MS : undefined,
          // 等 /live 先占稳连接，再错峰探测，避免空 /ai 打满 6 路上限
          delayMs: multi ? 1200 + targetIndex * 500 : 400,
        },
      )
    }

    if (!hasFallback || !allowAiUpgrade) return

    const timerId = window.setTimeout(async () => {
      aiFallbackTimers.delete(targetIndex)
      const slot = internalVideoList.value[targetIndex]
      if (!slot || slot.url !== primaryUrl) return
      if (videoRefs.value[targetIndex]?.playing) return

      internalVideoList.value[targetIndex] = { ...slot, url: fallbackUrl!, fallbackUrl: null }
    }, AI_PLAY_FALLBACK_MS)
    aiFallbackTimers.set(targetIndex, timerId)
  })
}

/** AI 流失败回退 /live；已是 live 仍超时则最多 remount 1 次 */
const liveRemountRetries = new Map<number, number>()

function handleStreamError(screenIdx: number) {
  const slot = internalVideoList.value[screenIdx]
  if (!slot) return
  const fb = slot.fallbackUrl?.trim()
  if (fb && fb !== slot.url) {
    clearAiFallbackTimer(screenIdx)
    liveRemountRetries.delete(screenIdx)
    internalVideoList.value[screenIdx] = { ...slot, url: fb, fallbackUrl: null }
    return
  }
  if (!slot.url || !slot.deviceId) return
  if (isAiStreamPlayUrl(slot.url)) {
    const liveUrl = slot.url.replace(/\/ai\//i, '/live/')
    if (liveUrl !== slot.url) {
      clearAiFallbackTimer(screenIdx)
      liveRemountRetries.delete(screenIdx)
      internalVideoList.value[screenIdx] = {
        ...slot,
        id: `video-${slot.deviceId}-live-${Date.now()}`,
        url: liveUrl,
        fallbackUrl: null,
      }
      return
    }
  }
  // live 超时：改 key 强制 Jessibuca 重建（多分屏继续走多 origin）
  const retries = liveRemountRetries.get(screenIdx) || 0
  if (retries >= 1) return
  liveRemountRetries.set(screenIdx, retries + 1)
  clearAiFallbackTimer(screenIdx)
  const remountBase = isMultiViewLayout()
    ? (toMultiViewPlayUrl(slot.url.replace(/([?&])_r=\d+/g, '').replace(/[?&]$/, '')) || slot.url)
    : slot.url
  const bust = `_r=${Date.now()}`
  const nextUrl = remountBase.includes('?')
    ? `${remountBase.replace(/([?&])_r=\d+/g, '$1').replace(/[?&]$/, '')}&${bust}`
    : `${remountBase}?${bust}`
  internalVideoList.value[screenIdx] = {
    ...slot,
    id: `video-${slot.deviceId}-retry-${Date.now()}`,
    url: nextUrl,
    fallbackUrl: null,
  }
}

async function resolvePlayUrlsForDevice(dev: MonitorTreeDeviceNode) {
  if (isGb28181Device(dev.source, dev.device_kind)) {
    return { url: null as string | null, fallbackUrl: null as string | null | undefined }
  }
  return pickDirectPlayUrls(dev, shouldEnableAiForPlay())
}

async function reloadVideoAtIndex(index: number) {
  const slot = internalVideoList.value[index]
  if (!slot?.url || !slot.deviceId) return

  const playId = slot.deviceId
  if (playId.startsWith('gb_ch_')) {
    const gb = parseGbChannelKey(playId)
    if (!gb) return
    const deviceNode = (slot as any).device as MonitorTreeDeviceNode | undefined
    const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolveGbChannelPlayUrls(
      gb.sipDeviceId,
      gb.channelId,
      { enableAi: shouldEnableAiForPlay(), synced: deviceNode },
    )
    if (url) {
      await startPlayAtScreen(index, {
        id: slot.id,
        name: slot.name,
        url,
        deviceId: playId,
        location: slot.location,
        fallbackUrl,
        preferAi,
        pendingAiUrl,
      })
    }
    return
  }

  const dev = (slot as any).device as MonitorTreeDeviceNode | undefined
  if (!dev) return

  const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolvePlayUrlsForDevice(dev)
  if (!url) {
    createMessage.warn(shouldEnableAiForPlay() ? '该设备暂无 AI 流或原始流地址' : '该设备暂无播放地址')
    return
  }
  await startPlayAtScreen(index, {
    id: slot.id,
    name: slot.name,
    url,
    deviceId: playId,
    location: slot.location,
    fallbackUrl,
    preferAi,
    pendingAiUrl,
  })
}

async function reloadAllVideosForAiToggle() {
  const indexes: number[] = []
  internalVideoList.value.forEach((slot, idx) => {
    if (slot?.url) indexes.push(idx)
  })
  await runWithConcurrency(
    indexes,
    MULTI_VIEW_PLAY_CONCURRENCY,
    async (idx) => {
      await reloadVideoAtIndex(idx)
    },
  )
}

watch(enableAi, () => {
  reloadAllVideosForAiToggle()
})

// 播放设备流（与分屏监控一致：默认 /live 原始流，启用 AI 时后台升级）
const playDeviceStream = async (device: any) => {
  const dev: MonitorTreeDeviceNode = (device.device || device) as MonitorTreeDeviceNode
  const playId = String(device.id || dev.id || '')
  const displayName =
    formatCameraShortName(device.name || formatCameraDeviceLabel(dev) || playId) || playId

  const maxCount = getMaxVideoCount(currentLayout.value)
  if (internalVideoList.value.length === 0) {
    for (let i = 0; i < maxCount; i++) {
      internalVideoList.value.push({
        id: `placeholder-${i}`,
        url: '',
        name: `视频${i + 1}`,
      })
    }
  }

  const targetIndex = resolveTargetScreenIndex()
  if (targetIndex === null) {
    createMessage.warning('当前没有空屏幕，请先移除占用通道后再试')
    return
  }

  if (playId.startsWith('gb_ch_')) {
    const gb = parseGbChannelKey(playId)
    if (!gb) {
      createMessage.warning('无效国标通道')
      return
    }
    const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolveGbChannelPlayUrls(
      gb.sipDeviceId,
      gb.channelId,
      { enableAi: shouldEnableAiForPlay(), synced: dev },
    )
    if (!url) {
      createMessage.warn(
        shouldEnableAiForPlay()
          ? '国标通道 AI 流不可用，请确认算法任务已启动；WVP 点播也失败，请检查通道状态'
          : '国标通道拉流失败，请检查 WVP 服务与通道状态',
      )
      return
    }
    await startPlayAtScreen(targetIndex, {
      id: `video-${playId}-${targetIndex}`,
      name: displayName,
      url,
      deviceId: playId,
      location: device.location || '',
      device: dev,
      fallbackUrl,
      preferAi,
      pendingAiUrl,
    })
    return
  }

  if (isGb28181Device(dev.source, dev.device_kind)) {
    createMessage.info('请展开上级国标设备并选择通道')
    return
  }

  const { url, fallbackUrl, preferAi, pendingAiUrl } = await resolvePlayUrlsForDevice(dev)
  if (!url) {
    createMessage.warning(
      shouldEnableAiForPlay()
        ? '该设备暂无 AI 流或原始流播放地址，请先在设备列表中配置'
        : '该设备暂无可用播放地址，请先在设备列表中配置流地址',
    )
    return
  }

  await startPlayAtScreen(targetIndex, {
    id: `video-${playId}-${targetIndex}`,
    name: displayName,
    url,
    deviceId: playId,
    location: device.location || '',
    device: dev,
    fallbackUrl,
    preferAi,
    pendingAiUrl,
  })
}

// 更新时间
const updateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 监听设备变化
watch(() => props.device, (newDevice) => {
  if (newDevice) {
    // 这里可以加载新设备的视频流
  }
}, { immediate: true })

// 监听视频列表变化
watch(() => props.videoList, (newList) => {
  if (skipDefaultVideoInit.value) return
  if (newList && newList.length > 0) {
    // 如果内部列表为空，则初始化内部列表
    if (internalVideoList.value.length === 0) {
      internalVideoList.value = newList.map((v, i) => ({
        ...v,
        id: v.id || `video-${i}`,
        url: v.url || '',
        name: v.name || `视频${i + 1}`
      }))
    }
  }
}, { immediate: true })

// 监听布局变化，调整内部视频列表
watch(() => currentLayout.value, (newLayout) => {
  const maxCount = getMaxVideoCount(newLayout)
  // 如果当前列表长度超过新布局的最大数量，截断
  if (internalVideoList.value.length > maxCount) {
    internalVideoList.value = internalVideoList.value.slice(0, maxCount)
  }
})

// 监听正在播放的视频列表变化，通知父组件
watch(activeVideos, (newVideos) => {
  emit('video-list-change', newVideos.map(v => ({ name: v.name, id: v.id })))
}, { deep: true, immediate: true })

// 检查滚动状态
const checkScrollStatus = () => {
  if (!scrollContainerRef.value) return
  const container = scrollContainerRef.value
  canScrollLeft.value = container.scrollLeft > 0
  canScrollRight.value = container.scrollLeft < container.scrollWidth - container.clientWidth - 1
}

// 向左滑动
const scrollLeft = () => {
  if (!scrollContainerRef.value) return
  const container = scrollContainerRef.value
  const scrollAmount = 220 // 每次滑动一个卡片宽度 + gap
  container.scrollBy({
    left: -scrollAmount,
    behavior: 'smooth'
  })
}

// 向右滑动
const scrollRight = () => {
  if (!scrollContainerRef.value) return
  const container = scrollContainerRef.value
  const scrollAmount = 220 // 每次滑动一个卡片宽度 + gap
  container.scrollBy({
    left: scrollAmount,
    behavior: 'smooth'
  })
}

// 处理滚动事件
const handleScroll = () => {
  checkScrollStatus()
}

// 加载告警录像列表
const loadAlertRecords = async () => {
  try {
    loadingRecords.value = true
    const response = await queryAlarmList({
      pageNo: 1,
      pageSize: 20, // 显示最近20条
    }, { polling: true })
    if (response && response.alert_list) {
      alertRecordList.value = response.alert_list.map((item: any) => {
        let imageUrl = resolveAlertImageDisplayUrl(item.image_url) || null
        
        // 如果没有level字段，根据event类型设置默认级别
        let level = item.level || '告警'
        if (!item.level) {
          // 可以根据event类型设置默认级别
          if (item.event && (item.event.includes('火') || item.event.includes('fire'))) {
            level = '一级'
          } else if (item.event && (item.event.includes('烟') || item.event.includes('smoke'))) {
            level = '二级'
          }
        }
        
        return {
          ...item,
          image: imageUrl,
          level: level,
          time: item.time || item.alert_time || item.created_at || '',
        }
      })
    }
  } catch (error) {
    console.error('加载告警录像列表失败', error)
    alertRecordList.value = []
  } finally {
    loadingRecords.value = false
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 处理录像点击
const playAlertRecord = async (record: any) => {
  if (!openPlayerModal || typeof openPlayerModal !== 'function') {
    createMessage.error('播放器未初始化，请刷新页面重试')
    return
  }

  if (isSnapAlertTask(record)) {
    createMessage.warn('抓拍任务无告警录像')
    return
  }

  if (!record.device_id || !record.time) {
    createMessage.warn('缺少必要信息：设备ID或告警时间')
    return
  }

  try {
    const ok = await playAlertRecordInModal(
      { openModal: openPlayerModal, closeModal: closePlayerModal, setModalProps: setPlayerModalProps },
      record,
    )
    if (ok) {
      lastVideoErrorTime = 0
      lastVideoErrorMsg = ''
    } else {
      showVideoErrorOnce('暂未找到该时间段的录像文件，请稍后再试')
    }
  } catch (error: any) {
    console.error('查询录像失败:', error)
    const errorData = error?.response?.data || error?.data
    showVideoErrorOnce(errorData?.message || error?.message || '查询录像失败，请稍后重试')
  }
}

const handleRecordClick = playAlertRecord

// 暴露方法给父组件
defineExpose({
  playDeviceStream,
  playAlertRecord,
})

let timeTimer: any = null
let recordTimer: any = null
let delayTimer: any = null
let scrollCheckTimer: any = null
let isMounted = false

onMounted(() => {
  isMounted = true
  
  updateTime()
  timeTimer = setInterval(updateTime, 1000)

  if (internalVideoList.value.some((slot) => slot?.pendingRestore)) {
    restorePendingVideos()
  }
  
  // 初始加载告警录像列表
  loadAlertRecords()
  
  // 错峰刷新：延迟2秒开始，每5秒刷新一次告警录像列表（2秒、7秒、12秒...）
  delayTimer = setTimeout(() => {
    // 检查组件是否仍然挂载
    if (!isMounted) return
    
    loadAlertRecords()
    
    // 再次检查组件是否仍然挂载
    if (!isMounted) return
    
    recordTimer = setInterval(() => {
      // 每次执行前检查组件是否仍然挂载
      if (!isMounted) {
        if (recordTimer) {
          clearInterval(recordTimer)
          recordTimer = null
        }
        return
      }
      
      loadAlertRecords()
    }, 5000)
  }, 2000)
  
  // 等待DOM渲染后检查滚动状态
  scrollCheckTimer = setTimeout(() => {
    if (isMounted) {
      checkScrollStatus()
    }
  }, 100)
  
  // 监听窗口大小变化
  window.addEventListener('resize', checkScrollStatus)
})

onUnmounted(() => {
  isMounted = false
  
  // 清理延迟定时器
  if (delayTimer) {
    clearTimeout(delayTimer)
    delayTimer = null
  }
  
  if (scrollCheckTimer) {
    clearTimeout(scrollCheckTimer)
    scrollCheckTimer = null
  }
  
  if (timeTimer) {
    clearInterval(timeTimer)
    timeTimer = null
  }
  
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  
  window.removeEventListener('resize', checkScrollStatus)

  aiFallbackTimers.forEach((id) => window.clearTimeout(id))
  aiFallbackTimers.clear()
  
  // 清理所有视频播放器实例
  videoRefs.value.forEach((ref) => {
    if (ref?.jessibuca) {
      ref._unmounting = true
    }
  })
  videoRefs.value = []
})

// 监听告警列表变化，更新滚动状态
watch(() => alertRecordList.value, () => {
  setTimeout(() => {
    checkScrollStatus()
  }, 100)
}, { deep: true })
</script>

<style lang="less" scoped>
.video-monitor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, rgba(15, 34, 73, 0.8), rgba(24, 46, 90, 0.6));
  border: 1px solid rgba(52, 134, 218, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 0 30px rgba(52, 134, 218, 0.1);
  border-radius: 8px;
  padding: 3px;
  position: relative;
  z-index: 10;
  min-height: 0;
  overflow: hidden;

  &.preset-panel-open {
    overflow: visible;
  }

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      linear-gradient(90deg, transparent 0%, rgba(52, 134, 218, 0.05) 50%, transparent 100%),
      radial-gradient(circle at top left, rgba(52, 134, 218, 0.1), transparent 50%);
    pointer-events: none;
    border-radius: 8px;
  }
}

.monitor-header {
  flex-shrink: 0;
  min-height: 50px;
  height: auto;
  background: rgba(52, 134, 218, 0.08);
  border-bottom: 1px solid rgba(52, 134, 218, 0.3);
  color: #fff;
  font-size: 14px;
  padding: 8px 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 20px;
  position: relative;
  z-index: 1;

  &.panel-open {
    z-index: 210;
  }

  .header-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
  }

  .header-time {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }

  .header-location {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .enable-ai-wrap {
    display: flex;
    align-items: center;
    height: 32px;
    padding: 0 12px;
    background: rgba(52, 134, 218, 0.15);
    border: 1px solid rgba(52, 134, 218, 0.3);
    border-radius: 4px;
    flex-shrink: 0;

    :deep(.ant-checkbox-wrapper) {
      color: rgba(200, 220, 255, 0.95) !important;
      font-size: 14px;
      line-height: 1;
      white-space: nowrap;
    }

    :deep(.ant-checkbox-wrapper:hover .ant-checkbox-inner) {
      border-color: #3486da !important;
    }

    :deep(.ant-checkbox .ant-checkbox-inner) {
      width: 16px;
      height: 16px;
      background-color: rgba(15, 34, 73, 0.6) !important;
      border-color: rgba(52, 134, 218, 0.6) !important;
    }

    :deep(.ant-checkbox-checked .ant-checkbox-inner) {
      background-color: #3486da !important;
      border-color: #3486da !important;
    }

    :deep(.ant-checkbox-checked .ant-checkbox-inner::after) {
      border-color: #fff !important;
    }

    :deep(.ant-checkbox + span) {
      color: rgba(200, 220, 255, 0.95) !important;
      padding-inline-start: 8px;
    }
  }

  .header-toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
    flex-shrink: 0;
  }

  .split-toolbar {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;

    .split-btn {
      min-width: 60px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(52, 134, 218, 0.15);
      border: 1px solid rgba(52, 134, 218, 0.3);
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s;
      color: rgba(200, 220, 255, 0.9);
      font-size: 12px;
      padding: 0 8px;
      white-space: nowrap;

      &:hover {
        background: rgba(52, 134, 218, 0.25);
        border-color: rgba(52, 134, 218, 0.6);
        color: #ffffff;
        box-shadow: 0 0 8px rgba(52, 134, 218, 0.3);
      }

      &.active {
        background: linear-gradient(135deg, rgba(52, 134, 218, 0.3), rgba(48, 82, 174, 0.2));
        border-color: #3486da;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(52, 134, 218, 0.5);
      }
    }
  }

  .toolbar-trigger {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    padding: 0 12px;
    border-radius: 6px;
    border: 1px solid rgba(52, 134, 218, 0.35);
    background: rgba(52, 134, 218, 0.12);
    color: rgba(214, 235, 255, 0.92);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    user-select: none;
    flex-shrink: 0;

    &:hover,
    &.open {
      background: rgba(52, 134, 218, 0.28);
      border-color: rgba(52, 134, 218, 0.6);
      color: #fff;
      box-shadow: 0 0 10px rgba(52, 134, 218, 0.25);
    }

    .trigger-label {
      font-weight: 500;
    }
  }

  .layout-preset-trigger {
    &.has-active {
      border-color: rgba(82, 196, 26, 0.45);
    }

    .trigger-badge {
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      padding: 0 6px;
      height: 20px;
      line-height: 20px;
      border-radius: 10px;
      font-size: 11px;
      color: #b7eb8f;
      background: rgba(82, 196, 26, 0.15);
      border: 1px solid rgba(82, 196, 26, 0.25);
    }
  }
}

.preset-panel-backdrop {
  position: absolute;
  inset: 0;
  top: 52px;
  z-index: 150;
  background: rgba(0, 0, 0, 0.35);
  pointer-events: auto;
}

.monitor-content {
  flex: 1;
  min-height: 0;
  display: grid;
  gap: 4px;
  padding: 4px;
  overflow: hidden;
  background:
    linear-gradient(rgba(52, 134, 218, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(52, 134, 218, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  background-color: #000;

  // 1分屏 - 全屏单画面
  &.layout-1 {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;
  }

  // 4分屏 - 2行2列
  &.layout-4 {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(2, 1fr);
  }

  // 9分屏 - 3行3列
  &.layout-9 {
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
  }

  // 16分屏 - 4行4列
  &.layout-16 {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 1fr);
  }
}

.video-window {
  position: relative;
  background: #000;
  border: 2px solid rgba(52, 134, 218, 0.3);
  border-radius: 2px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    border-color: rgba(52, 134, 218, 0.6);
    transform: scale(1.01);
    z-index: 10;
  }

  &.active {
    border-color: #3486da;
    box-shadow: 0 0 10px rgba(52, 134, 218, 0.5);
    z-index: 5;
  }

  &.drag-over {
    border-color: #52c41a;
    box-shadow: 0 0 12px rgba(82, 196, 26, 0.55);
    z-index: 12;
  }

  &.is-dragging {
    opacity: 0.55;
    border-style: dashed;
  }

  .video-container {
    width: 100%;
    height: 100%;
    position: relative;
    background: #000;

    .video-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.4);

      .camera-icon {
        width: 72px;
        height: 72px;
        opacity: 0.7;
        filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.4)) drop-shadow(0 0 8px rgba(74, 144, 226, 0.2));
        transition: all 0.3s ease;
      }

      &:hover .camera-icon {
        opacity: 0.95;
        transform: scale(1.08);
        filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.5)) drop-shadow(0 0 12px rgba(74, 144, 226, 0.4));
      }

      .placeholder-text {
        margin-top: 8px;
        font-size: 12px;
      }
    }

    .video-player {
      width: 100%;
      height: 100%;
    }

    .drag-zone {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 72px;
      height: 56px;
      max-width: 32%;
      max-height: 28%;
      z-index: 1;
      cursor: grab;
      border-radius: 4px;

      &:active {
        cursor: grabbing;
      }
    }

    .video-label {
      position: absolute;
      top: 0;
      left: 0;
      right: 32px;
      color: #ffffff;
      font-size: 12px;
      padding: 4px 8px;
      text-align: left;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      background: linear-gradient(to bottom, rgba(0, 0, 0, 0.75), transparent);
      z-index: 2;
      pointer-events: none;
    }

    .video-close-btn {
      position: absolute;
      top: 4px;
      right: 4px;
      z-index: 3;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      padding: 0;
      border: none;
      border-radius: 2px;
      color: #fff;
      background: rgba(255, 77, 79, 0.55);
      cursor: pointer;
      opacity: 0.75;
      transition: opacity 0.2s, background 0.2s;

      &:hover {
        opacity: 1;
        background: rgba(255, 77, 79, 0.85);
      }
    }

    .video-active-indicator {
      position: absolute;
      top: 4px;
      left: 4px;
      width: 8px;
      height: 8px;
      background: #3486da;
      border-radius: 50%;
      box-shadow: 0 0 6px rgba(52, 134, 218, 0.8);
    }
  }
}

.alert-record-list {
  flex-shrink: 0;
  height: 140px;
  min-height: 140px;
  background: linear-gradient(to bottom, rgba(48, 82, 174, 0.35), rgba(52, 134, 218, 0.25));
  border-top: 1px solid rgba(52, 134, 218, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.alert-record-header {
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(12, 40, 84, 0.8);
  border-bottom: 1px solid rgba(52, 134, 218, 0.2);

  .header-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
  }

  .header-count {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.alert-record-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.scroll-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(52, 134, 218, 0.3);
  border: 1px solid rgba(52, 134, 218, 0.5);
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s;
  color: #ffffff;
  backdrop-filter: blur(4px);

  &:hover {
    background: rgba(52, 134, 218, 0.5);
    border-color: #3486da;
    transform: translateY(-50%) scale(1.1);
  }

  &:active {
    transform: translateY(-50%) scale(0.95);
  }
}

.scroll-btn-left {
  left: 8px;
}

.scroll-btn-right {
  right: 8px;
}

.alert-record-scroll {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  overflow-x: auto;
  overflow-y: hidden;
  align-items: center;
  scroll-behavior: smooth;

  &::-webkit-scrollbar {
    height: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(52, 134, 218, 0.5);
    border-radius: 3px;

    &:hover {
      background: rgba(52, 134, 218, 0.7);
    }
  }
}

.alert-record-item {
  flex-shrink: 0;
  width: 200px;
  height: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(52, 134, 218, 0.3);
  border-radius: 6px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #3486da;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(52, 134, 218, 0.3);
  }
}

.record-thumbnail {
  position: relative;
  width: 100%;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);

  .thumbnail-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.4);
  }

  .record-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 500;
    background: rgba(52, 134, 218, 0.8);
    color: #ffffff;
    border: 1px solid #3486da;
  }
}

.record-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  width: 100%;
}

.record-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);

  .record-device {
    flex: 0 1 auto;
    max-width: 130px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .record-time {
    flex-shrink: 0;
    font-size: 13px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin-left: 8px;
    white-space: nowrap;
  }

  .play-icon {
    flex-shrink: 0;
    color: rgba(52, 134, 218, 0.9);
    margin-left: 8px;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: #3486da;
      transform: scale(1.1);
    }
  }
}

.empty-records {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.boxfoot {
  position: absolute;
  bottom: 0;
  width: 100%;
  left: 0;
  pointer-events: none;

  &:before, &:after {
    position: absolute;
    width: 17px;
    height: 17px;
    content: "";
    border-bottom: 3px solid #3486da;
    bottom: -2px;
  }

  &:before {
    border-left: 3px solid #3486da;
    left: -2px;
  }

  &:after {
    border-right: 3px solid #3486da;
    right: -2px;
  }
}
</style>
