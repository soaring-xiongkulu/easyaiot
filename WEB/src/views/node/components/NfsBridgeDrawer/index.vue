<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import { Input, Select, Space, Spin, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Icon } from '@/components/Icon';
import { BasicModal, useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import {
  activateNfsCluster,
  createNfsBridge,
  getNfsMultiClusterOverview,
  runNfsBridge,
  stopNfsBridge,
  type NfsBridgeVO,
  type NfsClusterVO,
  type NfsMultiClusterOverview,
} from '@/api/device/node';

defineOptions({ name: 'NfsBridgeDrawer' });

const emit = defineEmits<{
  (e: 'register', ...args: any[]): void;
  (e: 'changed'): void;
}>();

const { createMessage } = useMessage();
const [registerDrawer, { closeDrawer, setDrawerProps, getOpen }] = useDrawerInner(async () => {
  setDrawerProps({ confirmLoading: false });
  await reload();
});
const [registerCreateModal, { openModal: openCreateModal, setModalProps, closeModal }] = useModal();

const loading = ref(false);
const loadedOnce = ref(false);
const overview = ref<NfsMultiClusterOverview | null>(null);
const activatingId = ref<number | null>(null);
const runningId = ref<number | null>(null);
const stoppingId = ref<number | null>(null);
const createForm = reactive({
  targetClusterId: undefined as number | undefined,
  sourceRelPaths: 'alert_images,playbacks,snaps',
  targetRelPath: '',
});

const activeCluster = computed(
  () => (overview.value?.clusters || []).find((c) => c.isActive) || null,
);

const slaveClusters = computed(() => (overview.value?.clusters || []).filter((c) => !c.isActive));

const canCreateBridge = computed(
  () => !!activeCluster.value && slaveClusters.value.length > 0,
);

const defaultTargetRel = computed(() =>
  activeCluster.value?.id ? `_bridge/${activeCluster.value.id}` : '_bridge/{sourceId}',
);

const targetClusterOptions = computed(() =>
  slaveClusters.value
    .filter((c) => c.id != null)
    .map((c) => ({
      label: `${c.name || c.laneKey} (${c.primaryHost || '-'})`,
      value: c.id!,
    })),
);

const enabledBridges = computed(() =>
  (overview.value?.bridges || []).filter((b) => b.enabled !== false && b.status !== 'stopped'),
);

const bridgeCount = computed(() => overview.value?.bridges?.length || 0);
const clusterCount = computed(() => overview.value?.clusters?.length || 0);

const FLOW_TARGET_VISIBLE = 4;

const sourceFlowRow = computed(() => {
  const c = activeCluster.value;
  if (!c) return null;
  return {
    name: c.name || c.laneKey || '未命名',
    host: c.primaryHost || c.primaryName || '-',
    extra: c.mountRoot || '',
    ready: c.primaryReady,
  };
});

const targetFlowRows = computed(() =>
  slaveClusters.value.map((c) => ({
    id: c.id,
    name: c.name || c.laneKey || '未命名',
    host: c.primaryHost || c.primaryName || '-',
    ready: c.primaryReady,
  })),
);

const targetFlowOverflow = computed(() =>
  Math.max(0, targetFlowRows.value.length - FLOW_TARGET_VISIBLE),
);

watch(
  () => getOpen.value,
  (open) => {
    if (open) void reload();
  },
);

function bridgeTone(b: NfsBridgeVO) {
  if (b.status === 'running') return 'processing';
  if (b.status === 'error') return 'error';
  if (b.status === 'stopped') return 'default';
  if (b.lastSuccess === false) return 'warning';
  if (b.lastSuccess) return 'success';
  return 'blue';
}

function bridgeStatusText(b: NfsBridgeVO) {
  if (b.status === 'running') return '同步中';
  if (b.status === 'stopped' || b.enabled === false) return '已停止';
  if (b.status === 'error' || b.lastSuccess === false) return '失败';
  if (b.lastSuccess) return '最近成功';
  return b.status || '空闲';
}

async function reload() {
  loading.value = true;
  try {
    overview.value = await getNfsMultiClusterOverview();
    loadedOnce.value = true;
  } catch (e: unknown) {
    overview.value = { clusters: [], bridges: [] };
    loadedOnce.value = true;
    createMessage.error(e instanceof Error ? e.message : '加载桥接信息失败');
  } finally {
    loading.value = false;
  }
}

async function activate(cluster: NfsClusterVO) {
  if (!cluster.id || cluster.isActive) return;
  activatingId.value = cluster.id;
  try {
    try {
      overview.value = await activateNfsCluster({ clusterId: cluster.id, forceStopBridges: false });
      createMessage.success('已切换主集群');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '切换失败';
      if (msg.includes('桥接') || msg.includes('停止')) {
        overview.value = await activateNfsCluster({ clusterId: cluster.id, forceStopBridges: true });
        createMessage.success('已停止旧桥接并切换主集群');
      } else {
        throw e;
      }
    }
    emit('changed');
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '切换主集群失败');
  } finally {
    activatingId.value = null;
  }
}

function openCreate() {
  createForm.targetClusterId = targetClusterOptions.value[0]?.value;
  createForm.sourceRelPaths = 'alert_images,playbacks,snaps';
  createForm.targetRelPath = defaultTargetRel.value;
  openCreateModal(true);
}

async function submitCreate() {
  if (!activeCluster.value?.id || !createForm.targetClusterId) {
    createMessage.warning('请选择目标从集群');
    return;
  }
  setModalProps({ confirmLoading: true });
  try {
    overview.value = await createNfsBridge({
      sourceClusterId: activeCluster.value.id,
      targetClusterId: createForm.targetClusterId,
      sourceRelPaths: createForm.sourceRelPaths,
      targetRelPath: createForm.targetRelPath || defaultTargetRel.value,
    });
    closeModal();
    createMessage.success('桥接已创建');
    emit('changed');
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '创建失败');
  } finally {
    setModalProps({ confirmLoading: false });
  }
}

async function run(bridge: NfsBridgeVO) {
  if (!bridge.id) return;
  runningId.value = bridge.id;
  try {
    overview.value = await runNfsBridge(bridge.id);
    createMessage.success(
      overview.value.bridges?.find((b) => b.id === bridge.id)?.lastMessage || '同步完成',
    );
    emit('changed');
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '同步失败');
    await reload();
  } finally {
    runningId.value = null;
  }
}

async function stop(bridge: NfsBridgeVO) {
  if (!bridge.id) return;
  stoppingId.value = bridge.id;
  try {
    overview.value = await stopNfsBridge(bridge.id);
    createMessage.success('桥接已停止');
    emit('changed');
  } catch (e: unknown) {
    createMessage.error(e instanceof Error ? e.message : '停止失败');
  } finally {
    stoppingId.value = null;
  }
}

defineExpose({ reload });
</script>

<template>
  <BasicDrawer
    v-bind="$attrs"
    title="多集群切换与同步"
    width="86%"
    :show-footer="true"
    :destroy-on-close="false"
    root-class-name="nfs-bridge-drawer"
    @register="registerDrawer"
  >
    <template #title>
      <div class="bd-title">
        <span class="bd-title__name">多集群切换与同步</span>
        <span class="bd-title__desc">
          切换主集群；主 → 从 单向同步到 `_bridge/`（三方 / 客户），不覆盖业务目录
        </span>
        <Tag v-if="overview?.activeClusterName" color="processing">
          主：{{ overview.activeClusterName }}
        </Tag>
      </div>
    </template>

    <template #footer>
      <div class="bd-foot">
        <Space>
          <Button @click="closeDrawer">关闭</Button>
          <Button preIcon="ant-design:reload-outlined" :loading="loading" @click="reload">
            刷新
          </Button>
        </Space>
        <Button
          type="primary"
          preIcon="ant-design:plus-outlined"
          :disabled="!canCreateBridge"
          @click="openCreate"
        >
          创建桥接
        </Button>
      </div>
    </template>

    <Spin :spinning="loading && !loadedOnce">
      <div class="bd-body">
        <!-- 同步流向概览 -->
        <div class="bd-flow">
          <div class="bd-flow__toolbar">
            <span class="bd-flow__toolbar-title">同步流向</span>
            <span class="bd-flow__toolbar-desc">主 → 从 单向写入 <code>_bridge/</code></span>
            <Button
              type="primary"
              size="small"
              preIcon="ant-design:plus-outlined"
              :disabled="!canCreateBridge"
              @click="openCreate"
            >
              新建桥接
            </Button>
          </div>

          <div class="bd-flow__main">
            <!-- 同步源 -->
            <div class="bd-flow__col bd-flow__col--source">
              <div class="bd-flow__col-head">
                <Icon icon="ant-design:cloud-server-outlined" :size="14" />
                <span>同步源</span>
                <Tag color="processing">主</Tag>
                <Tag
                  v-if="sourceFlowRow"
                  :color="sourceFlowRow.ready ? 'success' : 'warning'"
                >
                  {{ sourceFlowRow.ready ? '就绪' : '未就绪' }}
                </Tag>
              </div>
              <div v-if="sourceFlowRow" class="bd-flow__card">
                <div class="bd-flow__row">
                  <span class="bd-flow__row-name">{{ sourceFlowRow.name }}</span>
                </div>
                <div class="bd-flow__row-meta">
                  <span>{{ sourceFlowRow.host }}</span>
                  <template v-if="sourceFlowRow.extra">
                    <span class="bd-flow__dot">·</span>
                    <span>{{ sourceFlowRow.extra }}</span>
                  </template>
                </div>
              </div>
              <div v-else class="bd-flow__card bd-flow__card--empty">请先在下方选择主集群</div>
            </div>

            <!-- 流向 -->
            <div class="bd-flow__col bd-flow__col--link" aria-hidden="true">
              <div class="bd-flow__link-line" />
              <div class="bd-flow__link-badge">
                <Icon icon="ant-design:arrow-right-outlined" :size="14" />
              </div>
              <span class="bd-flow__link-label">单向</span>
            </div>

            <!-- 接收端（支持多个从集群列表） -->
            <div class="bd-flow__col bd-flow__col--target">
              <div class="bd-flow__col-head">
                <Icon icon="ant-design:cluster-outlined" :size="14" />
                <span>接收端</span>
                <Tag>从</Tag>
                <Tag v-if="targetFlowRows.length" color="blue">
                  {{ targetFlowRows.length }} 个
                </Tag>
              </div>
              <div
                v-if="targetFlowRows.length"
                class="bd-flow__card bd-flow__card--list"
                :class="{ 'bd-flow__card--scroll': targetFlowRows.length > FLOW_TARGET_VISIBLE }"
              >
                <div
                  v-for="row in targetFlowRows.slice(0, FLOW_TARGET_VISIBLE)"
                  :key="row.id"
                  class="bd-flow__row bd-flow__row--item"
                >
                  <span class="bd-flow__row-name">{{ row.name }}</span>
                  <span class="bd-flow__row-host">{{ row.host }}</span>
                </div>
                <div v-if="targetFlowOverflow" class="bd-flow__row bd-flow__row--more">
                  还有 {{ targetFlowOverflow }} 个从集群，见下方列表
                </div>
              </div>
              <div v-else class="bd-flow__card bd-flow__card--empty">
                暂无从集群，需先有客户 / 三方从集群
              </div>
            </div>
          </div>
        </div>

        <div class="bd-cols">
          <!-- 左：选主，列表紧凑 -->
          <section class="bd-panel">
            <div class="bd-panel__head">
              <span class="bd-panel__title">选主集群</span>
              <span class="bd-panel__hint">点击行即可切换；共 {{ clusterCount }} 个</span>
            </div>
            <div v-if="loadedOnce && !clusterCount" class="bd-empty">
              暂无集群，请先「分配并刷新」
            </div>
            <div v-else class="bd-table">
              <button
                v-for="cluster in overview?.clusters || []"
                :key="cluster.id"
                type="button"
                class="bd-row"
                :class="{ 'bd-row--on': cluster.isActive }"
                :disabled="activatingId === cluster.id"
                @click="activate(cluster)"
              >
                <div class="bd-row__main">
                  <div class="bd-row__name">
                    {{ cluster.name || cluster.laneKey }}
                    <Tag v-if="cluster.isActive" color="processing">主</Tag>
                    <Tag v-else>从</Tag>
                    <Tag :color="cluster.primaryReady ? 'success' : 'warning'">
                      {{ cluster.primaryReady ? '就绪' : '未就绪' }}
                    </Tag>
                  </div>
                  <div class="bd-row__meta">
                    {{ cluster.primaryHost || cluster.primaryName || '-' }}
                    · {{ cluster.mountRoot || '-' }}
                  </div>
                </div>
                <span class="bd-row__act">
                  <template v-if="cluster.isActive">当前主</template>
                  <template v-else-if="activatingId === cluster.id">切换中…</template>
                  <template v-else>设为主</template>
                </span>
              </button>
            </div>
          </section>

          <!-- 右：桥接操作，主操作区 -->
          <section class="bd-panel bd-panel--grow">
            <div class="bd-panel__head">
              <span class="bd-panel__title">桥接链路</span>
              <span class="bd-panel__hint">
                启用 {{ enabledBridges.length }} / 全部 {{ bridgeCount }}
              </span>
            </div>

            <div v-if="loadedOnce && !bridgeCount" class="bd-empty">
              {{
                canCreateBridge
                  ? '还没有桥接。点「新建桥接」后，再点「同步」即可写入从集群 _bridge/'
                  : '先准备从集群，再创建桥接'
              }}
            </div>

            <div v-else class="bd-bridges">
              <div
                v-for="bridge in overview?.bridges || []"
                :key="bridge.id"
                class="bd-bridge"
                :class="{
                  'bd-bridge--off': bridge.enabled === false || bridge.status === 'stopped',
                }"
              >
                <div class="bd-bridge__route">
                  <span class="bd-bridge__src">
                    {{ bridge.sourceClusterName || bridge.sourceClusterId }}
                  </span>
                  <Icon icon="ant-design:arrow-right-outlined" :size="14" class="bd-bridge__arrow" />
                  <span class="bd-bridge__dst">
                    {{ bridge.targetClusterName || bridge.targetClusterId }}
                  </span>
                  <Tag :color="bridgeTone(bridge)">{{ bridgeStatusText(bridge) }}</Tag>
                </div>
                <div class="bd-bridge__path" :title="bridge.lastMessage || ''">
                  {{ bridge.targetRelPath || '-' }}
                  <template v-if="bridge.lastMessage"> · {{ bridge.lastMessage }}</template>
                </div>
                <div class="bd-bridge__ops">
                  <Button
                    type="primary"
                    size="small"
                    :loading="runningId === bridge.id"
                    :disabled="bridge.enabled === false"
                    @click="run(bridge)"
                  >
                    同步
                  </Button>
                  <Button
                    size="small"
                    danger
                    :loading="stoppingId === bridge.id"
                    :disabled="bridge.enabled === false && bridge.status === 'stopped'"
                    @click="stop(bridge)"
                  >
                    停止
                  </Button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Spin>

    <BasicModal
      @register="registerCreateModal"
      title="创建单向桥接"
      ok-text="创建"
      cancel-text="取消"
      :min-height="200"
      :width="480"
      :can-fullscreen="false"
      destroy-on-close
      @ok="submitCreate"
    >
      <div class="form-hint">
        从主集群 <b>{{ overview?.activeClusterName || '-' }}</b> 同步到从集群，只写 `_bridge/`。
      </div>
      <div class="form-item">
        <div class="form-label">目标从集群</div>
        <Select
          v-model:value="createForm.targetClusterId"
          style="width: 100%"
          :options="targetClusterOptions"
          placeholder="选择从集群"
        />
      </div>
      <div class="form-item">
        <div class="form-label">源目录</div>
        <Input v-model:value="createForm.sourceRelPaths" placeholder="alert_images,playbacks,snaps" />
      </div>
      <div class="form-item">
        <div class="form-label">目标前缀</div>
        <Input v-model:value="createForm.targetRelPath" :placeholder="defaultTargetRel" />
      </div>
    </BasicModal>
  </BasicDrawer>
</template>

<style scoped lang="less">
@import '../../utils/theme.less';

.bd-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding-right: 28px;
}

.bd-title__name {
  font-size: 16px;
  font-weight: 600;
  color: @node-text-primary;
}

.bd-title__desc {
  font-size: 12px;
  color: @node-text-muted;
}

.bd-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.bd-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bd-flow {
  border-radius: @node-radius;
  border: 1px solid @node-border;
  background: @node-bg;
  overflow: hidden;
}

.bd-flow__toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid @node-border-light;
  background: #fafbfc;

  .ant-btn {
    margin-left: auto;
  }
}

.bd-flow__toolbar-title {
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
}

.bd-flow__toolbar-desc {
  font-size: 12px;
  color: @node-text-muted;

  code {
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 11px;
    background: #f0f2f5;
    color: @node-text-secondary;
  }
}

.bd-flow__main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 72px minmax(0, 1fr);
  align-items: stretch;
  min-height: 96px;
}

.bd-flow__col {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  padding: 12px 14px;
}

.bd-flow__col--source {
  border-left: 3px solid @node-primary;
}

.bd-flow__col--target {
  border-right: 3px solid #0f766e;
}

.bd-flow__col--link {
  position: relative;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 0;
  border-left: 1px solid @node-border-light;
  border-right: 1px solid @node-border-light;
  background: #fafbfc;
}

.bd-flow__col-head {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 22px;
  font-size: 12px;
  font-weight: 600;
  color: @node-text-secondary;
}

.bd-flow__card {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  min-height: 52px;
  padding: 8px 10px;
  border: 1px solid @node-border-light;
  border-radius: 6px;
  background: #fff;
}

.bd-flow__card--list {
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.bd-flow__card--scroll {
  max-height: 132px;
  overflow-y: auto;
}

.bd-flow__card--empty {
  justify-content: center;
  font-size: 12px;
  color: @node-text-muted;
  background: #fafafa;
}

.bd-flow__row {
  min-width: 0;
}

.bd-flow__row--item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 7px 10px;
  border-bottom: 1px solid @node-border-light;

  &:last-child {
    border-bottom: none;
  }
}

.bd-flow__row--more {
  padding: 6px 10px;
  font-size: 11px;
  color: @node-text-muted;
  text-align: center;
  background: #fafafa;
  border-top: 1px dashed @node-border;
}

.bd-flow__row-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bd-flow__row-host {
  flex-shrink: 0;
  font-size: 12px;
  color: @node-text-muted;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.bd-flow__row-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 12px;
  color: @node-text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bd-flow__dot {
  color: @node-border;
}

.bd-flow__link-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 2px;
  margin-top: -1px;
  background: linear-gradient(90deg, fade(@node-primary, 20%) 0%, @node-primary 100%);
}

.bd-flow__link-badge {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: @node-primary;
  background: #fff;
  border: 2px solid fade(@node-primary, 30%);
  box-shadow: 0 1px 4px fade(@node-primary, 12%);
}

.bd-flow__link-label {
  position: relative;
  z-index: 1;
  font-size: 11px;
  color: @node-text-muted;
}

.bd-cols {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.4fr);
  gap: 12px;
  align-items: start;
}

.bd-panel {
  border: 1px solid @node-border;
  border-radius: 8px;
  background: #fff;
  padding: 10px 12px 12px;
  min-height: 0;
}

.bd-panel--grow {
  min-height: 320px;
}

.bd-panel__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.bd-panel__title {
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
}

.bd-panel__hint {
  font-size: 12px;
  color: @node-text-muted;
}

.bd-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 12px;
  color: @node-text-muted;
  border: 1px dashed @node-border;
  border-radius: 6px;
  background: #fafafa;
}

.bd-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bd-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border: 1px solid @node-border;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;

  &:hover:not(:disabled) {
    border-color: fade(@node-primary, 35%);
  }

  &:disabled {
    cursor: wait;
    opacity: 0.75;
  }
}

.bd-row--on {
  border-color: fade(@node-primary, 40%);
  background: #f5f8ff;
  box-shadow: inset 2px 0 0 @node-primary;
}

.bd-row__main {
  min-width: 0;
  flex: 1;
}

.bd-row__name {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
}

.bd-row__meta {
  margin-top: 2px;
  font-size: 11px;
  color: @node-text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bd-row__act {
  flex-shrink: 0;
  font-size: 12px;
  color: @node-primary;
  font-weight: 500;
}

.bd-bridges {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bd-bridge {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid @node-border;
  border-radius: 6px;
  background: #fff;
}

.bd-bridge--off {
  opacity: 0.7;
  background: #fafafa;
}

.bd-bridge__route {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.bd-bridge__src,
.bd-bridge__dst {
  font-size: 13px;
  font-weight: 600;
  color: @node-text-primary;
}

.bd-bridge__dst {
  color: #0f766e;
}

.bd-bridge__arrow {
  color: @node-primary;
}

.bd-bridge__path {
  font-size: 12px;
  color: @node-text-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bd-bridge__ops {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.form-hint {
  margin-bottom: 12px;
  color: @node-text-muted;
  font-size: 12px;
  line-height: 1.5;

  b {
    color: @node-text-secondary;
  }
}

.form-item + .form-item {
  margin-top: 12px;
}

.form-label {
  margin-bottom: 6px;
  font-size: 13px;
  color: @node-text-secondary;
}

@media (max-width: 1100px) {
  .bd-flow__main {
    grid-template-columns: 1fr;
  }

  .bd-flow__col--link {
    flex-direction: row;
    padding: 8px 14px;
    border-left: none;
    border-right: none;
    border-top: 1px solid @node-border-light;
    border-bottom: 1px solid @node-border-light;
  }

  .bd-flow__link-line {
    top: auto;
    left: 14px;
    right: 14px;
    bottom: 50%;
  }

  .bd-cols {
    grid-template-columns: 1fr;
  }

  .bd-bridge {
    grid-template-columns: 1fr;
  }
}
</style>

<style lang="less">
.nfs-bridge-drawer {
  .ant-drawer-content-wrapper {
    width: min(86vw, 1400px) !important;
    max-width: 96vw;
  }

  .ant-drawer-header {
    padding: 12px 20px;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-body {
    background: #f7f8fa;
  }

  .scrollbar__wrap {
    padding: 12px 16px 16px !important;
  }

  .ant-drawer-footer {
    padding: 10px 16px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }
}
</style>
