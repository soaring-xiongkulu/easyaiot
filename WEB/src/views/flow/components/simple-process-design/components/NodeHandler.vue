<script lang="ts" setup>
/**
 * 节点之间的「+」插入按钮：在当前节点之后插入新节点（分支节点会接管原有后继）
 */
import { computed, inject, ref } from 'vue'
import { Popover } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import type { SimpleFlowNode } from '../consts'
import {
  createConditionBranch,
  createNode,
  NODE_VISUALS,
  NodeType,
} from '../consts'

defineOptions({ name: 'FlowNodeHandler' })

const props = defineProps<{
  /** 当前节点（新节点插入到它之后） */
  currentNode: SimpleFlowNode
  readonly?: boolean
}>()

const isReadonly = inject<boolean>('fpd-readonly', props.readonly ?? false)
const popoverOpen = ref(false)

const INSERT_OPTIONS = [
  { type: NodeType.USER_TASK_NODE, label: '审批人' },
  { type: NodeType.COPY_TASK_NODE, label: '抄送人' },
  { type: NodeType.CONDITION_BRANCH_NODE, label: '条件分支' },
  { type: NodeType.PARALLEL_BRANCH_NODE, label: '并行分支' },
  { type: NodeType.DELAY_TIMER_NODE, label: '延迟器' },
] as const

/** 分支后不允许直接再挂并行分支（避免嵌套歧义），与 yudao 校验保持一致 */
const parentIsBranch = computed(() =>
  props.currentNode.type === NodeType.CONDITION_BRANCH_NODE
  || props.currentNode.type === NodeType.PARALLEL_BRANCH_NODE,
)

const options = computed(() =>
  INSERT_OPTIONS.filter(item => !(parentIsBranch.value && item.type === NodeType.PARALLEL_BRANCH_NODE)),
)

function handleInsert(type: NodeType) {
  let newNode: SimpleFlowNode
  if (type === NodeType.CONDITION_BRANCH_NODE) {
    newNode = createConditionBranch(false, props.currentNode.childNode)
  }
  else if (type === NodeType.PARALLEL_BRANCH_NODE) {
    newNode = createConditionBranch(true, props.currentNode.childNode)
  }
  else {
    newNode = createNode(type)
    newNode.childNode = props.currentNode.childNode
  }
  props.currentNode.childNode = newNode
  popoverOpen.value = false
}
</script>

<template>
  <Popover v-model:open="popoverOpen" trigger="click" placement="bottom" overlay-class-name="fpd-insert-popover">
    <template #content>
      <div class="fpd-insert">
        <div v-for="item in options" :key="item.type" class="fpd-insert__item" @click="handleInsert(item.type)">
          <div class="fpd-insert__icon" :style="{ backgroundColor: NODE_VISUALS[item.type]?.color }">
            <Icon :icon="NODE_VISUALS[item.type]?.icon" />
          </div>
          <span class="fpd-insert__label">{{ item.label }}</span>
        </div>
      </div>
    </template>
    <div class="fpd-handler">
      <div v-if="!isReadonly" class="fpd-handler__btn">
        <Icon icon="ant-design:plus-outlined" />
      </div>
    </div>
  </Popover>
</template>
