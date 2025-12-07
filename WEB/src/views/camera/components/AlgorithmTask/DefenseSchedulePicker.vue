<template>
  <div class="defense-schedule-picker">
    <div class="mode-selector">
      <a-select
        v-model:value="defenseMode"
        :disabled="disabled"
        @change="handleModeChange"
        :options="modeOptions"
        style="width: 200px"
        placeholder="请选择布防模式"
      />
    </div>
    
    <div class="schedule-grid" v-if="defenseMode === 'half'">
      <div class="grid-header">
        <div class="time-label"></div>
        <div
          v-for="day in weekDays"
          :key="day.value"
          class="day-header"
        >
          {{ day.label }}
        </div>
      </div>
      <div class="grid-body">
        <div
          v-for="hour in 24"
          :key="hour"
          class="grid-row"
        >
          <div class="time-label">{{ formatHour(hour - 1) }}</div>
          <div
            v-for="day in weekDays"
            :key="`${day.value}-${hour - 1}`"
            class="grid-cell"
            :class="{ active: isActive(day.value, hour - 1) }"
            @mousedown="(e) => handleMouseDown(e, day.value, hour - 1)"
            @mouseenter="handleMouseEnter(day.value, hour - 1)"
            @mouseup="handleMouseUp"
          ></div>
        </div>
      </div>
    </div>
    
    <div class="schedule-grid" v-else-if="defenseMode === 'day'">
      <div class="grid-header">
        <div class="time-label"></div>
        <div
          v-for="day in weekDays"
          :key="day.value"
          class="day-header"
        >
          {{ day.label }}
        </div>
      </div>
      <div class="grid-body">
        <div
          v-for="hour in 24"
          :key="hour"
          class="grid-row"
        >
          <div class="time-label">{{ formatHour(hour - 1) }}</div>
          <div
            v-for="day in weekDays"
            :key="`${day.value}-${hour - 1}`"
            class="grid-cell"
            :class="{ active: isDayTime(hour - 1) }"
          ></div>
        </div>
      </div>
    </div>
    
    <div class="schedule-grid" v-else-if="defenseMode === 'night'">
      <div class="grid-header">
        <div class="time-label"></div>
        <div
          v-for="day in weekDays"
          :key="day.value"
          class="day-header"
        >
          {{ day.label }}
        </div>
      </div>
      <div class="grid-body">
        <div
          v-for="hour in 24"
          :key="hour"
          class="grid-row"
        >
          <div class="time-label">{{ formatHour(hour - 1) }}</div>
          <div
            v-for="day in weekDays"
            :key="`${day.value}-${hour - 1}`"
            class="grid-cell"
            :class="{ active: isNightTime(hour - 1) }"
          ></div>
        </div>
      </div>
    </div>
    
    <div class="schedule-grid" v-else-if="defenseMode === 'full'">
      <div class="grid-header">
        <div class="time-label"></div>
        <div
          v-for="day in weekDays"
          :key="day.value"
          class="day-header"
        >
          {{ day.label }}
        </div>
      </div>
      <div class="grid-body">
        <div
          v-for="hour in 24"
          :key="hour"
          class="grid-row"
        >
          <div class="time-label">{{ formatHour(hour - 1) }}</div>
          <div
            v-for="day in weekDays"
            :key="`${day.value}-${hour - 1}`"
            class="grid-cell active"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, computed, onUnmounted } from 'vue';

interface Props {
  modelValue?: {
    mode?: string;
    schedule?: number[][]; // 7天×24小时的二维数组，1表示激活，0表示未激活
  };
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({ mode: 'full', schedule: Array(7).fill(null).map(() => Array(24).fill(1)) }),
  disabled: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: { mode: string; schedule: number[][] }];
}>();

const weekDays = [
  { label: '周一', value: 0 },
  { label: '周二', value: 1 },
  { label: '周三', value: 2 },
  { label: '周四', value: 3 },
  { label: '周五', value: 4 },
  { label: '周六', value: 5 },
  { label: '周日', value: 6 },
];

const modeOptions = [
  { label: '全防模式', value: 'full' },
  { label: '半防模式', value: 'half' },
  { label: '日间模式', value: 'day' },
  { label: '夜间模式', value: 'night' },
];

const defenseMode = ref<string>(props.modelValue?.mode || 'half');
const schedule = ref<number[][]>(
  props.modelValue?.schedule || Array(7).fill(null).map(() => Array(24).fill(0))
);

// 拖拽状态
const isDragging = ref(false);
const dragStart = ref<{ day: number; hour: number; targetValue?: number } | null>(null);
const dragEnd = ref<{ day: number; hour: number } | null>(null);

// 监听外部值变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      const newMode = newVal.mode || 'full';
      const newSchedule = newVal.schedule;
      
      // 如果模式改变了，需要同步更新内部状态
      if (defenseMode.value !== newMode) {
        defenseMode.value = newMode;
      }
      
      // 如果提供了schedule，使用提供的schedule；否则根据模式生成默认schedule
      if (newSchedule) {
        schedule.value = JSON.parse(JSON.stringify(newSchedule));
      } else {
        // 如果没有提供schedule，根据模式生成默认值
        if (newMode === 'full') {
          schedule.value = Array(7).fill(null).map(() => Array(24).fill(1));
        } else if (newMode === 'day') {
          schedule.value = Array(7).fill(null).map(() =>
            Array(24).fill(0).map((_, hour) => (hour >= 6 && hour < 21 ? 1 : 0))
          );
        } else if (newMode === 'night') {
          schedule.value = Array(7).fill(null).map(() =>
            Array(24).fill(0).map((_, hour) => (hour >= 21 || hour < 6 ? 1 : 0))
          );
        } else {
          // 半防模式：全部清空
          schedule.value = Array(7).fill(null).map(() => Array(24).fill(0));
        }
      }
    }
  },
  { deep: true, immediate: true }
);

// 格式化小时显示
const formatHour = (hour: number) => {
  return `${hour.toString().padStart(2, '0')}:00`;
};

// 判断是否为日间（6:00-21:00）
const isDayTime = (hour: number) => {
  return hour >= 6 && hour < 21;
};

// 判断是否为夜间（21:00-6:00）
const isNightTime = (hour: number) => {
  return hour >= 21 || hour < 6;
};

// 判断某个时段是否激活
const isActive = (day: number, hour: number) => {
  if (defenseMode.value === 'full') {
    return true;
  }
  if (defenseMode.value === 'day') {
    return isDayTime(hour);
  }
  if (defenseMode.value === 'night') {
    return isNightTime(hour);
  }
  // 半防模式：检查schedule数组
  return schedule.value[day]?.[hour] === 1;
};

// 处理模式变化
const handleModeChange = (value: string) => {
  const mode = value;
  defenseMode.value = mode;
  
  if (mode === 'full') {
    // 全防模式：全部填充
    schedule.value = Array(7).fill(null).map(() => Array(24).fill(1));
  } else if (mode === 'day') {
    // 日间模式：6:00-21:00填充
    schedule.value = Array(7).fill(null).map(() =>
      Array(24).fill(0).map((_, hour) => (hour >= 6 && hour < 21 ? 1 : 0))
    );
  } else if (mode === 'night') {
    // 夜间模式：21:00-6:00填充
    schedule.value = Array(7).fill(null).map(() =>
      Array(24).fill(0).map((_, hour) => (hour >= 21 || hour < 6 ? 1 : 0))
    );
  } else if (mode === 'half') {
    // 半防模式：全部清空，让用户自己选
    schedule.value = Array(7).fill(null).map(() => Array(24).fill(0));
  }
  
  emitValue();
};

// 鼠标按下
const handleMouseDown = (e: MouseEvent, day: number, hour: number) => {
  if (props.disabled || defenseMode.value !== 'half') return;
  // 只处理左键
  if (e.button !== 0) return;
  
  e.preventDefault();
  e.stopPropagation();
  
  isDragging.value = true;
  dragStart.value = { day, hour };
  dragEnd.value = { day, hour };
  
  // 记录起始单元格的原始状态
  const startValue = schedule.value[day][hour];
  // 计算目标值（切换后的值）
  const targetValue = startValue === 1 ? 0 : 1;
  
  // 更新拖拽状态中的目标值
  if (dragStart.value) {
    dragStart.value.targetValue = targetValue;
  }
  
  // 切换当前单元格状态
  schedule.value[day][hour] = targetValue;
  
  emitValue();
};

// 鼠标移动
const handleMouseEnter = (day: number, hour: number) => {
  if (props.disabled || defenseMode.value !== 'half' || !isDragging.value || !dragStart.value) return;
  
  dragEnd.value = { day, hour };
  
  // 计算拖拽范围内的所有单元格
  const startDay = Math.min(dragStart.value.day, dragEnd.value.day);
  const endDay = Math.max(dragStart.value.day, dragEnd.value.day);
  const startHour = Math.min(dragStart.value.hour, dragEnd.value.hour);
  const endHour = Math.max(dragStart.value.hour, dragEnd.value.hour);
  
  // 使用保存的目标值（在 mousedown 时切换后的值）
  const targetValue = dragStart.value.targetValue !== undefined ? dragStart.value.targetValue : 1;
  
  // 更新范围内的所有单元格
  for (let d = startDay; d <= endDay; d++) {
    for (let h = startHour; h <= endHour; h++) {
      schedule.value[d][h] = targetValue;
    }
  }
  
  emitValue();
};

// 鼠标释放
const handleMouseUp = (e: MouseEvent) => {
  // 只处理左键
  if (e.button !== 0) return;
  
  if (isDragging.value) {
    isDragging.value = false;
    dragStart.value = null;
    dragEnd.value = null;
  }
};

// 发出值变化事件
const emitValue = () => {
  emit('update:modelValue', {
    mode: defenseMode.value,
    schedule: JSON.parse(JSON.stringify(schedule.value)),
  });
};

// 监听全局鼠标释放事件
if (typeof window !== 'undefined') {
  window.addEventListener('mouseup', handleMouseUp);
}

// 组件卸载时清理事件监听器
onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('mouseup', handleMouseUp);
  }
});
</script>

<style lang="less" scoped>
.defense-schedule-picker {
  .mode-selector {
    margin-bottom: 16px;
  }
  
  .schedule-grid {
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    overflow: hidden;
    background: #fff;
    
    .grid-header {
      display: flex;
      background-color: #f5f5f5;
      border-bottom: 1px solid #e8e8e8;
      
      .time-label {
        width: 50px;
        padding: 6px 4px;
        text-align: center;
        font-weight: 500;
        font-size: 12px;
        border-right: 1px solid #e8e8e8;
        color: #666;
      }
      
      .day-header {
        flex: 1;
        padding: 6px 4px;
        text-align: center;
        font-weight: 500;
        font-size: 12px;
        border-right: 1px solid #e8e8e8;
        color: #666;
        
        &:last-child {
          border-right: none;
        }
      }
    }
    
    .grid-body {
      max-height: 300px;
      overflow-y: auto;
      
      .grid-row {
        display: flex;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .time-label {
          width: 50px;
          padding: 2px 4px;
          text-align: center;
          font-size: 11px;
          color: #999;
          border-right: 1px solid #f0f0f0;
          background-color: #fafafa;
          line-height: 16px;
        }
        
        .grid-cell {
          flex: 1;
          height: 16px;
          min-height: 16px;
          border-right: 1px solid #f0f0f0;
          cursor: pointer;
          transition: all 0.2s;
          user-select: none; // 防止文本选择
          -webkit-user-select: none;
          
          &:last-child {
            border-right: none;
          }
          
          &.active {
            background-color: #ffccc7;
            border-color: #ffccc7;
          }
          
          &:hover {
            background-color: #ffccc7;
            border-color: #ffccc7;
            opacity: 0.8;
          }
        }
      }
    }
  }
}
</style>

