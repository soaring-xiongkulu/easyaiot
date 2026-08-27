<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="告警事件" placeholder safe-area-inset-top fixed>
      <template #right>
        <AppNavUserButton />
      </template>
    </wd-navbar>

    <SearchForm @search="handleQuery" @reset="handleReset" @clear-all="handleClearAll" />

    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      empty-view-text="暂无告警"
      @query="queryList"
    >
      <view class="p-24rpx">
        <view
          v-for="item in list"
          :key="String(item.id)"
          class="alert-card"
          hover-class="alert-card--pressed"
          :hover-stay-time="60"
          @click="handleDetail(item)"
        >
          <view class="alert-card-accent" :class="`alert-card-accent--${getAlertEventTagType(item.event)}`" />
          <image
            v-if="item.image_url"
            :src="resolveAlertImageDisplayUrl(item.image_url)"
            mode="aspectFill"
            class="alert-img"
          />
          <view v-else class="alert-img alert-img--empty">
            <wd-icon name="exclamation-circle" size="44rpx" color="#c0c7d3" />
          </view>
          <view class="min-w-0 flex-1 py-24rpx pr-24rpx">
            <view class="mb-10rpx flex items-start justify-between gap-12rpx">
              <view class="line-clamp-2 flex-1 text-29rpx text-[#10131a] font-semibold leading-snug">
                {{ formatAlertListTitle(item) }}
              </view>
              <view class="event-pill" :class="`event-pill--${getAlertEventTagType(item.event)}`">
                {{ formatAlertEvent(item.event) }}
              </view>
            </view>
            <view class="mb-6rpx truncate text-25rpx text-[#3d4558]">
              {{ item.device_name || item.device_id }}
            </view>
            <view class="mb-12rpx truncate text-23rpx text-[#98a2b3]">
              {{ item.task_name || '-' }}
            </view>
            <view class="flex items-center justify-between">
              <view class="task-pill">
                {{ getTaskTypeText(item.task_type) }}
              </view>
              <text class="text-22rpx text-[#98a2b3]">
                {{ formatDateTime(item.time) }}
              </text>
            </view>
          </view>
        </view>
      </view>
    </z-paging>

    <DetailPopup ref="detailPopupRef" />
  </view>
</template>

<script lang="ts" setup>
import type { AlertRecord } from '@/api/video/alert'
import { ref } from 'vue'
import { useDialog } from '@wot-ui/ui/components/wd-dialog'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { clearAllAlarms, queryAlarmList } from '@/api/video/alert'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { formatDateTime } from '@/utils/date'
import { parseListResponse } from '@/utils/listResponse'
import {
  formatAlertEvent,
  formatAlertListTitle,
  getAlertEventTagType,
  getTaskTypeText,
} from '@/utils/video/alertDisplay'
import { resolveAlertImageDisplayUrl } from '@/utils/mediaDisplay'
import DetailPopup from './components/detail-popup.vue'
import SearchForm from './components/search-form.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const dialog = useDialog()
const list = ref<AlertRecord[]>([])
const pagingRef = ref<any>()
const queryParams = ref<Record<string, any>>({})
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>()
async function queryList(pageNo: number, pageSize: number) {
  try {
    const res = await queryAlarmList({ ...queryParams.value, pageNo, pageSize })
    const { list: data, total } = parseListResponse<AlertRecord>(res, ['alert_list'])
    pagingRef.value?.completeByTotal(data, total)
  }
  catch {
    pagingRef.value?.complete(false)
  }
}

function handleQuery(data?: Record<string, any>) {
  queryParams.value = { ...data }
  pagingRef.value?.reload()
}

function handleReset() {
  handleQuery()
}

function handleDetail(item: AlertRecord) {
  detailPopupRef.value?.open(item)
}

async function handleClearAll() {
  try {
    await dialog.confirm({
      title: '清空告警',
      msg: '确定清空全部告警记录？此操作不可恢复。',
    })
  }
  catch {
    return
  }
  try {
    await clearAllAlarms()
    toast.success('已清空全部告警')
    pagingRef.value?.reload()
  }
  catch {
    toast.error('清空失败')
  }
}
</script>

<style lang="scss" scoped>
.alert-card {
  position: relative;
  display: flex;
  overflow: hidden;
  margin-bottom: 22rpx;
  background: #ffffff;
  border-radius: 26rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.98);
    opacity: 0.92;
  }
}

// 事件级别左侧色条
.alert-card-accent {
  width: 8rpx;
  flex-shrink: 0;
  background: #98a2b3;

  &--danger {
    background: linear-gradient(180deg, #ff7d84, #e5484d);
  }

  &--warning {
    background: linear-gradient(180deg, #ffd08a, #f59e0b);
  }

  &--success {
    background: linear-gradient(180deg, #6fe3b1, #12b77c);
  }

  &--primary {
    background: linear-gradient(180deg, #7fa9ff, #2f6bff);
  }
}

.alert-img {
  width: 180rpx;
  height: 200rpx;
  margin: 24rpx 0 24rpx 16rpx;
  border-radius: 18rpx;
  background: #f0f2f6;
  flex-shrink: 0;

  &--empty {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.event-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  flex-shrink: 0;
  background: #eef0f4;
  color: #6b7688;

  &--danger {
    color: #e5484d;
    background: #fef2f2;
  }

  &--warning {
    color: #d97706;
    background: #fdf3e2;
  }

  &--success {
    color: #0fa36e;
    background: #e6f7f1;
  }

  &--primary {
    color: #2f6bff;
    background: #eaf1ff;
  }
}

.task-pill {
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
  color: #6b7688;
  background: #f4f6fb;
}
</style>
