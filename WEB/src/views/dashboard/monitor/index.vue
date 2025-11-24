<template>
  <div class="monitor-dashboard">
    <!-- 顶部头部 -->
    <MonitorHeader />
    
    <!-- 主体内容 -->
    <div class="monitor-content">
      <!-- 左侧导航 -->
      <MonitorSidebar 
        :selected-device="selectedDevice"
        @device-change="handleDeviceChange"
      />
      
      <!-- 中央视频监控区域 -->
      <div class="monitor-center">
        <VideoMonitor 
          :device="selectedDevice"
          :video-list="videoList"
        />
      </div>
      
      <!-- 右侧告警信息 -->
      <AlarmPanel 
        :alarm-list="alarmList"
        :today-alarm-count="todayAlarmCount"
      />
    </div>
    
    <!-- 底部监控记录 -->
    <RecordPanel 
      :record-list="recordList"
      :current-time="currentTime"
      @time-change="handleTimeChange"
    />
    
    <!-- 底部状态栏 -->
    <div class="status-bar">
      <span class="status-item">全部</span>
      <span class="status-item online">在线{{ onlineCount }}</span>
      <span class="status-item offline">离线{{ offlineCount }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import MonitorHeader from './components/Header.vue'
import MonitorSidebar from './components/Sidebar.vue'
import VideoMonitor from './components/VideoMonitor.vue'
import AlarmPanel from './components/AlarmPanel.vue'
import RecordPanel from './components/RecordPanel.vue'

defineOptions({
  name: 'MonitorDashboard'
})

// 选中的设备
const selectedDevice = ref<any>({
  id: '1',
  name: '华南小区西四路23号',
  location: '开发区华南小区西四路23号'
})

// 视频列表
const videoList = ref([
  { id: '1', url: '', name: '主视频' },
  { id: '2', url: '', name: '视频1' },
  { id: '3', url: '', name: '视频2' },
  { id: '4', url: '', name: '视频3' },
  { id: '5', url: '', name: '视频4' },
  { id: '6', url: '', name: '视频5' },
  { id: '7', url: '', name: '视频6' }
])

// 告警列表
const alarmList = ref([
  {
    id: '1',
    type: 'fire',
    title: '社区起火',
    level: '一级',
    location: '华南小区一期1-1入户电梯',
    time: '2025-08-08 12:12:12',
    image: ''
  }
])

// 今日告警次数
const todayAlarmCount = ref(8)

// 监控记录列表
const recordList = ref([
  { id: '1', time: '2025-08-08 12:00:00', thumbnail: '' },
  { id: '2', time: '2025-08-08 12:20:00', thumbnail: '' },
  { id: '3', time: '2025-08-08 12:40:00', thumbnail: '' },
  { id: '4', time: '2025-08-08 12:21:00', thumbnail: '' },
  { id: '5', time: '2025-08-08 13:00:00', thumbnail: '' },
  { id: '6', time: '2025-08-08 13:20:00', thumbnail: '' }
])

// 当前时间
const currentTime = ref('2025-08-08 12:12:12')

// 设备统计
const onlineCount = ref(678)
const offlineCount = ref(129)

// 定时器
let timeTimer: any = null

// 设备切换
const handleDeviceChange = (device: any) => {
  selectedDevice.value = device
  // 这里可以加载新设备的视频流
}

// 时间变化
const handleTimeChange = (time: string) => {
  currentTime.value = time
  // 这里可以加载对应时间的视频
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

onMounted(() => {
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  // 这里可以加载初始数据
})

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer)
  }
})
</script>

<style lang="less" scoped>
.monitor-dashboard {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #0a1929 0%, #1a2332 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #ffffff;
}

.monitor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0 16px 16px 16px;
  gap: 16px;
}

.monitor-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.status-bar {
  height: 40px;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  font-size: 14px;
  
  .status-item {
    color: rgba(255, 255, 255, 0.8);
    
    &.online {
      color: #52c41a;
    }
    
    &.offline {
      color: #ff4d4f;
    }
  }
}
</style>
