<template>
  <view class="panel-root">
    <template v-for="(page, pi) in pages" :key="pi">
      <view v-if="pages.length > 1" class="panel-section-title">
        {{ page.name }}
      </view>
      <view class="panel-grid">
        <template v-for="w in page.widgets" :key="w.id || w.title">
          <!-- 视频组件不参与属性绑定 -->
          <view v-if="w.type === 'video'" class="panel-card panel-video-card">
            <PanelVideo
              :widget="w"
              :iot-device-id="deviceId"
              :card-title="w.title"
            />
          </view>

          <view v-else class="panel-card" :class="{ 'is-half': w.span === 'half' }">
            <view class="panel-card-head">
              <text class="panel-card-title">{{ w.title }}</text>
              <wd-loading v-if="pendingId === widgetKey(w)" :size="18" color="#9aa7bd" />
            </view>

            <!-- 开关 -->
            <view v-if="w.type === 'switch'" class="panel-card-body between">
              <text class="panel-state-text" :class="{ on: isOn(w) }">
                {{ isOn(w) ? onLabel(w) : offLabel(w) }}
              </text>
              <wd-switch
                :model-value="isOn(w)"
                size="28px"
                :disabled="disabled || loading"
                active-color="var(--app-brand, #2f6bff)"
                @update:model-value="onSwitchChange(w, $event)"
              />
            </view>

            <!-- 滑条 -->
            <template v-else-if="w.type === 'slider'">
              <view class="panel-value-row">
                <text class="panel-value">{{ displayValue(w) }}</text>
                <text class="panel-unit">{{ w.config?.unit || '' }}</text>
              </view>
              <wd-slider
                :model-value="numberValue(w)"
                :min="numMin(w)"
                :max="numMax(w)"
                :step="numStep(w)"
                hide-label
                :disabled="disabled || loading"
                active-color="var(--app-brand, #2f6bff)"
                @update:model-value="(v: any) => sliderPreview[widgetKey(w)] = +v"
                @change="(v: any) => commitNumber(w, +(v?.value ?? v))"
              />
            </template>

            <!-- 步进器 -->
            <template v-else-if="w.type === 'number'">
              <wd-input-number
                :model-value="numberValue(w)"
                :min="numMin(w)"
                :max="numMax(w)"
                :step="numStep(w)"
                :disabled="loading"
                allow-null
                @change="(e) => commitNumber(w, Number(e.value))"
              />
            </template>

            <!-- 状态标签 -->
            <view v-else-if="w.type === 'status'" class="panel-card-body">
              <view class="status-pill" :style="{ background: statusOption(w)?.color || '#e8f0fe', color: statusOption(w)?.color ? '#fff' : 'var(--app-brand,#2f6bff)' }">
                {{ statusOption(w)?.label ?? displayValue(w) }}
              </view>
            </view>

            <!-- 数值文本 -->
            <template v-else-if="w.type === 'text'">
              <view class="panel-value-row">
                <text class="panel-value big">{{ displayValue(w) }}</text>
                <text class="panel-unit">{{ w.config?.unit || '' }}</text>
              </view>
            </template>

            <!-- 命令按钮 -->
            <view v-else-if="w.type === 'button'" class="panel-card-body center">
              <wd-button
                block
                round
                type="primary"
                :loading="pendingId === widgetKey(w)"
                :disabled="disabled"
                @click="onButtonClick(w)"
              >
                {{ w.title }}
              </wd-button>
            </view>

            <!-- 折线图（实时采样曲线） -->
            <view v-else-if="w.type === 'chart'" class="panel-card-body">
              <PanelChart
                :widget-id="widgetKey(w)"
                :title="w.title"
                :value="currentValue(w)"
                :unit="w.config?.unit"
                :color="w.config?.color"
                :max-points="w.config?.maxPoints"
                :min="numMin(w)"
                :max="numMax(w)"
              />
            </view>

            <!-- 仪表盘 -->
            <view v-else-if="w.type === 'gauge'" class="panel-card-body">
              <PanelGauge
                :widget-id="widgetKey(w)"
                :title="w.title"
                :value="currentValue(w)"
                :unit="w.config?.unit"
                :color="w.config?.color"
                :min="numMin(w)"
                :max="numMax(w)"
              />
            </view>

            <!-- 进度条 -->
            <view v-else-if="w.type === 'progress'" class="panel-card-body">
              <PanelProgress
                :widget-id="widgetKey(w)"
                :title="w.title"
                :value="currentValue(w)"
                :unit="w.config?.unit"
                :color="w.config?.color"
                :min="numMin(w)"
                :max="numMax(w)"
              />
            </view>
          </view>
        </template>
      </view>
    </template>
  </view>
</template>

<script lang="ts" setup>
import type { PanelTemplatePage, PanelWidget } from '@/api/device/panel'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import PanelVideo from './widgets/panel-video.vue'
import PanelChart from './widgets/panel-chart.vue'
import PanelGauge from './widgets/panel-gauge.vue'
import PanelProgress from './widgets/panel-progress.vue'
import {
  getDeviceShadow,
  issueDeviceCommand,
} from '@/api/device/panel'

const props = defineProps<{
  pages: PanelTemplatePage[]
  /** IoT 设备 id / 设备标识 / 产品标识 */
  deviceId: number | string
  deviceIdentification: string
  productIdentification: string
}>()

const ON_WORDS = new Set(['1', 'true', 'open', 'on', '开', '开启'])
const OFF_WORDS = new Set(['0', 'false', 'close', 'off', '关', '关闭'])

const values = ref<Record<string, any>>({})
const connectStatus = ref<string>('')
const online = ref(true)
const disabled = computed(() => !online.value)
const loading = ref(false)
const pendingId = ref('')
const sliderPreview = reactive<Record<string, number>>({})

const toast = (title: string) => uni.showToast({ icon: 'none', title })

function widgetKey(w: PanelWidget) {
  return w.id || `${w.type}_${w.propertyCode || ''}`
}

/** 只读组件取当前 shadow 值 */
function currentValue(w: PanelWidget) {
  const raw = values.value[w.propertyCode!]
  return raw === undefined || raw === null || raw === '' ? null : raw
}

let timer: ReturnType<typeof setInterval> | null = null

async function loadShadow(silent = false) {
  if (!silent)
    loading.value = true
  try {
    const res = await getDeviceShadow(props.deviceId)
    values.value = { ...values.value, ...res.reported }
    if (res.connectStatus)
      connectStatus.value = res.connectStatus
    online.value = (connectStatus.value || '').toUpperCase() !== 'OFFLINE'
  }
  finally {
    if (!silent)
      loading.value = false
  }
}

onMounted(() => {
  loadShadow()
  timer = setInterval(() => loadShadow(true), 10_000)
})
onUnmounted(() => {
  if (timer)
    clearInterval(timer)
})

defineExpose({ refresh: () => loadShadow() })

/** 解析开关的开/关取值：优先用模板枚举配置，否则回退到常见布尔词表 */
function resolveOnOffValues(w: PanelWidget): { onVal: any, offVal: any } {
  const opts = w.config?.options || []
  const findWord = (words: Set<string>) =>
    opts.find(o => words.has(String(o.label).toLowerCase()) || words.has(String(o.value).toLowerCase()))
  const onOpt = findWord(ON_WORDS)
  const offOpt = findWord(OFF_WORDS)
  if (onOpt && offOpt)
    return { onVal: onOpt.value, offVal: offOpt.value }
  if (opts.length >= 2)
    return { onVal: opts[0].value, offVal: opts[1].value }
  const cur = String(values.value[w.propertyCode!] ?? '').toLowerCase()
  if (cur === '1' || cur === 'true')
    return { onVal: '1', offVal: '0' }
  return { onVal: '1', offVal: '0' }
}

function isOn(w: PanelWidget) {
  const raw = values.value[w.propertyCode!]
  if (raw === undefined || raw === null || raw === '')
    return false
  const normalized = String(raw).toLowerCase()
  if (ON_WORDS.has(normalized) || raw === 1 || raw === true)
    return true
  if (OFF_WORDS.has(normalized) || raw === 0 || raw === false)
    return false
  // 数值型：大于最小值视为开启（如温度档位）
  const numeric = Number(raw)
  if (!Number.isNaN(numeric)) {
    const min = numMin({ ...w, config: w.config } as PanelWidget)
    return numeric > min
  }
  return false
}

function findOptionByValue(opts: { label: string, value: any }[], val: any) {
  return opts.find(o => String(o.value) === String(val))
}

function onLabel(w: PanelWidget): string {
  const opts = w.config?.options || []
  const on = findOptionByValue(opts, resolveOnOffValues(w).onVal)
  return on?.label || '已开启'
}

function offLabel(w: PanelWidget): string {
  const opts = w.config?.options || []
  const off = findOptionByValue(opts, resolveOnOffValues(w).offVal)
  return off?.label || '已关闭'
}

async function writeProperty(w: PanelWidget, value: any) {
  const key = widgetKey(w)
  if (!props.deviceIdentification || !props.productIdentification) {
    toast('设备信息缺失，无法下发')
    return
  }
  const prev = values.value[w.propertyCode!]
  values.value = { ...values.value, [w.propertyCode!]: value }
  pendingId.value = key
  try {
    await issueDeviceCommand({
      deviceIdentification: props.deviceIdentification,
      productIdentification: props.productIdentification,
      serviceCode: w.serviceId || 'setProperty',
      params: { [w.propertyCode as string]: value },
    })
    toast('指令已下发')
  }
  catch (e: any) {
    values.value = { ...values.value, [w.propertyCode!]: prev }
    toast(e?.msg || e?.message || '下发失败，请稍后重试')
  }
  finally {
    pendingId.value = ''
  }
}

function onSwitchChange(w: PanelWidget, checked: boolean) {
  const { onVal, offVal } = resolveOnOffValues(w)
  writeProperty(w, checked ? onVal : offVal)
}

function numberValue(w: PanelWidget) {
  const preview = sliderPreview[widgetKey(w)]
  if (preview !== undefined)
    return preview
  const raw = values.value[w.propertyCode!]
  const n = Number(raw)
  return Number.isNaN(n) ? numMin(w) : n
}

function displayValue(w: PanelWidget) {
  if (sliderPreview[widgetKey(w)] !== undefined && w.type === 'slider')
    return sliderPreview[widgetKey(w)]
  const raw = values.value[w.propertyCode!]
  if (raw === undefined || raw === null || raw === '')
    return '--'
  return String(raw)
}

function numMin(w: PanelWidget) {
  const v = Number(w.config?.min)
  return Number.isNaN(v) ? 0 : v
}
function numMax(w: PanelWidget) {
  const v = Number(w.config?.max)
  return Number.isNaN(v) ? 100 : v
}
function numStep(w: PanelWidget) {
  const v = Number(w.config?.step)
  return Number.isNaN(v) || v <= 0 ? 1 : v
}

let commitDebounce: ReturnType<typeof setTimeout> | null = null
function commitNumber(w: PanelWidget, value: number) {
  if (Number.isNaN(value))
    return
  delete sliderPreview[widgetKey(w)]
  if (commitDebounce)
    clearTimeout(commitDebounce)
  commitDebounce = setTimeout(() => writeProperty(w, value), 150)
}

function statusOption(w: PanelWidget): { label: string, value?: any, color?: string } | undefined {
  const raw = values.value[w.propertyCode!]
  if (raw === undefined || raw === null || raw === '')
    return undefined
  const opt = findOptionByValue(w.config?.options || [], raw)
  if (opt)
    return opt
  return { label: String(raw), value: raw }
}

function onButtonClick(w: PanelWidget) {
  const doIssue = async () => {
    if (!props.deviceIdentification || !props.productIdentification) {
      toast('设备信息缺失，无法下发')
      return
    }
    if (!w.serviceId) {
      toast('该按钮未配置服务标识')
      return
    }
    pendingId.value = widgetKey(w)
    try {
      await issueDeviceCommand({
        deviceIdentification: props.deviceIdentification,
        productIdentification: props.productIdentification,
        serviceCode: w.serviceId,
        params: {},
      })
      toast('指令已下发')
    }
    catch (e: any) {
      toast(e?.msg || e?.message || '下发失败，请稍后重试')
    }
    finally {
      pendingId.value = ''
    }
  }

  if (w.config?.confirm) {
    uni.showModal({
      title: '操作确认',
      content: `确认执行「${w.title}」？`,
      success: (res) => {
        if (res.confirm)
          doIssue()
      },
    })
    return
  }
  doIssue()
}
</script>

<style lang="scss" scoped>
.panel-root {
  padding-bottom: env(safe-area-inset-bottom);
}

// iOS 分组标题
.panel-section-title {
  padding: 34rpx 8rpx 14rpx;
  font-size: 26rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
  color: var(--app-text-3, #98a2b3);
  text-transform: uppercase;
}

.panel-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.panel-card {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  background: var(--app-card-bg, #ffffff);
  border-radius: var(--app-card-radius, 28rpx);
  padding: 30rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));

  &.is-half {
    width: calc((100% - 20rpx) / 2);
  }
}

.panel-video-card {
  padding: 20rpx;
}

.panel-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.panel-card-title {
  font-size: 24rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
  color: var(--app-text-3, #98a2b3);
}

.panel-card-body {
  &.between {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  &.center {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.panel-state-text {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--app-text-3, #98a2b3);

  &.on {
    color: var(--app-brand, #2f6bff);
  }
}

.panel-value-row {
  display: flex;
  align-items: baseline;
  gap: 6rpx;
  margin-bottom: 12rpx;
}

.panel-value {
  font-size: 46rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  font-variant-numeric: tabular-nums;

  &.big {
    font-size: 54rpx;
  }
}

.panel-unit {
  font-size: 24rpx;
  color: var(--app-text-3, #98a2b3);
}

.status-pill {
  display: inline-block;
  border-radius: 999rpx;
  padding: 12rpx 28rpx;
  font-size: 26rpx;
  font-weight: 600;
  box-shadow: 0 4rpx 12rpx rgba(23, 43, 77, 0.08);
}
</style>
