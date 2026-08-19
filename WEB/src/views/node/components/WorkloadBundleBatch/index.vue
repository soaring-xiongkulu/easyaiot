<template>
  <div class="workload-bundle-batch">
    <Alert
      type="info"
      show-icon
      class="mb-4"
      message="业务运行时分发"
      :description="`${WORKLOAD_BUNDLE_COPY.offlineHint} ${WORKLOAD_BUNDLE_COPY.remotePythonTip}`"
    />

    <div class="node-select-row mb-4">
      <Select
        v-model:value="selectedNodeIds"
        mode="multiple"
        show-search
        allow-clear
        placeholder="选择已勾选分析/训练/推理等计算功能的节点（可多选）"
        style="min-width: 480px; flex: 1"
        :options="nodeOptions"
        :filter-option="filterNode"
        :loading="nodesLoading"
      />
      <Button @click="loadNodes" :loading="nodesLoading">刷新</Button>
      <Button type="link" @click="selectAllEligible">全选可用</Button>
    </div>

    <CollapseContainer title="音视频转码 · FFmpeg" :canExpan="true" :defaultExpan="true" class="mb-4">
      <FfmpegBatchPanel :node-ids="selectedNodeIds" />
    </CollapseContainer>

    <CollapseContainer title="高性能算法 · RUNTIME(C++)" :canExpan="true" :defaultExpan="true" class="mb-4">
      <RuntimeCppBatchPanel :node-ids="selectedNodeIds" />
    </CollapseContainer>

    <Tabs v-model:activeKey="activeBundleKey" type="card" destroy-inactive-tab-pane>
      <TabPane v-for="bundle in WORKLOAD_BUNDLE_TYPES" :key="bundle.key" :tab="bundle.label">
        <WorkloadBundlePanel :bundle="bundle" :node-ids="selectedNodeIds" />
      </TabPane>
    </Tabs>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { Alert, Select, TabPane, Tabs } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { getNodePage, type ComputeNodeVO } from '@/api/device/node';
import { isPlatformNode } from '../../utils/platformNode';
import { WORKLOAD_BUNDLE_COPY, WORKLOAD_BUNDLE_TYPES, isSchedulableComputeNode } from '../../utils/constants';
import WorkloadBundlePanel from './WorkloadBundlePanel.vue';
import FfmpegBatchPanel from './FfmpegBatchPanel.vue';
import RuntimeCppBatchPanel from './RuntimeCppBatchPanel.vue';

defineOptions({ name: 'WorkloadBundleBatch' });

const route = useRoute();
const nodesLoading = ref(false);
const nodeList = ref<ComputeNodeVO[]>([]);
const selectedNodeIds = ref<number[]>([]);
const bundleFromQuery = String(route.query.bundle || '');
const defaultBundle = WORKLOAD_BUNDLE_TYPES.find((b) => b.key === bundleFromQuery)?.key
  || WORKLOAD_BUNDLE_TYPES[0].key;
const activeBundleKey = ref(defaultBundle);

const nodeOptions = ref<Array<{ label: string; value: number; disabled?: boolean }>>([]);

function filterNode(input: string, option: { label?: string }) {
  return (option.label || '').toLowerCase().includes(input.toLowerCase());
}

function isEligibleNode(node: ComputeNodeVO) {
  if (isPlatformNode(node)) return false;
  if (!isSchedulableComputeNode(node)) return false;
  return !!(node.sshUsername?.trim() || node.sshCredentialConfigured);
}

async function loadNodes() {
  nodesLoading.value = true;
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 500 });
    // 分发目标不含本机控制面：列表直接隐藏 platform 节点
    nodeList.value = (res?.data?.list || []).filter((node) => !isPlatformNode(node));
    nodeOptions.value = nodeList.value.map((node) => ({
      label: `${node.name} (${node.host}) — ${node.status || 'unknown'}`,
      value: node.id!,
      disabled: !isEligibleNode(node),
    }));
  } finally {
    nodesLoading.value = false;
  }
}

function selectAllEligible() {
  selectedNodeIds.value = nodeList.value.filter(isEligibleNode).map((n) => n.id!);
}

onMounted(() => {
  loadNodes();
});
</script>

<style scoped lang="less">
.workload-bundle-batch {
  padding: 16px 20px 24px;
  min-height: 480px;
}

.node-select-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
