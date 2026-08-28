<script lang="ts" setup>
import { ref } from 'vue'
import type { SimpleFlowNode } from '../../consts'
import { useWatchNode } from '../../helpers'
import NodeCard from '../NodeCard.vue'
import NodeHandler from '../NodeHandler.vue'
import CopyTaskNodeConfig from '../nodes-config/CopyTaskNodeConfig.vue'

defineOptions({ name: 'FlowCopyTaskNode' })

const props = defineProps<{ flowNode: SimpleFlowNode }>()

const emit = defineEmits<{
  'update:flowNode': [node: SimpleFlowNode | undefined]
}>()

const currentNode = useWatchNode(props)
const configRef = ref<InstanceType<typeof CopyTaskNodeConfig>>()

function deleteNode() {
  emit('update:flowNode', currentNode.value.childNode)
}
</script>

<template>
  <div class="fpd-node">
    <NodeCard :node="currentNode" :deletable="true" @click="configRef?.open()" @delete="deleteNode" />
    <NodeHandler v-if="currentNode" :current-node="currentNode" />
    <CopyTaskNodeConfig ref="configRef" :node="currentNode" />
  </div>
</template>
