<template>
  <div class="video-workload-init">
    <ClusterNodeSelector
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="computeWorkload"
      :initial-node-ids="initialNodeIds"
      placeholder="选择已勾选对应功能的节点（可多选）"
    />

    <Tabs
      v-model:activeKey="activeBundleKey"
      class="bundle-tabs-bar"
      type="card"
      :animated="{ inkBar: true, tabPane: false }"
    >
      <TabPane v-for="bundle in VIDEO_WORKLOAD_BUNDLE_TYPES" :key="bundle.key" :tab="bundle.label" />
    </Tabs>

    <div class="bundle-tab-content">
      <template v-for="bundle in VIDEO_WORKLOAD_BUNDLE_TYPES" :key="bundle.key">
        <WorkloadBundlePanel
          v-if="bundleMounted[bundle.key]"
          v-show="activeBundleKey === bundle.key"
          :bundle="bundle"
          :node-ids="selectedNodeIds"
        />
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { TabPane, Tabs } from 'ant-design-vue';
import { VIDEO_WORKLOAD_BUNDLE_TYPES } from '../../utils/constants';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import WorkloadBundlePanel from '../WorkloadBundleBatch/WorkloadBundlePanel.vue';

defineOptions({ name: 'VideoWorkloadInit' });

defineProps<{
  initialNodeIds?: number[];
}>();

const route = useRoute();
const selectedNodeIds = ref<number[]>([]);
const bundleFromQuery = String(route.query.bundle || '');
const defaultBundle =
  VIDEO_WORKLOAD_BUNDLE_TYPES.find((b) => b.key === bundleFromQuery)?.key ||
  VIDEO_WORKLOAD_BUNDLE_TYPES[0]?.key ||
  'stream_forward';
const activeBundleKey = ref(defaultBundle);
const bundleMounted = reactive<Record<string, boolean>>({
  [defaultBundle]: true,
});

watch(activeBundleKey, (key) => {
  bundleMounted[key] = true;
});
</script>

<style scoped lang="less">
.video-workload-init {
  padding: 16px 20px 24px;
  min-height: 480px;

  :deep(.bundle-tabs-bar .ant-tabs-content-holder) {
    display: none;
  }
}
</style>
