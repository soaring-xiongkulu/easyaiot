<template>
  <view class="yd-page-container">
    <!-- 顶部导航栏 -->
    <wd-navbar
      title="编辑工作台"
      left-arrow placeholder safe-area-inset-top fixed
      @click-left="handleBack"
    />

    <!-- 搜索框 -->
    <view class="ios-search-bar">
      <view class="ios-search-pill">
        <wd-icon name="search-line" size="17px" color="#98a2b3" />
        <input
          v-model="searchKeyword"
          class="search-input flex-1"
          type="text"
          placeholder="搜索服务"
          placeholder-class="search-placeholder"
        >
        <wd-icon
          v-if="searchKeyword"
          name="close-circle-fill"
          size="15px"
          color="#c0c7d3"
          @click="searchKeyword = ''"
        />
      </view>
    </view>

    <!-- 常用区域 -->
    <view class="fav-card mx-24rpx mt-8rpx">
      <view class="card-head">
        <view class="section-bar" />
        <text class="card-title">常用</text>
        <text class="count-chip">{{ favoriteMenus.length }}</text>
      </view>
      <view v-if="favoriteMenus.length > 0" class="menu-list">
        <view
          v-for="(menu, idx) in favoriteMenus"
          :key="menu.key"
          class="menu-item"
          :class="{ 'menu-item--border': idx < favoriteMenus.length - 1 }"
        >
          <view class="menu-item__left">
            <view class="menu-item__icon">
              <wd-icon :name="menu.icon" size="42rpx" :color="menu.iconColor" />
            </view>
            <text class="menu-item__name">{{ menu.name }}</text>
          </view>
          <view class="opt-pill opt-pill--remove" @click="handleRemoveFavorite(menu)">
            <wd-icon name="minus" size="24rpx" color="#c2410c" />
            <text>移除</text>
          </view>
        </view>
      </view>
      <view v-else class="fav-empty" @click="scrollToGroups">
        <wd-icon name="plus" size="30rpx" color="#98a2b3" />
        <text>添加我常用的</text>
      </view>
    </view>

    <!-- 菜单分组 -->
    <view id="menuGroups">
      <view v-for="group in filteredMenuGroups" :key="group.key" class="fav-card mx-24rpx mt-24rpx">
        <view class="card-head">
          <view class="section-bar" :style="{ background: `linear-gradient(180deg, #7fa9ff, #2f6bff)` }" />
          <text class="card-title">{{ group.name }}</text>
        </view>
        <view class="menu-list">
          <view
            v-for="(menu, idx) in group.menus"
            :key="menu.key"
            class="menu-item"
            :class="{ 'menu-item--border': idx < group.menus.length - 1 }"
          >
            <view class="menu-item__left">
              <view class="menu-item__icon">
                <wd-icon :name="menu.icon" size="42rpx" :color="menu.iconColor" />
              </view>
              <text class="menu-item__name">{{ menu.name }}</text>
            </view>
            <view
              v-if="isInFavorites(menu)"
              class="opt-pill opt-pill--remove"
              @click="handleRemoveFavorite(menu)"
            >
              <wd-icon name="minus" size="24rpx" color="#c2410c" />
              <text>移除</text>
            </view>
            <view v-else class="opt-pill opt-pill--add" @click="handleAddFavorite(menu)">
              <wd-icon name="plus" size="24rpx" color="#2f6bff" />
              <text>添加</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部安全区域 -->
    <view class="h-40rpx" />
  </view>
</template>

<script lang="ts" setup>
import type { MenuGroup, MenuItem } from '../index'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { useUserStore } from '@/store/user'
import { navigateBackPlus } from '@/utils'
import { getAllMenuItems, getMenuGroups, getMenuItemByKey } from '../index'

defineOptions({
  name: 'FavoriteSettings',
})

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const userStore = useUserStore()
const toast = useToast()

const searchKeyword = ref('') // 搜索关键词
const menuGroups = ref<MenuGroup[]>([]) // 菜单分组列表
const favoriteMenus = computed<MenuItem[]>(() => {
  const keys = userStore.favoriteMenus
  if (!keys || keys.length === 0) {
    return []
  }
  return keys.map(key => getMenuItemByKey(key)).filter(Boolean) as MenuItem[]
}) // 常用服务菜单（从 store 中计算得出）

/** 过滤后的菜单分组 */
const filteredMenuGroups = computed(() => {
  if (!searchKeyword.value) {
    return menuGroups.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return menuGroups.value
    .map(group => ({
      ...group,
      menus: group.menus.filter(menu => menu.name.toLowerCase().includes(keyword)),
    }))
    .filter(group => group.menus.length > 0)
})

/** 返回上一页 */
function handleBack() {
  navigateBackPlus()
}

/** 初始化 */
function initData() {
  // 直接进入编辑页时也兜底：常用菜单默认全选（首次使用或旧版数据一次性初始化）
  userStore.initFavoriteMenus(getAllMenuItems().map(item => item.key))
  menuGroups.value = getMenuGroups()
}

/** 处理添加常用服务 */
function handleAddFavorite(menu: MenuItem) {
  const keys = [...userStore.favoriteMenus]
  if (!keys.includes(menu.key)) {
    keys.push(menu.key)
    userStore.setFavoriteMenus(keys)
  }
  toast.success('已添加')
}

/** 处理移除常用服务 */
function handleRemoveFavorite(menu: MenuItem) {
  const keys = [...userStore.favoriteMenus]
  const index = keys.indexOf(menu.key)
  if (index > -1) {
    keys.splice(index, 1)
    userStore.setFavoriteMenus(keys)
  }
  toast.success('已移除')
}

/** 检查菜单是否已添加到常用服务 */
function isInFavorites(menu: MenuItem): boolean {
  return favoriteMenus.value.some(m => m.key === menu.key)
}

/** 滚动到菜单分组区域 */
function scrollToGroups() {
  uni.pageScrollTo({
    selector: '#menuGroups',
    duration: 300,
  })
}

onLoad(() => {
  initData()
})
</script>

<style lang="scss" scoped>
.search-input {
  height: 100%;
  font-size: 27rpx;
  color: var(--app-text-1, #10131a);
}

.search-placeholder {
  color: var(--app-text-3, #98a2b3);
}

.fav-card {
  overflow: hidden;
  padding: 26rpx 22rpx 10rpx;
  background: var(--app-card-bg, #ffffff);
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 0 8rpx 20rpx;
}

.section-bar {
  width: 8rpx;
  height: 30rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #f5a623, #fa8c16);
}

.card-title {
  font-size: 29rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.count-chip {
  min-width: 44rpx;
  padding: 2rpx 12rpx;
  border-radius: 999rpx;
  background: #eaf1ff;
  color: #2f6bff;
  font-size: 21rpx;
  font-weight: 700;
  text-align: center;
}

.menu-list {
  padding-bottom: 12rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 22rpx 8rpx;

  &--border {
    border-bottom: 1rpx solid var(--app-separator);
  }

  &__left {
    display: flex;
    align-items: center;
    gap: 24rpx;
    min-width: 0;
  }

  &__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 80rpx;
    height: 80rpx;
    border-radius: 24rpx;
    background: rgba(47, 107, 255, 0.08);
    flex-shrink: 0;
  }

  &__name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 29rpx;
    font-weight: 600;
    color: var(--app-text-1, #10131a);
  }
}

.opt-pill {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 60rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  font-size: 23rpx;
  font-weight: 600;
  flex-shrink: 0;

  &:active {
    opacity: 0.85;
  }

  &--remove {
    color: #c2410c;
    background: #fff3e8;
  }

  &--add {
    color: #2f6bff;
    background: #eaf1ff;
  }
}

.fav-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  margin: 0 8rpx 16rpx;
  padding: 24rpx;
  border: 2rpx dashed #dde3ee;
  border-radius: 16rpx;
  font-size: 26rpx;
  color: #98a2b3;
}
</style>
