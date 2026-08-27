<template>
  <view class="page-container">
    <wd-navbar
      title="设备控制台"
      left-arrow
      placeholder
      safe-area-inset-top
      fixed
      @click-left="handleBack"
    />

    <z-paging
      ref="pagingRef"
      v-model="deviceList"
      :fixed="false"
      height="100%"
      @query="queryList"
    >
      <template #top>
        <view class="console-tip">
          <view class="tip-icon">
            <wd-icon name="info" size="28rpx" color="#2f6bff" />
          </view>
          <text>选择设备，按其产品的面板模板进入定制控制页</text>
        </view>
      </template>

      <view
        v-for="(item, index) in deviceList"
        :key="item.id"
        class="device-card"
        hover-class="device-card--pressed"
        :hover-stay-time="60"
        @click="handleOpenControl(item)"
      >
        <view class="device-avatar" :class="{ online: isOnline(item) }">
          <text>{{ (item.deviceName || '设').slice(0, 1) }}</text>
        </view>
        <view class="device-info">
          <view class="device-name-row">
            <text class="device-name">{{ item.deviceName || item.deviceIdentification }}</text>
          </view>
          <view class="device-meta">
            <text class="meta-product">{{ item.productName || item.productIdentification || '未绑定产品' }}</text>
            <text v-if="item.deviceIdentification" class="device-id">
              {{ item.deviceIdentification }}
            </text>
          </view>
        </view>
        <view class="device-side">
          <view class="status-badge" :class="{ online: isOnline(item) }">
            <view class="status-dot" :class="{ online: isOnline(item) }" />
            <text>{{ isOnline(item) ? '在线' : '离线' }}</text>
          </view>
          <wd-icon name="arrow-right" color="#c8cfda" size="30rpx" />
        </view>
      </view>
      <view class="console-footer-space" />
    </z-paging>
  </view>
</template>

<script lang="ts" setup>
import type { IotDeviceItem } from '@/api/device/panel'
import { ref } from 'vue'
import { getIotDevicePage } from '@/api/device/panel'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const pagingRef = ref()
const deviceList = ref<IotDeviceItem[]>([])

function handleBack() {
  uni.navigateBack({ delta: 1 })
}

function isOnline(item: IotDeviceItem) {
  return (item.connectStatus || '').toUpperCase() === 'ONLINE'
}

async function queryList(pageNo: number, pageSize: number) {
  try {
    const res = await getIotDevicePage({ pageNum: pageNo, pageSize })
    pagingRef.value?.completeByTotal(res.list, res.total)
  }
  catch {
    pagingRef.value?.complete(false)
  }
}

function handleOpenControl(item: IotDeviceItem) {
  if (!item.productIdentification) {
    uni.showToast({ icon: 'none', title: '该设备未绑定产品' })
    return
  }
  const query = [
    `id=${encodeURIComponent(String(item.id ?? ''))}`,
    `deviceIdentification=${encodeURIComponent(item.deviceIdentification || '')}`,
    `productIdentification=${encodeURIComponent(item.productIdentification)}`,
    `name=${encodeURIComponent(item.deviceName || '')}`,
  ].join('&')
  uni.navigateTo({ url: `/pages/device/control/index?${query}` })
}
</script>

<style lang="scss" scoped>
.page-container {
  height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
  display: flex;
  flex-direction: column;
}

// iOS 系统提示条
.console-tip {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin: 16rpx 24rpx 8rpx;
  padding: 18rpx 24rpx;
  background: #eaf1ff;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: #3d66c9;

  .tip-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40rpx;
    height: 40rpx;
    border-radius: 50%;
    background: #dbe7ff;
    flex-shrink: 0;
  }
}

// iOS 分组卡片
.device-card {
  display: flex;
  align-items: center;
  gap: 22rpx;
  margin: 14rpx 24rpx 0;
  padding: 28rpx;
  background: var(--app-card-bg, #fff);
  border-radius: var(--app-card-radius, 28rpx);
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.975);
    opacity: 0.92;
  }
}

// app 图标式设备方块
.device-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 26rpx;
  background: linear-gradient(135deg, #b8c2d4, #8b96ab);
  color: #fff;
  font-size: 38rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 8rpx 18rpx rgba(23, 43, 77, 0.14);
  transition: background 0.3s ease;

  &.online {
    background: linear-gradient(135deg, #5d9bff 0%, #2f6bff 60%, #1f56d6 100%);
    box-shadow: 0 8rpx 20rpx rgba(47, 107, 255, 0.32);
  }
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.device-name {
  font-size: 31rpx;
  font-weight: 600;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);

  .meta-product {
    flex-shrink: 0;
    color: #7d8798;
  }
}

.device-id {
  max-width: 220rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14rpx;
  flex-shrink: 0;
}

// iOS 胶囊状态徽章
.status-badge {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: var(--app-fill, #eef0f4);
  font-size: 20rpx;
  font-weight: 600;
  color: #8a94a6;

  &.online {
    background: #e6f7f1;
    color: #0fa36e;
  }

  .status-dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    background: #c0c7d3;

    &.online {
      background: #12b77c;
      box-shadow: 0 0 0 4rpx rgba(18, 183, 124, 0.14);
    }
  }
}

.console-footer-space {
  height: 30rpx;
}
</style>
