<template>
  <div class="alarm-panel">
    <div class="panel-header">
      <div class="header-title">告警事件</div>
      <div class="header-count">
        今日告警 <span class="count-number">{{ todayAlarmCount }}</span> 次
      </div>
    </div>
    
    <div class="panel-content">
      <div
        v-for="alarm in alarmList"
        :key="alarm.id"
        class="alarm-item"
      >
        <div class="alarm-image">
          <img 
            v-if="getImageUrl(alarm) && !alarm.imageError" 
            :src="getImageUrl(alarm)" 
            alt="告警图片"
            class="alarm-img"
            @error="handleImageError(alarm)"
            @load="handleImageLoad(alarm)"
          />
          <div v-else class="alarm-icon">
            <Icon 
              :icon="getAlarmIcon(alarm.type)" 
              :size="32"
              :color="getAlarmColor(alarm.level)"
            />
          </div>
        </div>
        
        <div class="alarm-info">
          <div class="alarm-title">{{ alarm.title || alarm.event || '未知事件' }}</div>
          <div class="alarm-meta">
            <span 
              :class="['task-type-tag', getTaskTypeClass(alarm)]"
            >
              {{ getTaskTypeText(alarm) }}
            </span>
            <span class="alarm-location">{{ alarm.device_name || alarm.location || '未知设备' }}</span>
          </div>
          <div class="alarm-time">{{ alarm.time }}</div>
        </div>
      </div>
      
      <div v-if="alarmList.length === 0" class="empty-state">
        <Icon icon="ant-design:inbox-outlined" :size="48" />
        <div class="empty-text">暂无告警信息</div>
      </div>
    </div>
    <div class="boxfoot"></div>
  </div>
</template>

<script lang="ts" setup>
import { Icon } from '@/components/Icon'

defineOptions({
  name: 'AlarmPanel'
})

const props = defineProps<{
  alarmList?: any[]
  todayAlarmCount?: number
}>()

// 获取告警图标
const getAlarmIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    fire: 'ant-design:fire-outlined',
    smoke: 'ant-design:cloud-outlined',
    intrusion: 'ant-design:warning-outlined',
    default: 'ant-design:exclamation-circle-outlined'
  }
  return iconMap[type] || iconMap.default
}

// 获取告警颜色
const getAlarmColor = (level: string) => {
  const colorMap: Record<string, string> = {
    '一级': '#ff4d4f',
    '二级': '#ff9800',
    '三级': '#ffc107',
    '四级': '#1890ff'
  }
  return colorMap[level] || '#ff4d4f'
}

// 获取任务类型
const getTaskType = (alarm: any): string | null => {
  // 优先从 information 字段中获取 task_type
  let taskType = null
  if (alarm.information) {
    if (typeof alarm.information === 'object' && alarm.information.task_type) {
      taskType = alarm.information.task_type
    } else if (typeof alarm.information === 'string') {
      try {
        const info = JSON.parse(alarm.information)
        taskType = info?.task_type
      } catch (e) {
        // 解析失败，忽略
      }
    }
  }
  
  // 如果 information 中没有，尝试从 alarm 本身获取
  if (!taskType && alarm.task_type) {
    taskType = alarm.task_type
  }
  
  return taskType
}

// 获取任务类型文本
const getTaskTypeText = (alarm: any): string => {
  const taskType = getTaskType(alarm)
  
  // 根据 task_type 返回文本
  if (taskType === 'snap' || taskType === 'snapshot') {
    return '抓拍'
  } else {
    return '实时'
  }
}

// 获取任务类型样式类
const getTaskTypeClass = (alarm: any): string => {
  const taskType = getTaskType(alarm)
  
  // 根据 task_type 返回样式类
  if (taskType === 'snap' || taskType === 'snapshot') {
    return 'task-type-snap'
  } else {
    return 'task-type-realtime'
  }
}

// 获取图片URL
const getImageUrl = (alarm: any): string | null => {
  if (!alarm.image) return null
  
  const imagePath = alarm.image
  
  // 如果是完整URL，直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath
  }
  
  // 如果是MinIO路径（以/api/v1/buckets开头），添加前端启动地址前缀
  if (imagePath.startsWith('/api/v1/buckets')) {
    return `${window.location.origin}${imagePath}`
  }
  
  // 如果是相对路径（以/api开头），添加前端启动地址前缀
  if (imagePath.startsWith('/api/')) {
    return `${window.location.origin}${imagePath}`
  }
  
  // 如果是绝对路径（以/opt/、/data/、/var/等系统路径开头），通过API端点获取
  if (imagePath.startsWith('/opt/') || imagePath.startsWith('/data/') || imagePath.startsWith('/var/') || imagePath.startsWith('/usr/') || imagePath.startsWith('/home/')) {
    const apiUrl = import.meta.env.VITE_GLOB_API_URL || ''
    // 对路径进行URL编码
    const encodedPath = encodeURIComponent(imagePath)
    return apiUrl ? `${apiUrl}/video/alert/image?path=${encodedPath}` : `/video/alert/image?path=${encodedPath}`
  }
  
  // 其他以/开头的路径，也通过API端点获取（可能是其他绝对路径）
  if (imagePath.startsWith('/')) {
    const apiUrl = import.meta.env.VITE_GLOB_API_URL || ''
    // 对路径进行URL编码
    const encodedPath = encodeURIComponent(imagePath)
    return apiUrl ? `${apiUrl}/video/alert/image?path=${encodedPath}` : `/video/alert/image?path=${encodedPath}`
  }
  
  // 其他情况直接返回
  return imagePath
}

// 处理图片加载错误
const handleImageError = (alarm: any) => {
  // 标记图片加载失败，显示占位图标
  alarm.imageError = true
}

// 处理图片加载成功
const handleImageLoad = (alarm: any) => {
  // 确保清除错误标记
  alarm.imageError = false
}
</script>

<style lang="less" scoped>
.alarm-panel {
  width: 320px;
  height: 100%;
  padding: 0;
  background: linear-gradient(135deg, rgba(15, 34, 73, 0.8), rgba(24, 46, 90, 0.6));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  border: 1px solid rgba(52, 134, 218, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 0 30px rgba(52, 134, 218, 0.1);
  border-radius: 8px;
  padding: 3px;
  
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

.panel-header {
  text-align: center;
  background: rgba(52, 134, 218, 0.08);
  border-bottom: 1px solid rgba(52, 134, 218, 0.3);
  color: #fff;
  font-size: 16px;
  height: 60px;
  line-height: 40px;
  letter-spacing: .05rem;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  justify-content: center;
  position: relative;
  z-index: 1;
  
  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
    line-height: 1.2;
  }
  
  .header-count {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.2;
    
    .count-number {
      color: #ff4d4f;
      font-weight: 600;
      font-size: 18px;
    }
  }
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  
  &::-webkit-scrollbar {
    width: 6px;
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

.alarm-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(52, 134, 218, 0.15), rgba(48, 82, 174, 0.1));
  border: 1px solid rgba(52, 134, 218, 0.3);
  border-radius: 6px;
  border-left: 3px solid #ff4d4f;
  transition: all 0.3s;
  position: relative;
  
  &:hover {
    background: linear-gradient(135deg, rgba(52, 134, 218, 0.25), rgba(48, 82, 174, 0.15));
    border-color: rgba(52, 134, 218, 0.6);
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(52, 134, 218, 0.2);
  }
  
  &:last-child {
    margin-bottom: 0;
  }
}

.alarm-image {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  
  .alarm-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    cursor: pointer;
  }
  
  .alarm-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.alarm-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.alarm-title {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  line-height: 1.4;
}

.alarm-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-type-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &.task-type-realtime {
    background: #3B82F6;
    color: #ffffff;
    border: 1px solid #2563EB;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
      background: #2563EB;
    }
  }
  
  &.task-type-snap {
    background: #10B981;
    color: #ffffff;
    border: 1px solid #059669;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
      background: #059669;
    }
  }
}

.alarm-location {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.4);
  
  .empty-text {
    margin-top: 16px;
    font-size: 14px;
  }
}

</style>
