<script lang="ts" setup>
/**
 * FLOW Simple 流程设计器（编辑器）
 * - v-model:value 传入流程树（根节点为发起人节点），组件内就地修改
 * - expose：validate() 返回错误列表；getData() 返回当前树
 */
import type { ComputedRef } from 'vue'
import { computed, provide, toRaw } from 'vue'
import type { SimpleFlowNode } from './consts'
import { validateFlowTree } from './helpers'
import ProcessNodeTree from './components/ProcessNodeTree.vue'
import { useCandidateOptions } from './useCandidateOptions'
import './style.css'

defineOptions({ name: 'FlowDesigner' })

const props = defineProps<{
  value?: SimpleFlowNode
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:value': [node: SimpleFlowNode]
}>()

useCandidateOptions()

const rootNode = computed(() => props.value) as ComputedRef<SimpleFlowNode | undefined>

provide('readonly', props.readonly ?? false)
provide('fpd-readonly', props.readonly ?? false)
provide('fpd-root', rootNode)

function validate(): string[] {
  return validateFlowTree(props.value)
}

function getData(): SimpleFlowNode | undefined {
  return props.value ? toRaw(props.value) : undefined
}

defineExpose({ validate, getData })
</script>

<template>
  <div class="fpd-designer">
    <div class="fpd-canvas">
      <ProcessNodeTree
        v-if="value"
        :flow-node="value"
        @update:flow-node="(node: any) => emit('update:value', node as SimpleFlowNode)"
      />
    </div>
  </div>
</template>
