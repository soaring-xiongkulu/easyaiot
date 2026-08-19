<template>
  <div class="node-manage">
    <div class="node-manage__panel">
      <div class="node-manage__header">
        <div class="node-manage__header-left">
          <div class="node-manage__title">{{ NODE_TERM.nodeInventory }}</div>
          <div class="node-manage__sub">
            <template v-if="state.viewMode === 'cards'">
              一个中心节点一张卡片；本机卡片可批量维护与组件分发，NFS 请前往流媒体管理
            </template>
            <template v-else>
              平铺查看全部节点；筛选与批量操作请切回卡片视图
            </template>
          </div>
          <div v-if="stats.total" class="node-chipbar">
            <span class="chip">节点 <b>{{ stats.total }}</b></span>
            <span class="chip is-ok">在线 <b>{{ stats.online }}</b></span>
            <span v-if="stats.pending" class="chip is-warn">待纳管 <b>{{ stats.pending }}</b></span>
            <span v-if="stats.offline" class="chip is-bad">离线 <b>{{ stats.offline }}</b></span>
            <span v-if="stats.maintenance" class="chip is-warn">维护 <b>{{ stats.maintenance }}</b></span>
            <span class="chip chip--muted">中心 <b>{{ stats.central }}</b></span>
          </div>
        </div>
        <div class="node-manage__actions">
          <Button type="primary" :preIcon="IconEnum.ADD" @click="handleCreate">
            {{ NODE_TERM.addNode }}
          </Button>
          <Button type="default" preIcon="ant-design:cluster-outlined" @click="handleAddCentral">
            {{ NODE_TERM.addCentralNode }}
          </Button>
          <Button
            :loading="refreshing || lanesLoading"
            preIcon="ant-design:reload-outlined"
            @click="handleRefreshAll"
          >
            刷新
          </Button>
          <Button
            type="default"
            preIcon="ant-design:swap-outlined"
            @click="toggleViewMode"
          >
            {{ NODE_TERM.switchView }}
          </Button>
        </div>
      </div>

      <div class="node-manage__body">
        <ClusterSwimlane
          v-if="state.viewMode === 'cards'"
          :lanes="lanes"
          :loading="lanesLoading"
          @view="handleView"
          @edit="handleEdit"
          @refresh="handleSuccess"
        />

        <div v-else class="node-manage__table">
          <BasicTable @register="registerTable">
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'name'">
                <a class="node-link" @click="handleView(record)">{{ record.name }}</a>
              </template>
              <template v-else-if="column.dataIndex === 'action'">
                <TableAction
                  :actions="[
                    ...(record.status === 'pending'
                      ? [{
                          icon: 'ant-design:rocket-outlined',
                          tooltip: { title: NODE_TERM.continueOnboard, placement: 'top' },
                          onClick: handleContinueOnboard.bind(null, record),
                        }]
                      : []),
                    {
                      icon: IconEnum.VIEW,
                      tooltip: { title: NODE_TERM.viewDetail, placement: 'top' },
                      onClick: handleView.bind(null, record),
                    },
                    ...(isPlatformNode(record)
                      ? []
                      : [{
                          icon: IconEnum.EDIT,
                          tooltip: { title: NODE_TERM.editNode, placement: 'top' },
                          onClick: handleEdit.bind(null, record),
                        }]),
                    ...(isPlatformNode(record)
                      ? []
                      : [{
                          icon: IconEnum.DELETE,
                          tooltip: { title: '删除', placement: 'top' },
                          popConfirm: {
                            placement: 'topRight',
                            title: '确认删除该节点？',
                            confirm: handleDelete.bind(null, record),
                          },
                        }]),
                  ]"
                />
              </template>
            </template>
          </BasicTable>
        </div>
      </div>
    </div>

    <ControlPlanePeerDrawer @register="registerPeerDrawer" @success="handlePeerSuccess" />

    <NodeModal
      @register="registerNodeDrawer"
      @success="handleSuccess"
      @created="handleCreated"
      @host-exists="handleHostExists"
    />
    <NodeDetailDrawer
      ref="detailDrawerRef"
      @register="registerDetailDrawer"
      @edit="handleEdit"
      @maintenance="handleMaintenance"
      @continue-setup="handleContinueOnboard"
      @refresh="handleSuccess"
      @closed="handleDrawerClosed"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { columns, getNodeFormConfig } from '../../Data';
import NodeModal from '../NodeModal/index.vue';
import NodeDetailDrawer from '../NodeDetailDrawer/index.vue';
import ClusterSwimlane from '../ClusterSwimlane/index.vue';
import ControlPlanePeerDrawer from '../ControlPlanePeerModal/index.vue';
import { useClusterLanes } from '../ClusterSwimlane/useClusterLanes';
import { flattenLaneNodes } from '../../utils/clusterLanes';
import { useMessage } from '@/hooks/web/useMessage';
import { useDrawer } from '@/components/Drawer';
import { IconEnum } from '@/enums/appEnum';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { Button } from '@/components/Button';
import {
  deleteNode,
  getNodePage,
  setNodeMaintenance,
  type ComputeNodeVO,
} from '@/api/device/node';
import { NODE_STATUS_MAP, NODE_TERM } from '../../utils/constants';
import { navigateToOnboardService } from '../../utils/nodeNavigation';
import { isPlatformNode } from '../../utils/platformNode';

defineOptions({ name: 'ComputeNodeManage' });

type ViewMode = 'cards' | 'table';

const router = useRouter();
const { createMessage, createConfirm } = useMessage();
const detailDrawerRef = ref<InstanceType<typeof NodeDetailDrawer> | null>(null);
const [registerNodeDrawer, { openDrawer: openNodeDrawer }] = useDrawer();
const [registerDetailDrawer, { openDrawer: openDetailDrawer }] = useDrawer();
const [registerPeerDrawer, { openDrawer: openPeerDrawer }] = useDrawer();

const { loading: lanesLoading, lanes, loadLanes } = useClusterLanes();

const state = reactive<{ viewMode: ViewMode }>({
  viewMode: 'cards',
});

const stats = computed(() => {
  const seen = new Set<number>();
  let total = 0;
  let online = 0;
  let pending = 0;
  let offline = 0;
  let maintenance = 0;

  for (const lane of lanes.value) {
    for (const node of flattenLaneNodes(lane)) {
      if (node.id == null || seen.has(node.id)) continue;
      seen.add(node.id);
      total += 1;
      if (node.status === 'online') online += 1;
      else if (node.status === 'pending') pending += 1;
      else if (node.status === 'offline') offline += 1;
      else if (node.status === 'maintenance') maintenance += 1;
    }
  }

  return { total, online, pending, offline, maintenance, central: lanes.value.length };
});

function toggleViewMode() {
  state.viewMode = state.viewMode === 'cards' ? 'table' : 'cards';
}

function handleAddCentral() {
  openPeerDrawer(true);
}

async function handlePeerSuccess() {
  await loadLanes(1);
  await handleSuccess();
}

const refreshing = ref(false);

async function handleRefreshAll() {
  refreshing.value = true;
  try {
    await loadLanes();
    if (state.viewMode === 'table') await reload();
  } finally {
    refreshing.value = false;
  }
}

async function handleSuccess() {
  await loadLanes();
  if (state.viewMode === 'table') await reload();
  await detailDrawerRef.value?.reloadDetail?.();
}

function handleDrawerClosed() {
  void handleSuccess();
}

function handleCreate() {
  openNodeDrawer(true, { isUpdate: false });
}

function handleEdit(record: Recordable) {
  if (isPlatformNode(record)) {
    createMessage.warning(NODE_TERM.controlPlaneNodeReadonly);
    return;
  }
  openNodeDrawer(true, { record, isUpdate: true });
}

function handleView(record: Recordable) {
  openDetailDrawer(true, { record });
  if (state.viewMode === 'table') reload();
}

function handleCreated(record: ComputeNodeVO) {
  if (record.sentinelAutoDeployStarted) {
    createMessage.success('节点已分配，正在自动离线部署全量 Sentinel 并开始监测');
  }
  void handleSuccess();
  navigateToOnboardService(router, record);
}

function handleContinueOnboard(record: Recordable) {
  navigateToOnboardService(router, record);
}

async function handleHostExists(host: string) {
  let existing: ComputeNodeVO | undefined;
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 1, host });
    existing = res?.data?.list?.[0];
  } catch {
    // ignore
  }
  await handleSuccess();

  if (!existing) {
    createConfirm({
      iconType: 'info',
      title: '该主机地址已存在',
      content: `主机 ${host} 已在系统中注册，请在列表中点击「${NODE_TERM.continueOnboard}」。`,
      okText: '我知道了',
      cancelButtonProps: { style: { display: 'none' } },
    });
    return;
  }

  const statusLabel = NODE_STATUS_MAP[existing.status || '']?.text || existing.status || '未知';
  const isPending = existing.status === 'pending';

  createConfirm({
    iconType: 'info',
    title: '该主机地址已存在',
    content: isPending
      ? `节点「${existing.name}」(${statusLabel})，是否${NODE_TERM.continueOnboard}？`
      : `节点「${existing.name}」(${statusLabel})，是否${NODE_TERM.viewDetail}？`,
    okText: isPending ? NODE_TERM.continueOnboard : NODE_TERM.viewDetail,
    cancelText: '取消',
    onOk: async () => {
      if (isPending) handleContinueOnboard(existing!);
      else handleView(existing!);
    },
  });
}

async function handleDelete(record: Recordable) {
  if (isPlatformNode(record)) {
    createMessage.warning(`${NODE_TERM.controlPlaneNode}不可删除`);
    return;
  }
  await deleteNode(record.id);
  createMessage.success('删除成功');
  await handleSuccess();
}

async function handleMaintenance(record: Recordable, enabled: boolean) {
  if (isPlatformNode(record)) {
    createMessage.warning(NODE_TERM.controlPlaneNodeReadonly);
    return;
  }
  await setNodeMaintenance(record.id, enabled);
  createMessage.success(enabled ? '已进入维护模式' : '已退出维护模式');
  await handleSuccess();
}

const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '',
  api: getNodePage,
  columns,
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getNodeFormConfig(),
  actionColumn: {
    width: 160,
    title: '操作',
    dataIndex: 'action',
    fixed: 'right',
  },
  fetchSetting: {
    pageField: 'pageNo',
    sizeField: 'pageSize',
    listField: 'data.list',
    totalField: 'data.total',
  },
  rowKey: 'id',
});

onMounted(() => {
  void loadLanes(1);
});
</script>

<style lang="less" scoped>
@import '../../utils/node-manage.less';

.node-link {
  color: #266cfb;
  cursor: pointer;
  font-weight: 500;

  &:hover {
    color: #1a5ae8;
  }
}

:deep(.xingyuv-basic-table-action) {
  .ant-btn {
    padding-inline: 6px;
  }
}
</style>
