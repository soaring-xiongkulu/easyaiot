<template>
  <div
    ref="sidebarEl"
    class="sidebar"
    :class="{ collapsed: !visible, resizing: isResizing }"
    :style="{ width: sidebarWidth + 'px' }"
  >
    <div class="resize-handle" @mousedown="onResizeStart" />
    <div class="sidebar-header" @contextmenu.prevent="onTabStripContextMenu">
      <button class="sidebar-tab" :class="{ active: activeView === 'connections' }" @click="activeView = 'connections'" :title="t('header.connections')"><el-icon><Network :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('files')" class="sidebar-tab" :class="{ active: activeView === 'files' }" @click="onFilesTabClick" :title="t('header.files')"><el-icon><FolderTree :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('monitor')" class="sidebar-tab" :class="{ active: activeView === 'monitor' }" @click="onMonitorTabClick" :title="t('header.monitor')"><el-icon><Activity :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('tunnels')" class="sidebar-tab" :class="{ active: activeView === 'tunnels' }" @click="activeView = 'tunnels'" :title="t('tunnels.tunnelsTab')"><el-icon><ArrowRightLeft :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('quickCommands')" class="sidebar-tab" :class="{ active: activeView === 'quickCommands' }" @click="activeView = 'quickCommands'" :title="quickCommandsTitle"><el-icon><Zap :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('history')" class="sidebar-tab" :class="{ active: activeView === 'history' }" @click="activeView = 'history'" :title="t('quickCommands.historyTab')"><el-icon><Clock :size="'0.875rem'" /></el-icon></button>
      <button v-if="tabVisible('personalization')" class="sidebar-tab" :class="{ active: activeView === 'personalization' }" @click="activeView = 'personalization'" :title="t('sidebar.personalization')"><el-icon><Palette :size="'0.875rem'" /></el-icon></button>
      <button class="icon-btn" @click="emit('toggle')" :title="t('sidebar.collapse')"><el-icon><X :size="'0.875rem'" /></el-icon></button>
    </div>

    <template v-if="activeView === 'connections'">
      <div class="search-box">
        <el-input
          ref="searchInputRef"
          v-model="searchQuery"
          :placeholder="t('sidebar.searchPlaceholder')"
          clearable
          @keydown="onListKeydown"
        >
          <template #suffix>
            <span class="filter-trigger" :class="{ active: selectedTypeFilter !== 'all' }" @click.stop="filterMenuRef?.toggle($event.currentTarget)">
              <el-icon><Filter :size="'0.875rem'" /></el-icon>
            </span>
            <TypeFilterMenu ref="filterMenuRef" align="end" v-model="selectedTypeFilter" />
          </template>
        </el-input>
        <button class="sb-icon-btn" :title="t('header.newConnection')" @click.stop="newConnMenuRef?.toggle($event.currentTarget)">
          <Plus :size="'0.9375rem'" />
        </button>
        <!-- New-connection menu — Menu.vue, teleported + anchored right-edge (align=end). -->
        <Menu ref="newConnMenuRef" align="end" v-model:visible="showNewConnMenu">
          <MenuItem @click="onNewConnSelect('new-connection')">{{ t('header.newConnection') }}</MenuItem>
          <MenuItem @click="onNewConnSelect('new-group')">{{ t('conn.newGroupTitle') }}</MenuItem>
          <MenuDivider />
          <MenuItem @click="onNewConnSelect('import')">{{ t('importExport.import') }}</MenuItem>
          <MenuItem @click="onNewConnSelect('export')">{{ t('importExport.export') }}</MenuItem>
        </Menu>
      </div>

    <div class="connection-list" tabindex="0" @keydown="onListKeydown" @contextmenu.prevent="onEmptyAreaContextMenu">
      <!-- Virtual favorites group — persisted in favorites.json, rendered above all groups -->
      <template v-if="favoriteConns.length > 0">
        <div class="group-header" @click="favoritesExpanded = !favoritesExpanded" @contextmenu.prevent>
          <span class="group-arrow">
            <el-icon v-if="favoritesExpanded"><ChevronDown :size="'0.875rem'" /></el-icon>
            <el-icon v-else><ChevronRight :size="'0.875rem'" /></el-icon>
          </span>
          <span class="group-name">{{ t('sidebar.favorites') }}</span>
          <span class="group-count">{{ favoriteConns.length }}</span>
        </div>
        <template v-if="favoritesExpanded">
          <div
            v-for="conn in favoriteConns"
            :key="conn.id"
            class="connection-item indented"
            :data-conn-id="conn.id"
            :class="{
              active: selectedIds.has(conn.id),
              'has-session': openPanelConnIds.has(conn.id),
              'drop-before': dropIndicator?.id === conn.id && dropIndicator?.position === 'before',
              'drop-after': dropIndicator?.id === conn.id && dropIndicator?.position === 'after',
            }"
            draggable="true"
            @dragstart="onDragStart($event, conn)"
            @dragend="onDragEnd"
            @dragover.prevent="onFavDragOver($event, conn)"
            @drop.prevent="onFavDrop($event, conn)"
            @click="onItemClick($event, conn)"
            @dblclick="onItemDblClick(conn)"
            @contextmenu.prevent="onContextMenu($event, conn)"
          >
            <span class="conn-icon"><component :is="connIcon(conn)" :size="'0.875rem'" /></span>
            <div class="conn-details">
              <span class="name">{{ conn.name }}</span>
              <span class="conn-meta">
                <span class="host">{{ getSubtitle(conn) }}</span>
              </span>
            </div>
            <!-- Inside the favorites group the star is hover-only (everything
                 here is favorited; a lit star would be redundant noise) -->
            <button v-if="showHostRowButtons" class="conn-fav-btn lit" :title="t('sidebar.removeFromFavorites')" @click.stop="favoriteStore.toggle(conn.id)"><Star :size="'0.75rem'" /></button>
            <button v-if="showHostRowButtons" class="conn-more-btn" @click.stop="onConnMoreClick($event, conn)" :title="t('terminal.more')"><MoreHorizontal :size="'0.875rem'" /></button>
          </div>
        </template>
      </template>

      <!-- Nested group tree -->
      <GroupTreeItem
        v-for="root in filteredGrouped.roots"
        :key="root.group.id"
        :node="root"
        :depth="0"
      />

      <!-- Virtual (No Group) group - only when real groups exist -->
      <template v-if="connectionStore.groups.length > 0 && filteredGrouped.ungrouped.length > 0">
        <div
          class="group-header"
          :class="{ 'drag-over': dragOverGroupId === '__ungrouped__' }"
          @click="toggleGroup('__ungrouped__')"
          @contextmenu.prevent="onVirtualGroupContextMenu($event)"
          @dragover.prevent="onGroupDragOver('__ungrouped__', $event)"
          @dragleave="onGroupDragLeave('__ungrouped__')"
          @drop.prevent="onGroupDrop('__ungrouped__', $event)"
        >
          <span class="group-arrow">
            <el-icon v-if="expandedGroups.has('__ungrouped__')"><ChevronDown :size="'0.875rem'" /></el-icon>
            <el-icon v-else><ChevronRight :size="'0.875rem'" /></el-icon>
          </span>
          <span class="group-name">{{ t('conn.noGroup') }}</span>
          <span v-if="filteredGrouped.ungrouped.length > 0" class="group-count">{{ filteredGrouped.ungrouped.length }}</span>
        </div>
        <template v-if="expandedGroups.has('__ungrouped__')">
          <div
            v-for="conn in filteredGrouped.ungrouped"
            :key="conn.id"
            class="connection-item indented"
            :data-conn-id="conn.id"
            :class="{
              active: selectedIds.has(conn.id),
              'has-session': openPanelConnIds.has(conn.id),
              'drop-before': dropIndicator?.id === conn.id && dropIndicator?.position === 'before',
              'drop-after': dropIndicator?.id === conn.id && dropIndicator?.position === 'after',
            }"
            draggable="true"
            @dragstart="onDragStart($event, conn)"
            @dragend="onDragEnd"
            @dragover.prevent="onConnDragOver($event, conn)"
            @drop.prevent="onConnDrop($event, conn)"
            @click="onItemClick($event, conn)"
            @dblclick="onItemDblClick(conn)"
            @contextmenu.prevent="onContextMenu($event, conn)"
          >
            <span class="conn-icon"><component :is="connIcon(conn)" :size="'0.875rem'" /></span>
            <div class="conn-details">
              <span class="name">{{ conn.name }}</span>
              <span class="conn-meta">
                <span class="host">{{ getSubtitle(conn) }}</span>
              </span>
            </div>
            <button v-if="showHostRowButtons" class="conn-fav-btn" :class="{ on: favoriteStore.isFavorite(conn.id) }" :title="favoriteStore.isFavorite(conn.id) ? t('sidebar.removeFromFavorites') : t('sidebar.addToFavorites')" @click.stop="favoriteStore.toggle(conn.id)"><Star :size="'0.75rem'" /></button>
            <button v-if="showHostRowButtons" class="conn-more-btn" @click.stop="onConnMoreClick($event, conn)" :title="t('terminal.more')"><MoreHorizontal :size="'0.875rem'" /></button>
          </div>
        </template>
      </template>

      <!-- Flat ungrouped connections (only when no real groups exist) -->
      <template v-if="connectionStore.groups.length === 0">
        <div
          v-for="conn in filteredGrouped.ungrouped"
          :key="conn.id"
          class="connection-item"
          :data-conn-id="conn.id"
          :class="{
            active: selectedIds.has(conn.id),
            'has-session': openPanelConnIds.has(conn.id),
            'drop-before': dropIndicator?.id === conn.id && dropIndicator?.position === 'before',
            'drop-after': dropIndicator?.id === conn.id && dropIndicator?.position === 'after',
          }"
          draggable="true"
          @dragstart="onDragStart($event, conn)"
          @dragend="onDragEnd"
          @dragover.prevent="onConnDragOver($event, conn)"
          @drop.prevent="onConnDrop($event, conn)"
          @click="onItemClick($event, conn)"
          @dblclick="onItemDblClick(conn)"
          @contextmenu.prevent="onContextMenu($event, conn)"
        >
          <span class="conn-icon"><component :is="connIcon(conn)" :size="'0.875rem'" /></span>
          <div class="conn-details">
            <span class="name">{{ conn.name }}</span>
            <span class="conn-meta">
              <span class="host">{{ getSubtitle(conn) }}</span>
            </span>
          </div>
          <button v-if="showHostRowButtons" class="conn-more-btn" @click.stop="onConnMoreClick($event, conn)" :title="t('terminal.more')"><MoreHorizontal :size="'0.875rem'" /></button>
        </div>
      </template>

      <!-- Virtual "New Connection..." when searching -->
      <div
        v-if="searchQuery.trim()"
        class="connection-item virtual-new-conn"
        :class="{ active: focusedId === '__new_connection__' }"
        @click="focusedId = '__new_connection__'; selectedIds = new Set(); lastClickId = '__new_connection__'"
        @dblclick="openNewFormFromSearch"
      >
        <div class="conn-details">
          <span class="name virtual-name">{{ t('sidebar.newConnectionFromSearch') }}</span>
          <span class="host">{{ t('conn.host') }}: {{ searchQuery.trim() }}</span>
        </div>
      </div>

      <div v-if="totalFiltered === 0 && connectionStore.connections.length > 0 && !searchQuery.trim()" class="empty-state">
        {{ t('sidebar.noSearchResults') }}
      </div>
      <div v-if="connectionStore.connections.length === 0" class="empty-state">
        {{ t('sidebar.noConnections') }}
      </div>
    </div>
    </template>

    <QuickCommandsPanel v-if="activeView === 'quickCommands'" ref="quickCommandsRef" />

    <TunnelsPanel v-if="activeView === 'tunnels'" />

    
    <HistoryPanel v-if="activeView === 'history'" />

    <FileSidebar v-if="activeView === 'files'" />

    <MonitorOverviewSidebar v-if="activeView === 'monitor'" />

    <template v-if="activeView === 'personalization'">
      <div class="personalization-panel">
        <div class="persist-section-title">{{ t('settings.app') }}</div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.theme') }}</div>
          <el-select v-model="settingsStore.settings.theme" @change="settingsStore.save()">
            <el-option :label="t('settings.themeDark')" value="dark" />
            <el-option :label="t('settings.themeDeepBlue')" value="deep-blue" />
            <el-option :label="t('settings.themeLight')" value="light" />
            <el-option :label="t('settings.themeSystem')" value="system" />
          </el-select>
        </div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.language') }}</div>
          <el-select :model-value="settingsStore.settings.language" @change="settingsStore.updateLanguage">
            <el-option
              v-for="lang in LANGUAGE_OPTIONS"
              :key="lang.value"
              :label="lang.native"
              :value="lang.value"
            />
            <el-option :label="t('settings.langSystem')" value="system" />
          </el-select>
        </div>
        <div class="persist-section-title">{{ t('settings.terminal') }}</div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.colorScheme') }}</div>
          <div class="theme-select-row">
            <el-select v-model="settingsStore.settings.terminal.theme" @change="settingsStore.save()" popper-class="theme-select-popper">
              <el-option :label="t('settings.followAppTheme')" :value="FOLLOW_APP_THEME" />
              <el-option-group v-for="group in terminalThemeGroups" :key="group.label" :label="group.label">
                <el-option v-for="th in group.options" :key="th.value" :label="th.label" :value="th.value" />
              </el-option-group>
            </el-select>
            <button class="btn btn-ghost btn-icon btn-sm" :title="t('theme.newTitle')" @click="openThemeEditor()">
              <Plus :size="'0.875rem'" />
            </button>
            <button
              v-if="isCustomTheme(settingsStore.settings.terminal.theme)"
              class="btn btn-ghost btn-icon btn-sm"
              :title="t('theme.editTitle')"
              @click="openThemeEditor(settingsStore.settings.terminal.theme)"
            >
              <Pencil :size="'0.875rem'" />
            </button>
          </div>
        </div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.fontPrimary') }}</div>
          <el-select v-model="settingsStore.settings.terminal.fontFamily" @change="settingsStore.save()">
            <template #header>
              <div style="padding:0.25rem 0.75rem">
                <el-checkbox v-model="fontMonoOnly" @click.stop>{{ t('settings.fontMonoOnly') }}</el-checkbox>
              </div>
            </template>
            <el-option
              v-for="f in personalizationFontOptions"
              :key="f.value"
              :label="f.label"
              :value="f.value"
              :style="{ fontFamily: formatFontFamily(f.value) }"
            />
          </el-select>
        </div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.fontFallback') }}</div>
          <el-select v-model="settingsStore.settings.terminal.fallbackFont" @change="settingsStore.save()">
            <template #header>
              <div style="padding:0.25rem 0.75rem">
                <el-checkbox v-model="fallbackFontMonoOnly" @click.stop>{{ t('settings.fontMonoOnly') }}</el-checkbox>
              </div>
            </template>
            <el-option value="" :label="t('settings.fontNone')" />
            <el-option
              v-for="f in personalizationFallbackFontOptions"
              :key="f.value"
              :label="f.label"
              :value="f.value"
              :style="{ fontFamily: formatFontFamily(f.value) }"
            />
          </el-select>
        </div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.fontWeight') }}</div>
          <el-select v-model="settingsStore.settings.terminal.fontWeight" @change="settingsStore.save()">
            <el-option
              v-for="w in FONT_WEIGHT_OPTIONS"
              :key="w.value"
              :label="t(w.labelKey)"
              :value="w.value"
            />
          </el-select>
        </div>
        <div class="persist-section">
          <div class="persist-label">{{ t('settings.fontSize') }}</div>
          <el-input-number
            v-model="settingsStore.settings.terminal.fontSize"
            :min="8"
            :max="32"
            @change="settingsStore.save()"
          />
        </div>
      </div>
    </template>

    <ConnectionForm v-model="showForm" :edit-config="editConfig" :default-group-id="newConnGroupId" @save="onSave" @connect="onConnectFromForm" @connect-only="(c: ConnectionConfig) => { showForm = false; editConfig = undefined; emit('connectOnly', c) }" />
    <ExportDialog v-model:visible="showExportDialog" />
    <ImportDialog v-model:visible="showImportDialog" />
    <CustomThemeEditor v-model="themeEditorVisible" :source-theme-id="themeEditorSourceId" />

    <!-- Tab-strip context menu: toggle which sidebar tabs are shown.
         Reuses the same AppSettings.sidebarTabs as the Settings page card.
         "connections" is fixed, so it is not listed. -->
    <Menu ref="tabStripMenuRef" v-model:visible="tabStripMenuVisible">
      <MenuItem
        v-for="tab in SIDEBAR_TAB_ORDER.filter(tab => tab.key !== 'connections')"
        :key="tab.key"
        iconic
        :icon="tabVisible(tab.key) ? Check : undefined"
        @click="onTabVisibilityClick(tab.key)"
      >{{ t(tab.labelKey) }}</MenuItem>
    </Menu>

    <!-- Connection context menu -->
    <ConnectionContextMenu
      ref="menuRef"
      :config="selectedConn"
      :targets="ctxTargets"
      v-model:visible="menuVisible"
      @connect="onCtxConnect"
      @connect-to-workspace="onCtxConnectToWorkspace"
      @create-workspace="onCtxCreateWorkspace"
      @edit="doEdit"
      @change-group="(targets: ConnectionConfig[]) => openChangeGroupFor(targets.map(c => c.id))"
      @new-group="() => doNewGroup(selectedGroupParentId())"
      @delete="onCtxDelete"
    />

    <!-- Group context menu -->
    <GroupContextMenu
      ref="groupMenuRef"
      :group="selectedGroup"
      v-model:visible="groupMenuVisible"
      @new-group="() => { if (selectedGroup) doNewGroup(selectedGroup.id) }"
      @new-connection="doNewConnInGroup"
      @rename="doRenameGroup"
      @change-parent="doChangeParentGroup"
      @delete-group="doDeleteGroup"
    />

    <!-- Empty area context menu -->
    <Menu ref="emptyAreaMenuRef" v-model:visible="emptyAreaMenuVisible">
      <MenuItem @click="doNewGroup()">{{ t('conn.newGroupTitle') }}</MenuItem>
    </Menu>

    <DeleteGroupDialog v-model:visible="showDeleteGroupDialog" :group="selectedGroup" @confirm="confirmDeleteGroup" />

    <RenameGroupDialog v-model:visible="showRenameGroupDialog" :name="selectedGroup?.name || ''" @confirm="confirmRenameGroup" />

    <!-- Move to dialog -->
    <el-dialog append-to-body v-model="showChangeGroupDialog" :title="t('conn.group')" width="25rem">
      <el-tree-select
        v-model="changeGroupTargetId"
        :data="groupTreeData"
        :render-after-expand="false"
        check-strictly
        clearable
        :placeholder="t('conn.noGroup')"
        style="width:100%"
      />
      <template #footer>
        <el-button @click="showChangeGroupDialog = false">{{ t('conn.cancel') }}</el-button>
        <el-button type="primary" @click="confirmChangeGroup">{{ t('conn.save') }}</el-button>
      </template>
    </el-dialog>

    <NewGroupDialog v-model:visible="showNewGroupDialog" :parent-id="newGroupParentId" @confirm="confirmNewGroup" />

    <NewGroupDialog v-model:visible="showChangeNewGroupDialog" :parent-id="changeNewGroupParentId" @confirm="confirmChangeNewGroup" />

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick, provide } from 'vue'
import { X, ChevronRight, ChevronDown, Filter, Check, Network, Zap, Clock, Plus, Palette, SquareTerminal, Activity, Pencil, MoreHorizontal, FolderTree, ArrowRightLeft, Star } from '@lucide/vue'
import { getShellLabel as getShellLabelBase } from '../utils/shellLabel'
import { useConnectionStore } from '../stores/connectionStore'
import { useFavoriteStore } from '../stores/favoriteStore'
import type { GroupTreeNode } from '../stores/connectionStore'
import { usePanelStore } from '../stores/panelStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useI18n } from '../i18n'
import ConnectionForm from './ConnectionForm.vue'
import ExportDialog from './ExportDialog.vue'
import ImportDialog from './ImportDialog.vue'
import QuickCommandsPanel from './QuickCommandsPanel.vue'
import TunnelsPanel from './TunnelsPanel.vue'
import HistoryPanel from './HistoryPanel.vue'
import FileSidebar from './FileSidebar.vue'
import MonitorOverviewSidebar from './MonitorOverviewSidebar.vue'
import { useCompanionStore } from '../stores/companionStore'
import CustomThemeEditor from './CustomThemeEditor.vue'
import GroupTreeItem from './GroupTreeItem.vue'
import Menu from './Menu.vue'
import MenuItem from './MenuItem.vue'
import MenuDivider from './MenuDivider.vue'
import type { ConnectionConfig, ConnectionGroup } from '../types/session'
import { parseQuickConnect, formatConnSubtitle, matchTypeFilter } from '../utils/quickConnect'
import ConnectionContextMenu from './ConnectionContextMenu.vue'
import { connectionTypeIcon } from '../utils/connectionTypes'
import { isWorkspaceHostType } from '../composables/createWorkspace'
import GroupContextMenu from './GroupContextMenu.vue'
import TypeFilterMenu from './TypeFilterMenu.vue'
import RenameGroupDialog from './RenameGroupDialog.vue'
import NewGroupDialog from './NewGroupDialog.vue'
import DeleteGroupDialog from './DeleteGroupDialog.vue'
import { FONT_OPTIONS, FONT_WEIGHT_OPTIONS, LANGUAGE_OPTIONS, FOLLOW_APP_THEME, SIDEBAR_TAB_DEFAULTS, SIDEBAR_TAB_ORDER } from '../types/settings'
import { formatFontFamily, normalizeFontFamilyValue } from '../utils/formatFontFamily'
import { useTerminalThemeOptions } from '../composables/useTerminalThemeOptions'
import { GetAllFonts } from '../../bindings/easyaiot/terminal/app'
import { useLocalStateStore } from '../stores/localStateStore'
import { formatKeyBinding } from '../composables/useKeyboardShortcuts'

defineProps<{
  visible: boolean
}>()
const emit = defineEmits(['connect', 'connectToWorkspace', 'createWorkspace', 'connectOnly', 'toggle'])
const connectionStore = useConnectionStore()
const favoriteStore = useFavoriteStore()
const settingsStore = useSettingsStore()
// "Right-click menu" host-list mode hides the hover star/⋯ buttons entirely —
// the same connection menu stays reachable via right-click (issue #934).
const showHostRowButtons = computed(() => settingsStore.settings.hostListMenuStyle !== 'rightclick')
const panelStore = usePanelStore()
const companionStore = useCompanionStore()
const { t } = useI18n()
const isMacPlatform = /Mac|iPhone|iPad/.test(navigator.userAgent)
const quickCommandsTitle = computed(() => {
  const binding = settingsStore.settings.keyboard.openQuickCommands
  const shortcut = binding ? formatKeyBinding(binding, isMacPlatform) : ''
  return shortcut ? `${t('quickCommands.quickCommandsTab')} (${shortcut})` : t('quickCommands.quickCommandsTab')
})
// Connection ids that currently have an open panel/session (panel.config.id).
// Reactive over the panelStore map, so it updates as panels open/close.
const openPanelConnIds = computed<Set<string>>(() => {
  const s = new Set<string>()
  for (const p of panelStore.panels.values()) {
    if (p.config?.id) s.add(p.config.id)
  }
  return s
})
const showForm = ref(false)
const showExportDialog = ref(false)
const showImportDialog = ref(false)
const editConfig = ref<ConnectionConfig | undefined>(undefined)
const activeView = ref<'connections' | 'quickCommands' | 'history' | 'personalization' | 'files' | 'monitor' | 'tunnels'>('connections')
const quickCommandsRef = ref<InstanceType<typeof QuickCommandsPanel> | null>(null)

function openQuickCommands() {
  activeView.value = 'quickCommands'
  nextTick(() => quickCommandsRef.value?.focusSearch())
}

// ── SSH companion: files / monitor folded into this sidebar ──
function onFilesTabClick() {
  activeView.value = 'files'
  // Always open the files view (shows an idle/"need SSH" empty state when no
  // active SSH panel). If there is an active SSH panel, (re)establish the
  // companion SFTP session. Closing happens via the panel's X button, which
  // clears filesVisible and the watch below falls back to connections.
  companionStore.filesVisible = true
  const pid = companionStore.getActiveFilesPanelId()
  if (pid) companionStore.ensureSftp(pid).catch(() => {})
}
function onMonitorTabClick() {
  activeView.value = 'monitor'
  companionStore.monitorVisible = true
  const pid = companionStore.getActiveSshPanelId()
  if (pid) companionStore.ensureMonitor(pid).catch(() => {})
}
// If the companion panel hides itself (collapse button), fall back to connections view.
watch(
  () => [companionStore.filesVisible, companionStore.monitorVisible],
  ([filesVisible, monitorVisible]) => {
    if (!filesVisible && activeView.value === 'files') activeView.value = 'connections'
    if (!monitorVisible && activeView.value === 'monitor') activeView.value = 'connections'
  },
)

// ── Sidebar tab visibility ──
// Single source of truth is AppSettings.sidebarTabs (editable in Settings →
// basic); right-clicking the tab strip opens the same toggles as a shortcut.
// "connections" is the primary view and can never be hidden.

function tabVisible(key: string): boolean {
  return settingsStore.settings.sidebarTabs?.[key] ?? SIDEBAR_TAB_DEFAULTS[key] ?? true
}

const tabStripMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const tabStripMenuVisible = ref(false)

function onTabStripContextMenu(e: MouseEvent) {
  tabStripMenuRef.value?.openAt(e.clientX, e.clientY)
}

function onTabVisibilityClick(key: string) {
  if (key === 'connections') return // always visible
  const tabs = settingsStore.settings.sidebarTabs
  tabs[key] = !tabVisible(key)
  settingsStore.save()
  // Hiding the view that's currently active falls back to connections.
  if (!tabs[key] && activeView.value === key) activeView.value = 'connections'
}

// ── Personalization panel ──
// Single source: GetAllFonts returns every installed family with its mono
// flag (the bundled JetBrains Mono Variable is pinned first). Each select's
// embedded "monospace only" checkbox filters this client-side.
const allFonts = ref<{ Name: string; IsMono: boolean }[]>([])
const fontMonoOnly = ref(true)
const fallbackFontMonoOnly = ref(true)

const toFontOption = (name: string) => ({ label: name, value: name })
const personalizationFontOptions = computed(() =>
  allFonts.value.length > 0
    ? allFonts.value.filter(f => !fontMonoOnly.value || f.IsMono).map(f => toFontOption(f.Name))
    : FONT_OPTIONS
)
const personalizationFallbackFontOptions = computed(() =>
  allFonts.value.length > 0
    ? allFonts.value.filter(f => !fallbackFontMonoOnly.value || f.IsMono).map(f => toFontOption(f.Name))
    : FONT_OPTIONS
)

const { terminalThemeGroups, isCustomTheme } = useTerminalThemeOptions()

const themeEditorVisible = ref(false)
const themeEditorSourceId = ref<string | undefined>(undefined)
function openThemeEditor(sourceThemeId?: string) {
  themeEditorSourceId.value = sourceThemeId
  themeEditorVisible.value = true
}

// Notify App.vue to hide native RDP window when edit dialog opens
watch(showForm, (val) => {
  window.dispatchEvent(new CustomEvent(val ? 'rdp:overlay-push' : 'rdp:overlay-pop'))
})

const searchQuery = ref('')
const searchInputRef = ref<any>(null)
const selectedTypeFilter = ref('all')
const filterMenuRef = ref<InstanceType<typeof TypeFilterMenu> | null>(null)
const focusedId = ref<string | null>(null)

function focusSearch() {
  // The search input only exists in the connections view; switch back first
  // so the shortcut works no matter which view the sidebar was left in.
  activeView.value = 'connections'
  nextTick(() => {
    const el = searchInputRef.value?.$el?.querySelector('input')
    if (el instanceof HTMLInputElement) {
      el.focus()
      el.select()
    }
  })
}

// ── Expand/collapse state ──
const expandedGroups = ref<Set<string>>(new Set())
const collapsedGroupIds = ref<Set<string>>(new Set())

// Build expandedGroups from all known group IDs minus those explicitly collapsed
function syncExpandedFromCollapsed(groupIds: string[]) {
  expandedGroups.value = new Set(groupIds.filter(id => !collapsedGroupIds.value.has(id)))
}

// Persist collapsedGroupIds to LocalState
async function persistCollapsedState() {
  try {
    useLocalStateStore().update({ collapsedGroupIds: [...collapsedGroupIds.value] })
  } catch {
    // ignore errors — collapse state is not critical
  }
}

async function toggleGroup(groupId: string) {
  if (expandedGroups.value.has(groupId)) {
    expandedGroups.value.delete(groupId)
    collapsedGroupIds.value.add(groupId)
  } else {
    expandedGroups.value.add(groupId)
    collapsedGroupIds.value.delete(groupId)
  }
  await persistCollapsedState()
}

// ── Multi-select ──
const selectedIds = ref<Set<string>>(new Set())

// ── Search filter ──
function filterTreeNode(node: GroupTreeNode, q: string, matchConn: (c: ConnectionConfig) => boolean): GroupTreeNode | null {
  const groupNameMatch = node.group.name.toLowerCase().includes(q)
  const filteredConns = groupNameMatch
    ? node.connections.filter(matchConn)
    : node.connections.filter(matchConn)
  const filteredChildren: GroupTreeNode[] = []
  for (const child of node.children) {
    const filtered = filterTreeNode(child, q, matchConn)
    if (filtered) filteredChildren.push(filtered)
  }
  const hasMatchingName = groupNameMatch
  const hasConnections = filteredConns.length > 0
  const hasChildren = filteredChildren.length > 0
  if (hasMatchingName || hasConnections || hasChildren) {
    return { group: node.group, connections: hasMatchingName ? node.connections.filter(matchConn) : filteredConns, children: filteredChildren }
  }
  return null
}

const filteredGrouped = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const data = connectionStore.groupedConnections

  const matchConn = matchesConnFilters

  const filteredRoots: GroupTreeNode[] = []
  for (const root of data.roots) {
    const filtered = filterTreeNode(root, q, matchConn)
    if (filtered) filteredRoots.push(filtered)
  }

  const filteredUngrouped = data.ungrouped.filter(matchConn)

  return { roots: filteredRoots, ungrouped: filteredUngrouped }
})

// Shared search-text + type-filter predicate used by the group tree and the
// favorites list so both sections filter identically.
function matchesConnFilters(c: ConnectionConfig): boolean {
  const q = searchQuery.value.trim().toLowerCase()
  const textMatch = !q || c.name.toLowerCase().includes(q) || c.host.toLowerCase().includes(q)
  return textMatch && matchTypeFilter(c, selectedTypeFilter.value)
}

// ── Favorites (virtual group above all groups) ──
// Favorites keep their own expand state — they are not a real group, so they
// are neither persisted to collapsedGroupIds nor touched by the search-mode
// expand/restore logic.
const favoritesExpanded = ref(true)

// Resolved favorite connections in saved order; ids of deleted connections
// are silently dropped (same tolerate-missing policy as recent connections).
const favoriteConns = computed<ConnectionConfig[]>(() => {
  return favoriteStore.favoriteIds
    .map(id => connectionStore.connections.find(c => c.id === id))
    .filter((c): c is ConnectionConfig => !!c)
    .filter(matchesConnFilters)
})

// ── Favorites drag & drop: reorder within the favorites list only ──
function onFavDragOver(e: DragEvent, conn: ConnectionConfig) {
  if (!reorderEnabled.value) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  const position = (e.clientY - rect.top) < rect.height / 2 ? 'before' : 'after'
  dropIndicator.value = { id: conn.id, position }
  dragOverGroupId.value = null
}

async function onFavDrop(e: DragEvent, conn: ConnectionConfig) {
  if (!reorderEnabled.value) return
  const indicator = dropIndicator.value
  dropIndicator.value = null
  const raw = e.dataTransfer?.getData('text/plain')
  if (!raw || !indicator) return
  try {
    const data = JSON.parse(raw)
    if (!Array.isArray(data) || data.length === 0) return
    let beforeId: string | undefined
    if (indicator.position === 'before') {
      beforeId = conn.id
    } else {
      // After: insert before the favorite that follows the target
      const ids = favoriteStore.favoriteIds
      const idx = ids.indexOf(conn.id)
      beforeId = idx >= 0 ? ids[idx + 1] : undefined
    }
    await favoriteStore.reorder(data, beforeId)
  } catch {
    // ignore parse errors
  }
}

function countTreeNodes(nodes: GroupTreeNode[]): number {
  let count = 0
  for (const node of nodes) {
    count += node.connections.length
    count += countTreeNodes(node.children)
  }
  return count
}

const totalFiltered = computed(() => {
  return countTreeNodes(filteredGrouped.value.roots) + filteredGrouped.value.ungrouped.length
})

function collectTreeConnIds(nodes: GroupTreeNode[]): string[] {
  const ids: string[] = []
  for (const node of nodes) {
    for (const c of node.connections) ids.push(c.id)
    ids.push(...collectTreeConnIds(node.children))
  }
  return ids
}

// Update selection when filter changes
watch(filteredGrouped, () => {
  const allIds = collectTreeConnIds(filteredGrouped.value.roots)
  for (const c of filteredGrouped.value.ungrouped) allIds.push(c.id)
  // Favorites rows are also selectable; they render above the tree
  if (favoritesExpanded.value) {
    allIds.unshift(...favoriteConns.value.map(c => c.id))
  }

  if (allIds.length === 0) {
    focusedId.value = searchQuery.value.trim() ? '__new_connection__' : null
    selectedIds.value = new Set()
  } else if (!focusedId.value || !allIds.includes(focusedId.value)) {
    focusedId.value = allIds[0]
    selectedIds.value = new Set([allIds[0]])
  }
}, { immediate: true })

// Track the previous group ID set so we can detect new vs deleted groups
const prevGroupIds = ref<Set<string>>(new Set())
const collapsedStateLoaded = ref(false)

// Sync expanded state when groups change (add/delete/rename) — preserve user collapse choices
watch(() => connectionStore.allGroupIds, (ids) => {
  if (!collapsedStateLoaded.value) return
  const currentIds = new Set<string>(ids)
  if (connectionStore.groups.length > 0) {
    currentIds.add('__ungrouped__')
  }

  // Remove stale group IDs from both expanded and collapsed
  const allKnown = new Set([...expandedGroups.value, ...collapsedGroupIds.value])
  for (const id of allKnown) {
    if (id === '__ungrouped__' && connectionStore.groups.length === 0) continue
    if (id !== '__ungrouped__' && !currentIds.has(id)) {
      expandedGroups.value.delete(id)
      collapsedGroupIds.value.delete(id)
    }
  }

  // New groups (and __ungrouped__ if first time) — expand by default
  for (const id of currentIds) {
    if (!prevGroupIds.value.has(id) && !collapsedGroupIds.value.has(id)) {
      expandedGroups.value.add(id)
    }
  }

  prevGroupIds.value = currentIds
})

// Initialize collapse state from persisted LocalState
async function initCollapseState() {
  try {
    const ls = useLocalStateStore()
    if (!ls.loaded) await ls.init()
    if (ls.state.collapsedGroupIds && ls.state.collapsedGroupIds.length > 0) {
      collapsedGroupIds.value = new Set(ls.state.collapsedGroupIds)
    }
  } catch {
    // Use default (all expanded)
  }

  // Build initial expandedGroups and prevGroupIds
  const allIds = connectionStore.allGroupIds.slice()
  if (connectionStore.groups.length > 0) {
    allIds.push('__ungrouped__')
  }
  expandedGroups.value = new Set(allIds.filter(id => !collapsedGroupIds.value.has(id)))
  prevGroupIds.value = new Set(allIds)
  collapsedStateLoaded.value = true
}

// Track previous search query state
const wasSearching = ref(false)

// Auto-expand all groups while searching; restore persisted state when search is cleared
watch(searchQuery, (q) => {
  const isSearching = !!q.trim()
  if (isSearching && !wasSearching.value) {
    // Entering search mode — expand all visually (don't touch collapsedGroupIds)
    expandedGroups.value = new Set()
    function expandTree(nodes: GroupTreeNode[]) {
      for (const node of nodes) {
        expandedGroups.value.add(node.group.id)
        expandTree(node.children)
      }
    }
    expandTree(filteredGrouped.value.roots)
    if (connectionStore.groups.length > 0) {
      expandedGroups.value.add('__ungrouped__')
    }
  } else if (!isSearching && wasSearching.value) {
    // Exiting search mode — restore from persisted collapsed state
    const allIds = connectionStore.allGroupIds
    if (connectionStore.groups.length > 0) {
      allIds.push('__ungrouped__')
    }
    syncExpandedFromCollapsed(allIds)
    // Clean stale entries from collapsedGroupIds
    collapsedGroupIds.value = new Set(
      [...collapsedGroupIds.value].filter(id => id === '__ungrouped__' || connectionStore.groups.some(g => g.id === id))
    )
  }
  wasSearching.value = isSearching
})

// ── Resize ──
const sidebarWidth = ref(240)
const isResizing = ref(false)
const sidebarEl = ref<HTMLDivElement>()

function onResizeStart(e: MouseEvent) {
  isResizing.value = true
  const el = sidebarEl.value
  if (!el) return
  const startX = e.clientX
  const startWidth = el.offsetWidth

  window.dispatchEvent(new CustomEvent('split:resize-start'))

  function onMouseMove(ev: MouseEvent) {
    if (!isResizing.value) return
    const delta = ev.clientX - startX
    const newWidth = Math.min(Math.max(startWidth + delta, 240), 400)
    el!.style.width = newWidth + 'px'
  }

  function onMouseUp() {
    isResizing.value = false
    sidebarWidth.value = el!.offsetWidth
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    window.dispatchEvent(new CustomEvent('split:resize-end'))
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// ── Keyboard navigation ──
function getAllVisibleIds(): string[] {
  const ids: string[] = []
  if (favoritesExpanded.value) {
    for (const c of favoriteConns.value) ids.push(c.id)
  }
  function collectVisible(nodes: GroupTreeNode[]) {
    for (const node of nodes) {
      if (expandedGroups.value.has(node.group.id)) {
        for (const c of node.connections) ids.push(c.id)
        collectVisible(node.children)
      }
    }
  }
  collectVisible(filteredGrouped.value.roots)
  if (connectionStore.groups.length > 0) {
    if (expandedGroups.value.has('__ungrouped__')) {
      for (const c of filteredGrouped.value.ungrouped) ids.push(c.id)
    }
  } else {
    for (const c of filteredGrouped.value.ungrouped) ids.push(c.id)
  }
  if (searchQuery.value.trim()) {
    ids.push('__new_connection__')
  }
  return ids
}

function scrollActiveIntoView() {
  nextTick(() => {
    const activeEl = sidebarEl.value?.querySelector('.connection-item.active') as HTMLElement
    activeEl?.scrollIntoView({ block: 'nearest' })
  })
}

function onListKeydown(e: KeyboardEvent) {
  if (showForm.value || menuVisible.value || groupMenuVisible.value) return
  const ids = getAllVisibleIds()
  if (ids.length === 0) return

  const idx = ids.indexOf(focusedId.value || '')

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    const nextIdx = idx >= 0 && idx < ids.length - 1 ? idx + 1 : 0
    focusedId.value = ids[nextIdx]
    selectedIds.value = new Set([ids[nextIdx]])
    scrollActiveIntoView()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    const prevIdx = idx > 0 ? idx - 1 : ids.length - 1
    focusedId.value = ids[prevIdx]
    selectedIds.value = new Set([ids[prevIdx]])
    scrollActiveIntoView()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (focusedId.value === '__new_connection__') {
      openNewFormFromSearch()
      return
    }
    const ids = getSelectedConnectionIds()
    if (ids.length > 0) {
      for (const id of ids) {
        const c = connectionStore.connections.find(c => c.id === id)
        if (c) {
          emit('connect', c)
        }
      }
      selectedIds.value = new Set()
    }
  }
}


// ── Drag & drop ──
const dragOverGroupId = ref<string | null>(null)
// Insertion indicator for manual reordering. `id` is a connection id or a
// group id (or '__ungrouped__'); position drives before/after/inside visuals.
const dropIndicator = ref<{ id: string; position: 'before' | 'after' | 'inside' } | null>(null)

// Reordering is only meaningful against the full, unfiltered list.
const reorderEnabled = computed(() => !searchQuery.value.trim() && selectedTypeFilter.value === 'all')

function onDragStart(e: DragEvent, conn: ConnectionConfig) {
  const ids = getSelectedConnectionIds()
  // If dragging an unselected item, drag just this one
  if (!ids.includes(conn.id)) {
    selectedIds.value = new Set()
    e.dataTransfer!.setData('text/plain', JSON.stringify([conn.id]))
  } else {
    e.dataTransfer!.setData('text/plain', JSON.stringify(ids))
  }
  // Terminal-type connections can also be dropped onto a workspace panel to
  // connect + split at the drop position. The row-under-cursor wins over the
  // selection on purpose — a split drop is a single-connection gesture.
  if (isWorkspaceHostType(conn.type)) {
    e.dataTransfer!.setData('application/conn-id', conn.id)
  }
  // Any connection can be dropped onto the tab bar to open a tab there.
  e.dataTransfer!.setData('application/conn-open', conn.id)
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragEnd() {
  dragOverGroupId.value = null
  dropIndicator.value = null
}

// Ordered connection ids within a group, matching connections array order.
function connSiblingIds(groupId: string | undefined): string[] {
  return connectionStore.connections
    .filter(c => (c.groupId || undefined) === (groupId || undefined))
    .map(c => c.id)
}

// ── Connection item drag (reorder within / across groups) ──
function onConnDragOver(e: DragEvent, conn: ConnectionConfig) {
  if (!reorderEnabled.value) return
  const el = e.currentTarget as HTMLElement
  const rect = el.getBoundingClientRect()
  const position = (e.clientY - rect.top) < rect.height / 2 ? 'before' : 'after'
  dropIndicator.value = { id: conn.id, position }
  dragOverGroupId.value = null
}

async function onConnDrop(e: DragEvent, conn: ConnectionConfig) {
  const indicator = dropIndicator.value
  dropIndicator.value = null
  const raw = e.dataTransfer?.getData('text/plain')
  if (!raw || !indicator) return
  try {
    const data = JSON.parse(raw)
    if (!Array.isArray(data) || data.length === 0) return
    const targetGroupId = conn.groupId || undefined
    let beforeId: string | undefined
    if (indicator.position === 'before') {
      beforeId = conn.id
    } else {
      const siblings = connSiblingIds(targetGroupId)
      const idx = siblings.indexOf(conn.id)
      beforeId = idx >= 0 ? siblings[idx + 1] : undefined
    }
    await connectionStore.moveConnections(data, targetGroupId, beforeId)
    selectedIds.value = new Set()
  } catch {
    // ignore parse errors
  }
}

// ── Group header drag (reorder siblings vs reparent/move-in) ──
function onGroupDragOver(groupId: string, e?: DragEvent) {
  if (reorderEnabled.value && e && groupId !== '__ungrouped__') {
    const el = e.currentTarget as HTMLElement
    const rect = el.getBoundingClientRect()
    const offset = e.clientY - rect.top
    const edge = rect.height * 0.28
    if (offset < edge) {
      dropIndicator.value = { id: groupId, position: 'before' }
      dragOverGroupId.value = null
      return
    }
    if (offset > rect.height - edge) {
      dropIndicator.value = { id: groupId, position: 'after' }
      dragOverGroupId.value = null
      return
    }
  }
  // Middle region (or reorder disabled / ungrouped): move-in / reparent
  dropIndicator.value = null
  dragOverGroupId.value = groupId
}

function onGroupDragLeave(groupId: string) {
  if (dragOverGroupId.value === groupId) {
    dragOverGroupId.value = null
  }
  if (dropIndicator.value?.id === groupId) {
    dropIndicator.value = null
  }
}

async function onGroupDrop(groupId: string, e: DragEvent) {
  const indicator = dropIndicator.value
  dragOverGroupId.value = null
  dropIndicator.value = null
  const raw = e.dataTransfer?.getData('text/plain')
  if (!raw) return
  try {
    const data = JSON.parse(raw)
    // Dropping a group
    if (data && data.type === 'group') {
      if (indicator && indicator.id === groupId && indicator.position !== 'inside') {
        // Reorder as sibling of the target group
        const target = connectionStore.groups.find(g => g.id === groupId)
        const newParentId = target?.parentId
        let beforeId: string | undefined
        if (indicator.position === 'before') {
          beforeId = groupId
        } else {
          const siblings = connectionStore.groups
            .filter(g => (g.parentId || undefined) === (newParentId || undefined))
            .map(g => g.id)
          const idx = siblings.indexOf(groupId)
          beforeId = idx >= 0 ? siblings[idx + 1] : undefined
        }
        await connectionStore.moveGroup(data.id, newParentId, beforeId)
        return
      }
      // Middle: move into this group as a child
      const targetParentId = groupId === '__ungrouped__' ? undefined : groupId
      await connectionStore.reparentGroup(data.id, targetParentId)
      return
    }
    // Dropping connections
    if (Array.isArray(data) && data.length > 0) {
      const targetGroupId = groupId === '__ungrouped__' ? undefined : groupId
      if (indicator && indicator.id === groupId && indicator.position !== 'inside') {
        // Reorder relative to the group header: before = group's first slot
        let beforeId: string | undefined
        if (indicator.position === 'before') {
          beforeId = connSiblingIds(targetGroupId)[0]
        } else {
          beforeId = undefined // after header: append to group end
        }
        await connectionStore.moveConnections(data, targetGroupId, beforeId)
      } else {
        await connectionStore.moveConnections(data, targetGroupId)
      }
      selectedIds.value = new Set()
    }
  } catch {
    // ignore parse errors
  }
}

// ── Connection click / multi-select ──
const lastClickId = ref<string | null>(null)

function onItemClick(e: MouseEvent, conn: ConnectionConfig) {
  if (e.shiftKey && lastClickId.value) {
    // Range select from last click to current
    const ids = getAllVisibleIds()
    const anchorIdx = ids.indexOf(lastClickId.value)
    const currentIdx = ids.indexOf(conn.id)
    if (anchorIdx >= 0 && currentIdx >= 0) {
      const [start, end] = anchorIdx < currentIdx ? [anchorIdx, currentIdx] : [currentIdx, anchorIdx]
      const selected = new Set<string>()
      for (let i = start; i <= end; i++) {
        selected.add(ids[i])
      }
      selectedIds.value = selected
    }
    focusedId.value = conn.id
  } else if (e.ctrlKey || e.metaKey) {
    // Toggle multi-select
    if (selectedIds.value.has(conn.id)) {
      selectedIds.value.delete(conn.id)
    } else {
      selectedIds.value.add(conn.id)
    }
    selectedIds.value = new Set(selectedIds.value)
    lastClickId.value = conn.id
  } else {
    focusedId.value = conn.id
    selectedIds.value = new Set([conn.id])
    lastClickId.value = conn.id
  }
}

// ── Locate a connection from the tab context menu ──
async function locateConnectionById(id: string) {
  const conn = connectionStore.connections.find(c => c.id === id)
  if (!conn) return

  // Surface the target: drop any search / type filter that could hide it.
  searchQuery.value = ''
  selectedTypeFilter.value = 'all'

  // Expand the containing group (and its ancestors) so the row is rendered.
  if (conn.groupId) {
    let gid: string | undefined = conn.groupId
    while (gid) {
      expandedGroups.value.add(gid)
      collapsedGroupIds.value.delete(gid)
      const g = connectionStore.groups.find(g => g.id === gid)
      gid = g?.parentId
    }
    expandedGroups.value = new Set(expandedGroups.value)
  } else if (connectionStore.groups.length > 0) {
    // Ungrouped target with real groups present → expand the virtual No-Group group.
    expandedGroups.value.add('__ungrouped__')
    collapsedGroupIds.value.delete('__ungrouped__')
    expandedGroups.value = new Set(expandedGroups.value)
  }

  // Select the target. focusedId is set before the filter watcher flushes,
  // so that watcher keeps our selection instead of resetting to the first row.
  focusedId.value = conn.id
  lastClickId.value = conn.id
  selectedConn.value = conn
  selectedIds.value = new Set([conn.id])

  await nextTick()
  await nextTick()
  const row = sidebarEl.value?.querySelector<HTMLElement>(`.connection-item[data-conn-id="${conn.id}"]`)
  row?.scrollIntoView({ block: 'nearest' })
}

function onLocateConnection(e: Event) {
  const id = (e as CustomEvent)?.detail?.id
  if (typeof id === 'string') locateConnectionById(id)
}

function onItemDblClick(conn: ConnectionConfig) {
  selectedIds.value = new Set()
  emit('connect', conn)
}

// ── Context menu helper ──
function getSelectedConnectionIds(): string[] {
  if (selectedIds.value.size > 0) {
    return [...selectedIds.value]
  }
  if (selectedConn.value) {
    return [selectedConn.value.id]
  }
  if (focusedId.value) {
    return [focusedId.value]
  }
  return []
}

// ── Connection context menu ──
const menuVisible = ref(false)
const selectedConn = ref<ConnectionConfig | null>(null)
const menuRef = ref<InstanceType<typeof ConnectionContextMenu> | null>(null)

function onContextMenu(e: MouseEvent, conn: ConnectionConfig) {
  e.stopPropagation()
  selectedConn.value = conn
  // If right-clicking on a non-multi-selected item, clear others and select this one
  if (!selectedIds.value.has(conn.id)) {
    selectedIds.value = new Set([conn.id])
    focusedId.value = conn.id
  }
  menuRef.value?.openAt(e.clientX, e.clientY)
}

function onConnMoreClick(e: MouseEvent, conn: ConnectionConfig) {
  const btn = e.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  selectedConn.value = conn
  if (!selectedIds.value.has(conn.id)) {
    selectedIds.value = new Set([conn.id])
    focusedId.value = conn.id
  }
  menuRef.value?.openAt(rect.right + 4, rect.top)
}

function closeMenu() {
  menuVisible.value = false
}




// Open the WSL distro's file manager in a standalone tab (wsl-file session).






// Whether the given connection id currently has an open panel/session.








// Resolved multi-select targets for the shared context menu (always includes
// the right-clicked connection).
const ctxTargets = computed<ConnectionConfig[]>(() => {
  const conns = getSelectedConnectionIds()
    .map(id => connectionStore.connections.find(c => c.id === id))
    .filter(Boolean) as ConnectionConfig[]
  if (conns.length > 0) return conns
  return selectedConn.value ? [selectedConn.value] : []
})

function onCtxConnect(targets: ConnectionConfig[], kind?: 'file' | 'wsl-file' | 'monitor') {
  for (const c of targets) {
    emit('connect', c, kind)
  }
}

function onCtxConnectToWorkspace(targets: ConnectionConfig[], workspaceId: string) {
  for (const c of targets) {
    if (c.type !== 'ssh') continue
    emit('connectToWorkspace', { config: c, workspaceId })
  }
}

function onCtxCreateWorkspace(targets: ConnectionConfig[]) {
  emit('createWorkspace', targets)
}

function onCtxDelete(targets: ConnectionConfig[]) {
  connectionStore.removeMany(targets.map(c => c.id))
  selectedIds.value = new Set()
}

function doEdit(config: ConnectionConfig) {
  editConfig.value = { ...config }
  showForm.value = true
}




// ── Standalone new group ──
const showNewGroupDialog = ref(false)

const newConnGroupId = ref<string | undefined>(undefined)
const newGroupParentId = ref<string | undefined>(undefined)

// Tree data for el-tree-select
interface TreeOption {
  value: string
  label: string
  children?: TreeOption[]
}

const groupTreeData = computed<TreeOption[]>(() => {
  function buildTree(nodes: GroupTreeNode[]): TreeOption[] {
    return nodes.map(node => ({
      value: node.group.id,
      label: node.group.name,
      children: node.children.length > 0 ? buildTree(node.children) : undefined,
    }))
  }
  return [
    { value: '__none__', label: t('conn.noGroup') },
    ...buildTree(connectionStore.groupedConnections.roots),
  ]
})

function doNewConnInGroup() {
  closeMenu()
  closeGroupMenu()
  closeEmptyAreaMenu()
  editConfig.value = undefined
  newConnGroupId.value = selectedGroup.value?.id !== '__ungrouped__' ? selectedGroup.value?.id : undefined
  showForm.value = true
}

function doNewGroup(parentGroupId?: string) {
  closeMenu()
  closeGroupMenu()
  closeEmptyAreaMenu()
  // Clear the parent first, then render the explicitly-passed group. Callers
  // decide what to pass; empty-area creation passes nothing, so it defaults
  // to "None" instead of carrying over a previously-selected group.
  newGroupParentId.value = parentGroupId
  showNewGroupDialog.value = true
}

function selectedGroupParentId(): string | undefined {
  return (selectedGroup.value && selectedGroup.value.id !== '__ungrouped__') ? selectedGroup.value.id : undefined
}

async function confirmNewGroup(name: string, parentId: string | undefined) {
  // save in background, don't block dialog close
  await connectionStore.addGroup(name, parentId)
}

// ── Move to (unified dialog for connections and groups) ──
const changeDialogMode = ref<'connections' | 'group'>('connections')


function doChangeParentGroup() {
  closeMenu()
  closeGroupMenu()
  closeEmptyAreaMenu()
  changeDialogMode.value = 'group'
  changeGroupTargetId.value = selectedGroup.value?.parentId
  showChangeGroupDialog.value = true
}

// ── Change group ──
const showChangeGroupDialog = ref(false)
const changeGroupTargetId = ref<string | undefined>(undefined)
const showChangeNewGroupDialog = ref(false)
const changeNewGroupParentId = ref<string | undefined>(undefined)
const externalChangeGroupIds = ref<string[]>([])

// Open change-group dialog from outside (e.g. StartTab card context menu)
function openChangeGroupFor(ids: string[]) {
  externalChangeGroupIds.value = ids
  changeDialogMode.value = 'connections'
  const groups = new Set(ids.map(id => {
    const c = connectionStore.connections.find(c => c.id === id)
    return c?.groupId || '__none__'
  }))
  if (groups.size === 1) {
    const g = [...groups][0]
    changeGroupTargetId.value = g === '__none__' ? undefined : g
  } else {
    changeGroupTargetId.value = undefined
  }
  showChangeGroupDialog.value = true
}

function getChangeGroupIds(): string[] {
  if (externalChangeGroupIds.value.length > 0) {
    return externalChangeGroupIds.value
  }
  return getSelectedConnectionIds()
}

async function confirmChangeGroup() {
  if (changeDialogMode.value === 'group') {
    if (selectedGroup.value && selectedGroup.value.id !== '__ungrouped__') {
      await connectionStore.reparentGroup(selectedGroup.value.id, changeGroupTargetId.value)
    }
    showChangeGroupDialog.value = false
    return
  }

  const val = changeGroupTargetId.value
  if (val === '__new__') {
    showChangeNewGroupDialog.value = true
    return
  }
  const groupId = val === '__none__' ? undefined : val
  const ids = getChangeGroupIds()
  connectionStore.setConnectionsGroup(ids, groupId)
  selectedIds.value = new Set()
  showChangeGroupDialog.value = false
  changeGroupTargetId.value = undefined
  externalChangeGroupIds.value = []
}

async function confirmChangeNewGroup(name: string, parentId: string | undefined) {
  const group = await connectionStore.addGroup(name, parentId)
  const ids = getChangeGroupIds()
  if (ids.length > 0) {
    connectionStore.setConnectionsGroup(ids, group.id)
    selectedIds.value = new Set()
  }
  showChangeGroupDialog.value = false
  changeGroupTargetId.value = undefined
  externalChangeGroupIds.value = []
}

// Clear external IDs when dialog is closed without saving
watch(showChangeGroupDialog, (open) => {
  if (!open) externalChangeGroupIds.value = []
})

// ── Group context menu ──
const groupMenuVisible = ref(false)
const selectedGroup = ref<ConnectionGroup | null>(null)
const groupMenuRef = ref<InstanceType<typeof GroupContextMenu> | null>(null)

function onGroupContextMenu(e: MouseEvent, group: ConnectionGroup) {
  e.stopPropagation()
  selectedGroup.value = group
  groupMenuRef.value?.openAt(e.clientX, e.clientY)
}

function closeGroupMenu() {
  groupMenuVisible.value = false
}

// ── Empty area context menu ──
const emptyAreaMenuVisible = ref(false)
const emptyAreaMenuRef = ref<InstanceType<typeof Menu> | null>(null)

function onEmptyAreaContextMenu(e: MouseEvent) {
  emptyAreaMenuRef.value?.openAt(e.clientX, e.clientY)
}

function closeEmptyAreaMenu() {
  emptyAreaMenuVisible.value = false
}

// ── Virtual group context menu ──
function onVirtualGroupContextMenu(e: MouseEvent) {
  e.stopPropagation()
  selectedGroup.value = { id: '__ungrouped__', name: t('conn.noGroup') }
  groupMenuRef.value?.openAt(e.clientX, e.clientY)
}

// ── Rename group ──
const showRenameGroupDialog = ref(false)

function doRenameGroup() {
  if (!selectedGroup.value) return
  showRenameGroupDialog.value = true
}

function confirmRenameGroup(name: string) {
  if (!selectedGroup.value) return
  connectionStore.renameGroup(selectedGroup.value.id, name)
}

// ── Delete group ──
const showDeleteGroupDialog = ref(false)


function doDeleteGroup() {
  closeGroupMenu()
  if (!selectedGroup.value) return
  const connCount = connectionStore.connections.filter(c => c.groupId === selectedGroup.value!.id).length
  const childCount = connectionStore.groups.filter(cg => cg.parentId === selectedGroup.value!.id).length
  if (connCount === 0 && childCount === 0) {
    connectionStore.deleteGroup(selectedGroup.value.id, 'move-out')
    return
  }
  showDeleteGroupDialog.value = true
}

async function confirmDeleteGroup(connAction: 'delete-connections' | 'move-out') {
  if (selectedGroup.value) {
    // Deleting the connections too implies deleting nested child groups.
    const childAction = connAction === 'delete-connections' ? 'delete-all' : 'move-up'
    await connectionStore.deleteGroup(selectedGroup.value.id, connAction, childAction)
  }
  showDeleteGroupDialog.value = false
  selectedGroup.value = null
}

// ── New-connection dropdown ──
const showNewConnMenu = ref(false)
const newConnMenuRef = ref<InstanceType<typeof Menu> | null>(null)

function closeNewConnMenu() {
  showNewConnMenu.value = false
}

function onNewConnSelect(cmd: string) {
  closeNewConnMenu()
  onNewConnCommand(cmd)
}

function onNewConnCommand(cmd: string) {
  if (cmd === 'new-connection') {
    // Match quick-connect behavior: when the search box has content, parse it
    // into the new-connection form so fields are pre-filled; otherwise open a
    // blank form.
    if (searchQuery.value.trim()) {
      openNewFormFromSearch()
    } else {
      openNewForm()
    }
  } else if (cmd === 'new-group') {
    newGroupParentId.value = undefined
    showNewGroupDialog.value = true
  } else if (cmd === 'import') {
    showImportDialog.value = true
  } else if (cmd === 'export') {
    showExportDialog.value = true
  }
}


function getShellLabel(path: string): string {
  // Shared helper (utils/shellLabel.ts): same labels as the start-page
  // dropdown, connection form and settings, including the Cygwin/MSYS2
  // bash.exe disambiguation the inline copy here was missing.
  return getShellLabelBase(path, 'Local')
}

function getSubtitle(conn: ConnectionConfig): string {
  if (conn.type === 'container') return conn.containerRuntime || 'container'
  return formatConnSubtitle(conn, getShellLabel)
}

function connIcon(conn: ConnectionConfig) {
  return connectionTypeIcon(conn) || SquareTerminal
}


// ── Form handlers ──
function openNewForm() {
  editConfig.value = undefined
  newConnGroupId.value = undefined
  showForm.value = true
}

function openNewFormFromSearch() {
  const parsed = parseQuickConnect(searchQuery.value.trim())
  editConfig.value = (parsed || { host: searchQuery.value.trim() }) as ConnectionConfig
  selectedIds.value = new Set()
  newConnGroupId.value = undefined
  showForm.value = true
}

function onSave(config: ConnectionConfig) {
  if (editConfig.value?.id) {
    connectionStore.update(config.id, config)
  } else {
    connectionStore.add(config)
  }
  showForm.value = false
  editConfig.value = undefined
}

function onConnectFromForm(config: ConnectionConfig) {
  if (editConfig.value?.id) {
    connectionStore.update(config.id, config)
  } else {
    connectionStore.add(config)
  }
  showForm.value = false
  editConfig.value = undefined
  emit('connect', config)
}

// ── Lifecycle ──
onMounted(async () => {
  window.addEventListener('app:locate-connection', onLocateConnection)
  // Restore group collapse state from persisted settings
  await initCollapseState()
  // Load all fonts for personalization panel
  try {
    const fonts = await GetAllFonts()
    if (fonts && fonts.length > 0) {
      allFonts.value = fonts
      // Migrate a legacy full-stack fontFamily down to its bare family name so
      // it matches a dropdown option (and the new single-name default).
      const names = new Set(allFonts.value.map(f => f.Name))
      const cur = settingsStore.settings.terminal.fontFamily
      const normalized = normalizeFontFamilyValue(cur, names)
      if (normalized !== cur) {
        settingsStore.settings.terminal.fontFamily = normalized
        settingsStore.save()
      }
    }
  } catch {
    // Fall back to FONT_OPTIONS
  }
})

onUnmounted(() => {
  window.removeEventListener('app:locate-connection', onLocateConnection)
})

// Provide to GroupTreeItem (after all refs/functions are defined)
provide('expandedGroups', expandedGroups)
provide('selectedIds', selectedIds)
provide('openPanelConnIds', openPanelConnIds)
provide('dragOverGroupId', dragOverGroupId)
provide('dropIndicator', dropIndicator)
provide('groupHandlers', {
  onToggleGroup: toggleGroup,
  onGroupContextMenu,
  onGroupDragOver,
  onGroupDragLeave,
  onGroupDrop,
  onItemClick,
  onItemDblClick,
  onDragStart,
  onDragEnd,
  onConnDragOver,
  onConnDrop,
  onContextMenu,
  onConnMoreClick,
})
provide('utils', {
  connIcon,
  getSubtitle,
  t,
})

// Open move-to dialog for a specific group (from StartTabContent)
function openChangeGroupForGroup(groupId: string) {
  selectedGroup.value = connectionStore.groups.find(g => g.id === groupId) || null
  changeDialogMode.value = 'group'
  changeGroupTargetId.value = selectedGroup.value?.parentId
  showChangeGroupDialog.value = true
}

defineExpose({ focusSearch, openQuickCommands, openChangeGroupFor, openChangeGroupForGroup })
</script>

<style scoped>
.sidebar {
  background: var(--bg-elevated);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
}

.sidebar.collapsed {
  width: 0 !important;
  overflow: hidden;
}

.sidebar.resizing {
  transition: none;
}

.resize-handle {
  position: absolute;
  right: -0.375rem;
  top: 0;
  bottom: 0;
  width: 0.375rem;
  cursor: col-resize;
  z-index: 10;
  background: transparent;
}

/* Decorative line stays at the sidebar right edge */
.resize-handle::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 1px;
  background: linear-gradient(
    180deg,
    transparent 0%,
    var(--accent-subtle) 20%,
    var(--accent-glow) 50%,
    var(--accent-subtle) 80%,
    transparent 100%
  );
}

/* Hover: 0.1875rem accent bar extending into sidebar */
.resize-handle:hover::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 0.1875rem;
  background: var(--accent);
  box-shadow: 0 0 0.375rem var(--accent-glow);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.125rem;
  padding: 0.625rem 0.875rem;
  flex-shrink: 0;
}

.sidebar-header .icon-btn {
  margin-left: auto;
  font-size: 0.875rem;
}


.sb-icon-btn {
  width: 1.625rem;
  height: 1.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.sb-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.625rem;
  height: 1.625rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.12s ease;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.sidebar-tab {
  font-size: 0.875rem;
  width: 1.625rem;
  height: 1.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}

.sidebar-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.sidebar-tab.active {
  color: var(--accent);
  background: var(--accent-subtle);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0 0.625rem 0.375rem;
  flex-shrink: 0;
}

.connection-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem 0.5rem;
  outline: none;
}

/* ── Group header ── */
.group-header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.625rem 0.375rem 0.375rem;
  cursor: pointer;
  user-select: none;
  border-radius: var(--radius-sm);
  transition: background 0.12s ease;
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.group-header:hover {
  background: var(--bg-hover);
}

.group-arrow {
  display: inline-flex;
  align-items: center;
  width: 1rem;
  color: var(--text-disabled);
}
.group-arrow-icon {
  display: block;
}

.group-name {
  font-weight: 600;
}

.group-count {
  margin-left: auto;
  font-size: 0.625rem;
  color: var(--text-disabled);
  background: var(--bg-subtle);
  padding: 0 0.3125rem;
  border-radius: 0.5rem;
  flex-shrink: 0;
}

.group-header.drag-over {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}

/* ── Connection item ── */
.connection-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.625rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.12s ease;
  margin-bottom: 0.125rem;
  user-select: none;
  position: relative;
}

.connection-item.drop-before::before,
.connection-item.drop-after::after {
  content: '';
  position: absolute;
  left: 0.375rem;
  right: 0.375rem;
  height: 0.125rem;
  background: var(--accent);
  border-radius: 1px;
  z-index: 2;
  pointer-events: none;
}
.connection-item.drop-before::before { top: -1px; }
.connection-item.drop-after::after { bottom: -1px; }

.connection-item.indented {
  padding-left: 1.5rem;
}

.connection-item:hover {
  background: var(--bg-hover);
}

.connection-item.active {
  background: var(--accent-subtle);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.connection-item.active .name {
  color: var(--accent);
}

/* Connection has an open session → highlight its icon with the AI-lock amber */
.connection-item.has-session .conn-icon {
  color: var(--warning);
}

.conn-more-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-left: 0;
  padding: 0;
}
.connection-item:hover .conn-more-btn {
  display: flex;
}
.conn-more-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Favorite toggle: always reserves its slot and sits at the right edge so
   rows align; revealed on hover and while favorited */
.conn-fav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-left: auto;
  padding: 0;
  opacity: 0;
  pointer-events: none;
}
.connection-item:hover .conn-fav-btn,
.conn-fav-btn.on {
  opacity: 1;
  pointer-events: auto;
}
.conn-fav-btn.on {
  color: var(--warning);
}
/* Inside the favorites group: hover reveals the star already lit */
.conn-fav-btn.lit,
.conn-fav-btn.lit:hover {
  color: var(--warning);
}
.conn-fav-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.conn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  flex-shrink: 0;
  color: var(--text-muted);
}

.conn-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
}

.name {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.host {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.conn-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  min-width: 0;
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-disabled);
  font-family: var(--font-ui);
}

.virtual-new-conn .virtual-name {
  color: var(--accent);
}

.filter-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.12s ease;
  padding: 0.125rem;
  border-radius: var(--radius-sm);
}

.filter-trigger:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.filter-trigger.active {
  color: var(--accent);
}

.filter-trigger.active:hover {
  color: var(--accent);
  background: var(--accent-subtle);
}

/* ── Personalization panel ── */
.personalization-panel {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.persist-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-ui);
  color: var(--text-secondary);
  padding: 0 0 0.25rem 0;
  margin-bottom: -0.25rem;
}

.persist-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.persist-label {
  font-size: 0.6875rem;
  font-family: var(--font-ui);
  color: var(--text-muted);
  padding-left: 0.125rem;
}

.persist-section .el-select,
.persist-section .el-input-number {
  width: 100%;
}

.theme-select-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.theme-select-row .el-select {
  flex: 1;
  min-width: 0;
}

.tree-option {
  padding: 0.375rem 0.75rem;
  cursor: pointer;
  font-size: 0.8125rem;
  border-radius: 0.25rem;
}
.tree-option:hover {
  background: var(--bg-hover);
}
.tree-option.active {
  color: var(--accent);
  background: var(--accent-subtle);
}
</style>

<style>
.theme-select-popper .el-select-group__title {
  font-size: 0.625rem;
  color: var(--text-disabled);
  text-align: center;
  padding: 0.375rem 0.75rem 0.125rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.theme-select-popper .el-select-group__title::before,
.theme-select-popper .el-select-group__title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}
</style>
