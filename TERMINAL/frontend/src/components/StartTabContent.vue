<template>
  <div ref="startTabRef" class="start-tab">
    <div class="start-content" :style="contentStyle">
      <!-- Branding -->
      <div class="start-brand" v-show="!searchQuery.trim()">Terminal</div>

      <!-- Search row -->
    <div class="start-search-row">
      <span class="start-filter-btn" :class="{ active: selectedTypeFilter !== 'all' }" @click.stop="filterMenuRef?.toggle($event.currentTarget)">
        <el-icon><Filter :size="'0.875rem'" /></el-icon>
        <span>{{ filterDisplay }}</span>
      </span>
      <TypeFilterMenu ref="filterMenuRef" align="start" v-model="selectedTypeFilter" />
      <el-input
        ref="searchInputRef"
        v-model="searchQuery"
        class="start-search-input"
        :placeholder="t('sidebar.searchPlaceholder')"
        clearable
        @keydown="onSearchKeydown"
      />
    </div>

    <!-- Action buttons -->
    <div class="start-action-btns">
      <button class="start-action-btn primary" @click="emit('new-connection', { groupId: tab.viewMode === 'group' ? tab.groupId : undefined, host: (searchQuery || '').trim() || undefined })">
        <el-icon><Plus :size="'0.875rem'" /></el-icon>
        {{ t('header.newConnection') }}
      </button>
      <button class="start-action-btn" @click="emit('new-workspace')">
        <el-icon><LayoutDashboard :size="'0.875rem'" /></el-icon>
        {{ t('workspace.newWorkspace') }}
      </button>
      <div v-if="!isMobile" class="start-action-btn-group">
        <button class="start-action-btn" @click="handleDefaultLocalTerminal">
          <el-icon><Laptop :size="'0.875rem'" /></el-icon>
          {{ t('conn.startLocalTerminal') }}
        </button>
        <button class="start-action-btn-dropdown-arrow" @click.stop="shellMenuRef?.toggle($event.currentTarget)">
          <el-icon><ChevronDown :size="'0.75rem'" /></el-icon>
        </button>
        <Menu ref="shellMenuRef" v-model:visible="shellMenuVisible">
          <MenuItem
            v-for="sh in settingsStore.availableShells"
            :key="sh"
            @click="onShellPick(sh, $event)"
          >
            {{ getShellLabel(sh) }}
          </MenuItem>
          <MenuItem v-if="settingsStore.availableShells.length === 0" class="disabled">
            No shells available
          </MenuItem>
        </Menu>
      </div>

    </div>

    <!-- Breadcrumb for group view -->
    <div v-if="tab.viewMode === 'group'" class="start-breadcrumb">
      <span class="link" @click="goHome">{{ t('startTab.backToStart') }}</span>
      <template v-for="crumb in breadcrumbPath" :key="crumb.id">
        <span class="sep">/</span>
        <span v-if="crumb.id === tab.groupId" class="current">{{ crumb.name }}</span>
        <span v-else class="link" @click="enterGroupAt(crumb.id)">{{ crumb.name }}</span>
      </template>
      <span class="start-add-group-btn" @click="openNewGroupDialog" :title="t('conn.newGroupTitle')">
        <el-icon><Plus :size="'0.75rem'" /></el-icon>
      </span>
    </div>

    <!-- Home view sections -->
    <template v-if="tab.viewMode === 'home'">
      <!-- Favorites -->
      <template v-if="favoriteConfigs.length > 0">
        <div class="start-section-label">{{ t('startTab.favorites') }}</div>
        <div class="start-cards-grid">
          <div
            v-for="config in favoriteConfigs"
            :key="'fav:' + config.id"
            class="start-card"
            :class="{ focused: isCardFocused('fav:' + config.id), selected: selectedIds.has('fav:' + config.id) }"
            @click="onCardClick(config, $event, 'fav:')"
            @dblclick="onCardDblClick(config, $event)"
            @contextmenu.prevent="onContextMenu($event, config, 'fav:')"
          >
            <div class="start-card-top">
              <div class="start-card-icon" :class="config.type">
                <el-icon><component :is="connTypeIcon(config) || Server" :size="'1.75rem'" /></el-icon>
              </div>
              <div>
                <div class="start-card-name">{{ config.name }}</div>
                <div class="start-card-meta">{{ getCardSubtitle(config) }}</div>
              </div>
            </div>
            <!-- Inside the favorites section the star is hover-only (everything
                 here is favorited; a lit star would be redundant noise) -->
            <button class="card-fav-btn lit" :title="t('sidebar.removeFromFavorites')" @click.stop="favoriteStore.toggle(config.id)"><Star :size="'0.875rem'" /></button>
            <button class="card-more-btn" @click.stop="onCardMoreClick($event, config, 'fav:')" :title="t('terminal.more')"><MoreHorizontal :size="'1rem'" /></button>
          </div>
        </div>
      </template>

      <!-- Recent connections -->
      <template v-if="recentConfigs.length > 0">
        <div class="start-section-label">{{ t('startTab.recentConnections') }}</div>
        <div class="start-cards-grid">
          <div
            v-for="config in recentConfigs"
            :key="config.id"
            class="start-card"
            :class="{ focused: isCardFocused('recent:' + config.id), selected: selectedIds.has('recent:' + config.id) }"
            @click="onCardClick(config, $event, 'recent:')"
            @dblclick="onCardDblClick(config, $event)"
            @contextmenu.prevent="onContextMenu($event, config, 'recent:')"
          >
            <div class="start-card-top">
              <div class="start-card-icon" :class="config.type">
                <el-icon><component :is="connTypeIcon(config) || Server" :size="'1.75rem'" /></el-icon>
              </div>
              <div>
                <div class="start-card-name">{{ config.name }}</div>
                <div class="start-card-meta">{{ getCardSubtitle(config) }}</div>
              </div>
            </div>
            <button class="card-fav-btn" :class="{ on: favoriteStore.isFavorite(config.id) }" :title="favoriteStore.isFavorite(config.id) ? t('sidebar.removeFromFavorites') : t('sidebar.addToFavorites')" @click.stop="favoriteStore.toggle(config.id)"><Star :size="'0.875rem'" /></button>
            <button class="card-more-btn" @click.stop="onCardMoreClick($event, config, 'recent:')" :title="t('terminal.more')"><MoreHorizontal :size="'1rem'" /></button>
          </div>
        </div>
      </template>

      <!-- Groups -->
      <div class="start-section-label">
        {{ t('startTab.groups') }}
        <span class="start-add-group-btn" @click="openNewGroupDialog" :title="t('conn.newGroupTitle')"><el-icon><Plus :size="'0.75rem'" /></el-icon></span>
      </div>
      <div class="start-cards-grid">
        <div
          v-for="group in groupCards.groups"
          :key="group.id"
          class="start-card"
          :class="{ focused: isCardFocused('group:' + group.id) }"
          @click="onGroupClick(group.id)"
          @dblclick="enterGroup(group.id)"
          @contextmenu.prevent="onGroupContextMenu($event, group.id, group.name)"
        >
          <div class="start-card-top">
            <div class="start-card-icon group"><el-icon><Folder :size="'1.375rem'" /></el-icon></div>
            <div>
              <div class="start-card-name">{{ group.name }}</div>
              <div class="start-card-meta">{{ t('startTab.connectionsCount', { count: group.count }) }}</div>
            </div>
          </div>
        </div>
        <div
          v-if="groupCards.ungroupedCount > 0"
          class="start-card"
          :class="{ focused: isCardFocused('group:__ungrouped__') }"
          @click="onGroupClick('__ungrouped__')"
          @dblclick="enterGroup('__ungrouped__')"
        >
          <div class="start-card-top">
            <div class="start-card-icon ungrouped"><el-icon><FolderOpen :size="'1.375rem'" /></el-icon></div>
            <div>
              <div class="start-card-name">{{ t('conn.noGroup') }}</div>
              <div class="start-card-meta">{{ t('startTab.connectionsCount', { count: groupCards.ungroupedCount }) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- All connections - only shown when searching -->
      <template v-if="searchQuery.trim()">
        <div class="start-section-label">{{ t('startTab.allConnections') }}</div>
        <div class="start-cards-grid">
          <div
            v-for="{ config } in filteredConnections"
            :key="config.id"
            class="start-card"
            :class="{ focused: isCardFocused('conn:' + config.id), selected: selectedIds.has('conn:' + config.id) }"
            @click="onCardClick(config, $event)"
            @dblclick="onCardDblClick(config, $event)"
            @contextmenu.prevent="onContextMenu($event, config)"
          >
            <div class="start-card-top">
              <div class="start-card-icon" :class="config.type">
                <el-icon><component :is="connTypeIcon(config) || Server" :size="'1.75rem'" /></el-icon>
              </div>
              <div>
                <div class="start-card-name">{{ config.name }}</div>
                <div class="start-card-meta">{{ getCardSubtitle(config) }}</div>
              </div>
            </div>
            <button class="card-fav-btn" :class="{ on: favoriteStore.isFavorite(config.id) }" :title="favoriteStore.isFavorite(config.id) ? t('sidebar.removeFromFavorites') : t('sidebar.addToFavorites')" @click.stop="favoriteStore.toggle(config.id)"><Star :size="'0.875rem'" /></button>
            <button class="card-more-btn" @click.stop="onCardMoreClick($event, config)" :title="t('terminal.more')"><MoreHorizontal :size="'1rem'" /></button>
          </div>
        </div>
        <div v-if="filteredConnections.length === 0 && connectionStore.connections.length > 0" class="start-empty-hint">
          {{ t('startTab.noConnections') }}
        </div>
      </template>
    </template>

    <!-- Group detail view -->
    <template v-if="tab.viewMode === 'group'">
      <!-- Child groups -->
      <div v-if="groupCards.groups.length > 0" class="start-section-label">{{ t('startTab.groups') }}</div>
      <div v-if="groupCards.groups.length > 0" class="start-cards-grid">
        <div
          v-for="group in groupCards.groups"
          :key="group.id"
          class="start-card"
          :class="{ focused: isCardFocused('group:' + group.id) }"
          @click="onGroupClick(group.id)"
          @dblclick="enterGroup(group.id)"
          @contextmenu.prevent="onGroupContextMenu($event, group.id, group.name)"
        >
          <div class="start-card-top">
            <div class="start-card-icon group"><el-icon><Folder :size="'1.375rem'" /></el-icon></div>
            <div>
              <div class="start-card-name">{{ group.name }}</div>
              <div class="start-card-meta">{{ t('startTab.connectionsCount', { count: group.count }) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Connections in this group -->
      <div v-if="filteredConnections.length > 0 || groupCards.ungroupedCount > 0" class="start-section-label">{{ t('startTab.connections') }}</div>
      <div class="start-cards-grid">
        <div
          v-for="{ config } in filteredConnections"
          :key="config.id"
          class="start-card"
          :class="{ focused: isCardFocused('conn:' + config.id), selected: selectedIds.has('conn:' + config.id) }"
          @click="onCardClick(config, $event)"
          @dblclick="onCardDblClick(config, $event)"
	          @contextmenu.prevent="onContextMenu($event, config)"
        >
          <div class="start-card-top">
            <div class="start-card-icon" :class="config.type">
              <el-icon><component :is="connTypeIcon(config) || Server" :size="'1.75rem'" /></el-icon>
            </div>
            <div>
              <div class="start-card-name">{{ config.name }}</div>
              <div class="start-card-meta">{{ getCardSubtitle(config) }}</div>
            </div>
          </div>
          <button class="card-fav-btn" :class="{ on: favoriteStore.isFavorite(config.id) }" :title="favoriteStore.isFavorite(config.id) ? t('sidebar.removeFromFavorites') : t('sidebar.addToFavorites')" @click.stop="favoriteStore.toggle(config.id)"><Star :size="'0.875rem'" /></button>
          <button class="card-more-btn" @click.stop="onCardMoreClick($event, config)" :title="t('terminal.more')"><MoreHorizontal :size="'1rem'" /></button>
        </div>
      </div>
      <div v-if="filteredConnections.length === 0" class="start-empty-hint">
        {{ t('startTab.emptyGroup') }}
      </div>
    </template>

    <!-- Quick connect virtual card -->
    <div
      v-if="searchQuery.trim()"
      class="start-quick-card"
      :class="{ focused: isCardFocused('quick') }"
      @click="onQuickClick"
      @dblclick="emit('new-connection', { host: searchQuery.trim() })"
    >
      <div class="start-card-top">
        <div class="start-card-icon quick"><el-icon><Zap :size="'1.375rem'" /></el-icon></div>
        <div>
          <div class="start-card-name quick-name">{{ t('startTab.quickConnect', { host: searchQuery.trim() }) }}</div>
          <div class="start-card-meta">{{ t('startTab.quickConnectDesc') }}</div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="connectionStore.connections.length === 0" class="start-empty-state">
      <span class="empty-icon">📋</span>
      <p>{{ t('startTab.noConnections') }}</p>
    </div>
    </div>

    <!-- Context menu -->
    <ConnectionContextMenu
      ref="contextMenuRef"
      :config="contextMenuConfig"
      :targets="ctxTargets"
      v-model:visible="contextMenuVisible"
      @connect="onCtxConnect"
      @connect-to-workspace="onCtxConnectToWorkspace"
      @create-workspace="onCtxCreateWorkspace"
      @edit="doEditConnection"
      @change-group="onCtxChangeGroup"
      @new-group="openNewGroupDialog"
      @delete="onCtxDelete"
    />

    <!-- Group context menu -->
    <GroupContextMenu
      ref="groupMenuRef"
      :group="groupContextTarget"
      v-model:visible="groupMenuVisible"
      @new-group="doNewGroupFromCtx"
      @new-connection="doNewConnInGroup"
      @rename="doRenameGroup"
      @change-parent="doChangeGroupParent"
      @delete-group="doDeleteGroup"
    />

    <RenameGroupDialog v-model:visible="showRenameGroupDialog" :name="groupContextTarget?.name || ''" @confirm="onRenameGroupConfirm" />

    <NewGroupDialog v-model:visible="showNewGroupDialog" :parent-id="newGroupParentId" @confirm="onAddGroupConfirm" />

    <DeleteGroupDialog v-model:visible="showDeleteGroupDialog" :group="deleteGroupTarget" @confirm="confirmDeleteGroup" />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import Menu from './Menu.vue'
import TypeFilterMenu from './TypeFilterMenu.vue'
import ConnectionContextMenu from './ConnectionContextMenu.vue'
import GroupContextMenu from './GroupContextMenu.vue'
import RenameGroupDialog from './RenameGroupDialog.vue'
import NewGroupDialog from './NewGroupDialog.vue'
import DeleteGroupDialog from './DeleteGroupDialog.vue'
import type { StartTab } from '../types/workspace'
import type { ConnectionConfig, ConnectionGroup } from '../types/session'
import { useConnectionStore } from '../stores/connectionStore'
import { useFavoriteStore } from '../stores/favoriteStore'
import { useTabStore } from '../stores/tabStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useI18n } from '../i18n'
import { isMobilePlatform } from '../utils/platform'
import { GetRecentConnections } from '../../bindings/easyaiot/terminal/app'
import { formatConnSubtitle, formatTypeFilterLabel, matchTypeFilter } from '../utils/quickConnect'
import { connectionTypeIcon as connTypeIcon, connectionTypeLabel as connTypeLabel } from '../utils/connectionTypes'
import { getShellLabel as getShellLabelBase } from '../utils/shellLabel'
import MenuItem from './MenuItem.vue'
import { Filter, Plus, Laptop, Server, Folder, FolderOpen, Zap, MoreHorizontal, ChevronDown, Star, LayoutDashboard } from '@lucide/vue'

const props = defineProps<{
  tab: StartTab
}>()

const emit = defineEmits<{
  connect: [config: ConnectionConfig, keepOpen?: boolean]
  'connect-to-workspace': [payload: { configs: ConnectionConfig[]; workspaceId: string }]
  'create-workspace': [configs: ConnectionConfig[]]
  'new-workspace': []
  'new-connection': [payload?: { host?: string; groupId?: string; type?: string }]
  'local-terminal': [shellPath: string, keepOpen?: boolean]
  'close-self': [tabId: string]
  'edit-connection': [config: ConnectionConfig]
  'change-group': [config: ConnectionConfig]
  'change-group-ids': [ids: string[]]
}>()

const { t } = useI18n()
const connectionStore = useConnectionStore()
const favoriteStore = useFavoriteStore()
const tabStore = useTabStore()
const settingsStore = useSettingsStore()

// ── Default local shell ──
const effectiveDefaultShell = computed(() => {
  const shells = settingsStore.availableShells
  if (shells.length === 0) return ''
  const preferred = settingsStore.settings.defaultLocalShell
  return preferred && shells.includes(preferred) ? preferred : shells[0]
})

function onShellPick(sh: string, e: MouseEvent) {
  shellMenuVisible.value = false
  emit('local-terminal', sh, e.ctrlKey || e.metaKey)
}

function handleDefaultLocalTerminal() {
  const shell = effectiveDefaultShell.value
  if (shell) {
    emit('local-terminal', shell)
  }
}

// ── Card subtitle (matches sidebar display format) ──
function getCardSubtitle(config: ConnectionConfig): string {
  return formatConnSubtitle(config, getShellLabel)
}

// ── Multi-select ──
// Card keys: each card gets a unique key = prefix + config.id.
// "recent:" prefix for recent-connection cards, "conn:" for all others.
// This way the same connection appearing in both sections has two
// independently selectable cards.
const selectedIds = ref<Set<string>>(new Set())
const lastClickId = ref<string | null>(null)

function getAllVisibleIds(): string[] {
  const ids: string[] = []
  if (props.tab.viewMode === 'home') {
    for (const c of favoriteConfigs.value) ids.push('fav:' + c.id)
    for (const c of recentConfigs.value) ids.push('recent:' + c.id)
  }
  for (const { config } of filteredConnections.value) ids.push('conn:' + config.id)
  return ids
}

function cardKeyToId(key: string): string {
  const idx = key.indexOf(':')
  return idx >= 0 ? key.slice(idx + 1) : key
}

function getSelectedConnectionIds(): string[] {
  if (selectedIds.value.size > 0) {
    // Deduplicate by config ID (one connection may be selected via multiple cards)
    const seen = new Set<string>()
    const ids: string[] = []
    for (const key of selectedIds.value) {
      const id = cardKeyToId(key)
      if (!seen.has(id)) {
        seen.add(id)
        ids.push(id)
      }
    }
    return ids
  }
  if (contextMenuConfig.value) return [contextMenuConfig.value.id]
  return []
}

// ── Search & filter ──
const searchQuery = ref('')
const selectedTypeFilter = ref('all')
const searchInputRef = ref<HTMLInputElement>()

const filterDisplay = computed(() => {
  if (selectedTypeFilter.value === 'all') return t('sidebar.filterAll')
  return connTypeLabel(selectedTypeFilter.value) || formatTypeFilterLabel(selectedTypeFilter.value)
})

const filterMenuRef = ref<InstanceType<typeof TypeFilterMenu> | null>(null)

const shellMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const shellMenuVisible = ref(false)
// Local terminals spawn a host shell, which does not exist on android/ios.
const isMobile = isMobilePlatform()

// ── Shell label helper ──
function getShellLabel(path: string): string {
  return getShellLabelBase(path, 'Local')
}

// ── Recent connections ──
const recentConnectionIds = ref<string[]>([])

async function loadRecent() {
  try {
    recentConnectionIds.value = await GetRecentConnections()
  } catch {
    recentConnectionIds.value = []
  }
}
loadRecent()

// Refresh the recent list when connections are added/removed, so a newly
// created connection shows up in "Recent" without requiring a reload.
watch(
  () => connectionStore.connections.map(c => c.id),
  () => loadRecent()
)

const recentConfigs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return recentConnectionIds.value
    .map(id => connectionStore.connections.find(c => c.id === id))
    .filter((c): c is ConnectionConfig => !!c)
    .filter(c => matchTypeFilter(c, selectedTypeFilter.value))
    .filter(c => !query ||
      c.name.toLowerCase().includes(query) ||
      (c.host || '').toLowerCase().includes(query) ||
      c.type.toLowerCase().includes(query))
    .slice(0, 12)
})

// ── Favorite connections (favorites.json, ordered) ──
// Mirrors recentConfigs' filtering; ids of deleted connections are dropped.
const favoriteConfigs = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return favoriteStore.favoriteIds
    .map(id => connectionStore.connections.find(c => c.id === id))
    .filter((c): c is ConnectionConfig => !!c)
    .filter(c => matchTypeFilter(c, selectedTypeFilter.value))
    .filter(c => !query ||
      c.name.toLowerCase().includes(query) ||
      (c.host || '').toLowerCase().includes(query) ||
      c.type.toLowerCase().includes(query))
})

// ── Filtered connections ──
const filteredConnections = computed(() => {
  let conns = connectionStore.connections

  if (props.tab.viewMode === 'group' && props.tab.groupId) {
    if (props.tab.groupId === '__ungrouped__') {
      conns = conns.filter(c => !c.groupId)
    } else {
      conns = conns.filter(c => c.groupId === props.tab.groupId)
    }
  }

  const query = searchQuery.value.trim().toLowerCase()

  return conns
    .filter(c => matchTypeFilter(c, selectedTypeFilter.value))
    .filter(c => !query ||
      c.name.toLowerCase().includes(query) ||
      (c.host || '').toLowerCase().includes(query) ||
      c.type.toLowerCase().includes(query))
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(c => ({ config: c }))
})

// ── Groups ──
const groupCards = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const hasFilter = !!query || selectedTypeFilter.value !== 'all'
  const matchFilter = (c: ConnectionConfig) =>
    matchTypeFilter(c, selectedTypeFilter.value) &&
    (!query || c.name.toLowerCase().includes(query) || (c.host || '').toLowerCase().includes(query) || c.type.toLowerCase().includes(query))

  // In-group view: show child groups, or only connections for ungrouped
  const isGroupView = props.tab.viewMode === 'group' && !!props.tab.groupId
  const parentFilter = isGroupView
    ? props.tab.groupId === '__ungrouped__'
      ? (() => false) as any
      : (g: ConnectionGroup) => g.parentId === props.tab.groupId
    : (g: ConnectionGroup) => !g.parentId

  // Recursive subtree count
  function subtreeMatchCount(groupId: string): number {
    let count = connectionStore.connections.filter(c => c.groupId === groupId && matchFilter(c)).length
    for (const child of connectionStore.groups.filter(cg => cg.parentId === groupId)) {
      count += subtreeMatchCount(child.id)
    }
    return count
  }

  let groups = [...connectionStore.groups]
    .filter(parentFilter)
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(g => ({
      ...g,
      count: subtreeMatchCount(g.id)
    }))
  if (hasFilter) {
    groups = groups.filter(g => g.count > 0)
  }

  // Connection count for current view
  const connFilter = isGroupView
    ? props.tab.groupId === '__ungrouped__'
      ? (c: ConnectionConfig) => !c.groupId && matchFilter(c)
      : (c: ConnectionConfig) => c.groupId === props.tab.groupId && matchFilter(c)
    : (c: ConnectionConfig) => !c.groupId && matchFilter(c)
  const ungroupedCount = connectionStore.connections.filter(connFilter).length

  return { groups, ungroupedCount, isGroupView, currentGroupId: props.tab.groupId }
})


// ── Navigation ──
function onCardClick(config: ConnectionConfig, e: MouseEvent, prefix = 'conn:') {
  const key = prefix + config.id
  if (e.shiftKey && lastClickId.value) {
    const ids = getAllVisibleIds()
    const anchorIdx = ids.indexOf(lastClickId.value)
    const currentIdx = ids.indexOf(key)
    if (anchorIdx >= 0 && currentIdx >= 0) {
      const [start, end] = anchorIdx < currentIdx ? [anchorIdx, currentIdx] : [currentIdx, anchorIdx]
      const set = new Set<string>()
      for (let i = start; i <= end; i++) set.add(ids[i])
      selectedIds.value = set
    }
  } else if (e.ctrlKey || e.metaKey) {
    if (selectedIds.value.has(key)) {
      selectedIds.value.delete(key)
    } else {
      selectedIds.value.add(key)
    }
    selectedIds.value = new Set(selectedIds.value)
    lastClickId.value = key
  } else {
    selectedIds.value = new Set([key])
    lastClickId.value = key
  }
  const idx = focusableIndexMap.value.get(prefix + config.id)
  if (idx !== undefined) {
    focusedCardIndex.value = idx
    focusInGrid.value = true
  }
}

function onGroupClick(groupId: string) {
  const idx = focusableIndexMap.value.get('group:' + groupId)
  if (idx !== undefined) {
    focusedCardIndex.value = idx
    focusInGrid.value = true
    startTabRef.value?.focus()
  }
}

function onQuickClick() {
  const idx = focusableIndexMap.value.get('quick')
  if (idx !== undefined) {
    focusedCardIndex.value = idx
    focusInGrid.value = true
    startTabRef.value?.focus()
  }
}

function onCardDblClick(config: ConnectionConfig, e?: { ctrlKey?: boolean; metaKey?: boolean }) {
  emit('connect', config, e ? !!(e.ctrlKey || e.metaKey) : false)
}

function enterGroup(groupId: string) {
  props.tab.viewMode = 'group'
  props.tab.groupId = groupId
  focusedCardIndex.value = 0
  focusInGrid.value = true
}

// Breadcrumb: full path from root to current group
const breadcrumbPath = computed(() => {
  const path: { id: string; name: string }[] = []
  if (!props.tab.groupId || props.tab.groupId === '__ungrouped__') return path
  let currentId: string | undefined = props.tab.groupId
  while (currentId) {
    const g = connectionStore.groups.find(g => g.id === currentId)
    if (!g) break
    path.unshift({ id: g.id, name: g.name })
    currentId = g.parentId
  }
  return path
})

function enterGroupAt(groupId: string) {
  if (groupId === props.tab.groupId) return
  props.tab.groupId = groupId
  focusedCardIndex.value = 0
}

function goParent() {
  if (!props.tab.groupId || props.tab.groupId === '__ungrouped__') {
    goHome()
    return
  }
  const currentGroup = connectionStore.groups.find(g => g.id === props.tab.groupId)
  if (currentGroup?.parentId) {
    props.tab.groupId = currentGroup.parentId
  } else {
    goHome()
  }
}

function goHome() {
  const returnGroupId = props.tab.groupId
  props.tab.viewMode = 'home'
  props.tab.groupId = undefined
  focusInGrid.value = true
  nextTick(() => {
    if (returnGroupId) {
      const idx = focusableIndexMap.value.get('group:' + returnGroupId)
      focusedCardIndex.value = idx ?? 0
    } else {
      focusedCardIndex.value = 0
    }
  })
}


// ── Content area centering ──
const startTabRef = ref<HTMLElement | null>(null)
const contentWidth = ref(0)

// Card geometry lives in CSS as rem values (.start-cards-grid 15rem cards,
// 0.75rem gap, .start-tab 4rem side padding) so it scales with the platform
// root font size. Derive the px constants from the live root font-size to
// keep this JS math in sync with the CSS on every platform.
const remPx = () => parseFloat(getComputedStyle(document.documentElement).fontSize)
const CARD_WIDTH = () => 15 * remPx()
const CARD_GAP = () => 0.75 * remPx()
const PADDING = () => 4 * remPx() // .start-tab padding on each side

// Column count derived from the same math as the wrapper width; kept as
// state so keyboard navigation and the CSS grid can never disagree.
const contentCols = ref(3)

function updateContentWidth() {
  const el = startTabRef.value
  if (!el) return
  const w = CARD_WIDTH()
  const g = CARD_GAP()
  const available = el.clientWidth - PADDING() * 2
  // Min 1 column: narrow phone screens can't fit two 15rem cards, so allow
  // a single centered column there (wide desktop windows still get >= 2).
  const cols = Math.max(1, Math.min(6, Math.floor((available + g) / (w + g))))
  contentCols.value = cols
  contentWidth.value = cols * w + (cols - 1) * g
  el.style.setProperty('--start-cols', String(cols))
}

const contentStyle = computed(() => ({
  width: contentWidth.value + 'px',
  margin: '0 auto'
}))

let resizeObserver: ResizeObserver | null = null

// ── Keyboard navigation ──
const focusedCardIndex = ref(-1)
const focusInGrid = ref(false)

type FocusableItem =
  | { kind: 'favorite'; config: ConnectionConfig }
  | { kind: 'recent'; config: ConnectionConfig }
  | { kind: 'group'; groupId: string; name: string }
  | { kind: 'connection'; config: ConnectionConfig }
  | { kind: 'quick' }

const focusableItems = computed<FocusableItem[]>(() => {
  if (props.tab.viewMode === 'group') {
    const items: FocusableItem[] = []
    for (const group of groupCards.value.groups) items.push({ kind: 'group', groupId: group.id, name: group.name })
    for (const { config } of filteredConnections.value) items.push({ kind: 'connection' as const, config })
    if (searchQuery.value.trim()) items.push({ kind: 'quick' })
    return items
  }
  const items: FocusableItem[] = []
  for (const config of favoriteConfigs.value) items.push({ kind: 'favorite', config })
  for (const config of recentConfigs.value) items.push({ kind: 'recent', config })
  for (const group of groupCards.value.groups) items.push({ kind: 'group', groupId: group.id, name: group.name })
  if (groupCards.value.ungroupedCount > 0) items.push({ kind: 'group', groupId: '__ungrouped__', name: t('conn.noGroup') })
  for (const { config } of filteredConnections.value) items.push({ kind: 'connection', config })
  if (searchQuery.value.trim()) items.push({ kind: 'quick' })
  return items
})

const focusableIndexMap = computed(() => {
  const map = new Map<string, number>()
  focusableItems.value.forEach((item, idx) => {
    if (item.kind === 'favorite') map.set('fav:' + item.config.id, idx)
    else if (item.kind === 'recent') map.set('recent:' + item.config.id, idx)
    else if (item.kind === 'connection') map.set('conn:' + item.config.id, idx)
    else if (item.kind === 'group') map.set('group:' + item.groupId, idx)
    else if (item.kind === 'quick') map.set('quick', idx)
  })
  return map
})

function isCardFocused(key: string): boolean {
  if (!focusInGrid.value) return false
  const idx = focusableIndexMap.value.get(key)
  return idx === focusedCardIndex.value
}

function getGridColumns(): number {
  if (contentWidth.value === 0) return 3
  return contentCols.value
}

function onSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Tab' || e.key === 'ArrowDown') {
    e.preventDefault()
    e.stopPropagation()
    searchInputRef.value?.blur()
    focusInGrid.value = true
    focusedCardIndex.value = 0
    return
  }
}

function onKeydown(e: KeyboardEvent) {
  // Don't handle keyboard navigation when a dialog is open
  if (showNewGroupDialog.value || showDeleteGroupDialog.value) return
  // Don't intercept keyboard events from modal dialogs (e.g. ConnectionForm)
  if ((e.target as HTMLElement)?.closest?.('.el-dialog')) return
  // Only handle when this component is mounted and this tab is active
  if (!startTabRef.value) return
  if (tabStore.activeTabId !== props.tab.id) return
  if (e.key === 'Tab') {
    e.preventDefault()
    if (focusInGrid.value) {
      focusInGrid.value = false
      focusedCardIndex.value = -1
      searchInputRef.value?.focus()
    } else {
      focusInGrid.value = true
      focusedCardIndex.value = 0
    }
    return
  }

  if (e.key === 'Escape' && props.tab.viewMode === 'group') {
    goHome()
  }
  if (e.key === 'Backspace' && props.tab.viewMode === 'group') {
    goParent()
    focusedCardIndex.value = 0
    focusInGrid.value = true
    return
  }

  if (!focusInGrid.value) return

  const cols = getGridColumns()
  const items = focusableItems.value
  const total = items.length
  if (total === 0) return

  // Section boundaries: indices where kind changes
  const sectionStarts: number[] = [0]
  for (let i = 1; i < total; i++) {
    if (items[i].kind !== items[i - 1].kind) sectionStarts.push(i)
  }

  function sectionOf(idx: number) {
    for (let s = sectionStarts.length - 1; s >= 0; s--) {
      if (idx >= sectionStarts[s]) return s
    }
    return 0
  }

  if (e.key === 'ArrowRight') {
    e.preventDefault()
    focusedCardIndex.value = Math.min(focusedCardIndex.value + 1, total - 1)
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    focusedCardIndex.value = Math.max(focusedCardIndex.value - 1, 0)
  } else if (e.key === 'ArrowUp' && focusedCardIndex.value === 0) {
    e.preventDefault()
    focusInGrid.value = false
    focusedCardIndex.value = -1
    searchInputRef.value?.focus()
    return
  } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    const cur = focusedCardIndex.value
    const curSection = sectionOf(cur)
    const curStart = sectionStarts[curSection]
    const curEnd = curSection + 1 < sectionStarts.length ? sectionStarts[curSection + 1] : total
    const visualCol = (cur - curStart) % cols
    const dir = e.key === 'ArrowDown' ? 1 : -1

    // Stay in current section if possible
    const sameSectionTarget = cur + dir * cols
    if (sameSectionTarget >= curStart && sameSectionTarget < curEnd) {
      focusedCardIndex.value = sameSectionTarget
    } else {
      // Cross to next/prev section, align to same visual column
      const nextSection = curSection + dir
      if (nextSection < 0) {
        focusedCardIndex.value = Math.max(cur - cols, 0)
      } else if (nextSection >= sectionStarts.length) {
        focusedCardIndex.value = Math.min(cur + cols, total - 1)
      } else {
        const secStart = sectionStarts[nextSection]
        const secEnd = nextSection + 1 < sectionStarts.length ? sectionStarts[nextSection + 1] : total
        const secLen = secEnd - secStart
        const lastRowStart = secStart + Math.floor((secLen - 1) / cols) * cols
        const rowTarget = dir === 1 ? secStart : lastRowStart
        const target = Math.min(rowTarget + visualCol, secEnd - 1)
        focusedCardIndex.value = target
      }
    }
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const ids = getSelectedConnectionIds()
    if (ids.length > 1) {
      // Bulk connect: open all selected connections
      const configs = ids.map(id => connectionStore.connections.find(c => c.id === id)).filter(Boolean) as ConnectionConfig[]
      for (const c of configs) {
        emit('connect', c, e.ctrlKey || e.metaKey)
      }
      selectedIds.value = new Set()
    } else {
      const item = focusableItems.value[focusedCardIndex.value]
      if (!item) return
      if (item.kind === 'recent' || item.kind === 'favorite' || item.kind === 'connection') {
        onCardDblClick(item.config, e)
      } else if (item.kind === 'group') {
        enterGroup(item.groupId)
      } else if (item.kind === 'quick') {
        emit('new-connection', { host: searchQuery.value.trim() })
      }
    }
  }
}

// ── Context menu ──
const contextMenuVisible = ref(false)
const contextMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const contextMenuConfig = ref<ConnectionConfig | null>(null)

function closeContextMenu() {
  contextMenuVisible.value = false
}

function onContextMenu(e: MouseEvent, config: ConnectionConfig, prefix = 'conn:') {
  // If right-clicking an unselected item, replace selection with this card
  const key = prefix + config.id
  if (!selectedIds.value.has(key)) {
    selectedIds.value = new Set([key])
  }
  contextMenuConfig.value = config
  contextMenuRef.value?.openAt(e.clientX, e.clientY, config)
}

function onCardMoreClick(e: MouseEvent, config: ConnectionConfig, prefix = 'conn:') {
  const btn = e.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  const x = rect.right + 4
  const y = rect.top
  const key = prefix + config.id
  if (!selectedIds.value.has(key)) {
    selectedIds.value = new Set([key])
  }
  contextMenuConfig.value = config
  contextMenuRef.value?.openAt(x, y, config)
}

// ── Group context menu ──
const groupMenuVisible = ref(false)
const groupMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const groupContextTarget = ref<{ id: string; name: string } | null>(null)

function closeGroupContextMenu() {
  groupMenuVisible.value = false
}

function onGroupContextMenu(e: MouseEvent, groupId: string, groupName: string) {
  groupContextTarget.value = { id: groupId, name: groupName }
  groupMenuRef.value?.openAt(e.clientX, e.clientY, { id: groupId, name: groupName })
}

const showRenameGroupDialog = ref(false)
const showNewGroupDialog = ref(false)
const newGroupParentId = ref<string | undefined>(undefined)

function doRenameGroup() {
  if (!groupContextTarget.value) return
  closeGroupContextMenu()
  showRenameGroupDialog.value = true
}

function openNewGroupDialog() {
  // Pre-set parent to current group if in a group view
  newGroupParentId.value = (props.tab.viewMode === 'group' && props.tab.groupId && props.tab.groupId !== '__ungrouped__')
    ? props.tab.groupId
    : undefined
  showNewGroupDialog.value = true
}

// Group context menu: New Group (child of current)
function doNewGroupFromCtx() {
  if (!groupContextTarget.value) return
  closeGroupContextMenu()
  newGroupParentId.value = groupContextTarget.value.id
  showNewGroupDialog.value = true
}

// Group context menu: New Connection in group
function doNewConnInGroup() {
  if (!groupContextTarget.value) return
  closeGroupContextMenu()
  emit('new-connection', { groupId: groupContextTarget.value.id })
}

function doChangeGroupParent() {
  if (!groupContextTarget.value) return
  closeGroupContextMenu()
  emit('change-group-parent', groupContextTarget.value.id)
}

const showDeleteGroupDialog = ref(false)
const deleteGroupTarget = ref<ConnectionGroup | null>(null)

async function doDeleteGroup() {
  if (!groupContextTarget.value) return
  closeGroupContextMenu()
  const g = groupContextTarget.value
  const connCount = connectionStore.connections.filter(c => c.groupId === g.id).length
  const childCount = connectionStore.groups.filter(cg => cg.parentId === g.id).length
  if (connCount === 0 && childCount === 0) {
    await connectionStore.deleteGroup(g.id, 'move-out')
    return
  }
  deleteGroupTarget.value = g
  showDeleteGroupDialog.value = true
}

async function confirmDeleteGroup(action: 'delete-connections' | 'move-out') {
  if (deleteGroupTarget.value) {
    await connectionStore.deleteGroup(deleteGroupTarget.value.id, action)
  }
  showDeleteGroupDialog.value = false
  deleteGroupTarget.value = null
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  updateContentWidth()
  if (startTabRef.value) {
    resizeObserver = new ResizeObserver(() => updateContentWidth())
    resizeObserver.observe(startTabRef.value)
  }
  nextTick(() => searchInputRef.value?.focus())
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  resizeObserver?.disconnect()
})

// Context menu actions
// Resolved multi-select targets for the shared context menu (always includes
// the right-clicked connection).
const ctxTargets = computed<ConnectionConfig[]>(() => {
  const conns = getSelectedConnectionIds()
    .map(id => connectionStore.connections.find(c => c.id === id))
    .filter(Boolean) as ConnectionConfig[]
  if (conns.length > 0) return conns
  return contextMenuConfig.value ? [contextMenuConfig.value] : []
})

// Route one connect per target through the unified entries. Companion kinds
// still ride the app:connect-* window events (App owns the launcher wiring);
// plain connects emit to App with ctrl/meta = keep the start tab open.
function onCtxConnect(targets: ConnectionConfig[], kind: 'file' | 'wsl-file' | 'monitor' | undefined, event?: MouseEvent) {
  for (const c of targets) {
    if (kind === 'file') window.dispatchEvent(new CustomEvent('app:connect-sftp', { detail: c }))
    else if (kind === 'monitor') window.dispatchEvent(new CustomEvent('app:connect-monitor', { detail: c }))
    else if (kind === 'wsl-file') window.dispatchEvent(new CustomEvent('app:connect-wsl-file', { detail: c }))
    else emit('connect', c, event ? !!(event.ctrlKey || event.metaKey) : false)
  }
}

function onCtxConnectToWorkspace(targets: ConnectionConfig[], workspaceId: string) {
  emit('connect-to-workspace', { configs: targets, workspaceId })
}

function onCtxCreateWorkspace(targets: ConnectionConfig[]) {
  emit('create-workspace', targets)
}

function onCtxChangeGroup(targets: ConnectionConfig[]) {
  emit('change-group-ids', targets.map(c => c.id))
}

function onCtxDelete(targets: ConnectionConfig[]) {
  connectionStore.removeMany(targets.map(c => c.id))
  selectedIds.value = new Set()
}

function onRenameGroupConfirm(name: string) {
  if (!groupContextTarget.value) return
  connectionStore.renameGroup(groupContextTarget.value.id, name)
}

function onAddGroupConfirm(name: string, parentId: string | undefined) {
  connectionStore.addGroup(name, parentId)
}

function doEditConnection(config: ConnectionConfig | null) {
  if (!config) return
  closeContextMenu()
  emit('edit-connection', config)
}



</script>

<style scoped>
.start-tab {
  padding: 2rem 4rem 2rem 4rem;
  height: 100%;
  overflow-y: auto;
  outline: none;
}

.start-content {
  margin: 0 auto;
}

.start-brand {
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  margin-top: 4rem;
  margin-bottom: 2.25rem;
  user-select: none;
}

.start-search-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 1.25rem;
}

.start-filter-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8125rem;
  white-space: nowrap;
  user-select: none;
}
.start-filter-btn:hover,
.start-filter-btn.active {
  background: var(--bg-hover);
  color: var(--accent);
}

.start-search-input {
  flex: 1;
}
</style>

<style>
.start-search-input .el-input__wrapper {
  background-color: var(--bg-surface) !important;
  box-shadow: 0 0 0 1px var(--border-subtle) inset !important;
  padding: 0.25rem 0.875rem !important;
  border-radius: var(--radius-md) !important;
}
.start-search-input .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--accent) inset !important;
}
.start-search-input .el-input__inner {
  font-family: inherit !important;
  font-size: 0.8125rem !important;
  color: var(--text-primary) !important;
}
.start-search-input .el-input__inner::placeholder {
  color: var(--text-disabled) !important;
}

.start-action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.625rem;
  margin-bottom: 1.75rem;
  align-items: flex-start;
}

.start-action-btn {
  flex-shrink: 0;
  white-space: nowrap;
  padding: 0.5rem 1.25rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  transition: background 0.15s;
}
.start-action-btn:hover {
  background: var(--bg-hover);
}
.start-action-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--bg-base);
}
.start-action-btn.primary:hover {
  filter: brightness(0.9);
}

.start-action-btn-group {
  display: flex;
  align-items: stretch;
  flex-shrink: 0;
}

.start-action-btn-group > .start-action-btn {
  border-radius: var(--radius-md) 0 0 var(--radius-md);
  border-right: none;
}

.start-action-btn-dropdown-arrow {
  padding: 0.5rem 0.625rem;
  border: 1px solid var(--border-subtle);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.start-action-btn-dropdown-arrow:hover {
  background: var(--bg-hover);
}

.start-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  margin-bottom: 0.625rem;
  font-size: 0.75rem;
  color: var(--text-disabled);
}
.start-breadcrumb .link {
  color: var(--accent);
  cursor: pointer;
}
.start-breadcrumb .link:hover {
  text-decoration: underline;
}
.start-breadcrumb .sep {
  color: var(--text-disabled);
}
.start-breadcrumb .current {
  color: var(--text-primary);
  font-weight: 600;
}

.start-section-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-disabled);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 1.5rem;
  margin-bottom: 0.625rem;
}
.start-add-group-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.125rem;
  height: 1.125rem;
  border-radius: 0.25rem;
  cursor: pointer;
  color: var(--text-disabled);
  transition: background 0.15s, color 0.15s;
}
.start-add-group-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.start-divider {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 1.25rem 0;
}

.start-cards-grid {
  display: grid;
  grid-template-columns: repeat(var(--start-cols, auto-fill), 15rem);
  gap: 0.75rem;
}

.start-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s;
  width: 15rem;
}
.start-card:hover {
  border-color: var(--accent);
}
.card-more-btn {
  display: none;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: 0.375rem;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border: none;
  background: var(--bg-elevated);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  padding: 0;
  z-index: 2;
}
.start-card:hover .card-more-btn {
  display: flex;
}
.card-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
/* Favorite toggle on cards: rests at the card's right edge; when the card is
   hovered the more button takes the edge and pushes the star left. Revealed
   on hover and stays visible (amber) while favorited. */
.card-fav-btn {
  display: flex;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: 0.375rem;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  border: none;
  background: var(--bg-elevated);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  padding: 0;
  z-index: 2;
  opacity: 0;
  pointer-events: none;
  transition: right 0.12s ease, opacity 0.12s ease;
}
.start-card:hover .card-fav-btn {
  right: 2.25rem;
  opacity: 1;
  pointer-events: auto;
}
.card-fav-btn.on {
  opacity: 1;
  pointer-events: auto;
}
.card-fav-btn.on {
  color: var(--warning);
}
/* Inside the favorites section: hover reveals the star already lit */
.card-fav-btn.lit,
.card-fav-btn.lit:hover {
  color: var(--warning);
}
.card-fav-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.start-card.dimmed {
  opacity: 0.35;
}
.start-card.focused {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}
.start-card.selected {
  border-color: var(--accent);
  background: var(--accent-subtle);
}

.start-card-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}
.start-card-top > div:last-child {
  overflow: hidden;
  min-width: 0;
  flex: 1;
}

.start-card-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.4375rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.375rem;
  background: var(--bg-overlay);
  color: var(--text-secondary);
}
.start-card-icon.ssh,
.start-card-icon.telnet,
.start-card-icon.mosh { color: var(--accent); }
.start-card-icon.local { color: var(--success); }
.start-card-icon.database { color: var(--warning); }
.start-card-icon.rdp,
.start-card-icon.vnc,
.start-card-icon.spice { color: var(--accent); }
.start-card-icon.k8s { color: var(--accent); }
.start-card-icon.serial { color: var(--success-dim); }
.start-card-icon.group { color: var(--text-secondary); }
.start-card-icon.ungrouped { color: var(--text-muted); }
.start-card-icon.quick { background: var(--accent-subtle); color: var(--accent); }

.start-card-name {
  font-weight: 600;
  font-size: 0.75rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 10.75rem;
}
.start-card-meta {
  margin-top: 0.1875rem;
  font-size: 0.625rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.start-quick-card {
  background: transparent;
  border: 1px dashed var(--accent);
  border-radius: var(--radius-lg);
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background 0.15s;
  margin-top: 0.75rem;
  width: 15rem;
}
.start-quick-card.focused {
  border-style: solid;
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}
.start-quick-card:hover {
  background: var(--accent-subtle);
}
.quick-name {
  color: var(--accent);
}

.start-empty-hint,
.start-empty-state {
  text-align: center;
  color: var(--text-disabled);
  font-size: 0.875rem;
  margin-top: 3rem;
}
.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
  opacity: 0.3;
}

</style>
