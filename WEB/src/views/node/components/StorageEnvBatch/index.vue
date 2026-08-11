<template>
  <div class="storage-env-batch">
    <Tabs v-model:activeKey="innerTab" class="storage-inner-tabs">
      <TabPane key="topology" :tab="NODE_TERM.storageCephTopology">
        <Alert
          class="mb-3"
          type="info"
          show-icon
          message="中心关联的 NFS 共享媒体节点拓扑。点击节点可检测挂载状态并执行 NFS 服务端/客户端运维；批量表单式操作请切换至「批量运维」。"
        />
        <CephTopologyPanel
          v-if="innerTab === 'topology'"
          embedded-in-storage
          @open-ops="openBatchOps"
        />
      </TabPane>

      <TabPane key="ops" :tab="NODE_TERM.storageBatchOps">
        <ClusterScopeBar @lane-change="handleLaneChange" />

        <CollapseContainer title="① NFS 服务端（storage 角色）" :canExpan="true" :defaultExpan="true" class="mb-4">
          <ClusterNodeSelector
            ref="osdSelectorRef"
            v-model:selected-node-ids="osdNodeIds"
            role-filter="storage"
            :show-scope-bar="false"
            :initial-node-ids="initialNodeIds"
            placeholder="选择 storage 节点安装 NFS 服务端"
          />
          <Space wrap class="mb-3">
            <Button :loading="osdLoading === 'check'" :disabled="!osdNodeIds.length" @click="runOsdCheck">
              检测 NFS 服务端
            </Button>
            <Button type="primary" :loading="osdLoading === 'deploy'" :disabled="!osdNodeIds.length" @click="runOsdDeploy">
              安装 NFS 服务端
            </Button>
          </Space>
          <BatchNodeResults :results="osdResults" />
        </CollapseContainer>

        <CollapseContainer title="② Export 初始化（storage 节点）" :canExpan="true" :defaultExpan="true" class="mb-4">
          <ClusterNodeSelector
            ref="poolSelectorRef"
            v-model:selected-node-ids="poolNodeIds"
            role-filter="storage"
            :show-scope-bar="false"
            :initial-node-ids="initialNodeIds"
            placeholder="选择 NFS 服务端节点（通常单选）"
          />
          <Space wrap class="mb-3">
            <Button type="primary" :loading="poolLoading" :disabled="!poolNodeIds.length" @click="runPoolDeploy">
              初始化 Export
            </Button>
          </Space>
          <BatchNodeResults :results="poolResults" />
        </CollapseContainer>

        <CollapseContainer title="③ NFS 客户端挂载" :canExpan="true" :defaultExpan="true" class="mb-4">
          <ClusterNodeSelector
            ref="clientSelectorRef"
            v-model:selected-node-ids="clientNodeIds"
            role-filter="cephClient"
            :show-scope-bar="false"
            :initial-node-ids="initialNodeIds"
            placeholder="选择 compute / gpu / hybrid / media 节点挂载 NFS"
          />
          <Space wrap class="mb-3">
            <Button :loading="clientLoading === 'check'" :disabled="!clientNodeIds.length" @click="runClientCheck">
              检测挂载
            </Button>
            <Button
              type="primary"
              :loading="clientLoading === 'deploy'"
              :disabled="!clientNodeIds.length"
              @click="runClientDeploy"
            >
              挂载 NFS 客户端
            </Button>
          </Space>
          <BatchNodeResults :results="clientResults" />
        </CollapseContainer>
      </TabPane>
    </Tabs>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Alert, Space, TabPane, Tabs } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { useMessage } from '@/hooks/web/useMessage';
import {
  checkStorageMountBySsh,
  checkStorageStackBySsh,
  deployStorageClientBySsh,
  deployStorageOsdBySsh,
  deployStoragePoolBySsh,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import { NODE_TERM } from '../../utils/constants';
import { runSequentialNodeOps, summarizeBatchResults } from '../../utils/batchNodeOps';
import BatchNodeResults from '../BatchNodeResults/index.vue';
import CephTopologyPanel from '../CephTopologyPanel/index.vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import ClusterScopeBar from '../ClusterScopeBar/index.vue';

defineOptions({ name: 'StorageEnvBatch' });

const props = defineProps<{
  initialNodeIds?: number[];
}>();

const { createMessage } = useMessage();
const route = useRoute();
const router = useRouter();

function resolveStorageTab(): 'topology' | 'ops' {
  const raw = String(route.query.storageTab || '');
  if (raw === 'ops') return 'ops';
  // 兼容旧链接 mediaTab=ceph
  if (String(route.query.mediaTab || '') === 'ceph') return 'topology';
  return 'topology';
}

const innerTab = ref<'topology' | 'ops'>(resolveStorageTab());

const osdSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const poolSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const clientSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();

const osdNodeIds = ref<number[]>([]);
const poolNodeIds = ref<number[]>([]);
const clientNodeIds = ref<number[]>([]);

const osdLoading = ref<'check' | 'deploy' | null>(null);
const poolLoading = ref(false);
const clientLoading = ref<'check' | 'deploy' | null>(null);

const osdResults = ref<WorkloadBundleNodeResult[]>([]);
const poolResults = ref<WorkloadBundleNodeResult[]>([]);
const clientResults = ref<WorkloadBundleNodeResult[]>([]);

watch(
  () => [route.query.storageTab, route.query.mediaTab] as const,
  () => {
    innerTab.value = resolveStorageTab();
  },
);

watch(innerTab, (tab) => {
  const q: Record<string, any> = { ...route.query };
  if (tab === 'ops') q.storageTab = 'ops';
  else q.storageTab = 'topology';
  delete q.mediaTab;
  router.replace({ query: q }).catch(() => undefined);
});

function openBatchOps(nodeId?: number) {
  innerTab.value = 'ops';
  if (nodeId) {
    osdNodeIds.value = [nodeId];
    poolNodeIds.value = [nodeId];
    clientNodeIds.value = [nodeId];
  }
}

watch(
  () => props.initialNodeIds,
  (ids) => {
    if (!ids?.length) return;
    if (innerTab.value === 'ops' && !osdNodeIds.value.length) {
      clientNodeIds.value = [...ids];
    }
  },
  { immediate: true },
);

function handleLaneChange() {
  osdNodeIds.value = [];
  poolNodeIds.value = [];
  clientNodeIds.value = [];
}

const osdNodes = computed(() => osdSelectorRef.value?.selectedNodes ?? []);
const poolNodes = computed(() => poolSelectorRef.value?.selectedNodes ?? []);
const clientNodes = computed(() => clientSelectorRef.value?.selectedNodes ?? []);

async function runOsdCheck() {
  osdLoading.value = 'check';
  osdResults.value = [];
  try {
    const results: WorkloadBundleNodeResult[] = [];
    for (const node of osdNodes.value) {
      if (!node.id) continue;
      try {
        const data = await checkStorageStackBySsh(node.id);
        results.push({
          nodeId: node.id,
          nodeName: node.name,
          host: node.host,
          success: !!data.success,
          message: data.message || (data.osdRunning ? 'NFS 服务端就绪' : 'NFS 服务端未就绪'),
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
    osdResults.value = results;
    const summary = summarizeBatchResults(results);
    summary.success ? createMessage.success(summary.message) : createMessage.warning(summary.message);
  } finally {
    osdLoading.value = null;
  }
}

async function runOsdDeploy() {
  osdLoading.value = 'deploy';
  osdResults.value = [];
  try {
    osdResults.value = await runSequentialNodeOps(osdNodes.value, (nodeId) => deployStorageOsdBySsh(nodeId));
    const summary = summarizeBatchResults(osdResults.value);
    summary.success ? createMessage.success(summary.message) : createMessage.error(summary.message);
  } finally {
    osdLoading.value = null;
  }
}

async function runPoolDeploy() {
  poolLoading.value = true;
  poolResults.value = [];
  try {
    poolResults.value = await runSequentialNodeOps(poolNodes.value, (nodeId) => deployStoragePoolBySsh(nodeId));
    const summary = summarizeBatchResults(poolResults.value);
    summary.success ? createMessage.success(summary.message) : createMessage.error(summary.message);
  } finally {
    poolLoading.value = false;
  }
}

async function runClientCheck() {
  clientLoading.value = 'check';
  clientResults.value = [];
  try {
    const results: WorkloadBundleNodeResult[] = [];
    for (const node of clientNodes.value) {
      if (!node.id) continue;
      try {
        const data = await checkStorageMountBySsh(node.id);
        results.push({
          nodeId: node.id,
          nodeName: node.name,
          host: node.host,
          success: !!data.success,
          message: data.message || (data.mountReady ? '已挂载' : '未挂载'),
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
    clientResults.value = results;
    const summary = summarizeBatchResults(results);
    summary.success ? createMessage.success(summary.message) : createMessage.warning(summary.message);
  } finally {
    clientLoading.value = null;
  }
}

async function runClientDeploy() {
  clientLoading.value = 'deploy';
  clientResults.value = [];
  try {
    clientResults.value = await runSequentialNodeOps(clientNodes.value, (nodeId) =>
      deployStorageClientBySsh(nodeId),
    );
    const summary = summarizeBatchResults(clientResults.value);
    summary.success ? createMessage.success(summary.message) : createMessage.error(summary.message);
  } finally {
    clientLoading.value = null;
  }
}
</script>

<style scoped lang="less">
.storage-env-batch {
  padding: 16px 20px 24px;
  min-height: 480px;

  .storage-inner-tabs {
    :deep(.ant-tabs-nav) {
      margin-bottom: 16px;
    }
  }

  .mb-3 {
    margin-bottom: 12px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
