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
    
    <!-- 告警录像列表 -->
    <div class="alert-record-list">
      <div class="alert-record-header">
        <span class="header-title">告警录像</span>
        <span class="header-count">共 {{ alertRecordList.length }} 条</span>
      </div>
      <div class="alert-record-scroll">
        <div
          v-for="(record, index) in alertRecordList"
          :key="record.id || index"
          class="alert-record-item"
          @click="handleRecordClick(record)"
        >
          <div class="record-thumbnail">
            <img
              v-if="record.image"
              :src="record.image"
              alt="告警图片"
              class="thumbnail-img"
            />
            <div v-else class="thumbnail-placeholder">
              <Icon icon="ant-design:video-camera-outlined" :size="24" />
            </div>
            <div class="record-badge" :class="`level-${record.level}`">
              {{ record.level || '告警' }}
            </div>
          </div>
          <div class="record-info">
            <div class="record-title">{{ record.event || record.title || '未知事件' }}</div>
            <div class="record-meta">
              <span class="record-device">{{ record.device_name || record.device_id || '未知设备' }}</span>
              <span class="record-time">{{ formatTime(record.time) }}</span>
            </div>
          </div>
        </div>
        <div v-if="alertRecordList.length === 0" class="empty-records">
          <Icon icon="ant-design:inbox-outlined" :size="32" />
          <span>暂无告警录像</span>
        </div>
      </div>
    </div>
    
    <div class="boxfoot"></div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Icon } from '@/components/Icon'
import { queryAlarmList } from '@/api/device/calculate'

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
const alertRecordList = ref<any[]>([])
const loadingRecords = ref(false)

// 分屏布局配置
const splitLayouts = [
  { value: '1', label: '1分屏' },
  { value: '4', label: '4分屏' },
  { value: '6', label: '6分屏' },
  { value: '8', label: '8分屏' },
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

  // 8分屏：左侧大屏（2x2）+ 右侧3个小屏（一列）+ 下侧4个小屏，网格：3行4列
  if (layout === '8') {
    if (index === 0) {
      // 左侧大屏，占据第1-2行，第1-2列（2x2）
      return {
        gridColumn: '1 / 4',
        gridRow: '1 / 3'
      }
    } else if (index < 4) {
      // 右侧3个小屏：全部放在第4列，垂直排列
      const pos = index - 1
      if (pos === 0) {
        // 第1行第4列
        return {
          gridColumn: '4',
          gridRow: '1'
        }
      } else if (pos === 1) {
        // 第2行第4列
        return {
          gridColumn: '4',
          gridRow: '2'
        }
      } else {
        // 第3行第4列
        return {
          gridColumn: '4',
          gridRow: '3'
        }
      }
    } else {
      // 下侧4个小屏：第3行第1、2、3列，第4列已经被占用
      const pos = index - 4
      return {
        gridColumn: `${pos + 1}`,
        gridRow: '3'
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

// 加载告警录像列表
const loadAlertRecords = async () => {
  try {
    loadingRecords.value = true
    const response = await queryAlarmList({
      pageNo: 1,
      pageSize: 10, // 只显示最近10条
    })
    if (response && response.alert_list) {
      alertRecordList.value = response.alert_list.map((item: any) => {
        // 构建图片URL
        let imageUrl = null
        if (item.image_path) {
          imageUrl = `/video/alert/image?path=${encodeURIComponent(item.image_path)}`
        }
        
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
          level: level
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
const handleRecordClick = (record: any) => {
  // 可以在这里添加播放录像的逻辑
  console.log('点击告警录像', record)
}

let timeTimer: any = null
let recordTimer: any = null

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  loadAlertRecords()
  // 每30秒刷新一次告警录像列表
  recordTimer = setInterval(loadAlertRecords, 30000)
})

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
  if (recordTimer) {
    clearInterval(recordTimer)
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

  // 6分屏 - 左上大屏（2x2）+ 5个小屏，网格：3行3列
  &.layout-6 {
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
  }

  // 8分屏 - 左侧大屏（2x2）+ 右侧3个小屏（一列）+ 下侧4个小屏，网格：3行4列
  &.layout-8 {
    grid-template-columns: repeat(4, 1fr);
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

.alert-record-list {
  height: 140px;
  background: rgba(0, 0, 0, 0.5);
  border-top: 1px solid rgba(52, 134, 218, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.alert-record-scroll {
  flex: 1;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  overflow-x: auto;
  overflow-y: hidden;
  align-items: center;

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
    background: rgba(255, 77, 79, 0.8);
    color: #ffffff;
    border: 1px solid #ff4d4f;

    &.level-一级 {
      background: rgba(255, 77, 79, 0.8);
      border-color: #ff4d4f;
    }

    &.level-二级 {
      background: rgba(255, 152, 0, 0.8);
      border-color: #ff9800;
    }

    &.level-三级 {
      background: rgba(255, 193, 7, 0.8);
      border-color: #ffc107;
    }

    &.level-四级 {
      background: rgba(24, 144, 255, 0.8);
      border-color: #1890ff;
    }
  }
}

.record-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.record-title {
  font-size: 12px;
  font-weight: 500;
  color: #ffffff;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);

  .record-device {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .record-time {
    color: rgba(255, 255, 255, 0.5);
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
