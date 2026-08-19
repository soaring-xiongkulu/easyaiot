<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Alert, Tabs } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicTitle } from '@/components/Basic';
import { Description, useDescription } from '@/components/Description';
import { Icon } from '@/components/Icon';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { formatToDateTime } from '@/utils/dateUtil';
import { getNode, testNodeSsh, type ComputeNodeVO } from '@/api/device/node';
import { NODE_DETAIL, formatNodeFunctions, primaryNodeFunction, NODE_TERM, nodeHasAnyFunction, nodeHasFunction } from '../../utils/constants';
import { mediaDetailSchema, mqttDetailSchema, nodeSetupSummarySchema } from '../../Data';
import NodeMetaBadge from '../NodeMetaBadge/index.vue';
import { isPlatformNode } from '../../utils/platformNode';
import SetupOverviewPanel from '../SetupOverviewPanel/index.vue';
import NodeDetailResourcePanel from '../NodeDetailResourcePanel/index.vue';
import NodeSentinelPanel from '../NodeSentinelPanel/index.vue';

defineOptions({ name: 'NodeDetailDrawer' });

type DetailTabKey = 'resource' | 'sentinel' | 'config' | 'access';

const emit = defineEmits([
  'register',
  'edit',
  'maintenance',
  'continueSetup',
  'refresh',
  'closed',
]);

const { createMessage } = useMessage();

const drawerOpen = ref(false);
const testingSsh = ref(false);
const activeTab = ref<DetailTabKey>('resource');
const node = ref<ComputeNodeVO | null>(null);
const metricsLoading = ref(false);
const sentinelPanelRef = ref<InstanceType<typeof NodeSentinelPanel> | null>(null);

const isMediaNode = computed(() => nodeHasAnyFunction(node.value, ['live', 'forward']));

const isMqttNode = computed(() => nodeHasFunction(node.value, 'mqtt'));

const statusAlert = computed(() => {
  const status = node.value?.status;
  if (status === 'pending') {
    return { type: 'warning' as const, message: NODE_DETAIL.pendingMessage, description: NODE_DETAIL.pendingAlert };
  }
  if (status === 'offline') {
    return { type: 'error' as const, message: NODE_DETAIL.offlineMessage, description: NODE_DETAIL.offlineAlert };
  }
  if (status === 'maintenance') {
    return { type: 'warning' as const, message: NODE_DETAIL.maintenanceMessage, description: NODE_DETAIL.maintenanceAlert };
  }
  return null;
});

const isPlatformReadonly = computed(() => isPlatformNode(node.value));

const roleDesc = computed(() => formatNodeFunctions(node.value));

const [registerMediaDesc] = useDescription({
  useCollapse: false,
  bordered: true,
  column: 2,
  schema: mediaDetailSchema,
  data: node,
});

const [registerMqttDesc] = useDescription({
  useCollapse: false,
  bordered: true,
  column: 2,
  schema: mqttDetailSchema,
  data: node,
});

const [registerDrawer, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  drawerOpen.value = true;
  activeTab.value = 'resource';
  setDrawerProps({ showFooter: true, showOkBtn: false, showCancelBtn: false, loading: false });
  const record = data?.record as ComputeNodeVO | undefined;
  if (record) {
    node.value = { ...record };
  }
  if (record?.id) {
    await loadDetail(record.id);
  }
});

function normalizeNodeDetail(res: unknown): ComputeNodeVO | null {
  if (!res || typeof res !== 'object') return null;
  const payload = res as Record<string, unknown>;
  if (payload.id != null || payload.name != null) {
    return payload as ComputeNodeVO;
  }
  const nested = payload.data;
  if (nested && typeof nested === 'object') {
    return nested as ComputeNodeVO;
  }
  return null;
}

async function loadDetail(id: number) {
  metricsLoading.value = true;
  try {
    const res = await getNode(id);
    const detail = normalizeNodeDetail(res);
    if (detail) {
      node.value = detail;
    } else {
      createMessage.warning('节点详情数据格式异常');
    }
  } catch {
    createMessage.error('加载节点详情失败');
  } finally {
    metricsLoading.value = false;
  }
}

async function handleRefresh() {
  if (!node.value?.id) return;
  await loadDetail(node.value.id);
  await sentinelPanelRef.value?.reload?.();
  emit('refresh');
}

async function handleTestSsh() {
  if (!node.value?.id) return;
  testingSsh.value = true;
  try {
    await testNodeSsh(node.value.id);
    createMessage.success('SSH 连接成功');
    await loadDetail(node.value.id);
    emit('refresh');
  } catch {
    createMessage.error('SSH 连接失败');
  } finally {
    testingSsh.value = false;
  }
}

function handleDrawerOpenChange(open: boolean) {
  drawerOpen.value = open;
  if (!open) {
    metricsLoading.value = false;
    setDrawerProps({ loading: false });
    node.value = null;
    activeTab.value = 'resource';
    emit('closed');
  }
}

function handleClose() {
  closeDrawer();
}

defineExpose({
  reloadDetail: () => {
    const id = node.value?.id;
    if (id) return loadDetail(id);
  },
});
</script>

<template>
  <BasicDrawer
    v-bind="$attrs"
    width="1400"
    placement="right"
    destroy-on-close
    root-class-name="node-detail-drawer"
    @register="registerDrawer"
    @open-change="handleDrawerOpenChange"
  >
    <template #title>
      <div v-if="node" class="detail-drawer-header">
        <div class="detail-drawer-header__main">
          <div class="detail-drawer-header__icon">
            <Icon icon="ant-design:desktop-outlined" :size="22" />
          </div>
          <div>
            <BasicTitle span class="detail-drawer-header__title">{{ NODE_DETAIL.title }}</BasicTitle>
            <div class="detail-drawer-header__meta">
              <span>{{ node.name }}</span>
              <span class="meta-sep">·</span>
              <span>{{ node.host }}</span>
              <template v-if="node.lastHeartbeatAt">
                <span class="meta-sep">·</span>
                <span>心跳 {{ formatToDateTime(node.lastHeartbeatAt) }}</span>
              </template>
            </div>
          </div>
        </div>
        <div class="detail-drawer-header__tags">
          <NodeMetaBadge v-if="isPlatformNode(node)" type="scope" size="lg" />
          <NodeMetaBadge type="status" :status="node.status" size="lg" />
          <NodeMetaBadge type="role" :role="primaryNodeFunction(node)" :label="formatNodeFunctions(node)" size="lg" />
        </div>
      </div>
    </template>

    <template #footer>
      <div class="detail-footer">
        <div class="detail-footer__left">
          <Button @click="handleClose">{{ NODE_DETAIL.footerClose }}</Button>
          <Button @click="handleRefresh">{{ NODE_DETAIL.actionRefresh }}</Button>
        </div>
        <div v-if="!isPlatformReadonly" class="detail-footer__right">
          <Button
            v-if="node?.status === 'pending'"
            type="primary"
            @click="emit('continueSetup', node)"
          >
            {{ NODE_DETAIL.actionSetup }}
          </Button>
          <Button @click="emit('edit', node)">{{ NODE_DETAIL.actionEdit }}</Button>
          <Button @click="emit('maintenance', node, node?.status !== 'maintenance')">
            {{ node?.status === 'maintenance' ? '退出维护' : NODE_DETAIL.actionMaintenance }}
          </Button>
        </div>
      </div>
    </template>

    <div v-if="node" class="detail-drawer-content">
      <Alert
        v-if="isPlatformReadonly"
        type="info"
        show-icon
        class="detail-status-alert"
        :message="NODE_TERM.controlPlaneNodeReadonly"
        description="该节点由平台自动纳管，仅支持查看资源指标。监测代理需在宿主机手动启动。"
      />
      <Alert
        v-else-if="statusAlert"
        :type="statusAlert.type"
        show-icon
        class="detail-status-alert"
        :message="statusAlert.message"
        :description="statusAlert.description"
      >
        <template v-if="node.status === 'pending'" #action>
          <Button size="small" type="primary" @click="emit('continueSetup', node)">
            {{ NODE_DETAIL.actionSetup }}
          </Button>
        </template>
      </Alert>

      <Tabs v-model:activeKey="activeTab" class="detail-tabs">
        <Tabs.TabPane :key="'resource'" :tab="NODE_DETAIL.tabResource">
          <div class="detail-tab-pane">
            <p class="detail-tab-hint">{{ NODE_DETAIL.sectionResourceHint }}</p>
            <NodeDetailResourcePanel :node="node" :loading="metricsLoading" />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane v-if="!isPlatformReadonly" :key="'sentinel'" :tab="NODE_DETAIL.tabSentinel">
          <div class="detail-tab-pane">
            <NodeSentinelPanel ref="sentinelPanelRef" :node-id="node.id" />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane v-if="!isPlatformReadonly" :key="'config'" :tab="NODE_DETAIL.tabConfig">
          <div class="detail-tab-pane">
            <Alert v-if="roleDesc" type="info" show-icon class="detail-tab-alert" :message="roleDesc" />
            <div class="setup-desc">
              <Description
                :use-collapse="false"
                bordered
                :column="2"
                :schema="nodeSetupSummarySchema"
                :data="node"
              />
            </div>
            <div v-if="isMediaNode" class="media-desc-block">
              <h4 class="detail-subtitle">{{ NODE_DETAIL.sectionMedia }}</h4>
              <Description @register="registerMediaDesc" />
            </div>
            <div v-if="isMqttNode" class="media-desc-block">
              <h4 class="detail-subtitle">{{ NODE_DETAIL.sectionMqtt }}</h4>
              <Description @register="registerMqttDesc" />
            </div>
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane v-if="!isPlatformReadonly" :key="'access'" :tab="NODE_DETAIL.tabAccess">
          <div class="detail-tab-pane">
            <SetupOverviewPanel
              embedded
              :show-node-info="false"
              :node="node"
              :testing-ssh="testingSsh"
              @edit="emit('edit', node)"
              @test-ssh="handleTestSsh"
            />
          </div>
        </Tabs.TabPane>
      </Tabs>
    </div>
  </BasicDrawer>
</template>

<style lang="less" scoped>
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
  gap: 10px;
  flex-shrink: 0;
}

.detail-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

.detail-status-alert {
  margin-bottom: 0;
}

.detail-tabs {
  :deep(.ant-tabs-nav) {
    margin-bottom: 0;
    padding: 0 4px;
    background: #fff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: @setup-panel-radius;
    box-shadow: @setup-panel-shadow;

    &::before {
      border-bottom: none;
    }
  }

  :deep(.ant-tabs-tab) {
    padding: 12px 20px;
    font-size: 14px;
  }

  :deep(.ant-tabs-content-holder) {
    padding-top: 16px;
  }
}

.detail-tab-pane {
  padding: 20px 24px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: @setup-panel-radius;
  box-shadow: @setup-panel-shadow;
}

.detail-tab-pane--flush {
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.detail-tab-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-tab-hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}

.detail-tab-alert {
  margin-bottom: 16px;
}

.detail-subtitle {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.media-desc-block {
  margin-top: 20px;
  padding-top: 20px;
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
</style>

<style lang="less">
.node-detail-drawer {
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
