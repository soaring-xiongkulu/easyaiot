<script lang="ts" setup>
import { ref } from 'vue'
import type { SimpleFlowNode } from '../../consts'
import { useWatchNode } from '../../helpers'
import NodeCard from '../NodeCard.vue'
import NodeHandler from '../NodeHandler.vue'
import StartUserNodeConfig from '../nodes-config/StartUserNodeConfig.vue'

defineOptions({ name: 'FlowStartUserNode' })

const props = defineProps<{ flowNode: SimpleFlowNode }>()

const currentNode = useWatchNode(props)
const configRef = ref<InstanceType<typeof StartUserNodeConfig>>()
</script>

<template>
  <div class="fpd-node">
    <NodeCard :node="currentNode" :deletable="false" @click="configRef?.open()" />
    <NodeHandler :current-node="currentNode" />
    <StartUserNodeConfig ref="configRef" :node="currentNode" />
  </div>
</template>
