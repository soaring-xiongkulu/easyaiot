<template>
  <div class="record-panel">
    <div class="panel-header">
      <div class="header-title">监控记录</div>
      <div class="header-controls">
        <a-range-picker
          v-model:value="timeRange"
          :show-time="{ format: 'HH:mm:ss' }"
          format="YYYY-MM-DD HH:mm:ss"
          placeholder="['开始时间', '结束时间']"
          class="time-picker"
          @change="handleTimeRangeChange"
        />
        <a-button type="primary" @click="handleQuery" class="query-btn">
          查询
        </a-button>
      </div>
    </div>
    
    <div class="panel-content">
      <!-- 缩略图列表 -->
      <div class="thumbnail-list">
        <div
          v-for="record in recordList"
          :key="record.id"
          :class="['thumbnail-item', { active: selectedRecordId === record.id }]"
          @click="handlePlay(record)"
        >
          <div class="thumbnail-image">
            <img 
              v-if="record.thumbnail" 
              :src="record.thumbnail" 
              alt="缩略图"
              class="thumbnail-img"
            />
            <div v-else class="thumbnail-placeholder">
              <Icon icon="ant-design:video-camera-outlined" :size="24" />
            </div>
            <!-- 播放图标 -->
            <div class="play-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="24" cy="24" r="24" fill="rgba(0, 0, 0, 0.5)"/>
                <path d="M18 14L34 24L18 34V14Z" fill="white"/>
              </svg>
            </div>
            <div class="thumbnail-time">{{ formatTime(record.time) }}</div>
          </div>
        </div>
      </div>
      
      <!-- 时间轴 -->
      <div class="timeline-container">
        <div class="timeline">
          <div
            v-for="hour in hours"
            :key="hour"
            class="timeline-hour"
            :style="{ left: `${(hour / 24) * 100}%` }"
          >
            <div class="hour-label">{{ formatHour(hour) }}</div>
            <div class="hour-line"></div>
          </div>
          
          <!-- 当前时间指示器 -->
          <div
            class="timeline-indicator"
            :style="{ left: `${(currentHour / 24) * 100}%` }"
          >
            <div class="indicator-line"></div>
            <div class="indicator-time">{{ formatCurrentTime }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 视频播放器弹窗 -->
    <DialogPlayer @register="registerPlayerModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, nextTick } from 'vue'
import { DatePicker, Button } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import dayjs, { Dayjs } from 'dayjs'
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue'
import { useModal } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import { queryAlertRecord } from '@/api/device/calculate'

const { RangePicker } = DatePicker
const { createMessage } = useMessage()

// 播放器弹窗
const [registerPlayerModal, { openModal: openPlayerModal }] = useModal()

// 防重复提示：记录最近提示的时间和内容
let lastVideoErrorTime = 0
let lastVideoErrorMsg = ''

defineOptions({
  name: 'RecordPanel'
})

const props = defineProps<{
  recordList?: any[]
  currentTime?: string
  deviceId?: string | number // 设备ID，用于查询录像
}>()

const emit = defineEmits<{
  (e: 'time-change', time: string): void
}>()

const timeRange = ref<[Dayjs, Dayjs] | null>(null)
const selectedRecordId = ref<string | null>(null)

// 时间轴小时标记（每2小时一个）
const hours = computed(() => {
  return Array.from({ length: 13 }, (_, i) => i * 2)
})

// 当前小时（0-24）
const currentHour = computed(() => {
  if (!props.currentTime) return 12
  const hour = parseInt(props.currentTime.split(' ')[1]?.split(':')[0] || '12')
  const minute = parseInt(props.currentTime.split(' ')[1]?.split(':')[1] || '0')
  return hour + minute / 60
})

// 格式化当前时间（用于时间轴显示）
const formatCurrentTime = computed(() => {
  if (!props.currentTime) return '12:00'
  return props.currentTime.split(' ')[1]?.substring(0, 5) || '12:00'
})

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return ''
  return time.split(' ')[1]?.substring(0, 5) || time
}

// 格式化小时
const formatHour = (hour: number) => {
  return `${String(hour).padStart(2, '0')}:00`
}

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

// 播放录像
const handlePlay = async (record: any) => {
  console.log('handlePlay 被调用，record:', record)
  
  // 更新选中状态和时间
  selectedRecordId.value = record.id
  emit('time-change', record.time)
  
  // 检查 openPlayerModal 是否可用
  if (!openPlayerModal || typeof openPlayerModal !== 'function') {
    console.error('openPlayerModal 不可用:', openPlayerModal)
    createMessage.error('播放器未初始化，请刷新页面重试')
    return
  }
  
  try {
    // 如果record直接有video_url，直接使用
    if (record.video_url || record.url) {
      const videoUrl = getVideoUrl(record.video_url || record.url)
      console.log('使用 record 中的 video_url:', videoUrl)
      
      try {
        await nextTick()
        openPlayerModal(true, {
          id: record.device_id || props.deviceId || 0,
          http_stream: videoUrl,
        })
        console.log('成功调用 openPlayerModal')
      } catch (modalError: any) {
        console.error('调用 openPlayerModal 失败:', modalError)
        createMessage.error('打开播放器失败: ' + (modalError?.message || '未知错误'))
      }
      return
    }
  
    // 如果没有video_url，需要根据device_id和time查询
    const deviceId = record.device_id || props.deviceId
    if (!deviceId || !record.time) {
      console.warn('缺少必要信息:', { deviceId, time: record.time })
      createMessage.warn('缺少必要信息：设备ID或录像时间')
      return
    }
    
    console.log('开始查询录像，deviceId:', deviceId, 'time:', record.time)
    
    // 查询录像URL
    const result = await queryAlertRecord({
      device_id: String(deviceId),
      alert_time: record.time,
      time_range: 60, // 前后60秒
    })

    console.log('查询录像结果:', result)

    if (result && result.video_url) {
      // 处理录像URL，添加前缀
      const videoUrl = getVideoUrl(result.video_url)
      console.log('获取到录像URL:', videoUrl)
      
      // 使用DialogPlayer播放，参数格式：{ id, http_stream }
      try {
        await nextTick()
        openPlayerModal(true, {
          id: deviceId,
          http_stream: videoUrl,
        })
        console.log('成功调用 openPlayerModal')
        // 重置错误记录
        lastVideoErrorTime = 0
        lastVideoErrorMsg = ''
      } catch (modalError: any) {
        console.error('调用 openPlayerModal 失败:', modalError)
        createMessage.error('打开播放器失败: ' + (modalError?.message || '未知错误'))
      }
    } else {
      // 检查是否是业务错误（code=400）
      const errorMsg = result?.message || '暂未找到该时间段的录像文件'
      console.warn('未找到录像:', errorMsg)
      showVideoErrorOnce(errorMsg)
    }
  } catch (error: any) {
    console.error('播放录像失败:', error)
    // 处理业务错误（HTTP 200但code=400）
    const errorData = error?.response?.data || error?.data
    if (errorData && errorData.code === 400) {
      const errorMsg = errorData.message || '暂未找到该时间段的录像文件'
      showVideoErrorOnce(errorMsg)
    } else {
      // 其他错误
      const errorMsg = error?.response?.data?.message || error?.message || '播放录像失败，请稍后重试'
      showVideoErrorOnce(errorMsg)
    }
  }
}

// 时间范围变化
const handleTimeRangeChange = (dates: [Dayjs, Dayjs] | null) => {
  timeRange.value = dates
}

// 查询
const handleQuery = () => {
  if (timeRange.value) {
    const [start, end] = timeRange.value
    // 这里可以触发查询逻辑
    console.log('查询时间范围:', start.format('YYYY-MM-DD HH:mm:ss'), end.format('YYYY-MM-DD HH:mm:ss'))
  }
}
</script>

<style lang="less" scoped>
.record-panel {
  height: 200px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 0 16px 16px 16px;
}

.panel-header {
  height: 50px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  
  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
  }
  
  .header-controls {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .time-picker {
      :deep(.ant-picker) {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        
        .ant-picker-input > input {
          color: #ffffff;
          
          &::placeholder {
            color: rgba(255, 255, 255, 0.4);
          }
        }
        
        .ant-picker-suffix {
          color: rgba(255, 255, 255, 0.6);
        }
      }
    }
    
    .query-btn {
      background: #1890ff;
      border-color: #1890ff;
      
      &:hover {
        background: #40a9ff;
        border-color: #40a9ff;
      }
    }
  }
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  gap: 12px;
}

.thumbnail-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  
  &::-webkit-scrollbar {
    height: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
    
    &:hover {
      background: rgba(255, 255, 255, 0.3);
    }
  }
}

.thumbnail-item {
  flex-shrink: 0;
  width: 120px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-4px);
    
    .thumbnail-image {
      border-color: #1890ff;
      box-shadow: 0 0 8px rgba(24, 144, 255, 0.3);
    }
  }
  
  &.active {
    .thumbnail-image {
      border-color: #1890ff;
      box-shadow: 0 0 8px rgba(24, 144, 255, 0.5);
    }
  }
}

.thumbnail-image {
  width: 100%;
  height: 80px;
  background: #000000;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  border: 2px solid transparent;
  transition: all 0.3s;
  
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
    color: rgba(255, 255, 255, 0.3);
  }
  
  .play-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: 10;
  }
  
  &:hover .play-icon {
    opacity: 1;
  }
  
  .thumbnail-time {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
    color: #ffffff;
    font-size: 11px;
    padding: 4px 6px;
    text-align: center;
    z-index: 5;
  }
}

.timeline-container {
  height: 60px;
  position: relative;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 8px 0;
}

.timeline {
  width: 100%;
  height: 100%;
  position: relative;
}

.timeline-hour {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  
  .hour-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
    margin-bottom: 4px;
  }
  
  .hour-line {
    width: 1px;
    height: 20px;
    background: rgba(255, 255, 255, 0.2);
  }
}

.timeline-indicator {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  z-index: 10;
  
  .indicator-line {
    width: 2px;
    height: 100%;
    background: #ffc107;
    box-shadow: 0 0 4px rgba(255, 193, 7, 0.8);
  }
  
  .indicator-time {
    position: absolute;
    top: -20px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 11px;
    color: #ffc107;
    background: rgba(0, 0, 0, 0.6);
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
  }
}
</style>
