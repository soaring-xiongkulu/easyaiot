<template>
  <view class="yd-page-container yd-page-container-paging">
    <!-- 顶部导航栏 -->
    <wd-navbar
      title="我的消息"
      placeholder safe-area-inset-top fixed
    />

    <!-- 搜索组件 -->
    <SearchForm @search="handleQuery" @reset="handleReset" @read-all="handleReadAll" />

    <!-- 消息列表 -->
    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      :refresher-enabled="true"
      :inside-more="true"
      :loading-more-default-as-loading="true"
      empty-view-text="暂无消息"
      @query="queryList"
    >
      <view class="p-24rpx">
        <view
          v-for="item in list"
          :key="item.id"
          class="msg-card"
          hover-class="msg-card--pressed"
          :hover-stay-time="60"
          @click="handleDetail(item)"
        >
          <view class="msg-head">
            <view class="msg-avatar">
              <wd-icon name="notification" size="36rpx" color="#ffffff" />
              <view v-if="!item.readStatus" class="unread-dot" />
            </view>
            <view class="min-w-0 flex-1">
              <view class="truncate text-29rpx font-semibold" style="color: var(--app-text-1, #10131a)">
                {{ item.templateNickname }}
              </view>
              <view class="mt-4rpx text-22rpx" style="color: var(--app-text-3, #98a2b3)">
                {{ formatDateTime(item.createTime) }}
              </view>
            </view>
            <text
              v-if="!item.readStatus"
              class="read-pill"
              @click.stop="handleReadOne(item)"
            >
              标记已读
            </text>
            <view v-else class="done-pill">
              <wd-icon name="doublecheck" size="22rpx" color="#98a2b3" />
            </view>
          </view>

          <view class="msg-body">
            <view class="msg-title line-clamp-1">
              {{ getDictLabel(DICT_TYPE.SYSTEM_NOTIFY_TEMPLATE_TYPE, item.templateType) }}
            </view>
            <view class="msg-content line-clamp-2">
              {{ item.templateContent }}
            </view>
          </view>
        </view>
        <view class="h-20rpx" />
      </view>
    </z-paging>

    <!-- 详情弹窗 -->
    <DetailPopup ref="detailPopupRef" />
  </view>
</template>

<script lang="ts" setup>
import type { NotifyMessage } from '@/api/system/notify/message'
import { useDialog } from '@wot-ui/ui/components/wd-dialog'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { ref } from 'vue'
import {
  getMyNotifyMessagePage,
  updateAllNotifyMessageRead,
  updateNotifyMessageRead,
} from '@/api/system/notify/message'
import { getDictLabel } from '@/hooks/useDict'
import { DICT_TYPE } from '@/utils/constants'
import { formatDateTime } from '@/utils/date'
import DetailPopup from './components/detail-popup.vue'
import SearchForm from './components/search-form.vue'

definePage({
  style: {
    navigationBarTitleText: '',
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const dialog = useDialog()
const list = ref<NotifyMessage[]>([]) // 列表数据
const pagingRef = ref<any>() // 分页组件引用
const queryParams = ref<Record<string, any>>({}) // 查询参数
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>() // 详情弹窗

/** 查询消息列表 */
async function queryList(pageNo: number, pageSize: number) {
  try {
    const params = {
      ...queryParams.value,
      pageNo,
      pageSize,
    }
    const data = await getMyNotifyMessagePage(params)
    pagingRef.value?.completeByTotal(data.list, data.total)
  } catch {
    pagingRef.value?.complete(false)
  }
}

/** 搜索按钮操作 */
function handleQuery(data?: Record<string, any>) {
  queryParams.value = { ...data }
  reload()
}

/** 重置按钮操作 */
function handleReset() {
  handleQuery()
}

/** 重新加载 */
function reload() {
  pagingRef.value?.reload()
}

/** 查看详情 */
function handleDetail(item: NotifyMessage) {
  // 如果未读，先标记已读
  if (!item.readStatus) {
    handleReadOne(item, false)
  }
  // 打开详情弹窗
  detailPopupRef.value?.open(item)
}

/** 标记单条已读 */
async function handleReadOne(item: NotifyMessage, showToast = true) {
  try {
    await updateNotifyMessageRead(item.id)
  } catch {
    if (showToast) {
      toast.error('操作失败')
    }
    return
  }
  // 更新本地状态
  item.readStatus = true
  item.readTime = new Date()
  if (showToast) {
    toast.success('已标记为已读')
  }
}

/** 标记全部已读 */
async function handleReadAll() {
  try {
    await dialog.confirm({
      title: '提示',
      msg: '确定要将所有消息标记为已读吗？',
    })
  } catch {
    return
  }
  try {
    await updateAllNotifyMessageRead()
  } catch {
    toast.error('全部已读失败')
    return
  }
  toast.success('全部已读成功')
  // 刷新列表
  reload()
}
</script>

<style lang="scss" scoped>
.msg-card {
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

.msg-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.msg-avatar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #7fa9ff 0%, #2f6bff 60%, #2456d8 100%);
  box-shadow: 0 8rpx 20rpx rgba(47, 107, 255, 0.26);
  flex-shrink: 0;

  .unread-dot {
    position: absolute;
    top: -2rpx;
    right: -2rpx;
    width: 20rpx;
    height: 20rpx;
    border-radius: 50%;
    background: #e5484d;
    border: 4rpx solid #ffffff;
  }
}

.read-pill {
  display: flex;
  align-items: center;
  height: 52rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 600;
  color: #2f6bff;
  background: #eaf1ff;
  flex-shrink: 0;

  &:active {
    opacity: 0.85;
  }
}

.done-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: #f4f6fb;
  flex-shrink: 0;
}

.msg-body {
  margin-top: 20rpx;
  padding: 20rpx 22rpx;
  border-radius: 16rpx;
  background: #f7f9fd;
}

.msg-title {
  font-size: 27rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.msg-content {
  margin-top: 8rpx;
  font-size: 25rpx;
  line-height: 1.6;
  color: var(--app-text-3, #98a2b3);
}
</style>
