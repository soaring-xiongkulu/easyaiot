<template>
  <view class="yd-page-container">
    <!-- 顶部导航栏 -->
    <wd-navbar
      title="通讯录"
      placeholder safe-area-inset-top fixed
    />

    <!-- 面包屑导航 -->
    <Breadcrumb ref="breadcrumbRef" v-model="currentDeptId" />

    <!-- 通讯录列表 -->
    <view class="p-24rpx">
      <!-- 部门列表 -->
      <view class="group-card">
        <view
          v-for="(item, idx) in currentDeptList"
          :key="`dept-${item.id}`"
          class="group-row"
          :class="{ 'group-row--border': idx < currentDeptList.length - 1 }"
          hover-class="group-row--pressed"
          :hover-stay-time="60"
          @click="handleEnterDept(item)"
        >
          <view class="dept-icon">
            <wd-icon name="folder" size="36rpx" color="#ffffff" />
          </view>
          <view class="min-w-0 flex-1">
            <view class="row-title">
              {{ item.name }}
            </view>
            <view v-if="item.children && item.children.length > 0" class="row-sub">
              {{ item.children.length }} 个子部门
            </view>
          </view>
          <wd-icon name="arrow-right" size="15px" color="#c0c7d3" />
        </view>
      </view>

      <!-- 用户列表 -->
      <view v-if="currentDeptList.length > 0 && currentUserList.length > 0" class="divider-line">
        <view class="divider-bar" />
        <text>部门成员</text>
        <view class="divider-bar" />
      </view>
      <view v-if="currentUserList.length > 0" class="group-card">
        <view
          v-for="(item, idx) in currentUserList"
          :key="`user-${item.id}`"
          class="group-row"
          :class="{ 'group-row--border': idx < currentUserList.length - 1 }"
          hover-class="group-row--pressed"
          :hover-stay-time="60"
          @click="handleUserClick(item)"
        >
          <view v-if="item.avatar" class="mr-18rpx shrink-0">
            <wd-img :src="item.avatar" width="80rpx" height="80rpx" mode="aspectFill" round />
          </view>
          <view v-else class="user-avatar">
            {{ item.nickname?.charAt(0) || item.username?.charAt(0) }}
          </view>
          <view class="min-w-0 flex-1">
            <view class="row-title">
              {{ item.nickname }}
            </view>
          </view>
          <wd-icon name="phone" size="30rpx" color="#12b77c" />
          <wd-icon name="arrow-right" size="15px" color="#c0c7d3" class="ml-10rpx" />
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && currentDeptList.length === 0 && currentUserList.length === 0" class="py-100rpx text-center">
        <wd-empty icon="no-content" tip="暂无数据" />
      </view>
      <view class="h-40rpx" />
    </view>
  </view>
</template>

<script lang="ts" setup>
import type { Dept } from '@/api/system/dept'
import type { User } from '@/api/system/user'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { computed, onMounted, ref } from 'vue'
import { getSimpleDeptList } from '@/api/system/dept'
import { getSimpleUserList, getUser } from '@/api/system/user'
import { findChildren, handleTree } from '@/utils/tree'
import Breadcrumb from './components/breadcrumb.vue'

definePage({
  style: {
    navigationBarTitleText: '',
    navigationStyle: 'custom',
  },
})

const loading = ref(false) // 列表加载状态
const deptList = ref<Dept[]>([]) // 完整部门列表（树形结构）
const userList = ref<User[]>([]) // 用户列表
const toast = useToast()

const currentDeptId = ref(0) // 当前层级的部门编号
const breadcrumbRef = ref<InstanceType<typeof Breadcrumb>>()

/** 当前层级的部门列表 */
const currentDeptList = computed(() => {
  if (currentDeptId.value === 0) {
    return deptList.value.filter(item => item.parentId === 0)
  }
  return findChildren(deptList.value, currentDeptId.value)
})

/** 当前层级的用户列表 */
const currentUserList = computed(() => {
  if (currentDeptId.value === 0) {
    // 根层级不显示用户，只显示部门
    return []
  }
  return userList.value.filter(item => item.deptId === currentDeptId.value)
})

/** 进入部门层级 */
function handleEnterDept(item: Dept) {
  breadcrumbRef.value?.enter({ id: item.id!, name: item.name })
}

/** 点击用户：弹出联系方式 */
async function handleUserClick(item: User) {
  const userInfo = await getUser(item.id!)
  const actions: string[] = []
  if (userInfo.mobile) {
    actions.push(`手机：${userInfo.mobile}`)
  }
  if (userInfo.email) {
    actions.push(`邮箱：${userInfo.email}`)
  }
  if (actions.length === 0) {
    toast.show('暂无联系方式')
    return
  }
  uni.showActionSheet({
    title: userInfo.nickname,
    itemList: actions,
    success: (res) => {
      const selected = actions[res.tapIndex]
      if (selected.startsWith('手机')) {
        uni.makePhoneCall({ phoneNumber: userInfo.mobile! })
      } else if (selected.startsWith('邮箱')) {
        uni.setClipboardData({
          data: userInfo.email!,
          success: () => {
            uni.hideToast()
            toast.success('邮箱已复制')
          },
        })
      }
    },
  })
}

/** 初始化 */
onMounted(async () => {
  loading.value = true
  try {
    // 获取部门列表
    const deptData = await getSimpleDeptList()
    deptList.value = handleTree(deptData)
    // 获取用户列表
    userList.value = await getSimpleUserList()
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.group-card {
  overflow: hidden;
  background: var(--app-card-bg, #ffffff);
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow);
}

.group-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 26rpx 28rpx;
  transition: background-color 0.12s ease;

  &--pressed {
    background-color: #f7f9fd;
  }

  &--border {
    border-bottom: 1rpx solid var(--app-separator);
  }
}

.dept-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #5d9bff 0%, #2f6bff 60%, #2456d8 100%);
  box-shadow: 0 8rpx 20rpx rgba(47, 107, 255, 0.24);
  flex-shrink: 0;
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #6fe3b1 0%, #12b77c 70%);
  box-shadow: 0 8rpx 20rpx rgba(18, 183, 124, 0.22);
  flex-shrink: 0;
}

.row-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 29rpx;
  font-weight: 600;
  color: var(--app-text-1, #10131a);
}

.row-sub {
  margin-top: 6rpx;
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);
}

.divider-line {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 28rpx 6rpx;

  text {
    font-size: 23rpx;
    color: var(--app-text-3, #98a2b3);
  }
}

.divider-bar {
  flex: 1;
  height: 1rpx;
  background: var(--app-separator);
}
</style>
