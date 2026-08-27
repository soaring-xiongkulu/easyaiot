<template>
  <view
    class="chan-card"
    hover-class="chan-card--pressed"
    :hover-stay-time="60"
    @click="emit('click')"
  >
    <view class="chan-head">
      <view class="chan-avatar">
        <wd-icon name="camera-fill" size="38rpx" color="#ffffff" />
      </view>
      <view class="min-w-0 flex-1">
        <view class="truncate text-29rpx font-semibold" style="color: var(--app-text-1, #10131a)">
          {{ item.name || item.id }}
        </view>
        <view class="mt-6rpx truncate text-23rpx" style="color: var(--app-text-3, #98a2b3)">
          {{ subtitle }}
        </view>
      </view>
      <view v-if="showOnline" class="online-pill" :class="item.online ? 'online-pill--on' : 'online-pill--off'">
        <view class="online-pill-dot" />
        <text>{{ item.online ? '在线' : '离线' }}</text>
      </view>
    </view>

    <view class="meta-row">
      <text class="meta-pill meta-pill--blue">{{ getDeviceKindText(item.device_kind) }}</text>
      <text v-if="item.has_location" class="meta-pill meta-pill--green">已定位</text>
      <text v-if="item.nvr_label" class="meta-pill">{{ item.nvr_label }}</text>
      <text v-if="item.nvr_channel != null && item.nvr_channel > 0" class="meta-pill">CH{{ item.nvr_channel }}</text>
    </view>

    <view v-if="item.address" class="addr-row">
      <wd-icon name="location" size="24rpx" color="#98a2b3" />
      <text class="truncate">{{ item.address }}</text>
    </view>
  </view>
</template>

<script lang="ts" setup>
import type { DeviceInfo } from '@/api/video/camera'
import { computed } from 'vue'
import { getDeviceKindText } from '@/api/video/camera'

const props = withDefaults(defineProps<{
  item: DeviceInfo
  showOnline?: boolean
}>(), {
  showOnline: true,
})

const emit = defineEmits<{
  click: []
}>()

const subtitle = computed(() => {
  const ip = props.item.ip
  if (ip)
    return props.item.port ? `${ip}:${props.item.port}` : ip
  return props.item.id
})
</script>

<style lang="scss" scoped>
.chan-card {
  margin-bottom: 22rpx;
  padding: 26rpx 28rpx;
  background: var(--app-card-bg, #ffffff);
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow);
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.98);
    opacity: 0.92;
  }
}

.chan-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.chan-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #5d9bff 0%, #2f6bff 60%, #2456d8 100%);
  box-shadow: 0 8rpx 20rpx rgba(47, 107, 255, 0.26);
  flex-shrink: 0;
}

.online-pill {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 600;
  flex-shrink: 0;

  &--on {
    color: #0fa36e;
    background: #e6f7f1;

    .online-pill-dot {
      background: #12b77c;
      box-shadow: 0 0 0 5rpx rgba(18, 183, 124, 0.16);
    }
  }

  &--off {
    color: #e5484d;
    background: #fef2f2;

    .online-pill-dot {
      background: #e5484d;
    }
  }

  .online-pill-dot {
    width: 11rpx;
    height: 11rpx;
    border-radius: 50%;
  }
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.meta-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #6b7688;
  background: #f4f6fb;

  &--blue {
    color: #2f6bff;
    background: #eaf1ff;
  }

  &--green {
    color: #0fa36e;
    background: #e6f7f1;
  }
}

.addr-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-top: 18rpx;
  min-width: 0;

  text {
    font-size: 24rpx;
    color: var(--app-text-3, #98a2b3);
  }
}
</style>
