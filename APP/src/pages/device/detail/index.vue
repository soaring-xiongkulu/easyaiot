<template>
  <view class="page-container">
    <wd-navbar :title="deviceName || '设备详情'" left-arrow placeholder safe-area-inset-top fixed @click-left="handleBack" />

    <scroll-view scroll-y class="detail-scroll">
      <!-- 设备总览 -->
      <view class="card overview-card">
        <view class="overview-badge">
          设备总览
        </view>
        <view class="overview-main">
          <view class="overview-avatar" :class="`overview-avatar--${status}`">
            <text>{{ avatarLetter }}</text>
          </view>
          <view class="overview-info">
            <view class="overview-name">
              {{ deviceName || deviceIdentification || '--' }}
            </view>
            <view class="overview-product">
              {{ productName || productIdentification || '未绑定产品' }}
            </view>
          </view>
          <view class="status-pill" :class="`status-pill--${status}`">
            <view class="status-pill-dot" />
            <text>{{ statusText }}</text>
          </view>
        </view>
        <view class="overview-rows">
          <view class="overview-row">
            <text class="row-label">设备 ID</text>
            <view class="row-value-row" @click="copyIdentification">
              <text class="row-value">{{ deviceIdentification || '--' }}</text>
              <wd-icon name="copy" size="24rpx" color="#98a2b3" />
            </view>
          </view>
          <view class="overview-divider" />
          <view class="overview-row">
            <text class="row-label">最后上线</text>
            <text class="row-value">{{ lastOnlineText }}</text>
          </view>
        </view>
      </view>

      <!-- 快捷操作 -->
      <view class="card">
        <view class="card-head">
          <view class="section-bar" />
          <text class="card-title">快捷操作</text>
        </view>
        <view class="action-grid">
          <view v-for="action in quickActions" :key="action.key" class="action-item" hover-class="action-item--pressed" :hover-stay-time="60" @click="action.run">
            <view class="action-icon" :style="{ background: `${action.color}14`, color: action.color }">
              <wd-icon :name="action.icon" size="44rpx" :color="action.color" />
            </view>
            <text class="action-label">{{ action.label }}</text>
          </view>
        </view>
      </view>

      <!-- 设备属性（影子 reported） -->
      <view class="card">
        <view class="card-head">
          <view class="section-bar" />
          <text class="card-title">设备属性</text>
          <view class="flex-1" />
          <wd-icon name="refresh" size="32rpx" color="#2f6bff" @click="refreshAll" />
        </view>

        <view v-if="propertiesLoading" class="state-tip">
          <wd-loading size="18px" color="#2f6bff" />
          <text>正在读取设备影子…</text>
        </view>
        <view v-else-if="!propertyItems.length" class="state-tip">
          <text>暂无属性上报数据</text>
        </view>
        <view v-else class="prop-grid">
          <view v-for="prop in propertyItems" :key="prop.code" class="prop-card">
            <text class="prop-label">{{ prop.label }}</text>
            <text class="prop-value">{{ prop.value }}</text>
            <text v-if="prop.unit" class="prop-unit">{{ prop.unit }}</text>
          </view>
        </view>
      </view>

      <!-- 基本信息 -->
      <view class="card">
        <view class="card-head">
          <view class="section-bar" />
          <text class="card-title">基本信息</text>
        </view>
        <view class="info-list">
          <view v-for="row in infoRows" :key="row.label" class="info-row">
            <text class="row-label">{{ row.label }}</text>
            <text class="info-value">{{ row.value }}</text>
          </view>
        </view>
      </view>

      <view class="h-40rpx" />
    </scroll-view>
  </view>
</template>

<script lang="ts" setup>
import type { IotDeviceItem, ThingPropertyMeta } from '@/api/device/panel'
import { onLoad } from '@dcloudio/uni-app'
import {
  getDeviceByIdentification,
  getDeviceShadow,
  getPropertyMetaMap,
  normalizeConnectStatus,
} from '@/api/device/panel'
import { formatDateTime } from '@/utils/date'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const deviceId = ref<number | string>('')
const deviceIdentification = ref('')
const productIdentification = ref('')
const deviceName = ref('')
const productName = ref('')
const device = ref<IotDeviceItem | null>(null)
const propertyMeta = ref<Map<string, ThingPropertyMeta>>(new Map())
const reported = ref<Record<string, any>>({})
const propertiesLoading = ref(false)

const status = computed(() => normalizeConnectStatus(device.value?.connectStatus))
const statusText = computed(() => ({ online: '在线', offline: '离线', inactive: '未激活' })[status.value])
const avatarLetter = computed(() => (deviceName.value || deviceIdentification.value || '设').slice(0, 1).toUpperCase())
const lastOnlineText = computed(() => {
  const t = device.value?.lastOnlineTime
  return t ? formatDateTime(t) : '暂无上报'
})

const quickActions = computed(() => [
  {
    key: 'console',
    label: '控制台',
    icon: 'apps',
    color: '#2f6bff',
    run: openConsole,
  },
  {
    key: 'ota',
    label: 'OTA升级',
    icon: 'download',
    color: '#f59e0b',
    run: openOta,
  },
  {
    key: 'copy',
    label: '复制标识',
    icon: 'copy',
    color: '#12b77c',
    run: copyIdentification,
  },
  {
    key: 'refresh',
    label: '刷新',
    icon: 'refresh',
    color: '#8b5cf6',
    run: refreshAll,
  },
])

const infoRows = computed(() => {
  const d = device.value
  return [
    { label: '产品标识', value: d?.productIdentification || productIdentification.value || '-' },
    { label: '设备SN', value: d?.deviceSn || '-' },
    { label: 'IP 地址', value: d?.ipAddress || '-' },
    { label: '当前版本', value: d?.deviceVersion || '未知' },
    { label: '父网关', value: d?.parentIdentification || '独立设备' },
    { label: '激活状态', value: Number(d?.activeStatus) === 1 ? '已激活' : '未激活' },
  ]
})

/** 影子 reported → 属性卡片（中文标签优先，附单位） */
const propertyItems = computed(() => {
  return Object.entries(reported.value)
    .filter(([key]) => key !== '__system__' && key !== '_raw')
    .map(([code, raw]) => {
      const meta = propertyMeta.value.get(code)
      return {
        code,
        label: meta?.propertyName || code,
        value: formatPropValue(raw),
        unit: meta?.unit || '',
      }
    })
    .slice(0, 30)
})

function formatPropValue(raw: any): string {
  if (raw == null)
    return '-'
  if (typeof raw === 'boolean')
    return raw ? '开' : '关'
  if (typeof raw === 'number')
    return String(Math.round(raw * 1000) / 1000)
  const text = String(raw)
  if (text === 'true')
    return '开'
  if (text === 'false')
    return '关'
  try {
    if (typeof raw === 'object') {
      const json = JSON.stringify(raw)
      return json.length > 40 ? `${json.slice(0, 40)}…` : json
    }
  } catch {
    // 保持字符串展示
  }
  return text.length > 40 ? `${text.slice(0, 40)}…` : text
}

onLoad((query) => {
  deviceId.value = query?.id ?? ''
  deviceIdentification.value = decodeURIComponent(query?.deviceIdentification ?? '')
  productIdentification.value = decodeURIComponent(query?.productIdentification ?? '')
  deviceName.value = decodeURIComponent(query?.name ?? '')
  refreshAll()
})

async function refreshAll() {
  loadProperties()
  loadDevice()
}

async function loadDevice() {
  const detail = await getDeviceByIdentification(productIdentification.value, deviceIdentification.value)
  if (detail) {
    device.value = detail
    if (detail.deviceName) {
      deviceName.value = detail.deviceName
    }
    if (detail.productIdentification) {
      productIdentification.value = detail.productIdentification
    }
  }
}

async function loadProperties() {
  if (!deviceId.value) {
    return
  }
  propertiesLoading.value = true
  try {
    const [shadow, meta] = await Promise.all([
      getDeviceShadow(deviceId.value),
      productIdentification.value && !propertyMeta.value.size
        ? getPropertyMetaMap(productIdentification.value)
        : Promise.resolve(propertyMeta.value),
    ])
    reported.value = shadow.reported || {}
    if (meta.size) {
      propertyMeta.value = meta
    }
  } finally {
    propertiesLoading.value = false
  }
}

function openConsole() {
  if (!productIdentification.value) {
    uni.showToast({ icon: 'none', title: '该设备未绑定产品' })
    return
  }
  const query = [
    `id=${encodeURIComponent(String(deviceId.value ?? ''))}`,
    `deviceIdentification=${encodeURIComponent(deviceIdentification.value)}`,
    `productIdentification=${encodeURIComponent(productIdentification.value)}`,
    `name=${encodeURIComponent(deviceName.value || '')}`,
  ].join('&')
  uni.navigateTo({ url: `/pages/device/control/index?${query}` })
}

function openOta() {
  const query = [
    `deviceIdentification=${encodeURIComponent(deviceIdentification.value)}`,
    `productIdentification=${encodeURIComponent(productIdentification.value)}`,
    `name=${encodeURIComponent(deviceName.value || '')}`,
    `version=${encodeURIComponent(device.value?.deviceVersion || '')}`,
  ].join('&')
  uni.navigateTo({ url: `/pages/device/ota/index?${query}` })
}

function copyIdentification() {
  if (!deviceIdentification.value) {
    return
  }
  uni.setClipboardData({
    data: deviceIdentification.value,
    success: () => uni.showToast({ icon: 'none', title: '设备标识已复制' }),
  })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
}

.detail-scroll {
  flex: 1;
  height: 0;
  padding: 16rpx 24rpx 0;
  box-sizing: border-box;
}

.card {
  margin-bottom: 22rpx;
  padding: 28rpx;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
}

.card-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 22rpx;
}

.section-bar {
  width: 8rpx;
  height: 30rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #4a8bff, #2f6bff);
}

.card-title {
  font-size: 29rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

// ==================== 总览 ====================
.overview-card {
  padding: 26rpx 28rpx 0;
}

.overview-badge {
  display: inline-flex;
  padding: 6rpx 20rpx;
  border-radius: 999rpx;
  background: #eaf1ff;
  color: #2f6bff;
  font-size: 22rpx;
  font-weight: 600;
}

.overview-main {
  display: flex;
  align-items: center;
  gap: 22rpx;
  margin-top: 22rpx;
}

.overview-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 108rpx;
  height: 108rpx;
  border-radius: 30rpx;
  color: #ffffff;
  font-size: 46rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #b8c2d4, #8b96ab);
  flex-shrink: 0;

  &--online {
    background: linear-gradient(135deg, #5d9bff 0%, #2f6bff 60%, #1f56d6 100%);
    box-shadow: 0 10rpx 22rpx rgba(47, 107, 255, 0.32);
  }

  &--offline {
    background: linear-gradient(135deg, #b9c2d0, #97a1b3);
  }

  &--inactive {
    background: linear-gradient(135deg, #d8c49a, #bda06a);
  }
}

.overview-info {
  flex: 1;
  min-width: 0;
}

.overview-name {
  font-size: 34rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-product {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: var(--app-text-3, #98a2b3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 10rpx;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 600;
  background: #eef0f4;
  color: #8a94a6;
  flex-shrink: 0;

  &--online {
    background: #e6f7f1;
    color: #0fa36e;
  }

  &--offline {
    background: #f4f6fb;
    color: #8a94a6;
  }

  &--inactive {
    background: #fdf3e2;
    color: #c98a2b;
  }

  .status-pill-dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    background: currentColor;
  }
}

.overview-rows {
  display: flex;
  margin-top: 26rpx;
  padding: 22rpx 0;
  border-top: 1rpx solid var(--app-separator, rgba(23, 43, 77, 0.06));
}

.overview-row {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  min-width: 0;
}

.overview-divider {
  width: 1rpx;
  margin: 0 26rpx;
  background: var(--app-separator, rgba(23, 43, 77, 0.06));
}

.row-label {
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);
}

.row-value {
  font-size: 25rpx;
  font-weight: 600;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-value-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

// ==================== 快捷操作 ====================
.action-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14rpx;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14rpx;
  padding: 20rpx 0;
  border-radius: 20rpx;
  border: 1rpx solid #eef2fa;
  background: #fbfcff;
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.95);
    opacity: 0.9;
  }
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  box-shadow: 0 8rpx 18rpx rgba(23, 43, 77, 0.06);
}

.action-label {
  font-size: 23rpx;
  color: var(--app-text-2, #3d4558);
}

// ==================== 属性网格 ====================
.prop-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.prop-card {
  padding: 20rpx 22rpx;
  border-radius: 18rpx;
  background: #f7f9fd;
  border: 1rpx solid #eef2fa;
  min-width: 0;
}

.prop-label {
  display: block;
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prop-value {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  word-break: break-all;
}

.prop-unit {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #b3bccb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.state-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  padding: 40rpx 0;
  font-size: 25rpx;
  color: var(--app-text-3, #98a2b3);
}

// ==================== 基本信息 ====================
.info-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid var(--app-separator, rgba(23, 43, 77, 0.06));

  &:last-child {
    border-bottom: none;
  }

  .row-label {
    flex-shrink: 0;
  }
}

.info-value {
  font-size: 25rpx;
  color: var(--app-text-2, #3d4558);
  text-align: right;
  word-break: break-all;
}
</style>
