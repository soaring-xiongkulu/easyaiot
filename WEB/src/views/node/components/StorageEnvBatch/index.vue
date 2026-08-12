<template>
  <div class="storage-env-batch">
    <Tabs
      class="storage-tabs-bar"
      :activeKey="innerTab"
      :animated="{ inkBar: true, tabPane: false }"
      :tabBarGutter="32"
      @tabClick="handleTabClick"
    >
      <TabPane key="topology" :tab="NODE_TERM.storageCephTopology" />
      <TabPane key="ops" :tab="NODE_TERM.storageBatchOps" />
      <TabPane key="files" :tab="NODE_TERM.storageFileOps" />
    </Tabs>

    <div class="storage-tab-content">
      <CephTopologyPanel
        v-if="tabMounted.topology"
        v-show="innerTab === 'topology'"
        embedded-in-storage
        @open-ops="openBatchOps"
        @summary-change="onTopologySummary"
      />

      <div v-if="tabMounted.ops" v-show="innerTab === 'ops'" class="storage-ops">
        <Alert
          v-if="coverageSummary"
          class="mb-3"
          type="info"
          show-icon
          :message="coverageMessage"
        />
        <Space wrap class="mb-3">
          <Button type="primary" ghost :loading="refreshLoading" @click="runBatchRefresh">
            刷新现状
          </Button>
          <Button :loading="coverageLoading" @click="loadCoverage">刷新覆盖率</Button>
        </Space>
        <ClusterScopeBar @lane-change="handleLaneChange" />

        <CollapseContainer
          title="① NFS 服务端（storage 角色）"
          :canExpan="true"
          :defaultExpan="true"
          class="mb-4"
        >
          <ClusterNodeSelector
            ref="osdSelectorRef"
            v-model:selected-node-ids="osdNodeIds"
            role-filter="storage"
            :show-scope-bar="false"
            :initial-node-ids="opsInitialNodeIds"
            placeholder="选择 storage 节点安装 NFS 服务端"
          />
          <Space wrap class="mb-3">
            <Button :loading="osdLoading === 'check'" :disabled="!osdNodeIds.length" @click="runOsdCheck">
              检测 NFS 服务端
            </Button>
            <Button
              type="primary"
              :loading="osdLoading === 'deploy'"
              :disabled="!osdNodeIds.length"
              @click="runOsdDeploy"
            >
              安装 NFS 服务端
            </Button>
          </Space>
          <BatchNodeResults :results="osdResults" />
        </CollapseContainer>

        <CollapseContainer
          title="② Export 初始化（storage 节点）"
          :canExpan="true"
          :defaultExpan="true"
          class="mb-4"
        >
          <ClusterNodeSelector
            ref="poolSelectorRef"
            v-model:selected-node-ids="poolNodeIds"
            role-filter="storage"
            :show-scope-bar="false"
            :initial-node-ids="opsInitialNodeIds"
            placeholder="选择 NFS 服务端节点（通常单选）"
          />
          <Space wrap class="mb-3">
            <Button type="primary" :loading="poolLoading" :disabled="!poolNodeIds.length" @click="runPoolDeploy">
              初始化 Export
            </Button>
          </Space>
          <BatchNodeResults :results="poolResults" />
        </CollapseContainer>

        <CollapseContainer
          title="③ NFS 客户端挂载"
          :canExpan="true"
          :defaultExpan="true"
          class="mb-4"
        >
          <ClusterNodeSelector
            ref="clientSelectorRef"
            v-model:selected-node-ids="clientNodeIds"
            role-filter="cephClient"
            :show-scope-bar="false"
            :initial-node-ids="opsInitialNodeIds"
            placeholder="选择 compute / gpu / hybrid / media 节点挂载 NFS"
          />
          <Space wrap class="mb-3">
            <Button
              :loading="clientLoading === 'check'"
              :disabled="!clientNodeIds.length"
              @click="runClientCheck"
            >
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
      </div>

      <NfsFileBrowser v-if="tabMounted.files" v-show="innerTab === 'files'" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Alert, Space, TabPane, Tabs } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { CollapseContainer } from '@/components/Container';
import { useMessage } from '@/hooks/web/useMessage';
import {
  batchRefreshNfsBySsh,
  checkStorageMountBySsh,
  checkStorageStackBySsh,
  deployStorageClientBySsh,
  deployStorageOsdBySsh,
  deployStoragePoolBySsh,
  getCephTopology,
  type CephTopologySummaryVO,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import { NODE_TERM } from '../../utils/constants';
import { runSequentialNodeOps, summarizeBatchResults } from '../../utils/batchNodeOps';
import {
  useNodePageTabRequest,
  type StorageSubTabKey,
} from '../../utils/useNodePageTab';
import BatchNodeResults from '../BatchNodeResults/index.vue';
import CephTopologyPanel from '../CephTopologyPanel/index.vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import ClusterScopeBar from '../ClusterScopeBar/index.vue';
import NfsFileBrowser from '../NfsFileBrowser/index.vue';

defineOptions({ name: 'StorageEnvBatch' });

const props = defineProps<{
  initialNodeIds?: number[];
}>();

const { createMessage } = useMessage();
const route = useRoute();
const tabRequest = useNodePageTabRequest();

function resolveStorageTab(): StorageSubTabKey {
  const fromReq = tabRequest.value?.storageTab;
  if (fromReq === 'ops' || fromReq === 'files' || fromReq === 'topology') return fromReq;
  const raw = String(route.query.storageTab || '');
  if (raw === 'ops' || raw === 'files') return raw;
  if (String(route.query.mediaTab || '') === 'ceph') return 'topology';
  return 'topology';
}

const innerTab = ref<StorageSubTabKey>(resolveStorageTab());
const tabMounted = reactive({
  topology: innerTab.value === 'topology',
  ops: innerTab.value === 'ops',
  files: innerTab.value === 'files',
});

function ensureTabMounted(tab: StorageSubTabKey) {
  tabMounted[tab] = true;
}

function handleTabClick(key: string | number) {
  const tab = String(key) as StorageSubTabKey;
  if (tab !== 'topology' && tab !== 'ops' && tab !== 'files') return;
  innerTab.value = tab;
  ensureTabMounted(tab);
}

const osdSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const poolSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const clientSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();

const osdNodeIds = ref<number[]>([]);
const poolNodeIds = ref<number[]>([]);
const clientNodeIds = ref<number[]>([]);
const opsFocusNodeId = ref<number | undefined>();

const osdLoading = ref<'check' | 'deploy' | null>(null);
const poolLoading = ref(false);
const clientLoading = ref<'check' | 'deploy' | null>(null);
const refreshLoading = ref(false);
const coverageLoading = ref(false);
const coverageSummary = ref<CephTopologySummaryVO | null>(null);

const osdResults = ref<WorkloadBundleNodeResult[]>([]);
const poolResults = ref<WorkloadBundleNodeResult[]>([]);
const clientResults = ref<WorkloadBundleNodeResult[]>([]);

const opsInitialNodeIds = computed(() => {
  if (opsFocusNodeId.value) return [opsFocusNodeId.value];
  return props.initialNodeIds;
});

const coverageMessage = computed(() => {
  const s = coverageSummary.value;
  if (!s) return '尚未加载 NFS 覆盖率';
  const pct = s.coveragePercent ?? 0;
  const unprobed = s.unprobedCount ?? 0;
  let msg = `客户端挂载覆盖 ${pct}%（就绪 ${s.mountReadyCount ?? 0} / 客户端 ${s.clientNodes ?? 0}）`;
  if (unprobed > 0) msg += `；未探测 ${unprobed}，请点「刷新现状」`;
  if (s.lastProbeAt) msg += `；最近探测 ${s.lastProbeAt}`;
  return msg;
});

function onTopologySummary(s: CephTopologySummaryVO | null) {
  coverageSummary.value = s;
}

async function loadCoverage() {
  coverageLoading.value = true;
  try {
    const data = await getCephTopology();
    coverageSummary.value = data.summary || null;
  } catch {
    coverageSummary.value = null;
  } finally {
    coverageLoading.value = false;
  }
}

async function runBatchRefresh() {
  refreshLoading.value = true;
  try {
    const data = await batchRefreshNfsBySsh({});
    coverageSummary.value = data.topology?.summary || null;
    if (data.success) createMessage.success(data.message || '现状已刷新');
    else createMessage.warning(data.message || '部分节点刷新失败');
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '刷新现状失败');
  } finally {
    refreshLoading.value = false;
  }
}

watch(tabRequest, (req) => {
  if (!req?.storageTab) return;
  if (req.storageTab === 'ops' || req.storageTab === 'files' || req.storageTab === 'topology') {
    innerTab.value = req.storageTab;
    ensureTabMounted(req.storageTab);
  }
  if (req.nodeId) {
    opsFocusNodeId.value = req.nodeId;
    if (req.storageTab === 'ops') {
      osdNodeIds.value = [req.nodeId];
      poolNodeIds.value = [req.nodeId];
      clientNodeIds.value = [req.nodeId];
    }
  }
});

onMounted(() => {
  ensureTabMounted(innerTab.value);
  loadCoverage();
});

function openBatchOps(nodeId?: number) {
  innerTab.value = 'ops';
  ensureTabMounted('ops');
  if (nodeId) {
    opsFocusNodeId.value = nodeId;
    osdNodeIds.value = [nodeId];
    poolNodeIds.value = [nodeId];
    clientNodeIds.value = [nodeId];
  }
}

watch(
  () => props.initialNodeIds,
  (ids) => {
    if (!ids?.length) return;
    if (innerTab.value === 'ops' && !osdNodeIds.value.length && !opsFocusNodeId.value) {
      clientNodeIds.value = [...ids];
    }
  },
  { immediate: true },
);

function handleLaneChange() {
  osdNodeIds.value = [];
  poolNodeIds.value = [];
  clientNodeIds.value = [];
  opsFocusNodeId.value = undefined;
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
  min-height: 480px;

  .storage-tabs-bar {
    background: #fff;
    padding: 0 20px;

    :deep(.ant-tabs-nav) {
      margin-bottom: 0;
    }

    :deep(.ant-tabs-content-holder) {
      display: none;
    }
  }

  .storage-tab-content {
    padding: 16px 20px 24px;
  }

  .mb-3 {
    margin-bottom: 12px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
