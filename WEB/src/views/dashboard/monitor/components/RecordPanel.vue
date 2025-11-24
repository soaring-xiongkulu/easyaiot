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
          @click="handleSelectRecord(record)"
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
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { DatePicker, Button } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import dayjs, { Dayjs } from 'dayjs'

const { RangePicker } = DatePicker

defineOptions({
  name: 'RecordPanel'
})

const props = defineProps<{
  recordList?: any[]
  currentTime?: string
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

// 选择记录
const handleSelectRecord = (record: any) => {
  selectedRecordId.value = record.id
  emit('time-change', record.time)
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
