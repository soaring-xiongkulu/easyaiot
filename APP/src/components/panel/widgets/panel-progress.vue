<template>
  <view class="progress-widget">
    <view class="progress-head">
      <text class="progress-title">{{ title }}</text>
      <text class="progress-value">{{ displayValue }}<text v-if="unit" class="progress-unit">{{ unit }}</text></text>
    </view>
    <view class="progress-track">
      <view
        class="progress-fill"
        :style="{
          width: pct + '%',
          background: `linear-gradient(90deg, ${color}66, ${color})`,
        }"
      />
    </view>
    <view class="progress-scale">
      <text>{{ minV }}</text>
      <text>{{ maxV }}</text>
    </view>
  </view>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props = defineProps<{
  widgetId?: string
  title: string
  value?: string | number | null
  unit?: string
  color?: string
  min?: number
  max?: number
}>()

const minV = Number.isNaN(Number(props.min)) ? 0 : Number(props.min)
const maxV = Number.isNaN(Number(props.max)) ? 100 : Number(props.max)
const color = props.color || '#2f6bff'

const displayValue = computed(() => {
  if (props.value === undefined || props.value === null || props.value === '')
    return '--'
  return String(props.value)
})

const pct = computed(() => {
  const n = Number(props.value)
  if (Number.isNaN(n)) return 0
  const r = ((n - minV) / (maxV - minV || 1)) * 100
  return Math.min(100, Math.max(0, Math.round(r)))
})
</script>

<style lang="scss" scoped>
.progress-widget {
  width: 100%;
}

.progress-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.progress-title {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--app-text-3, #98a2b3);
}

.progress-value {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  font-variant-numeric: tabular-nums;

  .progress-unit {
    font-size: 20rpx;
    font-weight: 400;
    color: var(--app-text-3, #98a2b3);
    margin-left: 4rpx;
  }
}

.progress-track {
  height: 16rpx;
  border-radius: 99rpx;
  background: var(--app-fill, #eef0f4);
  overflow: hidden;

  .progress-fill {
    height: 100%;
    border-radius: 99rpx;
    transition: width 0.4s ease;
  }
}

.progress-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 8rpx;
  font-size: 18rpx;
  color: var(--app-text-3, #98a2b3);
}
</style>
