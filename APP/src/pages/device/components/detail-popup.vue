<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 90vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        设备详情
      </view>
      <view v-if="device" class="max-h-75vh overflow-y-auto">
        <view class="mb-24rpx flex items-center justify-between">
          <view class="text-34rpx font-semibold text-[#333]">
            {{ device.name || device.id }}
          </view>
          <wd-tag :type="device.online ? 'success' : 'danger'" plain>
            {{ device.online ? '在线' : '离线' }}
          </wd-tag>
        </view>

        <!-- 实时画面 -->
        <view class="mb-24rpx">
          <view class="mb-12rpx flex items-center justify-between">
            <view class="text-28rpx font-semibold text-[#333]">
              实时画面
            </view>
            <wd-tag v-if="showLiveTag" type="success" plain>
              直播中
            </wd-tag>
          </view>

          <view v-if="streamLoading" class="flex h-400rpx items-center justify-center rounded-12rpx bg-[#f0f0f0] text-26rpx text-[#999]">
            正在启动预览流...
          </view>
          <LiveStreamPlayer
            v-else-if="playUrl"
            :key="playerKey"
            :play-url="playUrl"
            :autoplay="true"
          />
          <view
            v-else
            class="flex h-400rpx flex-col items-center justify-center rounded-12rpx bg-[#f0f0f0] px-24rpx text-center"
          >
            <view class="mb-16rpx text-26rpx text-[#999]">
              {{ streamError || '暂无可用预览流' }}
            </view>
            <wd-button
              v-if="supportsFfmpegPreview"
              type="primary"
              size="small"
              :loading="streamLoading"
              @click="handleStartFfmpegPreview"
            >
              启动预览
            </wd-button>
          </view>
        </view>

        <view class="rounded-12rpx bg-[#f7f8f9] p-24rpx">
          <view v-for="row in detailRows" :key="row.label" class="mb-16rpx flex text-28rpx last:mb-0">
            <view class="w-160rpx flex-shrink-0 text-[#999]">
              {{ row.label }}
            </view>
            <view class="flex-1 break-all text-[#333]">
              {{ row.value }}
            </view>
          </view>
        </view>

        <view v-if="supportsFfmpegPreview" class="mt-32rpx flex gap-24rpx">
          <wd-button
            class="flex-1"
            type="primary"
            :loading="streamLoading"
            @click="handleToggleFfmpegPreview"
          >
            {{ ffmpegPreviewRunning ? '停止预览流' : '重新启动预览' }}
          </wd-button>
        </view>

        <view v-if="canManage" class="mt-16rpx flex gap-16rpx">
          <wd-button class="flex-1" plain @click="handleEdit">
            编辑
          </wd-button>
          <wd-button class="flex-1" type="danger" plain @click="handleDelete">
            删除
          </wd-button>
        </view>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import type { DeviceInfo } from '@/api/video/camera'
import { computed, ref, watch } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import LiveStreamPlayer from '@/components/live-stream-player.vue'
import {
  deleteDevice,
  getDeviceKindText,
  getDeviceInfo,
  getStreamStatus,
  startStreamForwarding,
  stopStreamForwarding,
} from '@/api/video/camera'
import { playByDeviceAndChannel } from '@/api/video/gb28181'
import { getGb28181PlayIds, maskSourceUrl, shouldPlayViaGb28181 } from '@/utils/video/deviceLabel'
import { hasDirectPlayStream, pickWvpPlayUrl, resolveDevicePlayUrl } from '@/utils/video/deviceStream'

const emit = defineEmits<{ refresh: [], edit: [device: DeviceInfo] }>()
const toast = useToast()
const visible = ref(false)
const device = ref<DeviceInfo | null>(null)
const streamLoading = ref(false)
const ffmpegPreviewRunning = ref(false)
const ffmpegStartedByPopup = ref(false)
const streamError = ref('')
const playUrl = ref('')
const playerKey = ref(0)

const showLiveTag = computed(() => !!playUrl.value || ffmpegPreviewRunning.value)

const isGb28181 = computed(() => device.value ? shouldPlayViaGb28181(device.value) : false)

const supportsFfmpegPreview = computed(() => {
  if (isGb28181.value)
    return false
  const source = device.value?.source?.trim().toLowerCase() || ''
  return !source.startsWith('rtmp://')
})

const canManage = computed(() => {
  const kind = device.value?.device_kind
  return !kind || kind === 'direct' || kind === 'nvr_channel'
})

const detailRows = computed(() => {
  if (!device.value)
    return []
  const d = device.value
  return [
    { label: '设备 ID', value: d.id },
    { label: '设备类型', value: getDeviceKindText(d.device_kind) },
    { label: 'IP 地址', value: d.ip ? `${d.ip}${d.port ? `:${d.port}` : ''}` : '-' },
    { label: '来源', value: maskSourceUrl(d.source) || '-' },
    { label: '厂商', value: d.manufacturer || '-' },
    { label: '型号', value: d.model || '-' },
    { label: '位置', value: d.address || (d.has_location ? '已设置坐标' : '未设置') },
    { label: 'NVR', value: d.nvr_label || (d.nvr_channel != null ? `通道 ${d.nvr_channel}` : '-') },
  ]
})

async function resolvePlayUrl(): Promise<string> {
  if (!device.value)
    return ''

  if (shouldPlayViaGb28181(device.value)) {
    const gbIds = getGb28181PlayIds(device.value)
    if (!gbIds)
      return ''
    try {
      const res = await playByDeviceAndChannel(gbIds.sipDeviceId, gbIds.channelId)
      const streamContent = res?.data?.data ?? res?.data
      return pickWvpPlayUrl(streamContent) || ''
    }
    catch {
      streamError.value = '国标点播失败，请检查设备连接'
      return ''
    }
  }

  if (hasDirectPlayStream(device.value))
    return resolveDevicePlayUrl(device.value)

  return ''
}

async function loadPlayUrl() {
  streamLoading.value = true
  streamError.value = ''
  playUrl.value = ''
  try {
    const url = await resolvePlayUrl()
    playUrl.value = url
    if (!url && !isGb28181.value && ffmpegPreviewRunning.value)
      streamError.value = '流已启动但未获取到播放地址，请稍后重试'
    else if (!url && isGb28181.value)
      streamError.value = streamError.value || '未获取到播放地址'
  }
  finally {
    streamLoading.value = false
  }
}

function updatePlayStateFromDevice() {
  if (!device.value)
    return
  if (hasDirectPlayStream(device.value)) {
    playUrl.value = resolveDevicePlayUrl(device.value)
    streamError.value = ''
    return
  }
  if (!playUrl.value && ffmpegPreviewRunning.value)
    streamError.value = '流已启动但未获取到播放地址，请稍后重试'
}

async function refreshFfmpegStatus(deviceId: string) {
  try {
    const res = await getStreamStatus(deviceId)
    ffmpegPreviewRunning.value = res?.status === 'running'
    updatePlayStateFromDevice()
  }
  catch {
    ffmpegPreviewRunning.value = false
  }
}

async function handleStartFfmpegPreview() {
  if (!device.value || isGb28181.value)
    return
  streamLoading.value = true
  streamError.value = ''
  try {
    await startStreamForwarding(device.value.id)
    ffmpegPreviewRunning.value = true
    ffmpegStartedByPopup.value = true
    try {
      const detail = await getDeviceInfo(device.value.id)
      device.value = { ...device.value, ...detail }
    }
    catch {
      // 列表数据已足够
    }
    updatePlayStateFromDevice()
    if (!playUrl.value)
      streamError.value = '预览流已启动，正在等待播放地址...'
    else
      toast.success('预览流已启动')
  }
  catch {
    streamError.value = '启动预览流失败'
    toast.error('流操作失败')
  }
  finally {
    streamLoading.value = false
  }
}

async function handleToggleFfmpegPreview() {
  if (!device.value)
    return
  if (ffmpegPreviewRunning.value) {
    streamLoading.value = true
    try {
      await stopStreamForwarding(device.value.id)
      ffmpegPreviewRunning.value = false
      ffmpegStartedByPopup.value = false
      playUrl.value = ''
      streamError.value = ''
      toast.success('已停止预览流')
    }
    catch {
      toast.error('流操作失败')
    }
    finally {
      streamLoading.value = false
    }
    return
  }
  await handleStartFfmpegPreview()
}

function handleEdit() {
  if (!device.value)
    return
  visible.value = false
  emit('edit', device.value)
}

function handleDelete() {
  if (!device.value)
    return
  const name = device.value.name || device.value.id
  uni.showModal({
    title: '确认删除',
    content: `确定删除设备「${name}」吗？`,
    success: async (res) => {
      if (!res.confirm || !device.value)
        return
      try {
        await deleteDevice(device.value.id)
        toast.success('删除成功')
        visible.value = false
        emit('refresh')
      }
      catch {
        toast.error('删除失败')
      }
    },
  })
}

async function open(item: DeviceInfo) {
  visible.value = true
  device.value = item
  ffmpegPreviewRunning.value = false
  ffmpegStartedByPopup.value = false
  streamError.value = ''
  playUrl.value = ''
  playerKey.value += 1
  try {
    const detail = await getDeviceInfo(item.id)
    device.value = { ...item, ...detail }
  }
  catch {
    // 列表数据已足够展示
  }

  if (shouldPlayViaGb28181(device.value)) {
    await loadPlayUrl()
    return
  }

  await refreshFfmpegStatus(item.id)
  if (hasDirectPlayStream(device.value)) {
    playUrl.value = resolveDevicePlayUrl(device.value)
    return
  }
  if (supportsFfmpegPreview.value && !ffmpegPreviewRunning.value)
    await handleStartFfmpegPreview()
  else
    await loadPlayUrl()
}

watch(visible, (val) => {
  if (!val) {
    playUrl.value = ''
    playerKey.value += 1
    if (device.value && ffmpegStartedByPopup.value) {
      stopStreamForwarding(device.value.id).catch(() => {})
      ffmpegPreviewRunning.value = false
      ffmpegStartedByPopup.value = false
    }
  }
})

defineExpose({ open })
</script>
