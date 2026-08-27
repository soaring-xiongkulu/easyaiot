<template>
  <scroll-view class="min-h-0 flex-1" scroll-y scroll-with-animation>
    <!-- 常用分组 -->
    <view class="mx-20rpx mt-20rpx overflow-hidden rounded-28rpx bg-white menu-card">
      <view class="flex items-center justify-between px-24rpx py-20rpx">
        <text class="text-28rpx text-[#1a2233] font-semibold">常用</text>
        <view class="p-10rpx" @click="handleGotoFavoriteSettings">
          <wd-icon name="settings" size="32rpx" color="#98a2b3" />
        </view>
      </view>
      <MenuGrid v-if="favoriteMenuItems.length > 0" :menus="favoriteMenuItems" />
      <view
        v-else
        class="mx-24rpx mb-24rpx flex items-center border-2rpx border-[#dde3ee] rounded-16rpx border-dashed px-24rpx py-12rpx"
        @click="handleGotoFavoriteSettings"
      >
        <wd-icon name="plus" size="32rpx" color="#98a2b3" />
        <text class="pl-10rpx text-28rpx text-[#98a2b3]">添加我常用的</text>
      </view>
    </view>

    <!-- 菜单分组 -->
    <view v-for="group in menuGroups" :key="group.key" class="mx-20rpx mt-20rpx overflow-hidden rounded-28rpx bg-white menu-card">
      <view class="px-24rpx pb-0 pt-20rpx">
        <text class="text-28rpx text-[#1a2233] font-semibold">{{ group.name }}</text>
      </view>
      <MenuGrid :menus="group.menus" />
    </view>

    <!-- 底部安全区域 -->
    <view class="h-40rpx" />
  </scroll-view>
</template>

<script lang="ts" setup>
import type { MenuGroup, MenuItem } from '../index'
import { useUserStore } from '@/store/user'
import { getMenuGroups, getMenuItemByKey } from '../index'
import MenuGrid from './menu-grid.vue'

defineOptions({
  name: 'MenuSection',
})

const userStore = useUserStore()

/** 菜单分组列表 */
const menuGroups = ref<MenuGroup[]>([])

/** 常用服务菜单（从 store 中计算得出） */
const favoriteMenuItems = computed<MenuItem[]>(() => {
  const keys = userStore.favoriteMenus
  if (!keys || keys.length === 0) {
    return []
  }
  return keys.map(key => getMenuItemByKey(key)).filter(Boolean) as MenuItem[]
})

/** 初始化 */
function initData() {
  menuGroups.value = getMenuGroups()
}

/** 跳转到常用服务设置页面 */
function handleGotoFavoriteSettings() {
  uni.navigateTo({
    url: '/pages/index/settings/index',
  })
}

/**
 * 初始化
 *
 * 不使用 onMounted 的原因是：登录后，页面可能已经挂载，但数据需要重新初始化
 */
onShow(() => {
  initData()
})
</script>

<style lang="scss" scoped>
.menu-card {
  box-shadow: var(--app-card-shadow, 0 4rpx 20rpx rgba(23, 43, 77, 0.05));
}
</style>
