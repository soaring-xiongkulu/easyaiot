<template>
  <div class="alarm-panel">
    <div class="panel-header">
      <div class="header-title">告警信息</div>
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
            v-if="alarm.image" 
            :src="alarm.image" 
            alt="告警图片"
            class="alarm-img"
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
          <div class="alarm-title">{{ alarm.title }}</div>
          <div class="alarm-meta">
            <span 
              :class="['alarm-level', `level-${alarm.level}`]"
            >
              {{ alarm.level }}
            </span>
            <span class="alarm-location">{{ alarm.location }}</span>
          </div>
          <div class="alarm-time">{{ alarm.time }}</div>
        </div>
      </div>
      
      <div v-if="alarmList.length === 0" class="empty-state">
        <Icon icon="ant-design:inbox-outlined" :size="48" />
        <div class="empty-text">暂无告警信息</div>
      </div>
    </div>
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
</script>

<style lang="less" scoped>
.alarm-panel {
  width: 320px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  height: 60px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
  }
  
  .header-count {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    
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
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border-left: 3px solid #ff4d4f;
  transition: all 0.3s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(4px);
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

.alarm-level {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
  border: 1px solid #ff4d4f;
  
  &.level-一级 {
    background: rgba(255, 77, 79, 0.2);
    color: #ff4d4f;
    border-color: #ff4d4f;
  }
  
  &.level-二级 {
    background: rgba(255, 152, 0, 0.2);
    color: #ff9800;
    border-color: #ff9800;
  }
  
  &.level-三级 {
    background: rgba(255, 193, 7, 0.2);
    color: #ffc107;
    border-color: #ffc107;
  }
  
  &.level-四级 {
    background: rgba(24, 144, 255, 0.2);
    color: #1890ff;
    border-color: #1890ff;
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
