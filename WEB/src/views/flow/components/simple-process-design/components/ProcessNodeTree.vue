<script lang="ts" setup>
/**
 * 节点树递归渲染器：按节点类型分发到对应节点组件
 * （与 yudao process-node-tree 的职责一致，链表结构 v-model 逐级替换实现删除）
 */
import type { SimpleFlowNode } from '../consts'
import { NodeType } from '../consts'
import BranchNode from './nodes/BranchNode.vue'
import CopyTaskNode from './nodes/CopyTaskNode.vue'
import DelayTimerNode from './nodes/DelayTimerNode.vue'
import EndEventNode from './nodes/EndEventNode.vue'
import StartUserNode from './nodes/StartUserNode.vue'
import UserTaskNode from './nodes/UserTaskNode.vue'

defineOptions({ name: 'FlowProcessNodeTree' })

defineProps<{
  flowNode: SimpleFlowNode
}>()

const emit = defineEmits<{
  'update:flowNode': [node: SimpleFlowNode | undefined]
}>()

function handleModelValueUpdate(value: SimpleFlowNode | undefined) {
  emit('update:flowNode', value)
}
</script>

<template>
  <div class="fpd-tree">
    <!-- 发起人节点 -->
    <StartUserNode v-if="flowNode.type === NodeType.START_USER_NODE" :flow-node="flowNode" />

    <!-- 审批节点 -->
    <UserTaskNode
      v-else-if="flowNode.type === NodeType.USER_TASK_NODE"
      :flow-node="flowNode"
      @update:flow-node="handleModelValueUpdate"
    />

    <!-- 抄送节点 -->
    <CopyTaskNode
      v-else-if="flowNode.type === NodeType.COPY_TASK_NODE"
      :flow-node="flowNode"
      @update:flow-node="handleModelValueUpdate"
    />

    <!-- 延迟器节点 -->
    <DelayTimerNode
      v-else-if="flowNode.type === NodeType.DELAY_TIMER_NODE"
      :flow-node="flowNode"
      @update:flow-node="handleModelValueUpdate"
    />

    <!-- 条件分支 / 并行分支 -->
    <BranchNode
      v-else-if="flowNode.type === NodeType.CONDITION_BRANCH_NODE || flowNode.type === NodeType.PARALLEL_BRANCH_NODE"
      :flow-node="flowNode"
      @update:flow-node="handleModelValueUpdate"
    />

    <!-- 结束节点 -->
    <EndEventNode v-else-if="flowNode.type === NodeType.END_EVENT_NODE" />

    <!-- 递归渲染后继节点 -->
    <template v-if="flowNode.childNode">
      <ProcessNodeTree v-model:flow-node="flowNode.childNode" />
    </template>
  </div>
</template>
