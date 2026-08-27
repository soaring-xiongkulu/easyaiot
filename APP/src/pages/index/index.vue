<template>
  <view class="home-page">
    <!-- 顶部蓝色渐变区：问候 + 搜索 + 状态筛选 -->
    <view class="home-hero">
      <view class="hero-top">
        <view class="hero-user" @click="goUser">
          <wd-img :src="displayAvatar" width="72rpx" height="72rpx" mode="aspectFill" round custom-class="hero-avatar" />
          <view class="hero-texts">
            <text class="hero-greeting">{{ greeting }}，{{ displayName }}</text>
            <text class="hero-sub">设备在线 {{ statusCount.onlineCount }} 台 · 离线 {{ statusCount.offlineCount }} 台</text>
          </view>
        </view>
        <view class="hero-bell" @click="goAlert">
          <wd-icon name="notification" size="22px" color="#ffffff" />
        </view>
      </view>

      <view class="hero-search">
        <wd-icon name="search-line" size="18px" color="#98a2b3" />
        <input
          v-model="keyword"
          class="hero-search-input"
          type="text"
          placeholder="搜索设备名称 / 标识"
          placeholder-class="hero-search-placeholder"
          confirm-type="search"
        >
        <wd-icon v-if="keyword" name="close-circle-fill" size="16px" color="#c0c7d3" @click="keyword = ''" />
      </view>

      <view class="hero-tabs">
        <view
          v-for="tab in filterTabs"
          :key="tab.key"
          class="hero-tab"
          :class="{ 'hero-tab--active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <text>{{ tab.label }}</text>
          <text v-if="tab.count != null" class="hero-tab-count">{{ tab.count }}</text>
        </view>
      </view>
    </view>

    <!-- 设备卡片网格 -->
    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="20"
      empty-view-text="暂无设备，下拉刷新试试"
      @query="queryList"
    >
      <view class="px-24rpx pt-8rpx">
        <view class="device-grid">
          <view
            v-for="item in list"
            :key="item.id"
            class="device-card"
            hover-class="device-card--pressed"
            :hover-stay-time="60"
            @click="openDetail(item)"
          >
            <view class="device-media">
              <image v-if="productImgOf(item)" :src="productImgOf(item)" mode="aspectFit" class="device-img" />
              <view v-else class="device-avatar" :class="`device-avatar--${statusOf(item)}`">
                <text>{{ avatarLetter(item) }}</text>
              </view>
              <view class="device-dot" :class="`device-dot--${statusOf(item)}`" />
            </view>
            <view class="device-name">
              {{ item.deviceName || item.deviceIdentification || '未命名设备' }}
            </view>
            <view class="device-product">
              {{ productNameOf(item) }}
            </view>
            <view class="device-tags">
              <text v-if="statusOf(item) === 'inactive'" class="device-tag device-tag--grey">未激活</text>
              <text v-if="isSubDevice(item)" class="device-tag device-tag--blue">子设备</text>
              <text v-if="item.deviceVersion" class="device-tag device-tag--plain">v{{ item.deviceVersion }}</text>
            </view>
          </view>
        </view>

        <!-- 常用服务 -->
        <view class="service-card">
          <view class="service-head">
            <view class="section-bar" />
            <text class="service-title">常用服务</text>
            <view class="flex-1" />
            <wd-icon name="settings" size="30rpx" color="#98a2b3" @click="goFavoriteSettings" />
          </view>
          <MenuGrid v-if="serviceMenus.length" :menus="serviceMenus" />
          <view v-else class="service-empty" @click="goFavoriteSettings">
            <wd-icon name="plus" size="30rpx" color="#98a2b3" />
            <text>添加我常用的</text>
          </view>
        </view>
        <view class="h-40rpx" />
      </view>
    </z-paging>
  </view>
</template>

<script lang="ts" setup>
import type { IotDeviceItem } from '@/api/device/panel'
import { storeToRefs } from 'pinia'
import {
  getIotDevicePage,
  getIotDeviceStatusCount,
  getProductNameMap,
  normalizeConnectStatus,
} from '@/api/device/panel'
import { useUserStore } from '@/store'
import { resolveAvatarDisplayUrl } from '@/utils/mediaDisplay'
import { getAllMenuItems, getMenuGroups, getMenuItemByKey } from './index'
import MenuGrid from './components/menu-grid.vue'

defineOptions({
  name: 'Home',
})

definePage({
  type: 'home',
  style: {
    navigationStyle: 'custom',
  },
})

const userStore = useUserStore()
const { userInfo } = storeToRefs(userStore)

// 常用菜单默认全选（首次使用或旧版数据时一次性初始化，之后尊重用户自选）
userStore.initFavoriteMenus(getAllMenuItems().map(item => item.key))

const pagingRef = ref()
const list = ref<IotDeviceItem[]>([])
const allDevices = ref<IotDeviceItem[]>([])
const productMap = ref<Map<string, { productName?: string, productImg?: string }>>(new Map())
const statusCount = ref({ onlineCount: 0, offlineCount: 0, initCount: 0 })
const keyword = ref('')
const activeTab = ref<'all' | 'online' | 'offline' | 'sub'>('all')

const displayName = computed(() => userInfo.value.nickname || userInfo.value.username || '游客')
const displayAvatar = computed(() => resolveAvatarDisplayUrl(userInfo.value.avatar))

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6)
    return '凌晨好'
  if (hour < 9)
    return '早上好'
  if (hour < 12)
    return '上午好'
  if (hour < 14)
    return '中午好'
  if (hour < 18)
    return '下午好'
  return '晚上好'
})

const isSubDevice = (item: IotDeviceItem) => !!item.parentIdentification
const statusOf = (item: IotDeviceItem) => normalizeConnectStatus(item.connectStatus)

function productNameOf(item: IotDeviceItem) {
  return item.productIdentification
    ? productMap.value.get(item.productIdentification)?.productName || item.productIdentification
    : '未绑定产品'
}

function productImgOf(item: IotDeviceItem) {
  const img = item.productIdentification ? productMap.value.get(item.productIdentification)?.productImg : ''
  return img || ''
}

function avatarLetter(item: IotDeviceItem) {
  return (item.deviceName || item.deviceIdentification || '设').slice(0, 1).toUpperCase()
}

const filterTabs = computed(() => {
  const all = allDevices.value
  return [
    { key: 'all' as const, label: '全部', count: all.length },
    { key: 'online' as const, label: '在线', count: all.filter(d => statusOf(d) === 'online').length },
    { key: 'offline' as const, label: '离线', count: all.filter(d => statusOf(d) === 'offline').length },
    { key: 'sub' as const, label: '子设备', count: all.filter(d => isSubDevice(d)).length },
  ]
})

function matchFilter(item: IotDeviceItem) {
  if (activeTab.value === 'online' && statusOf(item) !== 'online')
    return false
  if (activeTab.value === 'offline' && statusOf(item) !== 'offline')
    return false
  if (activeTab.value === 'sub' && !isSubDevice(item))
    return false
  if (keyword.value) {
    const kw = keyword.value.trim().toLowerCase()
    const hit
      = (item.deviceName || '').toLowerCase().includes(kw)
        || (item.deviceIdentification || '').toLowerCase().includes(kw)
        || productNameOf(item).toLowerCase().includes(kw)
    if (!hit)
      return false
  }
  return true
}

async function loadAllDevices() {
  const [pageRes, productRes] = await Promise.all([
    getIotDevicePage({ pageNum: 1, pageSize: 500 }),
    getProductNameMap(),
  ])
  allDevices.value = pageRes.list
  if (productRes.size) {
    productMap.value = productRes
  }
  try {
    statusCount.value = await getIotDeviceStatusCount()
  } catch {
    // 统计失败不影响列表
  }
}

async function queryList(pageNo: number, pageSize: number) {
  try {
    if (pageNo === 1 || !allDevices.value.length) {
      await loadAllDevices()
    }
    const filtered = allDevices.value.filter(matchFilter)
    const start = (pageNo - 1) * pageSize
    pagingRef.value?.completeByTotal(filtered.slice(start, start + pageSize), filtered.length)
  } catch {
    allDevices.value = []
    pagingRef.value?.complete(false)
  }
}

function reload() {
  pagingRef.value?.reload()
}

watch([keyword, activeTab], () => {
  reload()
})

// tab 页有缓存，回到首页时静默刷新最新状态
onShow(() => {
  if (allDevices.value.length) {
    reload()
  }
})

function openDetail(item: IotDeviceItem) {
  const query = [
    `id=${encodeURIComponent(String(item.id ?? ''))}`,
    `deviceIdentification=${encodeURIComponent(item.deviceIdentification || '')}`,
    `productIdentification=${encodeURIComponent(item.productIdentification || '')}`,
    `name=${encodeURIComponent(item.deviceName || '')}`,
  ].join('&')
  uni.navigateTo({ url: `/pages/device/detail/index?${query}` })
}

function goAlert() {
  uni.switchTab({ url: '/pages/alert/index' })
}

function goUser() {
  uni.switchTab({ url: '/pages/user/index' })
}

function goFavoriteSettings() {
  uni.navigateTo({ url: '/pages/index/settings/index' })
}

/** 常用服务：优先用户自选，未设置时给一组默认入口 */
const serviceMenus = computed(() => {
  const keys = userStore.favoriteMenus
  if (keys && keys.length > 0) {
    return keys.map(key => getMenuItemByKey(key)).filter(Boolean) as any[]
  }
  const firstGroup = getMenuGroups()[0]
  return firstGroup ? firstGroup.menus.slice(0, 8) : []
})
</script>

<style lang="scss" scoped>
.home-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
}

// ==================== 顶部渐变区 ====================
.home-hero {
  padding: calc(env(safe-area-inset-top) + 24rpx) 24rpx 24rpx;
  background: linear-gradient(160deg, #3f7bff 0%, #2f6bff 45%, #2456d8 100%);
  border-bottom-left-radius: 36rpx;
  border-bottom-right-radius: 36rpx;

  &::after {
    content: '';
    position: absolute;
  }
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-user {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-width: 0;
}

.hero-avatar {
  border: 3rpx solid rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
}

.hero-texts {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.hero-greeting {
  font-size: 32rpx;
  font-weight: 700;
  color: #ffffff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-sub {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.78);
}

.hero-bell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  flex-shrink: 0;
}

// 搜索框：白底胶囊浮在渐变上
.hero-search {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 26rpx;
  padding: 0 28rpx;
  height: 76rpx;
  border-radius: 999rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 26rpx rgba(13, 34, 101, 0.16);
}

.hero-search-input {
  flex: 1;
  height: 100%;
  font-size: 27rpx;
  color: var(--app-text-1, #10131a);
}

:deep(.hero-search-placeholder),
.hero-search-placeholder {
  color: #98a2b3;
}

// 状态筛选 tab
.hero-tabs {
  display: flex;
  gap: 14rpx;
  margin-top: 22rpx;
  overflow-x: auto;

  &::-webkit-scrollbar {
    display: none;
  }
}

.hero-tab {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 26rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.85);
  font-size: 24rpx;
  font-weight: 600;
  flex-shrink: 0;
  transition: all 0.18s ease;

  &--active {
    background: #ffffff;
    color: #2f6bff;
  }
}

.hero-tab-count {
  font-size: 22rpx;
  opacity: 0.85;
}

// ==================== 设备卡片网格 ====================
.device-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
  padding-top: 20rpx;
}

.device-card {
  overflow: hidden;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.97);
    opacity: 0.92;
  }
}

.device-media {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 176rpx;
  background: linear-gradient(180deg, #f5f8ff 0%, #eef2fa 100%);
}

.device-img {
  width: 100%;
  height: 100%;
  padding: 16rpx;
  box-sizing: border-box;
}

.device-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 104rpx;
  height: 104rpx;
  border-radius: 30rpx;
  color: #ffffff;
  font-size: 44rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #b8c2d4, #8b96ab);

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

.device-dot {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: #c0c7d3;

  &--online {
    background: #12b77c;
    box-shadow: 0 0 0 6rpx rgba(18, 183, 124, 0.16);
  }

  &--offline {
    background: #c0c7d3;
  }

  &--inactive {
    background: #e6b35a;
  }
}

.device-name {
  padding: 18rpx 22rpx 0;
  font-size: 28rpx;
  font-weight: 600;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-product {
  padding: 6rpx 22rpx 0;
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  padding: 14rpx 22rpx 22rpx;
}

.device-tag {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;

  &--blue {
    color: #2f6bff;
    background: #eaf1ff;
  }

  &--grey {
    color: #8a94a6;
    background: #eef0f4;
  }

  &--plain {
    color: #6b7688;
    background: #f4f6fb;
  }
}

// ==================== 常用服务 ====================
.service-card {
  margin-top: 28rpx;
  padding: 26rpx 22rpx 18rpx;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
}

.service-head {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 0 6rpx 18rpx;
}

.section-bar {
  width: 8rpx;
  height: 30rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #4a8bff, #2f6bff);
}

.service-title {
  font-size: 29rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.service-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  margin: 0 12rpx 16rpx;
  padding: 22rpx;
  border: 2rpx dashed #dde3ee;
  border-radius: 16rpx;
  font-size: 26rpx;
  color: #98a2b3;
}
</style>
