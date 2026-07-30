<template>
  <a-config-provider
    :theme="{
      token: {
        colorPrimary: '#1677ff',
        colorBgBase: '#ffffff',
        colorBgContainer: '#ffffff',
        colorBorder: '#f0f0f0',
        colorBorderSecondary: '#f0f0f0',
        borderRadius: 6,
        fontSize: 14,
        controlHeight: 32,
        fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif`,
      },
    }"
  >
    <div class="layout">
      <aside class="sidebar">
        <div class="brand">
          <img class="logo" src="/logo.png" alt="EasyAIoT" />
          <div class="brand-meta">
            <div class="brand-name">EasyAIoT PANEL</div>
            <div class="brand-sub">容器运维控制台</div>
          </div>
        </div>

        <nav class="menu">
          <button
            v-for="item in menus"
            :key="item.key"
            type="button"
            class="menu-item"
            :class="{ active: tab === item.key }"
            @click="tab = item.key"
          >
            <span class="menu-ico" v-html="item.icon" />
            <span class="menu-title">{{ item.label }}</span>
          </button>
        </nav>

        <div class="side-foot">
          <div class="agent-line">
            <i class="status-dot" :class="online ? 'on' : 'off'" />
            <span>{{ online ? 'Agent 在线' : 'Agent 离线' }} · :9200</span>
          </div>
          <div class="build-line">UI {{ uiBuild }} · 菜单 {{ menus.length }}</div>
          <a-button block size="small" @click="tokenOpen = true">访问令牌</a-button>
        </div>
      </aside>

      <section class="workspace">
        <header class="topbar">
          <div class="topbar-title">{{ current?.label }}</div>
          <div class="topbar-right">
            <span class="clock">{{ clock }}</span>
            <a-button size="small" @click="ping">检测连接</a-button>
          </div>
        </header>
        <main class="content" :class="{ 'content-fill': isStackTab }">
          <OverviewView
            v-if="tab === 'overview'"
            @goto="tab = $event"
            @open-platform="openWeb"
          />
          <ContainersView v-else-if="tab === 'containers'" />
          <DeployView v-else-if="tab === 'deploy'" />
          <ImagesView v-else-if="tab === 'images'" />
          <DiagnoseView v-else-if="tab === 'diagnose'" />
          <MaintainView v-else-if="tab === 'maintain'" />
          <TopologyView v-else-if="tab === 'topology'" />
        </main>
      </section>

      <a-modal
        v-model:open="tokenOpen"
        title="访问令牌"
        :width="480"
        ok-text="保存"
        cancel-text="取消"
        centered
        @ok="saveToken"
      >
        <p class="token-tip">仅当服务端配置了 PANEL_TOKEN 时需要填写。</p>
        <a-input v-model:value="token" placeholder="PANEL_TOKEN" allow-clear />
      </a-modal>

      <ConfirmDialog
        v-model:open="webOpen"
        :title="webDialogTitle"
        :description="webDialogDesc"
        :warning="webDialogWarn"
        :rows="webDialogRows"
        ok-text="仍要访问"
        cancel-text="取消"
        secondary-text="前往部署"
        @confirm="confirmOpenWeb"
        @secondary="goDeployFromWebDialog"
      />
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import axios from 'axios'
import { getLinks } from './api'
import ConfirmDialog from './components/ConfirmDialog.vue'
import OverviewView from './views/OverviewView.vue'
import ContainersView from './views/ContainersView.vue'
import TopologyView from './views/TopologyView.vue'
import DeployView from './views/DeployView.vue'
import ImagesView from './views/ImagesView.vue'
import DiagnoseView from './views/DiagnoseView.vue'
import MaintainView from './views/MaintainView.vue'

const tab = ref('overview')
const token = ref(localStorage.getItem('panel_token') || '')
const tokenOpen = ref(false)
const online = ref(false)
const clock = ref('')
const webUrl = ref('')
const webRunning = ref(false)
const webStatus = ref<'running' | 'stopped' | 'missing' | string>('missing')
const webMessage = ref('')
const webContainer = ref('')
const webOpen = ref(false)
const uiBuild = '20260730-img-compact'
let timer: number | undefined
let clockTimer: number | undefined

function defaultWebUrl() {
  const host = window.location.hostname || '127.0.0.1'
  return `http://${host}:8888`
}

const resolvedWebUrl = computed(() => (webUrl.value || defaultWebUrl()).replace(/\/$/, ''))

const webStatusLabel = computed(() => {
  if (webStatus.value === 'running') return 'WEB 运行中'
  if (webStatus.value === 'stopped') return 'WEB 已停止'
  return 'WEB 未部署'
})

const webDialogTitle = computed(() =>
  webStatus.value === 'stopped' ? '平台未在运行' : '尚未检测到 EasyAIoT 平台',
)
const webDialogDesc = computed(
  () =>
    webMessage.value ||
    '当前未检测到可用的 WEB 管控台。可先完成部署，或仍尝试打开配置的地址。',
)
const webDialogWarn = computed(() =>
  webStatus.value === 'stopped'
    ? '容器已存在但未启动，直接打开页面可能会打不开。'
    : '平台可能尚未安装，直接打开页面可能会打不开。',
)
const webDialogRows = computed(() => {
  const rows = [
    { label: '目标地址', value: resolvedWebUrl.value },
    { label: 'WEB 状态', value: webStatusLabel.value },
  ]
  if (webContainer.value) rows.push({ label: '容器', value: webContainer.value })
  return rows
})

function jumpWeb() {
  window.open(resolvedWebUrl.value, '_blank', 'noopener,noreferrer')
}

async function openWeb() {
  await refreshLinks()
  if (webRunning.value) {
    jumpWeb()
    return
  }
  webOpen.value = true
}

function confirmOpenWeb() {
  webOpen.value = false
  jumpWeb()
}

function goDeployFromWebDialog() {
  webOpen.value = false
  tab.value = 'deploy'
}

async function refreshLinks() {
  try {
    const data = await getLinks()
    webUrl.value = data?.web?.url || defaultWebUrl()
    webRunning.value = !!data?.web?.running
    webStatus.value = data?.web?.status || (webRunning.value ? 'running' : 'missing')
    webMessage.value = data?.web?.message || ''
    webContainer.value = data?.web?.container || ''
  } catch {
    webUrl.value = defaultWebUrl()
    webRunning.value = false
    webStatus.value = 'missing'
    webMessage.value = '无法检测 WEB 状态，平台可能尚未部署。'
    webContainer.value = ''
  }
}

const ico = {
  home: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z"/></svg>`,
  box: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/></svg>`,
  deploy: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 19h14"/></svg>`,
  image: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="m21 16-5.5-5.5L8 18"/></svg>`,
  diagnose: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/><path d="M11 8.5v5M8.5 11h5"/></svg>`,
  maintain: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M14.5 4.5 19 9l-8.5 8.5H6v-4.5L14.5 4.5z"/><path d="m12.5 6.5 5 5"/><path d="M4 20h16"/></svg>`,
  topo: `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8.2 7.5 10.5 15M15.8 7.5 13.5 15M8.5 6h7"/></svg>`,
}

const menus = [
  { key: 'overview', label: '系统概览', icon: ico.home },
  { key: 'containers', label: '容器管理', icon: ico.box },
  { key: 'deploy', label: '应用部署', icon: ico.deploy },
  { key: 'images', label: '镜像中心', icon: ico.image },
  { key: 'diagnose', label: '系统诊断', icon: ico.diagnose },
  { key: 'maintain', label: '系统维护', icon: ico.maintain },
  { key: 'topology', label: '服务拓扑', icon: ico.topo },
]

const current = computed(() => menus.find((m) => m.key === tab.value))
const isStackTab = computed(() =>
  ['deploy', 'images', 'diagnose', 'maintain'].includes(tab.value),
)

function saveToken() {
  if (token.value) localStorage.setItem('panel_token', token.value)
  else localStorage.removeItem('panel_token')
  tokenOpen.value = false
  message.success('已保存')
}

async function ping() {
  try {
    await axios.get('/health', { timeout: 4000 })
    online.value = true
    message.success('连接正常')
  } catch {
    online.value = false
    message.error('Agent 离线')
  }
}

onMounted(() => {
  axios.get('/health', { timeout: 4000 }).then(() => { online.value = true }).catch(() => { online.value = false })
  refreshLinks()
  const tick = () => {
    clock.value = new Date().toLocaleString('zh-CN', { hour12: false })
  }
  tick()
  clockTimer = window.setInterval(tick, 1000)
  timer = window.setInterval(() => {
    axios.get('/health', { timeout: 4000 }).then(() => { online.value = true }).catch(() => { online.value = false })
    refreshLinks()
  }, 10000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  if (clockTimer) window.clearInterval(clockTimer)
})
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--c-white);
}

.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  border-right: 1px solid var(--c-border);
  background: var(--c-white);
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.brand {
  min-height: var(--header-h);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--c-border);
}

.logo {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  object-fit: contain;
}

.brand-meta {
  min-width: 0;
}

.brand-name {
  font-size: 15px;
  font-weight: 650;
  line-height: 22px;
}

.brand-sub {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 18px;
  margin-top: 2px;
}

.menu {
  flex: 1;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
  border: 0;
  background: transparent;
  border-radius: 10px;
  padding: 14px 14px;
  cursor: pointer;
  text-align: left;
  color: var(--c-text-2);
  white-space: nowrap;
}

.menu-item:hover {
  background: var(--c-fill);
  color: var(--c-text);
}

.menu-item.active {
  background: var(--c-primary-bg);
  color: var(--c-primary);
}

.menu-ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  background: var(--c-fill);
  color: inherit;
}

.menu-item.active .menu-ico {
  background: #fff;
  color: var(--c-primary);
}

.menu-title {
  font-size: 15px;
  font-weight: 550;
  line-height: 24px;
  letter-spacing: 0.04em;
}

.side-foot {
  border-top: 1px solid var(--c-border);
  padding: 16px 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-line,
.build-line {
  font-size: 12px;
  color: var(--c-text-3);
  line-height: 18px;
  white-space: normal;
  word-break: break-word;
}

.agent-line {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--c-text-2);
}

.workspace {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--c-white);
}

.topbar {
  height: var(--header-h);
  border-bottom: 1px solid var(--c-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-lg);
  background: var(--c-white);
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.clock {
  font-size: 12px;
  color: var(--c-text-3);
  font-variant-numeric: tabular-nums;
}

.content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: var(--c-white);
}

.content-fill {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-fill > * {
  flex: 1;
  min-height: 0;
}

.token-tip {
  margin: 0 0 12px;
  color: var(--c-text-2);
  font-size: 13px;
}
</style>
