<template>
  <div class="video-monitor">
    <div class="monitor-header">
      <div class="header-title">实时监控</div>
      <div class="header-time">{{ currentTime }}</div>
      <div class="header-location">{{ device?.location || '未选择设备' }}</div>
    </div>
    
    <div class="monitor-content">
      <!-- 主视频窗口 -->
      <div class="main-video">
        <div class="video-container" ref="mainVideoRef">
          <div v-if="!mainVideoUrl" class="video-placeholder">
            <Icon icon="ant-design:video-camera-outlined" :size="48" />
            <div class="placeholder-text">暂无视频流</div>
          </div>
          <video
            v-else
            ref="mainVideo"
            :src="mainVideoUrl"
            autoplay
            muted
            playsinline
            class="video-player"
          ></video>
        </div>
      </div>
      
      <!-- 小视频窗口网格 -->
      <div class="video-grid">
        <div
          v-for="(video, index) in smallVideos"
          :key="video.id"
          :class="['video-item', { active: activeVideoIndex === index }]"
          @click="switchMainVideo(index)"
        >
          <div class="video-container-small">
            <div v-if="!video.url" class="video-placeholder-small">
              <Icon icon="ant-design:video-camera-outlined" :size="24" />
            </div>
            <video
              v-else
              :src="video.url"
              autoplay
              muted
              playsinline
              class="video-player-small"
            ></video>
            <div class="video-label">{{ video.name || `视频${index + 1}` }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Icon } from '@/components/Icon'

defineOptions({
  name: 'VideoMonitor'
})

const props = defineProps<{
  device?: any
  videoList?: any[]
}>()

const currentTime = ref('')
const mainVideoRef = ref<HTMLElement>()
const mainVideo = ref<HTMLVideoElement>()
const activeVideoIndex = ref(0)

// 主视频URL
const mainVideoUrl = ref('')

// 小视频列表（取前6个）
const smallVideos = computed(() => {
  if (!props.videoList || props.videoList.length <= 1) {
    return Array.from({ length: 6 }, (_, i) => ({
      id: `small-${i}`,
      url: '',
      name: `视频${i + 1}`
    }))
  }
  return props.videoList.slice(1, 7).map((v, i) => ({
    ...v,
    name: v.name || `视频${i + 1}`
  }))
})

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

// 切换主视频
const switchMainVideo = (index: number) => {
  activeVideoIndex.value = index
  const video = smallVideos.value[index]
  if (video && video.url) {
    mainVideoUrl.value = video.url
  }
}

// 监听设备变化
watch(() => props.device, (newDevice) => {
  if (newDevice) {
    // 这里可以加载新设备的视频流
    // mainVideoUrl.value = newDevice.videoUrl
  }
}, { immediate: true })

// 监听视频列表变化
watch(() => props.videoList, (newList) => {
  if (newList && newList.length > 0) {
    mainVideoUrl.value = newList[0].url || ''
  }
}, { immediate: true })

let timeTimer: any = null

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
})
</script>

<style lang="less" scoped>
.video-monitor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.monitor-header {
  height: 50px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  
  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
  }
  
  .header-time {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    margin-left: auto;
  }
  
  .header-location {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.monitor-content {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

.main-video {
  flex: 1;
  min-width: 0;
  
  .video-container {
    width: 100%;
    height: 100%;
    background: #000000;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
    
    .video-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.4);
      
      .placeholder-text {
        margin-top: 12px;
        font-size: 14px;
      }
    }
    
    .video-player {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }
}

.video-grid {
  width: 280px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(3, 1fr);
  gap: 8px;
  
  .video-item {
    position: relative;
    cursor: pointer;
    border-radius: 4px;
    overflow: hidden;
    border: 2px solid transparent;
    transition: all 0.3s;
    
    &:hover {
      border-color: rgba(24, 144, 255, 0.5);
      transform: scale(1.02);
    }
    
    &.active {
      border-color: #1890ff;
      box-shadow: 0 0 8px rgba(24, 144, 255, 0.5);
    }
    
    .video-container-small {
      width: 100%;
      height: 100%;
      background: #000000;
      position: relative;
      
      .video-placeholder-small {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(255, 255, 255, 0.3);
      }
      
      .video-player-small {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .video-label {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
        color: #ffffff;
        font-size: 12px;
        padding: 4px 8px;
        text-align: center;
      }
    }
  }
}
</style>
