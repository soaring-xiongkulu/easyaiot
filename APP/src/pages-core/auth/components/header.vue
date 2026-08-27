<template>
  <view class="auth-header">
    <view class="auth-header__brand">
      <view class="auth-header__logo-wrap">
        <wd-img
          class="auth-header__logo"
          src="/static/logo.png"
          width="120rpx"
          height="120rpx"
          mode="aspectFit"
        />
      </view>
      <view class="auth-header__title">
        {{ title }}
      </view>
      <view v-if="subtitle" class="auth-header__subtitle">
        {{ subtitle }}
      </view>
    </view>
  </view>
</template>

<script lang="ts" setup>
withDefaults(defineProps<{
  subtitle?: string
}>(), {
  subtitle: '',
})

const title = import.meta.env.VITE_APP_TITLE
</script>

<style lang="scss" scoped>
$brand: #2f6bff;

.auth-header {
  position: relative;
  z-index: 1;
  padding: calc(env(safe-area-inset-top) + 80rpx) 48rpx 36rpx;

  &__brand {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__logo-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 168rpx;
    height: 168rpx;
    margin-bottom: 32rpx;
    background: #fff;
    border-radius: 44rpx;
    box-shadow:
      0 0 0 2rpx rgba(47, 107, 255, 0.08),
      0 20rpx 48rpx rgba(47, 107, 255, 0.18);
  }

  &__logo {
    width: 120rpx;
    height: 120rpx;
  }

  &__title {
    font-size: 46rpx;
    font-weight: 700;
    color: #10131a;
    letter-spacing: 1rpx;
  }

  &__subtitle {
    margin-top: 18rpx;
    padding: 8rpx 30rpx;
    font-size: 24rpx;
    font-weight: 500;
    color: $brand;
    background: rgba(47, 107, 255, 0.08);
    border-radius: 999rpx;
    letter-spacing: 3rpx;
  }
}

@media (min-width: 768px) {
  .auth-header {
    padding: 40px 36px 24px;
  }
}
</style>
