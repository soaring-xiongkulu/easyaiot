<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { Alert, Button, Spin, Table, Tag } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { formatToDateTime } from '@/utils/dateUtil';
import { getNodeSentinel, probeNodeSentinel, resyncNodeSentinel, type NodeSentinelVO } from '@/api/device/node';
import { SENTINEL_TERM } from '../../utils/constants';

defineOptions({ name: 'NodeSentinelPanel' });

const props = defineProps<{
  nodeId?: number;
}>();

const { createMessage } = useMessage();
const loading = ref(false);
const probing = ref(false);
const resyncing = ref(false);
const snapshot = ref<NodeSentinelVO | null>(null);

const componentColumns = [
  { title: SENTINEL_TERM.component, dataIndex: 'componentId', key: 'componentId', width: 160 },
  { title: SENTINEL_TERM.state, dataIndex: 'state', key: 'state', width: 100 },
  { title: SENTINEL_TERM.expected, dataIndex: 'expected', key: 'expected', width: 90 },
  { title: SENTINEL_TERM.healMark, dataIndex: 'healMark', key: 'healMark', width: 110 },
  { title: SENTINEL_TERM.healAttempts, dataIndex: 'healAttempts', key: 'healAttempts', width: 100 },
  { title: SENTINEL_TERM.reason, dataIndex: 'reason', key: 'reason' },
];

const healLogColumns = [
  { title: SENTINEL_TERM.component, dataIndex: 'componentId', key: 'componentId', width: 150 },
  { title: SENTINEL_TERM.healMark, dataIndex: 'mark', key: 'mark', width: 110 },
  { title: SENTINEL_TERM.healAttempts, dataIndex: 'attemptCount', key: 'attemptCount', width: 90 },
  { title: '成功', dataIndex: 'success', key: 'success', width: 80 },
  { title: SENTINEL_TERM.reason, dataIndex: 'message', key: 'message' },
  { title: '时间', dataIndex: 'createTime', key: 'createTime', width: 170 },
];

const declaredRows = computed(() => {
  const declared = snapshot.value?.declaredCapabilities || {};
  const sched = snapshot.value?.schedulableCapabilities || {};
  return Object.entries(declared).map(([capability, enabled]) => {
    const detail = (sched[capability] || {}) as Record<string, unknown>;
    return {
      capability,
      declared: Boolean(enabled),
      schedulable: Boolean(detail.schedulable),
      state: String(detail.state || ''),
    };
  });
});

const declaredColumns = [
  { title: SENTINEL_TERM.capability, dataIndex: 'capability', key: 'capability', width: 180 },
  { title: '已声明', dataIndex: 'declared', key: 'declared', width: 90 },
  { title: SENTINEL_TERM.schedulable, dataIndex: 'schedulable', key: 'schedulable', width: 100 },
  { title: SENTINEL_TERM.state, dataIndex: 'state', key: 'state', width: 120 },
];

const envProfileText = computed(() => {
  const profile = snapshot.value?.environmentProfile;
  if (!profile || Object.keys(profile).length === 0) return SENTINEL_TERM.noData;
  try {
    return JSON.stringify(profile, null, 2);
  } catch {
    return String(profile);
  }
});

const capabilityRows = computed(() => {
  const caps = snapshot.value?.schedulableCapabilities || {};
  return Object.entries(caps).map(([capability, detail]) => {
    const row = (detail || {}) as Record<string, unknown>;
    return {
      capability,
      schedulable: Boolean(row.schedulable),
      state: String(row.state || ''),
      reason: String(row.reason || ''),
      missing: Array.isArray(row.missingComponents) ? row.missingComponents.join(', ') : '',
    };
  });
});

const capabilityColumns = [
  { title: SENTINEL_TERM.capability, dataIndex: 'capability', key: 'capability', width: 180 },
  { title: SENTINEL_TERM.schedulable, dataIndex: 'schedulable', key: 'schedulable', width: 100 },
  { title: SENTINEL_TERM.state, dataIndex: 'state', key: 'state', width: 120 },
  { title: SENTINEL_TERM.missing, dataIndex: 'missing', key: 'missing' },
  { title: SENTINEL_TERM.reason, dataIndex: 'reason', key: 'reason' },
];

const summaryText = computed(() => {
  const summary = snapshot.value?.summary as Record<string, unknown> | undefined;
  if (!summary) return SENTINEL_TERM.noData;
  const ready = summary.componentReady ?? 0;
  const total = summary.componentTotal ?? 0;
  const sched = summary.capabilitySchedulable ?? 0;
  return SENTINEL_TERM.summaryTemplate
    .replace('{ready}', String(ready))
    .replace('{total}', String(total))
    .replace('{sched}', String(sched));
});

function stateColor(state?: string) {
  if (state === 'ready' || state === 'healed') return 'success';
  if (state === 'degraded' || state === 'healing' || state === 'marked') return 'warning';
  if (state === 'skipped' || state === 'unknown' || state === 'unhealable') return 'default';
  return 'error';
}

function healMarkText(mark?: string) {
  if (mark === 'marked') return SENTINEL_TERM.healMarked;
  if (mark === 'healing') return SENTINEL_TERM.healHealing;
  if (mark === 'exhausted') return SENTINEL_TERM.healExhausted;
  if (mark === 'unhealable') return SENTINEL_TERM.healUnhealable;
  if (mark === 'healed') return SENTINEL_TERM.healHealed;
  return mark || '—';
}

function healMarkColor(mark?: string) {
  if (mark === 'healed') return 'success';
  if (mark === 'healing' || mark === 'marked') return 'warning';
  if (mark === 'exhausted') return 'error';
  return 'default';
}

async function loadSnapshot() {
  if (!props.nodeId) {
    snapshot.value = null;
    return;
  }
  loading.value = true;
  try {
    snapshot.value = await getNodeSentinel(props.nodeId);
  } catch {
    createMessage.error(SENTINEL_TERM.loadFailed);
  } finally {
    loading.value = false;
  }
}

async function handleProbe() {
  if (!props.nodeId) return;
  probing.value = true;
  try {
    snapshot.value = await probeNodeSentinel(props.nodeId, 'L1');
    createMessage.success(SENTINEL_TERM.probeSuccess);
  } catch {
    createMessage.error(SENTINEL_TERM.loadFailed);
  } finally {
    probing.value = false;
  }
}

async function handleResync() {
  if (!props.nodeId) return;
  resyncing.value = true;
  try {
    snapshot.value = await resyncNodeSentinel(props.nodeId);
    createMessage.success(SENTINEL_TERM.resyncSuccess);
  } catch {
    createMessage.error(SENTINEL_TERM.loadFailed);
  } finally {
    resyncing.value = false;
  }
}

watch(
  () => props.nodeId,
  () => {
    loadSnapshot();
  },
  { immediate: true },
);

defineExpose({ reload: loadSnapshot });
</script>

<template>
  <div class="node-sentinel-panel">
    <Spin :spinning="loading">
      <Alert
        type="info"
        show-icon
        class="sentinel-alert"
        :message="SENTINEL_TERM.title"
        :description="SENTINEL_TERM.hint"
      />

      <div v-if="snapshot" class="sentinel-meta">
        <Tag :color="snapshot.fresh ? 'success' : 'default'">
          {{ snapshot.fresh ? SENTINEL_TERM.fresh : SENTINEL_TERM.stale }}
        </Tag>
        <span v-if="snapshot.nodeProfile">功能: {{ snapshot.nodeProfile }}</span>
        <span v-if="snapshot.probeLevel">探测: {{ snapshot.probeLevel }}</span>
        <span v-if="snapshot.lastProbeAt">更新: {{ formatToDateTime(snapshot.lastProbeAt) }}</span>
        <span v-if="snapshot.operationalState">{{ SENTINEL_TERM.operationalState }}: {{ snapshot.operationalState }}</span>
        <Button size="small" :loading="probing" @click="handleProbe">{{ SENTINEL_TERM.probe }}</Button>
        <Button size="small" :loading="resyncing" @click="handleResync">{{ SENTINEL_TERM.resync }}</Button>
        <Button size="small" @click="loadSnapshot">{{ SENTINEL_TERM.refresh }}</Button>
      </div>

      <p v-if="snapshot" class="sentinel-summary">{{ summaryText }}</p>

      <h4 class="sentinel-subtitle">{{ SENTINEL_TERM.componentSection }}</h4>
      <Table
        size="small"
        bordered
        :pagination="false"
        row-key="componentId"
        :columns="componentColumns"
        :data-source="snapshot?.components || []"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'state'">
            <Tag :color="stateColor(record.state)">{{ record.state }}</Tag>
          </template>
          <template v-else-if="column.key === 'expected'">
            <Tag :color="record.expected ? 'processing' : 'default'">
              {{ record.expected ? SENTINEL_TERM.yes : SENTINEL_TERM.no }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'healMark'">
            <Tag :color="healMarkColor(record.healMark)">{{ healMarkText(record.healMark) }}</Tag>
          </template>
          <template v-else-if="column.key === 'healAttempts'">
            <span v-if="record.healMaxAttempts">{{ record.healAttempts || 0 }}/{{ record.healMaxAttempts }}</span>
            <span v-else>{{ record.healAttempts || '—' }}</span>
          </template>
        </template>
        <template #emptyText>{{ SENTINEL_TERM.noData }}</template>
      </Table>

      <h4 class="sentinel-subtitle">{{ SENTINEL_TERM.capabilitySection }}</h4>
      <Table
        size="small"
        bordered
        :pagination="false"
        row-key="capability"
        :columns="capabilityColumns"
        :data-source="capabilityRows"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'schedulable'">
            <Tag :color="record.schedulable ? 'success' : 'error'">
              {{ record.schedulable ? SENTINEL_TERM.yes : SENTINEL_TERM.no }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'state'">
            <Tag :color="stateColor(record.state)">{{ record.state || '—' }}</Tag>
          </template>
        </template>
        <template #emptyText>{{ SENTINEL_TERM.noCapability }}</template>
      </Table>

      <h4 class="sentinel-subtitle">{{ SENTINEL_TERM.healSection }}</h4>
      <Table
        size="small"
        bordered
        :pagination="false"
        row-key="id"
        :columns="healLogColumns"
        :data-source="snapshot?.remediateLogs || []"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'success'">
            <Tag :color="record.success ? 'success' : 'error'">
              {{ record.success ? SENTINEL_TERM.yes : SENTINEL_TERM.no }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'mark'">
            <Tag :color="healMarkColor(record.mark)">{{ healMarkText(record.mark) }}</Tag>
          </template>
          <template v-else-if="column.key === 'createTime'">
            {{ record.createTime ? formatToDateTime(record.createTime) : '—' }}
          </template>
        </template>
        <template #emptyText>{{ SENTINEL_TERM.noHealLog }}</template>
      </Table>

      <h4 class="sentinel-subtitle">{{ SENTINEL_TERM.declaredSection }}</h4>
      <Table
        size="small"
        bordered
        :pagination="false"
        row-key="capability"
        :columns="declaredColumns"
        :data-source="declaredRows"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'declared' || column.key === 'schedulable'">
            <Tag :color="record[column.key] ? 'success' : 'default'">
              {{ record[column.key] ? SENTINEL_TERM.yes : SENTINEL_TERM.no }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'state'">
            <Tag :color="stateColor(record.state)">{{ record.state || '—' }}</Tag>
          </template>
        </template>
        <template #emptyText>{{ SENTINEL_TERM.noData }}</template>
      </Table>

      <h4 class="sentinel-subtitle">{{ SENTINEL_TERM.envSection }}</h4>
      <pre class="sentinel-env">{{ envProfileText }}</pre>
    </Spin>
  </div>
</template>

<style lang="less" scoped>
.node-sentinel-panel {
  .sentinel-alert {
    margin-bottom: 12px;
  }

  .sentinel-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    color: rgb(0 0 0 / 65%);
    font-size: 13px;
  }

  .sentinel-summary {
    margin: 0 0 12px;
    color: rgb(0 0 0 / 75%);
  }

  .sentinel-subtitle {
    margin: 16px 0 8px;
    font-size: 14px;
    font-weight: 600;
  }

  .sentinel-env {
    margin: 0;
    padding: 12px;
    overflow: auto;
    max-height: 240px;
    font-size: 12px;
    background: rgb(0 0 0 / 3%);
    border-radius: 4px;
  }
}
</style>
