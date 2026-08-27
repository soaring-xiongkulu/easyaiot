<template>
  <view class="chart-widget">
    <view class="chart-head">
      <text class="chart-title">{{ title }}</text>
      <view class="chart-current">
        <text class="chart-value">{{ currentText }}</text>
        <text v-if="unit" class="chart-unit">{{ unit }}</text>
      </view>
    </view>
    <canvas
      v-if="ready"
      :id="canvasId"
      :canvas-id="canvasId"
      class="chart-canvas"
      :style="{ height: heightPx + 'px' }"
    />
    <view v-else class="chart-empty">
      <text>等待数据…</text>
    </view>
  </view>
</template>

<script lang="ts" setup>
import { computed, getCurrentInstance, nextTick, ref, watch } from 'vue'

const props = defineProps<{
  widgetId?: string
  title: string
  /** 当前采样值 */
  value?: string | number | null
  unit?: string
  color?: string
  maxPoints?: number
  min?: number
  max?: number
}>()

const MAX_POINTS = Math.max(5, props.maxPoints || 20)
const CANVAS_W = 300
const CANVAS_H = 110
const heightPx = CANVAS_H

const series = ref<number[]>([])
const ready = ref(false)
const canvasId = `panel-chart-${Math.random().toString(36).slice(2, 8)}`

const lineColor = props.color || '#2f6bff'
const currentText = computed(() => {
  if (props.value === undefined || props.value === null || props.value === '')
    return '--'
  return String(props.value)
})

watch(
  () => props.value,
  (v) => {
    const n = Number(v)
    if (Number.isNaN(n)) return
    series.value = [...series.value, n].slice(-MAX_POINTS)
    if (!ready.value) {
      ready.value = true
      nextTick(draw)
      return
    }
    draw()
  },
  { immediate: true },
)

function draw() {
  const ctx = uni.createCanvasContext(canvasId, getCurrentInstance()?.proxy)
  const data = series.value
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)

  if (data.length < 2) {
    ctx.draw()
    return
  }

  // 网格线
  ctx.setStrokeStyle('#eef1f6')
  ctx.setLineWidth(1)
  for (let i = 0; i <= 3; i++) {
    const y = 10 + (i * (CANVAS_H - 20)) / 3
    ctx.beginPath()
    ctx.moveTo(8, y)
    ctx.lineTo(CANVAS_W - 8, y)
    ctx.stroke()
  }

  const values = [...data]
  const vmin = props.min !== undefined ? props.min : Math.min(...values)
  const vmax = props.max !== undefined ? props.max : Math.max(...values)
  const range = vmax - vmin || 1

  const px = (i: number) => 8 + (i * (CANVAS_W - 16)) / (MAX_POINTS - 1)
  const py = (v: number) => CANVAS_H - 10 - ((v - vmin) * (CANVAS_H - 20)) / range

  // 面积渐变
  const grad = ctx.createLinearGradient(0, 0, 0, CANVAS_H)
  grad.addColorStop(0, lineColor + '33')
  grad.addColorStop(1, lineColor + '00')
  ctx.beginPath()
  values.forEach((v, i) => (i === 0 ? ctx.moveTo(px(i), py(v)) : ctx.lineTo(px(i), py(v))))
  ctx.lineTo(px(values.length - 1), CANVAS_H - 10)
  ctx.lineTo(px(0), CANVAS_H - 10)
  ctx.closePath()
  ctx.setFillStyle(grad)
  ctx.fill()

  // 折线
  ctx.beginPath()
  values.forEach((v, i) => (i === 0 ? ctx.moveTo(px(i), py(v)) : ctx.lineTo(px(i), py(v))))
  ctx.setStrokeStyle(lineColor)
  ctx.setLineWidth(2)
  ctx.setLineCap('round')
  ctx.setLineJoin('round')
  ctx.stroke()

  // 末端圆点
  const last = values[values.length - 1]
  ctx.beginPath()
  ctx.arc(px(values.length - 1), py(last), 3.5, 0, Math.PI * 2)
  ctx.setFillStyle(lineColor)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(px(values.length - 1), py(last), 1.8, 0, Math.PI * 2)
  ctx.setFillStyle('#ffffff')
  ctx.fill()

  ctx.draw()
}
</script>

<style lang="scss" scoped>
.chart-widget {
  width: 100%;
}

.chart-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.chart-title {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--app-text-3, #98a2b3);
}

.chart-current {
  display: flex;
  align-items: baseline;
  gap: 4rpx;

  .chart-value {
    font-size: 30rpx;
    font-weight: 700;
    color: var(--app-text-1, #10131a);
    font-variant-numeric: tabular-nums;
  }

  .chart-unit {
    font-size: 20rpx;
    color: var(--app-text-3, #98a2b3);
  }
}

.chart-canvas {
  width: 100%;
}

.chart-empty {
  height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
  background: var(--app-fill, #f2f3f7);
  font-size: 22rpx;
  color: var(--app-text-3, #98a2b3);
}
</style>
