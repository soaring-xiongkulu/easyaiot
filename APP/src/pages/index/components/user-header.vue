<template>
  <view class="hero-card" :style="heroBg">
    <view class="hero-inner">
      <view class="avatar-wrapper mr-20rpx">
        <wd-img :src="userInfo.avatar" width="100rpx" height="100rpx" mode="aspectFill" round />
      </view>
      <view class="flex-1 min-w-0">
        <view class="hero-greeting">
          {{ greeting }}，{{ userInfo.nickname || userInfo.username }}
        </view>
        <view class="hero-desc">
          {{ description }}
        </view>
      </view>
    </view>
  </view>
</template>

<script lang="ts" setup>
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store'

defineOptions({
  name: 'UserHeader',
})

const userStore = useUserStore()
const { userInfo } = storeToRefs(userStore)

/** 品牌渐变背景 */
const heroBg = {
  background: 'linear-gradient(135deg, #2f6bff 0%, #4a8bff 55%, #6fa8ff 100%)',
}

/** 根据时间获取问候语 */
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) {
    return '凌晨好'
  } else if (hour < 9) {
    return '早上好'
  } else if (hour < 12) {
    return '上午好'
  } else if (hour < 14) {
    return '中午好'
  } else if (hour < 17) {
    return '下午好'
  } else if (hour < 19) {
    return '傍晚好'
  } else {
    return '晚上好'
  }
})

/** 描述语 */
const description = computed(() => {
  const hour = new Date().getHours()
  if (hour < 9) {
    return '开始新的一天，加油！'
  } else if (hour < 12) {
    return '工作顺利，效率满满！'
  } else if (hour < 14) {
    return '午休时间，记得休息~'
  } else if (hour < 18) {
    return '继续努力，收获满满！'
  } else {
    return '辛苦了，注意休息！'
  }
})
</script>

<style lang="scss" scoped>
.hero-card {
  position: relative;
  margin: 24rpx 24rpx 0;
  border-radius: 32rpx;
  overflow: hidden;
  box-shadow: 0 16rpx 40rpx rgba(47, 107, 255, 0.24);
  // 右上角柔光装饰
  &::after {
    content: '';
    position: absolute;
    right: -60rpx;
    top: -100rpx;
    width: 300rpx;
    height: 300rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.14);
  }

  // 左下角次级光斑
  &::before {
    content: '';
    position: absolute;
    left: -80rpx;
    bottom: -120rpx;
    width: 260rpx;
    height: 260rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }
}

.hero-inner {
  display: flex;
  align-items: center;
  padding: 36rpx 32rpx;
  position: relative;
  z-index: 1;
}

.avatar-wrapper {
  border: 4rpx solid rgba(255, 255, 255, 0.55);
  box-shadow: 0 8rpx 20rpx rgba(13, 34, 101, 0.25);
}

.hero-greeting {
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 1rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-desc {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}
</style>
