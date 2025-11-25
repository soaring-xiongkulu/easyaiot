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
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import MonitorHeader from './components/Header.vue'
import MonitorSidebar from './components/Sidebar.vue'
import VideoMonitor from './components/VideoMonitor.vue'
import AlarmPanel from './components/AlarmPanel.vue'

defineOptions({
  name: 'MonitorDashboard'
})

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
})

onUnmounted(() => {
  const style = document.getElementById('monitor-dashboard-style')
  if (style) {
    document.head.removeChild(style)
  }
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

// 设备切换
const handleDeviceChange = (device: any) => {
  selectedDevice.value = device
  // 这里可以加载新设备的视频流
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
}

.monitor-center {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
