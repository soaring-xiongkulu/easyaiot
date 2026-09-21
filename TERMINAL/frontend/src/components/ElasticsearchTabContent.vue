<template>
  <div class="es-tab-content">
    <div class="es-main">
      <!-- Left: index tree -->
      <div class="es-left" :style="{ width: leftWidth + 'px' }">
        <div class="search-wrap">
          <input v-model="treeSearchQuery" class="search-input" :placeholder="t('es.searchIndices')" />
          <button class="btn btn-ghost btn-icon btn-sm" :title="t('es.refresh')" @click="loadIndices">
            <RefreshCw :size="'0.875rem'" />
          </button>
          <button class="btn btn-ghost btn-icon btn-sm" :title="t('common.more')" @click.stop="moreMenuRef?.toggle($event.currentTarget)">
            <MoreHorizontal :size="'0.875rem'" />
          </button>
          <Menu ref="moreMenuRef" v-model:visible="moreMenuVisible" align="end">
            <MenuItem @click="onMoreToggleSystem">{{ (hideSystemIndices ? '✓ ' : '') + t('es.hideSystem') }}</MenuItem>
            <MenuDivider />
            <MenuItem @click="onMoreNewIndex">{{ t('es.newIndex') }}</MenuItem>
          </Menu>
        </div>
        <div class="tree-content" @contextmenu.prevent="onTreeBlankContextMenu">
          <div v-if="treeLoading" class="tree-loading">{{ t('db.loading') }}</div>
          <template v-else>
            <!-- Cluster root node -->
            <div
              class="cluster-root"
              :class="{ selected: activeTab?.kind === 'cluster' }"
              @click="openClusterTab"
              @contextmenu.prevent="onClusterContextMenu"
            >
              <span class="db-arrow" @click.stop="clusterExpanded = !clusterExpanded">
                <component :is="clusterExpanded ? ChevronDown : ChevronRight" :size="'0.75rem'" />
              </span>
              <span class="health-dot" :class="healthStatus" />
              <span class="cluster-root-name" :title="clusterTooltip">{{ clusterName }}</span>
            </div>
            <div v-if="clusterExpanded" class="child-list">
              <div
                v-for="idx in filteredIndices"
                :key="idx.name"
                class="index-item"
                :class="{ selected: activeIndexName === idx.name }"
                @click="openIndexTab(idx.name)"
                @contextmenu.prevent="onIndexContextMenu($event, idx)"
              >
                <span class="health-dot" :class="idx.health || 'unknown'" />
                <span class="index-name" :title="idx.name">{{ idx.name }}</span>
              </div>
              <div v-if="filteredIndices.length === 0" class="empty-hint">{{ t('es.noIndices') }}</div>
            </div>
          </template>
        </div>
      </div>

      <div class="es-resizer" @mousedown="onResizeStart" />

      <!-- Right content -->
      <div class="es-right">
        <div class="es-tab-bar">
          <div ref="tabScrollRef" class="es-tab-scroll" @wheel="onTabsWheel">
            <template v-for="(tab, index) in tabs" :key="tab.id">
              <div
                v-if="tabDragOverIndex === index && tabDragInsertAfter"
                class="es-tab-indicator"
              />
              <div
                class="es-tab-item"
                :class="{ active: tab.id === activeTabId }"
                :data-tab-id="tab.id"
                draggable="true"
                @click="activateTab(tab.id)"
                @middleclick.prevent="closeTab(tab.id)"
                @contextmenu.prevent="onTabContextMenu($event, tab.id)"
                @dragstart="onTabDragStart($event, tab.id)"
                @dragover.prevent="onTabDragOver($event, index)"
                @dragend="clearTabDragState"
                @drop.prevent="onTabDrop($event, index)"
              >
                <component :is="tab.kind === 'cluster' ? Database : Layers" :size="'0.75rem'" class="tab-icon" />
                <span class="tab-title">{{ tabTitle(tab) }}</span>
                <button class="tab-close" :title="t('tab.close')" @click.stop="closeTab(tab.id)">×</button>
              </div>
            </template>
            <div v-if="tabDragOverIndex === tabs.length - 1 && tabDragInsertAfter" class="es-tab-indicator" />
          </div>
          <button
            v-if="tabShowMore"
            class="es-tab-more"
            :title="t('tab.more')"
            @click.stop="moreTabsMenuRef?.toggle($event.currentTarget)"
          >
            <MoreHorizontal :size="'0.875rem'" />
          </button>
          <Menu ref="moreTabsMenuRef" v-model:visible="moreTabsMenuVisible" align="end">
            <MenuItem
              v-for="tb in tabs"
              :key="tb.id"
              :class="{ active: tb.id === activeTabId }"
              @click="onTabMoreSelect(tb.id)"
            >{{ tabTitle(tb) }}</MenuItem>
          </Menu>
        </div>

        <!-- Panels (keep-alive via v-show) -->
        <div
          v-for="tab in tabs"
          v-show="tab.id === activeTabId"
          :key="'panel-' + tab.id"
          class="es-panel"
        >
          <ElasticsearchIndexView
            v-if="tab.kind === 'index'"
            :session-id="sessionId"
            :index-name="tab.indexName"
          />

          <!-- Cluster info tab -->
          <div v-else class="cluster-panel">
            <div class="cluster-subtabs">
              <button class="cluster-subtab" :class="{ active: clusterSubTab === 'indices' }" @click="clusterSubTab = 'indices'">
                {{ t('es.indexList') }}
              </button>
              <button class="cluster-subtab" :class="{ active: clusterSubTab === 'rest' }" @click="clusterSubTab = 'rest'">
                {{ t('es.restTab') }}
              </button>
            </div>

            <div v-if="clusterSubTab === 'indices'" class="cluster-panel-body">
            <div class="cluster-section">
              <div class="cluster-section-title">
                <span class="health-dot" :class="healthStatus" />
                {{ t('es.clusterInfo') }} · {{ clusterName }}
              </div>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">{{ t('es.version') }}</span>
                  <span class="info-value">{{ clusterInfo?.version || '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.health') }}</span>
                  <span class="info-value">{{ clusterHealth?.status || '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.nodes') }}</span>
                  <span class="info-value">{{ clusterHealth?.numberOfNodes ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.dataNodes') }}</span>
                  <span class="info-value">{{ clusterHealth?.numberOfDataNodes ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.activeShards') }}</span>
                  <span class="info-value">{{ clusterHealth?.activeShards ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.primaryShards') }}</span>
                  <span class="info-value">{{ clusterHealth?.activePrimaryShards ?? '—' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">{{ t('es.unassignedShards') }}</span>
                  <span class="info-value">{{ clusterHealth?.unassignedShards ?? '—' }}</span>
                </div>
              </div>
            </div>

            <div class="cluster-section">
              <div class="cluster-section-title">{{ t('es.indexList') }}</div>
              <div class="object-toolbar">
                <input
                  v-model="indexSearch"
                  class="object-search"
                  :placeholder="t('es.searchIndices')"
                />
                <button
                  class="btn btn-ghost btn-sm"
                  :class="{ active: hideSystemIndices }"
                  :title="t('es.hideSystem')"
                  @click="hideSystemIndices = !hideSystemIndices"
                >{{ (hideSystemIndices ? '✓ ' : '') + t('es.hideSystem') }}</button>
                <button class="btn btn-default btn-sm" @click="onClusterNewIndex">
                  <Plus :size="'0.875rem'" /> {{ t('es.newIndex') }}
                </button>
              </div>
              <el-table
                :data="filteredTableIndices"
                border
                size="small"
                style="width:100%"
                class="db-result-table"
                :empty-text="t('db.noData')"
              >
                <el-table-column prop="name" :label="t('es.indexName')" :min-width="uiPx(180)" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="object-name" @click="openIndexTab(row.name)">
                      <Layers :size="'0.875rem'" class="object-icon" />
                      {{ row.name }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="health" :label="t('es.health')" :width="uiPx(90)" />
                <el-table-column prop="status" :label="t('es.status')" :width="uiPx(90)" />
                <el-table-column :label="t('es.docsCount')" :width="uiPx(100)">
                  <template #default="{ row }">{{ formatDocs(row.docsCount) }}</template>
                </el-table-column>
                <el-table-column prop="storeSize" :label="t('es.storeSize')" :width="uiPx(110)" />
                <el-table-column :label="t('es.shards')" :width="uiPx(90)">
                  <template #default="{ row }">{{ row.pri }} / {{ row.rep }}</template>
                </el-table-column>
                <el-table-column :label="t('common.actions')" :width="uiPx(80)" align="right">
                  <template #default="{ row }">
                    <button
                      class="btn btn-ghost btn-icon btn-sm danger"
                      :title="t('es.deleteIndex')"
                      @click.stop="ctxDeleteIndex(row)"
                    >
                      <Trash2 :size="'0.875rem'" />
                    </button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            </div>

            <!-- REST sub-tab -->
            <div v-else class="rest-section">
              <div class="rest-toolbar">
                <el-select v-model="restMethod" style="width:6.875rem" size="small">
                  <el-option v-for="m in restMethods" :key="m" :label="m" :value="m" />
                </el-select>
                <input v-model="restPath" class="rest-path" placeholder="/_cluster/health" @keydown.enter="runRest" />
                <button class="btn btn-primary btn-sm" @click="runRest" :disabled="restLoading">{{ t('es.send') }}</button>
              </div>
              <SyntaxEditor
                v-model="restBody"
                lang="json"
                class="rest-body"
                :readonly="restMethod === 'GET' || restMethod === 'DELETE'"
              />
              <div class="rest-result">
                <div class="rest-status" v-if="restResult">HTTP {{ restResult.status }}</div>
                <div v-if="restError" class="error-msg">{{ restError }}</div>
                <pre class="json-pre">{{ restResult?.body || '' }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cluster root / tree blank context menu -->
    <Menu ref="clusterMenuRef" v-model:visible="clusterMenuVisible">
      <MenuItem @click="onClusterNewIndex">{{ t('es.newIndex') }}</MenuItem>
      <MenuDivider />
      <MenuItem @click="onClusterRefresh">{{ t('es.refresh') }}</MenuItem>
    </Menu>

    <!-- Index context menu -->
    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
      <MenuItem @click="ctxRefresh(current)">{{ t('es.refresh') }}</MenuItem>
      <MenuItem @click="ctxToggleIndex(current)">{{ toggleIndexAction(current) }}</MenuItem>
      <MenuDivider />
      <MenuItem class="danger" @click="ctxDeleteIndex(current)">{{ t('es.deleteIndex') }}</MenuItem>
    </Menu>

    <!-- Tab context menu -->
    <Menu ref="tabMenuRef" v-model:visible="tabMenuVisible" v-slot="{ current }">
      <template v-if="current">
        <MenuItem @click="onTabClose(current as number)">{{ t('tab.close') }}</MenuItem>
        <MenuItem :class="{ disabled: indexTabCount <= 1 }" @click="onTabCloseOthers(current as number)">{{ t('tab.closeOther') }}</MenuItem>
        <MenuItem :class="{ disabled: tabIndexFor(current as number) <= 0 }" @click="onTabCloseLeft(current as number)">{{ t('tab.closeLeft') }}</MenuItem>
        <MenuItem :class="{ disabled: tabIndexFor(current as number) >= tabs.length - 1 }" @click="onTabCloseRight(current as number)">{{ t('tab.closeRight') }}</MenuItem>
        <MenuDivider />
        <MenuItem @click="onTabCloseAll">{{ t('tab.closeAll') }}</MenuItem>
      </template>
    </Menu>

    <!-- Create index dialog -->
    <el-dialog v-model="createIndexVisible" :title="t('es.newIndex')" width="32.5rem" destroy-on-close>
      <el-form label-width="5rem">
        <el-form-item :label="t('es.indexName')" required>
          <el-input v-model="newIndexName" />
        </el-form-item>
        <el-form-item :label="t('es.indexBody')">
          <SyntaxEditor v-model="newIndexBody" lang="json" class="doc-editor index-body" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createIndexVisible = false">{{ t('settings.cancel') }}</el-button>
        <el-button type="primary" :disabled="!newIndexName.trim()" @click="createIndex">{{ t('redis.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { RefreshCw, Layers, MoreHorizontal, ChevronRight, ChevronDown, Database, Plus, Trash2 } from '@lucide/vue'
import { useI18n } from '../i18n'
import { msg } from '../services/message'
import { ElMessageBox } from 'element-plus'
import Menu from './Menu.vue'
import SyntaxEditor from './SyntaxEditor.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import ElasticsearchIndexView from './ElasticsearchIndexView.vue'
import { uiPx } from '../utils/uiScale'
import {
  EsClusterInfo,
  EsClusterHealth,
  EsListIndices,
  EsCreateIndex,
  EsDeleteIndex,
  EsOpenIndex,
  EsCloseIndex,
  EsRest,
} from '../../bindings/easyaiot/terminal/app'
import type { EsIndexInfo, EsClusterHealth as EsHealth, EsClusterInfo as EsInfo, EsRestResult } from '../types/elasticsearch'

const props = defineProps<{ sessionId: string }>()
const { t } = useI18n()

const leftWidth = ref(220)
const treeLoading = ref(false)
const treeSearchQuery = ref('')
const hideSystemIndices = ref(true)
const indices = ref<EsIndexInfo[]>([])

const clusterInfo = ref<EsInfo | null>(null)
const clusterHealth = ref<EsHealth | null>(null)
const healthStatus = computed(() => (clusterHealth.value?.status || 'unknown').toLowerCase())

const restMethods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
const restMethod = ref('GET')
const restPath = ref('/_cluster/health')
const restBody = ref('')
const restLoading = ref(false)
const restError = ref('')
const restResult = ref<EsRestResult | null>(null)

const ctxMenuVisible = ref(false)
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)

// ── Toolbar (search box) refresh + more menu ──
const moreMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const moreMenuVisible = ref(false)

function onMoreToggleSystem() {
  hideSystemIndices.value = !hideSystemIndices.value
  moreMenuVisible.value = false
}

function onMoreNewIndex() {
  moreMenuVisible.value = false
  openCreateIndex()
}

// ── Cluster root node ──
const clusterExpanded = ref(true)
const clusterSubTab = ref<'indices' | 'rest'>('indices')
const clusterName = computed(() => clusterInfo.value?.clusterName || clusterHealth.value?.clusterName || '—')
const clusterTooltip = computed(() => {
  const parts: string[] = []
  if (clusterInfo.value?.version) parts.push('v' + clusterInfo.value.version)
  if (clusterHealth.value) {
    parts.push(clusterHealth.value.status)
    parts.push(`${clusterHealth.value.numberOfNodes} ${t('es.nodes')}`)
    parts.push(`${clusterHealth.value.activeShards} ${t('es.shards')}`)
  }
  return parts.join(' · ')
})

const clusterMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const clusterMenuVisible = ref(false)

function onClusterContextMenu(e: MouseEvent) {
  clusterMenuRef.value?.openAt(e.clientX, e.clientY, null)
}

function onTreeBlankContextMenu(e: MouseEvent) {
  clusterMenuRef.value?.openAt(e.clientX, e.clientY, null)
}

function onClusterNewIndex() {
  clusterMenuVisible.value = false
  openCreateIndex()
}

function onClusterRefresh() {
  clusterMenuVisible.value = false
  loadIndices()
}

const createIndexVisible = ref(false)
const newIndexName = ref('')
const newIndexBody = ref('')

// ── Tabs ──
interface EsTab {
  id: number
  kind: 'index' | 'cluster'
  indexName: string
}

const tabs = ref<EsTab[]>([])
const activeTabId = ref<number | null>(null)
let nextTabId = 1

const activeTab = computed(() => tabs.value.find(x => x.id === activeTabId.value) || null)

const activeIndexName = computed(() => activeTab.value?.kind === 'index' ? activeTab.value.indexName : '')

function activateTab(id: number) {
  activeTabId.value = id
}

function tabTitle(tab: EsTab): string {
  return tab.kind === 'cluster' ? `${clusterName.value} · ${t('es.indexList')}` : tab.indexName
}

function openIndexTab(name: string) {
  const existing = tabs.value.find(x => x.kind === 'index' && x.indexName === name)
  if (existing) {
    activeTabId.value = existing.id
    return
  }
  const tab: EsTab = { id: nextTabId++, kind: 'index', indexName: name }
  tabs.value.push(tab)
  activeTabId.value = tab.id
}

function openClusterTab() {
  const existing = tabs.value.find(x => x.kind === 'cluster')
  if (existing) {
    activeTabId.value = existing.id
    return
  }
  const tab: EsTab = { id: nextTabId++, kind: 'cluster', indexName: '' }
  tabs.value.push(tab)
  activeTabId.value = tab.id
}

function closeTab(id: number) {
  const idx = tabs.value.findIndex(x => x.id === id)
  if (idx < 0) return
  tabs.value.splice(idx, 1)
  if (activeTabId.value === id) {
    const next = tabs.value[Math.min(idx, tabs.value.length - 1)]
    activeTabId.value = next?.id ?? null
  }
}

// ── Tab context menu (mirrors DBTabContent) ──
const tabMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const tabMenuVisible = ref(false)

function tabIndexFor(id: number) {
  return tabs.value.findIndex(x => x.id === id)
}
const indexTabCount = computed(() => tabs.value.length)

function onTabContextMenu(e: MouseEvent, id: number) {
  e.stopPropagation()
  activateTab(id)
  tabMenuRef.value?.openAt(e.clientX, e.clientY, id)
}

function onTabClose(id: number) {
  closeTab(id)
  tabMenuVisible.value = false
}

function onTabCloseOthers(id: number) {
  if (tabs.value.length > 1) {
    tabs.value = tabs.value.filter(x => x.id === id)
    activeTabId.value = id
  }
  tabMenuVisible.value = false
}

function onTabCloseLeft(id: number) {
  const idx = tabIndexFor(id)
  if (idx > 0) {
    tabs.value = tabs.value.filter((_, i) => i >= idx)
  }
  tabMenuVisible.value = false
}

function onTabCloseRight(id: number) {
  const idx = tabIndexFor(id)
  if (idx >= 0 && idx < tabs.value.length - 1) {
    tabs.value = tabs.value.filter((_, i) => i <= idx)
  }
  tabMenuVisible.value = false
}

function onTabCloseAll() {
  tabs.value = []
  activeTabId.value = null
  tabMenuVisible.value = false
}

// ── Tab bar overflow: wheel scroll + "more" dropdown ──

const tabScrollRef = ref<HTMLElement | null>(null)
const tabShowMore = ref(false)
const moreTabsMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const moreTabsMenuVisible = ref(false)

function updateTabOverflow() {
  const el = tabScrollRef.value
  if (!el) return
  tabShowMore.value = el.scrollWidth > el.clientWidth + 1
}

watch(() => tabs.value.length, () => nextTick(updateTabOverflow))
watch(activeTabId, () => nextTick(updateTabOverflow))

let tabBarResize: ResizeObserver | null = null

onMounted(() => {
  tabBarResize = new ResizeObserver(updateTabOverflow)
  if (tabScrollRef.value) tabBarResize.observe(tabScrollRef.value)
  nextTick(updateTabOverflow)
})

onBeforeUnmount(() => {
  tabBarResize?.disconnect()
  tabBarResize = null
})

function onTabsWheel(e: WheelEvent) {
  if (tabScrollRef.value) tabScrollRef.value.scrollLeft += e.deltaY
}

function onTabMoreSelect(id: number) {
  moreTabsMenuVisible.value = false
  activateTab(id)
  scrollToTab(id)
}

function scrollToTab(id: number) {
  if (!tabScrollRef.value) return
  const el = tabScrollRef.value.querySelector(`[data-tab-id="${id}"]`) as HTMLElement | null
  el?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

// ── Tab drag reorder (insert-indicator pattern, mirrors DBTabContent) ──

const tabDragId = ref(0)
const tabDragOverIndex = ref(-1)
const tabDragInsertAfter = ref(false)

function onTabDragStart(e: DragEvent, id: number) {
  tabDragId.value = id
  e.dataTransfer?.setData('application/es-tab-id', String(id))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onTabDragOver(e: DragEvent, index: number) {
  if (!e.dataTransfer?.types.includes('application/es-tab-id')) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  tabDragOverIndex.value = index
  tabDragInsertAfter.value = e.clientX >= rect.left + rect.width / 2
  e.dataTransfer.dropEffect = 'move'
}

function onTabDrop(_e: DragEvent, index: number) {
  const from = tabIndexFor(tabDragId.value)
  const insertAfter = tabDragInsertAfter.value
  clearTabDragState()
  if (from < 0) return
  let to = insertAfter ? index + 1 : index
  // Moving right compacts the source slot out of the range first.
  if (from < to) to -= 1
  if (to === from) return
  const [moved] = tabs.value.splice(from, 1)
  tabs.value.splice(to, 0, moved)
}

function clearTabDragState() {
  tabDragId.value = 0
  tabDragOverIndex.value = -1
  tabDragInsertAfter.value = false
}

const filteredIndices = computed(() => {
  const q = treeSearchQuery.value.trim().toLowerCase()
  return indices.value.filter(idx => {
    if (hideSystemIndices.value && idx.name.startsWith('.')) return false
    if (q && !idx.name.toLowerCase().includes(q)) return false
    return true
  })
})

const tableIndices = computed(() => {
  return hideSystemIndices.value ? indices.value.filter(idx => !idx.name.startsWith('.')) : indices.value
})

const indexSearch = ref('')

const filteredTableIndices = computed(() => {
  const q = indexSearch.value.trim().toLowerCase()
  if (!q) return tableIndices.value
  return tableIndices.value.filter(idx => idx.name.toLowerCase().includes(q))
})

watch(() => props.sessionId, () => {
  if (props.sessionId) refreshAll()
})

onMounted(() => {
  if (props.sessionId) refreshAll()
  openClusterTab()
})

async function refreshAll() {
  await Promise.all([loadCluster(), loadIndices()])
}

async function loadCluster() {
  if (!props.sessionId) return
  try {
    const [info, health] = await Promise.all([
      EsClusterInfo(props.sessionId),
      EsClusterHealth(props.sessionId),
    ])
    clusterInfo.value = info as EsInfo
    clusterHealth.value = health as EsHealth
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function loadIndices() {
  if (!props.sessionId) return
  treeLoading.value = true
  try {
    indices.value = (await EsListIndices(props.sessionId)) as EsIndexInfo[]
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
  treeLoading.value = false
}

function formatDocs(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n ?? 0)
}

async function runRest() {
  if (!props.sessionId) return
  restLoading.value = true
  restError.value = ''
  try {
    restResult.value = await EsRest(
      props.sessionId,
      restMethod.value,
      restPath.value,
      restMethod.value === 'GET' || restMethod.value === 'DELETE' || restMethod.value === 'HEAD' ? '' : restBody.value,
    ) as EsRestResult
  } catch (e: any) {
    restError.value = e?.message || String(e)
    restResult.value = null
  }
  restLoading.value = false
}

function openCreateIndex() {
  newIndexName.value = ''
  newIndexBody.value = ''
  createIndexVisible.value = true
}

async function createIndex() {
  if (!props.sessionId || !newIndexName.value.trim()) return
  try {
    await EsCreateIndex(props.sessionId, newIndexName.value.trim(), newIndexBody.value.trim())
    msg.success(t('es.indexCreated'))
    createIndexVisible.value = false
    await loadIndices()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function onIndexContextMenu(e: MouseEvent, idx: EsIndexInfo) {
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, idx)
}

async function ctxRefresh(_current: unknown) {
  ctxMenuVisible.value = false
  await loadIndices()
}

// Toggle item: a closed index offers "open", an open one offers "close".
function toggleIndexAction(current: unknown): string {
  const status = (current as EsIndexInfo | null)?.status
  return status === 'close' ? t('es.openIndex') : t('es.closeIndex')
}

async function ctxToggleIndex(current: unknown) {
  const info = current as EsIndexInfo | null
  ctxMenuVisible.value = false
  const name = info?.name
  if (!name || !props.sessionId) return
  const closing = info?.status !== 'close'
  const action = closing ? t('es.closeIndex') : t('es.openIndex')
  try {
    await ElMessageBox.confirm(t('es.toggleIndexConfirm', { action, name }), { type: 'warning' })
  } catch {
    return
  }
  try {
    if (closing) {
      await EsCloseIndex(props.sessionId, name)
      msg.success(t('es.indexClosed'))
    } else {
      await EsOpenIndex(props.sessionId, name)
      msg.success(t('es.indexOpened'))
    }
    await loadIndices()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

async function ctxDeleteIndex(current: unknown) {
  const name = (current as EsIndexInfo | null)?.name
  ctxMenuVisible.value = false
  if (!name || !props.sessionId) return
  try {
    await ElMessageBox.confirm(t('es.deleteIndexConfirm', { name }), { type: 'warning' })
  } catch {
    return
  }
  try {
    await EsDeleteIndex(props.sessionId, name)
    msg.success(t('es.indexDeleted'))
    const tab = tabs.value.find(x => x.indexName === name)
    if (tab) closeTab(tab.id)
    await loadIndices()
  } catch (e: any) {
    msg.error(e?.message || String(e))
  }
}

function onResizeStart(e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startW = leftWidth.value
  const onMove = (ev: MouseEvent) => {
    leftWidth.value = Math.max(180, Math.min(480, startW + ev.clientX - startX))
  }
  const onUp = () => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)
  }
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.es-tab-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-base);
  color: var(--text-primary);
  overflow: hidden;
}
.health-dot {
  display: inline-block;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--text-disabled);
}
.health-dot.green { background: #22c55e; }
.health-dot.yellow { background: #eab308; }
.health-dot.red { background: #ef4444; }
.health-dot.open { background: #22c55e; }
.health-dot.close, .health-dot.closed { background: var(--text-disabled); }

.es-main {
  display: flex;
  flex: 1;
  min-height: 0;
}
.es-left {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
  flex-shrink: 0;
  min-width: 0;
}
.search-wrap {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
}
.search-input {
  flex: 1;
  min-width: 0;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.tree-content {
  flex: 1;
  overflow: auto;
}
.cluster-root {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.cluster-root:hover { background: var(--bg-hover); }
.cluster-root.selected { background: var(--bg-hover); }
.db-arrow {
  width: 0.75rem;
  flex-shrink: 0;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  cursor: pointer;
}
.db-arrow:hover {
  color: var(--text-primary);
}
.cluster-root-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}
.child-list {
  padding-bottom: 0.25rem;
}
.child-list .index-item {
  padding-left: 2.75rem;
}
.tree-loading {
  padding: 0.75rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.75rem;
}
.index-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s ease;
}
.index-item:hover { background: var(--bg-hover); }
.index-item.selected { background: var(--bg-hover); }
.index-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
}
.index-meta {
  font-size: 0.6875rem;
  color: var(--text-muted);
  flex-shrink: 0;
}
.empty-hint, .select-hint {
  padding: 1rem;
  color: var(--text-muted);
  font-size: 0.8125rem;
  text-align: center;
}
.es-resizer {
  width: 0.25rem;
  cursor: col-resize;
  background: transparent;
  flex-shrink: 0;
}
.es-resizer:hover { background: var(--border-subtle); }

.es-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
.es-tab-bar {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  flex-shrink: 0;
  min-height: 2rem;
}
.es-tab-scroll {
  display: flex;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  min-width: 0;
}
.es-tab-scroll::-webkit-scrollbar { height: 0.25rem; }
.es-tab-indicator {
  width: 0.125rem;
  min-width: 0.125rem;
  align-self: stretch;
  background: var(--accent);
  opacity: 0.8;
  margin: 0.25rem 0;
}
.es-tab-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  max-width: 11.25rem;
  padding: 0.375rem 0.5rem 0.375rem 0.75rem;
  border-right: 1px solid var(--border-subtle);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.12s ease;
}
.es-tab-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.es-tab-item.active {
  background: var(--bg-base);
  color: var(--text-primary);
  box-shadow: inset 0 -0.125rem 0 var(--accent);
}
.tab-icon { flex-shrink: 0; opacity: 0.8; }
.tab-title { overflow: hidden; text-overflow: ellipsis; }
.tab-close {
  width: 1rem;
  height: 1rem;
  line-height: 0.875rem;
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  border-radius: 0.1875rem;
  flex-shrink: 0;
}
.tab-close:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.es-tab-more {
  width: 1.75rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-left: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
}
.es-tab-more:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.es-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.cluster-panel {
  flex: 1;
  overflow: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
}
.cluster-subtabs {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  padding: 0 0.75rem;
  min-height: 2rem;
  margin: -0.75rem -0.75rem 0;
}
.cluster-subtab {
  padding: 0.375rem 1rem;
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  border-bottom: 0.125rem solid transparent;
  transition: all 0.15s ease;
}
.cluster-subtab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.cluster-subtab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
}
/* 结果表格主题变量与 DBResultGrid 保持一致 */
.db-result-table {
  --el-table-header-bg-color: var(--bg-elevated, var(--bg-surface));
  --el-table-tr-bg-color: var(--bg-surface);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-subtle);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-text-color: var(--text-primary);
  --el-table-bg-color: var(--bg-surface);
  font-size: 0.75rem;
}
.cluster-panel-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 0.75rem;
}
.cluster-section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-ui);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.cluster-section-title .section-action { margin-left: auto; }
.object-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.object-toolbar .btn:last-child { margin-left: auto; }
.object-search {
  width: 15rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  outline: none;
}
.object-search:focus { border-color: var(--accent); }
.object-name {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
  transition: color 0.15s ease;
}
.object-name:hover { color: var(--accent); }
.object-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(11.25rem, 1fr));
  gap: 0.5rem;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0.5rem 0.625rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
}
.info-label {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  color: var(--text-muted);
}
.info-value {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--text-primary);
}

.rest-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0.5rem;
  gap: 0.5rem;
}
.rest-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-shrink: 0;
}
.rest-path {
  flex: 1;
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--bg-base);
  color: var(--text-primary);
  outline: none;
}
.rest-body {
  height: 8.75rem;
  flex-shrink: 0;
}
.rest-result {
  flex: 1;
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  background: var(--bg-elevated);
}
.rest-status {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
  color: var(--text-secondary);
}

.doc-editor {
  width: 100%;
  height: 20rem;
}
.doc-editor.index-body {
  height: 11.25rem;
}

</style>
