<template>
  <div class="cluster-node-selector">
    <div class="node-select-row">
      <label v-if="showScopeBar" class="control-item node-select-row__scope">
        <span>{{ NODE_DASHBOARD.overviewCentralNode }}</span>
        <Select
          v-model:value="centralLaneSelectValue"
          show-search
          class="node-select-row__scope-select"
          :options="centralLaneOptions"
          :filter-option="filterLane"
          :loading="scopeLoading"
        />
      </label>
      <label class="control-item node-select-row__target">
        <Select
          v-model:value="selectedNodeIds"
          mode="multiple"
          show-search
          allow-clear
          option-filter-prop="label"
          :placeholder="placeholder"
          class="node-select-row__node-select"
          :options="nodeOptions"
          :filter-option="filterNode"
          :loading="nodesLoading"
        >
          <template #tagRender="{ value: tagValue, closable, onClose }">
            <Tag :closable="closable" class="node-select-tag" @close="onClose">
              {{ resolveNodeHost(tagValue) }}
            </Tag>
          </template>
        </Select>
      </label>
      <div class="node-select-row__actions">
        <Button @click="loadNodes" :loading="nodesLoading">刷新</Button>
        <Button type="link" @click="selectAllEligible">全选可用</Button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { Select, Tag } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { getNodePage, type ComputeNodeVO } from '@/api/device/node';
import {
  CLUSTER_NODE_ROLE_FILTERS,
  NODE_DASHBOARD,
  type ClusterNodeRoleFilterKey,
} from '../../utils/constants';
import { isPlatformNode } from '../../utils/platformNode';
import { useClusterNodeScope } from '../../utils/useClusterNodeScope';

defineOptions({ name: 'ClusterNodeSelector' });

const props = withDefaults(
  defineProps<{
    roleFilter?: ClusterNodeRoleFilterKey | 'any';
    placeholder?: string;
    initialNodeId?: number;
    initialNodeIds?: number[];
    showScopeBar?: boolean;
    /** 默认隐藏本机控制面（platform）节点：分发目标不含本机默认实例 */
    excludePlatform?: boolean;
  }>(),
  {
    roleFilter: 'computeWorkload',
    placeholder: '选择目标节点（需已配置 SSH 凭据）',
    showScopeBar: true,
    excludePlatform: true,
  },
);

const selectedNodeIds = defineModel<number[]>('selectedNodeIds', { default: () => [] });

const nodesLoading = ref(false);
const scopeLoading = ref(false);
const nodeList = ref<ComputeNodeVO[]>([]);
const nodeOptions = ref<Array<{ label: string; value: number; disabled?: boolean }>>([]);
const laneReady = ref(false);

const { activeLaneKey, centralLaneOptions, scopeNodes, loadLanes, setActiveLaneKey } = useClusterNodeScope();

const centralLaneSelectValue = computed({
  get: () => activeLaneKey.value,
  set: (laneKey: string) => handleLaneChange(laneKey),
});

const allowedRoles = computed(() => {
  if (props.roleFilter === 'any') return null;
  return new Set<string>(CLUSTER_NODE_ROLE_FILTERS[props.roleFilter]);
});

const scopedNodeList = computed(() => scopeNodes(nodeList.value));

function filterNode(input: string, option: { label?: string }) {
  return (option.label || '').toLowerCase().includes(input.toLowerCase());
}

function filterLane(input: string, option: { label?: string }) {
  return filterNode(input, option);
}

function resolveNodeHost(value: number | string) {
  const id = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(id)) return String(value);
  const node = nodeList.value.find((item) => item.id === id);
  return node?.host?.trim() || String(id);
}

function isEligibleNode(node: ComputeNodeVO) {
  if (props.excludePlatform && isPlatformNode(node)) return false;
  const roles = allowedRoles.value;
  if (roles && !roles.has(node.nodeRole || '')) return false;
  return true;
}

function isListedNode(node: ComputeNodeVO) {
  // 分发场景：本机 platform 默认不出现在列表，避免误选
  if (props.excludePlatform && isPlatformNode(node)) return false;
  return true;
}

function hasSshCredential(node: ComputeNodeVO) {
  return !!(node.sshUsername?.trim() || node.sshCredentialConfigured);
}

function rebuildNodeOptions() {
  nodeOptions.value = scopedNodeList.value.filter(isListedNode).map((node) => ({
    label: `${node.name} (${node.host}) — ${node.nodeRole || '?'} / ${node.status || 'unknown'}${hasSshCredential(node) ? '' : ' / 未配置 SSH'}`,
    value: node.id!,
    disabled: !isEligibleNode(node),
  }));
}

function syncSelectedNodeIds() {
  const allowedIds = new Set(
    scopedNodeList.value.filter(isEligibleNode).map((node) => node.id).filter((id): id is number => id != null),
  );
  selectedNodeIds.value = selectedNodeIds.value.filter((id) => allowedIds.has(id));
}

async function loadNodes() {
  nodesLoading.value = true;
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 500 });
    nodeList.value = res?.data?.list || [];
    rebuildNodeOptions();
    syncSelectedNodeIds();
  } finally {
    nodesLoading.value = false;
  }
}

function selectAllEligible() {
  selectedNodeIds.value = scopedNodeList.value.filter(isEligibleNode).map((n) => n.id!);
}

function handleLaneChange(laneKey: string) {
  setActiveLaneKey(laneKey);
  selectedNodeIds.value = [];
  rebuildNodeOptions();
}

const selectedNodes = computed(() =>
  nodeList.value.filter((n) => n.id != null && selectedNodeIds.value.includes(n.id)),
);

defineExpose({ loadNodes, selectedNodes, nodeList });

watch(
  () => props.roleFilter,
  () => {
    rebuildNodeOptions();
    syncSelectedNodeIds();
  },
);

watch(
  () => props.excludePlatform,
  () => {
    rebuildNodeOptions();
    syncSelectedNodeIds();
  },
);

function applyInitialSelection() {
  if (props.initialNodeIds?.length) {
    const allowedIds = new Set(
      scopedNodeList.value.filter(isEligibleNode).map((node) => node.id).filter((id): id is number => id != null),
    );
    const ids = props.initialNodeIds.filter((id) => allowedIds.has(id));
    if (ids.length) {
      selectedNodeIds.value = ids;
      return;
    }
  }
  const id = props.initialNodeId;
  if (id && scopedNodeList.value.some((n) => n.id === id && isEligibleNode(n))) {
    selectedNodeIds.value = [id];
  }
}

watch(
  () => props.initialNodeId,
  () => {
    applyInitialSelection();
  },
);

watch(
  () => props.initialNodeIds,
  () => {
    applyInitialSelection();
  },
  { deep: true },
);

watch(activeLaneKey, (laneKey, prevLaneKey) => {
  if (!laneReady.value || laneKey === prevLaneKey) return;
  if (!props.showScopeBar) {
    selectedNodeIds.value = [];
    rebuildNodeOptions();
  }
});

watch(scopedNodeList, () => {
  rebuildNodeOptions();
  syncSelectedNodeIds();
});

onMounted(async () => {
  scopeLoading.value = true;
  try {
    await Promise.all([loadLanes(), loadNodes()]);
  } finally {
    scopeLoading.value = false;
    laneReady.value = true;
  }
  applyInitialSelection();
});
</script>

<style scoped lang="less">
@import '../../utils/theme.less';

.cluster-node-selector {
  margin-bottom: 16px;
}

.node-select-row {
  display: flex;
  align-items: center;
  gap: 12px 16px;
  flex-wrap: nowrap;
}

.node-select-row__scope {
  flex: 0 0 auto;
}

.node-select-row__scope-select {
  min-width: 180px;
  width: 200px;
}

.node-select-row__target {
  flex: 1 1 0;
  min-width: 0;
}

.node-select-row__node-select {
  flex: 1 1 0;
  min-width: 0;
  width: 100%;
}

.node-select-row__actions {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.control-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: @node-font-caption;
  color: @node-text-secondary;
}

.node-select-tag {
  margin-inline-end: 4px;
}
</style>
