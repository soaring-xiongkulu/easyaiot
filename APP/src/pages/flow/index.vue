<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="流程审批" placeholder safe-area-inset-top fixed>
      <template #right>
        <AppNavUserButton />
      </template>
    </wd-navbar>

    <wd-tabs v-model="activeTab" @change="handleTabChange">
      <wd-tab title="待办" name="todo" />
      <wd-tab title="已办" name="done" />
      <wd-tab title="处理记录" name="record" />
      <wd-tab title="抄送" name="copy" />
    </wd-tabs>

    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      empty-view-text="暂无数据"
      @query="queryList"
    >
      <view class="p-24rpx">
        <template v-if="activeTab === 'copy'">
          <view
            v-for="item in list"
            :key="`copy-${item.id}`"
            class="flow-card"
            hover-class="flow-card--pressed"
            :hover-stay-time="60"
            @click="handleCopyDetail(item)"
          >
            <view class="flow-card-accent accent--primary" />
            <view class="min-w-0 flex-1 py-24rpx pl-24rpx pr-24rpx">
              <view class="mb-10rpx flex items-start justify-between gap-12rpx">
                <view class="line-clamp-2 flex-1 text-29rpx text-[#10131a] font-semibold leading-snug">
                  {{ item.processInstanceName || '流程抄送' }}
                </view>
                <view class="status-pill status-pill--primary">
                  抄送
                </view>
              </view>
              <view class="mb-6rpx truncate text-25rpx text-[#3d4558]">
                {{ item.taskName ? `抄送节点：${item.taskName}` : '-' }}
              </view>
              <view class="mb-12rpx truncate text-23rpx text-[#98a2b3]">
                {{ item.reason ? `审批意见：${item.reason}` : '抄送备注：-' }}
              </view>
              <view class="flex items-center justify-between">
                <view class="meta-pill">
                  实例 #{{ item.processInstanceId?.slice(0, 8) }}
                </view>
                <text class="text-22rpx text-[#98a2b3]">
                  {{ formatDateTime(item.createTime) }}
                </text>
              </view>
            </view>
          </view>
        </template>

        <template v-else-if="activeTab !== 'record'">
          <view
            v-for="item in list"
            :key="item.id"
            class="flow-card"
            hover-class="flow-card--pressed"
            :hover-stay-time="60"
            @click="handleTaskDetail(item, activeTab === 'todo')"
          >
            <view class="flow-card-accent" :class="`accent--${getFlowTaskStatusType(item.status)}`" />
            <view class="min-w-0 flex-1 py-24rpx pl-24rpx pr-24rpx">
              <view class="mb-10rpx flex items-start justify-between gap-12rpx">
                <view class="line-clamp-2 flex-1 text-29rpx text-[#10131a] font-semibold leading-snug">
                  {{ item.processInstanceName || item.name || '流程任务' }}
                </view>
                <view class="status-pill" :class="`status-pill--${getFlowTaskStatusType(item.status)}`">
                  {{ formatFlowTaskStatus(item.status) }}
                </view>
              </view>
              <view class="mb-6rpx truncate text-25rpx text-[#3d4558]">
                {{ activeTab === 'todo' ? `当前节点：${item.name || '-'}` : (item.reason ? `审批意见：${item.reason}` : item.name || '-') }}
              </view>
              <view class="mb-12rpx truncate text-23rpx text-[#98a2b3]">
                发起人：{{ item.startUser?.nickname || '-' }}
              </view>
              <view class="flex items-center justify-between">
                <view class="meta-pill">
                  {{ item.processDefinitionName || item.processDefinitionKey || '流程' }}
                </view>
                <text class="text-22rpx text-[#98a2b3]">
                  {{ formatDateTime(activeTab === 'todo' ? item.createTime : (item.endTime || item.createTime)) }}
                </text>
              </view>
            </view>
          </view>
        </template>

        <template v-else>
          <view
            v-for="item in list"
            :key="String(item.id)"
            class="flow-card"
            hover-class="flow-card--pressed"
            :hover-stay-time="60"
            @click="handleRecordDetail(item)"
          >
            <view class="flow-card-accent" :class="`accent--${getFlowInstanceStatusType(item.processInstanceStatus)}`" />
            <view class="min-w-0 flex-1 py-24rpx pl-24rpx pr-24rpx">
              <view class="mb-10rpx flex items-start justify-between gap-12rpx">
                <view class="line-clamp-2 flex-1 text-29rpx text-[#10131a] font-semibold leading-snug">
                  {{ formatRecordTitle(item) }}
                </view>
                <view class="status-pill" :class="`status-pill--${getFlowInstanceStatusType(item.processInstanceStatus)}`">
                  {{ formatFlowInstanceStatus(item.processInstanceStatus) }}
                </view>
              </view>
              <view class="mb-6rpx truncate text-25rpx text-[#3d4558]">
                {{ formatRecordSubtitle(item) }}
              </view>
              <view class="mb-12rpx truncate text-23rpx text-[#98a2b3]">
                {{ formatRecordEvent(item) }} · 告警来源：{{ formatAlertSource(item.alertSource) }}
              </view>
              <view class="flex items-center justify-between">
                <view class="meta-pill">
                  告警 #{{ item.alertId ?? '-' }}
                </view>
                <text class="text-22rpx text-[#98a2b3]">
                  {{ formatDateTime(item.finishTime || item.createTime) }}
                </text>
              </view>
            </view>
          </view>
        </template>
      </view>
    </z-paging>
  </view>
</template>

<script lang="ts" setup>
import type { FlowAlertRecordVO, FlowCopyVO, FlowTaskVO } from '@/api/flow'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { ref } from 'vue'
import {
  formatFlowInstanceStatus,
  formatFlowTaskStatus,
  getFlowCopyPage,
  getFlowDonePage,
  getFlowInstanceStatusType,
  getFlowTaskStatusType,
  getMyFlowAlertRecordPage,
  getFlowTodoPage,
} from '@/api/flow'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { formatDateTime } from '@/utils/date'
import { parseListResponse } from '@/utils/listResponse'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

type TabName = 'todo' | 'done' | 'record' | 'copy'

const activeTab = ref<TabName>('todo')
const list = ref<any[]>([]) // 三类 tab 复用一个 z-paging 列表
const pagingRef = ref<any>()
let firstLoadDone = false
let needRefreshOnShow = false

async function queryList(pageNo: number, pageSize: number) {
  try {
    const params = { pageNo, pageSize }
    if (activeTab.value === 'todo') {
      const res = await getFlowTodoPage(params)
      const { list: data, total } = parseListResponse<FlowTaskVO>(res)
      pagingRef.value?.completeByTotal(data, total)
    }
    else if (activeTab.value === 'done') {
      const res = await getFlowDonePage(params)
      const { list: data, total } = parseListResponse<FlowTaskVO>(res)
      pagingRef.value?.completeByTotal(data, total)
    }
    else if (activeTab.value === 'copy') {
      const res = await getFlowCopyPage(params)
      const { list: data, total } = parseListResponse<FlowCopyVO>(res)
      pagingRef.value?.completeByTotal(data, total)
    }
    else {
      const res = await getMyFlowAlertRecordPage(params)
      const { list: data, total } = parseListResponse<FlowAlertRecordVO>(res)
      pagingRef.value?.completeByTotal(data, total)
    }
    firstLoadDone = true
  }
  catch {
    pagingRef.value?.complete(false)
  }
}

function handleTabChange({ name }: { name: TabName }) {
  activeTab.value = name
  pagingRef.value?.reload()
}

// 详情页审批完成后 uni.$emit('flow:refresh')，返回本页时刷新列表
function markNeedRefresh() {
  needRefreshOnShow = true
}
onLoad(() => {
  uni.$on('flow:refresh', markNeedRefresh)
})
onUnload(() => {
  uni.$off('flow:refresh', markNeedRefresh)
})
onShow(() => {
  if (firstLoadDone && needRefreshOnShow) {
    needRefreshOnShow = false
    pagingRef.value?.reload()
  }
})

function handleTaskDetail(item: FlowTaskVO, withTask: boolean) {
  const url = `/pages/flow/detail/index?id=${item.processInstanceId}${withTask ? `&taskId=${item.id}` : ''}`
  uni.navigateTo({ url })
}

function handleRecordDetail(item: FlowAlertRecordVO) {
  if (!item.processInstanceId) {
    uni.showToast({ title: '该记录无关联流程', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/flow/detail/index?id=${item.processInstanceId}` })
}

function handleCopyDetail(item: FlowCopyVO) {
  if (!item.processInstanceId) {
    uni.showToast({ title: '该抄送无关联流程', icon: 'none' })
    return
  }
  const url = `/pages/flow/detail/index?id=${item.processInstanceId}${item.taskId ? `&taskId=${item.taskId}` : ''}`
  uni.navigateTo({ url })
}

function formatRecordTitle(item: FlowAlertRecordVO): string {
  const snapshot = (item.alertSnapshot || {}) as Record<string, any>
  return snapshot.taskName || snapshot.task_name || snapshot.deviceName || snapshot.device_name
    || (item.alertId != null ? `告警处理 #${item.alertId}` : '告警处理')
}

function formatAlertSource(source?: string): string {
  switch ((source || '').toLowerCase()) {
    case 'video_task': return '视频任务'
    case 'manual': return '手动触发'
    default: return source || '-'
  }
}

/** 记录副标题：优先当前节点，否则展示告警事件 */
function formatRecordSubtitle(item: FlowAlertRecordVO): string {
  if (item.currentTaskName)
    return `当前节点：${item.currentTaskName}`
  return `责任人：${item.currentAssignees || '-'}`
}

/** 告警事件：真实 Kafka 快照（嵌套 alert.event）与早期蛇形快照均兼容 */
function formatRecordEvent(item: FlowAlertRecordVO): string {
  const snapshot = (item.alertSnapshot || {}) as Record<string, any>
  const event = snapshot.event || (snapshot.alert || {}).event
  return event ? `事件 ${event}` : '事件 -'
}
</script>

<style lang="scss" scoped>
.flow-card {
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

.flow-card-accent {
  width: 8rpx;
  flex-shrink: 0;
  background: #98a2b3;

  &--success {
    background: linear-gradient(180deg, #6fe3b1, #12b77c);
  }

  &--error {
    background: linear-gradient(180deg, #ff7d84, #e5484d);
  }

  &--warning {
    background: linear-gradient(180deg, #ffd08a, #f59e0b);
  }

  &--primary {
    background: linear-gradient(180deg, #7fa9ff, #2f6bff);
  }

  &--info {
    background: linear-gradient(180deg, #c6cdd8, #98a2b3);
  }
}

.status-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  flex-shrink: 0;
  background: #eef0f4;
  color: #6b7688;

  &--success {
    color: #0fa36e;
    background: #e6f7f1;
  }

  &--error {
    color: #e5484d;
    background: #fef2f2;
  }

  &--warning {
    color: #d97706;
    background: #fdf3e2;
  }

  &--primary {
    color: #2f6bff;
    background: #eaf1ff;
  }

  &--info {
    color: #6b7688;
    background: #eef0f4;
  }
}

.meta-pill {
  padding: 4rpx 14rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
  color: #6b7688;
  background: #f4f6fb;
}
</style>
