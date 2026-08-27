<template>
  <view class="user-page">
    <!-- 顶部渐变区 + 用户卡 -->
    <view class="user-hero">
      <view class="user-card" @click="handleGoProfile">
        <view class="avatar-wrapper">
          <wd-img :src="displayAvatar" width="120rpx" height="120rpx" mode="aspectFill" round custom-class="user-avatar" />
        </view>
        <view class="flex-1 min-w-0">
          <view class="user-name">
            {{ userInfo.nickname || userInfo.username || '未登录' }}
          </view>
          <view class="user-desc">
            {{ userProfile?.dept?.name || '智能物联网平台' }}
          </view>
        </view>
        <wd-icon name="arrow-right" size="18px" color="rgba(255,255,255,0.8)" />
      </view>
    </view>

    <!-- 服务宫格：原工作台全部能力收纳于此 -->
    <view v-for="group in menuGroups" :key="group.key" class="card">
      <view class="card-head">
        <view class="section-bar" />
        <text class="card-title">{{ group.name }}</text>
      </view>
      <MenuGrid :menus="group.menus" />
    </view>

    <!-- 账号 -->
    <view class="card list-card">
      <TenantSwitcher />
      <view class="list-cell" @click="handleGoProfile">
        <view class="cell-icon" style="background: #eaf1ff">
          <wd-icon name="user" size="20px" color="#2f6bff" />
        </view>
        <text class="cell-title">个人资料</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
      <view class="list-cell" @click="handleGoSecurity">
        <view class="cell-icon" style="background: #e6f7f1">
          <wd-icon name="lock" size="20px" color="#0fa36e" />
        </view>
        <text class="cell-title">账号安全</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
      <view class="list-cell">
        <view class="cell-icon" style="background: #eef0f4">
          <wd-icon name="info-circle" size="20px" color="#6b7688" />
        </view>
        <text class="cell-title">当前版本</text>
        <text class="cell-value">{{ appVersion }}</text>
      </view>
    </view>

    <!-- 通用 -->
    <view class="card list-card">
      <view class="list-cell" @click="handleGoFaq">
        <view class="cell-icon" style="background: #fdf3e2">
          <wd-icon name="exclamation-circle" size="20px" color="#d97706" />
        </view>
        <text class="cell-title">常见问题</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
      <view class="list-cell" @click="handleGoFeedback">
        <view class="cell-icon" style="background: #f3eaff">
          <wd-icon name="edit" size="20px" color="#7c3aed" />
        </view>
        <text class="cell-title">意见反馈</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
      <view class="list-cell" @click="handleGoContact">
        <view class="cell-icon" style="background: #e0f7f9">
          <wd-icon name="phone" size="20px" color="#0e9aa9" />
        </view>
        <text class="cell-title">联系客服</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
      <view class="list-cell" @click="handleGoSettings">
        <view class="cell-icon" style="background: #eaf1ff">
          <wd-icon name="settings" size="20px" color="#2f6bff" />
        </view>
        <text class="cell-title">应用设置</text>
        <wd-icon name="arrow-right" size="16px" color="#c8cfda" />
      </view>
    </view>

    <view class="px-24rpx pb-safe">
      <view v-if="isLoggedIn" class="logout-btn" @click="handleLogout">
        退出登录
      </view>
      <view v-else class="login-btn" @click="handleGoLogin">
        去登录
      </view>
      <view class="h-30rpx" />
    </view>
  </view>
</template>

<script lang="ts" setup>
import type { UserProfileVO } from '@/api/system/user/profile'
import MenuGrid from '@/pages/index/components/menu-grid.vue'
import { getMenuGroups } from '@/pages/index/index'
import { useDialog } from '@wot-ui/ui/components/wd-dialog'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { getUserProfile } from '@/api/system/user/profile'
import { LOGIN_PAGE } from '@/router/config'
import { useUserStore } from '@/store'
import { useTokenStore } from '@/store/token'
import { resolveAvatarDisplayUrl } from '@/utils/mediaDisplay'
import TenantSwitcher from './components/tenant-switcher.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const userStore = useUserStore()
const tokenStore = useTokenStore()
const toast = useToast()
const dialog = useDialog()
const { userInfo } = storeToRefs(userStore)
const userProfile = ref<UserProfileVO | null>(null)

const isLoggedIn = computed(() => tokenStore.hasLogin)
const displayAvatar = computed(() => resolveAvatarDisplayUrl(userInfo.value.avatar))
const menuGroups = computed(() => getMenuGroups())

/** App 版本号：App 端取 manifest versionName，其余端展示 H5 */
const appVersion = computed(() => {
  // #ifdef APP-PLUS
  const plus = (globalThis as any).plus
  if (plus?.runtime?.version) {
    return `V${plus.runtime.version}`
  }
  return 'V1.0.0'
  // #endif
  // eslint-disable-next-line no-unreachable
  return 'H5'
})

onMounted(async () => {
  if (!isLoggedIn.value)
    return
  try {
    userProfile.value = await getUserProfile()
    await userStore.fetchUserInfo()
  } catch {
    // ignore
  }
})

function handleGoProfile() {
  uni.navigateTo({ url: '/pages-core/user/profile/index' })
}

function handleGoSecurity() {
  uni.navigateTo({ url: '/pages-core/user/security/index' })
}

function handleGoFaq() {
  uni.navigateTo({ url: '/pages-core/user/faq/index' })
}

function handleGoFeedback() {
  uni.navigateTo({ url: '/pages-core/user/feedback/index' })
}

function handleGoContact() {
  uni.navigateTo({ url: '/pages-core/user/contact/index' })
}

function handleGoSettings() {
  uni.navigateTo({ url: '/pages-core/user/settings/index' })
}

function handleGoLogin() {
  uni.navigateTo({ url: LOGIN_PAGE })
}

async function handleLogout() {
  try {
    await dialog.confirm({
      title: '提示',
      msg: '确定要退出登录吗？',
    })
  } catch {
    return
  }

  await tokenStore.logout()
  toast.success('退出登录成功')
  setTimeout(() => {
    uni.reLaunch({ url: LOGIN_PAGE })
  }, 500)
}
</script>

<style lang="scss" scoped>
.user-page {
  min-height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
  padding-bottom: 40rpx;
}

// ==================== 顶部渐变 + 用户卡 ====================
.user-hero {
  padding: calc(env(safe-area-inset-top) + 40rpx) 24rpx 90rpx;
  background: linear-gradient(160deg, #3f7bff 0%, #2f6bff 48%, #2456d8 100%);
  border-bottom-left-radius: 36rpx;
  border-bottom-right-radius: 36rpx;
  margin-bottom: -60rpx;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  position: relative;
  z-index: 1;
}

.avatar-wrapper {
  border: 4rpx solid rgba(255, 255, 255, 0.55);
  border-radius: 50%;
  box-shadow: 0 8rpx 20rpx rgba(13, 34, 101, 0.25);
}

.user-avatar {
  display: block;
}

.user-name {
  font-size: 38rpx;
  font-weight: 800;
  color: #ffffff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

// ==================== 分组卡片 ====================
.card {
  margin: 24rpx 24rpx 0;
  padding: 26rpx 22rpx 18rpx;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
}

.card-head {
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

.card-title {
  font-size: 29rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

// ==================== 列表分组 ====================
.list-card {
  padding: 8rpx 26rpx;
}

.list-cell {
  display: flex;
  align-items: center;
  gap: 22rpx;
  padding: 26rpx 0;
  border-bottom: 1rpx solid var(--app-separator, rgba(23, 43, 77, 0.06));

  &:last-child {
    border-bottom: none;
  }

  &:active {
    opacity: 0.7;
  }
}

.cell-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  flex-shrink: 0;
}

.cell-title {
  flex: 1;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--app-text-1, #10131a);
}

.cell-value {
  font-size: 26rpx;
  color: var(--app-text-3, #98a2b3);
}

// ==================== 登录/退出 ====================
.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 92rpx;
  border-radius: 28rpx;
  background: #ffffff;
  color: #e5484d;
  font-size: 30rpx;
  font-weight: 600;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04));

  &:active {
    opacity: 0.85;
  }
}

.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 92rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 600;
  box-shadow: 0 10rpx 24rpx rgba(47, 107, 255, 0.3);

  &:active {
    opacity: 0.9;
  }
}
</style>
