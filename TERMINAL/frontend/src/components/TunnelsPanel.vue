<template>
  <div class="tunnels-panel">
    <!-- Toolbar -->
    <div class="tn-toolbar">
      <el-input
        v-model="searchQuery"
        :placeholder="t('tunnels.searchPlaceholder')"
        clearable
        class="tn-search-input"
      />
      <button class="tn-icon-btn" :title="t('tunnels.addTunnel')" @click="addTunnel">
        <Plus :size="'0.9375rem'" />
      </button>
    </div>

    <!-- Flat list (grouping lives in the Settings page's data model only;
         the sidebar shows every tunnel in sortOrder) -->
    <div class="tn-list">
      <div
        v-for="tn in visibleTunnels"
        :key="tn.id"
        class="tn-item"
        :class="{ running: statusOf(tn) === 'running', errored: statusOf(tn) === 'error' }"
        @dblclick="toggleRun(tn)"
        @contextmenu.prevent="onTunnelContextMenu($event, tn)"
      >
        <span class="tn-status" :title="statusTitle(tn)"></span>
        <div class="tn-item-content">
          <div class="tn-item-name">{{ tn.name }}</div>
          <div class="tn-item-meta">
            <span class="tn-badge" :class="tn.mode">{{ t(`tunnels.mode.${tn.mode}`) }}</span>
            <span class="tn-port">:{{ effPort(tn) }}</span>
          </div>
        </div>
        <button
          class="tn-run-btn"
          :title="statusOf(tn) === 'running' ? t('tunnels.stop') : t('tunnels.start')"
          @click.stop="toggleRun(tn)"
        >
          <Square v-if="statusOf(tn) === 'running'" :size="'0.8125rem'" />
          <Play v-else :size="'0.8125rem'" />
        </button>
      </div>

      <div v-if="store.tunnels.length === 0" class="tn-empty">{{ t('tunnels.empty') }}</div>
    </div>

    <!-- Row context menu -->
    <Menu ref="rowMenuRef" v-model:visible="rowMenuVisible">
      <template v-if="selectedTunnel">
        <MenuItem @click="toggleRun(selectedTunnel); rowMenuVisible = false">
          {{ statusOf(selectedTunnel) === 'running' ? t('tunnels.stop') : t('tunnels.start') }}
        </MenuItem>
        <MenuDivider />
        <!-- Editing a running tunnel would desync the form from what's actually
             running; edits require a stop first. -->
        <MenuItem
          :class="{ disabled: selectedRunning }"
          @click="editTunnel(selectedTunnel.id)"
        >{{ t('tunnels.editTunnel') }}</MenuItem>
        <MenuItem class="danger" @click="doDeleteTunnel(selectedTunnel)">{{ t('tunnels.deleteTunnel') }}</MenuItem>
      </template>
    </Menu>

    <TunnelEditDialog v-model="editDialogVisible" :editing-id="editingTunnelId" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Play, Square } from '@lucide/vue'
import { useTunnelStore, type Tunnel } from '../stores/tunnelStore'
import { useConnectionStore } from '../stores/connectionStore'
import { useI18n } from '../i18n'
import { useTunnelCredentials } from '../composables/useTunnelCredentials'
import TunnelEditDialog from './TunnelEditDialog.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'

const { t } = useI18n()
const store = useTunnelStore()
const connectionStore = useConnectionStore()
const { resolveTunnelCredentials } = useTunnelCredentials()

const searchQuery = ref('')

const rowMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const rowMenuVisible = ref(false)
const selectedTunnel = ref<Tunnel | null>(null)

const editDialogVisible = ref(false)
const editingTunnelId = ref<string | undefined>(undefined)

const visibleTunnels = computed(() =>
  [...store.tunnels]
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
    .filter(matchesSearch)
)

onMounted(async () => {
  await store.load()
  await connectionStore.load()
})

function matchesSearch(tn: Tunnel): boolean {
  if (!searchQuery.value.trim()) return true
  return tn.name.toLowerCase().includes(searchQuery.value.toLowerCase())
}

const statusOf = (tn: Tunnel) => store.statusOf(tn.id)
const selectedRunning = computed(() => !!selectedTunnel.value && statusOf(selectedTunnel.value) === 'running')
const effPort = (tn: Tunnel) => store.states[tn.id]?.localPort || tn.listenPort
const statusTitle = (tn: Tunnel) => {
  const status = statusOf(tn)
  if (status === 'error') return store.states[tn.id]?.error || t('tunnels.statusError')
  return status === 'running' ? t('tunnels.statusRunning') : t('tunnels.statusStopped')
}

async function toggleRun(tn: Tunnel) {
  // Errors toast from the tunnel:state listener in the tunnel store, which
  // also covers auto-start failures and mid-run disconnects.
  if (statusOf(tn) === 'running') {
    await store.stop(tn.id)
  } else {
    // Exit connection without saved credentials: prompt once for user/password
    // and pass them inline (backend fills only empty fields). Cancel aborts.
    const creds = await resolveTunnelCredentials(tn.sshConnId)
    if (!creds) return
    await store.start(tn.id, creds.user, creds.password)
  }
}

function onTunnelContextMenu(e: MouseEvent, tn: Tunnel) {
  selectedTunnel.value = tn
  rowMenuRef.value?.openAt(e.clientX, e.clientY)
}

function editTunnel(id: string) {
  rowMenuVisible.value = false
  // Disabled rows still fire click handlers (attr fallthrough); guard here.
  if (store.statusOf(id) === 'running') return
  editingTunnelId.value = id
  editDialogVisible.value = true
}

function addTunnel() {
  editingTunnelId.value = undefined
  editDialogVisible.value = true
}

function doDeleteTunnel(tn: Tunnel) {
  rowMenuVisible.value = false
  store.deleteTunnel(tn.id)
}
</script>

<style scoped>
.tunnels-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.tn-toolbar { display: flex; align-items: center; gap: 0.25rem; padding: 0 0.625rem 0.375rem; flex-shrink: 0; }
.tn-search-input { flex: 1; min-width: 0; }
.tn-icon-btn { width: 1.625rem; height: 1.625rem; display: flex; align-items: center; justify-content: center; border: none; border-radius: 0.25rem; background: transparent; color: var(--text-muted); cursor: pointer; flex-shrink: 0; }
.tn-icon-btn:hover { color: var(--text-primary); background: var(--bg-hover); }
.tn-list { flex: 1; overflow-y: auto; padding: 0 0.5rem 0.5rem; }
.tn-item { display: flex; align-items: center; gap: 0.625rem; padding: 0.4375rem 0.625rem; min-height: 2.5rem; border-radius: var(--radius-sm); cursor: pointer; margin: 1px 0; user-select: none; }
.tn-item:hover { background: var(--bg-hover); }
.tn-status { width: 0.5rem; height: 0.5rem; border-radius: 50%; background: var(--text-disabled); flex-shrink: 0; }
.tn-item.running .tn-status { background: var(--success, #24c08a); box-shadow: 0 0 0 0.1875rem color-mix(in srgb, var(--success, #24c08a) 20%, transparent); }
.tn-item.errored .tn-status { background: var(--error, #e5604d); }
.tn-item-content { flex: 1; min-width: 0; }
.tn-item-name { font-size: 0.75rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tn-item-meta { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.125rem; }
.tn-badge { font-size: 0.625rem; font-weight: 600; padding: 0 0.3125rem; border-radius: 0.25rem; background: var(--bg-active, rgba(255,255,255,.06)); color: var(--text-muted); }
.tn-badge.local { color: #8fb6ff; }
.tn-badge.remote { color: #e0a54b; }
.tn-badge.dynamic { color: #24c08a; }
.tn-port { font-size: 0.6875rem; color: var(--text-muted); font-family: var(--font-mono, monospace); }
.tn-run-btn { width: 1.5rem; height: 1.5rem; display: inline-flex; align-items: center; justify-content: center; border: none; border-radius: 0.3125rem; background: transparent; color: var(--text-muted); cursor: pointer; flex-shrink: 0; }
.tn-item.running .tn-run-btn { color: var(--error, #e5604d); }
.tn-item:not(.running) .tn-run-btn { color: var(--success, #24c08a); }
.tn-run-btn:hover { background: var(--bg-active, rgba(255,255,255,.08)); }
.tn-empty { padding: 1.5rem 0.75rem; text-align: center; color: var(--text-muted); font-size: 0.75rem; }
</style>
