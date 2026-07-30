<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>容器管理</h1>
        <p>查看状态与资源；启停需确认，点「日志」可查看完整输出</p>
      </div>
      <div class="stat-row">
        <div class="stat"><span>运行中</span><b class="ok">{{ runningCount }}</b></div>
        <div class="stat"><span>已停止</span><b>{{ stoppedCount }}</b></div>
        <div class="stat"><span>全部</span><b>{{ list.length }}</b></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-hd toolbar-hd">
        <a-input-search
          v-model:value="keyword"
          allow-clear
          size="small"
          placeholder="搜索名称 / 镜像 / ID / 端口"
          style="width: 280px"
        />
        <a-radio-group v-model:value="stateFilter" button-style="solid" size="small">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="running">运行中</a-radio-button>
          <a-radio-button value="exited">已停止</a-radio-button>
        </a-radio-group>
        <div class="toolbar-spacer" />
        <a-button size="small" type="primary" :loading="loading" @click="reload">刷新</a-button>
      </div>

      <a-table
        row-key="id"
        :loading="loading"
        :columns="columns"
        :data-source="filtered"
        :pagination="{
          pageSize: 10,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50'],
          showTotal: (t: number) => `共 ${t} 个`,
        }"
        :scroll="{ x: 1280 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="cell-name">
              <i class="status-dot" :class="record.state === 'running' ? 'on' : 'off'" />
              <div class="cell-name-text">
                <div class="name">{{ record.name || shortId(record.id) }}</div>
                <div class="mono muted">{{ shortId(record.id) }}</div>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'image'">
            <div class="wrap mono">{{ record.image }}</div>
          </template>
          <template v-else-if="column.key === 'state'">
            <a-tag :color="record.state === 'running' ? 'success' : 'default'">
              {{ record.state === 'running' ? '运行中' : record.state || '未知' }}
            </a-tag>
            <div class="muted status-line">{{ record.status }}</div>
          </template>
          <template v-else-if="column.key === 'cpu'">
            <div class="res">
              <div>{{ fmt(record.stats?.cpuPercent) }}</div>
              <div class="meter" :class="meterClass(record.stats?.cpuPercent)">
                <i :style="{ width: `${clamp(record.stats?.cpuPercent)}%` }" />
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'mem'">
            <div class="res">
              <div class="mono">{{ record.stats?.memUsage || '—' }}</div>
              <div class="meter" :class="meterClass(record.stats?.memPercent)">
                <i :style="{ width: `${clamp(record.stats?.memPercent)}%` }" />
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'net'">
            <div class="mono wrap">{{ record.stats?.netIO || '—' }}</div>
          </template>
          <template v-else-if="column.key === 'ports'">
            <div class="mono wrap">{{ record.ports || '—' }}</div>
          </template>
          <template v-else-if="column.key === 'action'">
            <div class="ops">
              <a-button
                size="small"
                type="primary"
                ghost
                :disabled="record.state === 'running'"
                @click="askAct(record, 'start')"
              >
                启动
              </a-button>
              <a-button
                size="small"
                :disabled="record.state !== 'running'"
                @click="askAct(record, 'stop')"
              >
                停止
              </a-button>
              <a-button size="small" @click="askAct(record, 'restart')">重启</a-button>
              <a-button size="small" type="primary" ghost @click="openLogs(record)">日志</a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <ConfirmDialog
      v-model:open="confirmOpen"
      :title="confirmTitle"
      :description="confirmDesc"
      :warning="confirmWarn"
      :rows="confirmRows"
      :ok-text="confirmOk"
      :danger="confirmDanger"
      :loading="confirmLoading"
      @confirm="doConfirm"
    />

    <LogDrawer
      v-model:open="logsOpen"
      :title="`日志 · ${logsName}`"
      :content="logsText"
      :loading="logsLoading"
      :meta="logsMeta"
      :on-refresh="refreshLogs"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import LogDrawer from '../components/LogDrawer.vue'
import {
  controlContainer,
  getContainerLogs,
  getContainers,
  type PanelContainer,
} from '../api'

const loading = ref(false)
const list = ref<PanelContainer[]>([])
const keyword = ref('')
const stateFilter = ref('all')

const confirmOpen = ref(false)
const confirmLoading = ref(false)
const confirmTitle = ref('')
const confirmDesc = ref('')
const confirmWarn = ref('')
const confirmOk = ref('确认')
const confirmDanger = ref(false)
const confirmRows = ref<{ label: string; value: string }[]>([])
let pending: { record: PanelContainer; action: 'start' | 'stop' | 'restart' } | null = null

const logsOpen = ref(false)
const logsLoading = ref(false)
const logsText = ref('')
const logsName = ref('')
const logsId = ref('')
const logsMeta = ref<{ label: string; value: string }[]>([])
let timer: number | undefined

const columns = [
  { title: '容器', key: 'name', width: 220 },
  { title: '镜像', key: 'image', width: 240 },
  { title: '状态', key: 'state', width: 170 },
  { title: 'CPU', key: 'cpu', width: 110 },
  { title: '内存', key: 'mem', width: 170 },
  { title: '网络', key: 'net', width: 150 },
  { title: '端口', key: 'ports', width: 220 },
  { title: '操作', key: 'action', width: 268, fixed: 'right' as const },
]

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return list.value.filter((c) => {
    const st = (c.state || '').toLowerCase()
    if (stateFilter.value === 'running' && st !== 'running') return false
    if (stateFilter.value === 'exited' && !(st === 'exited' || st === 'dead' || st === 'created')) return false
    if (!kw) return true
    return [c.name, c.image, c.status, c.id, c.ports].some((x) => (x || '').toLowerCase().includes(kw))
  })
})

const runningCount = computed(() => list.value.filter((c) => c.state === 'running').length)
const stoppedCount = computed(() => list.value.length - runningCount.value)

function shortId(id?: string) {
  return id ? id.slice(0, 12) : '—'
}
function fmt(v?: number) {
  if (v == null || Number.isNaN(v)) return '—'
  return `${Number(v).toFixed(1)}%`
}
function clamp(v?: number) {
  if (v == null || Number.isNaN(v)) return 0
  return Math.min(Math.max(v, 0), 100)
}
function meterClass(v?: number) {
  if (v == null) return ''
  if (v >= 90) return 'danger'
  if (v >= 70) return 'warn'
  return 'ok'
}

async function reload() {
  loading.value = true
  try {
    list.value = (await getContainers({ all: true, stats: true })).list || []
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

function askAct(record: PanelContainer, action: 'start' | 'stop' | 'restart') {
  const map = {
    start: { title: '启动容器', ok: '确认启动', danger: false, warn: '' },
    stop: { title: '停止容器', ok: '确认停止', danger: true, warn: '停止后依赖该容器的业务可能不可用。' },
    restart: { title: '重启容器', ok: '确认重启', danger: false, warn: '重启过程中会短暂中断。' },
  }[action]
  pending = { record, action }
  confirmTitle.value = map.title
  confirmDesc.value = '请核对信息后再执行，操作直接作用于宿主机 Docker。'
  confirmWarn.value = map.warn
  confirmOk.value = map.ok
  confirmDanger.value = map.danger
  confirmRows.value = [
    { label: '名称', value: record.name || '—' },
    { label: 'ID', value: record.id },
    { label: '镜像', value: record.image || '—' },
    { label: '状态', value: `${record.state || '—'} · ${record.status || ''}` },
    { label: '端口', value: record.ports || '—' },
  ]
  confirmOpen.value = true
}

async function doConfirm() {
  if (!pending) return
  confirmLoading.value = true
  try {
    await controlContainer(pending.record.id, pending.action)
    message.success('已提交')
    confirmOpen.value = false
    await reload()
  } finally {
    confirmLoading.value = false
    pending = null
  }
}

async function openLogs(record: PanelContainer) {
  logsOpen.value = true
  logsName.value = record.name || shortId(record.id)
  logsId.value = record.id
  logsMeta.value = [
    { label: '容器', value: record.name || '—' },
    { label: 'ID', value: record.id },
    { label: '镜像', value: record.image || '—' },
    { label: '状态', value: record.status || record.state || '—' },
  ]
  await refreshLogs()
}

async function refreshLogs() {
  if (!logsId.value) return
  logsLoading.value = true
  try {
    logsText.value = (await getContainerLogs(logsId.value, 2000)).logs || ''
  } catch {
    logsText.value = '读取失败'
  } finally {
    logsLoading.value = false
  }
}

onMounted(() => {
  reload()
  timer = window.setInterval(reload, 20000)
})
onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.toolbar-hd {
  gap: 12px;
}

.toolbar-spacer {
  flex: 1;
}

.stat-row {
  display: flex;
  gap: 8px;
}

.stat {
  min-width: 88px;
  height: 56px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  background: var(--c-white);
}

.stat span {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 18px;
}

.stat b {
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
}

.stat b.ok {
  color: var(--c-success);
}

.cell-name {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.cell-name-text {
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 14px;
  line-height: 22px;
}

.wrap {
  white-space: normal;
  word-break: break-all;
  line-height: 1.5;
}

.status-line {
  margin-top: 6px;
  max-width: 200px;
  word-break: break-word;
}

.res {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 96px;
}

.ops {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 6px;
  white-space: nowrap;
}

.ops :deep(.ant-btn) {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
  font-weight: 500;
  line-height: 22px;
  border-radius: 4px;
  flex-shrink: 0;
}

.ops :deep(.ant-btn-default) {
  color: var(--c-text-2);
  border-color: var(--c-border-2);
  background: #fff;
}

.ops :deep(.ant-btn-default:not(:disabled):hover) {
  color: var(--c-primary);
  border-color: var(--c-primary-border);
  background: var(--c-primary-bg);
}

.ops :deep(.ant-btn-primary.ant-btn-background-ghost) {
  color: #0958d9;
  border-color: #91caff;
  background: #fff;
}

.ops :deep(.ant-btn-primary.ant-btn-background-ghost:not(:disabled):hover) {
  color: #003eb3;
  border-color: #1677ff;
  background: #e6f4ff;
}

.ops :deep(.ant-btn-primary.ant-btn-background-ghost:disabled),
.ops :deep(.ant-btn-default:disabled) {
  color: rgba(0, 0, 0, 0.25);
  border-color: #d9d9d9;
  background: #f5f5f5;
}

:deep(.ant-table-pagination) {
  margin: 12px 16px !important;
}
</style>
