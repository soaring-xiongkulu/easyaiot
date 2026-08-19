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
          v-model:value="selectValue"
          :mode="multiple ? 'multiple' : undefined"
          show-search
          allow-clear
          option-filter-prop="label"
          :placeholder="placeholder"
          class="node-select-row__node-select"
          :options="nodeOptions"
          :filter-option="filterNode"
          :loading="nodesLoading"
        >
          <template v-if="multiple" #tagRender="{ value: tagValue, closable, onClose }">
            <Tag :closable="closable" class="node-select-tag" @close="onClose">
              {{ resolveNodeHost(tagValue) }}
            </Tag>
          </template>
        </Select>
      </label>
      <div class="node-select-row__actions">
        <Button @click="loadNodes" :loading="nodesLoading" preIcon="ant-design:reload-outlined">
          刷新
        </Button>
        <Button v-if="multiple" type="link" @click="selectAllEligible">全选可用</Button>
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
  formatNodeFunctions,
  nodeHasAnyFunction,
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
    /** 在角色过滤之外仍允许选择控制面（NFS 服务端/客户端场景） */
    includePlatform?: boolean;
    /** 强制排除的节点（如当前 NFS 主服务端不可再选为客户端） */
    excludeNodeIds?: number[];
    /** 是否多选；文件管理等场景建议单选 */
    multiple?: boolean;
  }>(),
  {
    roleFilter: 'computeWorkload',
    placeholder: '选择目标节点（需已配置 SSH 凭据）',
    showScopeBar: true,
    excludePlatform: true,
    includePlatform: false,
    multiple: true,
  },
);

const selectedNodeIds = defineModel<number[]>('selectedNodeIds', { default: () => [] });

const selectValue = computed<number | number[] | undefined>({
  get() {
    if (props.multiple) return selectedNodeIds.value;
    return selectedNodeIds.value[0];
  },
  set(val) {
    if (props.multiple) {
      selectedNodeIds.value = Array.isArray(val) ? val : val != null ? [val as number] : [];
      return;
    }
    if (Array.isArray(val)) {
      selectedNodeIds.value = val.length ? [val[val.length - 1]] : [];
    } else if (val != null) {
      selectedNodeIds.value = [val as number];
    } else {
      selectedNodeIds.value = [];
    }
  },
});

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

/** 未展示泳道选择时不再静默按泳道过滤，否则批量/文件运维会「看起来没节点」 */
const scopedNodeList = computed(() => {
  if (!props.showScopeBar) return nodeList.value;
  return scopeNodes(nodeList.value);
});

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
  if (node.id != null && (props.excludeNodeIds || []).includes(node.id)) {
    return false;
  }
  if (isPlatformNode(node)) {
    if (props.includePlatform) return true;
    if (props.excludePlatform) return false;
  }
  const allowed = allowedRoles.value;
  if (allowed && !nodeHasAnyFunction(node, [...allowed])) return false;
  return true;
}

function hasSshCredential(node: ComputeNodeVO) {
  return !!(node.sshUsername?.trim() || node.sshCredentialConfigured);
}

function rebuildNodeOptions() {
  // 只列出可操作节点，避免把 storage 等无关角色混进客户端下拉
  nodeOptions.value = scopedNodeList.value.filter(isEligibleNode).map((node) => ({
    label: `${node.name} (${node.host}) — ${formatNodeFunctions(node)} / ${node.status || 'unknown'}${hasSshCredential(node) ? '' : ' / 未配置 SSH'}`,
    value: node.id!,
    disabled: !hasSshCredential(node) && !isPlatformNode(node),
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
  () => [props.excludePlatform, props.includePlatform, props.excludeNodeIds] as const,
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
  if (!laneReady.value || laneKey === prevLaneKey || !props.showScopeBar) return;
  selectedNodeIds.value = [];
  rebuildNodeOptions();
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
