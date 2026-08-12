<template>
  <div class="storage-page">
    <div v-if="section === 'manage'" class="storage-manage">
      <div class="storage-manage__panel">
        <div class="storage-manage__header">
          <div class="storage-manage__header-left">
            <div class="storage-manage__title">{{ sectionTitle }}</div>
            <div class="storage-manage__sub">
              一个 NFS 集群一张卡片；「多集群切换与同步」管理主集群与三方 / 客户从集群
            </div>
            <div v-if="coverageSummary" class="storage-chipbar">
              <span class="chip" :class="coverageTone">
                覆盖 <b>{{ coverageSummary.coveragePercent ?? 0 }}%</b>
              </span>
              <span class="chip" :class="coverageSummary.primaryReady ? 'is-ok' : 'is-warn'">
                主 Export
                <b>{{
                  coverageSummary.primaryHost || (coverageSummary.primaryCount ? '已指定' : '-')
                }}</b>
              </span>
              <span class="chip">备 <b>{{ coverageSummary.standbyCount ?? 0 }}</b></span>
              <span class="chip">客 <b>{{ coverageSummary.clientNodes ?? 0 }}</b></span>
              <span class="chip chip--muted" :title="coverageSummary.lastProbeAt || ''">
                探测 {{ formatProbeAt(coverageSummary.lastProbeAt) }}
              </span>
            </div>
          </div>
          <Space wrap class="storage-manage__actions">
            <Button
              type="default"
              preIcon="ant-design:partition-outlined"
              @click="openBridgeDrawer"
            >
              {{ bridgeButtonLabel }}
            </Button>
            <Button
              type="primary"
              preIcon="ant-design:thunderbolt-outlined"
              :loading="actionBusy"
              @click="runAssignAndRefresh"
            >
              分配并刷新
            </Button>
          </Space>
        </div>

        <div class="storage-manage__body">
          <NfsClusterSwimlane
            ref="swimlaneRef"
            @open-ops="goDeploy"
            @summary-change="onTopologySummary"
          />
        </div>
      </div>
    </div>

    <div
      v-else-if="section !== 'files' && section !== 'topology'"
      class="storage-hero"
    >
      <div class="storage-hero__title">{{ sectionTitle }}</div>
      <Button
        type="default"
        preIcon="ant-design:reload-outlined"
        :loading="refreshLoading"
        @click="runBatchRefresh"
      >
        刷新探测
      </Button>
    </div>

    <div
      v-if="section !== 'manage'"
      class="storage-tab-content"
      :class="{
        'storage-tab-content--flush': section === 'topology',
        'storage-tab-content--files': section === 'files',
      }"
    >
      <CephTopologyPanel
        v-if="section === 'topology'"
        embedded-in-storage
        view-mode="topology"
        @open-ops="goDeploy"
        @summary-change="onTopologySummary"
      />

      <div v-else-if="section === 'ops'" class="storage-ops">
        <div class="ops-flow">
          <div class="ops-step">
            <div class="ops-step__head">
              <span class="ops-step__no">1</span>
              <div class="ops-step__title">安装 NFS 服务端（主 / 备）</div>
            </div>
            <ClusterNodeSelector
              ref="osdSelectorRef"
              v-model:selected-node-ids="osdNodeIds"
              role-filter="nfsServer"
              :show-scope-bar="false"
              :include-platform="true"
              :initial-node-ids="opsServerInitialIds"
              placeholder="选择主/备服务端节点"
            />
            <Space wrap>
              <Button
                type="default"
                preIcon="ant-design:check-circle-outlined"
                :loading="osdLoading === 'check'"
                :disabled="!osdNodeIds.length"
                @click="runOsdCheck"
              >
                检测服务端
              </Button>
              <Button
                type="primary"
                preIcon="ant-design:cloud-server-outlined"
                :loading="osdLoading === 'deploy'"
                :disabled="!osdNodeIds.length"
                @click="runOsdDeploy"
              >
                安装服务端
              </Button>
            </Space>
            <BatchNodeResults :results="osdResults" />
          </div>

          <div class="ops-step">
            <div class="ops-step__head">
              <span class="ops-step__no">2</span>
              <div class="ops-step__title">初始化 Export（仅主）</div>
            </div>
            <ClusterNodeSelector
              ref="poolSelectorRef"
              v-model:selected-node-ids="poolNodeIds"
              role-filter="nfsServer"
              :show-scope-bar="false"
              :include-platform="true"
              :initial-node-ids="opsPrimaryInitialIds"
              placeholder="选择主服务端"
            />
            <Space wrap>
              <Button
                type="primary"
                preIcon="ant-design:database-outlined"
                :loading="poolLoading"
                :disabled="!poolNodeIds.length"
                @click="runPoolDeploy"
              >
                初始化 Export
              </Button>
            </Space>
            <BatchNodeResults :results="poolResults" />
          </div>

          <div class="ops-step">
            <div class="ops-step__head">
              <span class="ops-step__no">3</span>
              <div class="ops-step__title">挂载 NFS 客户端</div>
            </div>
            <ClusterNodeSelector
              ref="clientSelectorRef"
              v-model:selected-node-ids="clientNodeIds"
              role-filter="nfsClient"
              :show-scope-bar="false"
              :include-platform="true"
              :exclude-node-ids="clientExcludeNodeIds"
              :initial-node-ids="opsClientInitialIds"
              placeholder="选择客户端节点"
            />
            <Space wrap>
              <Button
                type="default"
                preIcon="ant-design:check-circle-outlined"
                :loading="clientLoading === 'check'"
                :disabled="!clientNodeIds.length"
                @click="runClientCheck"
              >
                检测挂载
              </Button>
              <Button
                type="primary"
                preIcon="ant-design:link-outlined"
                :loading="clientLoading === 'deploy'"
                :disabled="!clientNodeIds.length"
                @click="runClientDeploy"
              >
                挂载客户端
              </Button>
            </Space>
            <BatchNodeResults :results="clientResults" />
          </div>
        </div>
      </div>

      <div v-else-if="section === 'files'" class="storage-files">
        <NfsFileBrowser :initial-node-id="filesFocusNodeId" layout="manager" />
      </div>
    </div>

    <NfsBridgeDrawer @register="registerBridgeDrawer" @changed="onBridgeChanged" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Space } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  assignNfsCluster,
  batchRefreshNfsBySsh,
  checkStorageMountBySsh,
  checkStorageStackBySsh,
  deployStorageClientBySsh,
  deployStorageOsdBySsh,
  deployStoragePoolBySsh,
  getCephTopology,
  getNfsMultiClusterOverview,
  type CephTopologySummaryVO,
  type WorkloadBundleNodeResult,
} from '@/api/device/node';
import { NODE_TERM } from '../../utils/constants';
import { runSequentialNodeOps, summarizeBatchResults } from '../../utils/batchNodeOps';
import { navigateToStorageSubTab } from '../../utils/nodeNavigation';
import type { StorageSubTabKey } from '../../utils/useNodePageTab';
import BatchNodeResults from '../BatchNodeResults/index.vue';
import CephTopologyPanel from '../CephTopologyPanel/index.vue';
import ClusterNodeSelector from '../ClusterNodeSelector/index.vue';
import NfsBridgeDrawer from '../NfsBridgeDrawer/index.vue';
import NfsClusterSwimlane from '../NfsClusterSwimlane/index.vue';
import NfsFileBrowser from '../NfsFileBrowser/index.vue';
import { useDrawer } from '@/components/Drawer';

defineOptions({ name: 'StorageEnvBatch' });

const props = defineProps<{
  /** 对应一级 Tab 能力切片 */
  section: StorageSubTabKey;
  initialNodeIds?: number[];
  focusNodeId?: number;
}>();

const { createMessage } = useMessage();
const router = useRouter();

const sectionTitle = computed(() => {
  if (props.section === 'manage') return NODE_TERM.storageCephTopology;
  if (props.section === 'topology') return NODE_TERM.storageClusterTopology;
  if (props.section === 'ops') return NODE_TERM.storageBatchOps;
  if (props.section === 'files') return NODE_TERM.storageFileOps;
  return NODE_TERM.storageCephTopology;
});

const [registerBridgeDrawer, { openDrawer: openBridgeDrawerInner }] = useDrawer();
const bridgeCount = ref(0);
const bridgeButtonLabel = computed(() => {
  const label = NODE_TERM.storageClusterRelation;
  return bridgeCount.value > 0 ? `${label}（${bridgeCount.value}）` : label;
});

const osdSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const poolSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const clientSelectorRef = ref<InstanceType<typeof ClusterNodeSelector>>();
const swimlaneRef = ref<InstanceType<typeof NfsClusterSwimlane>>();

const osdNodeIds = ref<number[]>([]);
const poolNodeIds = ref<number[]>([]);
const clientNodeIds = ref<number[]>([]);
const opsFocusNodeId = ref<number | undefined>();
const filesFocusNodeId = ref<number | undefined>(props.focusNodeId);

const osdLoading = ref<'check' | 'deploy' | null>(null);
const poolLoading = ref(false);
const clientLoading = ref<'check' | 'deploy' | null>(null);
const assignLoading = ref(false);
const refreshLoading = ref(false);
const coverageSummary = ref<CephTopologySummaryVO | null>(null);

const actionBusy = computed(() => assignLoading.value || refreshLoading.value);

async function runAssignAndRefresh() {
  assignLoading.value = true;
  try {
    const data = await assignNfsCluster({});
    coverageSummary.value = data.summary || null;
    applyDefaultsFromSummary(data.summary || null);
    if (data.nodes?.length) {
      clientNodeIds.value = data.nodes
        .filter((n) => n.nfsClusterRole === 'client' && n.nodeId != null)
        .map((n) => n.nodeId!);
    }
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '分配失败');
    assignLoading.value = false;
    return;
  } finally {
    assignLoading.value = false;
  }

  refreshLoading.value = true;
  try {
    const data = await batchRefreshNfsBySsh({});
    coverageSummary.value = data.topology?.summary || null;
    if (data.success) createMessage.success(data.message || '已分配角色并刷新探测');
    else createMessage.warning(data.message || '角色已分配，部分节点刷新失败');
    void loadBridgeCount();
    swimlaneRef.value?.reload?.();
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '刷新现状失败');
  } finally {
    refreshLoading.value = false;
  }
}

const osdResults = ref<WorkloadBundleNodeResult[]>([]);
const poolResults = ref<WorkloadBundleNodeResult[]>([]);
const clientResults = ref<WorkloadBundleNodeResult[]>([]);

const opsServerInitialIds = computed(() => {
  if (opsFocusNodeId.value) return [opsFocusNodeId.value];
  const ids: number[] = [];
  if (coverageSummary.value?.primaryNodeId) ids.push(coverageSummary.value.primaryNodeId);
  if (coverageSummary.value?.standbyNodeId) ids.push(coverageSummary.value.standbyNodeId);
  if (ids.length) return ids;
  return props.initialNodeIds;
});

const opsPrimaryInitialIds = computed(() => {
  if (coverageSummary.value?.primaryNodeId) return [coverageSummary.value.primaryNodeId];
  if (opsFocusNodeId.value) return [opsFocusNodeId.value];
  return props.initialNodeIds;
});

const opsClientInitialIds = computed(() => {
  if (opsFocusNodeId.value && !clientExcludeNodeIds.value.includes(opsFocusNodeId.value)) {
    return [opsFocusNodeId.value];
  }
  return undefined;
});

const clientExcludeNodeIds = computed(() => {
  const ids: number[] = [];
  if (coverageSummary.value?.primaryNodeId) ids.push(coverageSummary.value.primaryNodeId);
  if (coverageSummary.value?.standbyNodeId) ids.push(coverageSummary.value.standbyNodeId);
  return ids;
});

const coverageTone = computed(() => {
  const pct = coverageSummary.value?.coveragePercent ?? 0;
  if (pct >= 100) return 'is-ok';
  if (pct >= 50) return 'is-warn';
  return 'is-bad';
});

function goDeploy(nodeId?: number) {
  navigateToStorageSubTab(router, 'ops', nodeId);
}

function goFiles(nodeId?: number) {
  navigateToStorageSubTab(router, 'files', nodeId);
}

function onTopologySummary(s: CephTopologySummaryVO | null) {
  coverageSummary.value = s;
  applyDefaultsFromSummary(s);
}

function applyDefaultsFromSummary(s: CephTopologySummaryVO | null) {
  if (!s) return;
  const serverIds: number[] = [];
  if (s.primaryNodeId) serverIds.push(s.primaryNodeId);
  if (s.standbyNodeId) serverIds.push(s.standbyNodeId);
  if (serverIds.length && !osdNodeIds.value.length) {
    osdNodeIds.value = [...serverIds];
  }
  if (s.primaryNodeId && !poolNodeIds.value.length) {
    poolNodeIds.value = [s.primaryNodeId];
  }
}

async function loadCoverage() {
  try {
    const data = await getCephTopology();
    coverageSummary.value = data.summary || null;
    applyDefaultsFromSummary(data.summary || null);
    if (!clientNodeIds.value.length && data.nodes?.length) {
      clientNodeIds.value = data.nodes
        .filter((n) => n.nfsClusterRole === 'client' && n.nodeId != null)
        .map((n) => n.nodeId!);
    }
  } catch {
    coverageSummary.value = null;
  }
}

function onBridgeChanged() {
  void loadCoverage();
  void loadBridgeCount();
  swimlaneRef.value?.reload?.();
}

async function loadBridgeCount() {
  try {
    const overview = await getNfsMultiClusterOverview();
    bridgeCount.value = overview?.bridges?.length || 0;
  } catch {
    bridgeCount.value = 0;
  }
}

function openBridgeDrawer() {
  // 必须传 data，否则 useDrawerInner 的打开回调不会触发
  openBridgeDrawerInner(true, { ts: Date.now() });
}

function formatProbeAt(raw?: string | null) {
  if (!raw) return '-';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) {
    return raw.length > 19 ? raw.slice(0, 19).replace('T', ' ') : raw;
  }
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function runBatchRefresh() {
  refreshLoading.value = true;
  try {
    const data = await batchRefreshNfsBySsh({});
    coverageSummary.value = data.topology?.summary || null;
    if (data.success) createMessage.success(data.message || '现状已刷新');
    else createMessage.warning(data.message || '部分节点刷新失败');
    void loadBridgeCount();
    swimlaneRef.value?.reload?.();
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '刷新现状失败');
  } finally {
    refreshLoading.value = false;
  }
}

function applyFocusNode(nodeId?: number) {
  if (!nodeId) return;
  filesFocusNodeId.value = nodeId;
  if (props.section !== 'ops') {
    opsFocusNodeId.value = nodeId;
    return;
  }
  opsFocusNodeId.value = nodeId;
  const role =
    coverageSummary.value?.primaryNodeId === nodeId
      ? 'primary'
      : coverageSummary.value?.standbyNodeId === nodeId
        ? 'standby'
        : 'client';
  if (role === 'primary' || role === 'standby') {
    osdNodeIds.value = [nodeId];
    if (role === 'primary') poolNodeIds.value = [nodeId];
  } else {
    clientNodeIds.value = [nodeId];
  }
}

watch(
  () => props.focusNodeId,
  (id) => applyFocusNode(id),
  { immediate: true },
);

watch(
  () => props.initialNodeIds,
  (ids) => {
    if (!ids?.length || props.section !== 'ops') return;
    if (!clientNodeIds.value.length && !opsFocusNodeId.value) {
      const excluded = new Set(clientExcludeNodeIds.value);
      clientNodeIds.value = ids.filter((id) => !excluded.has(id));
    }
  },
  { immediate: true },
);

onMounted(() => {
  if (props.section === 'manage' || props.section === 'ops' || props.section === 'topology') {
    loadCoverage();
  }
  if (props.section === 'manage') {
    void loadBridgeCount();
  }
});

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
@import '../../utils/theme.less';

@storage-gutter: 16px;

.storage-page {
  min-height: calc(100vh - 168px);
  height: calc(100vh - 168px);
  background: #fff;
  display: flex;
  flex-direction: column;
}

/* 单一左右边距：标题 / 指标 / 泳道共用，左右贯通 */
.storage-manage {
  flex: 1;
  min-height: 0;
  padding: 12px @storage-gutter 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.storage-manage__panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  padding: 0;
}

.storage-manage__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 0 0 12px;
  flex-shrink: 0;
}

.storage-manage__header-left {
  min-width: 0;
  flex: 1;
}

.storage-manage__title {
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;
  color: @node-text-primary;
}

.storage-manage__sub {
  margin-top: 2px;
  font-size: 12px;
  color: @node-text-muted;
  line-height: 1.5;
}

.storage-manage__actions {
  flex-shrink: 0;
}

.storage-chipbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid @node-border;
  background: #fafafa;
  font-size: 12px;
  color: @node-text-muted;
  line-height: 20px;

  b {
    color: @node-text-primary;
    font-weight: 600;
  }
}

.chip.is-ok b {
  color: #389e0d;
}

.chip.is-warn b {
  color: #d48806;
}

.chip.is-bad b {
  color: #cf1322;
}

.chip--muted {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.storage-manage__body {
  flex: 1;
  min-height: 0;
  padding: 0;
  display: flex;
  flex-direction: column;

  :deep(.nfs-swimlane) {
    flex: 1;
    min-height: 0;
  }
}

.storage-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px @storage-gutter 8px;
  background: #fff;
}

.storage-hero__title {
  font-size: 16px;
  font-weight: 500;
  color: @node-text-primary;
}

.storage-tab-content {
  flex: 1;
  min-height: 0;
  padding: 16px @storage-gutter 24px;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.storage-tab-content--flush {
  flex: 1;
  min-height: 0;
  padding: 12px @storage-gutter 16px;
  display: flex;
  flex-direction: column;

  :deep(.ceph-topology-panel) {
    flex: 1;
    min-height: 0;
    height: 100%;
  }
}

.storage-tab-content--files {
  padding: 12px @storage-gutter 16px;
}

.storage-files {
  flex: 1;
  min-height: calc(100vh - 180px);
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.nfs-file-ops) {
    flex: 1;
    min-height: 0;
    height: 100%;
  }
}

.ops-flow {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ops-step {
  padding: 14px 16px;
  border: 1px solid @node-border;
  border-radius: 8px;
  background: #fff;
}

.ops-step__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.ops-step__no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: @node-primary-light;
  color: @node-primary;
  font-size: 12px;
  font-weight: 600;
}

.ops-step__title {
  font-size: 14px;
  font-weight: 600;
  color: @node-text-primary;
}

@media (max-width: 900px) {
  .storage-manage__header {
    flex-direction: column;
  }
}
</style>
