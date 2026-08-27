<template>
  <view class="video-page">
    <!-- 顶部渐变区 -->
    <view class="video-hero">
      <view class="hero-top">
        <view class="hero-title-row">
          <text class="hero-title">视频监控</text>
          <view class="hero-add" @click="handleCreate">
            <wd-icon name="plus" size="20px" color="#ffffff" />
          </view>
          <AppNavUserButton />
        </view>
      </view>

      <view class="hero-search">
        <wd-icon name="search-line" size="18px" color="#98a2b3" />
        <input
          v-model="keyword"
          class="hero-search-input"
          type="text"
          placeholder="搜索摄像头 / NVR / 国标设备"
          placeholder-class="hero-search-placeholder"
          confirm-type="search"
        >
        <wd-icon v-if="keyword" name="close-circle-fill" size="16px" color="#c0c7d3" @click="keyword = ''" />
      </view>

      <view class="hero-tabs">
        <view
          v-for="tab in onlineTabs"
          :key="tab.key"
          class="hero-tab"
          :class="{ 'hero-tab--active': onlineTab === tab.key }"
          @click="switchOnlineTab(tab.key)"
        >
          <text>{{ tab.label }}</text>
        </view>
      </view>
    </view>

    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="20"
      empty-view-text="暂无视频设备"
      @query="queryList"
    >
      <view class="px-24rpx">
        <view class="device-grid">
          <view
            v-for="item in list"
            :key="rowKey(item)"
            class="device-card"
            hover-class="device-card--pressed"
            :hover-stay-time="60"
            @click="handleItemClick(item)"
          >
            <view class="device-media">
              <view class="device-avatar">
                <wd-icon :name="kindIcon(item)" size="52rpx" color="#2f6bff" />
              </view>
              <view class="device-dot" :class="{ 'device-dot--online': item.online }" />
              <view v-if="item.channelCount" class="channel-badge">
                {{ item.channelCount }} 路
              </view>
            </view>
            <view class="device-name">
              {{ item.name }}
            </view>
            <view class="device-sub">
              {{ item.subtitle }}
            </view>
            <view class="device-tags">
              <text class="device-tag">
                {{ kindText(item) }}
              </text>
              <text v-if="item.device?.has_location" class="device-tag device-tag--green">
                已定位
              </text>
            </view>
          </view>
        </view>
        <view class="h-30rpx" />
      </view>
    </z-paging>

    <DetailPopup ref="detailPopupRef" @refresh="handleRefresh" @edit="handleEdit" />
    <CreatePopup ref="createPopupRef" @success="handleRefresh" />
    <EditPopup ref="editPopupRef" @success="handleRefresh" />
  </view>
</template>

<script lang="ts" setup>
import type { DeviceInfo } from '@/api/video/camera'
import type { DeviceRootRow } from '@/utils/video/deviceList'
import { ref } from 'vue'
import { getDeviceKindText } from '@/api/video/camera'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { fetchRootDeviceList } from '@/utils/video/deviceList'
import CreatePopup from './components/create-popup.vue'
import DetailPopup from './components/detail-popup.vue'
import EditPopup from './components/edit-popup.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const list = ref<DeviceRootRow[]>([])
const pagingRef = ref<any>()
const keyword = ref('')
const onlineTab = ref<'all' | 'online' | 'offline'>('all')
const cachedRows = ref<DeviceRootRow[]>([])
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>()
const createPopupRef = ref<InstanceType<typeof CreatePopup>>()
const editPopupRef = ref<InstanceType<typeof EditPopup>>()

const onlineTabs = [
  { key: 'all' as const, label: '全部' },
  { key: 'online' as const, label: '在线' },
  { key: 'offline' as const, label: '离线' },
]

const onlineFilterValue = computed(() => {
  if (onlineTab.value === 'online')
    return true
  if (onlineTab.value === 'offline')
    return false
  return undefined
})

function rowKey(item: DeviceRootRow) {
  return `${item.rowKind}-${item.nvrId ?? item.sipDeviceId ?? item.device?.id ?? item.name}`
}

function kindText(item: DeviceRootRow) {
  if (item.rowKind === 'nvr')
    return 'NVR'
  if (item.rowKind === 'gb28181')
    return '国标'
  return getDeviceKindText(item.device?.device_kind) || '摄像头'
}

function kindIcon(item: DeviceRootRow) {
  if (item.rowKind === 'nvr')
    return 'list'
  if (item.rowKind === 'gb28181')
    return 'camera'
  return 'video-camera'
}

async function loadAllRows() {
  cachedRows.value = await fetchRootDeviceList({
    search: keyword.value.trim() || undefined,
    online: onlineFilterValue.value,
  })
}

async function queryList(pageNo: number, pageSize: number) {
  try {
    if (pageNo === 1 || !cachedRows.value.length)
      await loadAllRows()
    const start = (pageNo - 1) * pageSize
    const page = cachedRows.value.slice(start, start + pageSize)
    pagingRef.value?.completeByTotal(page, cachedRows.value.length)
  } catch {
    cachedRows.value = []
    pagingRef.value?.complete(false)
  }
}

function switchOnlineTab(key: 'all' | 'online' | 'offline') {
  if (onlineTab.value === key)
    return
  onlineTab.value = key
  handleRefresh()
}

// tab 页有缓存，回到本页时静默刷新
onShow(() => {
  if (cachedRows.value.length) {
    handleRefresh()
  }
})

function handleRefresh() {
  cachedRows.value = []
  pagingRef.value?.reload()
}

function handleCreate() {
  createPopupRef.value?.openCreate()
}

function handleEdit(device: DeviceInfo) {
  editPopupRef.value?.openEdit(device)
}

function handleItemClick(item: DeviceRootRow) {
  if (item.rowKind === 'nvr' && item.nvrId != null) {
    uni.navigateTo({
      url: `/pages/device/nvr/index?nvrId=${item.nvrId}&title=${encodeURIComponent(item.name)}`,
    })
    return
  }
  if (item.rowKind === 'gb28181' && item.sipDeviceId) {
    uni.navigateTo({
      url: `/pages/device/gb28181/index?sipId=${encodeURIComponent(item.sipDeviceId)}&title=${encodeURIComponent(item.name)}`,
    })
    return
  }
  if (item.device)
    detailPopupRef.value?.open(item.device)
}
</script>

<style lang="scss" scoped>
.video-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
}

// ==================== 顶部渐变区 ====================
.video-hero {
  padding: calc(env(safe-area-inset-top) + 24rpx) 24rpx 24rpx;
  background: linear-gradient(160deg, #3f7bff 0%, #2f6bff 45%, #2456d8 100%);
  border-bottom-left-radius: 36rpx;
  border-bottom-right-radius: 36rpx;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.hero-title {
  font-size: 36rpx;
  font-weight: 800;
  color: #ffffff;
  flex: 1;
}

.hero-add {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
}

.hero-search {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 24rpx;
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

.hero-tabs {
  display: flex;
  gap: 14rpx;
  margin-top: 22rpx;
}

.hero-tab {
  padding: 10rpx 30rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.85);
  font-size: 24rpx;
  font-weight: 600;
  transition: all 0.18s ease;

  &--active {
    background: #ffffff;
    color: #2f6bff;
  }
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

.device-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 8rpx 20rpx rgba(47, 107, 255, 0.16);
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
}

.channel-badge {
  position: absolute;
  left: 16rpx;
  bottom: 14rpx;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(15, 23, 42, 0.55);
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 600;
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

.device-sub {
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
  color: #2f6bff;
  background: #eaf1ff;

  &--green {
    color: #0fa36e;
    background: #e6f7f1;
  }
}
</style>
