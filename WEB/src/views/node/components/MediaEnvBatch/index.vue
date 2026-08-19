<template>
  <div class="media-env-batch">
    <MediaPathReadinessBar :selected-node="singleNodeDetail" />

    <ClusterNodeSelector
      ref="selectorRef"
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="media"
      :initial-node-id="initialNodeId"
      :initial-node-ids="initialNodeIds"
      placeholder="选择已勾选直播接入或推流转发的节点（可多选）"
    />

    <CollapseContainer
      v-if="selectedNodeIds.length > 1"
      title="批量操作"
      :canExpan="true"
      :defaultExpan="true"
      class="mb-4"
    >
      <Space wrap class="mb-3">
        <Button :loading="loading === 'check'" :disabled="!canBatchOperate" @click="runCheck">
          {{ SETUP_COPY.checkMediaDeployBtn }}
        </Button>
        <Button type="primary" :loading="loading === 'deploy'" :disabled="!canBatchOperate" @click="runDeploy">
          {{ SETUP_COPY.deployMediaBtn }}
        </Button>
      </Space>
      <BatchNodeResults :results="nodeResults" />
    </CollapseContainer>

    <template v-if="singleNode">
      <MediaStackSetupPanel
        :active="true"
        :form-values="mediaFormValues"
        @deployed="handleSingleDeployed"
      />
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { Space } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { useMessage } from '@/hooks/web/useMessage';
import {
  checkMediaStackBySsh,
  deployMediaStackBySsh,
  getNode,
  type ComputeNodeVO,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import { readMediaPortsFromTags, SETUP_COPY } from '../../utils/constants';
import { runSequentialNodeOps, summarizeBatchResults } from '../../utils/batchNodeOps';
import BatchNodeResults from '../BatchNodeResults/index.vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import MediaPathReadinessBar from '../MediaPathReadinessBar/index.vue';
import MediaStackSetupPanel from '../MediaStackSetupPanel/index.vue';

defineOptions({ name: 'MediaEnvBatch' });

const props = defineProps<{
  initialNodeId?: number;
  initialNodeIds?: number[];
}>();

const { createMessage } = useMessage();

const selectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const selectedNodeIds = ref<number[]>([]);
const loading = ref<'check' | 'deploy' | null>(null);
const nodeResults = ref<WorkloadBundleNodeResult[]>([]);
const singleNodeDetail = ref<ComputeNodeVO | null>(null);

const selectedNodes = computed(() => selectorRef.value?.selectedNodes ?? []);
const canBatchOperate = computed(() => selectedNodeIds.value.length > 1);
const singleNode = computed(() => (selectedNodeIds.value.length === 1 ? selectedNodes.value[0] : null));

const mediaFormValues = computed(() => {
  const current = singleNodeDetail.value;
  if (!current) return undefined;
  const tags = current.tags || {};
  return {
    nodeRole: current.nodeRole,
    nodeId: current.id,
    name: current.name,
    host: current.host,
    sshUsername: current.sshUsername,
    sshCredentialConfigured: current.sshCredentialConfigured,
    sshLastTestOk: current.sshLastTestOk,
    sshPort: current.sshPort,
    ...readMediaPortsFromTags(tags),
  };
});

async function loadSingleNodeDetail(nodeId: number) {
  try {
    singleNodeDetail.value = await getNode(nodeId);
  } catch {
    singleNodeDetail.value = singleNode.value ?? null;
    createMessage.error('加载节点详情失败');
  }
}

watch(
  () => singleNode.value?.id,
  (nodeId) => {
    if (nodeId) loadSingleNodeDetail(nodeId);
    else singleNodeDetail.value = null;
  },
);

watch(
  () => props.initialNodeId,
  (id) => {
    if (id) selectedNodeIds.value = [id];
  },
  { immediate: true },
);

watch(
  () => props.initialNodeIds,
  (ids) => {
    if (ids?.length) selectedNodeIds.value = [...ids];
  },
  { immediate: true },
);

async function runCheck() {
  if (!canBatchOperate.value) {
    createMessage.warning('请先选择多个目标节点');
    return;
  }
  loading.value = 'check';
  nodeResults.value = [];
  try {
    const results: WorkloadBundleNodeResult[] = [];
    for (const node of selectedNodes.value) {
      if (!node.id) continue;
      try {
        const data = await checkMediaStackBySsh(node.id);
        results.push({
          nodeId: node.id,
          nodeName: node.name,
          host: node.host,
          success: !!data.success,
          message: data.message || (data.deployed ? '已部署' : '未部署'),
        });
      } catch (e: unknown) {
        results.push({
          nodeId: node.id,
          nodeName: node.name,
          host: node.host,
          success: false,
          message: e instanceof Error ? e.message : '检测失败',
        });
      }
    }
    nodeResults.value = results;
    const summary = summarizeBatchResults(results);
    summary.success ? createMessage.success(summary.message) : createMessage.warning(summary.message);
  } finally {
    loading.value = null;
  }
}

async function runDeploy() {
  if (!canBatchOperate.value) {
    createMessage.warning('请先选择多个目标节点');
    return;
  }
  loading.value = 'deploy';
  nodeResults.value = [];
  try {
    nodeResults.value = await runSequentialNodeOps(selectedNodes.value, (nodeId) =>
      deployMediaStackBySsh(nodeId),
    );
    const summary = summarizeBatchResults(nodeResults.value);
    summary.success ? createMessage.success(summary.message) : createMessage.error(summary.message);
  } finally {
    loading.value = null;
  }
}

async function handleSingleDeployed() {
  const id = singleNodeDetail.value?.id;
  if (id) await loadSingleNodeDetail(id);
  selectorRef.value?.loadNodes();
}
</script>

<style scoped lang="less">
.media-env-batch {
  padding: 16px 20px 24px;
  min-height: 480px;

  .mb-3 {
    margin-bottom: 12px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
