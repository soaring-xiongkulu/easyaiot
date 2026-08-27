<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="算法任务" placeholder safe-area-inset-top fixed>
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
      empty-view-text="暂无算法任务"
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
              <wd-icon name="experiment" size="40rpx" color="#ffffff" />
            </view>
            <view class="min-w-0 flex-1">
              <view class="truncate text-30rpx font-semibold" style="color: var(--app-text-1, #10131a)">
                {{ item.task_name }}
              </view>
              <view class="mt-6rpx truncate text-24rpx" style="color: var(--app-text-3, #98a2b3)">
                {{ item.device_names?.join('、') || `${item.device_ids?.length || 0} 个设备` }}
              </view>
            </view>
            <view class="run-pill" :class="item.is_enabled ? 'run-pill--on' : 'run-pill--off'">
              <view class="run-pill-dot" />
              <text>{{ item.is_enabled ? '运行中' : '已停止' }}</text>
            </view>
          </view>

          <view class="meta-row">
            <text class="meta-pill" :class="`meta-pill--${getTaskTypeTagType(item.task_type)}`">
              {{ getAlgorithmTaskTypeText(item.task_type, item.executor) }}
            </text>
            <text v-if="item.alert_event_enabled" class="meta-pill meta-pill--warning">
              告警
            </text>
          </view>

          <view class="stat-row">
            <view class="stat-item">
              <text class="stat-num">{{ item.total_detections ?? 0 }}</text>
              <text class="stat-label">检测</text>
            </view>
            <view class="stat-divider" />
            <view v-if="item.task_type === 'snap'" class="stat-item">
              <text class="stat-num">{{ item.total_captures ?? 0 }}</text>
              <text class="stat-label">抓拍</text>
            </view>
            <view v-else class="stat-item">
              <text class="stat-num">{{ item.total_frames ?? 0 }}</text>
              <text class="stat-label">帧数</text>
            </view>
          </view>

          <view class="action-row" @click.stop>
            <view
              v-if="!item.is_enabled"
              class="act-btn act-btn--primary"
              @click="handleQuickStart(item)"
            >
              <wd-icon name="play-arrow-fill" size="26rpx" color="#ffffff" />
              <text>启动</text>
            </view>
            <view
              v-else
              class="act-btn act-btn--warning"
              @click="handleQuickStop(item)"
            >
              <wd-icon name="pause-circle" size="26rpx" color="#ffffff" />
              <text>停止</text>
            </view>
            <view class="act-btn act-btn--ghost" @click="handleDetail(item)">
              <wd-icon name="eye" size="26rpx" color="#3d4558" />
              <text>详情</text>
            </view>
          </view>
        </view>
        <view class="h-20rpx" />
      </view>
    </z-paging>

    <DetailPopup ref="detailPopupRef" @refresh="reload" @edit="handleEdit" />
    <EditPopup ref="editPopupRef" @success="reload" />
  </view>
</template>

<script lang="ts" setup>
import type { AlgorithmTask } from '@/api/video/algorithm'
import { ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import {
  getAlgorithmTaskTypeText,
  listAlgorithmTasks,
  startAlgorithmTask,
  stopAlgorithmTask,
} from '@/api/video/algorithm'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { getTaskTypeTagType } from '@/utils/video/alertDisplay'
import { parseListResponse } from '@/utils/listResponse'
import DetailPopup from './components/detail-popup.vue'
import EditPopup from './components/edit-popup.vue'
import SearchForm from './components/search-form.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const list = ref<AlgorithmTask[]>([])
const pagingRef = ref<any>()
const queryParams = ref<Record<string, any>>({})
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>()
const editPopupRef = ref<InstanceType<typeof EditPopup>>()

async function queryList(pageNo: number, pageSize: number) {
  try {
    const res = await listAlgorithmTasks({ ...queryParams.value, pageNo, pageSize })
    const { list: data, total } = parseListResponse<AlgorithmTask>(res, ['data'])
    pagingRef.value?.completeByTotal(data, total)
  } catch {
    pagingRef.value?.complete(false)
  }
}

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

function handleEdit(item: AlgorithmTask) {
  editPopupRef.value?.openEdit(item)
}

function handleDetail(item: AlgorithmTask) {
  detailPopupRef.value?.open(item)
}

async function handleQuickStart(item: AlgorithmTask) {
  try {
    await startAlgorithmTask(item.id)
    toast.success('任务已启动')
    item.is_enabled = true
  } catch {
    toast.error('启动失败')
  }
}

async function handleQuickStop(item: AlgorithmTask) {
  try {
    await stopAlgorithmTask(item.id)
    toast.success('任务已停止')
    item.is_enabled = false
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
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 60%, #722ed1 100%);
  box-shadow: 0 10rpx 20rpx rgba(114, 46, 209, 0.26);
  flex-shrink: 0;
}

.run-pill {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 600;
  flex-shrink: 0;

  &--on {
    color: #0fa36e;
    background: #e6f7f1;

    .run-pill-dot {
      background: #12b77c;
      box-shadow: 0 0 0 5rpx rgba(18, 183, 124, 0.16);
    }
  }

  &--off {
    color: #8a94a6;
    background: #eef0f4;

    .run-pill-dot {
      background: #c0c7d3;
    }
  }

  .run-pill-dot {
    width: 11rpx;
    height: 11rpx;
    border-radius: 50%;
  }
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.meta-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #2f6bff;
  background: #eaf1ff;

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

  &--info,
  &--primary {
    color: #2f6bff;
    background: #eaf1ff;
  }
}

.stat-row {
  display: flex;
  align-items: stretch;
  margin-top: 20rpx;
  padding: 18rpx 0;
  border-radius: 16rpx;
  background: #f7f9fd;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  flex: 1;
}

.stat-num {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.stat-label {
  font-size: 21rpx;
  color: var(--app-text-3, #98a2b3);
}

.stat-divider {
  width: 1rpx;
  margin: 6rpx 0;
  background: var(--app-separator);
}

.action-row {
  display: flex;
  gap: 16rpx;
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

  &--primary {
    flex: 1;
    color: #ffffff;
    background: linear-gradient(135deg, #a78bfa, #7c3aed);
    box-shadow: 0 8rpx 20rpx rgba(124, 58, 237, 0.26);
  }

  &--warning {
    flex: 1;
    color: #c2410c;
    background: #fff3e8;
  }

  &--ghost {
    flex: 1;
    color: var(--app-text-2, #3d4558);
    background: #f4f6fb;
  }
}
</style>
