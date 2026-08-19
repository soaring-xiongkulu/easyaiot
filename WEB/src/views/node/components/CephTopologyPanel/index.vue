<template>
  <div class="ceph-topology-panel" :class="{ 'is-topology-only': isTopologyView }">
    <div v-if="!isTopologyView" class="toolbar">
      <Space wrap>
        <template v-if="!embeddedInStorage">
          <Button
            type="primary"
            preIcon="ant-design:cluster-outlined"
            :loading="assignLoading"
            @click="runAssignDefaultCluster"
          >
            分配 NFS 集群
          </Button>
          <Button
            type="default"
            preIcon="ant-design:cloud-sync-outlined"
            :loading="refreshing"
            @click="runRefreshStatus"
          >
            刷新现状
          </Button>
        </template>
        <Button type="default" preIcon="ant-design:reload-outlined" :loading="loading" @click="reload">
          刷新列表
        </Button>
      </Space>
      <div v-if="summary && !embeddedInStorage" class="summary">
        <Tag :color="coverageColor">
          挂载覆盖 {{ coverageReady }}/{{ coverageTotal }}（{{ coveragePercent }}%）
        </Tag>
        <Tag :color="summary.primaryReady ? 'success' : 'warning'">
          主 {{ summary.primaryHost || (summary.primaryCount ? '已指定' : '无') }}
        </Tag>
        <Tag color="purple">备 {{ summary.standbyCount ?? 0 }}</Tag>
        <Tag color="cyan">客户端 {{ summary.clientNodes ?? 0 }}</Tag>
        <Tag v-if="(summary.candidateCount ?? 0) > 0" color="default">
          候选 {{ summary.candidateCount }}
        </Tag>
        <Tag color="warning">未就绪 {{ summary.mountNotReadyCount ?? 0 }}</Tag>
        <span v-if="summary.lastProbeAt" class="probe-hint">最近探测 {{ summary.lastProbeAt }}</span>
      </div>
    </div>

    <BasicTable v-if="!isTopologyView" @register="registerTable" class="node-table">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'kind' || column.dataIndex === 'kind'">
          <Tag :color="kindColor(record.kind)">{{ kindLabel(record) }}</Tag>
        </template>
        <template v-else-if="column.key === 'status' || column.dataIndex === 'status'">
          <Tag :color="statusColor(record.status)">{{ record.status || '-' }}</Tag>
        </template>
        <template v-else-if="column.key === 'mount' || column.dataIndex === 'mount'">
          <Tag :color="mountTone(record)">{{ mountLabel(record) }}</Tag>
        </template>
        <template v-else-if="column.key === 'action' || column.dataIndex === 'action'">
          <TableAction :actions="buildRowActions(record)" />
        </template>
      </template>
    </BasicTable>

    <div v-if="isTopologyView" class="topo-map-section">
      <div class="topo-map-section__head">
        <div>
          <div class="topo-map-section__title">NFS 集群拓扑</div>
          <div class="topo-map-section__sub">圆球拓扑：主节点居中，备机 / 客户端环绕；点击圆球查看详情</div>
        </div>
        <Space wrap>
          <Button size="small" preIcon="ant-design:reload-outlined" :loading="loading" @click="reload">
            刷新
          </Button>
          <Button size="small" type="primary" ghost preIcon="ant-design:setting-outlined" @click="goManage">
            去集群管理
          </Button>
        </Space>
      </div>

      <div v-if="loading && !(topology?.nodes?.length)" class="topo-map__loading">加载拓扑中…</div>
      <div v-else-if="!(topology?.nodes?.length)" class="topo-map__empty">
        <div class="topo-map__empty-title">暂无拓扑节点</div>
        <div class="topo-map__empty-desc">
          请先在「NFS 集群管理」分配主/备/客户端角色，再回到本页查看关系图。
        </div>
        <Button type="primary" size="small" @click="goManage">打开集群管理</Button>
      </div>
      <div v-else class="topo-ball">
        <svg
          class="topo-ball__svg"
          :viewBox="`0 0 ${ballGraph.width} ${ballGraph.height}`"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <marker
              id="nfs-topo-arrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="3"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L7,3 L0,6 Z" fill="#69b1ff" />
            </marker>
            <filter id="nfs-ball-glow" x="-40%" y="-40%" width="180%" height="180%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="rgba(38,108,251,0.22)" />
            </filter>
          </defs>

          <g v-for="link in ballGraph.links" :key="link.key" class="topo-ball__link">
            <path
              :d="link.path"
              fill="none"
              :stroke="link.ready ? '#52c41a' : '#91caff'"
              stroke-width="2"
              stroke-dasharray="6 4"
              marker-end="url(#nfs-topo-arrow)"
            />
            <text :x="link.labelX" :y="link.labelY" class="topo-ball__link-label">
              {{ link.label }}
            </text>
          </g>

          <g
            v-for="ball in ballGraph.nodes"
            :key="ball.id"
            class="topo-ball__node"
            :class="[`is-${ball.role}`, { 'is-active': selected?.nodeId === ball.id }]"
            @click="openNodeDetail(ball.raw)"
          >
            <circle
              :cx="ball.x"
              :cy="ball.y"
              :r="ball.r"
              :fill="ball.fill"
              filter="url(#nfs-ball-glow)"
            />
            <circle
              :cx="ball.x"
              :cy="ball.y"
              :r="ball.r"
              fill="none"
              :stroke="ball.ring"
              stroke-width="3"
              opacity="0.85"
            />
            <text :x="ball.x" :y="ball.y - 5" class="topo-ball__node-role">{{ ball.roleShort }}</text>
            <text :x="ball.x" :y="ball.y + 11" class="topo-ball__node-name">{{ ball.nameShort }}</text>
            <text :x="ball.x" :y="ball.y + ball.r + 16" class="topo-ball__node-host">{{ ball.host }}</text>
            <text :x="ball.x" :y="ball.y + ball.r + 30" class="topo-ball__node-status">{{ ball.status }}</text>
          </g>
        </svg>

        <div class="topo-ball__legend">
          <span><i class="dot dot--primary" />主服务端</span>
          <span><i class="dot dot--standby" />备服务端</span>
          <span><i class="dot dot--client" />客户端</span>
          <span><i class="dot dot--candidate" />候选</span>
          <span class="topo-ball__hint">点击圆球查看详情</span>
        </div>
      </div>
    </div>

    <div v-else-if="showChartSection" class="chart-section">
      <div class="chart-section__head">
        <span class="chart-section__title">拓扑关系图</span>
        <Button type="link" size="small" @click="toggleChart">
          {{ showChart ? '收起' : '展开' }}
        </Button>
      </div>
      <div v-show="showChart" class="chart-wrap">
        <div ref="chartRef" class="chart"></div>
        <div v-if="!loading && !(topology?.nodes?.length)" class="empty">
          <div class="empty__title">暂无拓扑节点</div>
          <div class="empty__desc">请先在「NFS 集群管理」分配主/备/客户端角色，再回到本页查看关系图。</div>
          <Button type="primary" size="small" @click="goManage">打开集群管理</Button>
        </div>
      </div>
    </div>

    <BasicDrawer
      @register="registerDrawer"
      width="680"
      :show-footer="true"
      :destroy-on-close="false"
      root-class-name="nfs-topo-drawer"
    >
      <template #title>
        <div v-if="selected" class="detail-drawer-header">
          <div class="detail-drawer-header__main">
            <div class="detail-drawer-header__icon">
              <Icon :icon="drawerIcon" :size="22" />
            </div>
            <div>
              <BasicTitle span class="detail-drawer-header__title">NFS 节点详情</BasicTitle>
              <div class="detail-drawer-header__meta">
                <span>{{ selected.name || '-' }}</span>
                <span class="meta-sep">·</span>
                <span>{{ selected.host || '-' }}</span>
                <span class="meta-sep">·</span>
                <span>#{{ selected.nodeId }}</span>
              </div>
            </div>
          </div>
          <div class="detail-drawer-header__tags">
            <Tag :color="kindColor(selected.kind)">{{ kindLabel(selected) }}</Tag>
            <Tag :color="mountTone(selected)">{{ mountLabel(selected) }}</Tag>
            <Tag :color="statusColor(selected.status)">{{ selected.status || '-' }}</Tag>
          </div>
        </div>
      </template>

      <template #footer>
        <div class="detail-footer">
          <div class="detail-footer__left">
            <Button @click="closeDrawer">关闭</Button>
            <Button
              v-if="embeddedInStorage && selected && canBrowseFiles(selected)"
              preIcon="ant-design:folder-open-outlined"
              @click="openFiles"
            >
              打开文件
            </Button>
            <Button
              v-if="embeddedInStorage"
              preIcon="ant-design:tool-outlined"
              @click="openBatchOps"
            >
              打开部署
            </Button>
            <Button v-else preIcon="ant-design:tool-outlined" @click="goStorageTab">运维面板</Button>
          </div>
          <div class="detail-footer__right">
            <Button
              type="primary"
              preIcon="ant-design:check-circle-outlined"
              :loading="checking"
              @click="runCheckSelected"
            >
              重新检测
            </Button>
            <Button
              v-if="isClientKind"
              type="primary"
              ghost
              preIcon="ant-design:link-outlined"
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
              preIcon="ant-design:cloud-server-outlined"
              :loading="opLoading === 'osd'"
              :disabled="!canManage"
              @click="runDeployOsd"
            >
              安装服务端
            </Button>
            <Button
              v-if="isStorageKind"
              preIcon="ant-design:database-outlined"
              :loading="opLoading === 'pool'"
              :disabled="!canManage || (selected && clusterRoleOf(selected) !== 'primary')"
              @click="runDeployPool"
            >
              初始化 Export
            </Button>
            <Button
              v-if="selected && canPromote(selected)"
              type="primary"
              ghost
              preIcon="ant-design:arrow-up-outlined"
              @click="quickPromote(selected)"
            >
              升为主
            </Button>
            <Button
              v-if="selected && canSetStandby(selected)"
              preIcon="ant-design:swap-outlined"
              @click="quickSetStandby(selected)"
            >
              设为备
            </Button>
            <Button
              v-if="isClientKind && selected"
              type="primary"
              color="error"
              preIcon="ant-design:disconnect-outlined"
              :loading="opLoading === 'unmount'"
              :disabled="!canManage"
              @click="runUnmount"
            >
              卸载
            </Button>
          </div>
        </div>
      </template>

      <div v-if="selected" class="detail-drawer-content">
        <Alert
          v-if="checkMessage"
          class="detail-status-alert"
          :type="checkOk ? 'success' : 'warning'"
          show-icon
          :message="checkMessage"
        />
        <Alert
          v-else-if="!canManage && !selected.isPlatform"
          type="info"
          show-icon
          class="detail-status-alert"
          message="未配置 SSH"
          description="远程检测 / 挂载 / 部署需要先完成节点纳管并配置 SSH。"
        />

        <div class="detail-section-card">
          <h4 class="detail-subtitle">基本信息</h4>
          <div class="setup-desc">
            <Description
              :use-collapse="false"
              bordered
              :column="1"
              :schema="identitySchema"
              :data="selected"
            />
          </div>
          <div class="media-desc-block">
            <h4 class="detail-subtitle">挂载与探测</h4>
            <div class="setup-desc">
              <Description
                :use-collapse="false"
                bordered
                :column="1"
                :schema="mountSchema"
                :data="selected"
              />
            </div>
          </div>
        </div>

        <div class="detail-section-card">
          <div class="op-log-header">
            <span>操作日志</span>
            <Button size="small" :loading="opLogLoading" @click="loadOpLogs">刷新日志</Button>
          </div>
          <div v-if="!opLogs.length && !opLogLoading" class="op-log-empty">暂无操作日志</div>
          <div v-for="item in opLogs" :key="item.id" class="op-log-item">
            <div class="op-log-meta">
              <Tag :color="item.success ? 'success' : 'error'">{{ item.success ? '成功' : '失败' }}</Tag>
              <span class="op-type">{{ opTypeLabel(item.opType) }}</span>
              <span class="op-time">{{ item.createTime || '-' }}</span>
            </div>
            <div class="op-msg">{{ item.message || '-' }}</div>
            <details v-if="item.steps?.length" class="op-steps">
              <summary>步骤明细（{{ item.steps.length }}）</summary>
              <pre>{{ formatSteps(item.steps) }}</pre>
            </details>
          </div>
        </div>
      </div>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue';
import { computed, h, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Alert, Space, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { BasicTitle } from '@/components/Basic';
import type { DescItem } from '@/components/Description';
import { Description } from '@/components/Description';
import { BasicDrawer, useDrawer } from '@/components/Drawer';
import { Icon } from '@/components/Icon';
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
  promoteNfsPrimary,
  unmountStorageBySsh,
  type CephTopologyNodeVO,
  type CephTopologyResult,
  type CephTopologySummaryVO,
  type MediaDeployStepVO,
  type NfsOpLogItem,
} from '@/api/device/node';
import { navigateToStorageSubTab } from '../../utils/nodeNavigation';
import { formatNodeFunctions } from '../../utils/constants';

defineOptions({ name: 'CephTopologyPanel' });

const props = withDefaults(
  defineProps<{
    /** 已嵌入 NFS 页时，运维跳转改为一级 Tab */
    embeddedInStorage?: boolean;
    /** manage=表格管理；topology=仅拓扑图；all=表格+可折叠图 */
    viewMode?: 'manage' | 'topology' | 'all';
  }>(),
  { embeddedInStorage: false, viewMode: 'all' },
);

const emit = defineEmits<{
  (e: 'open-ops', nodeId?: number): void;
  (e: 'open-files', nodeId?: number): void;
  (e: 'summary-change', summary: CephTopologySummaryVO | null): void;
}>();

const { createMessage } = useMessage();
const router = useRouter();
const [registerDrawer, { openDrawer, closeDrawer }] = useDrawer();

const isTopologyView = computed(() => props.viewMode === 'topology');
const isManageView = computed(() => props.viewMode === 'manage');
const showChartSection = computed(() => !isManageView.value && !isTopologyView.value);

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
const showChart = ref(props.viewMode === 'all');
const chartPainted = ref(false);

const topoNodes = computed(() => topology.value?.nodes || []);
const topoPrimary = computed(
  () => topoNodes.value.find((n) => clusterRoleOf(n) === 'primary') || null,
);
const topoStandbys = computed(() => topoNodes.value.filter((n) => clusterRoleOf(n) === 'standby'));
const topoClients = computed(() => topoNodes.value.filter((n) => clusterRoleOf(n) === 'client'));
const topoCandidates = computed(() =>
  topoNodes.value.filter((n) => {
    const role = clusterRoleOf(n);
    return role !== 'primary' && role !== 'standby' && role !== 'client';
  }),
);

const chartRef = ref<HTMLDivElement | null>(null);
const { setOptions, resize, getInstance } = useECharts(chartRef as Ref<HTMLDivElement>);

const tableColumns: BasicColumn[] = [
  { title: '节点', dataIndex: 'name', key: 'name', width: 160, ellipsis: true },
  { title: '主机', dataIndex: 'host', key: 'host', width: 140, ellipsis: true },
  { title: '角色', dataIndex: 'kind', key: 'kind', width: 130 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '媒体根', dataIndex: 'mount', key: 'mount', width: 110 },
  {
    title: '挂载路径',
    dataIndex: 'nfsMountPath',
    key: 'nfsMountPath',
    ellipsis: true,
    customRender: ({ record }) =>
      record.nfsMountPath || record.cephMountPath || '-',
  },
  {
    title: '存储来源',
    dataIndex: 'nfsServerHost',
    key: 'nfsServerHost',
    width: 150,
    ellipsis: true,
    customRender: ({ record }) => storageSourceLabel(record),
  },
  {
    title: '最近探测',
    dataIndex: 'nfsProbeAt',
    key: 'nfsProbeAt',
    width: 170,
    customRender: ({ text }) => text || '未探测',
  },
  { title: '操作', key: 'action', dataIndex: 'action', width: 280, fixed: 'right' },
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
const coverageReady = computed(() => summary.value?.mountReadyCount ?? 0);
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
const isStorageKind = computed(() => !!selected.value && isServerCapable(selected.value));
const isClientKind = computed(() => !!selected.value && clusterRoleOf(selected.value) === 'client');
const canManage = computed(() => !!selected.value?.sshCredentialConfigured);

const drawerIcon = computed(() => {
  const role = clusterRoleOf(selected.value);
  if (role === 'primary' || role === 'standby') return 'ant-design:cloud-server-outlined';
  if (role === 'client') return 'ant-design:laptop-outlined';
  return 'ant-design:hdd-outlined';
});

const identitySchema = computed<DescItem[]>(() => [
  {
    field: 'kind',
    label: '类型 / 功能',
    render: (_v, data) => `${kindLabel(data)} / ${formatNodeFunctions(data)}`,
  },
  {
    field: 'nfsClusterRole',
    label: '集群角色',
    render: (_v, data) => clusterRoleOf(data) || '-',
  },
  {
    field: 'host',
    label: '主机',
    render: (_v, data) => `${data.host || '-'}:${data.agentPort || 9100}`,
  },
  { field: 'status', label: '状态' },
  {
    field: 'sshCredentialConfigured',
    label: 'SSH',
    render: (v) => (v ? '已配置' : '未配置'),
  },
  { field: 'lastHeartbeatAt', label: '心跳', render: (v) => v || '-' },
]);

const mountSchema = computed<DescItem[]>(() => [
  {
    field: 'storageBackend',
    label: '存储模式',
    render: () => 'NFS',
  },
  {
    field: 'nfsMountReady',
    label: '媒体根状态',
    render: (_v, data) => h(Tag, { color: mountTone(data) }, () => mountLabel(data)),
  },
  {
    field: 'nfsMountPath',
    label: '挂载路径',
    render: (_v, data) => data.nfsMountPath || data.cephMountPath || '-',
  },
  { field: 'alertImagesDir', label: '告警图', render: (v) => v || '-' },
  { field: 'playbacksDir', label: '录像', render: (v) => v || '-' },
  { field: 'snapsDir', label: '抓拍', render: (v) => v || '-' },
  {
    field: 'nfsServerHost',
    label: '存储来源',
    render: (_v, data) => storageSourceLabel(data),
  },
  {
    field: 'nfsExportPath',
    label: '共享路径',
    render: (_v, data) => data.nfsExportPath || data.nfsMountPath || '-',
  },
  { field: 'nfsMountSource', label: '挂载源', render: (v) => v || '-' },
  { field: 'nfsProbeAt', label: '最近探测', render: (v) => v || '-' },
  { field: 'nfsProbeSummary', label: '探测结果', render: (v) => v || '-' },
]);

type BallNode = {
  id: number;
  x: number;
  y: number;
  r: number;
  role: string;
  roleShort: string;
  nameShort: string;
  host: string;
  status: string;
  fill: string;
  ring: string;
  raw: CephTopologyNodeVO;
};

type BallLink = {
  key: string;
  path: string;
  label: string;
  labelX: number;
  labelY: number;
  ready: boolean;
};

function shortText(text: string, max = 10) {
  const t = (text || '').trim();
  if (t.length <= max) return t || '-';
  return `${t.slice(0, max - 1)}…`;
}

function ballRoleShort(role: string) {
  if (role === 'primary') return '主';
  if (role === 'standby') return '备';
  if (role === 'client') return '客';
  return '候';
}

function ballPalette(role: string, ready: boolean) {
  if (role === 'primary') return { fill: '#722ed1', ring: '#b37feb' };
  if (role === 'standby') return { fill: '#2f54eb', ring: '#85a5ff' };
  if (role === 'client') return { fill: ready ? '#13c2c2' : '#fa8c16', ring: ready ? '#87e8de' : '#ffd591' };
  return { fill: '#8c8c8c', ring: '#d9d9d9' };
}

function linkCurve(x1: number, y1: number, x2: number, y2: number) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(1, Math.hypot(dx, dy));
  const ox = (-dy / len) * Math.min(28, len * 0.14);
  const oy = (dx / len) * Math.min(28, len * 0.14);
  const cx = mx + ox;
  const cy = my + oy;
  return {
    path: `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`,
    labelX: cx,
    labelY: cy - 6,
  };
}

const ballGraph = computed(() => {
  // 画布留白充足，圆球居中且不贴边，缩放铺满时更有呼吸感
  const width = 880;
  const height = 520;
  const cx = width / 2;
  const cy = height / 2 - 8;
  const nodes: BallNode[] = [];
  const links: BallLink[] = [];

  const primary = topoPrimary.value;
  const ringNodes = [...topoStandbys.value, ...topoClients.value, ...topoCandidates.value];

  function orbitAngle(count: number, idx: number) {
    if (count <= 1) return 0;
    // 2 个环节点：左右排布
    if (count === 2) return idx === 0 ? Math.PI : 0;
    if (count === 3) {
      const start = (-Math.PI * 2) / 3;
      return start + (idx * (Math.PI * 4)) / 6;
    }
    const start = -Math.PI / 2;
    return start + (idx * Math.PI * 2) / count;
  }

  if (primary) {
    const ready = !!(primary.nfsExportReady || primary.nfsMountReady || primary.cephMountReady);
    const palette = ballPalette('primary', ready);
    nodes.push({
      id: primary.nodeId,
      x: cx,
      y: cy,
      r: 42,
      role: 'primary',
      roleShort: ballRoleShort('primary'),
      nameShort: shortText(primary.name || primary.host || '主', 8),
      host: shortText(primary.host || '-', 18),
      status: mountLabel(primary),
      fill: palette.fill,
      ring: palette.ring,
      raw: primary,
    });
  }

  const orbit = ringNodes.length <= 2 ? 168 : ringNodes.length <= 5 ? 186 : 200;
  ringNodes.forEach((n, idx) => {
    const role = clusterRoleOf(n) || 'candidate';
    const ready = !!(n.nfsMountReady ?? n.cephMountReady);
    const palette = ballPalette(role, ready);
    const angle = orbitAngle(ringNodes.length, idx);
    const x = cx + Math.cos(angle) * orbit;
    const y = cy + Math.sin(angle) * orbit;
    const r = role === 'standby' ? 36 : 34;
    nodes.push({
      id: n.nodeId,
      x,
      y,
      r,
      role,
      roleShort: ballRoleShort(role),
      nameShort: shortText(n.name || n.host || role, 8),
      host: shortText(n.host || '-', 16),
      status: mountLabel(n),
      fill: palette.fill,
      ring: palette.ring,
      raw: n,
    });

    if (primary && (role === 'client' || role === 'standby')) {
      const hub = nodes[0];
      const dist = Math.hypot(x - hub.x, y - hub.y) || 1;
      const sx = hub.x + ((x - hub.x) / dist) * hub.r;
      const sy = hub.y + ((y - hub.y) / dist) * hub.r;
      const tx = x - ((x - hub.x) / dist) * r;
      const ty = y - ((y - hub.y) / dist) * r;
      const curve = linkCurve(sx, sy, tx, ty);
      links.push({
        key: `${hub.id}-${n.nodeId}`,
        path: curve.path,
        label: role === 'standby' ? '备援' : '挂载',
        labelX: curve.labelX,
        labelY: curve.labelY,
        ready,
      });
    }
  });

  // 无主时：节点围成一圈，避免空图
  if (!primary && ringNodes.length) {
    nodes.length = 0;
    links.length = 0;
    const count = ringNodes.length;
    const radius = count === 1 ? 0 : 150;
    ringNodes.forEach((n, idx) => {
      const role = clusterRoleOf(n) || 'candidate';
      const ready = !!(n.nfsMountReady ?? n.cephMountReady);
      const palette = ballPalette(role, ready);
      const angle = orbitAngle(count, idx);
      nodes.push({
        id: n.nodeId,
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
        r: 34,
        role,
        roleShort: ballRoleShort(role),
        nameShort: shortText(n.name || n.host || role, 8),
        host: shortText(n.host || '-', 16),
        status: mountLabel(n),
        fill: palette.fill,
        ring: palette.ring,
        raw: n,
      });
    });
  }

  return { width, height, nodes, links };
});

function clusterRoleOf(n?: CephTopologyNodeVO | null): string {
  if (!n) return '';
  if (n.nfsClusterRole) return n.nfsClusterRole;
  if (n.kind === 'nfs_primary' || n.kind === 'storage_nfs' || n.kind === 'storage_osd') return 'primary';
  if (n.kind === 'nfs_standby') return 'standby';
  if (n.kind === 'nfs_client' || n.kind === 'ceph_client') return 'client';
  if (n.kind === 'nfs_candidate') return 'candidate';
  if (n.kind === 'platform') return isNfsServerNode(n) ? 'primary' : 'client';
  return '';
}

/** 主服务端（当前活跃 Export） */
function isNfsServerNode(n?: CephTopologyNodeVO | null) {
  return clusterRoleOf(n) === 'primary';
}

/** 可安装 NFS 服务端软件：主/备/候选 */
function isServerCapable(n?: CephTopologyNodeVO | null) {
  const role = clusterRoleOf(n);
  return role === 'primary' || role === 'standby' || role === 'candidate';
}

function kindLabel(kindOrNode?: string | CephTopologyNodeVO | null) {
  const n = typeof kindOrNode === 'object' ? kindOrNode : null;
  const role = n ? clusterRoleOf(n) : '';
  const kind = n ? n.kind : (kindOrNode as string | undefined);
  if (kind === 'platform' || n?.isPlatform) {
    if (role === 'primary') return '控制面·主服务端';
    if (role === 'standby') return '控制面·备服务端';
    if (role === 'client') return '控制面·客户端';
    return '控制面';
  }
  if (role === 'primary' || kind === 'nfs_primary' || kind === 'storage_nfs' || kind === 'storage_osd') {
    return '主服务端';
  }
  if (role === 'standby' || kind === 'nfs_standby') return '备服务端';
  if (role === 'candidate' || kind === 'nfs_candidate') return '存储候选';
  if (role === 'client' || kind === 'nfs_client' || kind === 'ceph_client') return '客户端';
  return kind || '-';
}

function storageSourceLabel(n: CephTopologyNodeVO) {
  if (clusterRoleOf(n) === 'primary') {
    return `本机 Export（${n.nfsExportPath || n.nfsMountPath || n.host || '-'}）`;
  }
  if (clusterRoleOf(n) === 'standby') {
    return `备机（主 ${n.nfsServerHost || '-'}）`;
  }
  return n.nfsServerHost || n.cephMonHost || '-';
}

function mountLabel(n: CephTopologyNodeVO) {
  const ready = !!(n.nfsMountReady ?? n.cephMountReady);
  const role = clusterRoleOf(n);
  if (role === 'primary') {
    if (n.nfsExportReady) return 'Export就绪';
    if (ready) return '本机目录就绪';
    return 'Export未就绪';
  }
  if (role === 'standby') return ready ? '备机就绪' : '备机未就绪';
  if (role === 'candidate') return '未分配';
  if (ready && String(n.nfsMountSource || '').startsWith('local:')) return '本机目录就绪';
  return ready ? '已挂载' : '未挂载';
}

function mountTone(n: CephTopologyNodeVO) {
  if (clusterRoleOf(n) === 'candidate') return 'default';
  if (clusterRoleOf(n) === 'primary') {
    if (n.nfsExportReady) return 'success';
    if (n.nfsMountReady ?? n.cephMountReady) return 'processing';
    return 'warning';
  }
  if (clusterRoleOf(n) === 'client' && (n.nfsMountReady ?? n.cephMountReady)
      && String(n.nfsMountSource || '').startsWith('local:')) {
    return 'processing';
  }
  return (n.nfsMountReady ?? n.cephMountReady) ? 'success' : 'warning';
}

function kindColor(kind?: string) {
  if (kind === 'platform') return 'blue';
  if (kind === 'nfs_primary' || kind === 'storage_nfs' || kind === 'storage_osd') return 'purple';
  if (kind === 'nfs_standby') return 'geekblue';
  if (kind === 'nfs_candidate') return 'default';
  return 'cyan';
}

function statusColor(status?: string) {
  if (status === 'online') return 'success';
  if (status === 'offline') return 'error';
  if (status === 'pending' || status === 'maintenance') return 'warning';
  return 'default';
}

function canMount(n: CephTopologyNodeVO) {
  return clusterRoleOf(n) === 'client' && !!n.sshCredentialConfigured;
}

function canBrowseFiles(n: CephTopologyNodeVO) {
  return !!n.sshCredentialConfigured || !!n.isPlatform || n.kind === 'platform';
}

function canInstallServer(n: CephTopologyNodeVO) {
  return isServerCapable(n) && (!!n.sshCredentialConfigured || !!n.isPlatform);
}

function canPromote(n: CephTopologyNodeVO) {
  return clusterRoleOf(n) === 'standby';
}

function canSetStandby(n: CephTopologyNodeVO) {
  return clusterRoleOf(n) === 'candidate' && !!(summary.value?.primaryNodeId);
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
  if (canPromote(record)) {
    actions.push({ label: '升为主', onClick: () => quickPromote(record) });
  }
  if (canSetStandby(record)) {
    actions.push({ label: '设为备', onClick: () => quickSetStandby(record) });
  }
  if (props.embeddedInStorage) {
    actions.push({
      label: 'NFS 节点部署',
      onClick: () => navigateToStorageSubTab(router, 'ops', record.nodeId),
    });
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
    promote_primary: '升为主',
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
  const role = clusterRoleOf(n);
  if (n.status === 'offline') return '#bfbfbf';
  if (role === 'primary') return n.nfsExportReady || (n.nfsMountReady ?? n.cephMountReady) ? '#722ed1' : '#b37feb';
  if (role === 'standby') return '#2f54eb';
  if (n.kind === 'platform') return '#266cfb';
  if (n.nfsMountReady ?? n.cephMountReady) return '#52c41a';
  if (n.nfsProbeAt) return '#fa8c16';
  return '#13c2c2';
}

function buildChartOption(data: CephTopologyResult) {
  const rawNodes = data.nodes || [];
  const primary = rawNodes.find((n) => clusterRoleOf(n) === 'primary');
  const standbys = rawNodes.filter((n) => clusterRoleOf(n) === 'standby');
  const clients = rawNodes.filter((n) => clusterRoleOf(n) === 'client');
  const others = rawNodes.filter((n) => {
    const role = clusterRoleOf(n);
    return role !== 'primary' && role !== 'standby' && role !== 'client';
  });

  const placed: CephTopologyNodeVO[] = [];
  if (primary) placed.push(primary);
  placed.push(...standbys);
  placed.push(...clients);
  for (const n of others) {
    if (!placed.includes(n)) placed.push(n);
  }

  const useFixed = placed.length > 0 && placed.length <= 12;
  const nodes = placed.map((n, idx) => {
    const role = clusterRoleOf(n);
    let x = 360;
    let y = 220;
    if (useFixed) {
      if (role === 'primary' || (n.kind === 'platform' && !primary)) {
        x = 160;
        y = 220;
      } else if (role === 'standby') {
        const si = standbys.indexOf(n);
        x = 160;
        y = 80 + si * 120;
      } else if (role === 'client') {
        const ci = clients.indexOf(n);
        x = 520;
        y = 60 + ci * 90;
      } else {
        x = 340;
        y = 40 + idx * 70;
      }
    }
    return {
      id: String(n.nodeId),
      name: `${n.name || n.host}\n${kindLabel(n)}`,
      symbolSize:
        n.kind === 'platform' || role === 'primary' ? 78 : role === 'standby' ? 62 : 50,
      category:
        role === 'primary' || (n.kind === 'platform' && role !== 'client' && role !== 'standby')
          ? 0
          : role === 'standby'
            ? 1
            : 2,
      x,
      y,
      fixed: useFixed,
      itemStyle: { color: nodeColor(n) },
      label: {
        show: true,
        formatter: `{b}`,
        fontSize: 11,
        color: '#333',
        lineHeight: 15,
      },
      raw: n,
    };
  });

  const links = (data.links || []).map((l) => ({
    source: String(l.sourceNodeId),
    target: String(l.targetNodeId),
    label: {
      show: true,
      formatter:
        l.relation === 'mon'
          ? 'MON'
          : l.relation === 'client_mount' || l.relation === 'nfs_mount'
            ? '挂载'
            : '',
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
          `功能: ${kindLabel(n)} / ${formatNodeFunctions(n)}`,
          `主机: ${n.host}`,
          `挂载: ${(n.nfsMountReady ?? n.cephMountReady) ? '就绪' : '未就绪'}`,
          `路径: ${n.nfsMountPath || n.cephMountPath || '-'}`,
          `NFS 服务端: ${n.nfsServerHost || n.cephMonHost || '-'}`,
        ].join('<br/>');
      },
    },
    legend: [
      {
        data: ['主服务端', '备服务端', '客户端'],
        bottom: 0,
      },
    ],
    series: [
      {
        type: 'graph',
        layout: useFixed ? 'none' : 'force',
        roam: true,
        draggable: true,
        categories: [{ name: '主服务端' }, { name: '备服务端' }, { name: '客户端' }],
        force: useFixed ? undefined : { repulsion: 360, edgeLength: [90, 180] },
        data: nodes,
        links,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 8,
        emphasis: { focus: 'adjacency' },
      },
    ],
  };
}

function paintChart(data: CephTopologyResult) {
  if (isTopologyView.value || !showChart.value) return;
  nextTick(() => {
    const el = chartRef.value;
    if (el && el.offsetHeight < 120) {
      el.style.minHeight = '420px';
    }
    setOptions(buildChartOption(data) as any);
    bindChartClick();
    resize();
    chartPainted.value = true;
    setTimeout(() => resize(), 80);
    setTimeout(() => resize(), 320);
  });
}

function applyTopology(data: CephTopologyResult) {
  topology.value = data;
  summary.value = data.summary || null;
  emit('summary-change', summary.value);
  const nodes = data.nodes || [];
  nextTick(() => {
    if (!isTopologyView.value && !isManageView.value) {
      try {
        setTableData(nodes);
        setLoading(false);
      } catch {
        // BasicTable 尚未 register 时忽略，onMounted 会再拉一次
      }
    }
    if (showChart.value && !isTopologyView.value) paintChart(data);
  });
}

function goManage() {
  navigateToStorageSubTab(router, 'manage');
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
  if (!isTopologyView.value) {
    setLoading(true);
  }
  checkMessage.value = '';
  try {
    const data = await getCephTopology();
    applyTopology(data);
  } catch (e: any) {
    topology.value = null;
    summary.value = null;
    if (!isTopologyView.value) {
      setTableData([]);
    }
    emit('summary-change', null);
    createMessage.error(e?.message || '加载 NFS 拓扑失败（请确认 iot-node 已更新并重启）');
  } finally {
    loading.value = false;
    if (!isTopologyView.value) {
      setLoading(false);
    }
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
  openDrawer(true);
  loadOpLogs();
}

async function runCheckOnNode(node: CephTopologyNodeVO) {
  if (!node.nodeId) return;
  checking.value = true;
  checkMessage.value = '';
  try {
    if (isServerCapable(node) || isNfsServerNode(node)) {
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

async function quickPromote(node: CephTopologyNodeVO) {
  if (!node.nodeId) return;
  try {
    const data = await promoteNfsPrimary(node.nodeId);
    summary.value = data.summary || null;
    topology.value = data;
    setTableData(data.nodes || []);
    emit('summary-change', summary.value);
    createMessage.success('已升为主服务端，请在部署页重新挂载客户端');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '升主失败');
  }
}

async function quickSetStandby(node: CephTopologyNodeVO) {
  const primaryId = summary.value?.primaryNodeId;
  if (!node.nodeId || !primaryId) {
    createMessage.warning('请先分配主服务端');
    return;
  }
  try {
    const data = await assignNfsCluster({
      serverNodeId: primaryId,
      standbyNodeId: node.nodeId,
      mountRoot: '/mnt/easyaiot-media',
    });
    summary.value = data.summary || null;
    topology.value = data;
    setTableData(data.nodes || []);
    emit('summary-change', summary.value);
    createMessage.success('已设为备服务端');
    await reload();
  } catch (e: any) {
    createMessage.error(e?.message || '设为备失败');
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
  navigateToStorageSubTab(router, 'manage', id);
}

function openBatchOps() {
  closeDrawer();
  navigateToStorageSubTab(router, 'ops', selected.value?.nodeId);
}

function openFiles() {
  closeDrawer();
  navigateToStorageSubTab(router, 'files', selected.value?.nodeId);
}

let ro: ResizeObserver | null = null;
onMounted(async () => {
  if (isTopologyView.value) {
    showChart.value = false;
  }
  await reload();
  if (!isTopologyView.value && chartRef.value && typeof ResizeObserver !== 'undefined') {
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
    if (!isTopologyView.value && showChart.value && chartPainted.value) nextTick(() => resize());
  },
);
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
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #999;
    pointer-events: none;
    z-index: 1;
  }

  .empty :deep(.ant-btn) {
    pointer-events: auto;
  }

  .empty__title {
    font-size: 15px;
    font-weight: 600;
    color: #595959;
  }

  .empty__desc {
    max-width: 420px;
    text-align: center;
    font-size: 13px;
    line-height: 1.5;
  }

  &.is-topology-only {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    height: 100%;
  }

  .topo-map-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    background: #fff;
    overflow: hidden;
  }

  .topo-map-section__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    flex-shrink: 0;
    padding: 16px 20px;
    border-bottom: 1px solid #f0f0f0;
  }

  .topo-map-section__title {
    font-size: 15px;
    font-weight: 600;
    color: #262626;
  }

  .topo-map-section__sub {
    margin-top: 4px;
    font-size: 12px;
    color: #8c8c8c;
  }

  .topo-map__loading,
  .topo-map__empty {
    flex: 1;
    min-height: 360px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #8c8c8c;
  }

  .topo-map__empty-title {
    font-size: 15px;
    font-weight: 600;
    color: #595959;
  }

  .topo-map__empty-desc {
    max-width: 420px;
    text-align: center;
    font-size: 13px;
    line-height: 1.5;
  }

  .topo-ball {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    padding: 8px 12px 0;
    background:
      radial-gradient(circle at 50% 44%, rgba(114, 46, 209, 0.06), transparent 42%),
      radial-gradient(circle at 78% 28%, rgba(19, 194, 194, 0.07), transparent 34%),
      linear-gradient(180deg, #f7faff 0%, #fafcff 100%);
  }

  .topo-ball__svg {
    width: 100%;
    flex: 1;
    min-height: 0;
    height: 100%;
  }

  .topo-ball__node {
    cursor: pointer;

    circle {
      transition: transform 0.15s ease, filter 0.15s ease;
      transform-box: fill-box;
      transform-origin: center;
    }

    &:hover circle:first-of-type {
      filter: url(#nfs-ball-glow) brightness(1.06);
    }

    &.is-active circle:last-of-type {
      stroke-width: 4;
      stroke: #266cfb;
    }
  }

  .topo-ball__node-role,
  .topo-ball__node-name {
    fill: #fff;
    text-anchor: middle;
    pointer-events: none;
    font-weight: 700;
  }

  .topo-ball__node-role {
    font-size: 14px;
  }

  .topo-ball__node-name {
    font-size: 11px;
    font-weight: 600;
  }

  .topo-ball__node-host,
  .topo-ball__node-status {
    fill: #595959;
    text-anchor: middle;
    pointer-events: none;
    font-size: 11px;
  }

  .topo-ball__node-status {
    fill: #8c8c8c;
    font-size: 10px;
  }

  .topo-ball__link-label {
    fill: #1677ff;
    font-size: 11px;
    font-weight: 600;
    text-anchor: middle;
    pointer-events: none;
  }

  .topo-ball__legend {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
    flex-shrink: 0;
    padding: 12px 20px 16px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
    color: #595959;
    font-size: 12px;

    span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;

      &--primary { background: #722ed1; }
      &--standby { background: #2f54eb; }
      &--client { background: #13c2c2; }
      &--candidate { background: #8c8c8c; }
    }
  }

  .topo-ball__hint {
    margin-left: auto;
    color: #8c8c8c;
  }

  .mb-3 {
    margin-bottom: 12px;
  }

  .mt-3 {
    margin-top: 12px;
  }
}
</style>

<style scoped lang="less">
@import '../../utils/setup-panel.less';

.detail-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 32px;
}

.detail-drawer-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.detail-drawer-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #eef4ff, #dce8ff);
  color: @node-primary;
  flex-shrink: 0;
}

.detail-drawer-header__title {
  font-size: 18px !important;
  font-weight: 600 !important;
}

.detail-drawer-header__meta {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.meta-sep {
  margin: 0 6px;
}

.detail-drawer-header__tags {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.detail-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-status-alert {
  margin-bottom: 0;
}

.detail-section-card {
  .setup-section-card();
}

.detail-subtitle {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: @node-text-primary;
}

.media-desc-block {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px dashed #f0f0f0;
}

.detail-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-footer__left,
.detail-footer__right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.op-log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-weight: 600;
  color: @node-text-primary;
}

.op-log-empty {
  color: @node-text-muted;
  font-size: 13px;
  padding: 12px 0;
}

.op-log-item {
  margin-bottom: 10px;
  padding: 10px 12px;
  background: #fafafa;
  border: 1px solid @node-border-light;
  border-radius: @node-radius;
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
  color: @node-text-muted;
  font-size: 12px;
}

.op-msg {
  font-size: 13px;
  color: @node-text-secondary;
  line-height: 1.5;
}

.op-steps {
  margin-top: 6px;

  summary {
    cursor: pointer;
    color: @node-primary;
    font-size: 12px;
  }

  pre {
    margin: 6px 0 0;
    max-height: 160px;
    overflow: auto;
    padding: 8px;
    background: #f5f5f5;
    border-radius: 6px;
    font-size: 12px;
    white-space: pre-wrap;
  }
}
</style>

<style lang="less">
.nfs-topo-drawer {
  .ant-drawer-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-body {
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 120px);
  }

  .scrollbar__wrap {
    padding: 20px 24px !important;
  }

  .ant-drawer-footer {
    padding: 12px 24px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }
}
</style>
