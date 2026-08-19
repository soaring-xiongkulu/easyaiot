<template>
  <div class="ffmpeg-env-tab">
    <ClusterNodeSelector
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="computeWorkload"
      :initial-node-ids="initialNodeIds"
      placeholder="选择已勾选对应功能的节点（可多选）"
    />

    <FfmpegBatchPanel :node-ids="selectedNodeIds" />
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import FfmpegBatchPanel from '../WorkloadBundleBatch/FfmpegBatchPanel.vue';

defineOptions({ name: 'FfmpegEnvTab' });

defineProps<{
  initialNodeIds?: number[];
}>();

const selectedNodeIds = ref<number[]>([]);
</script>

<style scoped lang="less">
.ffmpeg-env-tab {
  padding: 16px 20px 24px;
  min-height: 480px;
}
</style>
