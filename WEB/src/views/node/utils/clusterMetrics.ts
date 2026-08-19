import type { ComputeNodeVO } from '@/api/device/node';
import { NODE_INSIGHT, NODE_METRIC, NODE_TERM, parseGpuInfo, isSchedulableComputeNode, nodeHasAnyFunction, type GpuInfoItem } from './constants';

const MB_BYTES = 1024 * 1024;

export function aggregateGpuVram(gpus: GpuInfoItem[]): {
  usedBytes: number;
  totalBytes: number;
  avgPercent: number;
} {
  let usedMb = 0;
  let totalMb = 0;
  gpus.forEach((g) => {
    usedMb += num(g.mem_used_mb);
    totalMb += num(g.mem_total_mb);
  });
  return {
    usedBytes: usedMb * MB_BYTES,
    totalBytes: totalMb * MB_BYTES,
    avgPercent: totalMb > 0 ? Math.round((usedMb / totalMb) * 1000) / 10 : 0,
  };
}

export interface ClusterTrendPoint {
  time: string;
  timestamp: number;
  cpu: number;
  mem: number;
  disk: number;
  gpuUtil: number;
  gpuMem: number;
  memUsedBytes: number;
  diskUsedBytes: number;
  gpuMemUsedBytes: number;
  activeTasks: number;
  onlineCompute: number;
}

export type TrendMetricKey = 'cpu' | 'mem' | 'disk' | 'gpuMem' | 'gpuUtil';

export type TrendQuantityKey = 'mem' | 'disk' | 'gpuMem';

export function isTrendVolumeMetric(key: TrendMetricKey): key is TrendQuantityKey {
  return key === 'mem' || key === 'disk' || key === 'gpuMem';
}

function sumGpuMemUsedBytes(gpus: GpuInfoItem[]): number {
  return gpus.reduce((sum, gpu) => sum + num(gpu.mem_used_mb) * MB_BYTES, 0);
}

export type TrendViewMode = 'cluster' | 'node';

export interface NodeTrendPoint {
  time: string;
  timestamp: number;
  cpu: number;
  mem: number;
  disk: number;
  gpuMem: number;
  gpuUtil: number;
  memUsedBytes?: number;
  diskUsedBytes?: number;
  gpuMemUsedBytes?: number;
  activeTasks: number;
}

export interface NodeTrendSeries {
  nodeId: number;
  nodeName: string;
  host: string;
  status?: string;
  points: NodeTrendPoint[];
}

export interface GpuCardMetric {
  key: string;
  nodeId: number;
  nodeName: string;
  gpuId: number;
  name: string;
  util: number;
  memUsedMb: number;
  memTotalMb: number;
  memPercent: number;
}

export interface ClusterSnapshot {
  total: number;
  online: number;
  offline: number;
  pending: number;
  maintenance: number;
  computeOnline: number;
  mediaOnline: number;
  activeTasks: number;
  maxTasks: number;
  gpuCount: number;
  avgCpu: number;
  avgMem: number;
  avgDisk: number;
  avgGpuUtil: number;
  avgGpuMem: number;
  availability: number;
  diskWarningCount: number;
  memUsedBytes: number;
  memTotalBytes: number;
  diskUsedBytes: number;
  diskTotalBytes: number;
  gpuMemUsedBytes: number;
  gpuMemTotalBytes: number;
}

export interface NodeDiskItem {
  id: number;
  name: string;
  host: string;
  status?: string;
  disk: number;
  diskUsedBytes?: number;
  diskTotalBytes?: number;
}

export interface NodeGpuGroup {
  nodeId: number;
  nodeName: string;
  host: string;
  status?: string;
  gpus: GpuCardMetric[];
  avgUtil: number;
  avgVram: number;
}

export interface NodeLoadItem {
  id: number;
  name: string;
  host: string;
  status?: string;
  nodeRole?: string;
  cpu: number;
  mem: number;
  disk: number;
  memUsedBytes?: number;
  memTotalBytes?: number;
  diskUsedBytes?: number;
  diskTotalBytes?: number;
  activeTasks: number;
  gpuCount: number;
  avgGpuUtil: number;
  avgVram: number;
  gpuInfo?: string;
}

function avg(values: number[]): number {
  if (!values.length) return 0;
  return Math.round((values.reduce((sum, v) => sum + v, 0) / values.length) * 10) / 10;
}

function num(val?: number | null): number {
  if (val == null || Number.isNaN(Number(val))) return 0;
  return Number(val);
}

export function isComputeNode(node: ComputeNodeVO): boolean {
  return isSchedulableComputeNode(node);
}

export function isOnlineComputeNode(node: ComputeNodeVO): boolean {
  return node.status === 'online' && isComputeNode(node);
}

export function collectGpuCards(nodes: ComputeNodeVO[]): GpuCardMetric[] {
  const cards: GpuCardMetric[] = [];
  nodes.filter(isOnlineComputeNode).forEach((node) => {
    const parsed = parseGpuInfo(node.gpuInfo);
    if (parsed.length) {
      parsed.forEach((gpu) => {
        const memTotal = num(gpu.mem_total_mb);
        const memUsed = num(gpu.mem_used_mb);
        const memPercent = memTotal > 0 ? Math.round((memUsed / memTotal) * 1000) / 10 : 0;
        cards.push({
          key: `${node.id}-${gpu.id ?? 0}`,
          nodeId: node.id!,
          nodeName: node.name,
          gpuId: gpu.id ?? 0,
          name: gpu.name || `GPU ${gpu.id ?? 0}`,
          util: num(gpu.util),
          memUsedMb: memUsed,
          memTotalMb: memTotal,
          memPercent,
        });
      });
      return;
    }
    // 心跳 gpuInfo 尚未写入时，用节点配置的 maxGpuCount 兜底卡数量（显存可能暂为 0）
    const maxCount = Math.max(0, Math.floor(num(node.maxGpuCount)));
    for (let i = 0; i < maxCount; i += 1) {
      cards.push({
        key: `${node.id}-cfg-${i}`,
        nodeId: node.id!,
        nodeName: node.name,
        gpuId: i,
        name: `GPU ${i}`,
        util: 0,
        memUsedMb: 0,
        memTotalMb: 0,
        memPercent: 0,
      });
    }
  });
  return cards.sort((a, b) => b.util - a.util || b.memPercent - a.memPercent);
}

export function groupGpusByNode(nodes: ComputeNodeVO[]): NodeGpuGroup[] {
  const map = new Map<number, NodeGpuGroup>();
  collectGpuCards(nodes).forEach((card) => {
    let group = map.get(card.nodeId);
    if (!group) {
      const node = nodes.find((n) => n.id === card.nodeId);
      group = {
        nodeId: card.nodeId,
        nodeName: card.nodeName,
        host: node?.host || '',
        status: node?.status,
        gpus: [],
        avgUtil: 0,
        avgVram: 0,
      };
      map.set(card.nodeId, group);
    }
    group.gpus.push(card);
  });
  return Array.from(map.values())
    .map((group) => {
      group.gpus.sort((a, b) => a.gpuId - b.gpuId);
      group.avgUtil = avg(group.gpus.map((g) => g.util));
      group.avgVram = avg(group.gpus.map((g) => g.memPercent));
      return group;
    })
    .sort((a, b) => b.avgVram - a.avgVram || b.avgUtil - a.avgUtil);
}

export function buildNodeLoadList(nodes: ComputeNodeVO[]): NodeLoadItem[] {
  return nodes
    .filter(isComputeNode)
    .map((node) => {
      const gpus = parseGpuInfo(node.gpuInfo);
      let gpuInfoStr: string | undefined;
      try {
        gpuInfoStr =
          typeof node.gpuInfo === 'string'
            ? node.gpuInfo
            : gpus.length
              ? JSON.stringify(gpus)
              : undefined;
      } catch {
        gpuInfoStr = undefined;
      }
      return {
        id: node.id!,
        name: node.name,
        host: node.host,
        status: node.status,
        nodeRole: node.nodeRole,
        cpu: num(node.cpuPercent),
        mem: num(node.memPercent),
        disk: num(node.diskPercent),
        memUsedBytes: num(node.memUsedBytes) || undefined,
        memTotalBytes: num(node.memTotalBytes) || undefined,
        diskUsedBytes: num(node.diskUsedBytes) || undefined,
        diskTotalBytes: num(node.diskTotalBytes) || undefined,
        activeTasks: num(node.activeTasks),
        gpuCount: Math.max(gpus.length, Math.floor(num(node.maxGpuCount))),
        avgGpuUtil: avg(gpus.map((g) => num(g.util))),
        avgVram: avg(
          gpus.map((g) => {
            const total = num(g.mem_total_mb);
            const used = num(g.mem_used_mb);
            return total > 0 ? (used / total) * 100 : 0;
          }),
        ),
        gpuInfo: gpuInfoStr,
      };
    })
    .sort((a, b) => b.cpu - a.cpu || b.activeTasks - a.activeTasks);
}

export function buildNodeDiskList(nodes: ComputeNodeVO[]): NodeDiskItem[] {
  return nodes
    .filter(isComputeNode)
    .map((node) => ({
      id: node.id!,
      name: node.name,
      host: node.host,
      status: node.status,
      disk: num(node.diskPercent),
      diskUsedBytes: num(node.diskUsedBytes) || undefined,
      diskTotalBytes: num(node.diskTotalBytes) || undefined,
    }))
    .sort((a, b) => b.disk - a.disk || a.name.localeCompare(b.name));
}

function hasMemCapacity(node: ComputeNodeVO): boolean {
  return num(node.memTotalBytes) > 0;
}

function hasDiskCapacity(node: ComputeNodeVO): boolean {
  return num(node.diskTotalBytes) > 0;
}

export function buildClusterSnapshot(nodes: ComputeNodeVO[]): ClusterSnapshot {
  const onlineNodes = nodes.filter((n) => n.status === 'online');
  const computeNodes = nodes.filter(isComputeNode);
  const computeOnline = onlineNodes.filter(isComputeNode);
  const computeWithMem = computeNodes.filter(hasMemCapacity);
  const computeWithDisk = computeNodes.filter(hasDiskCapacity);
  const mediaOnline = onlineNodes.filter((n) => nodeHasAnyFunction(n, ['live', 'forward']));
  const gpuCards = collectGpuCards(nodes);

  return {
    total: nodes.length,
    online: nodes.filter((n) => n.status === 'online').length,
    offline: nodes.filter((n) => n.status === 'offline').length,
    pending: nodes.filter((n) => n.status === 'pending').length,
    maintenance: nodes.filter((n) => n.status === 'maintenance').length,
    computeOnline: computeOnline.length,
    mediaOnline: mediaOnline.length,
    activeTasks: computeOnline.reduce((sum, n) => sum + num(n.activeTasks), 0),
    maxTasks: computeOnline.reduce((sum, n) => sum + num(n.maxTaskCount || 0), 0),
    gpuCount: gpuCards.length,
    avgCpu: avg(computeNodes.map((n) => num(n.cpuPercent))),
    avgMem: avg(computeWithMem.map((n) => num(n.memPercent))),
    avgDisk: avg(computeWithDisk.map((n) => num(n.diskPercent))),
    avgGpuUtil: avg(gpuCards.map((g) => g.util)),
    avgGpuMem: avg(gpuCards.map((g) => g.memPercent)),
    availability: nodes.length
      ? Math.round((onlineNodes.length / nodes.length) * 100)
      : 0,
    diskWarningCount: computeWithDisk.filter((n) => num(n.diskPercent) >= 85).length,
    memUsedBytes: computeWithMem.reduce((sum, n) => sum + num(n.memUsedBytes), 0),
    memTotalBytes: computeWithMem.reduce((sum, n) => sum + num(n.memTotalBytes), 0),
    diskUsedBytes: computeWithDisk.reduce((sum, n) => sum + num(n.diskUsedBytes), 0),
    diskTotalBytes: computeWithDisk.reduce((sum, n) => sum + num(n.diskTotalBytes), 0),
    gpuMemUsedBytes: gpuCards.reduce((sum, g) => sum + g.memUsedMb * MB_BYTES, 0),
    gpuMemTotalBytes: gpuCards.reduce((sum, g) => sum + g.memTotalMb * MB_BYTES, 0),
  };
}

export function appendTrendPoint(
  history: ClusterTrendPoint[],
  snapshot: ClusterSnapshot,
  maxPoints = 120,
  minIntervalMs = 7000,
): ClusterTrendPoint[] {
  const now = new Date();
  const point: ClusterTrendPoint = {
    time: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`,
    timestamp: now.getTime(),
    cpu: snapshot.avgCpu,
    mem: snapshot.avgMem,
    disk: snapshot.avgDisk,
    gpuUtil: snapshot.avgGpuUtil,
    gpuMem: snapshot.avgGpuMem,
    memUsedBytes: snapshot.memUsedBytes,
    diskUsedBytes: snapshot.diskUsedBytes,
    gpuMemUsedBytes: snapshot.gpuMemUsedBytes,
    activeTasks: snapshot.activeTasks,
    onlineCompute: snapshot.computeOnline,
  };
  const last = history[history.length - 1];
  if (last && now.getTime() - last.timestamp < minIntervalMs) {
    const next = [...history];
    next[next.length - 1] = point;
    return next;
  }
  const next = [...history, point];
  return next.length > maxPoints ? next.slice(next.length - maxPoints) : next;
}

function formatTrendTime(date: Date): string {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
}

function parseCollectedAt(value?: string | null): Date {
  if (!value) return new Date();
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date() : parsed;
}

export function buildNodeTrendPointFromNode(node: ComputeNodeVO, at = new Date()): NodeTrendPoint {
  const gpus = parseGpuInfo(node.gpuInfo);
  return {
    time: formatTrendTime(at),
    timestamp: at.getTime(),
    cpu: num(node.cpuPercent),
    mem: num(node.memPercent),
    disk: num(node.diskPercent),
    gpuUtil: avg(gpus.map((g) => num(g.util))),
    gpuMem: avg(
      gpus.map((g) => {
        const total = num(g.mem_total_mb);
        const used = num(g.mem_used_mb);
        return total > 0 ? (used / total) * 100 : 0;
      }),
    ),
    memUsedBytes: num(node.memUsedBytes),
    diskUsedBytes: num(node.diskUsedBytes),
    gpuMemUsedBytes: sumGpuMemUsedBytes(gpus),
    activeTasks: num(node.activeTasks),
  };
}

export function buildNodeTrendPointFromApi(
  point: {
    collectedAt?: string;
    cpuPercent?: number;
    memPercent?: number;
    diskPercent?: number;
    gpuMemPercent?: number;
    gpuUtilPercent?: number;
    memUsedBytes?: number;
    diskUsedBytes?: number;
    gpuMemUsedBytes?: number;
    activeTasks?: number;
  },
): NodeTrendPoint {
  const at = parseCollectedAt(point.collectedAt);
  return {
    time: formatTrendTime(at),
    timestamp: at.getTime(),
    cpu: num(point.cpuPercent),
    mem: num(point.memPercent),
    disk: num(point.diskPercent),
    gpuMem: num(point.gpuMemPercent),
    gpuUtil: num(point.gpuUtilPercent),
    memUsedBytes: num(point.memUsedBytes),
    diskUsedBytes: num(point.diskUsedBytes),
    gpuMemUsedBytes: num(point.gpuMemUsedBytes),
    activeTasks: num(point.activeTasks),
  };
}

export function mergeNodeTrendSeries(
  existing: NodeTrendSeries[],
  incoming: NodeTrendSeries[],
  maxPoints = 120,
): NodeTrendSeries[] {
  const map = new Map<number, NodeTrendSeries>();
  existing.forEach((series) => map.set(series.nodeId, { ...series, points: [...series.points] }));
  incoming.forEach((series) => {
    const prev = map.get(series.nodeId);
    if (!prev) {
      map.set(series.nodeId, { ...series, points: trimTrendPoints(series.points, maxPoints) });
      return;
    }
    prev.nodeName = series.nodeName;
    prev.host = series.host;
    prev.status = series.status;
    prev.points = trimTrendPoints(mergeTrendPoints(prev.points, series.points), maxPoints);
  });
  return Array.from(map.values()).sort((a, b) => a.nodeName.localeCompare(b.nodeName));
}

function mergeTrendPoints(existing: NodeTrendPoint[], incoming: NodeTrendPoint[]): NodeTrendPoint[] {
  const map = new Map<number, NodeTrendPoint>();
  existing.forEach((point) => map.set(point.timestamp, point));
  incoming.forEach((point) => map.set(point.timestamp, point));
  return Array.from(map.values()).sort((a, b) => a.timestamp - b.timestamp);
}

function trimTrendPoints(points: NodeTrendPoint[], maxPoints: number): NodeTrendPoint[] {
  return points.length > maxPoints ? points.slice(points.length - maxPoints) : points;
}

export function appendLiveNodeTrendPoints(
  seriesList: NodeTrendSeries[],
  nodes: ComputeNodeVO[],
  maxPoints = 120,
  minIntervalMs = 7000,
): NodeTrendSeries[] {
  const now = new Date();
  const computeNodes = nodes.filter(isComputeNode);
  const map = new Map<number, NodeTrendSeries>();
  seriesList.forEach((series) => map.set(series.nodeId, { ...series, points: [...series.points] }));

  computeNodes.forEach((node) => {
    if (!node.id) return;
    const point = buildNodeTrendPointFromNode(node, now);
    let series = map.get(node.id);
    if (!series) {
      series = {
        nodeId: node.id,
        nodeName: node.name,
        host: node.host,
        status: node.status,
        points: [],
      };
      map.set(node.id, series);
    }
    series.nodeName = node.name;
    series.host = node.host;
    series.status = node.status;
    const last = series.points[series.points.length - 1];
    if (last && now.getTime() - last.timestamp < minIntervalMs) {
      series.points[series.points.length - 1] = point;
    } else {
      series.points = trimTrendPoints([...series.points, point], maxPoints);
    }
  });

  return Array.from(map.values()).sort((a, b) => a.nodeName.localeCompare(b.nodeName));
}

export function buildNodeTrendSeriesFromApi(
  series: Array<{
    nodeId: number;
    nodeName: string;
    host: string;
    status?: string;
    points: Array<{
      collectedAt?: string;
      cpuPercent?: number;
      memPercent?: number;
      diskPercent?: number;
      gpuMemPercent?: number;
      gpuUtilPercent?: number;
      memUsedBytes?: number;
      diskUsedBytes?: number;
      gpuMemUsedBytes?: number;
      activeTasks?: number;
    }>;
  }>,
): NodeTrendSeries[] {
  return series.map((item) => ({
    nodeId: item.nodeId,
    nodeName: item.nodeName,
    host: item.host,
    status: item.status,
    points: item.points.map(buildNodeTrendPointFromApi),
  }));
}

export const NODE_TREND_COLORS = [
  '#1677ff',
  '#52c41a',
  '#faad14',
  '#722ed1',
  '#13c2c2',
  '#eb2f96',
  '#fa541c',
  '#2f54eb',
  '#a0d911',
  '#597ef7',
] as const;

export function getTrendMetricValue(point: NodeTrendPoint | ClusterTrendPoint, key: TrendMetricKey): number {
  switch (key) {
    case 'cpu':
      return point.cpu;
    case 'mem':
      return point.mem;
    case 'disk':
      return point.disk;
    case 'gpuMem':
      return point.gpuMem;
    case 'gpuUtil':
      return 'gpuUtil' in point ? point.gpuUtil : 0;
    default:
      return 0;
  }
}

export function getTrendVolumeBytes(point: NodeTrendPoint, key: TrendQuantityKey): number | null {
  let value: number | undefined;
  switch (key) {
    case 'mem':
      value = point.memUsedBytes;
      break;
    case 'disk':
      value = point.diskUsedBytes;
      break;
    case 'gpuMem':
      value = point.gpuMemUsedBytes;
      break;
    default:
      return null;
  }
  if (value == null) return null;
  return value;
}

export function formatTrendAxisBytes(value: number): string {
  if (value <= 0) return '0';
  return formatStorageBytes(value);
}

export function formatTrendTooltipValue(value: number | null | undefined, key: TrendMetricKey): string {
  if (value == null) return '-';
  if (isTrendVolumeMetric(key)) return formatStorageBytes(value);
  return formatCpuQuantity(value);
}

export function formatCpuQuantity(val?: number | null): string {
  if (val == null) return '—';
  return formatPercent(val);
}

/** 每个节点一组四色：CPU / 内存 / 显存 / 磁盘 */
export const NODE_TREND_PALETTES = [
  { cpu: '#faad14', mem: '#722ed1', vram: '#52c41a', disk: '#13c2c2' },
  { cpu: '#fa541c', mem: '#9254de', vram: '#73d13d', disk: '#36cfc9' },
  { cpu: '#d48806', mem: '#531dab', vram: '#389e0d', disk: '#08979c' },
  { cpu: '#ff7a45', mem: '#b37feb', vram: '#95de64', disk: '#5cdbd3' },
  { cpu: '#ffc53d', mem: '#597ef7', vram: '#237804', disk: '#006d75' },
  { cpu: '#ff9c6e', mem: '#2f54eb', vram: '#7cb305', disk: '#08979c' },
  { cpu: '#ffd666', mem: '#10239e', vram: '#52c41a', disk: '#13a8a8' },
  { cpu: '#d4b106', mem: '#391085', vram: '#389e0d', disk: '#006d75' },
] as const;

export type NodeTrendPalette = (typeof NODE_TREND_PALETTES)[number];

export function getNodeTrendPalette(nodeIndex: number): NodeTrendPalette {
  return NODE_TREND_PALETTES[nodeIndex % NODE_TREND_PALETTES.length];
}

type ClusterNodeTrendMetricKey = 'cpu' | TrendQuantityKey;

const CLUSTER_NODE_TREND_METRICS: Array<{ key: ClusterNodeTrendMetricKey; name: string; axis: 'cpu' | 'volume' }> = [
  { key: 'cpu', name: NODE_METRIC.cpu, axis: 'cpu' },
  { key: 'mem', name: NODE_METRIC.mem, axis: 'volume' },
  { key: 'gpuMem', name: NODE_METRIC.vram, axis: 'volume' },
  { key: 'disk', name: NODE_METRIC.disk, axis: 'volume' },
];

function getClusterNodeTrendMetricValue(
  point: NodeTrendPoint,
  key: ClusterNodeTrendMetricKey,
): number | null {
  if (key === 'cpu') {
    return point.cpu ?? null;
  }
  return getTrendVolumeBytes(point, key);
}

/** 向前填充缺失点，保证折线连续 */
export function buildContinuousTrendData(
  timestamps: number[],
  pointMap: Map<number, NodeTrendPoint>,
  getter: (point: NodeTrendPoint) => number | null | undefined,
): number[] {
  let lastValue: number | undefined;
  return timestamps.map((ts) => {
    const point = pointMap.get(ts);
    if (point) {
      const value = getter(point);
      if (value != null && !Number.isNaN(Number(value))) {
        lastValue = Number(value);
      }
    }
    return lastValue ?? 0;
  });
}

export function buildClusterNodeTrendSeries(
  nodeSeries: NodeTrendSeries[],
  timestamps: number[],
): Array<{
  name: string;
  yAxisIndex: number;
  color: string;
  data: number[];
}> {
  const result: Array<{
    name: string;
    yAxisIndex: number;
    color: string;
    data: number[];
  }> = [];

  nodeSeries.forEach((series, nodeIndex) => {
    if (!series.points.length) return;
    const pointMap = new Map(series.points.map((point) => [point.timestamp, point]));
    const palette = getNodeTrendPalette(nodeIndex);
    CLUSTER_NODE_TREND_METRICS.forEach((metric) => {
      const colorKey = metric.key === 'gpuMem' ? 'vram' : metric.key;
      result.push({
        name: `${series.nodeName} · ${metric.name}`,
        yAxisIndex: metric.axis === 'cpu' ? 0 : 1,
        color: palette[colorKey as keyof NodeTrendPalette],
        data: buildContinuousTrendData(timestamps, pointMap, (point) =>
          getClusterNodeTrendMetricValue(point, metric.key),
        ),
      });
    });
  });

  return result;
}

export function isCpuTrendSeriesName(name?: string): boolean {
  return !!name?.endsWith(` · ${NODE_METRIC.cpu}`);
}

export function formatClusterTrendTooltipValue(value: number, seriesName?: string): string {
  if (isCpuTrendSeriesName(seriesName)) {
    return formatCpuQuantity(value);
  }
  return formatStorageBytes(value);
}

export function collectTrendTimestamps(
  clusterPoints: ClusterTrendPoint[],
  nodeSeries: NodeTrendSeries[],
): number[] {
  const timestampSet = new Set<number>();
  clusterPoints.forEach((point) => timestampSet.add(point.timestamp));
  nodeSeries.forEach((series) => {
    series.points.forEach((point) => timestampSet.add(point.timestamp));
  });
  return Array.from(timestampSet).sort((a, b) => a - b);
}

export function formatTrendTimestamps(timestamps: number[]): string[] {
  return timestamps.map((ts) => {
    const date = new Date(ts);
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`;
  });
}

function formatNiceDecimal(value: number, maxDecimals = 1): string {
  return value.toFixed(maxDecimals).replace(/\.0$/, '');
}

export function formatPercentValue(val?: number | null): string {
  return formatNiceDecimal(num(val));
}

export function formatPercent(val?: number | null): string {
  return `${formatPercentValue(val)}%`;
}

/** 存储容量数值（不含单位，默认换算为 GB） */
export function formatStorageValue(bytes?: number | null): string {
  const val = num(bytes);
  if (val <= 0) return '-';
  const gb = val / 1024 ** 3;
  if (gb >= 1024) return formatNiceDecimal(gb / 1024);
  if (gb >= 0.01) return formatNiceDecimal(gb);
  const mb = val / 1024 ** 2;
  if (mb >= 1) return formatNiceDecimal(mb / 1024);
  return formatNiceDecimal(val / 1024 ** 3);
}

export function formatStorageRangeValue(used?: number | null, total?: number | null): string {
  const totalVal = num(total);
  if (totalVal <= 0) return '-';
  return `${formatStorageValue(used)} / ${formatStorageValue(total)}`;
}

export function formatMemMbValue(mb: number): string {
  if (mb >= 1024) return formatNiceDecimal(mb / 1024);
  return formatNiceDecimal(mb / 1024);
}

export function formatMemMb(mb: number): string {
  if (mb >= 1024) return `${formatMemMbValue(mb)}G`;
  return `${Math.round(mb)}M`;
}

export function formatStorageBytes(bytes?: number | null): string {
  const val = num(bytes);
  if (val <= 0) return '-';
  const gb = val / 1024 ** 3;
  if (gb >= 1024) return `${formatNiceDecimal(gb / 1024)}T`;
  if (gb >= 1) return `${formatNiceDecimal(gb)}G`;
  const mb = val / 1024 ** 2;
  if (mb >= 1) return `${Math.round(mb)}M`;
  return `${Math.round(val / 1024)}K`;
}

export function formatStorageRange(used?: number | null, total?: number | null): string {
  const totalVal = num(total);
  if (totalVal <= 0) return '-';
  return `${formatStorageBytes(used)} / ${formatStorageBytes(total)}`;
}

export type InsightLevel = 'success' | 'warning' | 'error' | 'info';

export interface ClusterInsight {
  level: InsightLevel;
  title: string;
  description: string;
  action?: string;
}

export interface AttentionNode {
  id: number;
  name: string;
  host: string;
  status?: string;
  reasons: string[];
}

export function buildClusterInsight(
  snapshot: ClusterSnapshot,
  nodes: ComputeNodeVO[],
): ClusterInsight {
  if (snapshot.total === 0) {
    return {
      level: 'info',
      title: NODE_INSIGHT.noNodesTitle,
      description: NODE_INSIGHT.noNodesDesc,
      action: NODE_INSIGHT.noNodesAction,
    };
  }
  if (snapshot.online === 0) {
    return {
      level: 'error',
      title: NODE_INSIGHT.clusterDownTitle,
      description: NODE_INSIGHT.clusterDownDesc,
      action: NODE_INSIGHT.clusterDownAction,
    };
  }
  const offlineCompute = nodes.filter(
    (n) => isComputeNode(n) && (n.status === 'offline' || n.status === 'pending'),
  ).length;
  const overloaded = nodes.filter(
    (n) =>
      n.status === 'online' &&
      isComputeNode(n) &&
      (num(n.cpuPercent) >= 85 || num(n.memPercent) >= 85 || num(n.diskPercent) >= 90),
  ).length;
  const taskPressure =
    snapshot.maxTasks > 0
      ? Math.round((snapshot.activeTasks / snapshot.maxTasks) * 100)
      : 0;

  if (taskPressure >= 90) {
    return {
      level: 'warning',
      title: '推理任务接近容量上限',
      description: `当前 ${snapshot.activeTasks} 个运行任务，已占上报容量约 ${taskPressure}%，继续部署可能排队或失败。`,
      action: '建议扩容计算节点或清理闲置部署',
    };
  }
  if (overloaded > 0) {
    return {
      level: 'warning',
      title: NODE_INSIGHT.overloadedTitle(overloaded),
      description: NODE_INSIGHT.overloadedDesc,
      action: NODE_INSIGHT.overloadedAction,
    };
  }
  if (offlineCompute > 0) {
    return {
      level: 'warning',
      title: NODE_INSIGHT.notReadyTitle(offlineCompute),
      description: NODE_INSIGHT.notReadyDesc,
      action: NODE_INSIGHT.notReadyAction,
    };
  }
  return {
    level: 'success',
    title: NODE_INSIGHT.healthyTitle,
    description: `${snapshot.computeOnline} 台计算节点在线，${snapshot.gpuCount} 张 GPU 可用，当前 ${snapshot.activeTasks} 个推理任务运行中。`,
  };
}

export function buildAttentionNodes(nodes: ComputeNodeVO[]): AttentionNode[] {
  const list: AttentionNode[] = [];
  nodes.filter(isComputeNode).forEach((node) => {
    const reasons: string[] = [];
    if (node.status === 'offline') reasons.push(NODE_INSIGHT.nodeOffline);
    if (node.status === 'pending') reasons.push(NODE_INSIGHT.pendingReason);
    if (node.status === 'maintenance') reasons.push('维护模式中');
    if (node.status === 'online') {
      if (num(node.cpuPercent) >= 85) {
        reasons.push(`${NODE_METRIC.cpuUsage} ${num(node.cpuPercent)}%`);
      }
      if (num(node.memPercent) >= 85) {
        reasons.push(`${NODE_METRIC.memUsage} ${num(node.memPercent)}%`);
      }
      if (num(node.diskPercent) >= 90) {
        reasons.push(`${NODE_METRIC.diskUsage} ${num(node.diskPercent)}%`);
      }
      const gpus = parseGpuInfo(node.gpuInfo);
      gpus.forEach((g) => {
        if (num(g.util) >= 85) {
          reasons.push(`GPU${g.id ?? 0} ${NODE_METRIC.gpuUtil} ${num(g.util)}%`);
        }
        const total = num(g.mem_total_mb);
        const used = num(g.mem_used_mb);
        if (total > 0 && (used / total) * 100 >= 85) {
          reasons.push(
            `GPU${g.id ?? 0} ${NODE_METRIC.vramUsage} ${Math.round((used / total) * 100)}%`,
          );
        }
      });
    }
    if (reasons.length) {
      list.push({
        id: node.id!,
        name: node.name,
        host: node.host,
        status: node.status,
        reasons,
      });
    }
  });
  return list.sort((a, b) => {
    const weight = (s?: string) =>
      s === 'offline' ? 0 : s === 'pending' ? 1 : s === 'maintenance' ? 2 : 3;
    return weight(a.status) - weight(b.status);
  });
}

export function getProgressColor(val?: number): string {
  if (val == null) return '#1677ff';
  if (val >= 85) return '#ff4d4f';
  if (val >= 65) return '#faad14';
  return '#52c41a';
}
