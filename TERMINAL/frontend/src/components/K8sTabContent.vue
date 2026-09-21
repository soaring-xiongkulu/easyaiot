<template>
  <div class="db-tab-content">
    <div v-if="error" class="k8s-fatal">{{ error }}</div>
    <div v-else-if="!connId" class="k8s-connecting">Connecting…</div>
    <div v-else class="db-main">
      <div class="db-left" :style="{ width: leftWidth + 'px' }">
        <K8sTree :model-value="rootResourceKey" @update:model-value="selectResource" />
      </div>
      <div class="db-resizer" @mousedown="onResizeStart" />
      <div class="db-right">
        <K8sBreadcrumb
          :stack="navStack"
          :namespace="currentNamespace"
          :namespace-options="namespaceOptions"
          @pop="popTo"
          @update:namespace="setNamespace"
        />
        <div v-if="namespaceError" class="k8s-ns-warning" role="status">{{ namespaceError }}</div>
        <K8sResourceList
          :conn-id="connId"
          :frame="topFrame"
          :namespace-options="namespaceOptions"
          @open-detail="openDetail"
          @open-yaml="openYaml"
          @open-logs="openLogs"
          @view-pods="viewPods"
          @open-crd="openCrd"
          @open-terminal="openTerminal"
          @changed="() => {}"
        />
      </div>
    </div>

    <K8sDetailDrawer
      :conn-id="connId"
      :mode="drawerMode"
      :target="drawerTarget"
      :resource-key="drawerResourceKey"
      :self-path-override="drawerSelfPathOverride"
      :initial-tab="drawerInitialTab"
      @close="closeDrawer"
      @saved="() => {}"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import * as k8sClient from '../services/k8sClient'
import { usePanelStore } from '../stores/panelStore'
import { useTabStore } from '../stores/tabStore'
import { useSessionStore } from '../stores/sessionStore'
import { useK8sStore } from '../stores/k8sStore'
import { useTunnelCredentials } from '../composables/useTunnelCredentials'
import K8sTree from './K8sTree.vue'
import K8sResourceList from './K8sResourceList.vue'
import K8sBreadcrumb from './K8sBreadcrumb.vue'
import K8sDetailDrawer from './K8sDetailDrawer.vue'
import { parseCRD, crdListPath } from '../services/k8sCrd'
import type { K8sTab, NavFrame } from '../types/k8s'
import type { ConnectionConfig } from '../types/session'

const props = defineProps<{ tab: K8sTab; connection: ConnectionConfig }>()

const { resolveTunnelCredentials } = useTunnelCredentials()

const panelStore = usePanelStore()
const tabStore = useTabStore()
const sessionStore = useSessionStore()
const k8sStore = useK8sStore()

const connId = ref<string>('')
const error = ref('')
const initialNamespace = ref<string>(props.tab.namespace || '')

// Namespaces fetched live from the cluster once connected. If the list call
// fails (e.g. RBAC restricted to specific namespaces), keep only the context's
// default namespace so the dropdown still offers a valid target, and surface a
// non-fatal hint telling the user they can type a namespace manually.
const fetchedNamespaces = ref<string[]>([])
const namespaceError = ref('')
const namespaceOptions = computed(() => {
  const set = new Set<string>()
  for (const n of fetchedNamespaces.value) set.add(n)
  if (initialNamespace.value) set.add(initialNamespace.value)
  return Array.from(set).sort()
})

async function loadNamespaces() {
  if (!connId.value) return
  namespaceError.value = ''
  try {
    const { status, data } = await k8sClient.requestJSON<any>(connId.value, 'GET', '/api/v1/namespaces?limit=500')
    if (status === 200 && data?.items) {
      fetchedNamespaces.value = data.items.map((n: any) => n.metadata?.name).filter(Boolean).sort()
    } else {
      fetchedNamespaces.value = []
      namespaceError.value = `Failed to list namespaces (HTTP ${status}). You can type a namespace manually.`
    }
  } catch {
    fetchedNamespaces.value = []
    namespaceError.value = 'Failed to list namespaces — permission denied? You can type a namespace manually.'
  }
}

// ── nav stack ──────────────────────────────────────────────────
const navStack = ref<NavFrame[]>([{ kind: 'list', resourceKey: 'pods', namespace: props.tab.namespace || '' }])
const topFrame = computed(() => navStack.value[navStack.value.length - 1])
const rootResourceKey = computed(() => {
  const base = navStack.value[0]
  return base.kind === 'list' ? base.resourceKey : ''
})
const currentNamespace = computed(() => {
  const f = topFrame.value
  return f.kind === 'custom' ? f.namespace : (f as any).namespace || ''
})

function selectResource(key: string) {
  navStack.value = [{ kind: 'list', resourceKey: key, namespace: currentNamespace.value }]
}
function popTo(index: number) {
  navStack.value = navStack.value.slice(0, index + 1)
}
function setNamespace(ns: string) {
  const f = topFrame.value
  if (f.kind === 'list') navStack.value = [{ kind: 'list', resourceKey: f.resourceKey, namespace: ns }]
  else navStack.value = navStack.value.map((fr, i) => i === navStack.value.length - 1 ? { ...fr, namespace: ns } as NavFrame : fr)
}
function viewPods(owner: { kind: string; name: string; uid: string; namespace: string }) {
  navStack.value = [...navStack.value, {
    kind: 'owned', resourceKey: 'pods',
    ownerKind: owner.kind, ownerName: owner.name, ownerUid: owner.uid, namespace: owner.namespace,
  }]
}
function openCrd(crdObj: any) {
  const crd = parseCRD(crdObj)
  navStack.value = [...navStack.value, { kind: 'custom', crd, namespace: '' }]
}

// ── drawer ─────────────────────────────────────────────────────
const drawerMode = ref<'detail' | 'logs' | null>(null)
const drawerTarget = ref<any | null>(null)
const drawerResourceKey = ref<string>('pods')
const drawerSelfPathOverride = ref<((obj: any) => string) | undefined>(undefined)
const drawerInitialTab = ref<'detail' | 'yaml'>('detail')
function openDetail(obj: any) {
  drawerTarget.value = obj
  drawerResourceKey.value = resourceKeyOf()
  drawerSelfPathOverride.value = crSelfPathOverride()
  drawerInitialTab.value = 'detail'
  drawerMode.value = 'detail'
}
function openYaml(obj: any) {
  drawerTarget.value = obj
  drawerResourceKey.value = resourceKeyOf()
  drawerSelfPathOverride.value = crSelfPathOverride()
  drawerInitialTab.value = 'yaml'
  drawerMode.value = 'detail'
}
function openLogs(pod: any) { drawerTarget.value = pod; drawerResourceKey.value = 'pods'; drawerSelfPathOverride.value = undefined; drawerMode.value = 'logs' }
function closeDrawer() { drawerMode.value = null; drawerTarget.value = null }
function resourceKeyOf(): string {
  const f = topFrame.value
  if (f.kind === 'list') return f.resourceKey
  if (f.kind === 'owned') return f.resourceKey
  return 'customresourcedefinitions'
}
// CR 实例（custom frame）的 self-path 由 ParsedCRD 派生，避免落到 CRD 集合路径
function crSelfPathOverride(): ((obj: any) => string) | undefined {
  const f = topFrame.value
  if (f.kind !== 'custom') return undefined
  const crd = f.crd
  return (obj: any) => {
    const ns = obj.metadata?.namespace || f.namespace
    return crdListPath(crd, ns).split('?')[0] + '/' + encodeURIComponent(obj.metadata?.name)
  }
}
async function openTerminal(pod: any) {
  const containers = (pod.spec?.containers || []).map((c: any) => c.name)
  let container = containers[0]
  try {
    if (containers.length > 1) {
      const { value } = await ElMessageBox.prompt(
        `Container (${containers.join(', ')})`, 'Select container',
        { inputValue: containers[0], inputValidator: (v: string) => containers.includes(v) || 'unknown container' },
      )
      container = value
    }
    const ns = pod.metadata?.namespace
    const info = await k8sClient.execSession(connId.value, ns, pod.metadata?.name, container)
    const title = `${pod.metadata?.name}/${container}`
    // Store exec params on the config so Panel.vue can rebuild the stream on reconnect.
    const cfg = {
      id: '', name: title, type: 'k8s-exec' as any, host: '', port: 0, user: '', authType: 'password' as any,
      k8sExecConnId: connId.value, k8sNamespace: ns, k8sExecPod: pod.metadata?.name, k8sExecContainer: container,
    }
    const panel = panelStore.createPanel(cfg as any, 'k8s-exec')
    panelStore.updateTitle(panel.id, title)
    panelStore.bindSession(panel.id, info.id)
    sessionStore.initSession(info.id)
    // Exec socket is already connected when the binding returns; the backend only
    // emits session:status on later transitions (disconnect), so mark it now.
    sessionStore.updateStatus(info.id, 'connected')
    const tab = tabStore.createTerminalTab(panel.title, panel.id)
    panelStore.movePanelToTab(panel.id, tab.id)
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(String(e?.message || e))
  }
}

// 左侧宽度 + resizer（抄 DBTabContent）
const leftWidth = ref(220)
let resizeStartX = 0
let resizeStartWidth = 0
let resizing = false
function onResizeStart(e: MouseEvent) {
  resizeStartX = e.clientX
  resizeStartWidth = leftWidth.value
  resizing = true
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}
function onResizeMove(e: MouseEvent) {
  const dx = e.clientX - resizeStartX
  leftWidth.value = Math.max(150, Math.min(500, resizeStartWidth + dx))
}
function onResizeEnd() {
  resizing = false
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

async function connect() {
  k8sStore.setConnStatus(props.connection.id, 'connecting')
  try {
    const cfg = props.connection
    const source = cfg.k8sConfigInline ? cfg.k8sConfigInline : (cfg.k8sConfigPath || '~/.kube/config')
    const isPath = !cfg.k8sConfigInline
    let tunnelUser = ''
    let tunnelPassword = ''
    if (cfg.tunnelSSHConnId) {
      const creds = await resolveTunnelCredentials(cfg.tunnelSSHConnId)
      if (!creds) {
        error.value = 'Tunnel credentials cancelled'
        return
      }
      tunnelUser = creds.user
      tunnelPassword = creds.password
    }
    connId.value = await k8sClient.connect(
      source,
      isPath,
      cfg.k8sContext || '',
      cfg.tunnelSSHConnId || '',
      tunnelUser,
      tunnelPassword
    )
    k8sStore.setConnStatus(props.connection.id, 'connected')
    loadNamespaces()
  } catch (e: any) {
    k8sStore.setConnStatus(props.connection.id, 'error')
    error.value = String(e?.message || e)
  }
}

function onReconnectEvent(e: Event) {
  const panelId = (e as CustomEvent)?.detail?.panelId
  if (panelId && panelId === props.tab.panelId) reconnect()
}

// Force-reconnect: tear down the current cluster connection, then re-run the
// normal connect() (which already resets error state and re-resolves tunnel
// credentials on each call).
async function reconnect() {
  if (connId.value) {
    try { k8sClient.disconnect(connId.value) } catch (_) {}
    connId.value = ''
  }
  await connect()
}

onMounted(() => {
  connect()
  // Tab right-click 「重连」(Reconnect) menu → forced reconnect of this tab.
  window.addEventListener('panel:reconnect', onReconnectEvent)
})
onBeforeUnmount(() => {
  window.removeEventListener('panel:reconnect', onReconnectEvent)
  if (resizing) {
    document.removeEventListener('mousemove', onResizeMove)
    document.removeEventListener('mouseup', onResizeEnd)
  }
  if (connId.value) {
    // K8sResourceList 内部 onBeforeUnmount 已经 unsubscribe 当前订阅。
    k8sClient.disconnect(connId.value)
  }
})
</script>

<style scoped>
/* 直接抄 DBTabContent 的骨架 CSS，class 同名 */
.db-tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}
.db-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.db-left {
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle, #333);
  overflow: hidden;
}
.db-resizer {
  width: 0.25rem;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
  transition: background 0.15s ease;
}
.db-resizer:hover {
  background: var(--border-subtle, #333);
}
.db-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.k8s-fatal {
  color: var(--el-color-danger, #f56);
  padding: 0.75rem;
}
.k8s-connecting {
  padding: 0.75rem;
  opacity: 0.7;
}
.k8s-ns-warning {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  color: var(--el-color-warning, #e6a23c);
  background: var(--el-color-warning-light-9, #fdf6ec);
  border-bottom: 1px solid var(--el-color-warning-light-5, #faecd8);
  flex-shrink: 0;
}
</style>
