<script lang="ts" setup>
import { ref } from 'vue'
import type { SimpleFlowNode } from '../../consts'
import { useWatchNode } from '../../helpers'
import NodeCard from '../NodeCard.vue'
import NodeHandler from '../NodeHandler.vue'
import DelayTimerNodeConfig from '../nodes-config/DelayTimerNodeConfig.vue'

defineOptions({ name: 'FlowDelayTimerNode' })

const props = defineProps<{ flowNode: SimpleFlowNode }>()

const emit = defineEmits<{
  'update:flowNode': [node: SimpleFlowNode | undefined]
}>()

const currentNode = useWatchNode(props)
const configRef = ref<InstanceType<typeof DelayTimerNodeConfig>>()

function deleteNode() {
  emit('update:flowNode', currentNode.value.childNode)
}
</script>

<template>
  <div class="fpd-node">
    <NodeCard :node="currentNode" :deletable="true" @click="configRef?.open()" @delete="deleteNode" />
    <NodeHandler v-if="currentNode" :current-node="currentNode" />
    <DelayTimerNodeConfig ref="configRef" :node="currentNode" />
  </div>
</template>
