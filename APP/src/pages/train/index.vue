<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="模型训练" placeholder safe-area-inset-top fixed>
      <template #right>
        <view class="flex items-center gap-16rpx pr-16rpx">
          <view class="nav-action" @click="handleCreate">
            <wd-icon name="plus" size="20px" color="#2f6bff" />
          </view>
          <AppNavUserButton />
        </view>
      </template>
    </wd-navbar>

    <SearchForm @search="handleQuery" @reset="handleReset" />

    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      empty-view-text="暂无训练任务"
      @query="queryList"
    >
      <view class="p-24rpx">
        <view
          v-for="item in list"
          :key="item.id"
          class="task-card"
          hover-class="task-card--pressed"
          :hover-stay-time="60"
          @click="handleDetail(item)"
        >
          <view class="task-head">
            <view class="task-avatar">
              <wd-icon name="time-line" size="40rpx" color="#ffffff" />
            </view>
            <view class="min-w-0 flex-1">
              <view class="truncate text-30rpx font-semibold" style="color: var(--app-text-1, #10131a)">
                {{ item.name || item.task_name }}
              </view>
              <view class="mt-6rpx truncate text-24rpx" style="color: var(--app-text-3, #98a2b3)">
                {{ item.dataset_name || '-' }} · {{ item.dataset_version || '-' }}
              </view>
            </view>
            <view class="status-pill" :class="`status-pill--${getTrainStatusTagType(item.status)}`">
              {{ getTrainStatusText(item.status) }}
            </view>
          </view>

          <view class="progress-area">
            <view class="progress-head">
              <text class="progress-label">训练进度</text>
              <text class="progress-num">{{ Math.round(item.progress ?? 0) }}%</text>
            </view>
            <view class="progress-bar">
              <view class="progress-inner" :style="{ width: `${Math.min(100, Math.max(0, item.progress ?? 0))}%` }" />
            </view>
          </view>

          <view class="foot-row">
            <view class="foot-chip">
              <wd-icon name="storage" size="22rpx" color="#6b7688" />
              <text>{{ item.schedule_policy || 'local' }}</text>
            </view>
            <text class="foot-time">{{ formatDateTime(item.start_time) }}</text>
          </view>

          <view v-if="isTrainTaskActive(item.status)" class="action-row" @click.stop>
            <view class="act-btn act-btn--danger" @click="handleQuickStop(item)">
              <wd-icon name="stop" size="26rpx" color="#ffffff" />
              <text>停止训练</text>
            </view>
          </view>
        </view>
        <view class="h-20rpx" />
      </view>
    </z-paging>

    <DetailPopup ref="detailPopupRef" @refresh="reload" @resume="handleResume" @retrain="handleRetrain" />
    <EditPopup ref="editPopupRef" @success="reload" />
  </view>
</template>

<script lang="ts" setup>
import type { TrainTask } from '@/api/model/train'
import { onUnmounted, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { getTrainTaskPage, stopTrain } from '@/api/model/train'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { formatDateTime } from '@/utils/date'
import { parseListResponse } from '@/utils/listResponse'
import { getTrainStatusTagType, getTrainStatusText, isTrainTaskActive } from '@/utils/model/trainTaskUtils'
import DetailPopup from './components/detail-popup.vue'
import EditPopup from './components/edit-popup.vue'
import SearchForm from './components/search-form.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const list = ref<TrainTask[]>([])
const pagingRef = ref<any>()
const queryParams = ref<Record<string, any>>({})
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>()
const editPopupRef = ref<InstanceType<typeof EditPopup>>()
let pollTimer: ReturnType<typeof setInterval> | null = null

async function queryList(pageNo: number, pageSize: number) {
  try {
    const res = await getTrainTaskPage({ ...queryParams.value, pageNo, pageSize })
    const { list: data, total } = parseListResponse<TrainTask>(res, ['data', 'list'])
    pagingRef.value?.completeByTotal(data, total)
    setupPolling(data)
  } catch {
    pagingRef.value?.complete(false)
  }
}

function setupPolling(data: TrainTask[]) {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  const hasActive = data.some(item => isTrainTaskActive(item.status))
  if (hasActive) {
    pollTimer = setInterval(() => {
      pagingRef.value?.refresh()
    }, 10000)
  }
}

onUnmounted(() => {
  if (pollTimer)
    clearInterval(pollTimer)
})

function handleQuery(data?: Record<string, any>) {
  queryParams.value = { ...data }
  reload()
}

function handleReset() {
  handleQuery()
}

function reload() {
  pagingRef.value?.reload()
}

function handleCreate() {
  editPopupRef.value?.openCreate()
}

function handleResume(item: TrainTask) {
  editPopupRef.value?.openResume(item)
}

function handleRetrain(item: TrainTask) {
  editPopupRef.value?.openRetrain(item)
}

function handleDetail(item: TrainTask) {
  detailPopupRef.value?.open(item)
}

async function handleQuickStop(item: TrainTask) {
  try {
    await stopTrain(item.id)
    toast.success('已发送停止指令')
    reload()
  } catch {
    toast.error('停止失败')
  }
}
</script>

<style lang="scss" scoped>
.nav-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #eaf1ff;
}

.task-card {
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

.task-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.task-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #f7a2c4 0%, #ec64a8 60%, #eb2f96 100%);
  box-shadow: 0 10rpx 20rpx rgba(235, 47, 150, 0.26);
  flex-shrink: 0;
}

.status-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 600;
  color: #2f6bff;
  background: #eaf1ff;
  flex-shrink: 0;

  &--success {
    color: #0fa36e;
    background: #e6f7f1;
  }

  &--warning {
    color: #d97706;
    background: #fdf3e2;
  }

  &--danger {
    color: #e5484d;
    background: #fef2f2;
  }

  &--info,
  &--primary {
    color: #2f6bff;
    background: #eaf1ff;
  }
}

.progress-area {
  margin-top: 22rpx;
  padding: 18rpx 22rpx;
  border-radius: 16rpx;
  background: #f7f9fd;
}

.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.progress-label {
  font-size: 23rpx;
  color: var(--app-text-3, #98a2b3);
}

.progress-num {
  font-size: 25rpx;
  font-weight: 700;
  color: #eb2f96;
}

.progress-bar {
  height: 14rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: #e6eaf2;
}

.progress-inner {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #f7a2c4, #eb2f96);
  transition: width 0.3s ease;
}

.foot-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
  margin-top: 18rpx;
}

.foot-chip {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 600;
  color: #6b7688;
  background: #f4f6fb;
}

.foot-time {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 22rpx;
  color: var(--app-text-3, #98a2b3);
}

.action-row {
  margin-top: 20rpx;
}

.act-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  height: 68rpx;
  border-radius: 999rpx;
  font-size: 25rpx;
  font-weight: 600;
  transition: opacity 0.12s ease;

  &:active {
    opacity: 0.85;
  }

  &--danger {
    color: #ffffff;
    background: linear-gradient(135deg, #ff7d84, #e5484d);
    box-shadow: 0 8rpx 20rpx rgba(229, 72, 77, 0.24);
  }
}
</style>
