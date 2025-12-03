<template>
  <div class="monitor-dashboard">
    <!-- 顶部头部 -->
    <MonitorHeader :active-videos="activeVideos" />
    
    <!-- 主体内容 -->
    <div class="monitor-content">
      <!-- 左侧导航 -->
      <MonitorSidebar 
        :selected-device="selectedDevice"
        @device-change="handleDeviceChange"
        @device-play="handleDevicePlay"
      />
      
      <!-- 中央视频监控区域 -->
      <div class="monitor-center">
        <VideoMonitor 
          ref="videoMonitorRef"
          :device="selectedDevice"
          :video-list="videoList"
          @video-list-change="handleVideoListChange"
        />
      </div>
      
      <!-- 右侧告警信息 -->
      <AlarmPanel 
        :alarm-list="alarmList"
        :today-alarm-count="todayAlarmCount"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import MonitorHeader from './components/Header.vue'
import MonitorSidebar from './components/Sidebar.vue'
import VideoMonitor from './components/VideoMonitor.vue'
import AlarmPanel from './components/AlarmPanel.vue'
import { useMessage } from '@/hooks/web/useMessage'
import { queryAlarmList, getDashboardStatistics } from '@/api/device/calculate'

defineOptions({
  name: 'MonitorDashboard'
})

const { createMessage } = useMessage()
const videoMonitorRef = ref<InstanceType<typeof VideoMonitor> | null>(null)

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

// 正在播放的视频列表
const activeVideos = ref<any[]>([])

// 告警列表
const alarmList = ref<any[]>([])

// 今日告警次数
const todayAlarmCount = ref(0)

// 加载告警列表
const loadAlarmList = async () => {
  try {
    const response = await queryAlarmList({
      pageNo: 1,
      pageSize: 7, // 只加载最近7条
    })
    
    if (response && response.alert_list) {
      // 处理告警数据，确保格式正确
      alarmList.value = response.alert_list.map((item: any) => {
        // 构建图片URL - 直接使用 image_path
        let imageUrl = null
        if (item.image_path) {
          imageUrl = item.image_path
        }
        
        // 处理告警级别
        let level = item.level || '告警'
        if (!item.level) {
          // 根据event类型设置默认级别
          if (item.event && (item.event.includes('火') || item.event.includes('fire'))) {
            level = '一级'
          } else if (item.event && (item.event.includes('烟') || item.event.includes('smoke'))) {
            level = '二级'
          } else {
            level = '三级'
          }
        }
        
        // 处理告警类型
        let type = 'default'
        if (item.event) {
          if (item.event.includes('火') || item.event.includes('fire')) {
            type = 'fire'
          } else if (item.event.includes('烟') || item.event.includes('smoke')) {
            type = 'smoke'
          } else if (item.event.includes('入侵') || item.event.includes('intrusion')) {
            type = 'intrusion'
          }
        }
        
        return {
          id: item.id || item.alert_id,
          type: type,
          title: item.event || item.title || '未知事件',
          level: level,
          location: item.device_name || item.location || '未知设备',
          time: item.time || item.alert_time || item.created_at || '',
          image: imageUrl,
          device_name: item.device_name,
          device_id: item.device_id
        }
      })
    } else {
      alarmList.value = []
    }
  } catch (error) {
    console.error('加载告警列表失败', error)
    createMessage.error('加载告警列表失败')
    alarmList.value = []
  }
}

// 加载今日告警次数
const loadTodayAlarmCount = async () => {
  try {
    const statsResponse = await getDashboardStatistics()
    if (statsResponse) {
      todayAlarmCount.value = statsResponse.today_alarm_count || 0
    } else {
      todayAlarmCount.value = 0
    }
  } catch (error) {
    console.error('加载今日告警次数失败', error)
    todayAlarmCount.value = 0
  }
}

// 刷新定时器
let refreshTimer: any = null

// 动态添加样式，隐藏顶部导航栏、标签页和左侧菜单，让大屏覆盖整个屏幕
onMounted(() => {
  const style = document.createElement('style')
  style.id = 'monitor-dashboard-style'
  style.textContent = `
    .ant-layout-header,
    .layout-multiple-header,
    .layout-tabs,
    .layout-footer {
      display: none !important;
    }
    .ant-layout-sider,
    .layout-sider-wrapper {
      display: none !important;
    }
    .ant-layout-content,
    .layout-content {
      padding: 0 !important;
      margin: 0 !important;
      height: 100vh !important;
      overflow: hidden !important;
    }
    .ant-layout-main {
      height: 100vh !important;
      overflow: hidden !important;
      margin-left: 0 !important;
    }
  `
  document.head.appendChild(style)
  
  // 初始加载告警列表和今日告警次数（使用 Promise.all 确保同时发起，但去重机制会确保只发送一次请求）
  Promise.all([
    loadAlarmList(),
    loadTodayAlarmCount()
  ]).catch(error => {
    console.error('初始加载失败', error)
  })
  
  // 错峰刷新：延迟3秒开始，每5秒刷新一次告警列表和今日告警次数（3秒、8秒、13秒...）
  setTimeout(() => {
    Promise.all([
      loadAlarmList(),
      loadTodayAlarmCount()
    ]).catch(error => {
      console.error('刷新数据失败', error)
    })
    refreshTimer = setInterval(() => {
      Promise.all([
        loadAlarmList(),
        loadTodayAlarmCount()
      ]).catch(error => {
        console.error('定时刷新失败', error)
      })
    }, 5000)
  }, 3000)
})

onUnmounted(() => {
  const style = document.getElementById('monitor-dashboard-style')
  if (style) {
    document.head.removeChild(style)
  }
  
  // 清理定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

// 设备切换
const handleDeviceChange = (device: any) => {
  selectedDevice.value = device
  // 这里可以加载新设备的视频流
}

// 设备播放
const handleDevicePlay = (device: any) => {
  if (videoMonitorRef.value) {
    videoMonitorRef.value.playDeviceStream(device)
  }
}

// 处理视频列表变化
const handleVideoListChange = (videos: any[]) => {
  activeVideos.value = videos
}
</script>

<style lang="less">
.monitor-dashboard {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  max-height: 100vh;
  background: linear-gradient(25deg, #0f2249, #182e5a 20%, #0f2249 40%, #182e5a 60%, #0f2249 80%, #182e5a 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #ffffff;
  font-size: 14px;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  z-index: 9999;

  a {
    text-decoration: none;
    color: #399bff;
  }
}

.monitor-content {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
  padding: 0 16px 16px 16px;
  gap: 16px;
  box-sizing: border-box;
  margin-top: 8px;
}

.monitor-center {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
