<template>
  <div class="agent-env-batch">
    <ClusterNodeSelector
      ref="selectorRef"
      v-model:selected-node-ids="selectedNodeIds"
      role-filter="allManaged"
      :initial-node-id="initialNodeId"
      placeholder="选择已纳管节点（可多选）"
    />

    <CollapseContainer
      v-if="selectedNodeIds.length > 1"
      title="批量操作"
      :canExpan="true"
      :defaultExpan="true"
      class="mb-4"
    >
      <Form :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <FormItem :label="NODE_TERM.platformUrl">
          <Input v-model:value="controlPlaneUrl" :placeholder="NODE_TERM.platformUrl" />
        </FormItem>
      </Form>
      <Alert
        v-if="controlPlaneLocalhostWarn"
        type="warning"
        show-icon
        class="mb-3"
        message="平台接入地址为 localhost，远程节点可能无法连接。建议填写宿主机可达 IP。"
      />
      <Space wrap class="mb-3">
        <Button :loading="loading === 'check'" :disabled="!canBatchOperate" @click="runCheck">
          {{ SETUP_COPY.checkAgentDeployBtn }}
        </Button>
        <Button type="primary" :loading="loading === 'deploy'" :disabled="!canBatchOperate" @click="runDeploy">
          {{ SETUP_COPY.deployAgentBtn }}
        </Button>
      </Space>
      <BatchNodeResults :results="nodeResults" />
    </CollapseContainer>

    <template v-if="singleNode">
      <div class="single-node-panel">
        <AgentDeployPanel
          v-model:control-plane-url="controlPlaneUrl"
          :active="true"
          :node="singleNodeDetail"
          :agent-token="agentToken"
          @deployed="handleSingleDeployed"
        />
        <SetupVerifyPanel
          v-if="singleNodeDetail?.status !== 'online'"
          v-model:control-plane-url="controlPlaneUrl"
          :node-id="singleNodeDetail!.id!"
          :active="true"
          :ssh-ready="!!singleNodeDetail?.sshUsername?.trim() || singleNodeDetail?.sshCredentialConfigured === true"
          @online="handleSingleDeployed"
        />
        <div v-if="singleNodeDetail && !isPlatformNode(singleNodeDetail)" class="single-node-actions">
          <Button danger ghost @click="handleResetToken">
            重置{{ NODE_TERM.agentToken }}
          </Button>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { Alert, Form, FormItem, Input, Space } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { useMessage } from '@/hooks/web/useMessage';
import {
  checkAgentBySsh,
  deployAgentBySsh,
  getNode,
  resetAgentToken,
  type ComputeNodeVO,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import {
  isLocalControlPlaneUrl,
  NODE_TERM,
  resolveControlPlaneAgentUrl,
  SETUP_COPY,
  loadNodeControlPlaneUrlAsync,
} from '../../utils/constants';
import { runSequentialNodeOps, summarizeBatchResults } from '../../utils/batchNodeOps';
import { isPlatformNode } from '../../utils/platformNode';
import AgentDeployPanel from '../AgentDeployPanel/index.vue';
import BatchNodeResults from '../BatchNodeResults/index.vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import SetupVerifyPanel from '../SetupVerifyPanel/index.vue';

defineOptions({ name: 'AgentEnvBatch' });

const props = defineProps<{
  initialNodeId?: number;
  initialNodeIds?: number[];
}>();

const { createMessage, createConfirm } = useMessage();

const selectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const selectedNodeIds = ref<number[]>([]);
const controlPlaneUrl = ref('');
const loading = ref<'check' | 'deploy' | null>(null);
const nodeResults = ref<WorkloadBundleNodeResult[]>([]);
const singleNodeDetail = ref<ComputeNodeVO | null>(null);
const agentToken = ref('');

const controlPlaneLocalhostWarn = computed(() => isLocalControlPlaneUrl(controlPlaneUrl.value));
const selectedNodes = computed(() => selectorRef.value?.selectedNodes ?? []);
const canBatchOperate = computed(() => selectedNodeIds.value.length > 1 && !!controlPlaneUrl.value.trim());
const singleNode = computed(() => (selectedNodeIds.value.length === 1 ? selectedNodes.value[0] : null));

async function loadSingleNodeDetail(nodeId: number) {
  try {
    singleNodeDetail.value = await getNode(nodeId);
    agentToken.value = singleNodeDetail.value?.agentToken || '';
    const savedUrl = await loadNodeControlPlaneUrlAsync(nodeId);
    if (savedUrl) controlPlaneUrl.value = savedUrl;
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
    createMessage.warning('请先选择多个目标节点并填写平台接入地址');
    return;
  }
  loading.value = 'check';
  nodeResults.value = [];
  try {
    const results: WorkloadBundleNodeResult[] = [];
    for (const node of selectedNodes.value) {
      if (!node.id) continue;
      try {
        const data = await checkAgentBySsh(node.id, controlPlaneUrl.value);
        const deployed = !!(data.deployed || data.serviceRunning || data.installDirReady);
        results.push({
          nodeId: node.id,
          nodeName: node.name,
          host: node.host,
          success: !!data.success,
          message: data.message || (deployed ? '已部署' : '未部署'),
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
    createMessage.warning('请先选择多个目标节点并填写平台接入地址');
    return;
  }
  loading.value = 'deploy';
  nodeResults.value = [];
  try {
    nodeResults.value = await runSequentialNodeOps(selectedNodes.value, (nodeId) =>
      deployAgentBySsh(nodeId, controlPlaneUrl.value),
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

function handleResetToken() {
  const node = singleNodeDetail.value;
  if (!node?.id || isPlatformNode(node)) return;
  createConfirm({
    title: `重置${NODE_TERM.agentToken}`,
    content: `重置后需在目标服务器更新 agent.env 中的 AGENT_TOKEN，并重启${NODE_TERM.agent}`,
    onOk: async () => {
      const res = await resetAgentToken(node.id!);
      agentToken.value = typeof res === 'string' ? res : res?.data ?? res;
      createMessage.success('令牌已重置');
    },
  });
}

onMounted(async () => {
  controlPlaneUrl.value = await resolveControlPlaneAgentUrl();
});
</script>

<style scoped lang="less">
.agent-env-batch {
  padding: 16px 20px 24px;
  min-height: 480px;
}

.single-node-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.single-node-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0 4px;
}
</style>
