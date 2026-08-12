<template>
  <div class="ceph-topology-panel">
    <div class="toolbar">
      <Space wrap>
        <Button type="primary" :loading="assignLoading" @click="runAssignDefaultCluster">
          分配 NFS 集群
        </Button>
        <Button type="primary" ghost :loading="refreshing" @click="runRefreshStatus">
          刷新现状
        </Button>
        <Button :loading="loading" @click="reload">刷新列表</Button>
      </Space>
      <div v-if="summary" class="summary">
        <Tag :color="coverageColor">
          挂载覆盖 {{ coverageReady }}/{{ coverageTotal }}（{{ coveragePercent }}%）
        </Tag>
        <Tag color="blue">节点 {{ summary.totalNodes ?? 0 }}</Tag>
        <Tag color="purple">服务端 {{ summary.storageNodes ?? 0 }}</Tag>
        <Tag color="cyan">客户端 {{ summary.clientNodes ?? 0 }}</Tag>
        <Tag color="success">就绪 {{ summary.mountReadyCount ?? 0 }}</Tag>
        <Tag color="warning">未就绪 {{ summary.mountNotReadyCount ?? 0 }}</Tag>
        <Tag v-if="(summary.unprobedCount ?? 0) > 0" color="orange">
          未探测 {{ summary.unprobedCount }}
        </Tag>
        <Tag color="default">离线/待纳管 {{ summary.offlineCount ?? 0 }}</Tag>
        <span v-if="summary.lastProbeAt" class="probe-hint">最近探测 {{ summary.lastProbeAt }}</span>
      </div>
    </div>

    <Alert
      v-if="coverageWarning"
      class="mb-3"
      type="warning"
      show-icon
      message="NFS 覆盖异常：存在未就绪或未探测节点，可先「刷新现状」再对节点执行检测/挂载。"
    />

    <BasicTable @register="registerTable" class="node-table">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'kind' || column.dataIndex === 'kind'">
          <Tag :color="kindColor(record.kind)">{{ kindLabel(record.kind) }}</Tag>
        </template>
        <template v-else-if="column.key === 'status' || column.dataIndex === 'status'">
          <Tag :color="statusColor(record.status)">{{ record.status || '-' }}</Tag>
        </template>
        <template v-else-if="column.key === 'mount' || column.dataIndex === 'mount'">
          <Tag
            v-if="record.kind !== 'platform'"
            :color="(record.nfsMountReady ?? record.cephMountReady) ? 'success' : 'error'"
          >
            {{ (record.nfsMountReady ?? record.cephMountReady) ? '就绪' : '未就绪' }}
          </Tag>
          <span v-else>-</span>
        </template>
        <template v-else-if="column.key === 'action' || column.dataIndex === 'action'">
          <TableAction
            :actions="buildRowActions(record)"
          />
        </template>
      </template>
    </BasicTable>

    <div class="chart-section">
      <div class="chart-section__head">
        <span class="chart-section__title">拓扑关系图</span>
        <Button type="link" size="small" @click="toggleChart">
          {{ showChart ? '收起' : '展开' }}
        </Button>
      </div>
      <div v-show="showChart" class="chart-wrap">
        <div ref="chartRef" class="chart"></div>
        <div v-if="!loading && !(topology?.nodes?.length)" class="empty">暂无 NFS 关联节点</div>
      </div>
    </div>

    <BasicDrawer
      @register="registerDrawer"
      width="560"
      :show-footer="false"
      :destroy-on-close="false"
      :title="drawerTitle"
    >
      <template v-if="selected">
        <Description
          :use-collapse="false"
          bordered
          :column="1"
          :schema="detailSchema"
          :data="selected"
        />

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
            <Button
              v-if="isClientKind"
              type="primary"
              ghost
              :loading="opLoading === 'client'"
              :disabled="!canManage"
              @click="runDeployClient"
            >
              挂载客户端
            </Button>
            <Button
              v-if="isStorageKind"
              type="primary"
              ghost
              :loading="opLoading === 'osd'"
              :disabled="!canManage"
              @click="runDeployOsd"
            >
              安装服务端
            </Button>
            <Button
              v-if="isStorageKind"
              :loading="opLoading === 'pool'"
              :disabled="!canManage"
              @click="runDeployPool"
            >
              初始化 Export
            </Button>
            <Button
              v-if="isClientKind"
              danger
              ghost
              :loading="opLoading === 'unmount'"
              :disabled="!canManage"
              @click="runUnmount"
            >
              卸载
            </Button>
            <Button v-if="embeddedInStorage" @click="openBatchOps">打开批量运维</Button>
            <Button v-else @click="goStorageTab">打开运维面板</Button>
          </Space>
        </div>

        <div class="op-log-section">
          <div class="op-log-header">
            <span>操作日志</span>
            <Button size="small" :loading="opLogLoading" @click="loadOpLogs">刷新日志</Button>
          </div>
          <div v-if="!opLogs.length && !opLogLoading" class="op-log-empty">暂无日志</div>
          <div v-for="item in opLogs" :key="item.id" class="op-log-item">
            <div class="op-log-meta">
              <Tag :color="item.success ? 'success' : 'error'">{{ item.success ? '成功' : '失败' }}</Tag>
              <span class="op-type">{{ opTypeLabel(item.opType) }}</span>
              <span class="op-time">{{ item.createTime || '-' }}</span>
            </div>
            <div class="op-msg">{{ item.message || '-' }}</div>
            <details v-if="item.steps?.length">
              <summary>步骤明细（{{ item.steps.length }}）</summary>
              <pre>{{ formatSteps(item.steps) }}</pre>
            </details>
          </div>
        </div>
      </template>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue';
import { computed, h, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Alert, Space, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import type { DescItem } from '@/components/Description';
import { Description } from '@/components/Description';
import { BasicDrawer, useDrawer } from '@/components/Drawer';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import type { BasicColumn } from '@/components/Table';
import { useECharts } from '@/hooks/web/useECharts';
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
  getNfsOpLogs,
  unmountStorageBySsh,
  type CephTopologyNodeVO,
  type CephTopologyResult,
  type CephTopologySummaryVO,
  type MediaDeployStepVO,
  type NfsOpLogItem,
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
  (e: 'summary-change', summary: CephTopologySummaryVO | null): void;
}>();

const { createMessage } = useMessage();
const router = useRouter();
const [registerDrawer, { openDrawer, closeDrawer, setDrawerProps }] = useDrawer();

const assignLoading = ref(false);
const loading = ref(false);
const refreshing = ref(false);
const checking = ref(false);
const opLoading = ref<'client' | 'osd' | 'pool' | 'unmount' | null>(null);
const topology = ref<CephTopologyResult | null>(null);
const summary = ref<CephTopologySummaryVO | null>(null);
const selected = ref<CephTopologyNodeVO | null>(null);
const checkMessage = ref('');
const checkOk = ref(false);
const opLogLoading = ref(false);
const opLogs = ref<NfsOpLogItem[]>([]);
const showChart = ref(false);
const chartPainted = ref(false);

const chartRef = ref<HTMLDivElement | null>(null);
const { setOptions, resize, getInstance } = useECharts(chartRef as Ref<HTMLDivElement>);

const tableColumns: BasicColumn[] = [
  { title: '节点', dataIndex: 'name', key: 'name', width: 160, ellipsis: true },
  { title: '主机', dataIndex: 'host', key: 'host', width: 140, ellipsis: true },
  { title: '角色', dataIndex: 'kind', key: 'kind', width: 110 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '挂载', dataIndex: 'mount', key: 'mount', width: 90 },
  {
    title: '挂载根',
    dataIndex: 'nfsMountPath',
    key: 'nfsMountPath',
    ellipsis: true,
    customRender: ({ record }) =>
      record.nfsMountPath || record.cephMountPath || '-',
  },
  {
    title: 'NFS 服务端',
    dataIndex: 'nfsServerHost',
    key: 'nfsServerHost',
    width: 140,
    ellipsis: true,
    customRender: ({ record }) =>
      record.nfsServerHost || record.cephMonHost || '-',
  },
  {
    title: '最近探测',
    dataIndex: 'nfsProbeAt',
    key: 'nfsProbeAt',
    width: 170,
    customRender: ({ text }) => text || '未探测',
  },
  { title: '操作', key: 'action', dataIndex: 'action', width: 260, fixed: 'right' },
];

const [registerTable, { setTableData, setLoading }] = useTable({
  title: 'NFS 关联节点',
  columns: tableColumns,
  pagination: false,
  showIndexColumn: false,
  bordered: true,
  canResize: false,
  immediate: false,
  rowKey: 'nodeId',
  dataSource: [],
});

const coverageTotal = computed(() => summary.value?.clientNodes ?? 0);
const coverageReady = computed(() => {
  const nodes = topology.value?.nodes || [];
  let n = 0;
  for (const node of nodes) {
    if (node.kind === 'nfs_client' || node.kind === 'ceph_client') {
      if (node.nfsMountReady ?? node.cephMountReady) n++;
    }
  }
  return n;
});
const coveragePercent = computed(() => {
  if (summary.value?.coveragePercent != null) return summary.value.coveragePercent;
  const total = coverageTotal.value;
  if (total <= 0) return 0;
  return Math.round((coverageReady.value * 100) / total);
});
const coverageColor = computed(() => {
  const p = coveragePercent.value;
  if (p >= 100) return 'success';
  if (p >= 50) return 'warning';
  return 'error';
});
const coverageWarning = computed(() => {
  const s = summary.value;
  if (!s) return false;
  if ((s.clientNodes ?? 0) <= 0 && (s.storageNodes ?? 0) <= 0) return false;
  return (s.coveragePercent ?? 100) < 100 || (s.mountNotReadyCount ?? 0) > 0 || (s.unprobedCount ?? 0) > 0;
});

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

const drawerTitle = computed(() => {
  if (!selected.value) return '节点详情';
  return `${selected.value.name || ''} (#${selected.value.nodeId})`;
});

const detailSchema = computed<DescItem[]>(() => [
  {
    field: 'kind',
    label: '角色',
    render: (_v, data) => `${kindLabel(data.kind)} / ${data.nodeRole || '-'}`,
  },
  {
    field: 'host',
    label: '主机',
    render: (_v, data) => `${data.host || '-'}:${data.agentPort || 9100}`,
  },
  { field: 'status', label: '状态' },
  {
    field: 'nfsMountReady',
    label: 'NFS 挂载',
    render: (_v, data) =>
      h(
        Tag,
        { color: (data.nfsMountReady ?? data.cephMountReady) ? 'success' : 'error' },
        () => ((data.nfsMountReady ?? data.cephMountReady) ? '就绪' : '未就绪'),
      ),
  },
  {
    field: 'nfsMountPath',
    label: '挂载根',
    render: (_v, data) => data.nfsMountPath || data.cephMountPath || '-',
  },
  { field: 'alertImagesDir', label: '告警图', render: (v) => v || '-' },
  { field: 'playbacksDir', label: '录像', render: (v) => v || '-' },
  { field: 'snapsDir', label: '抓拍', render: (v) => v || '-' },
  {
    field: 'nfsServerHost',
    label: 'NFS 服务端',
    render: (_v, data) => data.nfsServerHost || data.cephMonHost || '-',
  },
  {
    field: 'nfsExportPath',
    label: 'Export',
    render: (_v, data) => data.nfsExportPath || data.nfsMountPath || '-',
  },
  { field: 'nfsMountSource', label: '实际挂载源', render: (v) => v || '-' },
  { field: 'nfsProbeAt', label: '最近探测', render: (v) => v || '未探测' },
  { field: 'nfsProbeSummary', label: '探测摘要', render: (v) => v || '-' },
  {
    field: 'sshCredentialConfigured',
    label: 'SSH 凭据',
    render: (v) => (v ? '已配置' : '未配置'),
  },
  { field: 'lastHeartbeatAt', label: '心跳', render: (v) => v || '-' },
]);

function kindLabel(kind?: string) {
  if (kind === 'platform') return '控制面';
  if (kind === 'storage_nfs' || kind === 'storage_osd') return 'NFS 服务端';
  if (kind === 'nfs_client' || kind === 'ceph_client') return 'NFS 客户端';
  return kind || '-';
}

function kindColor(kind?: string) {
  if (kind === 'platform') return 'blue';
  if (kind === 'storage_nfs' || kind === 'storage_osd') return 'purple';
  return 'cyan';
}

function statusColor(status?: string) {
  if (status === 'online') return 'success';
  if (status === 'offline') return 'error';
  if (status === 'pending' || status === 'maintenance') return 'warning';
  return 'default';
}

function canMount(n: CephTopologyNodeVO) {
  return (
    (n.kind === 'nfs_client' || n.kind === 'ceph_client' || n.kind === 'platform') &&
    !!n.sshCredentialConfigured
  );
}

function canInstallServer(n: CephTopologyNodeVO) {
  return (n.kind === 'storage_nfs' || n.kind === 'storage_osd') && !!n.sshCredentialConfigured;
}

function buildRowActions(record: CephTopologyNodeVO) {
  const actions: Array<{ label: string; onClick: () => void }> = [
    { label: '详情', onClick: () => openNodeDetail(record) },
    { label: '检测', onClick: () => quickCheck(record) },
  ];
  if (canMount(record)) {
    actions.push({ label: '挂载', onClick: () => quickDeployClient(record) });
  }
  if (canInstallServer(record)) {
    actions.push({ label: '装服务端', onClick: () => quickDeployOsd(record) });
  }
  if (props.embeddedInStorage) {
    actions.push({ label: '批量运维', onClick: () => emit('open-ops', record.nodeId) });
  }
  return actions;
}

function opTypeLabel(t?: string) {
  const map: Record<string, string> = {
    refresh: '刷新现状',
    auto_refresh: '定时巡检',
    check_stack: '检测服务端',
    check_mount: '检测挂载',
    deploy_server: '安装服务端',
    deploy_client: '挂载客户端',
    deploy_export: '初始化 Export',
    unmount: '卸载',
    mkdir: '新建目录',
    upload: '上传文件',
    delete: '删除文件',
    rename: '重命名',
  };
  return (t && map[t]) || t || '-';
}

function formatSteps(steps?: MediaDeployStepVO[]) {
  if (!steps?.length) return '';
  return steps.map((s) => `[${s.status || '-'}] ${s.name || ''}\n${s.output || ''}`).join('\n---\n');
}

async function loadOpLogs() {
  if (!selected.value?.nodeId) {
    opLogs.value = [];
    return;
  }
  opLogLoading.value = true;
  try {
    const data = await getNfsOpLogs({ nodeId: selected.value.nodeId, pageNo: 1, pageSize: 20 });
    opLogs.value = data.list || [];
  } catch {
    opLogs.value = [];
  } finally {
    opLogLoading.value = false;
  }
}

function nodeColor(n: CephTopologyNodeVO) {
  if (n.kind === 'platform') return '#266cfb';
  if (n.status === 'offline' || n.status === 'pending') return '#bfbfbf';
  if (!n.nfsProbeAt && !(n.nfsMountReady ?? n.cephMountReady)) return '#d9d9d9';
  if (n.nfsProbeAt && !(n.nfsMountReady ?? n.cephMountReady)) return '#ff4d4f';
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
      formatter: l.relation === 'mon' ? 'MON' : l.relation === 'client_mount' || l.relation === 'nfs_mount' ? '挂载' : '',
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

function paintChart(data: CephTopologyResult) {
  setOptions(buildChartOption(data) as any);
  bindChartClick();
  resize();
  chartPainted.value = true;
  setTimeout(() => resize(), 120);
}

function applyTopology(data: CephTopologyResult) {
  topology.value = data;
  summary.value = data.summary || null;
  emit('summary-change', summary.value);
  const nodes = data.nodes || [];
  nextTick(() => {
    try {
      setTableData(nodes);
      setLoading(false);
    } catch {
      // BasicTable 尚未 register 时忽略，onMounted 会再拉一次
    }
    if (showChart.value) paintChart(data);
  });
}

function toggleChart() {
  showChart.value = !showChart.value;
  if (showChart.value && topology.value) {
    nextTick(() => paintChart(topology.value!));
  }
}

async function runAssignDefaultCluster() {
  assignLoading.value = true;
  try {
    const data = await assignNfsCluster({ mountRoot: '/mnt/easyaiot-media' });
    applyTopology(data);
    createMessage.success('NFS 集群 tags 已分配（未指定服务端时使用平台本机 export）');
  } catch (e: any) {
    createMessage.error(e?.message || '分配 NFS 集群失败');
  } finally {
    assignLoading.value = false;
  }
}

async function runRefreshStatus() {
  refreshing.value = true;
  setLoading(true);
  try {
    const data = await batchRefreshNfsBySsh({});
    if (data.topology) {
      applyTopology(data.topology);
    } else {
      await reload();
    }
    if (data.success) createMessage.success(data.message || '现状已刷新');
    else createMessage.warning(data.message || '部分节点刷新失败');
  } catch (e: any) {
    createMessage.error(e?.message || '刷新现状失败');
  } finally {
    refreshing.value = false;
    setLoading(false);
  }
}

async function reload() {
  loading.value = true;
  setLoading(true);
  checkMessage.value = '';
  try {
    const data = await getCephTopology();
    applyTopology(data);
  } catch (e: any) {
    topology.value = null;
    summary.value = null;
    setTableData([]);
    emit('summary-change', null);
    createMessage.error(e?.message || '加载 NFS 拓扑失败（请确认 iot-node 已更新并重启）');
  } finally {
    loading.value = false;
    setLoading(false);
  }
}

function bindChartClick() {
  const inst = getInstance();
  if (!inst) return;
  inst.off('click');
  inst.on('click', (params: any) => {
    const raw = params?.data?.raw as CephTopologyNodeVO | undefined;
    if (!raw) return;
    openNodeDetail(raw);
  });
}

function openNodeDetail(node: CephTopologyNodeVO) {
  selected.value = node;
  checkMessage.value = '';
  setDrawerProps({ title: drawerTitle.value });
  openDrawer(true);
  loadOpLogs();
}

async function runCheckOnNode(node: CephTopologyNodeVO) {
  if (!node.nodeId) return;
  checking.value = true;
  checkMessage.value = '';
  try {
    if (node.kind === 'storage_nfs' || node.kind === 'storage_osd') {
      const r = await checkStorageStackBySsh(node.nodeId);
      checkOk.value = !!r.success && !!(r.nfsHealthy ?? r.cephHealthy);
      checkMessage.value = r.message || (checkOk.value ? 'NFS 服务端健康' : 'NFS 服务端检测未通过');
    } else {
      const r = await checkStorageMountBySsh(node.nodeId);
      checkOk.value = !!r.success && !!r.mountReady;
      checkMessage.value = r.message || (checkOk.value ? 'NFS 挂载就绪' : '挂载未就绪');
    }
    await reload();
    const refreshed = (topology.value?.nodes || []).find((n) => n.nodeId === node.nodeId);
    if (refreshed) selected.value = refreshed;
    await loadOpLogs();
    if (!checkOk.value) createMessage.warning(checkMessage.value);
    else createMessage.success(checkMessage.value);
  } catch (e: any) {
    checkOk.value = false;
    checkMessage.value = e?.message || '检测失败';
    createMessage.error(checkMessage.value);
  } finally {
    checking.value = false;
  }
}

async function runCheckSelected() {
  if (!selected.value) return;
  await runCheckOnNode(selected.value);
}

async function quickCheck(node: CephTopologyNodeVO) {
  selected.value = node;
  await runCheckOnNode(node);
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

async function quickDeployClient(node: CephTopologyNodeVO) {
  selected.value = node;
  await runDeployClient();
}

async function runDeployOsd() {
  if (!selected.value?.nodeId) return;
  opLoading.value = 'osd';
  try {
    const r = await deployStorageOsdBySsh(selected.value.nodeId);
    if (r.success) createMessage.success(r.message || '服务端准备完成');
    else createMessage.warning(r.message || '服务端准备未完全成功');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '服务端部署失败');
  } finally {
    opLoading.value = null;
  }
}

async function quickDeployOsd(node: CephTopologyNodeVO) {
  selected.value = node;
  await runDeployOsd();
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
    createMessage.error(e?.message || 'Export 初始化失败');
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
  closeDrawer();
  navigateToStorageSubTab(router, 'topology', id);
}

function openBatchOps() {
  closeDrawer();
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
  () => {
    if (showChart.value && chartPainted.value) nextTick(() => resize());
  },
);

watch(drawerTitle, (title) => setDrawerProps({ title }));
</script>

<style scoped lang="less">
.ceph-topology-panel {
  .toolbar {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 12px;
  }

  .summary {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }

  .probe-hint {
    color: #8c8c8c;
    font-size: 12px;
  }

  .node-table {
    margin-bottom: 12px;
  }

  .chart-section {
    margin-top: 8px;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    background: #fff;
  }

  .chart-section__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid #f5f5f5;
  }

  .chart-section__title {
    font-weight: 500;
    color: #262626;
  }

  .chart-wrap {
    position: relative;
    height: 420px;
    background: #fafafa;
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

  .op-log-section {
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px dashed #e8e8e8;
  }

  .op-log-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .op-log-empty {
    color: #999;
    font-size: 13px;
  }

  .op-log-item {
    margin-bottom: 10px;
    padding: 8px 10px;
    background: #fafafa;
    border-radius: 6px;
  }

  .op-log-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 4px;
  }

  .op-type {
    font-weight: 500;
  }

  .op-time {
    color: #8c8c8c;
    font-size: 12px;
  }

  .op-msg {
    font-size: 13px;
    color: #595959;
  }

  .op-log-item pre {
    margin: 6px 0 0;
    max-height: 160px;
    overflow: auto;
    padding: 8px;
    background: #f5f5f5;
    font-size: 12px;
    white-space: pre-wrap;
  }

  .mb-3 {
    margin-bottom: 12px;
  }

  .mt-3 {
    margin-top: 12px;
  }
}
</style>
