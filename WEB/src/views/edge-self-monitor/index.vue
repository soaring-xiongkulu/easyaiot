<template>
  <div class="monitor-page">
    <section class="hero">
      <div>
        <div class="eyebrow">EDGE SELF OBSERVABILITY</div>
        <h1>本机监测</h1>
        <p>{{ hostSummary }}</p>
      </div>
      <div class="hero-status">
        <Badge :status="metrics?.runtime.ready ? 'success' : 'error'" :text="runtimeStatus" />
        <Button :loading="loading" @click="loadMetrics">
          <template #icon><ReloadOutlined /></template>
          立即刷新
        </Button>
      </div>
    </section>

    <Alert
      v-if="errorMessage"
      type="error"
      show-icon
      closable
      :message="errorMessage"
      class="status-alert"
      @close="errorMessage = ''"
    />

    <section class="metric-grid">
      <article v-for="card in cards" :key="card.key" class="metric-card">
        <div class="metric-head">
          <span>{{ card.title }}</span>
          <component :is="card.icon" class="metric-icon" />
        </div>
        <strong>{{ card.value }}</strong>
        <Progress
          v-if="card.percent !== undefined"
          :percent="card.percent"
          :show-info="false"
          size="small"
          :stroke-color="progressColor(card.percent)"
        />
        <small>{{ card.detail }}</small>
      </article>
    </section>

    <section class="detail-grid">
      <Card title="运行时与算法任务" :bordered="false">
        <Descriptions :column="1" size="small">
          <DescriptionsItem label="运行时目标">{{ runtimeTarget }}</DescriptionsItem>
          <DescriptionsItem label="二进制">{{ metrics?.runtime.binPath || '未就绪' }}</DescriptionsItem>
          <DescriptionsItem label="版本">{{ metrics?.runtime.version || '-' }}</DescriptionsItem>
          <DescriptionsItem label="任务 / 流">
            {{ metrics?.runtime.runningTasks || 0 }} 个运行任务，{{ metrics?.runtime.runningStreams || 0 }} 路运行流
          </DescriptionsItem>
        </Descriptions>
      </Card>
      <Card title="主机与 VIDEO 进程" :bordered="false">
        <Descriptions :column="1" size="small">
          <DescriptionsItem label="启动时间">{{ formatTime(metrics?.host.bootAt) }}</DescriptionsItem>
          <DescriptionsItem label="系统负载">{{ loadSummary }}</DescriptionsItem>
          <DescriptionsItem label="VIDEO 进程">PID {{ metrics?.process.pid || '-' }} · {{ metrics?.process.threads || 0 }} 线程</DescriptionsItem>
          <DescriptionsItem label="进程内存">{{ formatBytes(metrics?.process.rssBytes) }}</DescriptionsItem>
        </Descriptions>
      </Card>
    </section>

    <div class="refresh-note">每 5 秒自动刷新 · 最近采集 {{ formatTime(metrics?.collectedAt) }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { Alert, Badge, Button, Card, Descriptions, DescriptionsItem, Progress } from 'ant-design-vue';
import {
  CloudDownloadOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  FireOutlined,
  HddOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';
import { getLocalMonitorMetrics, type LocalMonitorMetrics } from '@/api/device/localMonitor';

defineOptions({ name: 'EdgeSelfMonitorIndex' });

const metrics = ref<LocalMonitorMetrics>();
const loading = ref(false);
const errorMessage = ref('');
let timer: number | undefined;

function formatBytes(value?: number) {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let current = bytes / 1024;
  let index = 0;
  while (current >= 1024 && index < units.length - 1) {
    current /= 1024;
    index += 1;
  }
  return `${current.toFixed(current >= 10 ? 1 : 2)} ${units[index]}`;
}

function formatTime(value?: string) {
  return value ? new Date(value).toLocaleString() : '-';
}

function progressColor(value: number) {
  if (value >= 90) return '#ff4d4f';
  if (value >= 75) return '#faad14';
  return '#1677ff';
}

const runtimeTarget = computed(() => metrics.value?.runtime.target === 'rk3588'
  ? 'RUNTIME-RK3588 · MPP + RGA + 三核 RKNN NPU'
  : metrics.value?.runtime.target === 'bm1688'
    ? 'RUNTIME-BM1688 · VPU + VPSS/BMCV + 双核 TPU'
    : (metrics.value?.runtime.target || '自动识别'));
const runtimeStatus = computed(() => metrics.value?.runtime.ready ? `${runtimeTarget.value} 已就绪` : '算法运行时未就绪');
const hostSummary = computed(() => metrics.value
  ? `${metrics.value.host.hostname} · ${metrics.value.host.architecture} · 已连续运行 ${Math.floor(metrics.value.host.uptimeSec / 3600)} 小时`
  : '正在读取盒子自身 CPU、内存、温度、网络与算法运行时状态');
const loadSummary = computed(() => metrics.value
  ? `${metrics.value.cpu.load1} / ${metrics.value.cpu.load5} / ${metrics.value.cpu.load15}`
  : '-');

const cards = computed(() => {
  const item = metrics.value;
  return [
    { key: 'cpu', title: 'CPU', value: `${item?.cpu.percent || 0}%`, percent: item?.cpu.percent || 0, detail: `${item?.cpu.physicalCores || 0} 物理核 / ${item?.cpu.logicalCores || 0} 逻辑核`, icon: ThunderboltOutlined },
    { key: 'memory', title: '内存', value: `${item?.memory.percent || 0}%`, percent: item?.memory.percent || 0, detail: `${formatBytes(item?.memory.usedBytes)} / ${formatBytes(item?.memory.totalBytes)}`, icon: DatabaseOutlined },
    { key: 'disk', title: '本地存储', value: `${item?.disk.percent || 0}%`, percent: item?.disk.percent || 0, detail: `${formatBytes(item?.disk.freeBytes)} 可用 · ${item?.disk.path || '-'}`, icon: HddOutlined },
    { key: 'temperature', title: '芯片温度', value: item?.temperatureC == null ? '-' : `${item.temperatureC}℃`, detail: '取 SoC / CPU 可见传感器最高值', icon: FireOutlined },
    { key: 'rx', title: '网络接收', value: `${formatBytes(item?.network.rxBytesPerSec)}/s`, detail: `累计 ${formatBytes(item?.network.rxBytes)}`, icon: CloudDownloadOutlined },
    { key: 'tx', title: '网络发送', value: `${formatBytes(item?.network.txBytesPerSec)}/s`, detail: `累计 ${formatBytes(item?.network.txBytes)}`, icon: CloudUploadOutlined },
  ];
});

async function loadMetrics() {
  loading.value = true;
  try {
    const response: any = await getLocalMonitorMetrics();
    metrics.value = response?.data && response?.code !== undefined ? response.data : response;
    errorMessage.value = '';
  } catch (error: any) {
    errorMessage.value = error?.message || '本机指标读取失败';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadMetrics();
  timer = window.setInterval(loadMetrics, 5000);
});
onBeforeUnmount(() => timer && window.clearInterval(timer));
</script>

<style scoped lang="less">
.monitor-page { min-height: 100%; padding: 20px; background: #f4f7fb; }
.hero { display: flex; justify-content: space-between; gap: 20px; padding: 26px 30px; color: #fff; border-radius: 14px; background: linear-gradient(120deg, #102a56, #1765ad 62%, #19a0a8); box-shadow: 0 10px 30px rgb(24 86 153 / 18%); }
.hero h1 { margin: 4px 0 8px; color: #fff; font-size: 28px; }
.hero p { margin: 0; color: rgb(255 255 255 / 78%); }
.eyebrow { color: #75e6ff; font-size: 12px; letter-spacing: 1.8px; }
.hero-status { display: flex; align-items: center; gap: 18px; padding: 12px 16px; border-radius: 10px; background: rgb(255 255 255 / 92%); }
.status-alert { margin-top: 16px; }
.metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }
.metric-card { padding: 20px; border: 1px solid #e8edf5; border-radius: 12px; background: #fff; box-shadow: 0 4px 18px rgb(28 56 92 / 6%); }
.metric-head { display: flex; justify-content: space-between; color: #627087; }
.metric-icon { color: #1677ff; font-size: 21px; }
.metric-card strong { display: block; margin: 10px 0 8px; color: #15233c; font-size: 27px; }
.metric-card small { display: block; margin-top: 8px; color: #8a96a8; overflow-wrap: anywhere; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }
.refresh-note { margin: 14px 2px 0; color: #8a96a8; text-align: right; }
@media (max-width: 1000px) { .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 680px) { .hero { flex-direction: column; } .hero-status { justify-content: space-between; } .metric-grid, .detail-grid { grid-template-columns: 1fr; } }
</style>
