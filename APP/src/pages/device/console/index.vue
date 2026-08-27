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
          <text>选择设备，按其产品的面板模板进入定制控制页</text>
        </view>
      </template>

      <view
        v-for="(item, index) in deviceList"
        :key="item.id"
        class="device-card"
        @click="handleOpenControl(item)"
      >
        <view class="device-avatar" :class="{ online: isOnline(item) }">
          {{ (item.deviceName || '设').slice(0, 1) }}
        </view>
        <view class="device-info">
          <view class="device-name-row">
            <text class="device-name">{{ item.deviceName || item.deviceIdentification }}</text>
            <view class="status-dot" :class="{ online: isOnline(item) }" />
            <text class="status-text" :class="{ online: isOnline(item) }">
              {{ isOnline(item) ? '在线' : '离线' }}
            </text>
          </view>
          <view class="device-meta">
            <text>{{ item.productName || item.productIdentification || '未绑定产品' }}</text>
            <text v-if="item.deviceIdentification" class="device-id">
              {{ item.deviceIdentification }}
            </text>
          </view>
        </view>
        <wd-icon name="arrow-right" color="#c0c8d4" size="18px" />
      </view>
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
  background: #f5f7fb;
  display: flex;
  flex-direction: column;
}

.console-tip {
  padding: 16rpx 32rpx 8rpx;
  font-size: 22rpx;
  color: #98a2b3;
}

.device-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin: 12rpx 24rpx;
  padding: 26rpx;
  background: #fff;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(23, 43, 77, 0.05);
}

.device-avatar {
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #66a6ff, #0957de);
  color: #fff;
  font-size: 34rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.55;

  &.online {
    opacity: 1;
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
  font-size: 30rpx;
  font-weight: 600;
  color: #10131a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #cbd2dd;

  &.online {
    background: #16a377;
  }
}

.status-text {
  font-size: 22rpx;
  color: #98a2b3;

  &.online {
    color: #16a377;
  }
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #98a2b3;
}

.device-id {
  max-width: 240rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
