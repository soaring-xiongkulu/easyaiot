<script lang="ts" setup>
/**
 * 分支节点（条件分支 / 并行分支共用）：
 * 横向排布 conditionNodes 各列，列内递归渲染子链，删除分支需保留至少 2 条。
 */
import { computed, inject, ref } from 'vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../../consts'
import { createNode, NodeType } from '../../consts'
import { nodeDisplayText, useWatchNode } from '../../helpers'
import NodeHandler from '../NodeHandler.vue'
import ProcessNodeTree from '../ProcessNodeTree.vue'
import ConditionNodeConfig from '../nodes-config/ConditionNodeConfig.vue'
import EndEventNode from './EndEventNode.vue'

defineOptions({ name: 'FlowBranchNode' })

const props = defineProps<{ flowNode: SimpleFlowNode }>()

const emit = defineEmits<{
  'update:flowNode': [node: SimpleFlowNode | undefined]
}>()

const currentNode = useWatchNode(props)
const readonly = inject<boolean>('fpd-readonly', false)

const isParallel = computed(() => currentNode.value.type === NodeType.PARALLEL_BRANCH_NODE)

const conditionConfigRef = ref<InstanceType<typeof ConditionNodeConfig>>()
const activeConditionId = ref('')

const activeCondition = computed(() =>
  currentNode.value.conditionNodes?.find(item => item.id === activeConditionId.value),
)

const activePriority = computed(() => {
  const idx = currentNode.value.conditionNodes?.findIndex(item => item.id === activeConditionId.value) ?? -1
  return idx >= 0 ? idx + 1 : undefined
})

function openCondition(condition: SimpleFlowNode) {
  activeConditionId.value = condition.id
  conditionConfigRef.value?.open()
}

function addBranch() {
  const branches = currentNode.value.conditionNodes ?? []
  if (isParallel.value) {
    const branch = createNode(NodeType.CONDITION_NODE, `分支${branches.length + 1}`)
    branch.conditionSetting!.conditionType = 1
    branch.conditionSetting!.conditionExpression = '${true}'
    branch.childNode = branches[branches.length - 1]?.childNode
    branches.push(branch)
  }
  else {
    const branch = createNode(NodeType.CONDITION_NODE, `条件${branches.length}`)
    branch.childNode = branches[branches.length - 1]?.childNode
    branches.splice(branches.length - 1, 0, branch)
  }
}

function removeBranch(index: number) {
  const branches = currentNode.value.conditionNodes ?? []
  if (branches.length <= 2) {
    return
  }
  branches.splice(index, 1)
}

/** 删除分支节点整体 = 用其后继节点替换自己 */
function removeBranchNode() {
  emit('update:flowNode', currentNode.value.childNode)
}
</script>

<template>
  <div class="fpd-branch">
    <span v-if="!readonly" class="fpd-branch__remove" title="删除分支节点" @click="removeBranchNode">
      <Icon icon="ant-design:delete-outlined" />
    </span>
    <div class="fpd-branch__cols">
      <div v-for="(condition, idx) in currentNode.conditionNodes" :key="condition.id" class="fpd-branch__col">
        <div class="fpd-branch__inner">
          <!-- 分支头：条件卡（并行分支显示分支卡） -->
          <div class="fpd-condition" @click="openCondition(condition)">
            <span v-if="!readonly" class="fpd-condition__del" title="删除该分支" @click.stop="removeBranch(idx)">
              <Icon icon="ant-design:close-outlined" />
            </span>
            <div class="fpd-condition__head">
              <span class="fpd-condition__title">{{ condition.name }}</span>
              <span v-if="condition.conditionSetting?.defaultFlow" class="fpd-condition__tag fpd-condition__tag--default">默认</span>
              <span v-else-if="!isParallel" class="fpd-condition__tag">优先级{{ idx + 1 }}</span>
            </div>
            <div class="fpd-condition__text" :class="{ 'fpd-condition__text--empty': !nodeDisplayText(condition) }">
              {{ isParallel ? '无条件并行执行' : (nodeDisplayText(condition) || '请设置条件') }}
            </div>
          </div>
          <!-- 分支内插入节点 -->
          <NodeHandler :current-node="condition" />
          <!-- 分支内子链递归 -->
          <ProcessNodeTree v-if="condition.childNode" v-model:flow-node="condition.childNode" />
          <EndEventNode v-else />
        </div>
      </div>
      <!-- 汇聚线与主链路衔接的接头 -->
      <span class="fpd-branch__joint fpd-branch__joint--top" />
      <span class="fpd-branch__joint fpd-branch__joint--bottom" />
      <!-- 追加分支：悬浮在下汇聚线上 -->
      <div v-if="!readonly" class="fpd-branch__add" @click="addBranch">
        <Icon icon="ant-design:plus-outlined" />
        {{ isParallel ? '添加并行分支' : '添加条件' }}
      </div>
    </div>
    <!-- 分支汇聚后的后继链 -->
    <NodeHandler :current-node="currentNode" />
    <ProcessNodeTree v-if="currentNode.childNode" v-model:flow-node="currentNode.childNode" />
    <EndEventNode v-else />
    <!-- 条件配置抽屉（绑定当前编辑的条件节点） -->
    <ConditionNodeConfig ref="conditionConfigRef" :node="activeCondition ?? ({} as SimpleFlowNode)" :priority="activePriority" />
  </div>
</template>
