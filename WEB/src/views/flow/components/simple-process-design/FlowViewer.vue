<script lang="ts" setup>
/**
 * FLOW Simple 流程查看器（只读渲染 + 节点状态染色）
 * - flowNode：流程树（SimpleModel 快照）
 * - finished / unfinished / rejected / activityIds：get-bpmn-model-view 返回的高亮集合，
 *   在父组件把运行态写入节点 activityStatus 后传入，或直接传集合由本组件标注。
 */
import type { SimpleFlowNode } from './consts'
import { provide } from 'vue'
import ProcessNodeTree from './components/ProcessNodeTree.vue'
import { useCandidateOptions } from './useCandidateOptions'
import './style.css'

defineOptions({ name: 'FlowViewer' })

defineProps<{
  flowNode?: SimpleFlowNode
}>()

useCandidateOptions()
provide('fpd-readonly', true)
provide('readonly', true)
</script>

<template>
  <div class="fpd-designer fpd-designer--viewer">
    <div class="fpd-canvas">
      <ProcessNodeTree v-if="flowNode" :flow-node="flowNode" />
    </div>
  </div>
</template>

<style scoped>
.fpd-designer--viewer {
  pointer-events: none;
}
</style>
