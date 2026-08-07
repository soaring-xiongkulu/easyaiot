<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="算法任务" placeholder safe-area-inset-top fixed>
      <template #right>
        <view class="flex items-center gap-16rpx pr-16rpx">
          <view class="text-28rpx text-[#1890ff]" @click="handleCreate">
            新建
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
          class="mb-24rpx overflow-hidden rounded-12rpx bg-white shadow-sm"
          @click="handleDetail(item)"
        >
          <view class="p-24rpx">
            <view class="mb-16rpx flex items-start justify-between gap-16rpx">
              <view class="min-w-0 flex-1">
                <view class="truncate text-32rpx font-semibold text-[#333]">
                  {{ item.task_name }}
                </view>
                <view class="mt-8rpx text-26rpx text-[#999]">
                  {{ item.device_names?.join('、') || `${item.device_ids?.length || 0} 个设备` }}
                </view>
              </view>
              <wd-tag :type="item.is_enabled ? 'success' : 'default'" plain>
                {{ item.is_enabled ? '运行中' : '已停止' }}
              </wd-tag>
            </view>

            <view class="flex flex-wrap gap-12rpx">
              <wd-tag :type="getTaskTypeTagType(item.task_type)" plain>
                {{ getAlgorithmTaskTypeText(item.task_type, item.executor) }}
              </wd-tag>
              <wd-tag v-if="item.alert_event_enabled" type="warning" plain>
                告警
              </wd-tag>
            </view>

            <view class="mt-16rpx flex justify-between text-26rpx text-[#666]">
              <text>检测 {{ item.total_detections ?? 0 }}</text>
              <text v-if="item.task_type === 'snap'">抓拍 {{ item.total_captures ?? 0 }}</text>
              <text v-else>帧数 {{ item.total_frames ?? 0 }}</text>
            </view>

            <view class="mt-16rpx flex gap-16rpx" @click.stop>
              <wd-button
                v-if="!item.is_enabled"
                size="small"
                type="primary"
                @click="handleQuickStart(item)"
              >
                启动
              </wd-button>
              <wd-button
                v-else
                size="small"
                type="warning"
                @click="handleQuickStop(item)"
              >
                停止
              </wd-button>
            </view>
          </view>
        </view>
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
  }
  catch {
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
  }
  catch {
    toast.error('启动失败')
  }
}

async function handleQuickStop(item: AlgorithmTask) {
  try {
    await stopAlgorithmTask(item.id)
    toast.success('任务已停止')
    item.is_enabled = false
  }
  catch {
    toast.error('停止失败')
  }
}
</script>
