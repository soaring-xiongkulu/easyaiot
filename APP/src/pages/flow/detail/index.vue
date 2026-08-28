<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="审批详情" placeholder safe-area-inset-top fixed left-arrow @click-left="handleBack" />

    <scroll-view scroll-y class="min-h-0 flex-1">
      <view v-if="detail" class="p-24rpx pb-200rpx">
        <!-- 实例信息 -->
        <view class="section-card">
          <view class="mb-16rpx flex items-start justify-between gap-12rpx">
            <view class="flex-1 text-31rpx text-[#10131a] font-semibold leading-snug">
              {{ detail.processInstance?.name || '流程实例' }}
            </view>
            <view class="status-pill" :class="`status-pill--${getFlowInstanceStatusType(detail.processInstance?.status)}`">
              {{ formatFlowInstanceStatus(detail.processInstance?.status) }}
            </view>
          </view>
          <view class="info-row">
            <text class="info-label">流程类型</text>
            <text class="info-value">{{ detail.processInstance?.processDefinitionName || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">发起人</text>
            <text class="info-value">{{ detail.processInstance?.startUserNickname || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">发起时间</text>
            <text class="info-value">{{ formatDateTime(detail.processInstance?.startTime) || '-' }}</text>
          </view>
          <view v-if="detail.processInstance?.endTime" class="info-row">
            <text class="info-label">结束时间</text>
            <text class="info-value">{{ formatDateTime(detail.processInstance.endTime) }}</text>
          </view>
          <view v-if="detail.processInstance?.durationInMillis" class="info-row">
            <text class="info-label">耗时</text>
            <text class="info-value">{{ formatFlowDuration(detail.processInstance.durationInMillis) }}</text>
          </view>
          <view v-if="detail.processInstance?.reason" class="info-row">
            <text class="info-label">审批意见</text>
            <text class="info-value">{{ detail.processInstance.reason }}</text>
          </view>
        </view>

        <!-- 告警信息（告警流程才有 businessKey=alert:{alertId}） -->
        <view v-if="alertRecord" class="section-card">
          <view class="mb-16rpx text-29rpx text-[#10131a] font-semibold">
            告警信息
          </view>
          <view class="info-row">
            <text class="info-label">告警编号</text>
            <text class="info-value">#{{ alertRecord.alertId ?? '-' }}</text>
          </view>
          <view v-if="alertVars.alertEvent" class="info-row">
            <text class="info-label">告警事件</text>
            <text class="info-value">{{ alertVars.alertEvent }}</text>
          </view>
          <view v-if="alertVars.alertObject" class="info-row">
            <text class="info-label">告警对象</text>
            <text class="info-value">{{ alertVars.alertObject }}</text>
          </view>
          <view v-if="alertVars.taskName" class="info-row">
            <text class="info-label">算法任务</text>
            <text class="info-value">{{ alertVars.taskName }}</text>
          </view>
          <view v-if="alertVars.deviceName" class="info-row">
            <text class="info-label">设备</text>
            <text class="info-value">{{ alertVars.deviceName }}</text>
          </view>
          <view v-if="alertVars.alertTime" class="info-row">
            <text class="info-label">告警时间</text>
            <text class="info-value">{{ alertVars.alertTime }}</text>
          </view>
          <view v-if="alertVars.imageUrl" class="mt-12rpx overflow-hidden rounded-16rpx">
            <wd-img
              :src="alertVars.imageUrl"
              width="100%"
              height="320rpx"
              mode="aspectFill"
              enable-preview
            />
          </view>
          <view v-if="alertRecord.currentTaskName" class="info-row">
            <text class="info-label">当前节点</text>
            <text class="info-value">{{ alertRecord.currentTaskName }}</text>
          </view>
          <view v-if="alertRecord.currentAssignees" class="info-row">
            <text class="info-label">当前责任人</text>
            <text class="info-value">{{ alertRecord.currentAssignees }}</text>
          </view>
        </view>

        <!-- 审批进度 -->
        <view class="section-card">
          <view class="mb-16rpx text-29rpx text-[#10131a] font-semibold">
            审批进度
          </view>
          <view v-for="node in (detail.activityNodes || [])" :key="node.id" class="node-block">
            <view class="node-head">
              <view class="node-dot" />
              <text class="text-26rpx text-[#3d4558] font-semibold">{{ node.name || '节点' }}</text>
            </view>
            <view v-for="task in (node.tasks || [])" :key="task.id" class="node-task">
              <view class="mb-6rpx flex items-center justify-between gap-12rpx">
                <text class="min-w-0 flex-1 truncate text-25rpx text-[#10131a]">
                  {{ task.assigneeUser?.nickname || '待认领' }}
                </text>
                <view class="status-pill" :class="`status-pill--${getFlowTaskStatusType(task.status)}`">
                  {{ formatFlowTaskStatus(task.status) }}
                </view>
              </view>
              <view v-if="task.reason" class="mb-6rpx text-23rpx text-[#6b7688]">
                意见：{{ task.reason }}
              </view>
              <text class="text-21rpx text-[#98a2b3]">
                {{ formatDateTime(task.createTime) }}
                <template v-if="task.endTime">
                  ~ {{ formatDateTime(task.endTime) }}
                </template>
              </text>
            </view>
            <view v-if="!(node.tasks && node.tasks.length)" class="text-23rpx text-[#98a2b3]">
              暂无审批记录
            </view>
          </view>
        </view>
      </view>

      <view v-else-if="loadFailed" class="pt-200rpx text-center text-26rpx text-[#98a2b3]">
        加载失败，请下拉重试或返回
      </view>
    </scroll-view>

    <!-- 底部操作条（目标任务待审批时展示） -->
    <view v-if="canOperate" class="action-bar">
      <view class="action-btn action-btn--reject" @click="openAction('reject')">
        拒绝
      </view>
      <view class="action-btn action-btn--approve" @click="openAction('approve')">
        通过
      </view>
    </view>

    <!-- 审批意见弹窗 -->
    <wd-popup v-model="actionVisible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0" safe-area-inset-bottom @close="actionVisible = false">
      <view class="p-32rpx pb-48rpx">
        <view class="mb-24rpx text-32rpx font-semibold" style="color: var(--app-text-1, #10131a)">
          {{ actionType === 'approve' ? '通过审批' : '拒绝审批' }}
        </view>
        <wd-textarea
          v-model="actionReason"
          :placeholder="actionType === 'approve' ? '审批意见（可选）' : '请填写拒绝原因（必填）'"
          :maxlength="200"
          show-word-limit
        />
        <view class="mt-32rpx flex gap-20rpx">
          <wd-button block plain @click="actionVisible = false">
            取消
          </wd-button>
          <wd-button block type="primary" :loading="actionSubmitting" @click="submitAction">
            确定
          </wd-button>
        </view>
      </view>
    </wd-popup>
  </view>
</template>

<script lang="ts" setup>
import type { FlowAlertRecordVO, FlowApprovalDetail } from '@/api/flow'
import { onLoad } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import {
  approveFlowTask,
  formatFlowDuration,
  formatFlowInstanceStatus,
  formatFlowTaskStatus,
  getFlowAlertRecordPage,
  getFlowApprovalDetail,
  getFlowInstanceStatusType,
  getFlowTaskStatusType,
  rejectFlowTask,
} from '@/api/flow'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { formatDateTime } from '@/utils/date'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()

const instanceId = ref('')
const taskId = ref('')
const detail = ref<FlowApprovalDetail>()
const alertRecord = ref<FlowAlertRecordVO>()
const loadFailed = ref(false)

const snapshot = computed<Record<string, any>>(() => (alertRecord.value?.alertSnapshot || {}) as Record<string, any>)

/** 告警展示字段：优先流程变量（真实 Kafka 快照映射的 camelCase），兼容早期蛇形命名的快照 */
const alertVars = computed<Record<string, any>>(() => {
  const vars = (detail.value?.processInstance?.processVariables || {}) as Record<string, any>
  const snap = snapshot.value
  const alert = (snap.alert || {}) as Record<string, any>
  return {
    taskName: vars.taskName ?? snap.taskName ?? snap.task_name,
    deviceName: vars.deviceName ?? snap.deviceName ?? snap.device_name,
    alertTime: vars.alertTime ?? alert.time ?? snap.time ?? snap.timestamp,
    alertEvent: vars.alertEvent ?? alert.event ?? snap.event,
    alertObject: vars.alertObject ?? alert.object ?? snap.object,
    imageUrl: vars.imageUrl ?? alert.imagePath ?? snap.imagePath,
  }
})

/** 操作条仅在目标任务仍待审批时展示（站内信 deepLink 可能指向已完成任务） */
const canOperate = computed(() => {
  if (!taskId.value) return false
  const target = (detail.value?.activityNodes || [])
    .flatMap(node => node.tasks || [])
    .find(task => task.id === taskId.value)
  return target != null && [0, 1, 7].includes(target.status ?? -99)
})

onLoad((query) => {
  instanceId.value = String(query?.id || '')
  taskId.value = String(query?.taskId || '')
  loadDetail()
})

async function loadDetail() {
  loadFailed.value = false
  try {
    detail.value = await getFlowApprovalDetail(instanceId.value, taskId.value || undefined) as FlowApprovalDetail
    loadAlertRecord()
  }
  catch {
    loadFailed.value = true
  }
}

/** businessKey 约定为 alert:{alertId}，按告警 ID 拉处理记录展示告警信息卡 */
async function loadAlertRecord() {
  try {
    const businessKey = detail.value?.processInstance?.businessKey || ''
    const match = businessKey.match(/^alert:(\d+)$/)
    if (!match) return
    const res = await getFlowAlertRecordPage({ pageNo: 1, pageSize: 1, alertId: Number(match[1]) })
    const records = (res as any)?.list || []
    if (records.length) alertRecord.value = records[0]
  }
  catch {
    // 告警信息卡为增强展示，失败不阻塞详情
  }
}

function handleBack() {
  uni.navigateBack()
}

// ==================== 审批操作 ====================

const actionVisible = ref(false)
const actionType = ref<'approve' | 'reject'>('approve')
const actionReason = ref('')
const actionSubmitting = ref(false)

function openAction(type: 'approve' | 'reject') {
  actionType.value = type
  actionReason.value = ''
  actionVisible.value = true
}

async function submitAction() {
  if (actionType.value === 'reject' && !actionReason.value.trim()) {
    toast.show('请填写拒绝原因')
    return
  }
  actionSubmitting.value = true
  try {
    if (actionType.value === 'approve') {
      await approveFlowTask({ id: taskId.value, reason: actionReason.value.trim() || undefined })
      toast.success('已通过')
    }
    else {
      await rejectFlowTask({ id: taskId.value, reason: actionReason.value.trim() })
      toast.success('已拒绝')
    }
    actionVisible.value = false
    uni.$emit('flow:refresh')
    setTimeout(() => uni.navigateBack(), 600)
  }
  catch {
    toast.error('操作失败')
  }
  finally {
    actionSubmitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.section-card {
  margin-bottom: 22rpx;
  padding: 28rpx 24rpx;
  background: #ffffff;
  border-radius: 26rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
}

.info-row {
  display: flex;
  padding: 8rpx 0;
  font-size: 25rpx;

  .info-label {
    width: 150rpx;
    flex-shrink: 0;
    color: #98a2b3;
  }

  .info-value {
    flex: 1;
    min-width: 0;
    word-break: break-all;
    color: #3d4558;
  }
}

.node-block {
  padding: 16rpx 0;

  & + .node-block {
    border-top: 1rpx solid #f0f2f6;
  }
}

.node-head {
  display: flex;
  gap: 14rpx;
  align-items: center;
  margin-bottom: 12rpx;
}

.node-dot {
  width: 14rpx;
  height: 14rpx;
  flex-shrink: 0;
  border-radius: 50%;
  background: #2f6bff;
}

.node-task {
  padding: 14rpx 16rpx;
  margin-left: 8rpx;
  background: #f8f9fc;
  border-radius: 16rpx;

  & + .node-task {
    margin-top: 12rpx;
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

.action-bar {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 10;
  display: flex;
  gap: 20rpx;
  padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  box-shadow: 0 -4rpx 20rpx rgba(23, 43, 77, 0.06);
}

.action-btn {
  flex: 1;
  padding: 20rpx 0;
  font-size: 29rpx;
  font-weight: 600;
  text-align: center;
  border-radius: 999rpx;

  &--approve {
    color: #ffffff;
    background: linear-gradient(135deg, #4f8bff, #2f6bff);
  }

  &--reject {
    color: #e5484d;
    background: #fef2f2;
    border: 1rpx solid #fecaca;
  }
}
</style>
