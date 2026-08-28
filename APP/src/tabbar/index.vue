<script setup lang="ts">
/* eslint-disable brace-style */ // 原因：unibest 官方维护的代码，尽量不要大概，避免难以合并
// i-carbon-video i-carbon-flow-stream i-carbon-task-settings i-carbon-warning i-carbon-notification i-carbon-cube i-carbon-ai-results i-carbon-model-builder i-carbon-user-avatar
import type { CustomTabBarItem } from './types'
import { customTabbarEnable, needHideNativeTabbar, tabbarCacheEnable } from './config'
import { tabbarList, tabbarStore } from './store'

// #ifdef MP-WEIXIN
// 将自定义节点设置成虚拟的（去掉自定义组件包裹层），更加接近Vue组件的表现，能更好的使用flex属性
defineOptions({
  virtualHost: true,
})
// #endif

/**
 * 中间的鼓包tabbarItem的点击事件
 */
function handleClickBulge() {
  uni.showToast({
    title: '点击了中间的鼓包tabbarItem',
    icon: 'none',
  })
}

function handleClick(index: number) {
  const item = tabbarList[index]
  if (!item || !tabbarStore.isTabbarItemVisible(index)) {
    return
  }
  // 当前高亮和真实页面都已经是目标 tab 时，不重复跳转
  if (index === tabbarStore.curIdx && tabbarStore.isCurrentRouteTabbarItem(index)) {
    return
  }
  if (item.isBulge) {
    handleClickBulge()
    return
  }
  const url = item.pagePath
  const prevIdx = tabbarStore.curIdx
  const syncTabbarAfterNavigation = () => {
    tabbarStore.syncCurIdxByCurrentPageAsync()
  }
  const restoreTabbarWhenNavigationFailed = () => {
    tabbarStore.setCurIdx(prevIdx)
  }
  tabbarStore.setCurIdx(index)
  if (tabbarCacheEnable) {
    uni.switchTab({
      url,
      success: syncTabbarAfterNavigation,
      fail: restoreTabbarWhenNavigationFailed,
    })
  }
  else {
    uni.navigateTo({
      url,
      success: syncTabbarAfterNavigation,
      fail: restoreTabbarWhenNavigationFailed,
    })
  }
}
// #ifndef MP-WEIXIN || MP-ALIPAY
// 因为有了 custom:true， 微信里面不需要多余的hide操作
onLoad(() => {
  // 解决原生 tabBar 未隐藏导致有2个 tabBar 的问题
  needHideNativeTabbar
  && uni.hideTabBar({
    fail(err) {
      console.log('hideTabBar fail: ', err)
    },
    success(res) {
      // console.log('hideTabBar success: ', res)
    },
  })
})
// #endif

// #ifdef MP-ALIPAY
onMounted(() => {
  // 解决支付宝自定义tabbar 未隐藏导致有2个 tabBar 的问题; 注意支付宝很特别，需要在 onMounted 钩子调用
  customTabbarEnable // 另外，支付宝里面，只要是 customTabbar 都需要隐藏
  && uni.hideTabBar({
    fail(err) {
      console.log('hideTabBar fail: ', err)
    },
    success(res) {
      // console.log('hideTabBar success: ', res)
    },
  })
})
// #endif
const activeColor = 'var(--app-brand, #2f6bff)'
const inactiveColor = '#8a94a6'
function getColorByIndex(index: number) {
  return tabbarStore.curIdx === index ? activeColor : inactiveColor
}

function getImageByIndex(index: number, item: CustomTabBarItem) {
  if (!item.iconActive) {
    console.warn('image 模式下，需要配置 iconActive (高亮时的图片），否则无法切换高亮图片')
    return item.icon
  }
  return tabbarStore.curIdx === index ? item.iconActive : item.icon
}
</script>

<template>
  <view v-if="customTabbarEnable" class="h-50px pb-safe">
    <view class="border-and-fixed bg-white" @touchmove.stop.prevent>
      <view class="h-50px flex items-center">
        <template v-for="(item, index) in tabbarList" :key="index">
          <view
            v-if="tabbarStore.isTabbarItemVisible(index)"
            class="flex flex-1 flex-col items-center justify-center"
            :style="{ color: getColorByIndex(index) }"
            @click="handleClick(index)"
          >
            <view v-if="item.isBulge" class="relative">
              <!-- 中间一个鼓包tabbarItem的处理 -->
              <view class="bulge">
                <!-- TODO 2/2: 中间鼓包tabbarItem配置：通常是一个图片，或者icon，点击触发业务逻辑 -->
                <!-- 常见的是：扫描按钮、发布按钮、更多按钮等 -->
                <image class="mt-6rpx h-200rpx w-200rpx" src="/static/tabbar/scan.png" />
              </view>
            </view>
            <view v-else class="relative px-3 text-center">
              <template v-if="item.iconType === 'uiLib'">
                <!-- TODO: 以下内容请根据选择的UI库自行替换 -->
                <!-- 如：<wd-icon name="home" /> (https://wot-ui.cn/component/icon.html) -->
                <!-- 如：<uv-icon name="home" /> (https://www.uvui.cn/components/icon) -->
                <!-- 如：<sar-icon name="image" /> (https://sard.wzt.zone/sard-uniapp-docs/components/icon)(sar没有home图标^_^) -->
                <wd-icon :name="item.icon" size="20" />
              </template>
              <template v-if="item.iconType === 'unocss' || item.iconType === 'iconfont'">
                <view
                  class="icon-pill"
                  :class="{ 'icon-pill-active': tabbarStore.curIdx === index }"
                  :style="{ color: getColorByIndex(index) }"
                >
                  <view :class="item.icon" class="text-20px" />
                </view>
              </template>
              <template v-if="item.iconType === 'image'">
                <image :src="getImageByIndex(index, item)" mode="scaleToFill" class="h-20px w-20px" />
              </template>
              <view class="mt-2px text-11px leading-none" :style="{ color: getColorByIndex(index) }">
                {{ item.text }}
              </view>
              <!-- 角标显示 -->
              <view v-if="item.badge">
                <template v-if="item.badge === 'dot'">
                  <view class="absolute right-0 top-0 h-2 w-2 rounded-full bg-#f56c6c" />
                </template>
                <template v-else>
                  <view class="absolute top-0 box-border h-5 min-w-5 center rounded-full bg-#f56c6c px-1 text-center text-xs text-white -right-3">
                    {{ item.badge > 99 ? '99+' : item.badge }}
                  </view>
                </template>
              </view>
            </view>
          </view>
        </template>
      </view>

      <view class="pb-safe" />
    </view>
  </view>
</template>

<style scoped lang="scss">
.border-and-fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;

  // 毛玻璃质感：半透明白 + 模糊 + 极淡顶部描边与投影
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px);
  border-top: 1rpx solid rgba(23, 43, 77, 0.06);
  box-shadow: 0 -4rpx 24rpx rgba(23, 43, 77, 0.06);
  box-sizing: border-box;
}

// 图标胶囊底座：选中时浮现主色浅底，强化焦点
.icon-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 27px;
  margin-top: 6px;
  border-radius: 999px;
  transition: background-color 0.2s ease;
}

.icon-pill-active {
  background: var(--app-brand-tint, #eaefff);
}

// 中间鼓包的样式
.bulge {
  position: absolute;
  top: -20px;
  left: 50%;
  transform-origin: top center;
  transform: translateX(-50%) scale(0.5) translateY(-33%);
  display: flex;
  justify-content: center;
  align-items: center;
  width: 250rpx;
  height: 250rpx;
  border-radius: 50%;
  background-color: #fff;
  box-shadow: inset 0 0 0 1px #fefefe;

  &:active {
    // opacity: 0.8;
  }
}
</style>
