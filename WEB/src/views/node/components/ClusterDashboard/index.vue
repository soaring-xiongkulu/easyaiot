<script lang="ts" setup>
import { computed } from 'vue';
import { Button } from '@/components/Button';
import { ApiSelect, RadioButtonGroup } from '@/components/Form';
import { getPanelConsoleUrl, openPanelConsole } from '@/utils/panel';
import TrendChart from './TrendChart.vue';
import GaugePanel from './GaugePanel.vue';
import GpuVramOverview from './GpuVramOverview.vue';
import DiskStorageOverview from './DiskStorageOverview.vue';
import NodeLoadChart from './NodeLoadChart.vue';
import { useClusterDashboard } from './useClusterDashboard';
import { formatPercent, formatStorageRange } from '../../utils/clusterMetrics';
import { NODE_DASHBOARD, NODE_METRIC, OVERVIEW_ALL_NODES_ID, TREND_SAMPLE_INTERVAL_OPTIONS } from '../../utils/constants';

defineOptions({ name: 'ClusterDashboard' });

const panelConsoleUrl = computed(() => getPanelConsoleUrl());

const {
  loading,
  wsStatus,
  trendViewMode,
  trendMetric,
  selectedNodeIds,
  overviewFocusNodeId,
  nodes,
  displaySnapshot,
  trendHistory,
  displayNodeTrendSeries,
  displayGpuGroups,
  displayNodeLoads,
  displayNodeDisks,
  lastUpdated,
  computeNodeOptions,
  trendSampleIntervalSec,
  activeLaneKey,
  setActiveLaneKey,
  centralLaneOptions,
} = useClusterDashboard();

const trendSampleIntervalOptions = TREND_SAMPLE_INTERVAL_OPTIONS.map((item) => ({
  label: item.label,
  value: item.value,
}));

const overviewNodeOptions = computed(() => [
  { label: NODE_DASHBOARD.overviewNodeFocusAll, value: OVERVIEW_ALL_NODES_ID },
  ...computeNodeOptions.value,
]);

const overviewFocusSelectValue = computed({
  get: () => overviewFocusNodeId.value ?? OVERVIEW_ALL_NODES_ID,
  set: (value: number) => {
    overviewFocusNodeId.value = value === OVERVIEW_ALL_NODES_ID ? undefined : value;
  },
});

const centralLaneSelectValue = computed({
  get: () => activeLaneKey.value,
  set: (value: string) => setActiveLaneKey(value),
});

function filterLane(input: string, option: { label?: string }) {
  return (option.label || '').toLowerCase().includes(input.toLowerCase());
}

function backToAllNodes() {
  overviewFocusNodeId.value = undefined;
}

const statCards = computed(() => [
  { label: NODE_DASHBOARD.statTotal, value: displaySnapshot.value.total },
  { label: NODE_DASHBOARD.statGpuCount, value: displaySnapshot.value.gpuCount },
  {
    label: NODE_DASHBOARD.statVramCapacity,
    value: formatStorageRange(
      displaySnapshot.value.gpuMemUsedBytes,
      displaySnapshot.value.gpuMemTotalBytes,
    ),
    sub:
      displaySnapshot.value.gpuMemTotalBytes > 0
        ? formatPercent(displaySnapshot.value.avgGpuMem)
        : undefined,
    subLabel: NODE_DASHBOARD.statCapacityUsageAvg,
  },
  {
    label: NODE_DASHBOARD.statMemCapacity,
    value: formatStorageRange(displaySnapshot.value.memUsedBytes, displaySnapshot.value.memTotalBytes),
    sub: displaySnapshot.value.memTotalBytes > 0 ? formatPercent(displaySnapshot.value.avgMem) : undefined,
    subLabel: NODE_DASHBOARD.statCapacityUsageAvg,
  },
  {
    label: NODE_DASHBOARD.statDiskCapacity,
    value: formatStorageRange(displaySnapshot.value.diskUsedBytes, displaySnapshot.value.diskTotalBytes),
    sub: displaySnapshot.value.diskTotalBytes > 0 ? formatPercent(displaySnapshot.value.avgDisk) : undefined,
    subLabel: NODE_DASHBOARD.statCapacityUsageAvg,
  },
  { label: NODE_DASHBOARD.statOnlineRate, value: formatPercent(displaySnapshot.value.availability) },
]);

const metricOptions = computed(() => [
  { label: NODE_METRIC.cpu, value: 'cpu' as const },
  { label: NODE_METRIC.mem, value: 'mem' as const },
  { label: NODE_METRIC.vram, value: 'gpuMem' as const },
  { label: NODE_METRIC.gpuUtil, value: 'gpuUtil' as const },
  { label: NODE_METRIC.disk, value: 'disk' as const },
]);

const trendViewOptions = computed(() => [
  { label: NODE_DASHBOARD.trendViewCluster, value: 'cluster' as const },
  { label: NODE_DASHBOARD.trendViewNode, value: 'node' as const },
]);

const wsStatusLabel = computed(() => {
  if (wsStatus.value === 'open') return NODE_DASHBOARD.wsConnected;
  if (wsStatus.value === 'connecting') return NODE_DASHBOARD.wsConnecting;
  return NODE_DASHBOARD.wsDisconnected;
});

const trendHint = computed(() => {
  if (overviewFocusNodeId.value) {
    return NODE_DASHBOARD.overviewNodeFocusHint;
  }
  return trendViewMode.value === 'cluster'
    ? NODE_DASHBOARD.trendClusterHint
    : NODE_DASHBOARD.trendNodeHint;
});

const effectiveTrendViewMode = computed(() =>
  overviewFocusNodeId.value ? 'node' : trendViewMode.value,
);

const effectiveSelectedNodeIds = computed(() => {
  if (overviewFocusNodeId.value) {
    return [overviewFocusNodeId.value];
  }
  return selectedNodeIds.value;
});
</script>

<template>
  <div class="overview-page">
    <section class="stat-cards">
      <div v-for="item in statCards" :key="item.label" class="stat-card">
        <span class="stat-card__label">{{ item.label }}</span>
        <span class="stat-card__value" :class="{ 'stat-card__value--compact': item.sub }">{{ item.value }}</span>
        <span v-if="item.sub" class="stat-card__sub">
          <span class="stat-card__sub-label">{{ item.subLabel }}</span>
          <span class="stat-card__sub-value">{{ item.sub }}</span>
        </span>
      </div>
    </section>

    <section class="load-section">
      <div class="load-section__head">
        <h2 class="load-section__title">{{ NODE_DASHBOARD.clusterLoad }}</h2>
        <div class="load-section__head-right">
          <div class="load-section__scope-controls">
            <Button
              type="primary"
              class="load-section__console-btn"
              :title="panelConsoleUrl"
              @click="openPanelConsole"
            >
              {{ NODE_DASHBOARD.openPanelAction }}
            </Button>
            <label class="control-item load-section__central-node">
              <span>{{ NODE_DASHBOARD.overviewCentralNode }}</span>
              <ApiSelect
                v-model:value="centralLaneSelectValue"
                show-search
                class="load-section__scope-select"
                :options="centralLaneOptions"
                :filter-option="filterLane"
                :immediate="false"
              />
            </label>
            <label class="control-item load-section__node-focus">
              <span>{{ NODE_DASHBOARD.overviewNodeFocus }}</span>
              <ApiSelect
                v-model:value="overviewFocusSelectValue"
                show-search
                allow-clear
                size="small"
                class="load-section__scope-select"
                :options="overviewNodeOptions"
                :filter-option="filterLane"
                :immediate="false"
              />
              <Button
                v-if="overviewFocusNodeId"
                type="link"
                size="small"
                class="load-section__back"
                @click="backToAllNodes"
              >
                {{ NODE_DASHBOARD.overviewBackToAll }}
              </Button>
            </label>
          </div>
          <div class="load-section__status">
            <span class="ws-status" :class="`ws-status--${wsStatus}`">{{ wsStatusLabel }}</span>
            <span v-if="lastUpdated" class="action-sep" aria-hidden="true">·</span>
            <time v-if="lastUpdated" class="data-sync" :title="`数据更新于 ${lastUpdated}`">
              更新 {{ lastUpdated }}
            </time>
          </div>
        </div>
      </div>

      <div class="mode-toolbar">
        <RadioButtonGroup
          v-model:value="trendViewMode"
          :options="trendViewOptions"
          size="middle"
          class="mode-radio-group"
          :disabled="!!overviewFocusNodeId"
        />
        <span class="mode-hint">{{ trendHint }}</span>
        <label class="control-item mode-toolbar__interval" :title="NODE_DASHBOARD.trendSampleIntervalHint">
          <span>{{ NODE_DASHBOARD.trendSampleIntervalLabel }}</span>
          <ApiSelect
            v-model:value="trendSampleIntervalSec"
            :options="trendSampleIntervalOptions"
            size="small"
            style="width: 88px"
            :immediate="false"
          />
        </label>
      </div>

      <div v-if="!overviewFocusNodeId" class="load-section__filters">
        <label v-if="trendViewMode === 'node'" class="control-item">
          <span>{{ NODE_DASHBOARD.trendMetricLabel }}</span>
          <ApiSelect
            v-model:value="trendMetric"
            :options="metricOptions"
            size="small"
            style="min-width: 120px"
            :immediate="false"
          />
        </label>
        <label class="control-item">
          <span>{{ NODE_DASHBOARD.trendNodeFilter }}</span>
          <ApiSelect
            v-model:value="selectedNodeIds"
            mode="multiple"
            allow-clear
            :max-tag-count="2"
            :options="computeNodeOptions"
            :placeholder="NODE_DASHBOARD.trendNodeFilterAll"
            size="small"
            style="min-width: 220px"
            :immediate="false"
          />
        </label>
      </div>

      <div v-show="loading && !nodes.length" class="load-section__loading">加载中...</div>

      <div v-show="!loading || nodes.length" class="load-section__body">
        <div class="load-section__chart">
          <TrendChart
            :view-mode="effectiveTrendViewMode"
            :metric-key="trendMetric"
            :cluster-data="trendHistory"
            :node-series="displayNodeTrendSeries"
            :selected-node-ids="effectiveSelectedNodeIds"
          />
        </div>
        <div class="load-section__gauges">
          <GaugePanel :title="NODE_DASHBOARD.avgVramUsage" :value="displaySnapshot.avgGpuMem" />
          <GaugePanel :title="NODE_DASHBOARD.avgCpuUsage" :value="displaySnapshot.avgCpu" />
          <GaugePanel :title="NODE_DASHBOARD.avgMemUsage" :value="displaySnapshot.avgMem" />
          <GaugePanel :title="NODE_DASHBOARD.avgDiskUsage" :value="displaySnapshot.avgDisk" />
        </div>
      </div>
    </section>

    <section class="gpu-section">
      <div class="section-head">
        <h3>{{ NODE_DASHBOARD.sectionVram }}</h3>
        <span class="section-hint">{{ NODE_DASHBOARD.sectionVramHint }}</span>
      </div>
      <GpuVramOverview :groups="displayGpuGroups" />
    </section>

    <section class="storage-section">
      <div class="section-head">
        <h3>{{ NODE_DASHBOARD.sectionDisk }}</h3>
        <span class="section-hint">
          {{ NODE_DASHBOARD.sectionDiskHint }}
          <template v-if="displaySnapshot.diskWarningCount > 0">
            · <span class="section-hint--warn">{{ NODE_DASHBOARD.diskWarningNodes(displaySnapshot.diskWarningCount) }}</span>
          </template>
        </span>
      </div>
      <DiskStorageOverview :nodes="displayNodeDisks" />
    </section>

    <section class="node-section">
      <div class="section-head">
        <h3>{{ NODE_DASHBOARD.sectionResource }}</h3>
        <span class="section-hint">{{ NODE_DASHBOARD.sectionResourceHint }}</span>
      </div>
      <NodeLoadChart :nodes="displayNodeLoads" />
    </section>
  </div>
</template>

<style lang="less" scoped>
@import '../../utils/theme.less';

.overview-page {
  padding: 4px 8px 24px;
  background: @node-bg;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 20px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 20px;
  background: @node-bg;
  border: 1px solid @node-border;
  border-radius: @node-radius;
  text-align: center;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;

  &:hover {
    border-color: @node-primary-light;
    box-shadow: @node-card-shadow-hover;
  }
}

.stat-card__label {
  display: block;
  font-size: @node-font-body;
  color: @node-text-secondary;
  margin-bottom: 10px;
}

.stat-card__value {
  display: block;
  font-size: 32px;
  font-weight: 600;
  color: @node-text-primary;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;

  &--compact {
    font-size: 22px;
  }
}

.stat-card__sub {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.stat-card__sub-label {
  color: @node-text-secondary;
}

.stat-card__sub-value {
  color: @node-text-secondary;
  font-weight: 500;
}

.load-section {
  margin-bottom: 28px;
}

.load-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.load-section__head-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 20px;
  min-width: 0;
}

.load-section__scope-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 20px;
  flex-shrink: 0;
}

.load-section__console-btn {
  flex-shrink: 0;
}

.load-section__central-node,
.load-section__node-focus {
  flex-shrink: 0;
}

.load-section__scope-select {
  min-width: 220px;
}

.load-section__back {
  padding: 0;
  height: auto;
  font-size: 13px;
}

.load-section__title {
  margin: 0;
  font-size: @node-font-title;
  font-weight: 600;
  color: @node-text-primary;
  padding-left: 14px;
  position: relative;
  flex-shrink: 0;

  &::before {
    position: absolute;
    top: 4px;
    left: 0;
    width: 4px;
    height: 20px;
    background: @node-primary;
    content: '';
    border-radius: 2px;
  }
}

.load-section__status {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: @node-font-caption;
  color: @node-text-muted;
}

.ws-status {
  &--open {
    color: #52c41a;
  }

  &--connecting {
    color: #faad14;
  }

  &--closed {
    color: #ff4d4f;
  }
}

.mode-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  margin-bottom: 12px;
  background: #fff;
  border: 1px solid @node-border;
  border-radius: @node-radius;

  .mode-radio-group {
    :deep(.ant-radio-button-wrapper) {
      height: auto;
      line-height: 1;
      padding: 6px 14px;
    }
  }

  .mode-hint {
    color: #6b7280;
    font-size: 13px;
  }

  .mode-toolbar__interval {
    margin-left: auto;
  }
}

.load-section__filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  margin-bottom: 12px;
  padding: 0 16px;
}

.control-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: @node-font-caption;
  color: @node-text-secondary;
}

.data-sync {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.action-sep {
  color: @node-border;
  line-height: 1;
  user-select: none;
}

.load-section__loading {
  padding: 48px 24px;
  text-align: center;
  color: @node-text-muted;
  background: @node-bg;
  border: 1px solid @node-border;
  border-radius: @node-radius;
}

.load-section__body {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  padding: 24px;
  background: @node-bg;
  border: 1px solid @node-border;
  border-radius: @node-radius;
}

.load-section__gauges {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  align-content: start;
  overflow: visible;
}

.storage-section,
.gpu-section,
.node-section {
  margin-bottom: 24px;
}

.section-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;

  h3 {
    margin: 0;
    font-size: @node-font-title;
    font-weight: 600;
    color: @node-text-primary;
    padding-left: 14px;
    position: relative;

    &::before {
      position: absolute;
      top: 4px;
      left: 0;
      width: 4px;
      height: 20px;
      background: @node-primary;
      content: '';
      border-radius: 2px;
    }
  }
}

.section-hint {
  font-size: @node-font-body;
  color: @node-text-secondary;
}

.section-hint--warn {
  color: #ff4d4f;
  font-weight: 500;
}

@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }

  .load-section__body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .load-section__head {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .load-section__head-right {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .load-section__scope-controls {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .load-section__scope-select {
    min-width: 0;
    width: 100%;
  }
}
</style>
