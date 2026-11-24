<template>
  <div class="edge-page">
    <section class="hero">
      <div>
        <div class="eyebrow">EDGE AI CONTROL PLANE</div>
        <h1>边缘计算</h1>
        <p>统一纳管 RK3588、BM1688 等异构 AI 盒子。盒子通过 MQTT 持续上报，页面每 30 秒刷新在线状态、硬件负载、推理管线与远程入口。</p>
      </div>
      <div class="hero-actions">
        <Tag color="blue">MQTT 实时上报</Tag>
        <Button :loading="loading" @click="loadNodes(true)">
          <template #icon><ReloadOutlined /></template>
          立即刷新
        </Button>
      </div>
    </section>

    <div class="summary-grid">
      <div class="summary-card"><span>已纳管盒子</span><strong>{{ summary.total }}</strong><small>统一硬件资产</small></div>
      <div class="summary-card online"><span>在线节点</span><strong>{{ summary.online }}</strong><small>按中心心跳窗口判定</small></div>
      <div class="summary-card"><span>运行管线</span><strong>{{ summary.pipelines }}</strong><small>多路视频 / 多模型</small></div>
      <div class="summary-card"><span>NPU 平均负载</span><strong>{{ summary.acceleratorLoad }}%</strong><small>当前节点快照</small></div>
      <div class="summary-card"><span>远程入口</span><strong>{{ summary.remote }}</strong><small>FRP 服务或 SSH</small></div>
    </div>

    <Card class="resource-card" :bordered="false">
      <div class="resource-header">
        <div>
          <h2>边缘节点资源</h2>
          <span>节点按统一协议接入，芯片能力由 provider / SoC / accelerator / runtimeTarget 描述</span>
        </div>
        <Space wrap>
          <Input v-model:value="filters.keyword" allow-clear placeholder="节点名 / IP / 指纹" style="width: 210px" @pressEnter="search" />
          <Select v-model:value="filters.status" style="width: 120px" @change="search">
            <SelectOption value="all">全部状态</SelectOption>
            <SelectOption value="online">在线</SelectOption>
            <SelectOption value="offline">离线</SelectOption>
          </Select>
          <Input v-model:value="filters.socModel" allow-clear placeholder="芯片，如 RK3588" style="width: 160px" @pressEnter="search" />
          <Button type="primary" @click="search">查询</Button>
        </Space>
      </div>

      <Table
        row-key="id"
        :columns="columns"
        :data-source="nodes"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1240 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'node'">
            <div class="node-cell">
              <div class="node-icon" :class="record.status"><ApiOutlined /></div>
              <div><strong>{{ record.name }}</strong><span>{{ record.host || '等待 Agent 上报 IP' }}</span></div>
            </div>
          </template>
          <template v-else-if="column.key === 'status'">
            <Badge :status="record.status === 'online' ? 'success' : 'default'" :text="record.status === 'online' ? '在线' : '离线'" />
          </template>
          <template v-else-if="column.key === 'hardware'">
            <div class="hardware-cell">
              <strong>{{ record.socModel || '未知芯片' }}</strong>
              <span>{{ record.hardwareProvider || '-' }} · {{ (record.acceleratorType || 'accelerator').toUpperCase() }} × {{ record.acceleratorCount || 0 }}</span>
              <code>{{ record.runtimeTarget || '等待运行时上报' }}</code>
            </div>
          </template>
          <template v-else-if="column.key === 'pipelines'">
            <strong>{{ record.activeTaskCount || 0 }} / {{ record.maxTaskCount || record.pipelines?.length || 0 }}</strong>
            <div class="muted">活跃 / 容量</div>
          </template>
          <template v-else-if="column.key === 'resources'">
            <div class="resource-lines">
              <span>CPU <Progress :percent="percent(record.cpuPercent)" :show-info="false" size="small" /></span>
              <span>内存 <Progress :percent="percent(record.memPercent)" :show-info="false" size="small" stroke-color="#5b8ff9" /></span>
              <span class="temperature">{{ displayNumber(record.temperatureC) }}℃</span>
            </div>
          </template>
          <template v-else-if="column.key === 'remote'">
            <Tag v-if="record.remoteAccess?.enabled" :color="record.remoteAccess?.status === 'online' ? 'green' : 'orange'">
              {{ (record.remoteAccess?.provider || 'FRP').toUpperCase() }} {{ remoteStatus(record) }}
            </Tag>
            <span v-else class="muted">未启用</span>
          </template>
          <template v-else-if="column.key === 'heartbeat'">
            <div>{{ formatTime(record.lastHeartbeatAt) }}</div>
            <div class="muted">{{ heartbeatAgo(record.lastHeartbeatAt) }}</div>
          </template>
          <template v-else-if="column.key === 'actions'">
            <Space size="small">
              <Button type="link" size="small" @click="openDetail(record)">详情</Button>
              <Button type="link" size="small" @click="openMetrics(record)">监控</Button>
              <Button v-if="record.remoteAccess?.serviceAccessUrl" type="link" size="small" @click="openService(record)">访问</Button>
              <Button v-if="record.remoteAccess?.sshEnabled" type="link" size="small" @click="openSsh(record)">登录</Button>
              <Dropdown>
                <Button type="link" size="small">更多</Button>
                <template #overlay>
                  <Menu>
                    <MenuItem @click="sendCommand(record, 'status')">刷新盒子状态</MenuItem>
                    <MenuItem @click="confirmCommand(record, 'runtime.restart')">重启推理运行时</MenuItem>
                    <MenuItem v-if="record.remoteAccess?.enabled" @click="confirmCommand(record, 'frp.restart')">重启 FRP</MenuItem>
                    <MenuDivider />
                    <MenuItem danger @click="disableNode(record)">停用纳管</MenuItem>
                  </Menu>
                </template>
              </Dropdown>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Drawer v-model:open="detailOpen" width="760" title="边缘节点详情" destroy-on-close>
      <template v-if="current">
        <div class="detail-title">
          <div class="node-icon large" :class="current.status"><ApiOutlined /></div>
          <div><h3>{{ current.name }}</h3><Badge :status="current.status === 'online' ? 'success' : 'default'" :text="current.status === 'online' ? '在线' : '离线'" /></div>
        </div>
        <Descriptions bordered :column="2" size="small">
          <DescriptionsItem label="节点 ID">{{ current.id }}</DescriptionsItem>
          <DescriptionsItem label="IP / 主机">{{ current.host || '-' }}</DescriptionsItem>
          <DescriptionsItem label="芯片">{{ current.hardwareProvider || '-' }} {{ current.socModel || '-' }}</DescriptionsItem>
          <DescriptionsItem label="加速器">{{ current.acceleratorType || '-' }} × {{ current.acceleratorCount || 0 }}</DescriptionsItem>
          <DescriptionsItem label="运行目标">{{ current.runtimeTarget || '-' }}</DescriptionsItem>
          <DescriptionsItem label="运行时版本">{{ current.runtimeVersion || '-' }}</DescriptionsItem>
          <DescriptionsItem label="Agent">{{ current.agentVersion || '-' }}</DescriptionsItem>
          <DescriptionsItem label="遥测链路">EMQX → iot-sink → iot-video20</DescriptionsItem>
          <DescriptionsItem label="CPU / 内存">{{ displayNumber(current.cpuPercent) }}% / {{ displayNumber(current.memPercent) }}%</DescriptionsItem>
          <DescriptionsItem label="温度">{{ displayNumber(current.temperatureC) }}℃</DescriptionsItem>
          <DescriptionsItem label="最近心跳" :span="2">{{ formatTime(current.lastHeartbeatAt) }}</DescriptionsItem>
        </Descriptions>
        <h3 class="section-title">推理管线</h3>
        <Table size="small" :pagination="false" row-key="id" :data-source="current.pipelines || []" :columns="pipelineColumns" />
        <h3 class="section-title">远程访问</h3>
        <Descriptions bordered :column="1" size="small">
          <DescriptionsItem label="FRP 状态">{{ current.remoteAccess?.enabled ? remoteStatus(current) : '未启用' }}</DescriptionsItem>
          <DescriptionsItem label="服务入口">{{ current.remoteAccess?.serviceAccessUrl || '-' }}</DescriptionsItem>
          <DescriptionsItem label="SSH 入口">{{ sshCommand(current) || '-' }}</DescriptionsItem>
        </Descriptions>
      </template>
    </Drawer>

    <Modal v-model:open="metricsOpen" :title="`${current?.name || ''} · 运行监控`" width="900" :footer="null">
      <div class="metric-cards" v-if="current">
        <div><span>CPU</span><strong>{{ displayNumber(current.cpuPercent) }}%</strong></div>
        <div><span>内存</span><strong>{{ displayNumber(current.memPercent) }}%</strong></div>
        <div><span>磁盘</span><strong>{{ displayNumber(current.diskPercent) }}%</strong></div>
        <div><span>温度</span><strong>{{ displayNumber(current.temperatureC) }}℃</strong></div>
      </div>
      <Table size="small" :loading="metricsLoading" :pagination="{ pageSize: 8 }" row-key="id" :columns="metricColumns" :data-source="metrics" />
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import {
  Badge, Button, Card, Descriptions, DescriptionsItem, Drawer, Dropdown, Input, Menu,
  MenuDivider, MenuItem, Modal, Progress, Select, SelectOption, Space, Table, Tag, message,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { ApiOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import type { EdgeNodeMetric, EdgeNodeVO } from '@/api/device/edge';
import { deleteEdgeNode, getEdgeNode, getEdgeNodeMetrics, getEdgeNodePage, sendEdgeNodeCommand } from '@/api/device/edge';

defineOptions({ name: 'EdgeComputingIndex' });

const loading = ref(false);
const nodes = ref<EdgeNodeVO[]>([]);
const total = ref(0);
const detailOpen = ref(false);
const metricsOpen = ref(false);
const metricsLoading = ref(false);
const metrics = ref<EdgeNodeMetric[]>([]);
const current = ref<EdgeNodeVO>();
const filters = reactive({ keyword: '', status: 'all', socModel: '' });
const pagination = reactive({ current: 1, pageSize: 20, total: 0, showSizeChanger: true, showTotal: (value: number) => `共 ${value} 个节点` });
let poller: number | undefined;

type EdgeNodeRecord = EdgeNodeVO | Record<string, any>;

const columns: TableColumnsType<EdgeNodeVO> = [
  { title: '节点与 IP', key: 'node', width: 210, fixed: 'left' }, { title: '状态', key: 'status', width: 90 },
  { title: '硬件与运行目标', key: 'hardware', width: 230 }, { title: '管线', key: 'pipelines', width: 90 },
  { title: '资源占用', key: 'resources', width: 210 }, { title: '远程入口', key: 'remote', width: 130 },
  { title: '最后心跳', key: 'heartbeat', width: 170 }, { title: '操作', key: 'actions', width: 270, fixed: 'right' },
];
const pipelineColumns = [
  { title: '管线', dataIndex: 'name', key: 'name' }, { title: '设备', dataIndex: 'deviceId', key: 'deviceId' },
  { title: '状态', dataIndex: 'status', key: 'status' }, { title: 'FPS', dataIndex: 'fps', key: 'fps' },
];
const metricColumns = [
  { title: '采集时间', dataIndex: 'collectedAt', key: 'collectedAt', customRender: ({ text }: any) => formatTime(text) },
  { title: 'CPU', dataIndex: 'cpuPercent', customRender: ({ text }: any) => `${displayNumber(text)}%` },
  { title: '内存', dataIndex: 'memPercent', customRender: ({ text }: any) => `${displayNumber(text)}%` },
  { title: '磁盘', dataIndex: 'diskPercent', customRender: ({ text }: any) => `${displayNumber(text)}%` },
  { title: '温度', dataIndex: 'temperatureC', customRender: ({ text }: any) => `${displayNumber(text)}℃` },
  { title: '任务', dataIndex: 'activeTasks' },
];

const summary = computed(() => {
  const online = nodes.value.filter((item) => item.status === 'online');
  const loads = online.flatMap((item) => item.acceleratorInfo || []).map((item) => Number(item.loadPercent ?? item.load ?? 0)).filter(Number.isFinite);
  return {
    total: total.value, online: online.length,
    pipelines: nodes.value.reduce((sum, item) => sum + Number(item.activeTaskCount || 0), 0),
    acceleratorLoad: loads.length ? Math.round(loads.reduce((a, b) => a + b, 0) / loads.length) : 0,
    remote: nodes.value.filter((item) => item.remoteAccess?.enabled).length,
  };
});

async function loadNodes(notify = false) {
  loading.value = true;
  try {
    const result: any = await getEdgeNodePage({ pageNo: pagination.current, pageSize: pagination.pageSize,
      keyword: filters.keyword || undefined, status: filters.status, socModel: filters.socModel || undefined });
    nodes.value = result?.data || result?.list || [];
    total.value = Number(result?.total || nodes.value.length);
    pagination.total = total.value;
    if (notify) message.success('边缘节点状态已刷新');
  } finally { loading.value = false; }
}
function search() { pagination.current = 1; loadNodes(); }
function handleTableChange(page: any) { pagination.current = page.current; pagination.pageSize = page.pageSize; loadNodes(); }
function percent(value?: number) { return Math.max(0, Math.min(100, Number(value || 0))); }
function displayNumber(value?: number) { return Number.isFinite(Number(value)) ? Number(value).toFixed(1) : '-'; }
function formatTime(value?: string) { return value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '-'; }
function heartbeatAgo(value?: string) {
  if (!value) return '尚未上报';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds} 秒前`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  return `${Math.floor(seconds / 3600)} 小时前`;
}
function remoteStatus(node: EdgeNodeRecord) { return node.remoteAccess?.status === 'online' ? '在线' : '未连接'; }
function sshCommand(node: EdgeNodeRecord) {
  const remote = node.remoteAccess;
  if (!remote?.sshEnabled || !remote.sshAccessHost) return '';
  return `ssh -p ${remote.sshAccessPort || 22} ${remote.sshUsername || 'root'}@${remote.sshAccessHost}`;
}
async function openDetail(node: EdgeNodeRecord) { current.value = await getEdgeNode(node.id); detailOpen.value = true; }
async function openMetrics(node: EdgeNodeRecord) {
  current.value = node as EdgeNodeVO; metricsOpen.value = true; metricsLoading.value = true;
  try { metrics.value = await getEdgeNodeMetrics(node.id, { minutes: 60, limit: 360 }); }
  finally { metricsLoading.value = false; }
}
function openService(node: EdgeNodeRecord) {
  const raw = node.remoteAccess?.serviceAccessUrl;
  if (!raw) return;
  try {
    const target = new URL(raw);
    if (!['http:', 'https:'].includes(target.protocol)) throw new Error('unsupported protocol');
    window.open(target.toString(), '_blank', 'noopener,noreferrer');
  } catch {
    message.error('盒子上报的服务入口不是有效的 HTTP(S) 地址');
  }
}
async function openSsh(node: EdgeNodeRecord) {
  const command = sshCommand(node); if (!command) return;
  await navigator.clipboard?.writeText(command); message.success(`SSH 命令已复制：${command}`);
  const remote = node.remoteAccess!;
  window.location.href = `ssh://${remote.sshUsername || 'root'}@${remote.sshAccessHost}:${remote.sshAccessPort || 22}`;
}
async function sendCommand(node: EdgeNodeRecord, command: any) {
  await sendEdgeNodeCommand(node.id, command); message.success('命令已通过 MQTT 发送到盒子');
}
function confirmCommand(node: EdgeNodeRecord, command: any) {
  Modal.confirm({ title: '确认执行远程命令？', content: `${node.name}：${command}`, onOk: () => sendCommand(node, command) });
}
function disableNode(node: EdgeNodeRecord) {
  Modal.confirm({ title: '停用边缘节点', content: `停用后 ${node.name} 将无法继续通过 MQTT 鉴权。`, okType: 'danger', async onOk() {
    await deleteEdgeNode(node.id); message.success('节点已停用'); await loadNodes();
  } });
}
onMounted(() => { loadNodes(); poller = window.setInterval(() => loadNodes(), 30_000); });
onBeforeUnmount(() => { if (poller) window.clearInterval(poller); });
</script>

<style scoped lang="less">
.edge-page { min-height: 100%; padding: 22px; background: #f3f6fa; color: #172033; }
.hero { display: flex; align-items: flex-end; justify-content: space-between; padding: 25px 28px; color: white; border-radius: 14px; background: linear-gradient(115deg, #13253e 0%, #164a70 58%, #167e84 100%); box-shadow: 0 12px 30px rgba(20, 61, 91, .18); }
.hero h1 { margin: 3px 0 5px; color: white; font-size: 28px; }.hero p { margin: 0; color: rgba(255,255,255,.76); }.eyebrow { font-size: 11px; letter-spacing: 2px; color: #5fe3d1; }.hero-actions { display: flex; gap: 10px; align-items: center; }
.summary-grid { display: grid; grid-template-columns: repeat(5, minmax(150px, 1fr)); gap: 14px; margin: 16px 0; }.summary-card { padding: 17px 19px; border: 1px solid #e7edf4; border-radius: 11px; background: white; }.summary-card span,.summary-card small { display: block; color: #778399; }.summary-card strong { display: block; margin: 3px 0; font-size: 27px; }.summary-card.online strong { color: #10a37f; }
.resource-card { border-radius: 12px; box-shadow: 0 5px 18px rgba(34, 57, 86, .06); }.resource-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 18px; }.resource-header h2 { margin: 0 0 4px; font-size: 18px; }.resource-header span { color: #7a8798; }
.node-cell,.detail-title { display: flex; align-items: center; gap: 11px; }.node-cell strong,.node-cell span,.hardware-cell strong,.hardware-cell span,.hardware-cell code { display: block; }.node-cell span,.hardware-cell span,.muted { color: #8994a5; font-size: 12px; }.node-icon { display: grid; flex: 0 0 34px; width: 34px; height: 34px; place-items: center; border-radius: 9px; color: #718096; background: #edf1f5; }.node-icon.online { color: #087d64; background: #daf7ef; }.node-icon.large { width: 45px; height: 45px; font-size: 20px; }.hardware-cell code { width: max-content; margin-top: 3px; padding: 1px 5px; border-radius: 4px; color: #375d77; background: #edf5f8; }
.resource-lines { min-width: 185px; }.resource-lines > span { display: grid; grid-template-columns: 33px 1fr; align-items: center; gap: 7px; font-size: 11px; color: #667085; }.resource-lines .temperature { display: block; margin-top: 2px; color: #c76a25; }.detail-title { margin-bottom: 18px; }.detail-title h3 { margin: 0 0 3px; }.section-title { margin: 22px 0 10px; }.metric-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }.metric-cards > div { padding: 14px; border-radius: 9px; background: #f5f8fb; }.metric-cards span,.metric-cards strong { display: block; }.metric-cards span { color: #8090a4; }.metric-cards strong { margin-top: 3px; font-size: 20px; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(3, 1fr); }.resource-header { align-items: flex-start; flex-direction: column; } }
</style>
