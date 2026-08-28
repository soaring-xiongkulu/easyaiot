<script lang="ts" setup>
import { ref } from 'vue'
import type { SimpleFlowNode } from '../../consts'
import { useWatchNode } from '../../helpers'
import NodeCard from '../NodeCard.vue'
import NodeHandler from '../NodeHandler.vue'
import UserTaskNodeConfig from '../nodes-config/UserTaskNodeConfig.vue'

defineOptions({ name: 'FlowUserTaskNode' })

const props = defineProps<{ flowNode: SimpleFlowNode }>()

const emit = defineEmits<{
  'update:flowNode': [node: SimpleFlowNode | undefined]
}>()

const currentNode = useWatchNode(props)
const configRef = ref<InstanceType<typeof UserTaskNodeConfig>>()

/** 删除节点 = 用自己的后继节点替换自己 */
function deleteNode() {
  emit('update:flowNode', currentNode.value.childNode)
}
</script>

<template>
  <div class="fpd-node">
    <NodeCard :node="currentNode" :deletable="true" @click="configRef?.open()" @delete="deleteNode" />
    <NodeHandler v-if="currentNode" :current-node="currentNode" />
    <UserTaskNodeConfig ref="configRef" :node="currentNode" />
  </div>
</template>
