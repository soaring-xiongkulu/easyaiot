<template>
  <div class="panel">
    <div class="metric-strip">
      <div v-for="item in overviewCards" :key="item.key" class="metric-item" :class="{ 'metric-item--click': item.filter != null, 'metric-item--active': item.filter != null && state.statusFilter === item.filter, 'metric-item--warn': item.warn }" @click="item.filter != null && toggleFilter(item.filter)">
        <div class="metric-item__icon" :style="{ background: item.bg, color: item.color }"><Icon :icon="item.icon" :size="16" /></div>
        <div class="metric-item__body"><span class="metric-item__label">{{ item.label }}</span><span class="metric-item__value"><template v-if="item.isText">{{ item.textDisplay }}</template><template v-else><CountTo :start-val="0" :end-val="item.value" :duration="700" :decimals="item.decimals ?? 0" /><span v-if="item.suffix" class="metric-item__suffix">{{ item.suffix }}</span></template></span><span v-if="item.sub" class="metric-item__sub">{{ item.sub }}</span></div>
      </div>
    </div>
    <div class="panel-bar">
      <span class="panel-bar__label">运行状态</span>
      <RadioButtonGroup v-model:value="state.statusFilter" :options="filterOptions" size="small" button-style="solid" />
      <div class="panel-bar__actions">
        <Tooltip title="iot_transform_heartbeat"><Tag class="ch-tag">心跳</Tag></Tooltip>
        <Tooltip :title="clusterInfo.telemetryTopic || 'iot_transform_telemetry'"><Tag class="ch-tag">遥测</Tag></Tooltip>
        <Tooltip :title="clusterInfo.commandTopic || 'iot_transform_command'"><Tag class="ch-tag ch-tag--cmd">指令</Tag></Tooltip>
        <span class="sync" :class="state.loading ? 'sync--busy' : 'sync--ok'">{{ state.loading ? '同步中' : `更新 ${lastUpdated || '--:--:--'}` }}</span>
        <Button size="small" danger preIcon="ant-design:clear-outlined" :loading="state.purgeLoading" @click="confirmPurgeOffline">清理离线</Button>
        <Button size="small" type="primary" preIcon="ant-design:reload-outlined" :loading="state.loading" @click="handleRefresh">刷新</Button>
      </div>
    </div>
    <div v-if="lastCmdSummary" class="ack-bar"><span class="ack-bar__label">最近指令</span><span class="ack-bar__text">{{ lastCmdSummary }}</span></div>
    <div class="panel-body">
      <Spin :spinning="state.loading && !rawList.length">
        <div v-if="!filteredList.length" class="empty-box"><div class="empty-box__title">暂无转发运行机器</div><div class="empty-box__desc">启动 TRANSFORM runtime 后，本页按机器 IP 展示运行态势。</div></div>
        <List v-else class="instance-list" :grid="{ gutter: 10, xs: 1, sm: 2, md: 3, lg: 3, xl: 3, xxl: 3 }" :data-source="pagedList" :pagination="paginationProp">
          <template #renderItem="{ item }">
            <ListItem class="instance-list-item">
              <div class="inst-card" :class="{ 'inst-card--offline': !item.online, 'inst-card--active': state.selectedId === item.key, 'inst-card--local': item.isLocal }" @click="toggleSelect(item.key)">
                <div class="inst-card__top"><div class="inst-card__identity"><span class="live-dot" :class="item.online ? 'live-dot--on' : 'live-dot--off'" /><div class="inst-card__names"><div class="inst-card__title-row"><span class="inst-card__title" :title="item.title">{{ item.title }}</span><Tag v-if="item.isLocal" color="blue" class="local-tag">本机</Tag><Tag :color="item.online ? 'success' : 'default'" class="inst-tag">{{ item.online ? '在线' : '离线' }}</Tag></div><div class="inst-card__meta"><span class="meta-ip">{{ item.ip }}</span> · {{ item.businessLine }} · {{ item.instanceCount }} 个运行实例（在线 {{ item.onlineCount }} / 离线 {{ item.offlineCount }}）</div></div></div></div>
                <div class="inst-metrics">
                  <div class="metric"><div class="metric__head"><span>平均 CPU</span><strong :class="{ 'is-warn': Number(item.cpuLoad) >= 80 }">{{ formatCpu(item.cpuLoad) }}</strong></div><div class="metric__bar"><i :style="{ width: `${clampPct(item.cpuLoad)}%`, background: Number(item.cpuLoad) >= 80 ? '#ff7d00' : '#266cfb' }" /></div></div>
                  <div class="metric"><div class="metric__head"><span>平均堆内存</span><strong>{{ compactHeap(item) }}</strong></div><div class="metric__bar"><i :style="{ width: `${heapPct(item)}%`, background: heapPct(item) >= 85 ? '#ff7d00' : '#14c9c9' }" /></div></div>
                </div>
                <div class="traffic-row">
                  <span :class="{ 'is-warn': Number(item.deliverSuccessRate) < 0.95 }"><i>成功率</i>{{ formatPercentRate(item.deliverSuccessRate) }}</span>
                  <span><i>入站</i>{{ metricVal(item, 'accepted') }}</span>
                  <span><i>送达</i>{{ metricVal(item, 'delivered') }}</span>
                  <span :class="{ 'is-warn': Number(metricVal(item, 'failed')) > 0 }"><i>失败</i>{{ metricVal(item, 'failed') }}</span>
                  <span><i>死信</i>{{ metricVal(item, 'dlq') }}</span>
                </div>
                <div class="inst-card__foot"><span class="heartbeat">{{ item.onlineCount ? `最近心跳 ${relativeHeartbeat(item.lastHeartbeatTime)}` : '暂无在线实例' }}</span><div class="inst-actions" @click.stop><Button size="small" type="link" :disabled="state.cmdLoading || !item.onlineCount" @click="() => issueMachineCommand('PING', item)">探活</Button><Button size="small" type="link" :disabled="state.cmdLoading || !item.onlineCount" @click="() => issueMachineCommand('RELOAD_CONFIG', item)">重载</Button><Button v-if="item.onlineCount" size="small" type="link" danger :disabled="state.cmdLoading" @click="() => confirmMachineShutdown(item)">停机</Button></div></div>
                <div v-if="state.selectedId === item.key" class="inst-detail machine-detail" @click.stop>
                  <div class="machine-detail__head"><strong>该机器上的运行实例</strong><span>{{ item.roles || '全能' }}</span></div>
                  <div v-for="container in item.instances" :key="container.instanceId" class="container-row"><div class="container-row__main"><span class="live-dot" :class="container.online ? 'live-dot--on' : 'live-dot--off'" /><div><div class="container-row__id" :title="container.instanceId">{{ shortId(container.instanceId) }}</div><div class="container-row__meta">数据转发 · {{ container._roleLabel || '全能' }} · {{ relativeHeartbeat(container.lastHeartbeatTime) }}</div></div></div><div class="inst-actions"><Button size="small" type="link" :disabled="state.cmdLoading" @click="() => issueCommand('PING', container.instanceId)">探活</Button><Button size="small" type="link" :disabled="state.cmdLoading" @click="() => issueCommand('RELOAD_CONFIG', container.instanceId)">重载</Button><Button v-if="container.online" size="small" type="link" danger :disabled="state.cmdLoading" @click="() => confirmShutdown(container)">停机</Button><Button v-else size="small" type="link" danger :disabled="state.purgeLoading" @click="() => confirmRemoveRecord(container)">移除记录</Button></div></div>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { List, Tag, Tooltip, Spin } from 'ant-design-vue'
import { CountTo } from '@/components/CountTo'
import { Icon } from '@/components/Icon'
import { RadioButtonGroup } from '@/components/Form'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  getTransformCluster,
  getTransformCommandAcks,
  getTransformInstances,
  issueTransformCommand,
  purgeTransformInstances,
  removeTransformInstance,
} from '@/api/device/transform'
import {
  getNodePage,
  stopNodeWorkload,
  stopNodeWorkloadById,
  type ComputeNodeVO,
} from '@/api/device/node'
import { isPlatformNode } from '@/views/node/utils/platformNode'
import {
  formatCpu,
  formatHeartbeat,
  formatPercentRate,
} from '../data'

defineOptions({ name: 'TransformClusterPanel' })

const ListItem = List.Item

const ROLE_LABELS: Record<string, string> = {
  full: '全能',
  worker: '工作节点',
  edge: '边缘',
  relay: '中继',
}

const { createMessage, createConfirm } = useMessage()

const rawList = ref<Recordable[]>([])
const nodeList = ref<ComputeNodeVO[]>([])
const clusterInfo = ref<Recordable>({})
const lastUpdated = ref('')
const lastCmdSummary = ref('')
const PAGE_SIZE = 9

const state = reactive({
  statusFilter: '',
  selectedId: '' as string,
  loading: false,
  cmdLoading: false,
  purgeLoading: false,
  page: 1,
})

let timer: ReturnType<typeof setInterval> | null = null

const platformNode = computed(
  () => nodeList.value.find((n) => isPlatformNode(n)) || null,
)

const ONLINE_WINDOW_MS = 90_000

const allList = computed(() => {
  const localId = String(clusterInfo.value.localInstanceId || '')
  const localHost = String(clusterInfo.value.localHost || '')
  return rawList.value.map((item) =>
    enrichInstance(item, nodeList.value, platformNode.value, localId, localHost),
  )
})

const machineList = computed(() => groupMachines(allList.value))
const onlineCount = computed(() => machineList.value.filter((item) => item.online).length)
const offlineCount = computed(() => machineList.value.length - onlineCount.value)
const localCount = computed(() => machineList.value.filter((item) => item.isLocal).length)

function sortMachines(list: Recordable[]) {
  return [...list].sort((a, b) => {
    const localDiff = Number(!!b.isLocal) - Number(!!a.isLocal)
    if (localDiff) return localDiff
    const onlineDiff = Number(!!b.online) - Number(!!a.online)
    if (onlineDiff) return onlineDiff
    return String(a.title || '').localeCompare(String(b.title || ''), 'zh')
  })
}

function sortInstances(list: Recordable[]) {
  return [...list].sort((a, b) => {
    const onlineDiff = Number(!!b.online) - Number(!!a.online)
    if (onlineDiff) return onlineDiff
    const localDiff = Number(!!b._isLocal) - Number(!!a._isLocal)
    if (localDiff) return localDiff
    return String(a.instanceId || '').localeCompare(String(b.instanceId || ''))
  })
}

const filteredList = computed(() => {
  let list = machineList.value
  if (state.statusFilter === 'online') list = list.filter((i) => !!i.online)
  else if (state.statusFilter === 'offline') list = list.filter((i) => !i.online)
  else if (state.statusFilter === 'local') list = list.filter((i) => !!i.isLocal)
  return sortMachines(list)
})

const pagedList = computed(() => {
  const start = (state.page - 1) * PAGE_SIZE
  return filteredList.value.slice(start, start + PAGE_SIZE)
})

const paginationProp = computed(() => ({
  showSizeChanger: false,
  showQuickJumper: false,
  pageSize: PAGE_SIZE,
  current: state.page,
  total: filteredList.value.length,
  showTotal: (total: number) => `共 ${total} 台机器 · 每页 ${PAGE_SIZE} 台`,
  onChange: (page: number) => {
    state.page = page
  },
}))

const filterOptions = computed(() => [
  { label: `全部 (${machineList.value.length})`, value: '' },
  { label: `本机 (${localCount.value})`, value: 'local' },
  { label: `在线 (${onlineCount.value})`, value: 'online' },
  { label: `离线 (${offlineCount.value})`, value: 'offline' },
])

const onlineRate = computed(() => {
  if (!machineList.value.length) return 0
  return Math.round((onlineCount.value / machineList.value.length) * 100)
})

const overviewCards = computed(() => [
  {
    key: 'total',
    label: '机器数',
    value: machineList.value.length,
    filter: '' as string | null,
    icon: 'ant-design:cluster-outlined',
    bg: '#f0f5ff',
    color: '#266cfb',
  },
  {
    key: 'local',
    label: '本机',
    value: localCount.value,
    filter: 'local' as string | null,
    icon: 'ant-design:desktop-outlined',
    bg: '#e8f0ff',
    color: '#266cfb',
  },
  {
    key: 'online',
    label: '在线机器',
    value: onlineCount.value,
    sub: `${onlineRate.value}%`,
    filter: 'online' as string | null,
    icon: 'ant-design:check-circle-outlined',
    bg: '#e8ffea',
    color: '#00b42a',
  },
  {
    key: 'offline',
    label: '离线机器',
    value: offlineCount.value,
    warn: offlineCount.value > 0,
    filter: 'offline' as string | null,
    icon: 'ant-design:disconnect-outlined',
    bg: '#f2f3f5',
    color: '#86909c',
  },
])

function toggleFilter(filter: string) {
  state.statusFilter = state.statusFilter === filter && filter !== '' ? '' : filter
  state.page = 1
}

function toggleSelect(id: string) {
  state.selectedId = state.selectedId === id ? '' : id
}

function shortId(id?: string) {
  if (!id) return '—'
  if (id.length <= 14) return id
  return `${id.slice(0, 8)}…${id.slice(-4)}`
}

function roleLabel(role?: string) {
  if (!role) return ''
  return ROLE_LABELS[role] || role
}

function normalizeKey(v?: string | number | null) {
  if (v == null) return ''
  return String(v).trim().toLowerCase()
}

function parseHeartbeatMs(value: any): number {
  if (value === null || value === undefined || value === '') return NaN
  const num = Number(value)
  if (!Number.isNaN(num) && num > 1e9) {
    return num > 1e12 ? num : num * 1000
  }
  const d = new Date(value)
  return d.getTime()
}

/** 后端 online 与心跳双保险，避免 45s 过短窗口导致刷新后在线数骤降 */
function resolveOnline(item: Recordable): boolean {
  const ms = parseHeartbeatMs(item.lastHeartbeatTime)
  if (!Number.isNaN(ms) && Date.now() - ms <= ONLINE_WINDOW_MS) return true
  return !!item.online
}

function matchNode(
  item: Recordable,
  nodes: ComputeNodeVO[],
  platform: ComputeNodeVO | null,
): ComputeNodeVO | null {
  const nodeId = String(item.nodeId || '').trim()
  const host = String(item.host || '').trim()
  if (nodeId) {
    const byId = nodes.find((n) => n.id != null && String(n.id) === nodeId)
    if (byId) return byId
    const byName = nodes.find((n) => normalizeKey(n.name) === normalizeKey(nodeId))
    if (byName) return byName
    if (['platform', 'local', 'control-plane', 'controlplane'].includes(normalizeKey(nodeId))) {
      return platform
    }
  }
  if (host) {
    const byHost = nodes.find(
      (n) =>
        normalizeKey(n.host) === normalizeKey(host) ||
        normalizeKey(n.name) === normalizeKey(host),
    )
    if (byHost) return byHost
  }
  return null
}

function enrichInstance(
  item: Recordable,
  nodes: ComputeNodeVO[],
  platform: ComputeNodeVO | null,
  localInstanceId: string,
  localHost: string,
) {
  const matched = matchNode(item, nodes, platform)
  const nodeIdRaw = String(item.nodeId || '').trim()
  const hostRaw = String(item.host || '').trim()
  const online = resolveOnline(item)
  const isLocalHint = ['platform', 'local', 'control-plane', 'controlplane'].includes(
    normalizeKey(nodeIdRaw),
  )
  const sameAsApiHost =
    !!localHost && !!hostRaw && normalizeKey(localHost) === normalizeKey(hostRaw)
  const sameAsApiInstance =
    !!localInstanceId && String(item.instanceId || '') === localInstanceId
  // 同主机名的已销毁容器不要标「本机」：仅当前服务实例 / 在线同机 / 明确 platform 绑定
  const isLocal =
    sameAsApiInstance ||
    isLocalHint ||
    (sameAsApiHost && online) ||
    (matched != null && isPlatformNode(matched) && (online || sameAsApiInstance))

  let nodeTitle = matched?.name || ''
  if (!nodeTitle && isLocal && platform?.name) nodeTitle = platform.name
  if (!nodeTitle && isLocal) nodeTitle = hostRaw || '本机控制面'
  if (!nodeTitle && nodeIdRaw) nodeTitle = nodeIdRaw
  if (!nodeTitle && hostRaw) nodeTitle = hostRaw
  if (!nodeTitle) nodeTitle = '未绑定节点'

  return {
    ...item,
    online,
    _nodeTitle: nodeTitle,
    _matchedNodeName: matched?.name || '',
    _nodeHost: matched?.host || hostRaw || '',
    _registryHost: matched?.host || '',
    _boundNodeId: matched?.id ?? null,
    _isLocal: isLocal,
    _roleLabel: roleLabel(item.role),
  }
}

function average(values: unknown[]) {
  const valid = values.map(Number).filter((value) => !Number.isNaN(value))
  if (!valid.length) return null
  return valid.reduce((sum, value) => sum + value, 0) / valid.length
}

function sumMetric(instances: Recordable[], key: string) {
  return instances.reduce((sum, item) => {
    const value = Number(item?.metrics?.[key])
    return sum + (Number.isNaN(value) ? 0 : value)
  }, 0)
}

function isDockerHostname(host?: string) {
  return /^[a-f0-9]{12}$/i.test(String(host || '').trim())
}

/** 是否适合作为机器维度展示的地址（IP 或正常主机名） */
function isMachineAddress(host?: string) {
  const v = String(host || '').trim()
  if (!v) return false
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(v)) return true
  if (isDockerHostname(v)) return false
  return /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(v)
}

/**
 * 数据转发业务维度：按「机器」聚合运行实例。
 * nodeId / host 仅作机器身份，不引入 NODE「纳管」语义。
 */
function machineKey(item: Recordable) {
  if (item._isLocal) return 'local-machine'
  if (item._boundNodeId != null) return `node-${item._boundNodeId}`
  const nid = String(item.nodeId || '').trim()
  if (/^\d+$/.test(nid)) return `node-${nid}`
  if (nid && !isDockerHostname(nid) && !['unknown', 'platform', 'local'].includes(normalizeKey(nid))) {
    return `host-${normalizeKey(nid)}`
  }
  const registry = String(item._registryHost || '').trim()
  if (registry && isMachineAddress(registry)) return `host-${normalizeKey(registry)}`
  const host = String(item.host || item._nodeHost || '').trim()
  if (host) return `host-${normalizeKey(host)}`
  return 'host-unknown'
}

function groupMachines(instances: Recordable[]) {
  const groups = new Map<string, Recordable[]>()
  instances.forEach((item) => {
    const key = machineKey(item)
    groups.set(key, [...(groups.get(key) || []), item])
  })
  return [...groups.entries()]
    .map(([key, members]) => {
      const primary =
        members.find((item) => item._isLocal) ||
        members.find((item) => item._boundNodeId != null) ||
        members[0]
      const onlineMembers = members.filter((item) => item.online)
      const isLocal = key === 'local-machine' || members.some((item) => item._isLocal)
      const displayName = primary._matchedNodeName || ''
      const ip =
        members.map((item) => item._registryHost).find((h) => isMachineAddress(h)) ||
        members.map((item) => item.host).find((h) => isMachineAddress(h)) ||
        (isLocal ? String(primary._nodeHost || primary.host || '') : '') ||
        String(primary.host || primary._nodeHost || '')
      const roles = [...new Set(members.map((item) => item._roleLabel).filter(Boolean))].join(' / ')
      const heartbeat = members
        .map((item) => ({ item, ms: parseHeartbeatMs(item.lastHeartbeatTime) }))
        .filter((entry) => !Number.isNaN(entry.ms))
        .sort((a, b) => b.ms - a.ms)[0]?.item
      const heapUsedMb = average(members.map((item) => item.heapUsedMb))
      const heapMaxMb = average(members.map((item) => item.heapMaxMb))

      // 标题优先 IP，其次主机名/节点名；本机固定「本机」
      let title = isLocal ? '本机' : ''
      if (!title && isMachineAddress(ip) && /^\d{1,3}(\.\d{1,3}){3}$/.test(ip)) title = ip
      if (!title && displayName) title = displayName
      if (!title && isMachineAddress(ip)) title = ip
      if (!title) title = ip || '转发主机'

      const roleText = roles || '全能'
      const businessLine = `数据转发 · ${roleText}`

      return {
        key,
        title,
        ip: ip || '—',
        isLocal,
        online: onlineMembers.length > 0,
        onlineCount: onlineMembers.length,
        offlineCount: members.length - onlineMembers.length,
        instanceCount: members.length,
        roles: roleText,
        businessLine,
        instances: sortInstances(members),
        cpuLoad: average(members.map((item) => item.cpuLoad)),
        heapUsedMb,
        heapMaxMb,
        deliverSuccessRate: average(members.map((item) => item.deliverSuccessRate)),
        lastHeartbeatTime: heartbeat?.lastHeartbeatTime,
        metrics: {
          accepted: sumMetric(members, 'accepted'),
          delivered: sumMetric(members, 'delivered'),
          failed: sumMetric(members, 'failed'),
          dlq: sumMetric(members, 'dlq'),
        },
      }
    })
    .sort((a, b) => {
      const localDiff = Number(b.isLocal) - Number(a.isLocal)
      if (localDiff) return localDiff
      const onlineDiff = Number(b.online) - Number(a.online)
      if (onlineDiff) return onlineDiff
      return String(a.title).localeCompare(String(b.title), 'zh')
    })
}

function clampPct(val?: number | null) {
  const n = Number(val)
  if (Number.isNaN(n)) return 0
  return Math.max(0, Math.min(100, n))
}

function heapPct(item: Recordable) {
  const used = Number(item.heapUsedMb)
  const max = Number(item.heapMaxMb)
  if (!max || Number.isNaN(used) || Number.isNaN(max)) return 0
  return clampPct((used / max) * 100)
}

function compactHeap(item: Recordable) {
  const used = item.heapUsedMb
  const max = item.heapMaxMb
  if (used == null) return '—'
  if (max == null) return `${used} MB`
  if (Number(max) >= 4096) return `${heapPct(item).toFixed(0)}% · ${used}MB`
  return `${used}/${max}`
}

function metricVal(item: Recordable, key: string) {
  const m = item?.metrics
  if (!m || typeof m !== 'object') return '—'
  const v = m[key]
  return v == null ? '—' : v
}

function splitGroups(groups?: string) {
  if (!groups) return []
  return String(groups)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

function shortGroup(g: string) {
  if (g.length <= 24) return g
  return `${g.slice(0, 10)}…${g.slice(-8)}`
}

function hasMetrics(item: Recordable) {
  return item?.metrics && typeof item.metrics === 'object' && Object.keys(item.metrics).length > 0
}

function pickMetrics(item: Recordable) {
  const m = item.metrics || {}
  const prefer = ['accepted', 'delivered', 'failed', 'dlq', 'published', 'relayed']
  const out: Recordable = {}
  prefer.forEach((k) => {
    if (m[k] != null) out[k] = m[k]
  })
  if (!Object.keys(out).length) {
    Object.keys(m)
      .slice(0, 4)
      .forEach((k) => {
        out[k] = m[k]
      })
  }
  return out
}

function relativeHeartbeat(value: any) {
  const ms = parseHeartbeatMs(value)
  if (Number.isNaN(ms)) {
    if (value === null || value === undefined || value === '') return '无心跳'
    return formatHeartbeat(value)
  }
  const diff = Date.now() - ms
  if (diff < 0) return formatHeartbeat(value)
  if (diff < 60_000) return `${Math.max(1, Math.floor(diff / 1000))} 秒前`
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  return formatHeartbeat(value)
}

function stampUpdated() {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  lastUpdated.value = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

async function loadNodes() {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 500 })
    nodeList.value = res?.data?.list || []
  } catch {
    nodeList.value = []
  }
}

async function handleRefresh() {
  state.loading = true
  try {
    const [cluster, list] = await Promise.all([
      getTransformCluster(),
      getTransformInstances(),
      loadNodes(),
    ])
    clusterInfo.value = cluster || {}
    rawList.value = list || []
    if (state.selectedId && !machineList.value.some((item) => item.key === state.selectedId)) {
      state.selectedId = ''
    }
    stampUpdated()
  } catch (error: any) {
    createMessage.error(error?.message || '刷新失败')
  } finally {
    state.loading = false
  }
}

function resolveBoundNodeId(item: Recordable): number | null {
  if (item._boundNodeId != null && !Number.isNaN(Number(item._boundNodeId))) {
    return Number(item._boundNodeId)
  }
  const raw = Number(item.nodeId)
  if (!Number.isNaN(raw) && raw > 0) return raw
  return null
}

/** 心跳未带 TRANSFORM_NODE_ID 时，尽量推断硬停目标节点 */
function inferStopNodeId(item: Recordable): number | null {
  const fromBound = resolveBoundNodeId(item)
  if (fromBound != null) return fromBound

  const fromWid = String(item.instanceId || '').match(/^tr-n(\d+)-/i)
  if (fromWid) {
    const id = Number(fromWid[1])
    if (!Number.isNaN(id) && id > 0) return id
  }

  const hosts = [
    item._registryHost,
    item._nodeHost,
    item.host,
  ]
    .map((h) => String(h || '').trim())
    .filter(Boolean)
  for (const host of hosts) {
    if (isDockerHostname(host)) continue
    const matched = nodeList.value.find(
      (n) =>
        normalizeKey(n.host) === normalizeKey(host) ||
        normalizeKey(n.name) === normalizeKey(host),
    )
    if (matched?.id != null) return Number(matched.id)
  }

  // 本机 / Docker 短主机名：优先走控制面 Agent（同机 docker rm）
  if (item._isLocal || isDockerHostname(item.host) || isDockerHostname(item._nodeHost)) {
    if (platformNode.value?.id != null) return Number(platformNode.value.id)
  }
  return null
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitCommandAcks(commandId: string, expectAtLeast = 1, timeoutMs = 8000) {
  if (!commandId) return [] as Recordable[]
  const started = Date.now()
  let acks: Recordable[] = []
  while (Date.now() - started < timeoutMs) {
    try {
      acks = (await getTransformCommandAcks(commandId)) || []
      if (acks.length >= expectAtLeast) return acks
    } catch {
      return acks
    }
    await sleep(500)
  }
  return acks
}

function summarizeAcks(type: string, acks: Recordable[]) {
  if (!acks.length) return `${type} 已下发，暂未收到回执（请确认 runtime 已升级）`
  const ok = acks.filter((a) => ['OK', 'ACCEPTED'].includes(String(a.status))).length
  const fail = acks.filter((a) => a.status === 'FAILED').length
  const restart = acks.filter((a) => a.status === 'REQUIRES_RESTART').length
  const parts = [`回执 ${acks.length}`]
  if (ok) parts.push(`成功 ${ok}`)
  if (restart) parts.push(`需重启 ${restart}`)
  if (fail) parts.push(`失败 ${fail}`)
  const sample = acks
    .slice(0, 3)
    .map((a) => `${shortId(a.instanceId)}:${a.status}`)
    .join(' · ')
  return `${type} · ${parts.join(' / ')} · ${sample}`
}

async function issueCommand(type: string, targetInstanceId: string) {
  try {
    state.cmdLoading = true
    const res = await issueTransformCommand({
      type,
      targetInstanceId,
      issuedAt: Date.now(),
    })
    const cmdId = (res as any)?.commandId || ''
    const label =
      type === 'PING' ? '探活' : type === 'RELOAD_CONFIG' ? '重载配置' : '优雅停机'
    const expect =
      targetInstanceId === '*'
        ? Math.max(1, onlineContainerCount.value || 1)
        : 1
    const acks = await waitCommandAcks(cmdId, expect, type === 'SHUTDOWN_HINT' ? 5000 : 8000)
    lastCmdSummary.value = summarizeAcks(label, acks)
    if (acks.some((a) => a.status === 'FAILED')) {
      createMessage.warning(lastCmdSummary.value)
    } else if (acks.length) {
      createMessage.success(lastCmdSummary.value)
    } else {
      createMessage.info(
        `${label}已下发${targetInstanceId === '*' ? '（广播）' : ''}${
          cmdId ? ` · ${String(cmdId).slice(0, 8)}` : ''
        }`,
      )
    }
    if (type === 'PING' || type === 'RELOAD_CONFIG') {
      await handleRefresh()
    }
    return { commandId: cmdId, acks }
  } catch (error: any) {
    createMessage.error(error?.message || '指令下发失败')
    return null
  } finally {
    state.cmdLoading = false
  }
}

async function issueMachineCommand(type: string, machine: Recordable) {
  const targets = machine.instances.filter((item: Recordable) => item.online)
  if (!targets.length) {
    createMessage.info('该机器没有在线容器可执行指令')
    return
  }
  const failures: string[] = []
  for (const item of targets) {
    const result = await issueCommand(type, item.instanceId)
    if (!result) failures.push(shortId(item.instanceId))
  }
  if (targets.length > 1) {
    lastCmdSummary.value = `${type === 'PING' ? '机器探活' : '机器重载'}：已下发 ${targets.length} 个在线容器${
      failures.length ? `，失败 ${failures.join('、')}` : ''
    }`
  }
}

async function hardStopWorkload(item: Recordable) {
  const nodeId = inferStopNodeId(item)
  const workloadId = String(item.instanceId || '')
  if (!workloadId) {
    createMessage.warning('缺少 instanceId，无法硬停')
    return false
  }
  try {
    if (nodeId != null) {
      await stopNodeWorkload(nodeId, 'transform_runtime', workloadId)
      createMessage.success(`已通过节点 #${nodeId} Agent 硬停 ${shortId(workloadId)}`)
      return true
    }
    // 无节点可推断：尝试绑定表反查（节点分发部署过的实例）
    await stopNodeWorkloadById('transform_runtime', workloadId)
    createMessage.success(`已按绑定反查硬停 ${shortId(workloadId)}`)
    return true
  } catch (error: any) {
    const msg = error?.message || '节点硬停失败'
    if (nodeId == null) {
      createMessage.warning(
        `无法定位 Agent（未绑定 TRANSFORM_NODE_ID / 无 workload 绑定）。仅完成优雅退出，Docker unless-stopped 可能被拉起。${msg}`,
      )
    } else {
      createMessage.error(msg)
    }
    return false
  }
}

function confirmShutdown(item: Recordable) {
  const name = item._nodeTitle || shortId(item.instanceId)
  const nodeId = inferStopNodeId(item)
  createConfirm({
    iconType: 'warning',
    title: '停机（先硬停容器，再优雅退出）',
    content: nodeId
      ? `将对「${name}」通过节点 #${nodeId} Agent 执行 docker rm，并下发 SHUTDOWN_HINT。确认继续？`
      : `「${name}」未解析到节点，将尝试绑定反查硬停；失败则仅优雅退出（旧 unless-stopped 容器可能被拉起）。确认继续？`,
    onOk: async () => {
      // 先硬停：避免 JVM 退出后 unless-stopped 立刻拉起
      const hard = await hardStopWorkload(item)
      if (!hard) {
        await issueCommand('SHUTDOWN_HINT', item.instanceId)
      }
      await sleep(800)
      await handleRefresh()
    },
  })
}

function confirmMachineShutdown(machine: Recordable) {
  const targets = machine.instances.filter((item: Recordable) => item.online)
  createConfirm({
    iconType: 'warning',
    title: '停止机器上的 TRANSFORM 容器',
    content: `将对「${machine.title}」上的 ${targets.length} 个在线容器优先 Agent 硬停（docker rm），失败再优雅退出。确认继续？`,
    onOk: async () => {
      for (const item of targets) {
        const hard = await hardStopWorkload(item)
        if (!hard) {
          await issueCommand('SHUTDOWN_HINT', item.instanceId)
        }
      }
      await sleep(800)
      await handleRefresh()
    },
  })
}

function confirmRemoveRecord(item: Recordable) {
  createConfirm({
    iconType: 'warning',
    title: '移除幽灵记录',
    content: `容器「${item._nodeTitle || shortId(item.instanceId)}」已离线。仅从监控表删除记录，不会操作 Docker。确认移除？`,
    onOk: async () => {
      try {
        state.purgeLoading = true
        await removeTransformInstance(item.instanceId)
        createMessage.success('已移除记录')
        await handleRefresh()
      } catch (error: any) {
        createMessage.error(error?.message || '移除失败')
      } finally {
        state.purgeLoading = false
      }
    },
  })
}

function confirmPurgeOffline() {
  const offline = offlineContainerCount.value
  if (!offline) {
    createMessage.info('当前没有离线实例')
    return
  }
  createConfirm({
    iconType: 'warning',
    title: '清理离线幽灵实例',
    content: `将删除超过 10 分钟无心跳的幽灵记录（约 ${offline} 台机器相关）。不会停掉真实容器。确认清理？`,
    onOk: async () => {
      try {
        state.purgeLoading = true
        const res = await purgeTransformInstances(true)
        const removed = Number((res as any)?.removed ?? 0)
        createMessage.success(removed > 0 ? `已清理 ${removed} 条幽灵记录` : '没有可清理的记录')
        if (Array.isArray((res as any)?.instances)) {
          rawList.value = (res as any).instances
          stampUpdated()
        } else {
          await handleRefresh()
        }
      } catch (error: any) {
        createMessage.error(error?.message || '清理失败（需重启 TRANSFORM 后生效）')
      } finally {
        state.purgeLoading = false
      }
    },
  })
}

watch(
  () => state.statusFilter,
  () => {
    state.page = 1
    if (
      state.selectedId &&
      !filteredList.value.some((item) => item.key === state.selectedId)
    ) {
      state.selectedId = ''
    }
  },
)

watch(
  () => state.page,
  () => {
    if (
      state.selectedId &&
      !pagedList.value.some((item) => item.key === state.selectedId)
    ) {
      state.selectedId = ''
    }
  },
)

watch(
  () => filteredList.value.length,
  (total) => {
    const maxPage = Math.max(1, Math.ceil(total / PAGE_SIZE) || 1)
    if (state.page > maxPage) state.page = maxPage
  },
)

onMounted(async () => {
  await handleRefresh()
  timer = setInterval(() => {
    handleRefresh()
  }, 12000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

defineExpose({ refresh: handleRefresh })
</script>

<style lang="less" scoped>
@import '../theme.less';

.panel {
  .tf-panel();
}

.metric-strip {
  .tf-metric-strip();
}

.metric-item {
  .tf-metric-item();
  transition: background 0.15s;

  &--click {
    cursor: pointer;
  }

  &:hover {
    background: @tf-primary-bg;
  }

  &--active {
    background: @tf-primary-bg;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      height: 2px;
      background: @tf-primary;
    }
  }

  &--warn {
    background: #fffaf0;
  }
}

.metric-item__icon {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-item__label {
  display: block;
  font-size: 12px;
  color: @tf-text-secondary;
  line-height: 1.2;
}

.metric-item__value {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 2px;
  font-size: 20px;
  font-weight: 600;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}

.metric-item__suffix {
  font-size: 12px;
  font-weight: 500;
  color: @tf-text-muted;
}

.metric-item__sub {
  display: block;
  margin-top: 1px;
  font-size: 11px;
  color: @tf-text-muted;
}

.panel-bar {
  .tf-panel-bar();
}

.panel-bar__label {
  font-size: 13px;
  color: @tf-text-muted;
  flex-shrink: 0;
}

.panel-bar__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 8px;
}

.ch-tag {
  margin: 0 !important;
  border-color: @tf-primary-light !important;
  background: @tf-primary-bg !important;
  color: @tf-primary !important;

  &--cmd {
    border-color: #b7eb8f !important;
    background: #f6ffed !important;
    color: #389e0d !important;
  }
}

.sync {
  font-size: 12px;
  color: @tf-text-muted;
  font-variant-numeric: tabular-nums;

  &--ok {
    color: #00b42a;
  }

  &--busy {
    color: #ff7d00;
  }
}

.ack-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-bottom: 1px solid @tf-border;
  background: @tf-primary-bg;
  font-size: 12px;
  color: @tf-text-secondary;
}

.ack-bar__label {
  flex-shrink: 0;
  color: @tf-primary;
  font-weight: 600;
}

.ack-bar__text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-body {
  .tf-panel-body();
  overflow: auto;
  padding: 12px;
}

.instance-list {
  :deep(.ant-row) {
    display: flex;
    flex-wrap: wrap;
    align-items: start;
  }

  :deep(.ant-col) {
    display: flex;
    align-items: start;
  }

  :deep(.ant-list-item) {
    margin-bottom: 0;
    padding: 0 !important;
    border: none;
    width: 100%;
    display: flex;
    align-items: start;
  }

  :deep(.ant-list-pagination) {
    margin-top: 12px;
    text-align: right;
  }
}

.instance-list-item {
  width: 100%;
}

.empty-box {
  padding: 40px 24px;
  text-align: center;
  border: 1px dashed @tf-border;
  border-radius: @tf-radius;
  background: @tf-soft;
}

.empty-box__title {
  font-size: 15px;
  font-weight: 600;
  color: @tf-text-primary;
}

.empty-box__desc {
  margin-top: 8px;
  font-size: 13px;
  color: @tf-text-muted;
  line-height: 1.6;

  code {
    padding: 0 4px;
    background: @tf-bg;
    border-radius: 3px;
  }
}

.inst-card {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid @tf-border;
  border-radius: @tf-radius;
  background: @tf-bg;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  align-self: start;

  &:hover {
    border-color: @tf-primary-light;
    box-shadow: @tf-card-shadow;
  }

  &--active {
    border-color: @tf-primary;
    box-shadow: 0 0 0 1px fade(@tf-primary, 16%);
  }

  &--offline {
    background: @tf-soft;
  }

  &--local {
    border-color: @tf-primary-light;
  }
}

.inst-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.inst-card__identity {
  display: flex;
  gap: 8px;
  min-width: 0;
}

.inst-card__names {
  min-width: 0;
}

.live-dot {
  width: 7px;
  height: 7px;
  margin-top: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &--on {
    background: #00b42a;
    box-shadow: 0 0 0 3px rgba(0, 180, 42, 0.16);
  }

  &--off {
    background: #c9cdd4;
  }
}

.inst-card__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 6px;
  min-width: 0;
}

.inst-card__title {
  font-size: 14px;
  font-weight: 650;
  color: @tf-text-primary;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

.inst-card__meta {
  margin-top: 3px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 4px;
  font-size: 11px;
  color: @tf-text-muted;
  line-height: 1.4;
}

.meta-ip {
  color: @tf-text-primary;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.mono-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
}

.local-tag,
.inst-tag,
.adapt-tag {
  margin: 0 !important;
  line-height: 18px;
  font-size: 11px;
}

.break-all {
  word-break: break-all;
}

.traffic-row {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 4px;
  padding: 6px 8px;
  border-radius: 4px;
  background: @tf-soft;
  font-size: 12px;
  color: @tf-text-primary;
  font-variant-numeric: tabular-nums;

  span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  i {
    font-style: normal;
    color: @tf-text-muted;
    margin-right: 3px;
    font-size: 11px;
  }
}

.adapt-tag {
  flex-shrink: 0;
}

.inst-metrics {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.metric__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11px;
  color: @tf-text-muted;
  margin-bottom: 4px;

  strong {
    color: @tf-text-primary;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }
}

.metric__bar {
  height: 5px;
  border-radius: 3px;
  background: @tf-border-light;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 3px;
  }
}

.is-warn {
  color: #ff7d00 !important;
}

.inst-card__foot {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid @tf-border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.heartbeat {
  font-size: 11px;
  color: @tf-text-muted;
}

.inst-actions {
  display: flex;
  align-items: center;

  :deep(.ant-btn) {
    padding-inline: 4px;
    height: 22px;
    font-size: 12px;
  }
}

.inst-detail {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: @tf-soft;
  border: 1px solid @tf-border;
}

.machine-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.machine-detail__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: @tf-text-secondary;
  font-size: 12px;

  strong {
    color: @tf-text-primary;
  }
}

.container-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 0;
  border-top: 1px solid @tf-border-light;
}

.container-row__main {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  gap: 8px;

  .live-dot {
    margin-top: 5px;
  }
}

.container-row__id {
  color: @tf-text-primary;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.3;
}

.container-row__meta {
  margin-top: 2px;
  color: @tf-text-muted;
  font-size: 11px;
}

.inst-detail__row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 12px;

  & + & {
    margin-top: 6px;
  }

  > span:first-child {
    color: @tf-text-muted;
    flex-shrink: 0;
    width: 42px;
  }

  em {
    font-style: normal;
    color: @tf-text-secondary;
    word-break: break-all;
  }
}

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.kv-line {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: @tf-text-secondary;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
}

.muted {
  color: #c9cdd4;
}
</style>
