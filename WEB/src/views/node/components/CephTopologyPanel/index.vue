<template>
  <div class="ceph-topology-panel">
    <div class="toolbar">
      <Space wrap>
        <Button type="default" :loading="assignLoading" @click="runAssignDefaultCluster">
          分配 NFS 集群（默认本机）
        </Button>
        <Button type="primary" :loading="loading" @click="reload">刷新拓扑</Button>
        <Button :disabled="!selected" :loading="checking" @click="runCheckSelected">
          检测选中节点
        </Button>
        <Button
          v-if="selected && isClientKind"
          type="primary"
          ghost
          :loading="opLoading === 'client'"
          :disabled="!canManage"
          @click="runDeployClient"
        >
          挂载 NFS 客户端
        </Button>
        <Button
          v-if="selected && isStorageKind"
          type="primary"
          ghost
          :loading="opLoading === 'osd'"
          :disabled="!canManage"
          @click="runDeployOsd"
        >
          安装 NFS 服务端
        </Button>
        <Button
          v-if="selected && isStorageKind"
          :loading="opLoading === 'pool'"
          :disabled="!canManage"
          @click="runDeployPool"
        >
          初始化 Export
        </Button>
        <Button
          v-if="selected && isClientKind"
          danger
          ghost
          :loading="opLoading === 'unmount'"
          :disabled="!canManage"
          @click="runUnmount"
        >
          卸载挂载
        </Button>
        <Button v-if="selected && !embeddedInStorage" @click="goStorageTab">去分布式存储运维</Button>
        <Button v-if="selected && embeddedInStorage" @click="openBatchOps">打开批量运维</Button>
      </Space>
      <div v-if="summary" class="summary">
        <Tag color="blue">节点 {{ summary.totalNodes ?? 0 }}</Tag>
        <Tag color="purple">存储 {{ summary.storageNodes ?? 0 }}</Tag>
        <Tag color="cyan">客户端 {{ summary.clientNodes ?? 0 }}</Tag>
        <Tag color="success">挂载就绪 {{ summary.mountReadyCount ?? 0 }}</Tag>
        <Tag color="warning">未就绪 {{ summary.mountNotReadyCount ?? 0 }}</Tag>
        <Tag color="default">离线/待纳管 {{ summary.offlineCount ?? 0 }}</Tag>
      </div>
    </div>

    <div class="body">
      <div class="chart-wrap">
        <div ref="chartRef" class="chart"></div>
        <div v-if="!loading && !(topology?.nodes?.length)" class="empty">暂无 NFS 关联节点</div>
      </div>

      <Drawer
        v-model:open="drawerOpen"
        :title="selected ? `${selected.name || ''} (#${selected.nodeId})` : '节点详情'"
        width="420"
        :destroy-on-close="false"
      >
        <template v-if="selected">
          <Descriptions :column="1" size="small" bordered>
            <Descriptions.Item label="角色">{{ kindLabel(selected.kind) }} / {{ selected.nodeRole }}</Descriptions.Item>
            <Descriptions.Item label="主机">{{ selected.host }}:{{ selected.agentPort || 9100 }}</Descriptions.Item>
            <Descriptions.Item label="状态">{{ selected.status || '-' }}</Descriptions.Item>
            <Descriptions.Item label="NFS 挂载">
              <Tag :color="(selected.nfsMountReady ?? selected.cephMountReady) ? 'success' : 'error'">
                {{ (selected.nfsMountReady ?? selected.cephMountReady) ? '就绪' : '未就绪' }}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="挂载根">{{ selected.nfsMountPath || selected.cephMountPath || '-' }}</Descriptions.Item>
            <Descriptions.Item label="告警图">{{ selected.alertImagesDir || '-' }}</Descriptions.Item>
            <Descriptions.Item label="录像">{{ selected.playbacksDir || '-' }}</Descriptions.Item>
            <Descriptions.Item label="抓拍">{{ selected.snapsDir || '-' }}</Descriptions.Item>
            <Descriptions.Item label="NFS 服务端">{{ selected.nfsServerHost || selected.cephMonHost || '-' }}</Descriptions.Item>
            <Descriptions.Item label="Export">{{ selected.nfsExportPath || selected.nfsMountPath || '-' }}</Descriptions.Item>
            <Descriptions.Item label="SSH 凭据">
              {{ selected.sshCredentialConfigured ? '已配置' : '未配置' }}
            </Descriptions.Item>
            <Descriptions.Item label="心跳">{{ selected.lastHeartbeatAt || '-' }}</Descriptions.Item>
          </Descriptions>

          <Alert
            v-if="checkMessage"
            class="mt-3"
            :type="checkOk ? 'success' : 'warning'"
            show-icon
            :message="checkMessage"
          />

          <div class="drawer-actions">
            <Space wrap>
              <Button type="primary" :loading="checking" @click="runCheckSelected">重新检测</Button>
              <Button v-if="embeddedInStorage" @click="openBatchOps">打开批量运维</Button>
              <Button v-else @click="goStorageTab">打开运维面板</Button>
            </Space>
          </div>
        </template>
      </Drawer>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue';
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Alert, Descriptions, Drawer, Space, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useECharts } from '@/hooks/web/useECharts';
import { useMessage } from '@/hooks/web/useMessage';
import {
  checkStorageMountBySsh,
  checkStorageStackBySsh,
  deployStorageClientBySsh,
  deployStorageOsdBySsh,
  deployStoragePoolBySsh,
  assignNfsCluster,
  getCephTopology,
  unmountStorageBySsh,
  type CephTopologyNodeVO,
  type CephTopologyResult,
  type CephTopologySummaryVO,
} from '@/api/device/node';
import { navigateToStorageSubTab } from '../../utils/nodeNavigation';

defineOptions({ name: 'CephTopologyPanel' });

const props = withDefaults(
  defineProps<{
    /** 已嵌入「分布式存储」页时，运维跳转改为切换子 Tab */
    embeddedInStorage?: boolean;
  }>(),
  { embeddedInStorage: false },
);

const emit = defineEmits<{
  (e: 'open-ops', nodeId?: number): void;
}>();

const { createMessage } = useMessage();
const router = useRouter();

const assignLoading = ref(false);
const checking = ref(false);
const opLoading = ref<'client' | 'osd' | 'pool' | 'unmount' | null>(null);
const topology = ref<CephTopologyResult | null>(null);
const summary = ref<CephTopologySummaryVO | null>(null);
const selected = ref<CephTopologyNodeVO | null>(null);
const drawerOpen = ref(false);
const checkMessage = ref('');
const checkOk = ref(false);

const chartRef = ref<HTMLDivElement | null>(null);
const { setOptions, resize, getInstance } = useECharts(chartRef as Ref<HTMLDivElement>);

const isStorageKind = computed(
  () => selected.value?.kind === 'storage_nfs' || selected.value?.kind === 'storage_osd',
);
const isClientKind = computed(
  () =>
    selected.value?.kind === 'nfs_client' ||
    selected.value?.kind === 'ceph_client' ||
    selected.value?.kind === 'platform',
);
const canManage = computed(() => !!selected.value?.sshCredentialConfigured);

function kindLabel(kind?: string) {
  if (kind === 'platform') return '控制面';
  if (kind === 'storage_nfs' || kind === 'storage_osd') return 'NFS 服务端';
  if (kind === 'nfs_client' || kind === 'ceph_client') return 'NFS 客户端';
  return kind || '-';
}

function nodeColor(n: CephTopologyNodeVO) {
  if (n.kind === 'platform') return '#266cfb';
  if (n.status === 'offline' || n.status === 'pending') return '#bfbfbf';
  if (n.nfsMountReady ?? n.cephMountReady) return '#52c41a';
  return '#faad14';
}

function buildChartOption(data: CephTopologyResult) {
  const nodes = (data.nodes || []).map((n) => ({
    id: String(n.nodeId),
    name: `${n.name || n.host}\n${n.host}`,
    symbolSize:
      n.kind === 'platform' ? 72 : n.kind === 'storage_nfs' || n.kind === 'storage_osd' ? 58 : 48,
    category:
      n.kind === 'platform' ? 0 : n.kind === 'storage_nfs' || n.kind === 'storage_osd' ? 1 : 2,
    itemStyle: { color: nodeColor(n) },
    label: {
      show: true,
      formatter: `{b}`,
      fontSize: 11,
      color: '#333',
    },
    raw: n,
  }));
  const links = (data.links || []).map((l) => ({
    source: String(l.sourceNodeId),
    target: String(l.targetNodeId),
    label: {
      show: true,
      formatter: l.relation === 'mon' ? 'MON' : l.relation === 'client_mount' ? '挂载' : '',
      fontSize: 10,
      color: '#999',
    },
    lineStyle: {
      color: l.relation === 'mon' ? '#722ed1' : '#91d5ff',
      curveness: 0.15,
      width: 1.5,
    },
  }));
  return {
    tooltip: {
      formatter: (p: any) => {
        const n = p?.data?.raw as CephTopologyNodeVO | undefined;
        if (!n) return p?.name || '';
        return [
          `<b>${n.name || ''}</b> (#${n.nodeId})`,
          `角色: ${kindLabel(n.kind)} / ${n.nodeRole || '-'}`,
          `主机: ${n.host}`,
          `挂载: ${(n.nfsMountReady ?? n.cephMountReady) ? '就绪' : '未就绪'}`,
          `路径: ${n.nfsMountPath || n.cephMountPath || '-'}`,
          `NFS 服务端: ${n.nfsServerHost || n.cephMonHost || '-'}`,
        ].join('<br/>');
      },
    },
    legend: [
      {
        data: ['控制面', 'NFS 服务端', 'NFS 客户端'],
        bottom: 0,
      },
    ],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories: [{ name: '控制面' }, { name: 'NFS 服务端' }, { name: 'NFS 客户端' }],
        force: { repulsion: 320, edgeLength: [80, 160] },
        data: nodes,
        links,
        emphasis: { focus: 'adjacency' },
      },
    ],
  };
}

async function runAssignDefaultCluster() {
  assignLoading.value = true;
  try {
    const data = await assignNfsCluster({ mountRoot: '/mnt/easyaiot-media' });
    topology.value = data;
    summary.value = data.summary || null;
    createMessage.success('NFS 集群 tags 已分配（未指定服务端时使用平台本机 export）');
    await nextTick();
    setOptions(buildChartOption(data) as any);
  } catch (e: any) {
    createMessage.error(e?.message || '分配 NFS 集群失败');
  } finally {
    assignLoading.value = false;
  }
}

async function reload() {
  loading.value = true;
  checkMessage.value = '';
  try {
    const data = await getCephTopology();
    topology.value = data;
    summary.value = data.summary || null;
    await nextTick();
    setOptions(buildChartOption(data) as any);
    bindChartClick();
  } catch (e: any) {
    createMessage.error(e?.message || '加载 NFS 拓扑失败（请确认 iot-node 已更新并重启）');
  } finally {
    loading.value = false;
    resize();
  }
}

function bindChartClick() {
  const inst = getInstance();
  if (!inst) return;
  inst.off('click');
  inst.on('click', (params: any) => {
    const raw = params?.data?.raw as CephTopologyNodeVO | undefined;
    if (!raw) return;
    selected.value = raw;
    drawerOpen.value = true;
    checkMessage.value = '';
  });
}

async function runCheckSelected() {
  if (!selected.value?.nodeId) return;
  checking.value = true;
  checkMessage.value = '';
  try {
    if (selected.value.kind === 'storage_nfs' || selected.value.kind === 'storage_osd') {
      const r = await checkStorageStackBySsh(selected.value.nodeId);
      checkOk.value = !!r.success && !!(r.nfsHealthy ?? r.cephHealthy);
      checkMessage.value = r.message || (checkOk.value ? 'NFS 服务端健康' : 'NFS 服务端检测未通过');
    } else {
      const r = await checkStorageMountBySsh(selected.value.nodeId);
      checkOk.value = !!r.success && !!r.mountReady;
      checkMessage.value = r.message || (checkOk.value ? 'NFS 挂载就绪' : '挂载未就绪');
      if (selected.value) {
        selected.value = {
          ...selected.value,
          nfsMountReady: !!r.mountReady,
          cephMountReady: !!r.mountReady,
        };
      }
    }
    await reload();
  } catch (e: any) {
    checkOk.value = false;
    checkMessage.value = e?.message || '检测失败';
    createMessage.error(checkMessage.value);
  } finally {
    checking.value = false;
  }
}

async function runDeployClient() {
  if (!selected.value?.nodeId) return;
  opLoading.value = 'client';
  try {
    const r = await deployStorageClientBySsh(selected.value.nodeId);
    if (r.success) createMessage.success(r.message || '客户端挂载完成');
    else createMessage.warning(r.message || '客户端挂载未完全成功');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '挂载失败');
  } finally {
    opLoading.value = null;
  }
}

async function runDeployOsd() {
  if (!selected.value?.nodeId) return;
  opLoading.value = 'osd';
  try {
    const r = await deployStorageOsdBySsh(selected.value.nodeId);
    if (r.success) createMessage.success(r.message || 'OSD 准备完成');
    else createMessage.warning(r.message || 'OSD 准备未完全成功');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || 'OSD 部署失败');
  } finally {
    opLoading.value = null;
  }
}

async function runDeployPool() {
  if (!selected.value?.nodeId) return;
  opLoading.value = 'pool';
  try {
    const r = await deployStoragePoolBySsh(selected.value.nodeId);
    if (r.success) createMessage.success(r.message || 'Export 初始化完成');
    else createMessage.warning(r.message || 'Export 初始化未完全成功');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || 'Pool 部署失败');
  } finally {
    opLoading.value = null;
  }
}

async function runUnmount() {
  if (!selected.value?.nodeId) return;
  opLoading.value = 'unmount';
  try {
    const r = await unmountStorageBySsh(selected.value.nodeId);
    if (r.success) createMessage.success(r.message || '已卸载');
    else createMessage.warning(r.message || '卸载未完全成功');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '卸载失败');
  } finally {
    opLoading.value = null;
  }
}

function goStorageTab() {
  const id = selected.value?.nodeId;
  navigateToStorageSubTab(router, 'topology', id);
}

function openBatchOps() {
  emit('open-ops', selected.value?.nodeId);
}

let ro: ResizeObserver | null = null;
onMounted(async () => {
  await reload();
  if (chartRef.value && typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(() => resize());
    ro.observe(chartRef.value);
  }
});
onUnmounted(() => {
  ro?.disconnect();
  getInstance()?.off('click');
});

watch(
  () => topology.value,
  () => nextTick(() => resize()),
);
</script>

<style scoped lang="less">
.ceph-topology-panel {
  .toolbar {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 12px;
  }
  .summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .body {
    position: relative;
    min-height: 480px;
    background: #fafafa;
    border: 1px solid #ebebeb;
    border-radius: 8px;
  }
  .chart-wrap {
    position: relative;
    height: 520px;
  }
  .chart {
    width: 100%;
    height: 100%;
  }
  .empty {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
  }
  .drawer-actions {
    margin-top: 16px;
  }
  .mt-3 {
    margin-top: 12px;
  }
}
</style>
