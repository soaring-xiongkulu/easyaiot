<script lang="ts" setup>
import { computed, ref } from 'vue';
import { Checkbox, Space, Tag } from 'ant-design-vue';
import type { ClusterLaneVO, ComputeNodeVO } from '@/api/device/node';
import { batchClusterLaneAction } from '@/api/device/node';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  LANE_BATCH_DEPLOY_ACTIONS,
  NODE_STATUS_MAP,
  NODE_TERM,
  formatNodeFunctions,
} from '../../utils/constants';
import {
  canManageLaneWorkers,
  laneLabel,
  laneSyncStatusColor,
  localLaneWorkers,
} from '../../utils/clusterLanes';
import { isPlatformNode } from '../../utils/platformNode';

defineOptions({ name: 'ClusterLaneRow' });

const props = defineProps<{
  lane: ClusterLaneVO;
}>();

const emit = defineEmits<{
  view: [node: ComputeNodeVO];
  edit: [node: ComputeNodeVO];
  delete: [node: ComputeNodeVO];
  continueSetup: [node: ComputeNodeVO];
  batchNavigate: [tab: string, nodeIds: number[]];
  refresh: [];
}>();

const { createMessage } = useMessage();
const selectedWorkerIds = ref<number[]>([]);
const batchLoading = ref(false);

const workers = computed(() => props.lane.workerNodes || []);
const manageable = computed(() => canManageLaneWorkers(props.lane));
const laneTitle = computed(() => laneLabel(props.lane));
const central = computed(() => props.lane.centralNode);

const allWorkerIds = computed(() =>
  localLaneWorkers(props.lane)
    .map((node) => node.id)
    .filter((id): id is number => id != null),
);

const allSelected = computed({
  get: () => allWorkerIds.value.length > 0 && selectedWorkerIds.value.length === allWorkerIds.value.length,
  set: (checked: boolean) => {
    selectedWorkerIds.value = checked ? [...allWorkerIds.value] : [];
  },
});

const hasSelection = computed(() => selectedWorkerIds.value.length > 0);

const onlineWorkers = computed(
  () => workers.value.filter((n) => n.status === 'online' && !isPlatformNode(n)).length,
);

function roleLabel(node?: { functions?: string[] | null; nodeRole?: string | null } | null) {
  return formatNodeFunctions(node);
}

function statusMeta(status?: string | null) {
  return NODE_STATUS_MAP[status || ''] || { text: status || '未知', color: 'default' };
}

function toggleWorker(node: ComputeNodeVO, checked: boolean) {
  if (!node.id) return;
  if (checked) {
    if (!selectedWorkerIds.value.includes(node.id)) {
      selectedWorkerIds.value = [...selectedWorkerIds.value, node.id];
    }
    return;
  }
  selectedWorkerIds.value = selectedWorkerIds.value.filter((id) => id !== node.id);
}

function handleBatchNavigate(tab: string) {
  if (!selectedWorkerIds.value.length) {
    createMessage.warning('请先选择工作节点');
    return;
  }
  emit('batchNavigate', tab, selectedWorkerIds.value);
}

async function runBatchMaintenance(enabled: boolean) {
  if (!selectedWorkerIds.value.length) {
    createMessage.warning('请先选择工作节点');
    return;
  }
  batchLoading.value = true;
  try {
    await batchClusterLaneAction({
      laneKey: props.lane.laneKey,
      nodeIds: selectedWorkerIds.value,
      action: enabled ? 'maintenance_on' : 'maintenance_off',
    });
    createMessage.success(enabled ? '已批量进入维护模式' : '已批量退出维护模式');
    selectedWorkerIds.value = [];
    emit('refresh');
  } finally {
    batchLoading.value = false;
  }
}

function isWorkerSelectable(node: ComputeNodeVO) {
  return manageable.value && !!node.id && !node.isRemote && !isPlatformNode(node);
}
</script>

<template>
  <article class="node-card" :class="{ 'node-card--local': lane.isLocal, 'node-card--remote': !lane.isLocal }">
    <header class="node-card__head">
      <div class="node-card__head-main">
        <div class="node-card__icon">
          <Icon icon="ant-design:cluster-outlined" :size="16" />
        </div>
        <div class="node-card__titles">
          <div class="node-card__title">
            {{ laneTitle }}
            <Tag :color="lane.isLocal ? 'processing' : 'default'">
              {{ lane.isLocal ? '本机' : '远程' }}
            </Tag>
            <Tag :color="laneSyncStatusColor(lane.syncStatus)">
              {{ lane.isLocal ? '可操控' : lane.syncStatus || 'unknown' }}
            </Tag>
          </div>
          <div class="node-card__sub">
            <template v-if="central?.host">{{ central.host }}</template>
            <template v-else>暂无中心节点</template>
            · {{ NODE_TERM.laneWorkers }} {{ workers.length }}
            · 在线 {{ onlineWorkers }}
          </div>
        </div>
      </div>
    </header>

    <div class="node-card__body">
      <div v-if="!central && !workers.length" class="node-card__empty">暂无节点</div>

      <div
        v-if="central"
        class="node-row node-row--central"
        @click="emit('view', central)"
      >
        <div class="node-row__tags">
          <Tag color="purple">中心</Tag>
          <Tag :color="statusMeta(central.status).color">{{ statusMeta(central.status).text }}</Tag>
          <Tag v-if="isPlatformNode(central)">控制面</Tag>
        </div>
        <div class="node-row__main">
          <div class="node-row__name">{{ central.name || '-' }}</div>
          <div class="node-row__meta">{{ central.host || '-' }} · {{ roleLabel(central) }}</div>
        </div>
        <div class="node-row__ops" @click.stop>
          <Button size="small" type="link" @click="emit('view', central)">详情</Button>
        </div>
      </div>

      <div
        v-for="worker in workers"
        :key="`${lane.laneKey}-${worker.id}`"
        class="node-row"
        :class="{ 'node-row--selected': !!worker.id && selectedWorkerIds.includes(worker.id) }"
        @click="emit('view', worker)"
      >
        <div class="node-row__tags">
          <Checkbox
            v-if="isWorkerSelectable(worker)"
            :checked="!!worker.id && selectedWorkerIds.includes(worker.id)"
            @click.stop
            @change="(e) => toggleWorker(worker, e.target.checked)"
          />
          <Tag color="cyan">{{ roleLabel(worker) }}</Tag>
          <Tag :color="statusMeta(worker.status).color">{{ statusMeta(worker.status).text }}</Tag>
        </div>
        <div class="node-row__main">
          <div class="node-row__name">{{ worker.name || '-' }}</div>
          <div class="node-row__meta">{{ worker.host || '-' }}</div>
        </div>
        <div class="node-row__ops" @click.stop>
          <Button
            v-if="worker.status === 'pending'"
            size="small"
            type="link"
            @click="emit('continueSetup', worker)"
          >
            纳管
          </Button>
          <Button size="small" type="link" @click="emit('view', worker)">详情</Button>
          <Button
            v-if="manageable && !isPlatformNode(worker) && !worker.isRemote"
            size="small"
            type="link"
            @click="emit('edit', worker)"
          >
            编辑
          </Button>
          <Button
            v-if="manageable && !isPlatformNode(worker) && !worker.isRemote"
            size="small"
            type="link"
            danger
            @click="emit('delete', worker)"
          >
            删除
          </Button>
        </div>
      </div>
    </div>

    <footer v-if="manageable" class="node-card__foot">
      <Checkbox v-model:checked="allSelected">{{ NODE_TERM.laneBatchSelectAll }}</Checkbox>
      <Space wrap :size="6">
        <Button
          size="small"
          preIcon="ant-design:tool-outlined"
          :loading="batchLoading"
          :disabled="!hasSelection"
          @click="runBatchMaintenance(true)"
        >
          {{ NODE_TERM.laneBatchMaintenanceOn }}
        </Button>
        <Button
          size="small"
          preIcon="ant-design:check-circle-outlined"
          :loading="batchLoading"
          :disabled="!hasSelection"
          @click="runBatchMaintenance(false)"
        >
          {{ NODE_TERM.laneBatchMaintenanceOff }}
        </Button>
        <Button
          v-for="action in LANE_BATCH_DEPLOY_ACTIONS"
          :key="action.tab"
          size="small"
          :preIcon="action.icon"
          :disabled="!hasSelection"
          @click="handleBatchNavigate(action.tab)"
        >
          {{ action.label }}
        </Button>
      </Space>
    </footer>
    <div v-else class="node-card__foot node-card__foot--hint">
      {{ NODE_TERM.laneRemoteHint }}
    </div>
  </article>
</template>

<style lang="less" scoped>
@import '../../utils/theme.less';

.node-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid @node-border;
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:hover {
    border-color: fade(@node-primary, 22%);
    box-shadow: 0 4px 14px rgba(38, 108, 251, 0.06);
  }
}

.node-card--local {
  border-top: 2px solid @node-primary;
}

.node-card--remote {
  border-top: 2px solid @node-text-muted;
}

.node-card__head {
  padding: 10px 12px;
  border-bottom: 1px solid fade(@node-border, 70%);
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}

.node-card__head-main {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.node-card__icon {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: fade(@node-primary, 8%);
  color: @node-primary;
}

.node-card--remote .node-card__icon {
  background: fade(@node-text-muted, 10%);
  color: @node-text-muted;
}

.node-card__titles {
  min-width: 0;
  flex: 1;
}

.node-card__title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: @node-text-primary;
  line-height: 1.35;
}

.node-card__sub {
  margin-top: 4px;
  font-size: 12px;
  color: @node-text-muted;
  line-height: 1.45;
  word-break: break-all;
}

.node-card__body {
  flex: 1;
  min-height: 0;
  max-height: 360px;
  overflow: auto;
  padding: 8px 10px;
}

.node-card__empty {
  padding: 24px 8px;
  text-align: center;
  color: @node-text-muted;
  font-size: 13px;
}

.node-row {
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  padding: 8px 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: fade(@node-primary, 4%);
  }

  & + & {
    border-top: 1px dashed fade(@node-border, 80%);
  }
}

.node-row--central {
  background: fade(@node-primary, 3%);
  margin-bottom: 4px;
  border: 1px solid fade(@node-primary, 12%);
}

.node-row--selected {
  background: fade(@node-primary, 6%);
}

.node-row__tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.node-row__main {
  min-width: 0;
}

.node-row__name {
  font-size: 13px;
  font-weight: 500;
  color: @node-text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-row__meta {
  margin-top: 2px;
  font-size: 11px;
  color: @node-text-muted;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-row__ops {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0;
}

.node-card__foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 12px 10px;
  border-top: 1px solid fade(@node-border, 70%);
  background: #fafbfc;
}

.node-card__foot--hint {
  justify-content: flex-end;
  font-size: 12px;
  color: @node-text-muted;
}

@media (max-width: 900px) {
  .node-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .node-row__ops {
    justify-content: flex-start;
  }
}
</style>
