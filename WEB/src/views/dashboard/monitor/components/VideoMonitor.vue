<template>
  <div class="video-monitor">
    <div class="monitor-header">
      <div class="header-title">实时监控</div>
      <div class="header-time">{{ currentTime }}</div>
      <div class="header-location">{{ device?.location || '未选择设备' }}</div>
      <!-- 分屏切换工具栏 -->
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
    </div>
    
    <div class="monitor-content" :class="`layout-${currentLayout}`">
      <!-- 根据当前布局渲染视频窗口 -->
      <div
        v-for="(video, index) in displayVideos"
        :key="video.id || index"
        :class="['video-window', getVideoClass(index)]"
        :style="getVideoStyle(index)"
        @click="handleVideoClick(index)"
      >
        <div class="video-container">
          <div v-if="!video.url" class="video-placeholder">
            <img src="@/assets/images/bigscreen/camera-icon.svg" alt="摄像头" class="camera-icon" />
            <div class="placeholder-text">{{ video.name || `视频${index + 1}` }}</div>
          </div>
          <video
            v-else
            :src="video.url"
            autoplay
            muted
            playsinline
            class="video-player"
            :ref="el => setVideoRef(el, index)"
          ></video>
          <div class="video-label">{{ video.name || `视频${index + 1}` }}</div>
          <div v-if="index === activeVideoIndex" class="video-active-indicator"></div>
        </div>
      </div>
    </div>
    <div class="boxfoot"></div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

defineOptions({
  name: 'VideoMonitor'
})

const props = defineProps<{
  device?: any
  videoList?: any[]
}>()

const currentTime = ref('')
const activeVideoIndex = ref(0)
const currentLayout = ref('1')
const videoRefs = ref<(HTMLVideoElement | null)[]>([])

// 分屏布局配置
const splitLayouts = [
  { value: '1', label: '1分屏' },
  { value: '4', label: '4分屏' },
  { value: '6', label: '6分屏' },
  { value: '9', label: '9分屏' },
  { value: '16', label: '16分屏' }
]

// 设置视频引用
const setVideoRef = (el: any, index: number) => {
  if (el) {
    videoRefs.value[index] = el
  }
}

// 获取视频列表（填充到需要的数量）
const videoListWithPlaceholder = computed(() => {
  const list = props.videoList || []
  const maxCount = getMaxVideoCount(currentLayout.value)
  const result = [...list]
  
  // 填充空位
  while (result.length < maxCount) {
    result.push({
      id: `placeholder-${result.length}`,
      url: '',
      name: `视频${result.length + 1}`
    })
  }
  
  return result.slice(0, maxCount)
})

// 获取当前布局需要的最大视频数量
const getMaxVideoCount = (layout: string) => {
  const count = parseInt(layout)
  return isNaN(count) ? 1 : count
}

// 显示的视频列表
const displayVideos = computed(() => {
  return videoListWithPlaceholder.value
})

// 切换布局
const switchLayout = (layout: string) => {
  currentLayout.value = layout
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

// 获取视频窗口的样式（用于特殊布局）
// 除了1、4、9、16分屏外，其他都采用左上大屏+其他小屏的布局
const getVideoStyle = (index: number) => {
  const layout = currentLayout.value
  
  // 6分屏：左上大屏（2x2）+ 5个小屏，网格：3行3列
  if (layout === '6') {
    if (index === 0) {
      // 左上大屏，占据2行2列
      return {
        gridColumn: '1 / 3',
        gridRow: '1 / 3'
      }
    } else {
      // 其他5个小屏：第1行第3列、第2行第3列、第3行第1、2、3列
      const pos = index - 1
      if (pos === 0) {
        // 第1行第3列
        return {
          gridColumn: '3',
          gridRow: '1'
        }
      } else if (pos === 1) {
        // 第2行第3列
        return {
          gridColumn: '3',
          gridRow: '2'
        }
      } else {
        // 第3行的3个位置
        return {
          gridColumn: `${pos - 1}`,
          gridRow: '3'
        }
      }
    }
  }
  
  return {}
}

// 处理视频点击
const handleVideoClick = (index: number) => {
  activeVideoIndex.value = index
  // 可以在这里添加全屏或其他操作
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
  if (newList && newList.length > 0) {
    // 可以在这里处理视频列表变化
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
  background: #000;
  border: 1px solid #3486da;
  padding: 3px;
  position: relative;
  z-index: 10;
  
  &:before, &:after {
    position: absolute;
    width: 17px;
    height: 17px;
    content: "";
    border-top: 3px solid #3486da;
    top: -2px;
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

.monitor-header {
  height: 50px;
  background: linear-gradient(to right, rgba(48, 82, 174, 1), rgba(48, 82, 174, 0));
  color: #fff;
  font-size: 14px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  
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
  }
  
  .split-toolbar {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-left: auto;
    
    .split-btn {
      min-width: 60px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s;
      color: rgba(255, 255, 255, 0.8);
      font-size: 12px;
      padding: 0 8px;
      white-space: nowrap;
      
      &:hover {
        background: rgba(255, 255, 255, 0.2);
        border-color: #3486da;
        color: #ffffff;
      }
      
      &.active {
        background: #3486da;
        border-color: #3486da;
        color: #ffffff;
      }
    }
  }
}

.monitor-content {
  flex: 1;
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
  
  // 6分屏 - 左上大屏（2x2）+ 5个小屏，网格：3行3列
  &.layout-6 {
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
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
      object-fit: contain;
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
      text-align: left;
      pointer-events: none;
    }
    
    .video-active-indicator {
      position: absolute;
      top: 4px;
      right: 4px;
      width: 8px;
      height: 8px;
      background: #3486da;
      border-radius: 50%;
      box-shadow: 0 0 6px rgba(52, 134, 218, 0.8);
    }
  }
}

.boxfoot {
  position: absolute;
  bottom: 0;
  width: 100%;
  left: 0;
  
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
