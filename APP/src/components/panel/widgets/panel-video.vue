<template>
  <view class="video-widget">
    <view class="video-head">
      <text class="video-title">{{ cardTitle || '实时画面' }}</text>
      <wd-tag v-if="playing" type="success" plain custom-class="live-tag">
        直播中
      </wd-tag>
    </view>

    <view v-if="stateText && !playUrl" class="video-placeholder">
      <text class="video-state">{{ stateText }}</text>
      <wd-button v-if="!resolving" size="small" type="primary" plain @click="start">
        {{ retryCount > 0 ? '重试' : '启动预览' }}
      </wd-button>
    </view>

    <LiveStreamPlayer
      v-else-if="playUrl"
      :key="playerKey"
      :play-url="playUrl"
      :autoplay="true"
    />

    <view v-else class="video-placeholder">
      <wd-loading :size="24" color="#98a2b3" />
      <text class="video-state">正在解析播放地址…</text>
    </view>
  </view>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref } from 'vue'
import LiveStreamPlayer from '@/components/live-stream-player.vue'
import {
  getDeviceInfo,
  startStreamForwarding,
  stopStreamForwarding,
} from '@/api/video/camera'
import type { DeviceInfo } from '@/api/video/camera'
import { playByDeviceAndChannel } from '@/api/video/gb28181'
import { getGb28181PlayIds, shouldPlayViaGb28181 } from '@/utils/video/deviceLabel'
import { hasDirectPlayStream, pickWvpPlayUrl, resolveDevicePlayUrl } from '@/utils/video/deviceStream'
import { getLinkedCameraIds } from '@/api/device/panel'

const props = defineProps<{
  widget: { id?: string }
  iotDeviceId: number | string
  cardTitle?: string
}>()

const playUrl = ref('')
const resolving = ref(true)
const playing = ref(false)
const stateText = ref('')
const playerKey = ref(0)
const retryCount = ref(0)
let camera: DeviceInfo | null = null
let startedByWidget = false

async function resolvePlayUrl(device: DeviceInfo): Promise<string> {
  if (shouldPlayViaGb28181(device)) {
    const gbIds = getGb28181PlayIds(device)
    if (!gbIds)
      return ''
    try {
      const res = await playByDeviceAndChannel(gbIds.sipDeviceId, gbIds.channelId)
      const streamContent = res?.data?.data ?? res?.data
      return pickWvpPlayUrl(streamContent) || ''
    }
    catch {
      return ''
    }
  }
  if (hasDirectPlayStream(device))
    return resolveDevicePlayUrl(device)
  return ''
}

async function start() {
  resolving.value = true
  stateText.value = ''
  try {
    if (!camera) {
      const ids = await getLinkedCameraIds(props.iotDeviceId)
      if (!ids.length) {
        stateText.value = '该设备未关联摄像头，请在 WEB 端绑定后使用'
        return
      }
      camera = await getDeviceInfo(ids[0])
    }

    let url = await resolvePlayUrl(camera)
    if (!url && !shouldPlayViaGb28181(camera)) {
      // 无直连流时尝试拉起平台转发流
      try {
        await startStreamForwarding(camera.id)
        startedByWidget = true
        playing.value = true
        camera = { ...camera, ...(await getDeviceInfo(camera.id).catch(() => ({}) as any)) }
        url = hasDirectPlayStream(camera) ? resolveDevicePlayUrl(camera) : ''
      }
      catch {
        // 转发流启动失败，落入下方提示
      }
    }

    playUrl.value = url
    playerKey.value++
    if (!url) {
      stateText.value = shouldPlayViaGb28181(camera)
        ? '国标点播失败，请检查设备连接'
        : '暂未获取到播放地址，请点击重试'
      playing.value = false
    }
    else {
      playing.value = true
    }
  }
  finally {
    resolving.value = false
    retryCount.value++
  }
}

onMounted(() => {
  start()
})

onUnmounted(async () => {
  if (!startedByWidget || !camera)
    return
  try {
    await stopStreamForwarding(camera.id)
  }
  catch {
    // 忽略停止失败
  }
})
</script>

<style lang="scss" scoped>
.video-widget {
  width: 100%;
}

.video-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
  padding: 8rpx 8rpx 0;
}

.video-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #6b7688;
}

.video-placeholder {
  min-height: 320rpx;
  border-radius: 20rpx;
  background: #0f1420;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
}

.video-state {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.55);
}
</style>
