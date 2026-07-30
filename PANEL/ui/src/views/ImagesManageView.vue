<template>
  <div class="manage-root" :class="{ embedded }">
    <div class="page-head" v-if="!embedded">
      <div>
        <h1>镜像管理</h1>
        <p>
          按 EasyAIoT 模块核对本机运行时镜像 · 形态
          <code>{{ profile }}</code>
        </p>
      </div>
      <a-space>
        <a-radio-group v-model:value="profile" button-style="solid" size="small">
          <a-radio-button value="mini">mini</a-radio-button>
          <a-radio-button value="standard">standard</a-radio-button>
          <a-radio-button value="full">full</a-radio-button>
        </a-radio-group>
        <a-button size="small" type="primary" :loading="loading" @click="reload">刷新</a-button>
      </a-space>
    </div>

    <div class="embed-bar" v-else>
      <div class="embed-meta">
        形态 <code>{{ profile }}</code>
        <span class="muted">· 按模块核对运行时镜像</span>
      </div>
      <a-space>
        <a-radio-group v-model:value="profile" button-style="solid" size="small">
          <a-radio-button value="mini">mini</a-radio-button>
          <a-radio-button value="standard">standard</a-radio-button>
          <a-radio-button value="full">full</a-radio-button>
        </a-radio-group>
        <a-button size="small" type="primary" :loading="loading" @click="reload">刷新</a-button>
      </a-space>
    </div>

    <div class="summary-board">
      <div class="summary-main">
        <div class="summary-label">运行时就绪度</div>
        <div class="summary-ratio">
          <span class="ratio-num">{{ summary.ready }}</span>
          <span class="ratio-sep">/</span>
          <span class="ratio-den">{{ summary.required }}</span>
          <span class="meter-text">{{ readyPercent }}%</span>
        </div>
        <div class="summary-meter">
          <div class="meter-track">
            <i :style="{ width: `${readyPercent}%` }" />
          </div>
        </div>
      </div>
      <div class="summary-metrics">
        <button type="button" class="metric" @click="scope = 'required'">
          <span class="metric-k">形态所需</span>
          <strong class="metric-v">{{ summary.required }}</strong>
        </button>
        <button type="button" class="metric" @click="scope = 'required'">
          <span class="metric-k">已就绪</span>
          <strong class="metric-v ok">{{ summary.ready }}</strong>
        </button>
        <button type="button" class="metric" :class="{ alert: summary.missing > 0 }" @click="scope = 'missing'">
          <span class="metric-k">缺失</span>
          <strong class="metric-v" :class="{ danger: summary.missing > 0 }">{{ summary.missing }}</strong>
        </button>
        <button type="button" class="metric" @click="scope = 'all'">
          <span class="metric-k">本机镜像</span>
          <strong class="metric-v">{{ summary.totalLocalImages }}</strong>
        </button>
      </div>
    </div>

    <div class="toolbar-line">
      <a-input-search
        v-model:value="keyword"
        allow-clear
        size="small"
        placeholder="搜索模块 / 服务 / 镜像名"
        style="width: 260px"
      />
      <a-radio-group v-model:value="scope" button-style="solid" size="small">
        <a-radio-button value="required">当前形态</a-radio-button>
        <a-radio-button value="missing">仅缺失</a-radio-button>
        <a-radio-button value="all">全部目录</a-radio-button>
      </a-radio-group>
      <a-select
        v-model:value="moduleFilter"
        size="small"
        allow-clear
        placeholder="模块"
        style="width: 140px"
        :options="moduleOptions"
      />
      <div class="toolbar-spacer" />
      <a-button size="small" :disabled="!summary.dangling" @click="askPrune">清理悬空</a-button>
      <a-button size="small" type="primary" :disabled="summary.missing === 0" @click="emit('goto-build')">
        去拉取缺失
      </a-button>
    </div>

    <div class="panel">
      <a-table
        row-key="rowKey"
        :loading="loading"
        :columns="columns"
        :data-source="filtered"
        :pagination="{
          pageSize: 15,
          showSizeChanger: true,
          pageSizeOptions: ['15', '30', '50'],
          showTotal: (t: number) => `共 ${t} 项`,
        }"
        :scroll="{ x: 1180 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'service'">
            <div class="svc">
              <div class="svc-title">
                <a-tag>{{ record.module }}</a-tag>
                <strong>{{ record.compose }}</strong>
              </div>
              <div class="mono muted">远程 {{ record.remote }}</div>
            </div>
          </template>
          <template v-else-if="column.key === 'local'">
            <div class="mono wrap">{{ record.expectedRef }}</div>
            <div class="muted" v-if="record.image?.size">实际 {{ record.image.size }} · {{ record.image.shortId }}</div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusText(record.status) }}</a-tag>
            <div class="muted" v-if="!record.required">当前形态非必需</div>
          </template>
          <template v-else-if="column.key === 'containers'">
            <template v-if="record.containers.length">
              <div v-for="c in record.containers.slice(0, 3)" :key="c.id" class="ct">
                <i class="status-dot" :class="c.state === 'running' ? 'on' : 'off'" />
                <span>{{ c.name || c.id }}</span>
              </div>
              <div class="muted" v-if="record.containers.length > 3">+{{ record.containers.length - 3 }}</div>
            </template>
            <span class="muted" v-else>—</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <div class="ops">
              <a-button
                v-if="record.status === 'missing'"
                size="small"
                type="primary"
                ghost
                @click="emit('goto-build')"
              >
                去拉取
              </a-button>
              <a-button
                v-if="record.present && record.image"
                size="small"
                @click="openInspect(record)"
              >
                详情
              </a-button>
              <a-button
                v-if="record.present && record.image"
                size="small"
                danger
                @click="askRemove(record)"
              >
                删除
              </a-button>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <div class="panel other-panel" v-if="othersFiltered.length">
      <div class="panel-hd">
        <h2>其他本机镜像（非 EasyAIoT 目录）</h2>
        <span class="muted">{{ othersFiltered.length }} 个</span>
      </div>
      <a-table
        row-key="rowKey"
        size="small"
        :columns="otherColumns"
        :data-source="othersFiltered"
        :pagination="{ pageSize: 8, showTotal: (t: number) => `共 ${t} 个` }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'ref'">
            <div class="mono wrap">{{ record.ref }}</div>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button size="small" danger @click="askRemoveOther(record)">删除</a-button>
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
      :danger="true"
      :loading="confirmLoading"
      @confirm="doConfirm"
    />

    <a-drawer
      class="image-drawer"
      :open="inspectOpen"
      :width="Math.min(Math.floor(windowWidth * 0.56), 720)"
      placement="right"
      destroy-on-close
      :body-style="{ padding: 0, display: 'flex', flexDirection: 'column', height: '100%' }"
      @close="inspectOpen = false"
    >
      <template #title>
        <div class="drawer-title">
          <span>镜像详情</span>
          <a-tag v-if="inspectRecord" :color="statusColor(inspectRecord.status)">
            {{ statusText(inspectRecord.status) }}
          </a-tag>
        </div>
      </template>
      <template #extra>
        <a-space :size="8">
          <a-button size="small" :loading="inspectLoading" @click="refreshInspect">刷新</a-button>
          <a-button size="small" :disabled="!inspectCopyText" @click="copyInspect">复制</a-button>
        </a-space>
      </template>

      <div class="drawer-body" v-if="inspectRecord">
        <div class="drawer-hero">
          <div class="hero-name">{{ inspectRecord.compose }}</div>
          <div class="hero-ref mono">{{ inspectRecord.expectedRef }}</div>
          <div class="hero-tags">
            <a-tag>{{ inspectRecord.module }}</a-tag>
            <a-tag v-if="inspectRecord.image?.size" color="processing">{{ inspectRecord.image.size }}</a-tag>
            <a-tag v-if="inspectRecord.runningContainers">运行中 {{ inspectRecord.runningContainers }}</a-tag>
          </div>
        </div>

        <div class="drawer-facts">
          <div class="fact" v-for="m in inspectMeta" :key="m.label">
            <span>{{ m.label }}</span>
            <b class="mono">{{ m.value }}</b>
          </div>
        </div>

        <div class="drawer-section" v-if="inspectRecord.containers.length">
          <div class="section-hd">关联容器</div>
          <div class="ct-list">
            <div v-for="c in inspectRecord.containers" :key="c.id" class="ct-row">
              <i class="status-dot" :class="c.state === 'running' ? 'on' : 'off'" />
              <div class="ct-info">
                <div>{{ c.name || c.id }}</div>
                <div class="muted mono">{{ c.status || c.state }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="drawer-section grow">
          <div class="section-hd">
            <span>Inspect</span>
            <span class="muted">docker image inspect</span>
          </div>
          <a-spin :spinning="inspectLoading" class="inspect-spin">
            <div class="inspect-keys" v-if="inspectHighlights.length">
              <div v-for="h in inspectHighlights" :key="h.label" class="ikey">
                <span>{{ h.label }}</span>
                <b class="mono">{{ h.value }}</b>
              </div>
            </div>
            <pre class="logs viewer drawer-json">{{ inspectText || '暂无内容' }}</pre>
          </a-spin>
        </div>

        <div class="drawer-actions">
          <a-button block @click="emit('goto-build')" v-if="inspectRecord.status === 'missing'">去拉取此镜像</a-button>
          <a-button
            v-if="inspectRecord.present && inspectRecord.image"
            block
            danger
            @click="askRemove(inspectRecord)"
          >
            删除此镜像
          </a-button>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import {
  getImageCatalog,
  getProfile,
  inspectImage,
  pruneImages,
  removeImage,
  type ImageCatalogItem,
  type PanelImage,
} from '../api'

withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })
const emit = defineEmits<{ 'goto-build': []; goto: [key: string] }>()

type Row = ImageCatalogItem & { rowKey: string }
type OtherRow = PanelImage & { rowKey: string }

const loading = ref(false)
const profile = ref('full')
const items = ref<Row[]>([])
const others = ref<OtherRow[]>([])
const summary = ref({
  required: 0,
  ready: 0,
  missing: 0,
  optionalMissing: 0,
  otherImages: 0,
  totalLocalImages: 0,
  dangling: 0,
})
const keyword = ref('')
const scope = ref<'required' | 'missing' | 'all'>('required')
const moduleFilter = ref<string | undefined>()

const confirmOpen = ref(false)
const confirmLoading = ref(false)
const confirmTitle = ref('')
const confirmDesc = ref('')
const confirmWarn = ref('')
const confirmOk = ref('确认')
const confirmRows = ref<{ label: string; value: string }[]>([])
let pending:
  | { type: 'remove'; ref: string; force: boolean }
  | { type: 'prune' }
  | null = null

const inspectOpen = ref(false)
const inspectLoading = ref(false)
const inspectText = ref('')
const inspectMeta = ref<{ label: string; value: string }[]>([])
const inspectHighlights = ref<{ label: string; value: string }[]>([])
const inspectRecord = ref<Row | null>(null)
const inspectRef = ref('')
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const readyPercent = computed(() => {
  const total = summary.value.required || 0
  if (!total) return 0
  return Math.min(100, Math.round((summary.value.ready / total) * 100))
})

const inspectCopyText = computed(() => inspectText.value || inspectRecord.value?.expectedRef || '')

const columns = [
  { title: '服务', key: 'service', width: 240 },
  { title: '期望本地镜像', key: 'local', width: 280 },
  { title: '状态', key: 'status', width: 120 },
  { title: '关联容器', key: 'containers', width: 200 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' as const },
]

const otherColumns = [
  { title: '镜像', key: 'ref' },
  { title: '大小', dataIndex: 'size', key: 'size', width: 120 },
  { title: '操作', key: 'action', width: 100 },
]

const moduleOptions = computed(() =>
  [...new Set(items.value.map((i) => i.module))].map((m) => ({ value: m, label: m })),
)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value.filter((row) => {
    if (scope.value === 'required' && !row.required) return false
    if (scope.value === 'missing' && row.status !== 'missing') return false
    if (moduleFilter.value && row.module !== moduleFilter.value) return false
    if (!kw) return true
    return [row.module, row.compose, row.local, row.remote, row.expectedRef]
      .some((x) => (x || '').toLowerCase().includes(kw))
  })
})

const othersFiltered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return others.value
  return others.value.filter((o) =>
    [o.ref, o.repository, o.tag, o.shortId].some((x) => (x || '').toLowerCase().includes(kw)),
  )
})

function statusText(s: string) {
  if (s === 'ready' || s === 'optional_ready') return '已就绪'
  if (s === 'missing') return '缺失'
  if (s === 'optional_missing') return '未安装'
  return s
}
function statusColor(s: string) {
  if (s === 'ready' || s === 'optional_ready') return 'success'
  if (s === 'missing') return 'error'
  return 'default'
}

async function reload() {
  loading.value = true
  try {
    const data = await getImageCatalog(profile.value)
    items.value = (data.items || []).map((it, idx) => ({
      ...it,
      rowKey: `${it.module}-${it.local}-${idx}`,
    }))
    others.value = (data.others || []).map((img, idx) => ({
      ...img,
      rowKey: `other-${img.id || img.ref}-${idx}`,
    }))
    summary.value = {
      required: data.summary?.required || 0,
      ready: data.summary?.ready || 0,
      missing: data.summary?.missing || 0,
      optionalMissing: data.summary?.optionalMissing || 0,
      otherImages: data.summary?.otherImages || 0,
      totalLocalImages: data.summary?.totalLocalImages || 0,
      dangling: data.summary?.dangling || 0,
    }
  } catch {
    items.value = []
    others.value = []
  } finally {
    loading.value = false
  }
}

function askRemove(record: Row) {
  const img = record.image
  if (!img) return
  const target = img.id || img.ref
  pending = { type: 'remove', ref: target, force: false }
  confirmTitle.value = '删除项目镜像'
  confirmDesc.value = '删除后需重新拉取/构建才能部署对应服务。'
  confirmWarn.value =
    record.runningContainers > 0
      ? `当前有 ${record.runningContainers} 个容器正在使用该镜像，删除可能失败。`
      : '请确认该镜像暂不被业务依赖。'
  confirmOk.value = '确认删除'
  confirmRows.value = [
    { label: '模块', value: record.module },
    { label: '服务', value: record.compose },
    { label: '镜像', value: record.expectedRef },
    { label: 'ID', value: img.shortId || img.id },
  ]
  confirmOpen.value = true
}

function askRemoveOther(record: OtherRow) {
  pending = { type: 'remove', ref: record.id || record.ref, force: false }
  confirmTitle.value = '删除本机镜像'
  confirmDesc.value = '将从本机 Docker 删除该镜像。'
  confirmWarn.value = '若仍被容器引用会失败。'
  confirmOk.value = '确认删除'
  confirmRows.value = [
    { label: '镜像', value: record.ref },
    { label: '大小', value: record.size || '—' },
  ]
  confirmOpen.value = true
}

function askPrune() {
  pending = { type: 'prune' }
  confirmTitle.value = '清理悬空镜像'
  confirmDesc.value = '删除无仓库名/Tag 的悬空镜像，释放磁盘。'
  confirmWarn.value = '不会删除已命名或仍被容器引用的镜像。'
  confirmOk.value = '确认清理'
  confirmRows.value = [{ label: '悬空数量', value: String(summary.value.dangling) }]
  confirmOpen.value = true
}

async function doConfirm() {
  if (!pending) return
  confirmLoading.value = true
  try {
    if (pending.type === 'prune') {
      await pruneImages(true)
      message.success('已清理悬空镜像')
    } else {
      try {
        await removeImage(pending.ref, pending.force)
        message.success('已删除')
      } catch (e: any) {
        if (!pending.force) {
          confirmWarn.value = e?.message || '普通删除失败，可强制删除。'
          confirmOk.value = '强制删除'
          pending = { ...pending, force: true }
          confirmLoading.value = false
          return
        }
        throw e
      }
    }
    confirmOpen.value = false
    pending = null
    await reload()
  } catch {
    /* */
  } finally {
    confirmLoading.value = false
  }
}

async function openInspect(record: Row) {
  const img = record.image
  if (!img) return
  inspectRecord.value = record
  inspectRef.value = img.id || img.ref
  inspectMeta.value = [
    { label: '模块', value: record.module },
    { label: '服务', value: record.compose },
    { label: '远程名', value: record.remote },
    { label: '期望引用', value: record.expectedRef },
    { label: '实际引用', value: img.ref || '—' },
    { label: '镜像 ID', value: img.shortId || img.id || '—' },
    { label: '大小', value: img.size || '—' },
    { label: '创建', value: img.createdAt || img.createdSince || '—' },
  ]
  inspectOpen.value = true
  await refreshInspect()
}

async function refreshInspect() {
  if (!inspectRef.value) return
  inspectLoading.value = true
  try {
    const data = await inspectImage(inspectRef.value)
    inspectText.value = JSON.stringify(data.inspect || {}, null, 2)
    const raw = data.inspect || {}
    const tags = Array.isArray(raw.RepoTags) ? raw.RepoTags.join(', ') : '—'
    inspectHighlights.value = [
      { label: 'Architecture', value: raw.Architecture || '—' },
      { label: 'Os', value: raw.Os || '—' },
      { label: 'Created', value: raw.Created || '—' },
      { label: 'RepoTags', value: tags || '—' },
      { label: 'Docker Size', value: raw.Size != null ? formatBytes(Number(raw.Size)) : '—' },
    ]
  } catch {
    inspectText.value = '读取失败'
    inspectHighlights.value = []
  } finally {
    inspectLoading.value = false
  }
}

function formatBytes(n: number) {
  if (!n || Number.isNaN(n)) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = n
  let i = 0
  while (v >= 1024 && i < u.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(i ? 1 : 0)} ${u[i]}`
}

async function copyInspect() {
  const text = inspectCopyText.value
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

function onResize() {
  windowWidth.value = window.innerWidth
}

onMounted(async () => {
  try {
    const p = await getProfile()
    if (p?.profile) profile.value = String(p.profile)
  } catch {
    /* */
  }
  await reload()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => window.removeEventListener('resize', onResize))

watch(profile, () => {
  reload()
})
</script>

<style scoped>
.embed-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.embed-meta {
  font-size: 13px;
  color: var(--c-text-2);
}

.embed-meta code {
  font-size: 12px;
  color: var(--c-primary);
  background: var(--c-primary-bg);
  padding: 1px 6px;
  border-radius: 4px;
}

.summary-board {
  display: grid;
  grid-template-columns: minmax(200px, 0.9fr) minmax(0, 2.1fr);
  gap: 0;
  margin-bottom: 14px;
  border: 1px solid var(--c-border);
  border-radius: 10px;
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 55%, #ffffff 100%);
  overflow: hidden;
}

.summary-main {
  padding: 12px 16px;
  border-right: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.summary-label {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 1;
}

.summary-ratio {
  display: flex;
  align-items: baseline;
  gap: 4px;
  line-height: 1;
}

.ratio-num {
  font-size: 26px;
  font-weight: 650;
  color: var(--c-text);
  letter-spacing: -0.02em;
}

.ratio-sep {
  font-size: 16px;
  color: var(--c-text-3);
}

.ratio-den {
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text-2);
}

.summary-meter .meter-track {
  height: 5px;
  border-radius: 999px;
  background: #eef2f7;
  overflow: hidden;
}

.summary-meter .meter-track > i {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #69b1ff, #1677ff);
}

.meter-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--c-text-3);
  font-weight: 500;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric {
  border: 0;
  border-left: 1px solid var(--c-border);
  background: transparent;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}

.metric:first-child {
  border-left: 0;
}

.metric:hover {
  background: rgba(22, 119, 255, 0.04);
}

.metric.alert {
  background: #fff8f7;
}

.metric-k {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 1;
}

.metric-v {
  font-size: 22px;
  font-weight: 650;
  line-height: 1;
  color: var(--c-text);
  letter-spacing: -0.02em;
}

.metric-v.ok {
  color: var(--c-success);
}

.metric-v.danger {
  color: var(--c-danger);
}

.toolbar-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.toolbar-spacer {
  flex: 1;
}

.svc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.wrap {
  word-break: break-all;
}

.ct {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  line-height: 20px;
}

.ops {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ops :deep(.ant-btn) {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
}

.other-panel {
  margin-top: 16px;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.drawer-body {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 0;
}

.drawer-hero {
  padding: 20px 24px 18px;
  background: linear-gradient(180deg, #f7faff 0%, #fff 100%);
  border-bottom: 1px solid var(--c-border);
}

.hero-name {
  font-size: 22px;
  font-weight: 650;
  line-height: 30px;
  margin-bottom: 6px;
}

.hero-ref {
  font-size: 13px;
  color: var(--c-text-2);
  word-break: break-all;
  margin-bottom: 12px;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.drawer-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  border-bottom: 1px solid var(--c-border);
}

.fact {
  padding: 14px 24px;
  border-bottom: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.fact:nth-child(odd) {
  border-right: 1px solid var(--c-border);
}

.fact span {
  font-size: 12px;
  color: var(--c-text-3);
}

.fact b {
  font-size: 13px;
  font-weight: 500;
  word-break: break-all;
  color: var(--c-text);
}

.drawer-section {
  padding: 16px 24px;
}

.drawer-section.grow {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.section-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
}

.ct-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ct-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  background: var(--c-fill);
}

.ct-info {
  min-width: 0;
  font-size: 13px;
}

.inspect-spin {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.inspect-spin :deep(.ant-spin-container) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.inspect-keys {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.ikey {
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--c-fill);
  border: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.ikey span {
  font-size: 11px;
  color: var(--c-text-3);
}

.ikey b {
  font-size: 12px;
  font-weight: 500;
  word-break: break-all;
}

.drawer-json {
  margin: 0;
  flex: 1;
  min-height: 220px;
  max-height: 42vh;
  border-radius: 8px;
}

.drawer-actions {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--c-border);
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

:deep(.ant-table-pagination) {
  margin: 12px 16px !important;
}

code {
  font-size: 12px;
  color: var(--c-primary);
  background: var(--c-primary-bg);
  padding: 1px 6px;
  border-radius: 4px;
}

@media (max-width: 1100px) {
  .summary-board {
    grid-template-columns: 1fr;
  }
  .summary-main {
    border-right: 0;
    border-bottom: 1px solid var(--c-border);
  }
  .summary-metrics {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
