<template>
  <view class="gauge-widget">
    <view class="gauge-head">
      <text class="gauge-title">{{ title }}</text>
      <text class="gauge-value">{{ displayValue }}<text v-if="unit" class="gauge-unit">{{ unit }}</text></text>
    </view>
    <canvas
      v-if="ready"
      :id="canvasId"
      :canvas-id="canvasId"
      class="gauge-canvas"
      :style="{ height: heightPx + 'px' }"
    />
    <view v-else class="gauge-empty" :style="{ height: heightPx + 'px' }" />
  </view>
</template>

<script lang="ts" setup>
import { computed, getCurrentInstance, nextTick, ref, watch } from 'vue'

const props = defineProps<{
  widgetId?: string
  title: string
  value?: string | number | null
  unit?: string
  color?: string
  min?: number
  max?: number
}>()

const CANVAS_W = 300
const CANVAS_H = 108

const ready = ref(false)
const canvasId = `panel-gauge-${Math.random().toString(36).slice(2, 8)}`

const minV = Number.isNaN(Number(props.min)) ? 0 : Number(props.min)
const maxV = Number.isNaN(Number(props.max)) ? 100 : Number(props.max)
const lineColor = props.color || '#2f6bff'
const heightPx = '110px'

const displayValue = computed(() => {
  if (props.value === undefined || props.value === null || props.value === '')
    return '--'
  return String(props.value)
})

const ratio = computed(() => {
  const n = Number(props.value)
  if (Number.isNaN(n)) return 0
  const r = (n - minV) / (maxV - minV || 1)
  return Math.min(1, Math.max(0, r))
})

watch(ratio, () => {
  if (!ready.value) {
    ready.value = true
    nextTick(draw)
    return
  }
  draw()
}, { immediate: true })

function draw() {
  const ctx = uni.createCanvasContext(canvasId, getCurrentInstance()?.proxy)
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H)

  const cx = CANVAS_W / 2
  const cy = CANVAS_H - 8
  const r = 86
  const start = Math.PI
  const end = Math.PI * 2
  const angle = start + (end - start) * ratio.value

  // 底弧
  ctx.beginPath()
  ctx.arc(cx, cy, r, start, end)
  ctx.setStrokeStyle('#eef1f6')
  ctx.setLineWidth(12)
  ctx.setLineCap('round')
  ctx.stroke()

  // 进度弧
  if (ratio.value > 0.01) {
    const grad = ctx.createLinearGradient(cx - r, cy, cx + r, cy)
    grad.addColorStop(0, lineColor)
    grad.addColorStop(1, lineColor + 'aa')
    ctx.beginPath()
    ctx.arc(cx, cy, r, start, angle)
    ctx.setStrokeStyle(grad as unknown as string)
    ctx.setLineWidth(12)
    ctx.setLineCap('round')
    ctx.stroke()
  }

  // 端点圆
  if (ratio.value > 0.01) {
    const ex = cx + Math.cos(angle) * r
    const ey = cy + Math.sin(angle) * r
    ctx.beginPath()
    ctx.arc(ex, ey, 6, 0, Math.PI * 2)
    ctx.setFillStyle('#ffffff')
    ctx.fill()
    ctx.beginPath()
    ctx.arc(ex, ey, 3.2, 0, Math.PI * 2)
    ctx.setFillStyle(lineColor)
    ctx.fill()
  }

  // 刻度文字
  ctx.setFontSize(9)
  ctx.setFillStyle('#98a2b3')
  ctx.setTextAlign('center')
  ctx.fillText(String(minV), cx - r + 6, cy + 12)
  ctx.fillText(String(maxV), cx + r - 6, cy + 12)

  ctx.draw()
}
</script>

<style lang="scss" scoped>
.gauge-widget {
  width: 100%;
}

.gauge-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 4rpx;
}

.gauge-title {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--app-text-3, #98a2b3);
}

.gauge-value {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  font-variant-numeric: tabular-nums;

  .gauge-unit {
    font-size: 20rpx;
    font-weight: 400;
    color: var(--app-text-3, #98a2b3);
    margin-left: 4rpx;
  }
}

.gauge-canvas {
  width: 100%;
}

.gauge-empty {
  width: 100%;
  background: var(--app-fill, #f2f3f7);
  border-radius: 12rpx;
}
</style>
