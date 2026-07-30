<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>系统概览</h1>
        <p>主机资源、容器健康与部署形态</p>
      </div>
      <a-space :size="8" class="head-actions">
        <a-button
          type="primary"
          :ghost="webNotReady"
          class="head-btn"
          @click="emit('open-platform')"
        >
          {{ webNotReady ? '管控台未运行' : '进入管控台' }}
        </a-button>
        <a-button class="head-btn" :loading="loading" @click="reload">刷新</a-button>
      </a-space>
    </div>

    <a-alert
      v-if="error"
      type="warning"
      show-icon
      :message="error"
      style="margin-bottom: 16px"
    />

    <a-alert
      v-if="!error && deployUnsupported"
      type="info"
      show-icon
      style="margin-bottom: 16px"
      :message="`${platformLabel} 环境：一键部署不可用`"
      :description="deployUnsupportedDesc"
    />

    <div class="metric-grid">
      <div class="metric" v-for="m in metrics" :key="m.label">
        <div class="metric-label">{{ m.label }}</div>
        <div class="metric-value" :class="m.tone">{{ m.value }}</div>
        <div class="meter" :class="m.meterClass" v-if="m.percent != null">
          <i :style="{ width: `${Math.min(m.percent, 100)}%` }" />
        </div>
        <div class="metric-sub">{{ m.sub }}</div>
      </div>
    </div>

    <div class="main-grid">
      <div class="panel">
        <div class="panel-hd">
          <h2>当前部署</h2>
          <a-space :size="8" class="panel-actions">
            <a-button
              size="small"
              class="panel-btn"
              :disabled="deployUnsupported"
              @click="emit('goto', 'deploy')"
            >
              {{ deployUnsupported ? '部署不可用' : '前往部署' }}
            </a-button>
            <a-button size="small" class="panel-btn" @click="emit('goto', 'topology')">查看拓扑</a-button>
          </a-space>
        </div>
        <div class="panel-bd">
          <div class="profile">
            <span class="badge">{{ (overview?.profile?.profile || '—').toUpperCase() }}</span>
            <span class="muted">{{ overview?.profile?.description || '尚未读取' }}</span>
          </div>
          <div class="entry-grid">
            <button type="button" class="entry" @click="emit('goto', 'containers')">
              <strong>容器管理</strong>
              <span>启停 · 资源 · 日志</span>
            </button>
            <button type="button" class="entry" @click="emit('goto', 'deploy')">
              <strong>应用部署</strong>
              <span>安装 · 启停 · 更新</span>
            </button>
            <button type="button" class="entry" @click="emit('goto', 'images')">
              <strong>镜像中心</strong>
              <span>本地管理 · 构建拉取</span>
            </button>
            <button type="button" class="entry" @click="emit('goto', 'diagnose')">
              <strong>系统诊断</strong>
              <span>检查 · 状态 · 分析</span>
            </button>
            <button type="button" class="entry" @click="emit('goto', 'maintain')">
              <strong>系统维护</strong>
              <span>清理 · 进程管控</span>
            </button>
            <button type="button" class="entry" @click="emit('goto', 'topology')">
              <strong>服务拓扑</strong>
              <span>调用关系全景</span>
            </button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hd"><h2>主机与 Docker</h2></div>
        <div class="panel-bd info-list">
          <div class="info-row" v-for="row in infoRows" :key="row.k">
            <span>{{ row.k }}</span>
            <b>{{ row.v }}</b>
          </div>
          <div class="info-row" v-if="overview?.projects?.length">
            <span>Compose</span>
            <b>{{ overview.projects.join(' · ') }}</b>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getOverview, type PanelOverview } from '../api'

const emit = defineEmits<{ goto: [key: string]; 'open-platform': [] }>()
const overview = ref<PanelOverview | null>(null)
const loading = ref(false)
const error = ref('')
let timer: number | undefined

const deployUnsupported = computed(() => {
  const p = overview.value?.panel
  if (!p) return false
  if (typeof p.deploySupported === 'boolean') return !p.deploySupported
  return p.platform?.deploySupported === false
})
const platformLabel = computed(() => overview.value?.panel?.platform?.label || '当前系统')
const deployUnsupportedDesc = computed(
  () =>
    overview.value?.panel?.platform?.message ||
    overview.value?.panel?.platform?.hint ||
    '当前环境无法执行一键部署，请检查 Docker 与 INSTALL_SCRIPT / EASYAIOT_ROOT。',
)

const webInfo = computed(() => overview.value?.panel?.web)
const webNotReady = computed(() => !!overview.value && !webInfo.value?.running)

function fmtBytes(n?: number) {
  if (n == null) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = n
  let i = 0
  while (v >= 1024 && i < u.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(i ? 1 : 0)} ${u[i]}`
}

function meterClass(p?: number) {
  if (p == null) return ''
  if (p >= 90) return 'danger'
  if (p >= 75) return 'warn'
  return 'ok'
}

const metrics = computed(() => {
  const o = overview.value
  const cpu = Number(o?.host?.cpuPercent || 0)
  const mem = Number(o?.host?.memPercent || 0)
  const disk = Number(o?.host?.diskPercent || 0)
  return [
    {
      label: '运行中容器',
      value: String(o?.containers?.running ?? '—'),
      sub: `全部 ${o?.containers?.total ?? 0} · 停止 ${o?.containers?.stopped ?? 0}`,
      tone: 'tone-ok',
      percent: o?.containers?.total ? (o.containers.running / o.containers.total) * 100 : null,
      meterClass: 'ok',
    },
    {
      label: 'CPU',
      value: o ? `${cpu.toFixed(1)}%` : '—',
      sub: `${o?.host?.cpuCount ?? '—'} 核`,
      tone: '',
      percent: o ? cpu : null,
      meterClass: meterClass(cpu),
    },
    {
      label: '内存',
      value: o ? `${mem.toFixed(1)}%` : '—',
      sub: o ? `${fmtBytes(o.host?.memUsed)} / ${fmtBytes(o.host?.memTotal)}` : '—',
      tone: '',
      percent: o ? mem : null,
      meterClass: meterClass(mem),
    },
    {
      label: '磁盘',
      value: o ? `${disk.toFixed(1)}%` : '—',
      sub: o ? `${fmtBytes(o.host?.diskUsed)} / ${fmtBytes(o.host?.diskTotal)}` : '—',
      tone: '',
      percent: o ? disk : null,
      meterClass: meterClass(disk),
    },
  ]
})

const infoRows = computed(() => {
  const h = overview.value?.host
  const d = overview.value?.docker
  const p = overview.value?.panel
  const rows = [
    { k: '主机', v: h?.hostname || '—' },
    { k: '系统', v: h ? `${h.system || ''} ${h.release || ''}`.trim() : '—' },
    { k: '架构', v: h?.machine || '—' },
    {
      k: '一键部署',
      v: deployUnsupported.value
        ? `不可用（${platformLabel.value}）`
        : `可用（${platformLabel.value} / ${overview.value?.panel?.platform?.scriptName || 'install_*.sh'}）`,
    },
  ]
  if (!d?.available) {
    rows.push({ k: 'Docker', v: d?.error || '不可用' })
  } else {
    rows.push(
      { k: 'Docker', v: d.serverVersion || '—' },
      { k: '镜像', v: String(d.images ?? '—') },
      { k: '容器', v: `${d.containersRunning ?? '—'} / ${d.containers ?? '—'}` },
      { k: '存储', v: d.driver || '—' },
    )
  }
  if (p?.listen) rows.push({ k: 'PANEL', v: String(p.listen) })
  return rows
})

async function reload() {
  loading.value = true
  error.value = ''
  try {
    overview.value = await getOverview()
  } catch (e: any) {
    error.value = e?.message || 'API 不可用'
    overview.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  reload()
  timer = window.setInterval(reload, 15000)
})
onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.metric {
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 20px;
  background: var(--c-white);
  min-height: 128px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-label {
  font-size: 13px;
  color: var(--c-text-3);
  line-height: 20px;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 36px;
  color: var(--c-text);
}

.metric-value.tone-ok {
  color: var(--c-success);
}

.metric-sub {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 20px;
  margin-top: auto;
}

.main-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: stretch;
}

.profile {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  min-height: 32px;
}

.badge {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  background: var(--c-primary-bg);
  color: var(--c-primary);
  font-weight: 600;
  font-size: 14px;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.entry {
  border: 1px solid var(--c-border);
  background: var(--c-white);
  border-radius: var(--radius);
  padding: 16px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 92px;
}

.entry:hover {
  border-color: var(--c-primary-border);
  background: var(--c-primary-bg);
}

.entry strong {
  font-size: 14px;
  color: var(--c-text);
}

.entry span {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 18px;
}

.info-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 12px;
  align-items: start;
  padding: 12px 0;
  border-bottom: 1px solid var(--c-border);
  font-size: 13px;
}

.info-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.info-row:first-child {
  padding-top: 0;
}

.info-row span {
  color: var(--c-text-3);
}

.info-row b {
  font-weight: 500;
  color: var(--c-text);
  word-break: break-all;
  text-align: right;
}

@media (max-width: 1100px) {
  .metric-grid,
  .main-grid,
  .entry-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .metric-grid,
  .main-grid,
  .entry-grid {
    grid-template-columns: 1fr;
  }
}

.head-actions :deep(.ant-btn.head-btn) {
  min-width: 112px;
  height: 32px !important;
  padding: 0 14px !important;
  font-size: 13px !important;
  font-weight: 500;
  border-radius: 6px;
  line-height: 30px !important;
}

.panel-actions :deep(.ant-btn.panel-btn) {
  min-width: 88px;
  height: 28px !important;
  padding: 0 12px !important;
  font-size: 12px !important;
  font-weight: 500;
  border-radius: 6px;
}

:deep(.panel-hd) {
  height: 52px;
  padding: 0 20px;
}
:deep(.panel-bd) {
  padding: 20px;
}
</style>
