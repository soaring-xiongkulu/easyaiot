<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Empty, Pagination, Spin, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  checkStorageMountBySsh,
  checkStorageStackBySsh,
  deployStorageClientBySsh,
  getCephTopology,
  getNfsMultiClusterOverview,
  type CephTopologyNodeVO,
  type CephTopologySummaryVO,
  type NfsClusterVO,
} from '@/api/device/node';
import { NODE_TERM } from '../../utils/constants';
import { navigateToStorageSubTab } from '../../utils/nodeNavigation';

defineOptions({ name: 'NfsClusterSwimlane' });

const emit = defineEmits<{
  'summary-change': [summary: CephTopologySummaryVO | null];
  'open-ops': [nodeId?: number];
}>();

const router = useRouter();
const { createMessage } = useMessage();

type NfsLane = {
  key: string;
  title: string;
  sub?: string;
  mountRoot?: string;
  isActive?: boolean;
  primaryReady?: boolean;
  members: CephTopologyNodeVO[];
  clientReady: number;
  clientTotal: number;
  standbyCount: number;
};

const PAGE_SIZE = 9;
const loading = ref(false);
const actionNodeId = ref<number | null>(null);
const nodes = ref<CephTopologyNodeVO[]>([]);
const summary = ref<CephTopologySummaryVO | null>(null);
const clusters = ref<NfsClusterVO[]>([]);
const page = ref(1);

const lanes = computed<NfsLane[]>(() => buildLanes(nodes.value, clusters.value, summary.value));
const pagedLanes = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE;
  return lanes.value.slice(start, start + PAGE_SIZE);
});

watch(lanes, (list) => {
  const maxPage = Math.max(1, Math.ceil(list.length / PAGE_SIZE) || 1);
  if (page.value > maxPage) page.value = maxPage;
});

function clusterRoleOf(n?: CephTopologyNodeVO | null) {
  const r = (n?.nfsClusterRole || '').toLowerCase();
  if (r === 'primary' || r === 'standby' || r === 'client' || r === 'candidate') return r;
  if (n?.kind === 'nfs_primary' || n?.kind === 'storage_nfs' || n?.kind === 'storage_osd') return 'primary';
  if (n?.kind === 'nfs_standby') return 'standby';
  if (n?.kind === 'nfs_client' || n?.kind === 'ceph_client') return 'client';
  if (n?.isPlatform || n?.kind === 'platform') return 'client';
  return 'candidate';
}

function mountReady(n?: CephTopologyNodeVO | null) {
  return !!(n?.nfsMountReady ?? n?.cephMountReady);
}

function mountLabel(n: CephTopologyNodeVO) {
  const ready = mountReady(n);
  const role = clusterRoleOf(n);
  if (role === 'primary') {
    if (n.nfsExportReady) return 'Export就绪';
    if (ready) return '本机就绪';
    return 'Export未就绪';
  }
  if (role === 'standby') return ready ? '备机就绪' : '备机未就绪';
  if (role === 'candidate') return '未分配';
  if (ready && String(n.nfsMountSource || '').startsWith('local:')) return '本机就绪';
  return ready ? '已挂载' : '未挂载';
}

function mountTone(n: CephTopologyNodeVO) {
  const role = clusterRoleOf(n);
  if (role === 'candidate') return 'default';
  if (role === 'primary') {
    if (n.nfsExportReady) return 'success';
    if (mountReady(n)) return 'processing';
    return 'warning';
  }
  if (mountReady(n) && String(n.nfsMountSource || '').startsWith('local:')) return 'processing';
  return mountReady(n) ? 'success' : 'warning';
}

function roleLabel(n: CephTopologyNodeVO) {
  const role = clusterRoleOf(n);
  if (n.isPlatform || n.kind === 'platform') {
    if (role === 'primary') return '控制面·主';
    if (role === 'client') return '控制面·客';
    return '控制面';
  }
  if (role === 'primary') return '主';
  if (role === 'standby') return '备';
  if (role === 'client') return '客';
  return '候选';
}

function buildLanes(
  allNodes: CephTopologyNodeVO[],
  clusterRows: NfsClusterVO[],
  sum: CephTopologySummaryVO | null,
): NfsLane[] {
  const byId = new Map<number, CephTopologyNodeVO>();
  for (const n of allNodes) {
    if (n.nodeId != null) byId.set(n.nodeId, n);
  }

  if (clusterRows.length) {
    const active = clusterRows.find((c) => c.isActive) || clusterRows[0];
    return clusterRows.map((c, idx) => {
      const members: CephTopologyNodeVO[] = [];
      const seen = new Set<number>();
      const push = (n?: CephTopologyNodeVO | null) => {
        if (!n?.nodeId || seen.has(n.nodeId)) return;
        seen.add(n.nodeId);
        members.push(n);
      };

      push(c.primaryNodeId != null ? byId.get(c.primaryNodeId) : null);
      push(c.standbyNodeId != null ? byId.get(c.standbyNodeId) : null);

      if (c.id === active?.id || clusterRows.length === 1) {
        for (const n of allNodes) {
          const role = clusterRoleOf(n);
          if (role === 'client' || role === 'candidate' || role === 'standby') push(n);
        }
      }

      const clients = members.filter((w) => clusterRoleOf(w) === 'client');
      const standbys = members.filter((w) => clusterRoleOf(w) === 'standby');
      return {
        key: c.laneKey || `cluster-${c.id || idx}`,
        title: c.name || c.laneKey || `集群 ${idx + 1}`,
        sub: c.primaryHost || undefined,
        mountRoot: c.mountRoot || undefined,
        isActive: !!c.isActive,
        primaryReady: c.primaryReady ?? !!(c.primaryNodeId != null && byId.get(c.primaryNodeId)?.nfsExportReady),
        members,
        clientReady: clients.filter((w) => mountReady(w)).length,
        clientTotal: clients.length,
        standbyCount: standbys.length,
      };
    });
  }

  const primary =
    allNodes.find((n) => clusterRoleOf(n) === 'primary') ||
    (sum?.primaryNodeId != null ? byId.get(sum.primaryNodeId) : undefined) ||
    null;
  const members: CephTopologyNodeVO[] = [];
  const seen = new Set<number>();
  const push = (n?: CephTopologyNodeVO | null) => {
    if (!n?.nodeId || seen.has(n.nodeId)) return;
    seen.add(n.nodeId);
    members.push(n);
  };
  push(primary);
  for (const n of allNodes) {
    const role = clusterRoleOf(n);
    if (role === 'standby' || role === 'client' || role === 'candidate' || role === 'primary') push(n);
  }
  if (!members.length) return [];
  const clients = members.filter((w) => clusterRoleOf(w) === 'client');
  return [
    {
      key: 'local',
      title: '本机 NFS 集群',
      sub: primary?.host,
      mountRoot: primary?.nfsMountPath || primary?.cephMountPath,
      isActive: true,
      primaryReady: !!primary?.nfsExportReady,
      members,
      clientReady: clients.filter((w) => mountReady(w)).length,
      clientTotal: clients.length,
      standbyCount: members.filter((w) => clusterRoleOf(w) === 'standby').length,
    },
  ];
}

async function reload() {
  loading.value = true;
  try {
    let topoNodes: CephTopologyNodeVO[] = [];
    let topoSummary: CephTopologySummaryVO | null = null;
    try {
      const topo = await getCephTopology();
      topoNodes = topo?.nodes || [];
      topoSummary = topo?.summary || null;
    } catch (e: unknown) {
      createMessage.error(e instanceof Error ? e.message : '加载 NFS 拓扑失败');
    }

    let overviewClusters: NfsClusterVO[] = [];
    try {
      const overview = await getNfsMultiClusterOverview();
      overviewClusters = overview?.clusters || [];
    } catch {
      overviewClusters = [];
    }

    nodes.value = topoNodes;
    summary.value = topoSummary;
    clusters.value = overviewClusters;
    emit('summary-change', summary.value);
  } finally {
    loading.value = false;
  }
}

async function runCheck(node: CephTopologyNodeVO) {
  if (!node.nodeId) return;
  actionNodeId.value = node.nodeId;
  try {
    const role = clusterRoleOf(node);
    const res =
      role === 'primary' || role === 'standby'
        ? await checkStorageStackBySsh(node.nodeId)
        : await checkStorageMountBySsh(node.nodeId);
    if (res.success) createMessage.success(res.message || '检测完成');
    else createMessage.warning(res.message || '检测未通过');
    await reload();
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '检测失败');
  } finally {
    actionNodeId.value = null;
  }
}

async function runMount(node: CephTopologyNodeVO) {
  if (!node.nodeId) return;
  actionNodeId.value = node.nodeId;
  try {
    const res = await deployStorageClientBySsh(node.nodeId);
    if (res.success) createMessage.success(res.message || '挂载完成');
    else createMessage.warning(res.message || '挂载失败');
    await reload();
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '挂载失败');
  } finally {
    actionNodeId.value = null;
  }
}

function goDeploy(node?: CephTopologyNodeVO) {
  emit('open-ops', node?.nodeId);
  navigateToStorageSubTab(router, 'ops', node?.nodeId);
}

onMounted(() => {
  void reload();
});

defineExpose({ reload });
</script>

<template>
  <div class="nfs-cards">
    <Spin :spinning="loading">
      <div v-if="lanes.length" class="nfs-cards__grid">
        <article
          v-for="lane in pagedLanes"
          :key="lane.key"
          class="nfs-card"
          :class="{ 'nfs-card--active': lane.isActive }"
        >
          <header class="nfs-card__head">
            <div class="nfs-card__head-main">
              <div class="nfs-card__icon">
                <Icon icon="ant-design:cloud-server-outlined" :size="16" />
              </div>
              <div class="nfs-card__titles">
                <div class="nfs-card__title">
                  {{ lane.title }}
                  <Tag v-if="lane.isActive" color="processing">主</Tag>
                  <Tag v-else>从</Tag>
                </div>
                <div class="nfs-card__sub">
                  <template v-if="lane.sub">{{ lane.sub }}</template>
                  <template v-if="lane.mountRoot">
                    <template v-if="lane.sub"> · </template>{{ lane.mountRoot }}
                  </template>
                  <template v-if="!lane.sub && !lane.mountRoot">暂无 Export</template>
                  · Export {{ lane.primaryReady ? '就绪' : '未就绪' }}
                  · 备 {{ lane.standbyCount }}
                  · 客 {{ lane.clientReady }}/{{ lane.clientTotal }}
                </div>
              </div>
            </div>
          </header>

          <div class="nfs-card__body">
            <div v-if="!lane.members.length" class="nfs-card__empty">暂无节点</div>
            <div
              v-for="node in lane.members"
              :key="node.nodeId"
              class="nfs-node"
            >
              <div class="nfs-node__tags">
                <Tag
                  :color="
                    clusterRoleOf(node) === 'primary'
                      ? 'purple'
                      : clusterRoleOf(node) === 'standby'
                        ? 'geekblue'
                        : 'cyan'
                  "
                >
                  {{ roleLabel(node) }}
                </Tag>
                <Tag :color="mountTone(node)">{{ mountLabel(node) }}</Tag>
              </div>
              <div class="nfs-node__main">
                <div class="nfs-node__name">{{ node.name || '-' }}</div>
                <div class="nfs-node__meta">
                  {{ node.host || '-' }}
                  · {{ node.nfsMountPath || node.cephMountPath || '-' }}
                </div>
              </div>
              <div class="nfs-node__ops">
                <Button
                  size="small"
                  type="link"
                  :loading="actionNodeId === node.nodeId"
                  @click="runCheck(node)"
                >
                  检测
                </Button>
                <Button
                  v-if="clusterRoleOf(node) === 'client'"
                  size="small"
                  type="link"
                  :loading="actionNodeId === node.nodeId"
                  @click="runMount(node)"
                >
                  挂载
                </Button>
                <Button size="small" type="link" @click="goDeploy(node)">部署</Button>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-if="lanes.length > PAGE_SIZE" class="nfs-cards__pager">
        <Pagination
          v-model:current="page"
          :total="lanes.length"
          :page-size="PAGE_SIZE"
          size="small"
          :show-size-changer="false"
          :show-total="(total) => `共 ${total} 个集群`"
        />
      </div>

      <Empty
        v-if="!loading && !lanes.length"
        class="nfs-cards__empty"
        :description="`暂无 NFS 集群，请点击「分配并刷新」或先在「${NODE_TERM.storageBatchOps}」纳管节点`"
      />
    </Spin>
  </div>
</template>

<style scoped lang="less">
@import '../../utils/theme.less';

.nfs-cards {
  min-height: 120px;
}

.nfs-cards__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.nfs-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid @node-border;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@node-primary, 28%);
    box-shadow: 0 4px 14px rgba(38, 108, 251, 0.06);
  }
}

.nfs-card--active {
  border-color: fade(@node-primary, 35%);
  box-shadow: inset 2px 0 0 @node-primary;
}

.nfs-card__head {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 8px 10px;
  background: #fafbfd;
  border-bottom: 1px solid @node-border-light;
}

.nfs-card--active .nfs-card__head {
  background: #f3f7ff;
}

.nfs-card__head-main {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.nfs-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #e8f0ff;
  color: @node-primary;
  flex-shrink: 0;
  margin-top: 1px;
}

.nfs-card__titles {
  min-width: 0;
  flex: 1;
}

.nfs-card__title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
  line-height: 1.35;
}

.nfs-card__sub {
  margin-top: 1px;
  font-size: 11px;
  color: @node-text-muted;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nfs-card__body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 0;
}

.nfs-card__empty {
  padding: 16px 10px;
  text-align: center;
  color: @node-text-muted;
  font-size: 12px;
}

.nfs-node {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 6px;
  align-items: center;
  padding: 6px 10px;
  border-top: 1px solid @node-border-light;

  &:first-child {
    border-top: none;
  }
}

.nfs-node__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;

  :deep(.ant-tag) {
    margin: 0;
    line-height: 18px;
    padding: 0 4px;
    font-size: 11px;
  }
}

.nfs-node__main {
  min-width: 0;
}

.nfs-node__name {
  font-size: 12px;
  font-weight: 600;
  color: @node-text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nfs-node__meta {
  margin-top: 0;
  font-size: 11px;
  color: @node-text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nfs-node__ops {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;

  :deep(.ant-btn) {
    padding: 0 4px;
    height: 22px;
    font-size: 12px;
  }
}

.nfs-cards__pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.nfs-cards__empty {
  margin: 28px 0;
}

@media (max-width: 1400px) {
  .nfs-cards__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .nfs-cards__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .nfs-node {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .nfs-node__ops {
    justify-content: flex-start;
  }
}
</style>
