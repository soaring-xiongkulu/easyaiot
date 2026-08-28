<script lang="ts" setup>
/**
 * 审批详情页（隐藏路由 /flow/process-instance/detail?id=&taskId=）
 * 同一页面复用：待办审批（带 taskId 可操作）/ 我的流程查看 / 抄送查看。
 * 布局：实例头卡 + 告警信息卡（告警流程）+ 审批时间线 + 流程图（Simple 查看器染色）+ 操作按钮。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Button, Card, Descriptions, DescriptionsItem, Empty, Modal, Select, Space, Spin, Tag, Textarea, Timeline, TimelineItem } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import { useMessage } from '@/hooks/web/useMessage'
import { FlowViewer } from '../components/simple-process-design'
import type { SimpleFlowNode } from '../components/simple-process-design'
import { cloneNode } from '../components/simple-process-design'
import {
  approveTask,
  copyTask,
  delegateTask,
  getTaskListByReturn,
  rejectTask,
  returnTask,
  transferTask,
} from '@/api/flow/task'
import { getApprovalDetail, getProcessInstanceBpmnModelView, type FlowProcessInstanceVO } from '@/api/flow/processInstance'
import { useCandidateOptions } from '../components/simple-process-design/useCandidateOptions'
import UserSelectModal from '../components/simple-process-design/modules/UserSelectModal.vue'

defineOptions({ name: 'FlowProcessInstanceDetail' })

const route = useRoute()
const router = useRouter()
const { createMessage } = useMessage()
useCandidateOptions()

const instanceId = route.query.id as string
const taskId = (route.query.taskId as string) || ''

const loading = ref(true)
const instance = ref<FlowProcessInstanceVO>()
const activityNodes = ref<any[]>([])
const viewerNode = ref<SimpleFlowNode>()
const canOperate = ref(false)

const INSTANCE_STATUS: Record<number, { text: string; color: string }> = {
  1: { text: '审批中', color: 'processing' },
  2: { text: '已通过', color: 'success' },
  3: { text: '已拒绝', color: 'error' },
  4: { text: '已取消', color: 'default' },
}

const NODE_TYPE_NAME: Record<number, string> = {
  1: '结束',
  10: '发起人',
  11: '审批',
  12: '抄送',
  14: '延迟',
  50: '条件',
  51: '条件分支',
  52: '并行分支',
}

const TASK_STATUS: Record<number, { text: string; color: string }> = {
  0: { text: '待审批', color: 'orange' },
  1: { text: '审批中', color: 'processing' },
  2: { text: '通过', color: 'success' },
  3: { text: '拒绝', color: 'error' },
  4: { text: '已取消', color: 'default' },
  5: { text: '已退回', color: 'warning' },
  7: { text: '审批中', color: 'processing' },
}

/** 节点时间线的图标颜色（按节点内任务状态推导） */
function nodeTimelineColor(node: any): string {
  const statuses = (node.tasks ?? []).map((task: any) => task.status)
  if (statuses.includes(3)) {
    return 'red'
  }
  if (statuses.length && statuses.every((status: number) => status === 2)) {
    return 'green'
  }
  if (statuses.includes(0) || statuses.includes(1) || statuses.includes(7)) {
    return 'blue'
  }
  return 'gray'
}

/** 告警流程变量（告警自动发起时后端注入） */
const alarmVars = computed(() => {
  const vars = instance.value?.processVariables
  if (!vars?.alertId) {
    return null
  }
  return {
    alertId: vars.alertId,
    alertEvent: vars.alertEvent,
    alertObject: vars.alertObject,
    taskName: vars.taskName,
    deviceId: vars.deviceId,
    deviceName: vars.deviceName,
    imageUrl: vars.imageUrl,
    alertTime: vars.alertTime,
  }
})

const displayVars = computed(() => {
  const vars = instance.value?.processVariables ?? {}
  const exclude = new Set(['PROCESS_STATUS', 'PROCESS_REASON', 'PROCESS_START_USER_ID', '_FLOWABLE_SKIP_EXPRESSION_ENABLED'])
  return Object.entries(vars)
    .filter(([key]) => !exclude.has(key) && !key.startsWith('alert') && key !== 'imageUrl' && key !== 'recordPath')
    .map(([key, value]) => ({ key, value: typeof value === 'object' ? JSON.stringify(value) : String(value) }))
})

async function loadData() {
  loading.value = true
  try {
    const detail = await getApprovalDetail({ id: instanceId, taskId: taskId || undefined })
    instance.value = detail?.processInstance
    activityNodes.value = detail?.activityNodes ?? []
    canOperate.value = !!taskId && instance.value?.status === 1

    const modelView = await getProcessInstanceBpmnModelView(instanceId).catch(() => null)
    if (modelView?.simpleModel) {
      const tree = cloneNode(modelView.simpleModel)
      markNodeStatus(tree, new Set(modelView.finishedTaskActivityIds ?? []), 2)
      markNodeStatus(tree, new Set(modelView.rejectedTaskActivityIds ?? []), 3)
      markNodeStatus(tree, new Set(modelView.unfinishedTaskActivityIds ?? []), 1)
      viewerNode.value = tree
    }
    else {
      viewerNode.value = undefined
    }
  }
  finally {
    loading.value = false
  }
}

/** 递归把运行状态写入节点（查看器染色） */
function markNodeStatus(node: SimpleFlowNode | undefined, ids: Set<string>, status: number) {
  if (!node) {
    return
  }
  if (ids.has(node.id)) {
    node.activityStatus = status
  }
  node.conditionNodes?.forEach(branch => markNodeStatus(branch, ids, status))
  markNodeStatus(node.childNode, ids, status)
}

// ==================== 审批操作 ====================
type ActionType = 'approve' | 'reject' | 'return' | 'transfer' | 'delegate' | 'copy' | ''

const actionModalOpen = ref(false)
const actionType = ref<ActionType>('')
const actionReason = ref('')
const actionSubmitting = ref(false)
const returnNodeOptions = ref<{ label: string; value: string }[]>([])
const returnTarget = ref<string>()
const targetUserIds = ref<number[]>([])
const userSelectOpen = ref(false)

const ACTION_TITLES: Record<string, string> = {
  approve: '通过审批',
  reject: '拒绝审批',
  return: '退回',
  transfer: '转办',
  delegate: '委派',
  copy: '抄送',
}

function openAction(type: ActionType) {
  actionType.value = type
  actionReason.value = ''
  returnTarget.value = undefined
  targetUserIds.value = []
  if (type === 'return') {
    loadReturnNodes()
  }
  actionModalOpen.value = true
}

async function loadReturnNodes() {
  const list = await getTaskListByReturn(taskId).catch(() => [])
  returnNodeOptions.value = (list ?? []).map((item: any) => ({ label: item.name, value: item.taskDefinitionKey ?? item.id }))
}

async function submitAction() {
  if ((actionType.value === 'return' || actionType.value === 'reject') && !actionReason.value) {
    createMessage.warning('请填写审批意见')
    return
  }
  if (actionType.value === 'return' && !returnTarget.value) {
    createMessage.warning('请选择退回目标节点')
    return
  }
  if ((actionType.value === 'transfer' || actionType.value === 'delegate' || actionType.value === 'copy') && !targetUserIds.value.length) {
    createMessage.warning('请选择目标成员')
    return
  }
  actionSubmitting.value = true
  try {
    switch (actionType.value) {
      case 'approve':
        await approveTask({ id: taskId, reason: actionReason.value })
        break
      case 'reject':
        await rejectTask({ id: taskId, reason: actionReason.value })
        break
      case 'return':
        await returnTask({ id: taskId, targetTaskDefinitionKey: returnTarget.value!, reason: actionReason.value })
        break
      case 'transfer':
        await transferTask({ id: taskId, assigneeUserId: targetUserIds.value[0], reason: actionReason.value })
        break
      case 'delegate':
        await delegateTask({ id: taskId, assigneeUserId: targetUserIds.value[0], reason: actionReason.value })
        break
      case 'copy':
        await copyTask({ id: taskId, userIds: targetUserIds.value, reason: actionReason.value })
        break
    }
    actionModalOpen.value = false
    createMessage.success(`${ACTION_TITLES[actionType.value]}成功`)
    await loadData()
  }
  finally {
    actionSubmitting.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="flow-detail">
    <div class="flow-detail__bar">
      <Button type="text" @click="router.back()">
        <template #icon>
          <Icon icon="ant-design:arrow-left-outlined" />
        </template>
        返回
      </Button>
      <Space v-if="canOperate" class="flow-detail__actions">
        <Button type="primary" @click="openAction('approve')">
          <template #icon><Icon icon="ant-design:check-outlined" /></template>
          通过
        </Button>
        <Button danger @click="openAction('reject')">
          <template #icon><Icon icon="ant-design:close-outlined" /></template>
          拒绝
        </Button>
        <Button @click="openAction('return')">退回</Button>
        <Button @click="openAction('transfer')">转办</Button>
        <Button @click="openAction('delegate')">委派</Button>
        <Button @click="openAction('copy')">抄送</Button>
      </Space>
    </div>

    <Spin :spinning="loading">
      <div class="flow-detail__body">
        <div class="flow-detail__main">
          <!-- 实例头卡 -->
          <Card class="flow-detail__card">
            <div class="flow-detail__title">
              <span class="flow-detail__name">{{ instance?.name || '流程详情' }}</span>
              <Tag :color="INSTANCE_STATUS[instance?.status ?? 0]?.color">
                {{ INSTANCE_STATUS[instance?.status ?? 0]?.text ?? '未知' }}
              </Tag>
            </div>
            <Descriptions size="small" :column="3" style="margin-top: 12px">
              <DescriptionsItem label="发起人">{{ instance?.startUserNickname || '系统发起' }}</DescriptionsItem>
              <DescriptionsItem label="发起时间">{{ instance?.startTime || '—' }}</DescriptionsItem>
              <DescriptionsItem label="结束时间">{{ instance?.endTime || '—' }}</DescriptionsItem>
              <DescriptionsItem v-if="instance?.reason" label="原因" :span="3">{{ instance.reason }}</DescriptionsItem>
            </Descriptions>
          </Card>

          <!-- 告警信息卡（告警流程专属） -->
          <Card v-if="alarmVars" title="告警信息" class="flow-detail__card">
            <template #title>
              <div class="flow-detail__card-title">
                <Icon icon="ant-design:alert-outlined" style="color: #ff943e" />
                <span>告警信息</span>
                <Tag color="orange" style="margin-left: 8px">告警 #{{ alarmVars.alertId }}</Tag>
              </div>
            </template>
            <div class="flow-detail__alarm">
              <div v-if="alarmVars.imageUrl" class="flow-detail__alarm-img">
                <img :src="alarmVars.imageUrl" alt="告警快照" @error="($event.target as HTMLImageElement).style.display = 'none'">
              </div>
              <Descriptions size="small" :column="2" style="flex: 1">
                <DescriptionsItem label="告警事件">{{ alarmVars.alertEvent || '—' }}</DescriptionsItem>
                <DescriptionsItem label="告警对象">{{ alarmVars.alertObject || '—' }}</DescriptionsItem>
                <DescriptionsItem label="算法任务">{{ alarmVars.taskName || '—' }}</DescriptionsItem>
                <DescriptionsItem label="告警时间">{{ alarmVars.alertTime || '—' }}</DescriptionsItem>
                <DescriptionsItem label="设备">{{ alarmVars.deviceName || '—' }}（{{ alarmVars.deviceId || '—' }}）</DescriptionsItem>
              </Descriptions>
            </div>
          </Card>

          <!-- 其他流程变量 -->
          <Card v-if="displayVars.length" title="流程表单" class="flow-detail__card">
            <Descriptions size="small" :column="2">
              <DescriptionsItem v-for="item in displayVars" :key="item.key" :label="item.key">
                {{ item.value }}
              </DescriptionsItem>
            </Descriptions>
          </Card>

          <!-- 审批时间线 -->
          <Card title="审批进度" class="flow-detail__card">
            <Empty v-if="!activityNodes.length" description="暂无审批记录" />
            <Timeline v-else style="margin-top: 4px">
              <TimelineItem v-for="node in activityNodes" :key="node.id" :color="nodeTimelineColor(node)">
                <div class="flow-detail__node">
                  <div class="flow-detail__node-head">
                    <span class="flow-detail__node-name">{{ node.name }}</span>
                    <span class="flow-detail__node-type">{{ NODE_TYPE_NAME[node.nodeType] || '' }}</span>
                  </div>
                  <div v-for="task in node.tasks ?? []" :key="task.id" class="flow-detail__task">
                    <Avatar :size="24" style="background-color: #0a7cff; flex-shrink: 0">
                      {{ (task.assigneeUser?.nickname || '?').slice(0, 1) }}
                    </Avatar>
                    <span class="flow-detail__task-user">{{ task.assigneeUser?.nickname || '系统' }}</span>
                    <Tag :color="TASK_STATUS[task.status]?.color ?? 'default'" style="margin: 0">
                      {{ TASK_STATUS[task.status]?.text ?? task.status }}
                    </Tag>
                    <span class="flow-detail__task-time">{{ task.endTime || task.createTime }}</span>
                    <div v-if="task.reason" class="flow-detail__task-reason">审批意见：{{ task.reason }}</div>
                  </div>
                </div>
              </TimelineItem>
            </Timeline>
          </Card>
        </div>

        <!-- 右侧流程图 -->
        <div class="flow-detail__side">
          <Card title="流程图" class="flow-detail__card">
            <template #title>
              <div class="flow-detail__legend">
                <span>流程图</span>
                <span class="flow-detail__legend-item"><i class="legend-dot legend-dot--done" />已通过</span>
                <span class="flow-detail__legend-item"><i class="legend-dot legend-dot--running" />进行中</span>
                <span class="flow-detail__legend-item"><i class="legend-dot legend-dot--reject" />已拒绝</span>
              </div>
            </template>
            <FlowViewer v-if="viewerNode" :flow-node="viewerNode" />
            <Empty v-else description="暂无流程图" />
          </Card>
        </div>
      </div>
    </Spin>

    <!-- 审批操作弹窗 -->
    <Modal
      v-model:open="actionModalOpen"
      :title="ACTION_TITLES[actionType]"
      :confirm-loading="actionSubmitting"
      ok-text="确定"
      cancel-text="取消"
      @ok="submitAction"
    >
      <div style="display: flex; flex-direction: column; gap: 12px; padding-top: 8px">
        <div v-if="actionType === 'return'">
          <div class="flow-detail__label">退回到节点</div>
          <Select v-model:value="returnTarget" :options="returnNodeOptions" placeholder="选择退回目标节点" style="width: 100%" />
        </div>
        <div v-if="['transfer', 'delegate', 'copy'].includes(actionType)">
          <div class="flow-detail__label">
            目标成员
            <Button type="link" size="small" @click="userSelectOpen = true">选择成员</Button>
          </div>
          <div class="flow-detail__picked">
            {{ targetUserIds.length ? `已选 ${targetUserIds.length} 人` : '未选择' }}
          </div>
          <UserSelectModal
            v-model:open="userSelectOpen"
            title="选择目标成员"
            :selected-ids="targetUserIds"
            @confirm="(ids: number[]) => (targetUserIds = ids)"
          />
        </div>
        <div v-if="['approve', 'reject', 'return', 'transfer', 'delegate', 'copy'].includes(actionType)">
          <div class="flow-detail__label">审批意见{{ actionType === 'reject' || actionType === 'return' ? '（必填）' : '（选填）' }}</div>
          <Textarea v-model:value="actionReason" :rows="3" placeholder="请输入审批意见" />
        </div>
      </div>
    </Modal>
  </div>
</template>

<style lang="less" scoped>
.flow-detail {
  &__bar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 8px;
    background: #fff;
    border-bottom: 1px solid #eef0f4;
  }

  &__body {
    display: flex;
    gap: 12px;
    padding: 12px;
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__side {
    width: 420px;
    flex-shrink: 0;

    @media (max-width: 1200px) {
      display: none;
    }
  }

  &__card {
    margin-bottom: 12px;
  }

  &__card-title {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  &__title {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  &__name {
    color: #1f2d3d;
    font-size: 16px;
    font-weight: 600;
  }

  &__alarm {
    display: flex;
    gap: 16px;
  }

  &__alarm-img {
    width: 180px;
    height: 120px;
    overflow: hidden;
    border-radius: 8px;
    background: #f5f7fa;
    flex-shrink: 0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  &__node-head {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  &__node-name {
    color: #1f2d3d;
    font-weight: 600;
  }

  &__node-type {
    color: #8c94a5;
    font-size: 12px;
  }

  &__task {
    position: relative;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-top: 8px;
    padding: 6px 8px;
    border-radius: 8px;
    background: #f7f9fc;
    width: fit-content;
  }

  &__task-user {
    color: #1f2d3d;
    font-size: 13px;
  }

  &__task-time {
    color: #8c94a5;
    font-size: 12px;
  }

  &__task-reason {
    width: 100%;
    color: #6b7a90;
    font-size: 12px;
  }

  &__legend {
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 13px;
    font-weight: 400;
  }

  &__legend-item {
    display: flex;
    gap: 4px;
    align-items: center;
    color: #8c94a5;
    font-size: 12px;
  }

  &__label {
    margin-bottom: 4px;
    color: #1f2d3d;
    font-size: 13px;
  }

  &__picked {
    color: #6b7a90;
    font-size: 12px;
  }
}

.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;

  &--done {
    background: #52c41a;
  }

  &--running {
    background: #0a7cff;
  }

  &--reject {
    background: #ff4d4f;
  }
}
</style>
