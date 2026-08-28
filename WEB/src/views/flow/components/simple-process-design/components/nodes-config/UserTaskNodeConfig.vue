<script lang="ts" setup>
/**
 * 审批人节点配置抽屉：审批人策略、多人审批方式、超时、拒绝、为空处理、审批意见
 */
import type { ComputedRef } from 'vue'
import { computed, inject, ref } from 'vue'
import { Button, Divider, Drawer, Form, FormItem, Input, InputNumber, RadioButton, RadioGroup, Select, Switch } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import {
  APPROVE_METHODS,
  APPROVE_TYPES,
  AssignEmptyHandlerType,
  ASSIGN_EMPTY_HANDLER_TYPES,
  ASSIGN_START_USER_HANDLER_TYPES,
  ApproveMethodType,
  ApproveType,
  CANDIDATE_STRATEGIES,
  NODE_VISUALS,
  NodeType,
  RejectHandlerType,
  REJECT_HANDLER_TYPES,
  TIME_UNIT_TYPES,
  TIMEOUT_HANDLER_TYPES,
  TimeoutHandlerType,
} from '../../consts'
import { buildTimeDuration, collectUserTaskNodes, parseTimeDuration } from '../../helpers'
import { useCandidateOptions } from '../../useCandidateOptions'
import CandidateParamForm from '../../modules/CandidateParamForm.vue'
import UserSelectModal from '../../modules/UserSelectModal.vue'

defineOptions({ name: 'FlowUserTaskNodeConfig' })

const props = defineProps<{ node: SimpleFlowNode }>()

const visible = ref(false)
const { users } = useCandidateOptions()

function open() {
  visible.value = true
}

defineExpose({ open })

const node = computed(() => props.node)
const visual = NODE_VISUALS[NodeType.USER_TASK_NODE]

/** 可驳回目标节点 = 流程树中的全部审批节点（排除自身），由 FlowDesigner provide 根节点 */
const rootNode = inject<ComputedRef<SimpleFlowNode | undefined>>('fpd-root')

const returnNodeOptions = computed(() =>
  collectUserTaskNodes(rootNode?.value)
    .filter(item => item.id !== node.value.id)
    .map(item => ({ label: item.name, value: item.id })),
)

const strategyOption = computed(() =>
  CANDIDATE_STRATEGIES.find(item => item.value === node.value.candidateStrategy),
)

const timeout = computed(() => {
  if (!node.value.timeoutHandler) {
    node.value.timeoutHandler = { enable: false }
  }
  return node.value.timeoutHandler
})

const parsedTimeout = computed(() => parseTimeDuration(timeout.value.timeDuration))
const timeoutValue = ref(parsedTimeout.value.value)
const timeoutUnit = ref(parsedTimeout.value.unit)

function syncTimeoutDuration() {
  timeout.value.timeDuration = buildTimeDuration(timeoutValue.value || 1, timeoutUnit.value)
}

const assignEmpty = computed(() => {
  if (!node.value.assignEmptyHandler) {
    node.value.assignEmptyHandler = { type: AssignEmptyHandlerType.APPROVE }
  }
  return node.value.assignEmptyHandler
})

const assignEmptyUserOpen = ref(false)

const assignEmptyUserNames = computed(() =>
  (assignEmpty.value.userIds ?? []).map((id) => {
    const user = users.value.find(item => item.id === id)
    return user?.nickname ?? `用户${id}`
  }),
)

function handleApproveMethodChange() {
  if (node.value.approveMethod === ApproveMethodType.BY_RATIO && !node.value.approveRatio) {
    node.value.approveRatio = 100
  }
}
</script>

<template>
  <Drawer v-model:open="visible" width="560" title="审批节点配置">
    <div class="config-head">
      <div class="config-head__icon" :style="{ backgroundColor: visual.color }">
        <Icon :icon="visual.icon" />
      </div>
      <Input v-model:value="node.name" placeholder="节点名称" />
    </div>

    <Form layout="vertical">
      <FormItem label="审批类型">
        <RadioGroup v-model:value="node.approveType" button-style="solid">
          <RadioButton v-for="item in APPROVE_TYPES" :key="item.value" :value="item.value">
            {{ item.label }}
          </RadioButton>
        </RadioGroup>
      </FormItem>

      <template v-if="node.approveType === ApproveType.USER">
        <Divider>审批人</Divider>
        <FormItem label="候选人策略">
          <Select
            v-model:value="node.candidateStrategy"
            placeholder="请选择候选人策略"
            :options="CANDIDATE_STRATEGIES.map(item => ({ label: item.label, value: item.value }))"
            option-filter-prop="label"
          />
        </FormItem>
        <FormItem v-if="strategyOption?.paramRequired" label="候选对象">
          <CandidateParamForm
            :strategy="node.candidateStrategy"
            :param="node.candidateParam"
            label="选择审批人"
            @update:param="(value: string) => (node.candidateParam = value)"
          />
        </FormItem>
        <FormItem label="多人审批方式">
          <Select
            v-model:value="node.approveMethod"
            :options="APPROVE_METHODS"
            @change="handleApproveMethodChange"
          />
        </FormItem>
        <FormItem v-if="node.approveMethod === ApproveMethodType.BY_RATIO" label="会签通过比例（%）">
          <InputNumber v-model:value="node.approveRatio" :min="1" :max="100" style="width: 100%" />
        </FormItem>
        <FormItem label="审批人与发起人相同时">
          <Select v-model:value="node.assignStartUserHandlerType" :options="ASSIGN_START_USER_HANDLER_TYPES" />
        </FormItem>
        <FormItem label="审批人为空时">
          <Select v-model:value="assignEmpty.type" :options="ASSIGN_EMPTY_HANDLER_TYPES" />
        </FormItem>
        <FormItem v-if="assignEmpty.type === AssignEmptyHandlerType.ASSIGN_USER" label="为空时指定成员">
          <div style="display: flex; gap: 8px; align-items: center">
            <span style="flex: 1; color: #6b7a90; font-size: 12px">
              {{ assignEmptyUserNames.length ? assignEmptyUserNames.join('、') : '未选择' }}
            </span>
            <Button size="small" @click="assignEmptyUserOpen = true">
              选择
            </Button>
          </div>
          <UserSelectModal
            v-model:open="assignEmptyUserOpen"
            title="选择兜底审批人"
            :selected-ids="assignEmpty.userIds ?? []"
            @confirm="(ids: number[]) => (assignEmpty.userIds = ids)"
          />
        </FormItem>

        <Divider>超时处理</Divider>
        <FormItem>
          <Switch v-model:checked="timeout.enable" checked-children="开启" un-checked-children="关闭" />
          <span style="margin-left: 8px; color: #8c94a5; font-size: 12px">超时后自动提醒 / 通过 / 拒绝</span>
        </FormItem>
        <template v-if="timeout.enable">
          <FormItem label="超时时间">
            <div style="display: flex; gap: 8px">
              <InputNumber v-model:value="timeoutValue" :min="1" style="flex: 1" @change="syncTimeoutDuration" />
              <Select v-model:value="timeoutUnit" :options="TIME_UNIT_TYPES" style="width: 100px" @change="syncTimeoutDuration" />
            </div>
          </FormItem>
          <FormItem label="超时动作">
            <Select v-model:value="timeout.type" :options="TIMEOUT_HANDLER_TYPES" />
          </FormItem>
          <FormItem v-if="timeout.type === TimeoutHandlerType.REMINDER" label="最大提醒次数">
            <InputNumber v-model:value="timeout.maxRemindCount" :min="1" :max="10" style="width: 100%" />
          </FormItem>
        </template>

        <Divider>拒绝处理</Divider>
        <FormItem label="审批拒绝时">
          <Select v-model:value="node.rejectHandler!.type" :options="REJECT_HANDLER_TYPES" />
        </FormItem>
        <FormItem v-if="node.rejectHandler?.type === RejectHandlerType.RETURN_USER_TASK" label="驳回目标节点">
          <Select
            v-model:value="node.rejectHandler.returnNodeId"
            placeholder="选择驳回到的审批节点"
            :options="returnNodeOptions"
          />
        </FormItem>

        <Divider>其他</Divider>
        <FormItem label="审批意见必填">
          <Switch v-model:checked="node.reasonRequire" checked-children="必填" un-checked-children="选填" />
        </FormItem>
      </template>
    </Form>
  </Drawer>
</template>

<style scoped>
.config-head {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}

.config-head__icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #fff;
  flex-shrink: 0;
}
</style>
